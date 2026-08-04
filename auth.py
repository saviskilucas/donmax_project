import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def conectar_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(credentials).open("Planilha Don Max")

# DICIONÁRIO COMPLETO DE PERMISSÕES DO SISTEMA
TODAS_PERMISSOES = {
    "pesagem:visualizar": "Lançamentos - Accessar Formulário de Pesagem",
    "pesagem:criar": "Lançamentos - Registrar Novas Pesagens",
    "pesagem:editar": "Lançamentos - Editar Lançamentos do Dia",
    "pesagem:excluir": "Lançamentos - Excluir Lançamentos do Dia",
    "dashboard:visualizar": "Dashboard - Visualizar Painel de Métricas",
    "dashboard:filtrar": "Dashboard - Alterar Filtros de Data",
    "dashboard:matriz": "Dashboard - Ver Matriz de Desempenho por Prato",
    "relatorios:exportar_pdf": "Relatórios - Gerar e Baixar PDF Executivo",
    "usuarios:gerenciar": "Administração - Gerenciar Contas de Usuários",
    "perfis:gerenciar": "Administração - Criar/Editar Perfis e Permissões",
    "historico:editar_passado": "Administração - Editar Registros Passados"
}

def buscar_perfis():
    try:
        sheet = conectar_gsheets().worksheet("Perfis")
        registros = sheet.get_all_records()
        perfis = {}
        for r in registros:
            id_p = str(r.get("ID_Perfil", "")).strip().lower()
            nome_p = str(r.get("Nome_Perfil", id_p)).strip()
            perms_raw = str(r.get("Permissoes", "")).strip()
            
            if perms_raw == "ALL":
                lista_perms = ["ALL"]
            else:
                lista_perms = [p.strip() for p in perms_raw.split(",") if p.strip()]
                
            perfis[id_p] = {
                "nome": nome_p,
                "permissoes": lista_perms
            }
        return perfis
    except Exception:
        # Perfil fallback de emergência caso a aba Perfis ainda não tenha sido criada
        return {"administrador": {"nome": "Administrador", "permissoes": ["ALL"]}}

def tem_permissao(chave_permissao):
    """Retorna True se o usuário logado tiver a permissão informada."""
    if not st.session_state.get("usuario_logado"):
        return False
        
    permissoes_usuario = st.session_state.get("permissoes_usuario", [])
    
    if "ALL" in permissoes_usuario:
        return True
        
    return chave_permissao in permissoes_usuario