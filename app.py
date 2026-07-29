import streamlit as st

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA (LAYOUT MOBILE COMPACTO)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Don Max - Buffet",
    page_icon="🍲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Injeção de CSS para experiência 100% Mobile
st.markdown("""
    <style>
    /* 1. Reduzir as margens superiores e laterais para aproveitar a tela do celular */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 500px !important; /* Força o visual compacto de celular */
    }

    /* 2. Esconder a barra superior e o menu padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* 3. Aumentar os rótulos/títulos dos campos para facilitar a leitura */
    label {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #222222 !important;
    }

    /* 4. Estilizar os campos de entrada de números (Inputs) */
    div[data-baseweb="input"] input {
        font-size: 1.2rem !important;
        padding: 10px !important;
        border-radius: 8px !important;
    }

    /* 5. Deixar os botões de + e - dos números maiores */
    div[data-baseweb="input"] button {
        width: 40px !important;
        height: 40px !important;
    }

    /* 6. Botão Principal de SALVAR (Destaque Gigante Vermelho) */
    .stButton > button {
        width: 100% !important;
        height: 3.8rem !important;
        font-size: 1.25rem !important;
        font-weight: bold !important;
        background-color: #D32F2F !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0px 4px 10px rgba(211, 47, 47, 0.3) !important;
        margin-top: 1rem !important;
    }

    /* 7. Caixas de alertas e mensagens bonitas */
    .stAlert {
        border-radius: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)