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

# Estado inicial da aba
if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = "inicio"

aba = st.session_state["aba_ativa"]

# =========================================================
# 2. INJEÇÃO DE CSS (MODO ESCURO + HOVER BRANCO + CENTRALIZAÇÃO EXATA)
# =========================================================
st.markdown("""
    <style>
    /* MODO ESCURO FORÇADO EM TUDO */
    html, body, [data-testid="stApp"], .stApp {
        background-color: #121212 !important;
        color: #F8F9FA !important;
    }

    /* Espaçamento para o conteúdo rolar limpo atrás das barras */
    .block-container {
        padding-top: 3.8rem !important;
        padding-bottom: 9.5rem !important; 
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }

    /* Ocultar topo e rodapé padrão do Streamlit */
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
       CÁPSULA TRAVADA NO RODAPÉ COM CENTRALIZAÇÃO ABSOLUTA
       ========================================================= */
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

    /* Cápsula Vermelha que envolve as 4 colunas */
    div.st-key-nav_bar_container div[data-testid="stHorizontalBlock"] {
        background-color: #B71C1C !important;
        border-radius: 30px !important;
        box-shadow: 0px 8px 25px rgba(0, 0, 0, 0.8) !important;
        border: 2px solid #2D2D2D !important;
        height: 60px !important;
        padding: 4px 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 0 !important;
    }

    /* Colunas individuais centralizadas */
    div.st-key-nav_bar_container div[data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        padding: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        position: relative !important;
    }

    /* Divisória vertical sutil entre os botões */
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

    /* ESTILO DOS BOTÕES (INATIVOS) */
    div.st-key-nav_bar_container button {
        width: 100% !important;
        height: 44px !important;
        background-color: transparent !important;
        color: #E0E0E0 !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        border-radius: 20px !important;
        border: none !important;
        box-shadow: none !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* CENTRALIZAÇÃO RIGOROSA DOS ELEMENTOS INTERNOS DOS BOTÕES */
    div.st-key-nav_bar_container button *,
    div.st-key-nav_bar_container button div,
    div.st-key-nav_bar_container button p,
    div.st-key-nav_bar_container button [data-testid="stMarkdownContainer"] {
        margin: 0 !important;
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

    /* HOVER NOS BOTÕES INATIVOS (FUNDO BRANCO + TEXTO VERMELHO) */
    div.st-key-nav_bar_container button:hover:not(.active-btn) {
        background-color: #FFFFFF !important;
        color: #B71C1C !important;
        cursor: pointer !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3) !important;
    }

    div.st-key-nav_bar_container button:hover:not(.active-btn) *,
    div.st-key-nav_bar_container button:hover:not(.active-btn) p {
        color: #B71C1C !important;
    }

    /* BOTÃO SELECIONADO / ATIVO (FUNDO BRANCO FIXO + TEXTO VERMELHO) */
    div.st-key-nav_bar_container button.active-btn,
    div.st-key-nav_bar_container button.active-btn:hover,
    div.st-key-nav_bar_container button.active-btn:focus {
        background-color: #FFFFFF !important;
        color: #B71C1C !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4) !important;
    }

    div.st-key-nav_bar_container button.active-btn *,
    div.st-key-nav_bar_container button.active-btn p {
        color: #B71C1C !important;
        font-weight: 800 !important;
    }

    /* FORMULÁRIO DARK MODE */
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

# =========================================================
# 6. RODAPÉ FIXO DE BOTÕES NATIVOS (SÓ A ENGRENAGEM NO CONFIG)
# =========================================================
nav_bar = st.container(key="nav_bar_container")
with nav_bar:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Início", key="btn_inicio"):
            st.session_state["aba_ativa"] = "inicio"
            st.rerun()
    with c2:
        if st.button("Formulário", key="btn_pesagem"):
            st.session_state["aba_ativa"] = "pesagem"
            st.rerun()
    with c3:
        if st.button("Painel", key="btn_historico"):
            st.session_state["aba_ativa"] = "historico"
            st.rerun()
    with c4:
        if st.button("⚙️", key="btn_config"):
            st.session_state["aba_ativa"] = "config"
            st.rerun()

# SCRIPT QUE APLICA O DESTAQUE BRANCO AO BOTÃO ATIVO
st.components.v1.html(f"""
    <script>
    function updateActiveButton() {{
        const doc = window.parent.document;
        const mapa = {{
            'inicio': 'btn_inicio',
            'pesagem': 'btn_pesagem',
            'historico': 'btn_historico',
            'config': 'btn_config'
        }};
        
        Object.values(mapa).forEach(k => {{
            const btns = doc.querySelectorAll('button[key="' + k + '"]');
            btns.forEach(btn => btn.classList.remove('active-btn'));
        }});

        const ativoKey = mapa['{aba}'];
        if (ativoKey) {{
            const btnsAtivos = doc.querySelectorAll('button[key="' + ativoKey + '"]');
            btnsAtivos.forEach(btn => btn.classList.add('active-btn'));
        }}
    }}
    updateActiveButton();
    setTimeout(updateActiveButton, 50);
    setTimeout(updateActiveButton, 150);
    </script>
""", height=0)