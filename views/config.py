import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def conectar_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(credentials).open("Planilha Don Max")

def buscar_pratos():
    try:
        sheet = conectar_gsheets().worksheet("Alimentos")
        registros = sheet.get_all_records()
        pratos = [str(r.get("Prato", "")).strip() for r in registros if r.get("Prato")]
        return [p for p in pratos if p]
    except Exception:
        return []

def adicionar_prato(nome_prato):
    sheet = conectar_gsheets().worksheet("Alimentos")
    sheet.append_row([nome_prato.strip()])

def remover_prato(nome_prato):
    sheet = conectar_gsheets().worksheet("Alimentos")
    cell = sheet.find(nome_prato)
    if cell:
        sheet.delete_rows(cell.row)

def render():
    st.markdown("<div class='section-header'>⚙️ CONFIGURAÇÕES E ALIMENTOS</div>", unsafe_allow_html=True)
    
    tab_alimentos, tab_sistema = st.tabs(["🍲 Cadastrar Pratos", "⚙️ Sistema"])
    
    with tab_alimentos:
        st.write("Gerencie os pratos disponíveis no formulário de pesagem:")
        
        with st.form("form_add_prato"):
            novo_prato = st.text_input("Novo Prato / Preparação", placeholder="Ex: Cupim Assado")
            btn_add = st.form_submit_button("➕ ADICIONAR PRATO")
            
            if btn_add:
                if not novo_prato.strip():
                    st.warning("⚠️ Digite o nome do prato antes de adicionar.")
                else:
                    try:
                        adicionar_prato(novo_prato)
                        st.cache_data.clear()
                        st.success(f"✅ Prato **{novo_prato.strip()}** cadastrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao cadastrar prato: {e}")

        st.markdown("---")
        st.write("📋 **Pratos Cadastrados Atualizados:**")
        pratos_atuais = buscar_pratos()
        
        if pratos_atuais:
            prato_para_remover = st.selectbox("Selecione para remover", pratos_atuais)
            if st.button("🗑️ Remover Prato Selecionado"):
                try:
                    remover_prato(prato_para_remover)
                    st.cache_data.clear()
                    st.success(f"🗑️ Prato **{prato_para_remover}** removido!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao remover prato: {e}")
        else:
            st.info("Nenhum prato cadastrado na aba 'Alimentos'.")

    with tab_sistema:
        st.markdown("**Don Max Buffet v1.0**\n*Sistema Integrado de Controle de Pesagens*\n\n---\n\n**Instruções para a Cozinha:**\n1. Realize as pesagens sempre ao final do turno.\n2. Certifique-se de zerar a tara da balança.\n3. Dúvidas ou problemas falar com a gerência.")
        
        if st.button("🔄 Limpar Cache Geral"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache limpo com sucesso!")