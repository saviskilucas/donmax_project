import streamlit as st
import gspread
import smtplib
import os
import base64
from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials
from auth import buscar_perfis, conectar_gsheets

# =========================================================
# CONSULTA DE USUÁRIOS COM CACHE DE ALTA VELOCIDADE
# =========================================================
@st.cache_data(ttl=300, show_spinner=False)
def buscar_usuarios_cache():
    try:
        sheet = conectar_gsheets().worksheet("Usuarios")
        registros = sheet.get_all_records()
        usuarios_normalizados = []
        
        for reg in registros:
            item_limpo = {}
            for k, v in reg.items():
                chave = str(k).strip().lower().replace("á", "a").replace("ã", "a").replace("â", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
                chave = chave.replace("-", "").replace(" ", "").replace("_", "")
                item_limpo[chave] = str(v).strip()
            
            item_limpo["nome_original"] = str(reg.get("Nome", reg.get("nome", "Usuário"))).strip()
            usr_valor = item_limpo.get("usuario", item_limpo.get("email", ""))
            item_limpo["login_identificador"] = str(usr_valor).strip().lower()
            
            id_perf_valor = item_limpo.get("idperfil", item_limpo.get("perfil", "cozinha"))
            item_limpo["id_perfil"] = str(id_perf_valor).strip().lower()
            item_limpo["ativo"] = str(item_limpo.get("ativo", "TRUE")).strip().upper() == "TRUE"
            item_limpo["senha"] = str(item_limpo.get("senha", "")).strip()
            
            usuarios_normalizados.append(item_limpo)
            
        return usuarios_normalizados
    except Exception as e:
        st.error(f"Erro ao acessar a aba 'Usuarios' na planilha: {e}")
        return []

def enviar_email_recuperacao_admin(usuario_solicitante, usuario_encontrado):
    try:
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = int(st.secrets["email"]["smtp_port"])
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        admin_email = st.secrets["email"]["admin_email"]

        assunto = f"🔑 [Don Max] Solicitação de Senha - {usuario_solicitante}"
        
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
                }}
                .content {{
                    padding: 24px;
                }}
                .info-box {{
                    background-color: #262626;
                    border-left: 4px solid #FF5252;
                    border-radius: 8px;
                    padding: 16px;
                }}
                .value {{
                    color: #FFFFFF;
                    font-weight: 700;
                }}
                .badge-senha {{
                    background-color: #B71C1C;
                    color: #FFFFFF;
                    padding: 4px 10px;
                    border-radius: 6px;
                    font-family: monospace;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <h2>DON MAX BUFFET</h2>
                </div>
                <div class="content">
                    <p>Olá, <strong>Administrador</strong>!</p>
                    <p>Uma solicitação de recuperação de senha foi realizada no sistema.</p>
                    <div class="info-box">
                        <p><strong>Usuário:</strong> <span class="value">{usuario_solicitante}</span></p>
                        <p><strong>Nome:</strong> <span class="value">{usuario_encontrado.get('nome_original', 'N/D')}</span></p>
                        <p><strong>Senha:</strong> <span class="badge-senha">{usuario_encontrado.get('senha', 'N/D')}</span></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

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
    if not st.session_state.get("usuario_logado"):
        # Converte imagem local para Base64 para injeção HTML perfeita sem quebra
        logo_html_element = '<div style="font-size: 2.8rem; margin-bottom: 5px;">🍽️</div>'
        
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                logo_html_element = f'<img src="data:image/png;base64,{encoded_string}" class="login-logo-img" alt="Don Max Logo">'
            except Exception:
                pass

        # CSS Exclusivo para a Tela de Login
        st.markdown("""
            <style>
            .login-card {
                background-color: #1E1E1E;
                border: 1px solid #2D2D2D;
                border-top: 5px solid #B71C1C;
                border-radius: 16px;
                padding: 28px 20px 20px 20px;
                box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.6);
                margin-top: 10px;
                margin-bottom: 20px;
                text-align: center;
            }
            .login-logo-img {
                max-width: 160px;
                max-height: 160px;
                object-fit: contain;
                margin-bottom: 12px;
                filter: drop-shadow(0px 4px 8px rgba(0,0,0,0.5));
            }
            .login-title {
                color: #FFFFFF;
                font-size: 1.4rem;
                font-weight: 800;
                letter-spacing: 0.5px;
                margin: 0;
            }
            .login-subtitle {
                color: #888888;
                font-size: 0.85rem;
                margin-top: 4px;
            }
            div[data-testid="stForm"] {
                border: none !important;
                padding: 0 !important;
            }
            div[data-testid="stForm"] button[kind="primaryFormSubmit"],
            div[data-testid="stForm"] button {
                background-color: #B71C1C !important;
                color: #FFFFFF !important;
                border-radius: 12px !important;
                height: 48px !important;
                font-size: 1rem !important;
                font-weight: 800 !important;
                border: none !important;
                margin-top: 10px !important;
                box-shadow: 0px 4px 12px rgba(183, 28, 28, 0.4) !important;
                transition: all 0.2s ease !important;
            }
            div[data-testid="stForm"] button:hover {
                background-color: #D32F2F !important;
                transform: translateY(-1px);
            }
            </style>
        """, unsafe_allow_html=True)

        col_esq, col_centro, col_dir = st.columns([0.1, 0.8, 0.1])
        
        with col_centro:
            # CARD DE LOGIN COM A LOGO TRANSPARENTE EMBUTIDA
            st.markdown(f"""
                <div class="login-card">
                    {logo_html_element}
                    <div class="login-title">DON MAX RESTAURANTE</div>
                    <div class="login-subtitle">Gestão de Buffet</div>
                </div>
            """, unsafe_allow_html=True)

            # FORMULÁRIO DE LOGIN
            with st.form("form_login_principal"):
                usuario_login = st.text_input("Usuário", placeholder="ex: nome.sobrenome")
                senha_login = st.text_input("Senha", type="password", placeholder="••••••••")
                btn_login = st.form_submit_button("ENTRAR NO SISTEMA", width="stretch")
                
                if btn_login:
                    usr_digitado = usuario_login.strip().lower()
                    senha_digitada = senha_login.strip()
                    
                    if not usr_digitado or not senha_digitada:
                        st.warning("⚠️ Preencha usuário e senha.")
                    else:
                        usuarios = buscar_usuarios_cache()
                        usuario_achado = None
                        
                        for u in usuarios:
                            if u.get("login_identificador") == usr_digitado and u.get("senha") == senha_digitada:
                                if not u.get("ativo"):
                                    st.error("❌ Conta de usuário desativada. Entre em contato com o Administrador.")
                                    return
                                usuario_achado = u
                                break
                        
                        if usuario_achado:
                            perfis = buscar_perfis()
                            id_perf = usuario_achado.get("id_perfil", "master")
                            dados_perfil = perfis.get(id_perf, {"nome": "Usuário", "permissoes": []})
                            
                            st.session_state["usuario_logado"] = usuario_achado.get("nome_original")
                            st.session_state["id_usuario_logado"] = usr_digitado
                            st.session_state["perfil_logado"] = id_perf
                            st.session_state["nome_perfil_logado"] = dados_perfil.get("nome")
                            st.session_state["permissoes_usuario"] = dados_perfil.get("permissoes", [])
                            
                            st.session_state["aba_ativa"] = "pesagem"
                            st.success(f"Bem-vindo(a), {usuario_achado.get('nome_original')}!")
                            st.rerun()
                        else:
                            st.error("❌ Usuário ou senha incorretos.")

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🔑 Esqueceu sua senha?"):
                with st.form("form_esqueci_senha_exp"):
                    usr_recup = st.text_input("Insira seu usuário cadastrado", placeholder="ex: nome.sobrenome")
                    btn_recuperar = st.form_submit_button("SOLICITAR SENHA AO ADMIN", width="stretch")
                    
                    if btn_recuperar:
                        usr_target = usr_recup.strip().lower()
                        if not usr_target:
                            st.warning("⚠️ Digite o usuário.")
                        else:
                            usuarios = buscar_usuarios_cache()
                            u_target = next((u for u in usuarios if u.get("login_identificador") == usr_target), None)
                            
                            if u_target:
                                se_env = enviar_email_recuperacao_admin(usr_target, u_target)
                                if se_env:
                                    st.success("📩 Solicitação enviada ao Administrador por e-mail!")
                            else:
                                st.error("❌ Usuário não localizado.")

    else:
        st.markdown("<div class='section-header'>PAINEL INICIAL</div>", unsafe_allow_html=True)
        st.subheader(f"Olá, {st.session_state['usuario_logado']}! 👋")
        st.info(f"Perfil de Acesso: **{st.session_state.get('nome_perfil_logado', 'Usuário')}**")
        
        st.markdown("---")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("NOVO LANÇAMENTO", width="stretch"):
                st.session_state["aba_ativa"] = "pesagem"
                st.rerun()
        with col_b:
            if st.button("CONSULTAR PAINEL", width="stretch"):
                st.session_state["aba_ativa"] = "historico"
                st.rerun()

        st.markdown("---")
        if st.button("ENCERRAR SESSÃO", width="stretch"):
            for key in ["usuario_logado", "id_usuario_logado", "perfil_logado", "nome_perfil_logado", "permissoes_usuario"]:
                st.session_state[key] = None
            st.session_state["aba_ativa"] = "inicio"
            st.rerun()