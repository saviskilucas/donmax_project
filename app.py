import streamlit as st
import os
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

# Captura clique de saída via Query Param do HTML
if "logout" in st.query_params:
    st.session_state["usuario_logado"] = None
    st.session_state["aba_ativa"] = "inicio"
    st.query_params.clear()
    st.rerun()

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
# 2. INJEÇÃO DE CSS REFINADO (VISUAL MODERNO)
# =========================================================
st.markdown("""
    <style>
    /* 1. MODO ESCURO E FUNDO COM DEGRADÊ SUAVE */
    html, body, [data-testid="stApp"], .stApp {
        background: radial-gradient(circle at top, #1A1A1A 0%, #101010 100%) !important;
        color: #F8F9FA !important;
    }

    /* Espaçamento para o conteúdo rolar limpo atrás das barras fixas */
    .block-container {
        padding-top: 4.2rem !important;
        padding-bottom: 9.5rem !important; 
        padding-left: 0.9rem !important;
        padding-right: 0.9rem !important;
        max-width: 100% !important;
    }

    /* Ocultar elementos nativos do Streamlit */
    #MainMenu, header, .stDeployButton, footer, [data-testid="stFooter"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* 2. BARRA SUPERIOR FIXA (ESTRUTURA INTACTA) */
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
        box-shadow: 0px 4px 18px rgba(0, 0, 0, 0.7) !important;
        border-radius: 0 0 16px 16px !important;
        box-sizing: border-box !important;
    }

    .modern-header-title {
        font-size: 1.15rem;
        font-weight: 800;
        display: flex;
        align-items: center;
        gap: 10px;
        letter-spacing: 0.5px;
    }

    /* BOTÃO APENAS "SAIR" NO CABEÇALHO (SEM A PORTA) */
    .btn-header-action {
        background: rgba(255, 255, 255, 0.18);
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.35);
        border-radius: 20px;
        height: 32px;
        padding: 0 14px;
        font-weight: 700;
        font-size: 0.82rem;
        cursor: pointer;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: all 0.25s ease;
        backdrop-filter: blur(4px);
    }

    .btn-header-action:hover, .btn-header-action:active {
        background-color: #FFFFFF !important;
        color: #B71C1C !important;
        box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.3);
    }

    /* 3. DESIGN DOS INPUTS E CAMPOS DE FORMULÁRIO */
    label {
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        color: #E0E0E0 !important;
        margin-bottom: 0.3rem !important;
        letter-spacing: 0.3px;
    }

    div[data-baseweb="input"] input, div[data-baseweb="select"], textarea {
        font-size: 1rem !important;
        background-color: #1A1A1A !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }

    div[data-baseweb="input"] input:focus, textarea:focus {
        border-color: #FF5252 !important;
        box-shadow: 0 0 8px rgba(255, 82, 82, 0.25) !important;
    }

    div[data-baseweb="select"] * {
        color: #FFFFFF !important;
        background-color: #1A1A1A !important;
    }

    /* 4. DESIGN DAS ABAS (TABS) MODERNAS */
    div[data-testid="stTabs"] button {
        background-color: transparent !important;
        color: #888888 !important;
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 8px 16px !important;
        border: none !important;
        transition: color 0.2s ease !important;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #FF5252 !important;
        border-bottom: 3px solid #FF5252 !important;
    }

    /* 5. BOTÕES PRIMÁRIOS DOS FORMULÁRIOS (SUBMIT) */
    div[data-testid="stForm"] button[type="submit"], 
    div.stButton > button:not([kind="secondary"]) {
        background: linear-gradient(135deg, #C62828 0%, #B71C1C 100%) !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
        border-radius: 14px !important;
        border: 1px solid #E53935 !important;
        box-shadow: 0px 4px 15px rgba(183, 28, 28, 0.35) !important;
        transition: transform 0.15s ease, box-shadow 0.2s ease !important;
        padding: 12px 0 !important;
    }

    div[data-testid="stForm"] button[type="submit"]:active,
    div.stButton > button:not([kind="secondary"]):active {
        transform: scale(0.98) !important;
        box-shadow: 0px 2px 8px rgba(183, 28, 28, 0.2) !important;
    }

    /* 6. ESTILIZAÇÃO DOS CARTOES E SEÇÕES */
    .section-header {
        font-size: 0.9rem;
        font-weight: 800;
        color: #FF5252;
        border-bottom: 2px solid rgba(183, 28, 28, 0.5);
        padding-bottom: 6px;
        margin-top: 15px;
        margin-bottom: 16px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    [data-testid="stForm"] {
        background-color: #181818 !important;
        border: 1px solid #282828 !important;
        border-radius: 18px !important;
        padding: 18px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4) !important;
    }

    /* 7. CÁPSULA TRAVADA NO RODAPÉ (REGRAS INTACTAS) */
    div[data-testid="stElementContainer"]:has(div.st-key-nav_bar_container),
    div:has(> div.st-key-nav_bar_container) {
        position: fixed !important;
        bottom: 30px !important;
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
        height: 60px !important;
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

    [data-testid="stMetricValue"] {
        color: #FF5252 !important;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 3. BARRA SUPERIOR FIXA (COM BOTÃO "SAIR" SEM EMOJI)
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
# 4. ROTEAMENTO DE ABAS
# =========================================================
if aba == "inicio":
    inicio.render()
elif aba == "pesagem" and st.session_state["usuario_logado"]:
    pesagem.render()
elif aba == "historico" and st.session_state["usuario_logado"]:
    historico.render()
elif aba == "config" and st.session_state["usuario_logado"]:
    config.render()

# =========================================================
# 5. RODAPÉ FIXO (REGRAS DE MENU INTACTAS)
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
                st.session_state["aba_ativa"] = "pesagem"
                st.rerun()
        with c3:
            tipo = "primary" if aba == "historico" else "secondary"
            if st.button("Painel", key="btn_historico", type=tipo):
                st.session_state["aba_ativa"] = "historico"
                st.rerun()
        with c4:
            tipo = "primary" if aba == "config" else "secondary"
            if st.button("⚙️", key="btn_config", type=tipo):
                st.session_state["aba_ativa"] = "config"
                st.rerun()