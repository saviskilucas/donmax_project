import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from auth import buscar_perfis, conectar_gsheets, tem_permissao

# =========================================================
# FUNÇÕES DE AUXÍLIO - GSHEETS
# =========================================================
def carregar_usuarios_planilha():
    try:
        sheet = conectar_gsheets().worksheet("Usuarios")
        return sheet.get_all_records()
    except Exception as e:
        st.error(f"Erro ao carregar lista de usuários: {e}")
        return []

def carregar_pratos_planilha():
    try:
        sheet = conectar_gsheets().worksheet("Pratos")
        return sheet.get_all_records()
    except Exception as e:
        st.error(f"Erro ao carregar lista de pratos: {e}")
        return []

# =========================================================
# RENDERIZAÇÃO DA PÁGINA DE CONFIGURAÇÕES
# =========================================================
def render():
    st.markdown("<div class='section-header'>⚙️ PAINEL DE CONFIGURAÇÕES</div>", unsafe_allow_html=True)

    # Verifica permissões básicas
    pode_gerenciar_usr = tem_permissao("usuarios:gerenciar")
    pode_gerenciar_pratos = tem_permissao("pratos:gerenciar")

    if not pode_gerenciar_usr and not pode_gerenciar_pratos:
        st.error("⛔ Você não tem permissão para acessar o menu de Configurações.")
        return

    # Tabs principais da tela de configurações
    aba_usr, aba_pratos = st.tabs(["👥 Gerenciar Usuários", "🍲 Gerenciar Produtos / Pratos"])

    # =========================================================
    # SEÇÃO 1: GESTÃO DE USUÁRIOS
    # =========================================================
    with aba_usr:
        if not pode_gerenciar_usr:
            st.warning("🔒 Seu perfil não possui permissão para gerenciar usuários.")
        else:
            perfis_disponiveis = buscar_perfis()
            lista_id_perfis = list(perfis_disponiveis.keys())
            perfil_usuario_atual = st.session_state.get("perfil_logado", "").lower()

            tab_listar_usr, tab_criar_usr = st.tabs(["📋 Usuários Cadastrados", "➕ Novo Usuário"])

            # TAB: LISTAR / EDITAR USUÁRIOS
            with tab_listar_usr:
                registros_usr = carregar_usuarios_planilha()
                if not registros_usr:
                    st.info("Nenhum usuário cadastrado até o momento.")
                else:
                    sheet_usr = conectar_gsheets().worksheet("Usuarios")

                    for index, reg in enumerate(registros_usr):
                        linha_planilha = index + 2
                        
                        usr_login = str(reg.get("Usuario", reg.get("usuario", reg.get("Email", "")))).strip().lower()
                        nome_usr = str(reg.get("Nome", reg.get("nome", usr_login))).strip()
                        id_perfil_usr = str(reg.get("ID_Perfil", reg.get("idperfil", reg.get("perfil", "cozinha")))).strip().lower()
                        ativo_usr = str(reg.get("Ativo", reg.get("ativo", "TRUE"))).strip().upper() == "TRUE"
                        senha_usr = str(reg.get("Senha", reg.get("senha", ""))).strip()

                        nome_perfil_display = perfis_disponiveis.get(id_perfil_usr, {}).get("nome", id_perfil_usr.capitalize())
                        status_emoji = "🟢 Ativo" if ativo_usr else "🔴 Inativo"

                        with st.expander(f"👤 {nome_usr} ({usr_login}) — [{nome_perfil_display}] {status_emoji}"):
                            pode_editar = True
                            if perfil_usuario_atual != "master" and id_perfil_usr in ["master", "admin"]:
                                pode_editar = False

                            if not pode_editar:
                                st.warning("🔒 Você não tem hierarquia para alterar este usuário.")
                            else:
                                with st.form(f"form_editar_usr_{index}"):
                                    col_f1, col_f2 = st.columns(2)
                                    with col_f1:
                                        novo_nome = st.text_input("Nome", value=nome_usr, key=f"edit_nome_{index}")
                                        nova_senha = st.text_input("Senha", value=senha_usr, type="password", key=f"edit_senha_{index}")
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
                                        btn_salvar = st.form_submit_button("💾 SALVAR", use_container_width=True)
                                    with col_btn2:
                                        btn_excluir = st.form_submit_button("🗑️ EXCLUIR", use_container_width=True)

                                    if btn_salvar:
                                        try:
                                            sheet_usr.update_cell(linha_planilha, 1, novo_nome.strip())
                                            sheet_usr.update_cell(linha_planilha, 2, usr_login)
                                            sheet_usr.update_cell(linha_planilha, 3, nova_senha.strip())
                                            sheet_usr.update_cell(linha_planilha, 4, novo_id_perfil)
                                            sheet_usr.update_cell(linha_planilha, 5, "TRUE" if novo_status else "FALSE")

                                            st.cache_data.clear()
                                            st.success(f"✅ Usuário {usr_login} atualizado!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Erro ao atualizar: {e}")

                                    if btn_excluir:
                                        if usr_login == st.session_state.get("id_usuario_logado"):
                                            st.error("❌ Você não pode excluir a sua própria conta ativa.")
                                        else:
                                            try:
                                                sheet_usr.delete_rows(linha_planilha)
                                                st.cache_data.clear()
                                                st.success(f"🗑️ Usuário {usr_login} excluído!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Erro ao excluir: {e}")

            # TAB: CRIAR USUÁRIO
            with tab_criar_usr:
                with st.form("form_novo_usuario_config"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nome_novo = st.text_input("Nome Completo", placeholder="ex: João Silva")
                        usr_novo = st.text_input("Login", placeholder="ex: joao.silva")
                    with col2:
                        senha_nova = st.text_input("Senha", type="password", placeholder="••••••••")
                        
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
                                ja_existe = any(
                                    str(r.get("Usuario", r.get("usuario", ""))).strip().lower() == usr_limpo
                                    for r in registros_usr
                                )
                                if ja_existe:
                                    st.error(f"❌ O login **{usr_limpo}** já está em uso.")
                                else:
                                    sheet_usr = conectar_gsheets().worksheet("Usuarios")
                                    nova_linha = [nome_limpo, usr_limpo, senha_limpa, perfil_novo, "TRUE"]
                                    sheet_usr.append_row(nova_linha)

                                    st.cache_data.clear()
                                    st.success(f"✅ Usuário {usr_limpo} cadastrado!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao cadastrar usuário: {e}")

    # =========================================================
    # SEÇÃO 2: GESTÃO DE PRATOS / PRODUTOS
    # =========================================================
    with aba_pratos:
        if not pode_gerenciar_pratos:
            st.warning("🔒 Seu perfil não possui permissão para gerenciar pratos/produtos.")
        else:
            tab_listar_pratos, tab_criar_prato = st.tabs(["📋 Pratos Cadastrados", "➕ Novo Prato"])

            # TAB: LISTAR / EDITAR PRATOS
            with tab_listar_pratos:
                registros_pratos = carregar_pratos_planilha()
                if not registros_pratos:
                    st.info("Nenhum prato cadastrado até o momento.")
                else:
                    sheet_pratos = conectar_gsheets().worksheet("Pratos")

                    for index, reg in enumerate(registros_pratos):
                        linha_planilha = index + 2

                        nome_prato = str(reg.get("Prato", reg.get("prato", reg.get("ID_Prato", "")))).strip()
                        categoria_prato = str(reg.get("Categoria", reg.get("categoria", "Geral"))).strip()
                        ativo_prato = str(reg.get("Ativo", reg.get("ativo", "TRUE"))).strip().upper() == "TRUE"

                        status_emoji = "🟢 Ativo" if ativo_prato else "🔴 Inativo"

                        with st.expander(f"🍲 {nome_prato} — [{categoria_prato}] {status_emoji}"):
                            with st.form(f"form_editar_prato_{index}"):
                                col_p1, col_p2 = st.columns(2)
                                with col_p1:
                                    novo_nome_prato = st.text_input("Nome do Prato", value=nome_prato, key=f"edit_prato_nome_{index}")
                                with col_p2:
                                    nova_cat_prato = st.text_input("Categoria", value=categoria_prato, key=f"edit_prato_cat_{index}")
                                
                                novo_status_prato = st.checkbox("Prato Ativo (Exibir no Formulário)", value=ativo_prato, key=f"edit_prato_ativo_{index}")

                                col_btn_p1, col_btn_p2 = st.columns(2)
                                with col_btn_p1:
                                    btn_salvar_prato = st.form_submit_button("💾 SALVAR", use_container_width=True)
                                with col_btn_p2:
                                    btn_excluir_prato = st.form_submit_button("🗑️ EXCLUIR", use_container_width=True)

                                if btn_salvar_prato:
                                    try:
                                        sheet_pratos.update_cell(linha_planilha, 1, novo_nome_prato.strip())
                                        sheet_pratos.update_cell(linha_planilha, 2, nova_cat_prato.strip())
                                        sheet_pratos.update_cell(linha_planilha, 3, "TRUE" if novo_status_prato else "FALSE")

                                        st.cache_data.clear()
                                        st.success(f"✅ Prato **{novo_nome_prato}** atualizado!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Erro ao atualizar prato: {e}")

                                if btn_excluir_prato:
                                    try:
                                        sheet_pratos.delete_rows(linha_planilha)
                                        st.cache_data.clear()
                                        st.success(f"🗑️ Prato **{nome_prato}** removido!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Erro ao excluir prato: {e}")

            # TAB: CRIAR PRATO
            with tab_criar_prato:
                with st.form("form_novo_prato"):
                    col_np1, col_np2 = st.columns(2)
                    with col_np1:
                        nome_novo_prato = st.text_input("Nome do Prato", placeholder="ex: Strogonoff de Frango")
                    with col_np2:
                        cat_nova_prato = st.text_input("Categoria", placeholder="ex: Proteínas / Acompanhamentos")

                    btn_cadastrar_prato = st.form_submit_button("CADASTRAR PRATO", use_container_width=True)

                    if btn_cadastrar_prato:
                        nome_limpo_prato = nome_novo_prato.strip()
                        cat_limpa_prato = cat_nova_prato.strip() if cat_nova_prato.strip() else "Geral"

                        if not nome_limpo_prato:
                            st.warning("⚠️ O nome do prato é obrigatório.")
                        else:
                            try:
                                registros_pratos_atuais = carregar_pratos_planilha()
                                ja_existe = any(
                                    str(r.get("Prato", r.get("prato", r.get("ID_Prato", "")))).strip().lower() == nome_limpo_prato.lower()
                                    for r in registros_pratos_atuais
                                )

                                if ja_existe:
                                    st.error(f"❌ O prato **{nome_limpo_prato}** já está cadastrado.")
                                else:
                                    sheet_pratos = conectar_gsheets().worksheet("Pratos")
                                    nova_linha = [nome_limpo_prato, cat_limpa_prato, "TRUE"]
                                    sheet_pratos.append_row(nova_linha)

                                    st.cache_data.clear()
                                    st.success(f"✅ Prato **{nome_limpo_prato}** cadastrado com sucesso!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao cadastrar prato na planilha: {e}")