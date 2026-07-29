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

# Verificar se houve mudança de aba via parâmetros
if "aba" in st.query_params:
    st.session_state["aba_ativa"] = st.query_params["aba"]

# =========================================================
# 4. INJEÇÃO DE CSS CUSTOMIZADO (TOPO E RODAPÉ FIXOS/CONGELADOS)
# =========================================================
st.markdown("""
    <style>
    /* Configuração Geral da Tela Mobile */
    html, body, [data-testid="stApp"], .stApp {
        background-color: #F4F5F7 !important;
    }

    /* Recuo de segurança para o conteúdo rolar entre o topo e o rodapé congelados */
    .block-container {
        padding-top: 4.2rem !important;
        padding-bottom: 5.5rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }

    /* Ocultar elementos padrão do Streamlit */
    #MainMenu, header, .stDeployButton, footer {
        display: none !important;
    }

    /* =========================================================
       1. BARRA SUPERIOR CONGELADA (TOPO)
       ========================================================= */
    .appsheet-header {
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
        padding: 0 16px;
        z-index: 999999 !important;
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
    }

    /* =========================================================
       2. BARRA INFERIOR CONGELADA (RODAPÉ)
       ========================================================= */
    .appsheet-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        width: 100vw;
        height: 60px;
        background-color: #D32F2F;
        color: #FFFFFF;
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: space-around;
        z-index: 999999 !important;
        box-shadow: 0px -2px 8px rgba(0,0,0,0.2);
    }

    .appsheet-footer-button {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: transparent;
        border: none;
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 0.8rem;
        font-weight: 600;
        height: 100%;
        cursor: pointer;
        padding: 0;
        margin: 0;
    }

    .appsheet-footer-button.active {
        color: #FFFFFF !important;
        background-color: rgba(0, 0, 0, 0.2);
        border-top: 3px solid #FFFFFF;
    }

    .appsheet-footer-icon {
        font-size: 1.2rem;
        margin-bottom: 2px;
    }

    /* =========================================================
       3. ESTILIZAÇÃO DOS INPUTS E BOTÕES
       ========================================================= */
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

    div[data-baseweb="input"] button {
        width: 36px !important;
        height: 36px !important;
    }

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

    .section-header {
        font-size: 1rem;
        font-weight: bold;
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
# 6. BARRA SUPERIOR CONGELADA (TOPO ESTILO APPSHEET)
# =========================================================
st.markdown("""
    <div class="appsheet-header">
        <div class="appsheet-header-title">
            <span>☰</span>
            <span>Don Max Buffet</span>
        </div>
        <div class="appsheet-header-icons">
            <span>🔍</span>
            <span onclick="window.location.reload();" style="cursor:pointer;">🔄</span>
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

# --- ABA 3: CONFIGURAÇÕES ---
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
# 8. BARRA INFERIOR CONGELADA (RODAPÉ FIXO GARANTIDO VIA JS)
# =========================================================
active_p = "active" if st.session_state["aba_ativa"] == "Pesagem" else ""
active_h = "active" if st.session_state["aba_ativa"] == "Histórico" else ""
active_c = "active" if st.session_state["aba_ativa"] == "Config" else ""

footer_html = f"""
    <div class="appsheet-footer">
        <button onclick="mudarAba('Pesagem')" class="appsheet-footer-button {active_p}">
            <span class="appsheet-footer-icon">📅</span>
            <span>Formulário</span>
        </button>
        <button onclick="mudarAba('Histórico')" class="appsheet-footer-button {active_h}">
            <span class="appsheet-footer-icon">📋</span>
            <span>Histórico</span>
        </button>
        <button onclick="mudarAba('Config')" class="appsheet-footer-button {active_c}">
            <span class="appsheet-footer-icon">⚙️</span>
            <span>Opções</span>
        </button>
    </div>

    <script>
    function mudarAba(nomeAba) {{
        const url = new URL(window.location.href);
        url.searchParams.set('aba', nomeAba);
        window.location.href = url.toString();
    }}
    </script>
"""

st.markdown(footer_html, unsafe_allow_html=True)