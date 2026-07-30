import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def conectar_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(credentials).open("Planilha Don Max")

@st.cache_data(ttl=300)
def carregar_dados_painel():
    try:
        sheet = conectar_gsheets().worksheet("Lancamentos_Diarios")
        return sheet.get_all_records()
    except Exception:
        return []

def render():
    st.markdown("<div class='section-header'>📊 PAINEL DE CONTROLE DE DESCARTE</div>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([0.7, 0.3])
    with col_b:
        if st.button("🔄 Recarregar Dados"):
            st.cache_data.clear()
            st.rerun()

    dados = carregar_dados_painel()
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df.tail(10).iloc[::-1], use_container_width=True, hide_index=True)
        st.markdown("---")
        total_descarte = df['Descarte Total'].sum() if 'Descarte Total' in df.columns else 0
        st.metric("Descarte Acumulado (kg)", f"{total_descarte:.2f} kg")
    else:
        st.info("Nenhum registro encontrado na planilha ainda.")