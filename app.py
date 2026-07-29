import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import os

# =========================================================
# 1. CARREGAMENTO DA LOGO LOCAL (PNG)
# =========================================================
NOME_ARQUIVO_LOGO = "logo.png"

# =========================================================
# 2. CONFIGURAÇÃO DA PÁGINA (PWA & MOBILE LAYOUT)
# =========================================================
st.set_page_config(
    page_title="Don Max - Buffet",
    page_icon=NOME_ARQUIVO_LOGO if os.path.exists(NOME_ARQUIVO_LOGO) else "🍲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================================================
# 3. INJEÇÃO DE CSS CUSTOMIZADO PARA INTERFACE DA COZINHA
# =========================================================
st.markdown("""
    <style>
    /* Ajustes gerais de layout mobile */
    html, body, [data-testid="stApp"], .stApp {
        background-color: #FFFFFF !important;
    }

    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 4rem !important; /* Margem estendida para garantir acesso no PWA */
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }

    /* Ocultar cabeçalhos/menus padrão */
    #MainMenu, header, .stDeployButton {
        display: none !important;
    }

    /* Destaque nos rótulos dos campos */
    label {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: #1A1A1A !important;
        margin-bottom: 0.2rem !important;
    }

    /* Inputs numéricos e seletores */
    div[data-baseweb="input"] input, div[data-baseweb="select"] {
        font-size: 1.15rem !important;
        padding: 10px !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="input"] button {
        width: 38px !important;
        height: 38px !important;
    }

    /* Botão Principal - Vermelho Don Max */
    .stButton > button {
        width: 100% !important;
        height: 3.8rem !important;
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        background-color: #D32F2F !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0px 4px 12px rgba(211, 47, 47, 0.35) !important;
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }

    .stButton > button:active {
        background-color: #B71C1C !important;
        transform: scale(0.98);
    }

    .section-header {
        font-size: 1.1rem;
        font-weight: bold;
        color: #D32F2F;
        border-bottom: 2px solid #D32F2F;
        padding-bottom: 4px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 4. FUNÇÃO DE CONEXÃO COM O GOOGLE SHEETS
# =========================================================
@st.cache_resource
def conectar_gsheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(credentials)
    sheet = client.open("Planilha Don Max").worksheet("Lancamentos_Diarios")
    return sheet

# =========================================================
# 5. CABEÇALHO (LOGO E NOME DO RESTAURANTE)
# =========================================================
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    if os.path.exists(NOME_ARQUIVO_LOGO):
        st.image(NOME_ARQUIVO_LOGO, use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center;'>🍲</h1>", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; margin-top: -10px; color: #222;'>Controle de Buffet</h3>", unsafe_allow_html=True)

# =========================================================
# 6. FORMULÁRIO OPERACIONAL DA COZINHA
# =========================================================
with st.form("form_pesagem", clear_on_submit=True):

    st.markdown("<div class='section-header'>1. INFORMAÇÕES DO DIA</div>", unsafe_allow_html=True)
    
    data_sel = st.date_input("Data do Serviço", value=date.today())
    responsavel = st.text_input("Responsável pelo Turno", placeholder="Ex: João Silva")
    clientes = st.number_input("Clientes Atendidos no Dia", min_value=0, step=1, value=0)

    st.markdown("<div class='section-header'>2. PREPARAÇÃO / PRATO</div>", unsafe_allow_html=True)
    
    pratos_lista = [
        "Arroz", "Feijão", "Barreado", "Carne 1", "Carne 2",
        "Massa", "Guarnição 1", "Guarnição 2", "Saladas", "Sobremesas",
        "Outro 1", "Outro 2"
    ]
    prato_sel = st.selectbox("Selecione o Prato", pratos_lista)

    st.markdown("<div class='section-header'>3. MEDIÇÕES DA BALANÇA (KG)</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        prod_inicial = st.number_input("Produção Inicial", min_value=0.0, step=0.1, format="%.2f")
        reposicao = st.number_input("Reposição Total", min_value=0.0, step=0.1, format="%.2f")
        sobra_limpa = st.number_input("Sobra Limpa", min_value=0.0, step=0.1, format="%.2f")

    with col2:
        sobra_buffet = st.number_input("Sobra Buffet", min_value=0.0, step=0.1, format="%.2f")
        descarte = st.number_input("Descarte Total", min_value=0.0, step=0.1, format="%.2f")

    observacoes = st.text_area("Observações (Opcional)", placeholder="Ex: Sobra de carne devido ao tempo chuvoso...")

    btn_salvar = st.form_submit_button("💾 SALVAR PESAGEM")

    # =========================================================
    # 7. LÓGICA DE PROCESSAMENTO E GRAVAÇÃO
    # =========================================================
    if btn_salvar:
        if not responsavel.strip():
            st.error("⚠️ Preencha o nome do Responsável antes de salvar.")
        else:
            try:
                sheet = conectar_gsheets()
                
                nova_linha = [
                    str(data_sel),
                    responsavel.strip(),
                    int(clientes),
                    prato_sel,
                    float(prod_inicial),
                    float(reposicao),
                    float(sobra_limpa),
                    float(sobra_buffet),
                    float(descarte),
                    observacoes.strip()
                ]

                sheet.append_row(nova_linha)
                
                st.success(f"✅ **{prato_sel}** registrado com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Erro ao salvar na planilha: {e}")