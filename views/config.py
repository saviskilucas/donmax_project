import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from auth import buscar_perfis, conectar_gsheets, tem_permissao

def carregar_usuarios_planilha():
    try:
        sheet = conectar_gsheets().worksheet("Usuarios")
        return sheet.get_all_records()
    except Exception as e:
        st.error(f"Erro ao carregar lista de usuários: {e}")
        return []

def render():
    if not tem_permissao("usuarios:gerenciar"):
        st.error("⛔ Você não tem permissão para acessar a Gestão de Usuários.")
        return

    st.markdown("<div class='section-header'>⚙️ GESTÃO DE USUÁRIOS E PERFIS</div>", unsafe_allow_html=True)

    perfis_disponiveis = buscar_perfis()
    lista_id_perfis = list(perfis_disponiveis.keys())
    perfil_usuario_atual = st.session_state.get("perfil_logado", "").lower()

    tab_listar, tab_criar = st.tabs(["👥 Usuários Cadastrados", "➕ Criar Novo Usuário"])

    # =========================================================
    # TAB 1: LISTAR, EDITAR E EXCLUIR USUÁRIOS
    # =========================================================
    with tab_listar:
        registros = carregar_usuarios_planilha()
        
        if not registros:
            st.info("Nenhum usuário cadastrado até o momento.")
        else:
            sheet = conectar_gsheets().worksheet("Usuarios")

            for index, reg in enumerate(registros):
                # Linha real na planilha considerando o cabeçalho (linha 1)
                linha_planilha = index + 2 
                
                # Leitura normalizada dos campos
                usr_login = str(reg.get("Usuario", reg.get("usuario", reg.get("Email", "")))).strip().lower()
                nome_usr = str(reg.get("Nome", reg.get("nome", usr_login))).strip()
                id_perfil_usr = str(reg.get("ID_Perfil", reg.get("idperfil", reg.get("perfil", "cozinha")))).strip().lower()
                ativo_usr = str(reg.get("Ativo", reg.get("ativo", "TRUE"))).strip().upper() == "TRUE"
                senha_usr = str(reg.get("Senha", reg.get("senha", ""))).strip()

                nome_perfil_display = perfis_disponiveis.get(id_perfil_usr, {}).get("nome", id_perfil_usr.capitalize())
                status_emoji = "🟢 Ativo" if ativo_usr else "🔴 Inativo"

                with st.expander(f"👤 {nome_usr} ({usr_login}) — [{nome_perfil_display}] {status_emoji}"):
                    # REGRAS DE HIERARQUIA
                    # Admin não pode alterar Master nem outros Admins
                    pode_editar = True
                    if perfil_usuario_atual != "master":
                        if id_perfil_usr in ["master", "admin"]:
                            pode_editar = False

                    if not pode_editar:
                        st.warning("🔒 Você não tem hierarquia para alterar este usuário.")
                    else:
                        with st.form(f"form_editar_usr_{index}"):
                            col_f1, col_f2 = st.columns(2)
                            with col_f1:
                                novo_nome = st.text_input("Nome", value=nome_usr, key=f"edit_nome_{index}")
                                nova_senha = st.text_input("Nova Senha", value=senha_usr, type="password", key=f"edit_senha_{index}")
                            with col_f2:
                                index_perf = lista_id_perfis.index(id_perfil_usr) if id_perfil_usr in lista_id_perfis else 0
                                novo_id_perfil = st.selectbox(
                                    "Perfil de Acesso",
                                    options=lista_id_perfis,
                                    format_func=lambda x: perfis_disponiveis.get(x, {}).get("nome", x),
                                    index=index_perf,
                                    key=f"edit_perf_{index}"
                                )
                                novo_status = st.checkbox("Conta Ativa", value=ativo_usr, key=f"edit_ativo_{index}")

                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                btn_salvar = st.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True)
                            with col_btn2:
                                btn_excluir = st.form_submit_button("🗑️ EXCLUIR USUÁRIO", use_container_width=True)

                            if btn_salvar:
                                try:
                                    # Atualiza os valores na linha da planilha
                                    sheet.update_cell(linha_planilha, 1, novo_nome.strip())
                                    sheet.update_cell(linha_planilha, 2, usr_login)
                                    sheet.update_cell(linha_planilha, 3, nova_senha.strip())
                                    sheet.update_cell(linha_planilha, 4, novo_id_perfil)
                                    sheet.update_cell(linha_planilha, 5, "TRUE" if novo_status else "FALSE")

                                    st.cache_data.clear()
                                    st.success(f"✅ Usuário **{usr_login}** atualizado com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro ao atualizar usuário: {e}")

                            if btn_excluir:
                                # Proteção extra: Não permitir excluir a si mesmo
                                if usr_login == st.session_state.get("id_usuario_logado"):
                                    st.error("❌ Você não pode excluir a sua própria conta ativa.")
                                else:
                                    try:
                                        sheet.delete_rows(linha_planilha)
                                        st.cache_data.clear()
                                        st.success(f"🗑️ Usuário **{usr_login}** excluído com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Erro ao excluir usuário: {e}")

    # =========================================================
    # TAB 2: CRIAR NOVO USUÁRIO
    # =========================================================
    with tab_criar:
        with st.form("form_novo_usuario_admin"):
            col1, col2 = st.columns(2)
            with col1:
                nome_novo = st.text_input("Nome Completo", placeholder="ex: Maria Silva")
                usr_novo = st.text_input("Usuário (Login)", placeholder="ex: maria.silva")
            with col2:
                senha_nova = st.text_input("Senha", type="password", placeholder="••••••••")
                
                # Se for Admin, filtra a opção de criar Master/Admin
                perfis_para_criacao = lista_id_perfis
                if perfil_usuario_atual != "master":
                    perfis_para_criacao = [p for p in lista_id_perfis if p not in ["master", "admin"]]

                perfil_novo = st.selectbox(
                    "Perfil de Acesso",
                    options=perfis_para_criacao,
                    format_func=lambda x: perfis_disponiveis.get(x, {}).get("nome", x)
                )

            btn_cadastrar = st.form_submit_button("CADASTRAR USUÁRIO", use_container_width=True)

            if btn_cadastrar:
                usr_limpo = usr_novo.strip().lower()
                nome_limpo = nome_novo.strip()
                senha_limpa = senha_nova.strip()

                if not usr_limpo or not senha_limpa or not nome_limpo:
                    st.warning("⚠️ Preencha todos os campos obrigatórios.")
                else:
                    try:
                        registros_atuais = carregar_usuarios_planilha()
                        ja_existe = any(
                            str(r.get("Usuario", r.get("usuario", ""))).strip().lower() == usr_limpo
                            for r in registros_atuais
                        )

                        if ja_existe:
                            st.error(f"❌ O usuário **{usr_limpo}** já está cadastrado.")
                        else:
                            sheet = conectar_gsheets().worksheet("Usuarios")
                            nova_linha = [nome_limpo, usr_limpo, senha_limpa, perfil_novo, "TRUE"]
                            sheet.append_row(nova_linha)

                            st.cache_data.clear()
                            st.success(f"✅ Usuário **{usr_limpo}** cadastrado com sucesso!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao cadastrar usuário na planilha: {e}")