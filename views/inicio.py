import streamlit as st
import gspread
import smtplib
from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials

@st.cache_resource
def conectar_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(credentials).open("Planilha Don Max")

def buscar_usuarios_sem_cache():
    try:
        sheet = conectar_gsheets().worksheet("Usuarios")
        registros = sheet.get_all_records()
        usuarios_normalizados = []
        for reg in registros:
            item_limpo = {}
            for k, v in reg.items():
                chave_formatada = str(k).strip().lower().replace("-", "").replace(" ", "")
                item_limpo[chave_formatada] = str(v).strip()
            item_limpo["nome_original"] = str(reg.get("Nome", reg.get("nome", "Usuário"))).strip()
            usuarios_normalizados.append(item_limpo)
        return usuarios_normalizados
    except Exception as e:
        st.error(f"Erro ao acessar a aba 'Usuarios' na planilha: {e}")
        return []

def cadastrar_usuario(nome, usuario, senha):
    sheet = conectar_gsheets().worksheet("Usuarios")
    # Colunas salvas na planilha: Nome Completo, Usuario (nome.sobrenome), Senha
    sheet.append_row([nome.strip(), usuario.strip().lower(), str(senha).strip()])

def enviar_email_recuperacao_admin(usuario_solicitante, usuario_encontrado):
    try:
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = int(st.secrets["email"]["smtp_port"])
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        admin_email = st.secrets["email"]["admin_email"]

        assunto = f"🔑 Solicitação de Recuperação de Senha - {usuario_solicitante}"
        corpo = f"""
        Olá, Administrador!

        Houve uma solicitação de recuperação de senha no aplicativo Don Max Buffet.

        • Usuário Solicitado: {usuario_solicitante}
        • Nome Cadastrado: {usuario_encontrado.get('nome_original', 'N/D')}
        • Senha Atual: {usuario_encontrado.get('senha', 'N/D')}

        Esta mensagem foi gerada automaticamente pelo sistema.
        """

        msg = MIMEText(corpo, "plain", "utf-8")
        msg["Subject"] = assunto
        # Em vez de passar só o e-mail, enviamos o Nome + E-mail:
        msg["From"] = f"Don Max Buffet <{sender_email}>"
        msg["To"] = admin_email

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [admin_email], msg.as_string())

        return True
    except Exception as e:
        st.error(f"Erro ao disparar e-mail de recuperação: {e}")
        return False

def render():
    if not st.session_state["usuario_logado"]:
        st.markdown("<div class='section-header'>🔐 ACESSO AO SISTEMA</div>", unsafe_allow_html=True)
        
        tab_login, tab_cadastro, tab_esqueci = st.tabs(["🔐 Entrar", "📝 Criar Conta", "🔑 Esqueci a Senha"])
        
        # ---------------------------------------------------------
        # TAB 1: LOGIN POR USUÁRIO (nome.sobrenome)
        # ---------------------------------------------------------
        with tab_login:
            with st.form("form_login"):
                usuario_login = st.text_input("Usuário", placeholder="ex: nome.sobrenome")
                senha_login = st.text_input("Senha", type="password", placeholder="••••••••")
                btn_login = st.form_submit_button("ENTRAR NO SISTEMA")
                
                if btn_login:
                    usr_digitado = usuario_login.strip().lower()
                    senha_digitada = senha_login.strip()
                    
                    if not usr_digitado or not senha_digitada:
                        st.warning("⚠️ Preencha usuário e senha para continuar.")
                    else:
                        usuarios = buscar_usuarios_sem_cache()
                        usuario_encontrado = None
                        
                        for u in usuarios:
                            # Compara com a coluna 'usuario' ou 'email' se for o formato antigo
                            usr_banco = u.get("usuario", u.get("email", "")).lower()
                            if usr_banco == usr_digitado and u.get("senha", "") == senha_digitada:
                                usuario_encontrado = u.get("nome_original", "Usuário")
                                break
                        
                        if usuario_encontrado:
                            st.session_state["usuario_logado"] = usuario_encontrado
                            st.session_state["aba_ativa"] = "pesagem"
                            st.success(f"Bem-vindo(a), {usuario_encontrado}!")
                            st.rerun()
                        else:
                            st.error("❌ Usuário ou senha incorretos.")

        # ---------------------------------------------------------
        # TAB 2: CADASTRO COM NOME, USUÁRIO E SENHA
        # ---------------------------------------------------------
        with tab_cadastro:
            with st.form("form_cadastro"):
                nome_cad = st.text_input("Nome Completo", placeholder="Ex: João Silva")
                usuario_cad = st.text_input("Nome de Usuário", placeholder="Ex: joao.silva")
                senha_cad = st.text_input("Senha de Acesso", type="password", placeholder="••••••••")
                btn_cadastrar = st.form_submit_button("CRIAR MINHA CONTA")
                
                if btn_cadastrar:
                    nome_digitado = nome_cad.strip()
                    usr_digitado = usuario_cad.strip().lower().replace(" ", "")
                    senha_digitada = senha_cad.strip()
                    
                    if not nome_digitado or not usr_digitado or not senha_digitada:
                        st.warning("⚠️ Por favor, preencha todos os campos do cadastro.")
                    else:
                        usuarios = buscar_usuarios_sem_cache()
                        ja_existe = any(u.get("usuario", u.get("email", "")).lower() == usr_digitado for u in usuarios)
                        
                        if ja_existe:
                            st.error("⚠️ Este nome de usuário já está cadastrado.")
                        else:
                            try:
                                cadastrar_usuario(nome_digitado, usr_digitado, senha_digitada)
                                st.success("✅ Conta criada com sucesso! Você já pode entrar na aba 'Entrar'.")
                            except Exception as e:
                                st.error(f"❌ Erro ao salvar cadastro na planilha: {e}")

        # ---------------------------------------------------------
        # TAB 3: RECUPERAÇÃO ENVIANDO E-MAIL PARA O ADMIN
        # ---------------------------------------------------------
        with tab_esqueci:
            with st.form("form_esqueci"):
                usr_recup = st.text_input("Insira seu Usuário (ex: nome.sobrenome)", placeholder="nome.sobrenome")
                btn_recuperar = st.form_submit_button("SOLICITAR RECUPERAÇÃO DE SENHA")
                
                if btn_recuperar:
                    usr_target = usr_recup.strip().lower()
                    if not usr_target:
                        st.warning("⚠️ Digite o usuário para buscar.")
                    else:
                        usuarios = buscar_usuarios_sem_cache()
                        usuario_achado = None
                        for u in usuarios:
                            if u.get("usuario", u.get("email", "")).lower() == usr_target:
                                usuario_achado = u
                                break
                        
                        if usuario_achado:
                            sucesso = enviar_email_recuperacao_admin(usr_target, usuario_achado)
                            if sucesso:
                                st.success("📩 Solicitação enviada! A senha foi encaminhada ao e-mail do Administrador (saviskilucas@gmail.com). Entre em contato com ele para redefinir seu acesso.")
                        else:
                            st.error("❌ Usuário não localizado na base do sistema.")
    else:
        st.markdown(f"<div class='section-header'>🏠 PAINEL INICIAL</div>", unsafe_allow_html=True)
        st.subheader(f"Olá, {st.session_state['usuario_logado']}! 👋")
        st.write("Sua sessão está ativa no **Sistema Don Max Buffet**.")
        
        st.markdown("---")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📝 Novo Lançamento", use_container_width=True):
                st.session_state["aba_ativa"] = "pesagem"
                st.rerun()
        with col_b:
            if st.button("📊 Consultar Painel", use_container_width=True):
                st.session_state["aba_ativa"] = "historico"
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Encerrar Sessão", use_container_width=True):
            st.session_state["usuario_logado"] = None
            st.session_state["aba_ativa"] = "inicio"
            st.rerun()