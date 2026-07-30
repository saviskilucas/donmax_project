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

# Gerenciamento de Estado da Aba Ativa (Padrão: Início)
if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = "inicio"

# =========================================================
# 2. INJEÇÃO DE CSS (MODO ESCURO + CÁPSULA COM BOTÕES NATIVOS)
# =========================================================
st.markdown("""
    <style>
    /* MODO ESCURO FORÇADO */
    html, body, [data-testid="stApp"], .stApp {
        background-color: #121212 !important;
        color: #F8F9FA !important;
    }

    /* Recuo inferior para rolar o conteúdo sem cobrir */
    .block-container {
        padding-top: 3.8rem !important;
        padding-bottom: 9.5rem !important; 
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }

    /* Ocultar elementos padrão do Streamlit */
    #MainMenu, header, .stDeployButton, footer, [data-testid="stFooter"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* TRANSIÇÃO SUAVE */
    .main-content-animated {
        animation: fadeIn 0.2s ease-out forwards;
    }

    @keyframes fadeIn {
        from { opacity: 0.3; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* BARRA SUPERIOR FIXA */
    .modern-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        width: 100vw;
        height: 52px;
        background-color: #B71C1C;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 18px;
        z-index: 99999 !important;
        box-shadow: 0px 4px 14px rgba(0, 0, 0, 0.6);
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
       ESTILIZAÇÃO DO CONTAINER DO RODAPÉ (CÁPSULA VERMELHA)
       ========================================================= */
    div[data-testid="stHorizontalBlock"]:has(button[key^="btn_nav_"]) {
        position: fixed !important;
        bottom: 80px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 360px !important;
        max-width: 95vw !important;
        height: 60px !important;
        background-color: #B71C1C !important;
        border-radius: 30px !important;
        box-shadow: 0px 8px 25px rgba(0, 0, 0, 0.7) !important;
        border: 2px solid #2D2D2D !important;
        z-index: 9999999 !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-around !important;
        padding: 0 4px !important;
    }

    /* Remove margens internas das colunas dentro da cápsula */
    div[data-testid="stHorizontalBlock"]:has(button[key^="btn_nav_"]) > div {
        flex: 1 1 0% !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex !important;
        justify-content: center !important;
    }

    /* Estilo padrão dos 4 botões da barra */
    div[data-testid="stHorizontalBlock"]:has(button[key^="btn_nav_"]) button {
        width: 100% !important;
        height: 44px !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 20px !important;
        color: #E0E0E0 !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 2px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* Botão selecionado / Ativo (Caixinha Branca em Destaque) */
    div[data-testid="stHorizontalBlock"]:has(button[key^="btn_nav_"]) button.btn-active-tab {
        background-color: #FFFFFF !important;
        color: #B71C1C !important;
        font-weight: 800 !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.4) !important;
    }

    /* CAMPOS DO FORMULÁRIO (MODO ESCURO) */
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

    .stButton > button {
        width: 100% !important;
        height: 3.5rem !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        background-color: #B71C1C !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0px 4px 14px rgba(183, 28, 28, 0.4) !important;
        margin-top: 0.8rem !important;
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
# 5. CONTEÚDO DAS ABAS
# =========================================================
st.markdown("<div class='main-content-animated'>", unsafe_allow_html=True)

aba = st.session_state["aba_ativa"]

if aba == "inicio":
    st.markdown("<div class='section-header'>🔐 ACESSO AO SISTEMA</div>", unsafe_allow_html=True)
    st.write("Insira suas credenciais para acessar o painel de pesagens:")
    
    with st.form("form_login"):
        usuario = st.text_input("Usuário", placeholder="Ex: gerencia")
        senha = st.text_input("Senha", type="password", placeholder="••••••••")
        btn_login = st.form_submit_button("ENTRAR NO SISTEMA")
        
        if btn_login:
            st.info("ℹ️ Login demonstrativo em desenvolvimento. Use os menus abaixo para navegar.")

elif aba == "pesagem":
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
    st.markdown("<div class='section-header'>📊 PAINEL DE CONTROLE DE DESCARTE</div>", unsafe_allow_html=True)
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
    st.markdown("<div class='section-header'>⚙️ CONFIGURAÇÕES DO SISTEMA</div>", unsafe_allow_html=True)
    st.markdown("**Don Max Buffet v1.0**\n*Sistema Integrado de Controle de Pesagens*\n\n---\n\n**Instruções para a Cozinha:**\n1. Realize as pesagens sempre ao final do turno.\n2. Certifique-se de zerar a tara da balança.\n3. Dúvidas ou problemas falar com a gerência.")
    if st.button("🔄 Atualizar Conexão com a Planilha"):
        st.cache_resource.clear()
        st.success("Conexão atualizada com sucesso!")

st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 6. MENU FIXO DE BOTÕES NATIVOS NO RODAPÉ
# =========================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Início", key="btn_nav_inicio"):
        st.session_state["aba_ativa"] = "inicio"
        st.rerun()

with col2:
    if st.button("Formulário", key="btn_nav_pesagem"):
        st.session_state["aba_ativa"] = "pesagem"
        st.rerun()

with col3:
    if st.button("Painel", key="btn_nav_historico"):
        st.session_state["aba_ativa"] = "historico"
        st.rerun()

with col4:
    if st.button("⚙️ Config", key="btn_nav_config"):
        st.session_state["aba_ativa"] = "config"
        st.rerun()

# Aplicação dinâmica da classe da caixinha branca no botão ativo
js_highlight = f"""
    <script>
    setTimeout(function() {{
        const parentDoc = window.parent.document;
        const b1 = parentDoc.querySelector('button[key="btn_nav_inicio"]');
        const b2 = parentDoc.querySelector('button[key="btn_nav_pesagem"]');
        const b3 = parentDoc.querySelector('button[key="btn_nav_historico"]');
        const b4 = parentDoc.querySelector('button[key="btn_nav_config"]');

        [b1, b2, b3, b4].forEach(b => {{ if(b) b.classList.remove('btn-active-tab'); }});

        if ("{aba}" === "inicio" && b1) b1.classList.add('btn-active-tab');
        if ("{aba}" === "pesagem" && b2) b2.classList.add('btn-active-tab');
        if ("{aba}" === "historico" && b3) b3.classList.add('btn-active-tab');
        if ("{aba}" === "config" && b4) b4.classList.add('btn-active-tab');
    }}, 30);
    </script>
"""
st.components.v1.html(js_highlight, height=0)