import streamlit as st
import os
from auth import tem_permissao
from views import inicio, pesagem, historico, config

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

# Captura clique de saída via Query Param do HTML sem criar loops
if "logout" in st.query_params:
    st.session_state["usuario_logado"] = None
    st.session_state["perfil_logado"] = None
    st.session_state["permissoes_usuario"] = None
    st.session_state["aba_ativa"] = "inicio"
    try:
        st.query_params.clear()
    except Exception:
        pass

# Estados de sessão
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = "inicio"

# Se NÃO estiver logado, trava na aba inicial
if not st.session_state["usuario_logado"]:
    st.session_state["aba_ativa"] = "inicio"

aba = st.session_state["aba_ativa"]

# =========================================================
# 2. INJEÇÃO DE CSS GLOBAL (OCULTA FOTO DO GITHUB / STREAMLIT BADGE)
# =========================================================
st.markdown("""
    <style>
    /* FORÇAR MODO ESCURO NA ESTRUTURA GLOBAL E REMOVER PADDINGS DO EMBED */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"], .stApp {
        background-color: #121212 !important;
        color: #F8F9FA !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* REMOVE MARGENS E SPACING INTERNO DAS PÁGINAS EM EMBED */
    div[data-testid="stAppViewContainer"] > section {
        padding: 0 !important;
    }

    /* OCULTAR FOTO DO GITHUB, BADGES DO STREAMLIT E RODAPÉS NATIVOS */
    #MainMenu, 
    header, 
    footer, 
    [data-testid="stFooter"], 
    [data-testid="stHeader"],
    .stDeployButton, 
    div[class*="viewerBadge"], 
    div[class*="styles_viewerBadge"], 
    div[class*="stStatusWidget"],
    a[href*="streamlit.io"],
    a[href*="github.com"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0px !important;
        pointer-events: none !important;
    }

    /* Espaçamento do container principal */
    .block-container {
        padding-top: 3.8rem !important;
        padding-bottom: 10.5rem !important; 
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }

    /* BARRA SUPERIOR FIXA NO TOPO */
    .modern-header {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100vw !important;
        height: 52px !important;
        background-color: #B71C1C !important;
        color: #FFFFFF !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 0 16px !important;
        z-index: 999999 !important;
        box-shadow: 0px 4px 14px rgba(0, 0, 0, 0.6) !important;
        border-radius: 0 0 16px 16px !important;
        box-sizing: border-box !important;
    }

    .modern-header-title {
        font-size: 1.15rem;
        font-weight: 800;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* ESTILO DO BOTÃO DE SAIR DENTRO DO CABEÇALHO */
    .btn-header-action {
        background-color: rgba(255, 255, 255, 0.2);
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 12px;
        height: 34px;
        padding: 0 12px;
        font-weight: 700;
        font-size: 0.85rem;
        cursor: pointer;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }

    .btn-header-action:hover {
        background-color: #FFFFFF;
        color: #B71C1C !important;
    }

    /* CÁPSULA TRAVADA NO RODAPÉ */
    div[data-testid="stElementContainer"]:has(div.st-key-nav_bar_container),
    div:has(> div.st-key-nav_bar_container) {
        position: fixed !important;
        bottom: 40px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 360px !important;
        max-width: 95vw !important;
        z-index: 99999999 !important;
    }

    div.st-key-nav_bar_container div[data-testid="stHorizontalBlock"] {
        background-color: #B71C1C !important;
        border-radius: 30px !important;
        box-shadow: 0px 8px 25px rgba(0, 0, 0, 0.8) !important;
        border: 2px solid #2D2D2D !important;
        height: 90px !important;
        padding: 4px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 0 !important;
    }

    div.st-key-nav_bar_container div[data-testid="stColumn"],
    div.st-key-nav_bar_container div[data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0% !important;
        width: 100% !important;
        min-width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        position: relative !important;
    }

    div.st-key-nav_bar_container div[data-testid="stColumn"]:not(:last-child)::after,
    div.st-key-nav_bar_container div[data-testid="stHorizontalBlock"] > div:not(:last-child)::after {
        content: "" !important;
        position: absolute !important;
        right: 0 !important;
        top: 25% !important;
        height: 50% !important;
        width: 1px !important;
        background-color: rgba(255, 255, 255, 0.2) !important;
        pointer-events: none !important;
    }

    div.st-key-nav_bar_container div[data-testid="stElementContainer"],
    div.st-key-nav_bar_container div[data-testid="stButton"] {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    div.st-key-nav_bar_container button {
        width: 90% !important;
        height: 44px !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        border-radius: 20px !important;
        border: none !important;
        margin: 0 auto !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease-in-out !important;
    }

    div.st-key-nav_bar_container button *,
    div.st-key-nav_bar_container button div,
    div.st-key-nav_bar_container button p,
    div.st-key-nav_bar_container button [data-testid="stMarkdownContainer"] {
        margin: 0 auto !important;
        padding: 0 !important;
        text-align: center !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
    }

    div.st-key-nav_bar_container button[kind="secondary"] {
        background-color: transparent !important;
        color: #E0E0E0 !important;
        box-shadow: none !important;
    }

    div.st-key-nav_bar_container button[kind="secondary"]:hover {
        background-color: #FFFFFF !important;
        color: #B71C1C !important;
        cursor: pointer !important;
    }

    div.st-key-nav_bar_container button[kind="secondary"]:hover * {
        color: #B71C1C !important;
    }

    div.st-key-nav_bar_container button[kind="primary"],
    div.st-key-nav_bar_container button[kind="primary"]:hover,
    div.st-key-nav_bar_container button[kind="primary"]:focus {
        background-color: #FFFFFF !important;
        color: #B71C1C !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4) !important;
    }

    div.st-key-nav_bar_container button[kind="primary"] *,
    div.st-key-nav_bar_container button[kind="primary"] p {
        color: #B71C1C !important;
        font-weight: 800 !important;
    }

    label {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #E0E0E0 !important;
        margin-bottom: 0.2rem !important;
    }

    div[data-baseweb="input"] input, div[data-baseweb="select"], textarea {
        font-size: 1.05rem !important;
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] * {
        color: #FFFFFF !important;
        background-color: #1E1E1E !important;
    }

    .section-header {
        font-size: 0.95rem;
        font-weight: 800;
        color: #FF5252;
        border-bottom: 2px solid #B71C1C;
        padding-bottom: 4px;
        margin-top: 15px;
        margin-bottom: 12px;
        text-transform: uppercase;
    }

    [data-testid="stMetricValue"] {
        color: #FF5252 !important;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 3. BARRA SUPERIOR FIXA
# =========================================================
if st.session_state["usuario_logado"]:
    btn_html = '<a href="?logout=true" target="_self" class="btn-header-action">Sair</a>'
else:
    btn_html = '<span onclick="window.location.reload();" style="cursor:pointer; font-size:1.2rem; color:#fff;" title="Recarregar">🔄</span>'

st.markdown(f"""
    <div class="modern-header">
        <div class="modern-header-title">
            <span>Don Max Buffet</span>
        </div>
        <div>
            {btn_html}
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# 4. ROTEAMENTO DE ABAS COM TRAVA DE PERMISSÃO
# =========================================================
if aba == "inicio":
    inicio.render()
elif aba == "pesagem" and st.session_state["usuario_logado"]:
    if tem_permissao("pesagem:visualizar"):
        pesagem.render()
    else:
        st.error("⛔ Seu perfil não tem permissão para acessar a tela de Pesagem.")
elif aba == "historico" and st.session_state["usuario_logado"]:
    if tem_permissao("dashboard:visualizar"):
        historico.render()
    else:
        st.error("⛔ Seu perfil não tem permissão para acessar o Dashboard.")
elif aba == "config" and st.session_state["usuario_logado"]:
    config.render()

# =========================================================
# 5. RODAPÉ FIXO (CÁPSULA)
# =========================================================
if st.session_state["usuario_logado"]:
    nav_bar = st.container(key="nav_bar_container")
    with nav_bar:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tipo = "primary" if aba == "inicio" else "secondary"
            if st.button("Início", key="btn_inicio", type=tipo):
                st.session_state["aba_ativa"] = "inicio"
                st.rerun()
        with c2:
            tipo = "primary" if aba == "pesagem" else "secondary"
            if st.button("Formulário", key="btn_pesagem", type=tipo):
                if tem_permissao("pesagem:visualizar"):
                    st.session_state["aba_ativa"] = "pesagem"
                    st.rerun()
                else:
                    st.warning("Acesso restrito ao formulário.")
        with c3:
            tipo = "primary" if aba == "historico" else "secondary"
            if st.button("Painel", key="btn_historico", type=tipo):
                if tem_permissao("dashboard:visualizar"):
                    st.session_state["aba_ativa"] = "historico"
                    st.rerun()
                else:
                    st.warning("Acesso restrito ao painel.")
        with c4:
            tipo = "primary" if aba == "config" else "secondary"
            if st.button("⚙️", key="btn_config", type=tipo):
                st.session_state["aba_ativa"] = "config"
                st.rerun()