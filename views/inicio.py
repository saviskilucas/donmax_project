import streamlit as st
import gspread
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
            usuarios_normalizados.append(item_limpo)
        return usuarios_normalizados
    except Exception as e:
        st.error(f"Erro ao acessar a aba 'Usuarios' na planilha: {e}")
        return []

def cadastrar_usuario(nome, email, senha):
    sheet = conectar_gsheets().worksheet("Usuarios")
    sheet.append_row([nome.strip(), email.strip().lower(), str(senha).strip()])

def render():
    if not st.session_state["usuario_logado"]:
        st.markdown("<div class='section-header'>🔐 ACESSO AO SISTEMA</div>", unsafe_allow_html=True)
        
        tab_login, tab_cadastro, tab_esqueci = st.tabs(["🔐 Entrar", "📝 Criar Conta", "🔑 Esqueci a Senha"])
        
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
                            if u.get("email", "") == email_digitado and u.get("senha", "") == senha_digitada:
                                usuario_encontrado = u.get("nome", "Usuário")
                                break
                        
                        if usuario_encontrado:
                            st.session_state["usuario_logado"] = usuario_encontrado
                            st.session_state["aba_ativa"] = "pesagem"
                            st.success(f"Bem-vindo(a), {usuario_encontrado}!")
                            st.rerun()
                        else:
                            st.error("❌ E-mail ou senha incorretos.")

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
                            st.error("⚠️ Este e-mail já está cadastrado.")
                        else:
                            try:
                                cadastrar_usuario(nome_digitado, email_digitado, senha_digitada)
                                st.success("✅ Conta criada com sucesso! Faça login na aba 'Entrar'.")
                            except Exception as e:
                                st.error(f"❌ Erro ao salvar cadastro na planilha: {e}")

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
        st.info("Utilize os menus no rodapé da tela para navegar.")