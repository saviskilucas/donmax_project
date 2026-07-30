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

# Estados de sessão
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = "inicio"

# Se o usuário NÃO estiver logado, força o aplicativo a ficar travado na aba inicio
if not st.session_state["usuario_logado"]:
    st.session_state["aba_ativa"] = "inicio"

aba = st.session_state["aba_ativa"]

# =========================================================
# 2. INJEÇÃO DE CSS (MODO ESCURO + CÁPSULA ESTÁVEL)
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

    /* CÁPSULA TRAVADA NO RODAPÉ */
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

    /* Cápsula Vermelha que envolve as colunas */
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

    /* FORÇA COLUNAS COM LARGURA IGUAL */
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

    /* Divisória vertical sutil entre os botões */
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

    /* WRAPPER INTERNO DOS BOTÕES */
    div.st-key-nav_bar_container div[data-testid="stElementContainer"],
    div.st-key-nav_bar_container div[data-testid="stButton"] {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    /* ESTILO BASE DOS BOTÕES */
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

    /* BOTÕES INATIVOS */
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

    /* BOTÃO ATIVO */
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
# 3. CONEXÃO E BANCO DE DADOS GOOGLE SHEETS
# =========================================================
@st.cache_resource
def conectar_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(credentials).open("Planilha Don Max")

@st.cache_data(ttl=300)
def carregar_dados_painel():
    try:
        sheet = conectar_gsheets().worksheet("Lancamentos_Diarios")
        return sheet.get_all_records()
    except Exception:
        return []

def buscar_usuarios_sem_cache():
    """Lê diretamente do Google Sheets sem cache para validar login/cadastro em tempo real."""
    try:
        sheet = conectar_gsheets().worksheet("Usuarios")
        registros = sheet.get_all_records()
        
        # Normalização resiliente das chaves do dicionário
        usuarios_normalizados = []
        for reg in registros:
            item_limpo = {}
            for k, v in reg.items():
                chave_formatada = str(k).strip().lower().replace("-", "").replace(" ", "")
                item_limpo[chave_formatada] = str(v).strip()
            usuarios_normalizados.append(item_limpo)
            
        return usuarios_normalizados
    except Exception as e:
        st.error(f"Erro ao acessar a aba 'Usuarios' na planilha: {e}")
        return []

def cadastrar_usuario(nome, email, senha):
    sheet = conectar_gsheets().worksheet("Usuarios")
    sheet.append_row([nome.strip(), email.strip().lower(), str(senha).strip()])

# =========================================================
# 4. BARRA SUPERIOR FIXA
# =========================================================
st.markdown("""
    <div class="modern-header">
        <div class="modern-header-title">
            <span>Don Max Buffet</span>
        </div>
        <div>
            <span onclick="window.location.reload();" style="cursor:pointer;" title="Recarregar">🔄</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Botão de Logout se o usuário estiver logado
if st.session_state["usuario_logado"]:
    col_head1, col_head2 = st.columns([0.7, 0.3])
    with col_head2:
        if st.button("🚪 Sair", key="btn_logout"):
            st.session_state["usuario_logado"] = None
            st.session_state["aba_ativa"] = "inicio"
            st.rerun()

# =========================================================
# 5. CONTEÚDO DAS ABAS
# =========================================================
if aba == "inicio":
    if not st.session_state["usuario_logado"]:
        st.markdown("<div class='section-header'>🔐 ACESSO AO SISTEMA</div>", unsafe_allow_html=True)
        
        tab_login, tab_cadastro, tab_esqueci = st.tabs(["🔐 Entrar", "📝 Criar Conta", "🔑 Esqueci a Senha"])
        
        # ABA 1: LOGIN
        with tab_login:
            with st.form("form_login"):
                email_login = st.text_input("E-mail", placeholder="seuemail@exemplo.com")
                senha_login = st.text_input("Senha", type="password", placeholder="••••••••")
                btn_login = st.form_submit_button("ENTRAR NO SISTEMA")
                
                if btn_login:
                    email_digitado = email_login.strip().lower()
                    senha_digitada = senha_login.strip()
                    
                    if not email_digitado or not senha_digitada:
                        st.warning("⚠️ Preencha e-mail e senha para continuar.")
                    else:
                        usuarios = buscar_usuarios_sem_cache()
                        usuario_encontrado = None
                        
                        for u in usuarios:
                            e_mail_banco = u.get("email", "")
                            senha_banco = u.get("senha", "")
                            
                            if e_mail_banco == email_digitado and senha_banco == senha_digitada:
                                usuario_encontrado = u.get("nome", "Usuário")
                                break
                        
                        if usuario_encontrado:
                            st.session_state["usuario_logado"] = usuario_encontrado
                            st.session_state["aba_ativa"] = "pesagem"
                            st.success(f"Bem-vindo(a), {usuario_encontrado}!")
                            st.rerun()
                        else:
                            st.error("❌ E-mail ou senha incorretos. Verifique e tente novamente.")

        # ABA 2: CADASTRO
        with tab_cadastro:
            with st.form("form_cadastro"):
                nome_cad = st.text_input("Nome Completo", placeholder="Ex: João Silva")
                email_cad = st.text_input("E-mail de Acesso", placeholder="seuemail@exemplo.com")
                senha_cad = st.text_input("Senha", type="password", placeholder="••••••••")
                btn_cadastrar = st.form_submit_button("CRIAR MINHA CONTA")
                
                if btn_cadastrar:
                    nome_digitado = nome_cad.strip()
                    email_digitado = email_cad.strip().lower()
                    senha_digitada = senha_cad.strip()
                    
                    if not nome_digitado or not email_digitado or not senha_digitada:
                        st.warning("⚠️ Por favor, preencha todos os campos do cadastro.")
                    else:
                        usuarios = buscar_usuarios_sem_cache()
                        ja_existe = any(u.get("email", "") == email_digitado for u in usuarios)
                        
                        if ja_existe:
                            st.error("⚠️ Este e-mail já está cadastrado. Faça login ou recupere sua senha.")
                        else:
                            try:
                                cadastrar_usuario(nome_digitado, email_digitado, senha_digitada)
                                st.success("✅ Conta criada com sucesso! Você já pode ir na aba 'Entrar' para fazer seu login.")
                            except Exception as e:
                                st.error(f"❌ Erro ao salvar cadastro na planilha: {e}")

        # ABA 3: ESQUECI A SENHA
        with tab_esqueci:
            with st.form("form_esqueci"):
                email_recup = st.text_input("Insira seu E-mail Cadastrado", placeholder="seuemail@exemplo.com")
                btn_recuperar = st.form_submit_button("RECUPERAR MINHA SENHA")
                
                if btn_recuperar:
                    email_target = email_recup.strip().lower()
                    if not email_target:
                        st.warning("⚠️ Digite o e-mail para buscar a senha.")
                    else:
                        usuarios = buscar_usuarios_sem_cache()
                        senha_achada = None
                        
                        for u in usuarios:
                            if u.get("email", "") == email_target:
                                senha_achada = u.get("senha", "")
                                break
                        
                        if senha_achada:
                            st.info(f"🔑 **Sua senha cadastrada é:** `{senha_achada}`")
                        else:
                            st.error("❌ E-mail não localizado na base de usuários.")

    else:
        st.markdown(f"<div class='section-header'>👋 BEM-VINDO, {st.session_state['usuario_logado'].upper()}!</div>", unsafe_allow_html=True)
        st.write("Você está conectado ao sistema do **Don Max Buffet**.")
        st.info("Utilize os menus no rodapé da tela para registrar pesagens ou visualizar relatórios.")

elif aba == "pesagem" and st.session_state["usuario_logado"]:
    with st.form("form_pesagem", clear_on_submit=True):
        st.markdown("<div class='section-header'>1. INFORMAÇÕES DO DIA</div>", unsafe_allow_html=True)
        data_sel = st.date_input("Data do Serviço", value=date.today())
        responsavel = st.text_input("Responsável pelo Turno", value=st.session_state["usuario_logado"])
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
                    sheet = conectar_gsheets().worksheet("Lancamentos_Diarios")
                    nova_linha = [str(data_sel), responsavel.strip(), int(clientes), prato_sel, float(prod_inicial), float(reposicao), float(sobra_limpa), float(sobra_buffet), float(descarte), observacoes.strip()]
                    sheet.append_row(nova_linha)
                    st.cache_data.clear()
                    st.success(f"✅ **{prato_sel}** registrado com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar na planilha: {e}")

elif aba == "historico" and st.session_state["usuario_logado"]:
    st.markdown("<div class='section-header'>📊 PAINEL DE CONTROLE DE DESCARTE</div>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([0.7, 0.3])
    with col_b:
        if st.button("🔄 Recarregar Dados"):
            st.cache_data.clear()
            st.rerun()

    dados = carregar_dados_painel()
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df.tail(10).iloc[::-1], use_container_width=True, hide_index=True)
        st.markdown("---")
        total_descarte = df['Descarte Total'].sum() if 'Descarte Total' in df.columns else 0
        st.metric("Descarte Acumulado (kg)", f"{total_descarte:.2f} kg")
    else:
        st.info("Nenhum registro encontrado na planilha ainda.")

elif aba == "config" and st.session_state["usuario_logado"]:
    st.markdown("<div class='section-header'>⚙️ CONFIGURAÇÕES DO SISTEMA</div>", unsafe_allow_html=True)
    st.markdown("**Don Max Buffet v1.0**\n*Sistema Integrado de Controle de Pesagens*\n\n---\n\n**Instruções para a Cozinha:**\n1. Realize as pesagens sempre ao final do turno.\n2. Certifique-se de zerar a tara da balança.\n3. Dúvidas ou problemas falar com a gerência.")
    if st.button("🔄 Limpar Cache Geral"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Cache limpo com sucesso!")

# =========================================================
# 6. RODAPÉ FIXO (SÓ EXIBE SE ESTIVER LOGADO)
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