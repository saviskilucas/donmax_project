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

# Gerenciamento de Estado sem recarregamento da URL
if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = "pesagem"

# =========================================================
# 2. INJEÇÃO DE CSS (ANIMAÇÃO DE PÁGINA E DESIGN MOBILE)
# =========================================================
st.markdown("""
    <style>
    /* 1. Configuração de Fundo sem Pistas Escuras */
    html, body, [data-testid="stApp"], .stApp {
        background-color: #F8F9FA !important;
    }

    /* Recuo inferior ajustado para a margem de 80px */
    .block-container {
        padding-top: 3.8rem !important;
        padding-bottom: 7.5rem !important; 
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }

    /* Ocultar elementos nativos do Streamlit */
    #MainMenu, header, .stDeployButton, footer, [data-testid="stFooter"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* =========================================================
       2. ANIMAÇÃO DE TRANSIÇÃO SUAVE ENTRE ABAS (FADE-IN)
       ========================================================= */
    .main-content-animated {
        animation: fadeInSlide 0.25s ease-out forwards;
    }

    @keyframes fadeInSlide {
        from {
            opacity: 0;
            transform: translateY(8px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* =========================================================
       3. BARRA SUPERIOR FIXA
       ========================================================= */
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

    /* =========================================================
       4. BARRA DE MENU NATIVA EM FLUXO ÚNICO (SISTEMA DE COLUNAS)
       ========================================================= */
    div[data-testid="stHorizontalBlock"]:has(button[key^="btn_nav_"]) {
        position: fixed !important;
        bottom: 80px !important; /* SUA CONFIGURAÇÃO DE 80PX */
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 280px !important;
        height: 60px !important;
        background-color: #D32F2F !important;
        border-radius: 30px !important;
        box-shadow: 0px 8px 25px rgba(0, 0, 0, 0.35) !important;
        z-index: 999999 !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-around !important;
        padding: 0 8px !important;
        border: 2px solid #FFFFFF !important;
    }

    div[data-testid="stHorizontalBlock"]:has(button[key^="btn_nav_"]) > div {
        flex: 1 1 0% !important;
        width: 33.33% !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex !important;
        justify-content: center !important;
    }

    div[data-testid="stHorizontalBlock"]:has(button[key^="btn_nav_"]) button {
        width: 70px !important;
        height: 44px !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 18px !important;
        color: rgba(255, 255, 255, 0.8) !important;
        font-size: 1.3rem !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* Botão Selecionado com Caixinha Branca */
    div[data-testid="stHorizontalBlock"]:has(button[key^="btn_nav_"]) button.btn-active-tab {
        background-color: #FFFFFF !important;
        color: #D32F2F !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2) !important;
    }

    /* =========================================================
       5. ESTILIZAÇÃO DOS FORMULÁRIOS
       ========================================================= */
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
# 5. CONTEÚDO DAS ABAS COM ENVOLVET DE ANIMAÇÃO
# =========================================================
st.markdown("<div class='main-content-animated'>", unsafe_allow_html=True)

aba = st.session_state["aba_ativa"]

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

st.markdown("</div>", unsafe_allow_html=True) # Fim do container animado

# =========================================================
# 6. RODAPÉ FIXO COMPACTO (80PX) COM RE-RENDER INSTANTÂNEO
# =========================================================
col_nav1, col_nav2, col_nav3 = st.columns(3)

with col_nav1:
    if st.button("🏠", key="btn_nav_1"):
        st.session_state["aba_ativa"] = "pesagem"
        st.rerun()

with col_nav2:
    if st.button("📋", key="btn_nav_2"):
        st.session_state["aba_ativa"] = "historico"
        st.rerun()

with col_nav3:
    if st.button("👤", key="btn_nav_3"):
        st.session_state["aba_ativa"] = "config"
        st.rerun()

# JS Instantâneo para aplicar a caixinha branca no ícone ativo sem piscar
st.components.v1.html(f"""
    <script>
    setTimeout(function() {{
        const parentDoc = window.parent.document;
        const navContainer = parentDoc.querySelector('div[data-testid="stHorizontalBlock"]:has(button[key^="btn_nav_"])');
        if (navContainer) {{
            const btns = navContainer.querySelectorAll('button');
            btns.forEach(b => b.classList.remove('btn-active-tab'));
            
            if ("{aba}" === "pesagem" && btns[0]) {{
                btns[0].classList.add('btn-active-tab');
            }} else if ("{aba}" === "historico" && btns[1]) {{
                btns[1].classList.add('btn-active-tab');
            }} else if ("{aba}" === "config" && btns[2]) {{
                btns[2].classList.add('btn-active-tab');
            }}
        }}
    }}, 20);
    </script>
""", height=0)