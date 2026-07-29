import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA (Layout Mobile & Identidade Visual)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Don Max - Buffet",
    page_icon="🍲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização CSS para botões grandes e amigáveis para a cozinha
st.markdown("""
    <style>
    .main { padding: 1rem; }
    .stButton>button {
        width: 100%;
        height: 3.5rem;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        background-color: #D32F2F !important;
        color: white !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="input"] {
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. CONEXÃO COM O GOOGLE SHEETS
# ---------------------------------------------------------
@st.cache_resource
def conectar_gsheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Busca as credenciais salvas nos segredos do Streamlit
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(credentials)
    # Abre a planilha pelo nome exato
    sheet = client.open("Planilha Don Max").worksheet("Lancamentos_Diarios")
    return sheet

# ---------------------------------------------------------
# 3. CABEÇALHO COM LOGO DESTAQUE
# ---------------------------------------------------------
# Exibe a logo centralizada e do tamanho que você quiser!
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    # Substitua pelo link da sua logo ou caminho do arquivo local 'logo.png'
    st.image("https://www.appsheet.com:443/fsimage.png?appid=33166895-21f5-4355-9589-9a260ced39c5#view=Inicio", use_container_width=True)

st.markdown("<h3 style='text-align: center; color: #333;'>Controle Diário de Pesagem</h3>", unsafe_allow_html=True)
st.write("---")

# ---------------------------------------------------------
# 4. FORMULÁRIO DE PESAGEM PARA A COZINHA
# ---------------------------------------------------------
with st.form("form_pesagem", clear_on_submit=True):
    st.subheader("📋 Novo Lançamento")

    # Linha 1: Data e Responsável
    data_sel = st.date_input("Data do Serviço", value=date.today())
    responsavel = st.text_input("Responsável pelo Turno/Buffet", placeholder="Ex: João")
    clientes = st.number_input("Clientes Atendidos no Dia", min_value=0, step=1, value=0)

    st.markdown("---")

    # Linha 2: Prato
    pratos_lista = [
        "Arroz", "Feijão", "Barreado", "Carne 1", "Carne 2",
        "Massa", "Guarnição 1", "Guarnição 2", "Saladas", "Sobremesas",
        "Outro 1", "Outro 2"
    ]
    prato_sel = st.selectbox("Selecione a Preparação/Prato", pratos_lista)

    st.markdown("---")
    st.caption("⚖️ Medições da Balança (em Quilogramas)")

    # Linha 3: Pesagens divididas em 2 colunas
    col1, col2 = st.columns(2)
    with col1:
        prod_inicial = st.number_input("Produção Inicial (kg)", min_value=0.0, step=0.1, format="%.2f")
        reposicao = st.number_input("Reposição Total (kg)", min_value=0.0, step=0.1, format="%.2f")
        sobra_limpa = st.number_input("Sobra Limpa (kg)", min_value=0.0, step=0.1, format="%.2f")

    with col2:
        sobra_buffet = st.number_input("Sobra Buffet (kg)", min_value=0.0, step=0.1, format="%.2f")
        descarte = st.number_input("Descarte Total (kg)", min_value=0.0, step=0.1, format="%.2f")

    observacoes = st.text_area("Observações (Opcional)", placeholder="Ex: Carne sobrou por conta da chuva...")

    # Botão Grande de Salvar
    btn_salvar = st.form_submit_button("💾 SALVAR PESAGEM")

    if btn_salvar:
        if not responsavel:
            st.error("⚠️ Por favor, informe o nome do Responsável antes de salvar.")
        else:
            try:
                sheet = conectar_gsheets()
                
                # Monta a linha para inserir na planilha
                nova_linha = [
                    str(data_sel),
                    responsavel,
                    int(clientes),
                    prato_sel,
                    float(prod_inicial),
                    float(reposicao),
                    float(sobra_limpa),
                    float(sobra_buffet),
                    float(descarte),
                    observacoes
                ]

                sheet.append_row(nova_linha)
                st.success(f"✅ Lançamento do **{prato_sel}** salvo com sucesso no Google Sheets!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao conectar com a planilha: {e}")