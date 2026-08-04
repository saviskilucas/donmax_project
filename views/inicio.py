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
                # Remove acentos básicos, espaços e coloca em minúsculo para a chave
                chave = str(k).strip().lower().replace("á", "a").replace("ã", "a").replace("â", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
                chave = chave.replace("-", "").replace(" ", "")
                item_limpo[chave] = str(v).strip()
            
            # Mapeia nome original
            nome_orig = str(reg.get("Nome", reg.get("nome", "Usuário"))).strip()
            item_limpo["nome_original"] = nome_orig
            
            # Identifica a coluna do login (seja 'usuario', 'usuario', 'email', etc.)
            usr_valor = item_limpo.get("usuario", item_limpo.get("email", ""))
            item_limpo["login_identificador"] = str(usr_valor).strip().lower()
            
            usuarios_normalizados.append(item_limpo)
            
        return usuarios_normalizados
    except Exception as e:
        st.error(f"Erro ao acessar a aba 'Usuarios' na planilha: {e}")
        return []

def cadastrar_usuario(nome, usuario, senha):
    sheet = conectar_gsheets().worksheet("Usuarios")
    # Escreve respeitando as colunas da planilha: Nome, Usuário, Senha
    sheet.append_row([nome.strip(), usuario.strip().lower(), str(senha).strip()])

def enviar_email_recuperacao_admin(usuario_solicitante, usuario_encontrado):
    try:
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = int(st.secrets["email"]["smtp_port"])
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        admin_email = st.secrets["email"]["admin_email"]

        assunto = f"🔑 [Don Max] Solicitação de Senha - {usuario_solicitante}"
        
        # HTML do E-mail Estilizado
        corpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-color: #121212;
                    color: #E0E0E0;
                    margin: 0;
                    padding: 20px;
                }}
                .card {{
                    max-width: 500px;
                    margin: 0 auto;
                    background-color: #1E1E1E;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
                    border: 1px solid #2D2D2D;
                }}
                .header {{
                    background-color: #B71C1C;
                    color: #FFFFFF;
                    padding: 24px 20px;
                    text-align: center;
                }}
                .header h2 {{
                    margin: 0;
                    font-size: 1.25rem;
                    font-weight: 800;
                    letter-spacing: 0.5px;
                }}
                .content {{
                    padding: 24px;
                }}
                .intro {{
                    font-size: 0.95rem;
                    color: #CCCCCC;
                    margin-bottom: 20px;
                    line-height: 1.4;
                }}
                .info-box {{
                    background-color: #262626;
                    border-left: 4px solid #FF5252;
                    border-radius: 8px;
                    padding: 16px;
                    margin-bottom: 20px;
                }}
                .info-item {{
                    margin-bottom: 10px;
                    font-size: 0.9rem;
                }}
                .info-item:last-child {{
                    margin-bottom: 0;
                }}
                .label {{
                    color: #A0A0A0;
                    font-size: 0.8rem;
                    text-transform: uppercase;
                    font-weight: 700;
                    display: block;
                    margin-bottom: 2px;
                }}
                .value {{
                    color: #FFFFFF;
                    font-size: 1rem;
                    font-weight: 700;
                }}
                .badge-senha {{
                    background-color: #B71C1C;
                    color: #FFFFFF;
                    padding: 4px 10px;
                    border-radius: 6px;
                    font-family: monospace;
                    font-size: 1.05rem;
                    letter-spacing: 1px;
                }}
                .footer {{
                    text-align: center;
                    padding: 16px;
                    font-size: 0.75rem;
                    color: #777777;
                    border-top: 1px solid #2A2A2A;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <h2>DON MAX BUFFET</h2>
                </div>
                <div class="content">
                    <div class="intro">
                        Olá, <strong>Administrador</strong>!<br>
                        Uma solicitação de recuperação de senha foi realizada no sistema.
                    </div>
                    
                    <div class="info-box">
                        <div class="info-item">
                            <span class="label">Usuário Solicitado</span>
                            <span class="value">{usuario_solicitante}</span>
                        </div>
                        <div class="info-item" style="margin-top: 12px;">
                            <span class="label">Nome Cadastrado</span>
                            <span class="value">{usuario_encontrado.get('nome_original', 'N/D')}</span>
                        </div>
                        <div class="info-item" style="margin-top: 12px;">
                            <span class="label">Senha Atual</span>
                            <span class="badge-senha">{usuario_encontrado.get('senha', 'N/D')}</span>
                        </div>
                    </div>
                </div>
                <div class="footer">
                    Mensagem automática gerada pelo Painel de Controle Don Max.
                </div>
            </div>
        </body>
        </html>
        """

        # Define a mensagem como HTML
        msg = MIMEText(corpo_html, "html", "utf-8")
        msg["Subject"] = assunto
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
        # TAB 1: LOGIN (Aceita nome.sobrenome ou e-mail cadastrado)
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
                            if u.get("login_identificador", "") == usr_digitado and u.get("senha", "") == senha_digitada:
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
                        ja_existe = any(u.get("login_identificador", "") == usr_digitado for u in usuarios)
                        
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
                            if u.get("login_identificador", "") == usr_target:
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