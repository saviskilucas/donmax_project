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
# 4. INJEÇÃO DE CSS CUSTOMIZADO (RODAPÉ ARREDONDADO MODERNO)
# =========================================================
st.markdown("""
    <style>
    /* Configuração Geral da Tela Mobile */
    html, body, [data-testid="stApp"], .stApp {
        background-color: #F8F9FA !important;
    }

    /* Espaçamento central para o formulário rolar entre as barras congeladas */
    .block-container {
        padding-top: 4.0rem !important;
        padding-bottom: 6.0rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }

    /* Ocultar elementos padrão do Streamlit */
    #MainMenu, header, .stDeployButton, footer {
        display: none !important;
    }

    /* =========================================================
       1. BARRA SUPERIOR (HEADER MODERNO COM CANTOS ARREDONDADOS)
       ========================================================= */
    .modern-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        width: 100vw;
        height: 55px;
        background-color: #D32F2F;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 18px;
        z-index: 999999 !important;
        box-shadow: 0px 4px 12px rgba(211, 47, 47, 0.25);
        border-radius: 0 0 16px 16px;
    }

    .modern-header-title {
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: 0.3px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .modern-header-icons {
        display: flex;
        gap: 16px;
        font-size: 1.25rem;
        cursor: pointer;
    }

    /* =========================================================
       2. BARRA INFERIOR CONGELADA (DESIGN IDÊNTICO À FOTO DE REFERÊNCIA)
       ========================================================= */
    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100vw !important;
        height: 65px !important;
        background-color: #D32F2F !important; /* Cor principal Don Max */
        border-radius: 22px 22px 0 0 !important; /* Cantos arredondados do topo da barra */
        box-shadow: 0px -6px 20px rgba(0, 0, 0, 0.15) !important;
        z-index: 999999 !important;

        /* Força os 3 botões em linha horizontal perfeita */
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-around !important;
        padding: 0 10px !important;
        margin: 0 !important;
    }

    /* Cada coluna ocupa 1/3 exato da largura */
    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) > div {
        flex: 1 1 0% !important;
        width: 33.33% !important;
        min-width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex !important;
        justify-content: center !important;
    }

    /* Estilo dos Botões/Ícones estilo App Moderno */
    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) button {
        width: 85% !important;
        height: 48px !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 14px !important; /* Caixinha arredondada do ícone */
        box-shadow: none !important;
        color: rgba(255, 255, 255, 0.75) !important;
        font-size: 1.3rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        margin: 0 !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* ABA ATIVA: Cartão interno em destaque (Exatamente como na foto de referência) */
    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) button.active-btn {
        background-color: #FFFFFF !important; /* Caixa branca flutuante igual a foto */
        color: #D32F2F !important; /* Ícone na cor do tema */
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-2px);
    }

    /* =========================================================
       3. ESTILIZAÇÃO DOS CAMPOS DO FORMULÁRIO
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

    div[data-baseweb="input"] button {
        width: 36px !important;
        height: 36px !important;
    }

    /* Botão Salvar Principal */
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
        letter-spacing: 0.5px;
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
# 6. BARRA SUPERIOR FIXA (MODERNA)
# =========================================================
st.markdown("""
    <div class="modern-header">
        <div class="modern-header-title">
            <span> Don Max Buffet</span>
        </div>
        <div class="modern-header-icons">
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
# 8. RODAPÉ FIXO ESTILO APLICATIVO MODERNO (IGUAL À FOTO)
# =========================================================
col_nav1, col_nav2, col_nav3 = st.columns(3)

is_pesagem = st.session_state["aba_ativa"] == "Pesagem"
is_historico = st.session_state["aba_ativa"] == "Histórico"
is_config = st.session_state["aba_ativa"] == "Config"

with col_nav1:
    btn_p = st.button("🏠" if not is_pesagem else "🏠", key="nav_pesagem", help="Formulário")
    if btn_p:
        st.session_state["aba_ativa"] = "Pesagem"
        st.rerun()

with col_nav2:
    btn_h = st.button("📋" if not is_historico else "📋", key="nav_historico", help="Histórico")
    if btn_h:
        st.session_state["aba_ativa"] = "Histórico"
        st.rerun()

with col_nav3:
    btn_c = st.button("👤" if not is_config else "👤", key="nav_config", help="Opções")
    if btn_c:
        st.session_state["aba_ativa"] = "Config"
        st.rerun()

# Injetar classe 'active-btn' no botão selecionado via JS
js_active = f"""
    <script>
    setTimeout(function() {{
        const buttons = window.parent.document.querySelectorAll('div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) button');
        buttons.forEach(btn => btn.classList.remove('active-btn'));
        
        if ("{st.session_state['aba_ativa']}" === "Pesagem" && buttons[0]) {{
            buttons[0].classList.add('active-btn');
        }} else if ("{st.session_state['aba_ativa']}" === "Histórico" && buttons[1]) {{
            buttons[1].classList.add('active-btn');
        }} else if ("{st.session_state['aba_ativa']}" === "Config" && buttons[2]) {{
            buttons[2].classList.add('active-btn');
        }}
    }}, 100);
    </script>
"""
st.components.v1.html(js_active, height=0)