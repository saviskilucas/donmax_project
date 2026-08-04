import streamlit as st
import pandas as pd
from auth import conectar_gsheets, TODAS_PERMISSOES, tem_permissao, buscar_perfis

def cadastrar_usuario(nome, usuario, senha, id_perfil):
    sheet = conectar_gsheets().worksheet("Usuarios")
    sheet.append_row([nome.strip(), usuario.strip().lower(), str(senha).strip(), id_perfil.strip().lower(), "TRUE"])

def salvar_perfil(id_perfil, nome_perfil, lista_permissoes):
    sheet = conectar_gsheets().worksheet("Perfis")
    registros = sheet.get_all_records()
    
    str_perms = ",".join(lista_permissoes) if "ALL" not in lista_permissoes else "ALL"
    
    linha_existente = None
    for idx, r in enumerate(registros, start=2):
        if str(r.get("ID_Perfil", "")).strip().lower() == id_perfil.lower():
            linha_existente = idx
            break
            
    if linha_existente:
        sheet.update_cell(linha_existente, 2, nome_perfil)
        sheet.update_cell(linha_existente, 3, str_perms)
    else:
        sheet.append_row([id_perfil.lower(), nome_perfil, str_perms])

def render():
    if not tem_permissao("usuarios:gerenciar") and not tem_permissao("perfis:gerenciar"):
        st.error("⛔ Você não tem permissão para acessar esta área do sistema.")
        return

    st.markdown("<div class='section-header'>⚙️ GESTÃO DE USUÁRIOS E PERMISSÕES</div>", unsafe_allow_html=True)
    
    tab_users, tab_perfis = st.tabs(["👤 Usuários Cadastrados", "🛡️ Matriz de Perfis & Permissões"])

    # ---------------------------------------------------------
    # TAB 1: CADASTRO E GERENCIAMENTO DE USUÁRIOS
    # ---------------------------------------------------------
    with tab_users:
        st.markdown("##### Novo Usuário")
        perfis_dict = buscar_perfis()
        opcoes_perfis = {k: v["nome"] for k, v in perfis_dict.items()}

        with st.form("form_novo_usuario"):
            c1, c2 = st.columns(2)
            with c1:
                nome = st.text_input("Nome Completo", placeholder="ex: João Silva")
                usuario = st.text_input("Nome de Usuário", placeholder="ex: joao.silva")
            with c2:
                senha = st.text_input("Senha", type="password")
                id_perfil = st.selectbox("Perfil de Acesso", options=list(opcoes_perfis.keys()), format_func=lambda x: opcoes_perfis[x])
            
            if st.form_submit_button("CADASTRAR USUÁRIO"):
                if nome and usuario and senha:
                    try:
                        cadastrar_usuario(nome, usuario, senha, id_perfil)
                        st.success("✅ Usuário cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                else:
                    st.warning("⚠️ Preencha todos os campos.")

    # ---------------------------------------------------------
    # TAB 2: MATRIZ DE PERMISSÕES PERSONALIZADA
    # ---------------------------------------------------------
    with tab_perfis:
        st.markdown("##### Configurar Permissões por Perfil")
        perfis_dict = buscar_perfis()
        
        perfil_sel = st.selectbox(
            "Selecione o Perfil para Editar ou Criar Novo:",
            options=["[CRIAR NOVO PERFIL]"] + list(perfis_dict.keys()),
            format_func=lambda x: "[➕ Criar Novo Perfil]" if x == "[CRIAR NOVO PERFIL]" else perfis_dict[x]["nome"]
        )

        if perfil_sel == "[CRIAR NOVO PERFIL]":
            id_p_input = st.text_input("ID do Perfil (sem espaços)", placeholder="ex: supervisor_salão").strip().lower().replace(" ", "_")
            nome_p_input = st.text_input("Nome de Exibição do Perfil", placeholder="ex: Supervisor de Salão")
            perms_atuais = []
        else:
            id_p_input = perfil_sel
            nome_p_input = st.text_input("Nome de Exibição do Perfil", value=perfis_dict[perfil_sel]["nome"])
            perms_atuais = perfis_dict[perfil_sel]["permissoes"]

        st.markdown("---")
        st.markdown("###### Selecione as Permissões Ativas:")
        
        is_all = "ALL" in perms_atuais
        chk_all = st.checkbox("🔥 ACESSO TOTAL (Super Admin)", value=is_all)
        
        novas_permissoes = []
        if chk_all:
            novas_permissoes = ["ALL"]
        else:
            for chave, desc in TODAS_PERMISSOES.items():
                marcado = st.checkbox(desc, value=(chave in perms_atuais))
                if marcado:
                    novas_permissoes.append(chave)

        if st.button("💾 SALVAR CONFIGURAÇÕES DO PERFIL", use_container_width=True):
            if id_p_input and nome_p_input:
                salvar_perfil(id_p_input, nome_p_input, novas_permissoes)
                st.success("✅ Perfil e permissões salvos com sucesso!")
                st.rerun()
            else:
                st.warning("⚠️ Preencha o ID e o Nome do perfil.")