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
# 3. GERENCIAMENTO DE ESTADO DA NAVEGAÇÃO
# =========================================================
if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = "Pesagem"

# =========================================================
# 4. INJEÇÃO DE CSS CUSTOMIZADO (DESIGN IDÊNTICO AO APPSHEET)
# =========================================================
st.markdown("""
    <style>
    /* Configuração da Tela Mobile */
    html, body, [data-testid="stApp"], .stApp {
        background-color: #F4F5F7 !important;
    }

    /* Trava o conteúdo para não ficar oculto atrás das barras fixas */
    .block-container {
        padding-top: 3.8rem !important;
        padding-bottom: 5.5rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }

    /* Ocultar elementos nativos do Streamlit */
    #MainMenu, header, .stDeployButton, footer {
        display: none !important;
    }

    /* BARRA SUPERIOR ESTILO APPSHEET (VERMELHO DON MAX) */
    .appsheet-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        width: 100%;
        height: 52px;
        background-color: #D32F2F;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 16px;
        z-index: 999999;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.2);
    }

    .appsheet-header-title {
        font-size: 1.15rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .appsheet-header-icons {
        display: flex;
        gap: 15px;
        font-size: 1.2rem;
        cursor: pointer;
    }

    /* ESTILIZAÇÃO DOS FORMULÁRIOS E INPUTS */
    label {
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: #333333 !important;
        margin-bottom: 0.2rem !important;
    }

    div[data-baseweb="input"] input, div[data-baseweb="select"] {
        font-size: 1.1rem !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        background-color: #FFFFFF !important;
    }

    /* Botões de soma/subtração dos inputs numéricos */
    div[data-baseweb="input"] button {
        width: 36px !important;
        height: 36px !important;
    }

    /* Botão Principal - Salvar */
    .stButton > button {
        width: 100% !important;
        height: 3.5rem !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        background-color: #D32F2F !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0px 3px 8px rgba(211, 47, 47, 0.3) !important;
        margin-top: 0.8rem !important;
    }

    .stButton > button:active {
        background-color: #B71C1C !important;
    }

    /* Títulos de Seção */
    .section-header {
        font-size: 1rem;
        font-weight: bold;
        color: #D32F2F;
        border-bottom: 2px solid #D32F2F;
        padding-bottom: 4px;
        margin-top: 15px;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* BARRA FIXA INFERIOR (TAB BAR IGUAL AO APPSHEET) */
    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        height: 56px !important;
        background-color: #D32F2F !important; /* Cor da barra inferior do AppSheet */
        box-shadow: 0px -2px 10px rgba(0, 0, 0, 0.15) !important;
        z-index: 999999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-around !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Botões de abas dentro do rodapé */
    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) div[data-testid="column"] {
        padding: 0 !important;
        margin: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) button {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 1.2rem !important;
        height: 56px !important;
        border-radius: 0px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) button:hover {
        color: #FFFFFF !important;
    }

    /* Destaque da aba selecionada no estilo AppSheet (fundo mais escuro ou borda superior branca) */
    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) button.tab-active {
        color: #FFFFFF !important;
        background-color: rgba(0, 0, 0, 0.15) !important;
        border-top: 3px solid #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 5. CONEXÃO COM O GOOGLE SHEETS
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
# 6. CABEÇALHO FIXO SUPERIOR NO ESTILO APPSHEET
# =========================================================
st.markdown(f"""
    <div class="appsheet-header">
        <div class="appsheet-header-title">
            <span>☰</span>
            <span>Don Max Buffet</span>
        </div>
        <div class="appsheet-header-icons">
            <span>🔍</span>
            <span onclick="window.location.reload();">🔄</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# 7. CONTEÚDO DAS ABAS NAVEGÁVEIS
# =========================================================

# --- ABA 1: FORMULÁRIO DE PESAGEM ---
if st.session_state["aba_ativa"] == "Pesagem":
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

# --- ABA 2: HISTÓRICO DA PLANILHA ---
elif st.session_state["aba_ativa"] == "Histórico":
    st.markdown("<div class='section-header'>📊 ÚLTIMOS LANÇAMENTOS</div>", unsafe_allow_html=True)
    
    try:
        sheet = conectar_gsheets()
        dados = sheet.get_all_records()
        
        if dados:
            df = pd.DataFrame(dados)
            df_recente = df.tail(10).iloc[::-1]
            
            st.dataframe(
                df_recente,
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            total_descarte = df['Descarte Total'].sum() if 'Descarte Total' in df.columns else 0
            st.metric("Descarte Acumulado (kg)", f"{total_descarte:.2f} kg")
        else:
            st.info("Nenhum registro encontrado na planilha ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Sheets: {e}")

# --- ABA 3: CONFIGURAÇÕES / SOBRE ---
elif st.session_state["aba_ativa"] == "Config":
    st.markdown("<div class='section-header'>⚙️ CONFIGURAÇÕES</div>", unsafe_allow_html=True)
    
    st.markdown("""
        **Don Max Buffet v1.0**  
        *Sistema Integrado de Controle de Pesagens*
        
        ---
        
        **Instruções para a Cozinha:**
        1. Realize as pesagens sempre ao final do turno.
        2. Certifique-se de zerar a tara da balança.
        3. Dúvidas ou problemas falar com a gerência.
    """)
    
    if st.button("🔄 Atualizar Conexão com a Planilha"):
        st.cache_resource.clear()
        st.success("Conexão atualizada com sucesso!")

# =========================================================
# 8. RODAPÉ FIXO DE NAVEGAÇÃO EM ÍCONES (IDÊNTICO AO APPSHEET)
# =========================================================
col_nav1, col_nav2, col_nav3 = st.columns(3)

with col_nav1:
    btn_p = st.button("📅\nFormulário", key="nav_pesagem", use_container_width=True)
    if btn_p:
        st.session_state["aba_ativa"] = "Pesagem"
        st.rerun()

with col_nav2:
    btn_h = st.button("📋\nHistórico", key="nav_historico", use_container_width=True)
    if btn_h:
        st.session_state["aba_ativa"] = "Histórico"
        st.rerun()

with col_nav3:
    btn_c = st.button("⚙️\nOpções", key="nav_config", use_container_width=True)
    if btn_c:
        st.session_state["aba_ativa"] = "Config"
        st.rerun()