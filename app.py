import streamlit as st
import os
import streamlit.components.v1 as components
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

# Captura clique de saída via Query Param
if "logout" in st.query_params:
    st.session_state["usuario_logado"] = None
    st.session_state["perfil_logado"] = None
    st.session_state["permissoes_usuario"] = None
    st.session_state["aba_ativa"] = "inicio"
    try:
        st.query_params.clear()
    except Exception:
        pass

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = "inicio"

# =========================================================
# 2. ESTILOS CSS FIXOS E ANIMAÇÕES
# =========================================================
st.markdown("""
    <style>
    /* MODO ESCURO FORÇADO */
    html, body, [data-testid="stApp"], .stApp {
        background-color: #121212 !important;
        color: #F8F9FA !important;
    }

    /* OCULTAR ELEMENTOS NATIVOS DO STREAMLIT */
    #MainMenu, header, footer, 
    [data-testid="stFooter"], [data-testid="stHeader"],
    .stDeployButton, div[class*="viewerBadge"], 
    div[class*="styles_viewerBadge"], div[class*="stStatusWidget"],
    a[href*="streamlit.io"], a[href*="github.com"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0px !important;
        pointer-events: none !important;
    }

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

    /* ESTILOS DOS BOTÕES DO RODAPÉ (INJECTADO VIA HTML FRONT-END) */
    .nav-bar-wrapper {
        position: fixed !important;
        bottom: 70px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 360px !important;
        max-width: 95vw !important;
        z-index: 99999999 !important;
        background-color: #B71C1C !important;
        border-radius: 30px !important;
        box-shadow: 0px 8px 25px rgba(0, 0, 0, 0.8) !important;
        border: 2px solid #2D2D2D !important;
        height: 60px !important;
        padding: 4px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        box-sizing: border-box !important;
    }

    .nav-btn {
        flex: 1 !important;
        height: 44px !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        border-radius: 20px !important;
        border: none !important;
        background-color: transparent;
        color: #E0E0E0;
        cursor: pointer;
        transition: all 0.1s ease-in-out;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 2px;
    }

    .nav-btn.active {
        background-color: #FFFFFF !important;
        color: #B71C1C !important;
        font-weight: 800 !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4) !important;
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
# 4. RENDERIZAÇÃO DOS CONTAINERS DAS VIEWS
# =========================================================
c_inicio = st.container(key="view_inicio")
with c_inicio:
    inicio.render()

if st.session_state["usuario_logado"]:
    c_pesagem = st.container(key="view_pesagem")
    with c_pesagem:
        if tem_permissao("pesagem:visualizar"):
            pesagem.render()

    c_historico = st.container(key="view_historico")
    with c_historico:
        if tem_permissao("dashboard:visualizar"):
            historico.render()

    c_config = st.container(key="view_config")
    with c_config:
        if tem_permissao("usuarios:gerenciar") or tem_permissao("pratos:gerenciar"):
            config.render()

# =========================================================
# 5. CÁPSULA DO RODAPÉ EM JAVASCRIPT INSTANTÂNEO (SEM RE-RUNS)
# =========================================================
if st.session_state["usuario_logado"]:
    st.markdown("""
        <div class="nav-bar-wrapper">
            <button id="btn-nav-inicio" class="nav-btn active" onclick="trocarAba('inicio')">Início</button>
            <button id="btn-nav-pesagem" class="nav-btn" onclick="trocarAba('pesagem')">Formulário</button>
            <button id="btn-nav-historico" class="nav-btn" onclick="trocarAba('historico')">Painel</button>
            <button id="btn-nav-config" class="nav-btn" onclick="trocarAba('config')">⚙️</button>
        </div>

        <script>
        function trocarAba(nomeAba) {
            // 1. Alterna visualização dos containers das views instantaneamente
            const abas = ['inicio', 'pesagem', 'historico', 'config'];
            
            abas.forEach(a => {
                const elView = parent.document.querySelector('div[data-testid="stElementContainer"]:has(div.st-key-view_' + a + ')');
                const btnNav = parent.document.getElementById('btn-nav-' + a);
                
                if (elView) {
                    if (a === nomeAba) {
                        elView.style.display = 'block';
                    } else {
                        elView.style.display = 'none';
                    }
                }
                
                if (btnNav) {
                    if (a === nomeAba) {
                        btnNav.classList.add('active');
                    } else {
                        btnNav.classList.remove('active');
                    }
                }
            });
        }
        
        // Garante exibição inicial correta no carregamento
        setTimeout(function() {
            trocarAba('inicio');
        }, 100);
        </script>
    """, unsafe_allow_html=True)