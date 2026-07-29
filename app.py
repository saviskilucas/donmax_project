import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import os

# =========================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =========================================================
NOME_ARQUIVO_LOGO = "logo.png"

st.set_page_config(
    page_title="Don Max - Buffet",
    page_icon=NOME_ARQUIVO_LOGO if os.path.exists(NOME_ARQUIVO_LOGO) else "🍲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Gerenciamento da aba via session_state
if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = "pesagem"

# Captura evento de clique nos botões do menu interno
if "aba" in st.query_params:
    st.session_state["aba_ativa"] = st.query_params["aba"]

# =========================================================
# 2. INJEÇÃO DE CSS DA TELA E DO MENU FIXO INTERNO
# =========================================================
st.markdown("""
    <style>
    /* Configuração Geral da Tela Mobile */
    html, body, [data-testid="stApp"], .stApp {
        background-color: #F8F9FA !important;
    }

    .block-container {
        padding-top: 3.8rem !important;
        padding-bottom: 5.0rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }

    /* Ocultar elementos padrão do Streamlit */
    #MainMenu, header, .stDeployButton, footer, [data-testid="stFooter"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* BARRA SUPERIOR FIXA */
    .modern-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        width: 100vw;
        height: 52px;
        background-color: #D32F2F;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 18px;
        z-index: 99999 !important;
        box-shadow: 0px 4px 12px rgba(211, 47, 47, 0.25);
        border-radius: 0 0 16px 16px;
    }

    .modern-header-title {
        font-size: 1.15rem;
        font-weight: 800;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* MENU FLUTUANTE FIXO NO MEIO DA TELA (INJETADO NATIVAMENTE) */
    .middle-navbar-internal {
        position: fixed !important;
        bottom: 15px !important; /* Trava a 15px do rodapé da tela */
        left: 50% !important;
        transform: translateX(-50%) !important; /* Centraliza na horizontal */
        width: 280px !important;
        height: 60px !important;
        background-color: #D32F2F !important;
        border-radius: 30px !important;
        box-shadow: 0px 8px 25px rgba(0, 0, 0, 0.4) !important;
        z-index: 999999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-around !important;
        padding: 0 10px !important;
        border: 2px solid #FFFFFF !important;
    }

    .nav-btn-int {
        width: 70px;
        height: 44px;
        background: transparent;
        border: none;
        border-radius: 18px;
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.3rem;
        text-decoration: none !important;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }

    .nav-btn-int.active {
        background-color: #FFFFFF !important;
        color: #D32F2F !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2) !important;
    }

    /* CAMPOS DO FORMULÁRIO */
    label {
        font-size: 0.98rem !important;
        font-weight: 700 !important;
        color: #2D3748 !important;
        margin-bottom: 0.2rem !important;
    }

    div[data-baseweb="input"] input, div[data-baseweb="select"] {
        font-size: 1.05rem !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        background-color: #FFFFFF !important;
    }

    .stButton > button {
        width: 100% !important;
        height: 3.5rem !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        background-color: #D32F2F !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0px 4px 12px rgba(211, 47, 47, 0.3) !important;
        margin-top: 0.8rem !important;
    }

    .section-header {
        font-size: 0.95rem;
        font-weight: 800;
        color: #D32F2F;
        border-bottom: 2px solid #D32F2F;
        padding-bottom: 4px;
        margin-top: 15px;
        margin-bottom: 12px;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 3. CONEXÃO GOOGLE SHEETS
# =========================================================
@st.cache_resource
def conectar_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(credentials)
    return client.open("Planilha Don Max").worksheet("Lancamentos_Diarios")

# =========================================================
# 4. BARRA SUPERIOR FIXA
# =========================================================
st.markdown("""
    <div class="modern-header">
        <div class="modern-header-title">
            <span>Don Max Buffet</span>
        </div>
        <div>
            <span onclick="window.location.reload();" style="cursor:pointer;">🔄</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# 5. BARRA DE MENU NO MEIO DA TELA (INJETADA NO PYTHON)
# =========================================================
aba = st.session_state["aba_ativa"]
act_p = "active" if aba == "pesagem" else ""
act_h = "active" if aba == "historico" else ""
act_c = "active" if aba == "config" else ""

st.markdown(f"""
    <div class="middle-navbar-internal">
        <a href="?aba=pesagem" target="_self" class="nav-btn-int {act_p}">🏠</a>
        <a href="?aba=historico" target="_self" class="nav-btn-int {act_h}">📋</a>
        <a href="?aba=config" target="_self" class="nav-btn-int {act_c}">👤</a>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# 6. EXIBIÇÃO DAS ABAS
# =========================================================
if aba == "pesagem":
    with st.form("form_pesagem", clear_on_submit=True):
        st.markdown("<div class='section-header'>1. INFORMAÇÕES DO DIA</div>", unsafe_allow_html=True)
        data_sel = st.date_input("Data do Serviço", value=date.today())
        responsavel = st.text_input("Responsável pelo Turno", placeholder="Ex: João Silva")
        clientes = st.number_input("Clientes Atendidos no Dia", min_value=0, step=1, value=0)

        st.markdown("<div class='section-header'>2. PREPARAÇÃO / PRATO</div>", unsafe_allow_html=True)
        pratos_lista = ["Arroz", "Feijão", "Barreado", "Carne 1", "Carne 2", "Massa", "Guarnição 1", "Guarnição 2", "Saladas", "Sobremesas", "Outro 1", "Outro 2"]
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

        if btn_salvar:
            if not responsavel.strip():
                st.error("⚠️ Preencha o nome do Responsável antes de salvar.")
            else:
                try:
                    sheet = conectar_gsheets()
                    nova_linha = [str(data_sel), responsavel.strip(), int(clientes), prato_sel, float(prod_inicial), float(reposicao), float(sobra_limpa), float(sobra_buffet), float(descarte), observacoes.strip()]
                    sheet.append_row(nova_linha)
                    st.success(f"✅ **{prato_sel}** registrado com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar na planilha: {e}")

elif aba == "historico":
    st.markdown("<div class='section-header'>📊 ÚLTIMOS LANÇAMENTOS</div>", unsafe_allow_html=True)
    try:
        sheet = conectar_gsheets()
        dados = sheet.get_all_records()
        if dados:
            df = pd.DataFrame(dados)
            st.dataframe(df.tail(10).iloc[::-1], use_container_width=True, hide_index=True)
            st.markdown("---")
            total_descarte = df['Descarte Total'].sum() if 'Descarte Total' in df.columns else 0
            st.metric("Descarte Acumulado (kg)", f"{total_descarte:.2f} kg")
        else:
            st.info("Nenhum registro encontrado na planilha ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Sheets: {e}")

elif aba == "config":
    st.markdown("<div class='section-header'>⚙️ CONFIGURAÇÕES</div>", unsafe_allow_html=True)
    st.markdown("**Don Max Buffet v1.0**\n*Sistema Integrado de Controle de Pesagens*\n\n---\n\n**Instruções para a Cozinha:**\n1. Realize as pesagens sempre ao final do turno.\n2. Certifique-se de zerar a tara da balança.\n3. Dúvidas ou problemas falar com a gerência.")
    if st.button("🔄 Atualizar Conexão com a Planilha"):
        st.cache_resource.clear()
        st.success("Conexão atualizada com sucesso!")