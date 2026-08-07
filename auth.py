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
    "pesagem:visualizar": "Lançamentos - Acessar Tela de Lançamentos",
    "pesagem:criar": "Lançamentos - Registrar Dados",
    "campo:data": "Formulário - Selecionar/Editar Data",
    "campo:prato": "Formulário - Selecionar Prato / Item",
    "campo:pesos": "Formulário - Lançar Pesos (Produção/Descarte/Sobra)",
    "campo:clientes": "Formulário - Lançar Clientes Atendidos",
    "campo:obs": "Formulário - Lançar Observações",
    "dashboard:visualizar": "Dashboard - Visualizar Painel de Métricas",
    "dashboard:filtrar": "Dashboard - Alterar Filtros de Data",
    "dashboard:matriz": "Dashboard - Ver Matriz de Desempenho por Prato",
    "relatorios:exportar_pdf": "Relatórios - Gerar e Baixar PDF Executivo",
    "usuarios:gerenciar": "Administração - Gerenciar Contas de Usuários",
    "perfis:gerenciar": "Administração - Criar/Editar Perfis e Permissões"
}

def buscar_perfis():
    return {
        "master": {
            "nome": "Master",
            "permissoes": ["pesagem:visualizar", "pesagem:criar", "campo:data", "campo:prato", "campo:pesos", "campo:clientes", "campo:obs", "dashboard:visualizar", "dashboard:filtrar", "dashboard:matriz", "relatorios:exportar_pdf", "lancamentos:editar", "usuarios:gerenciar", "pratos:gerenciar"]
        },
        "admin": {
            "nome": "Admin",
            "permissoes": ["pesagem:visualizar", "pesagem:criar", "campo:data", "campo:prato", "campo:pesos", "campo:clientes", "campo:obs", "dashboard:visualizar", "dashboard:filtrar", "dashboard:matriz", "relatorios:exportar_pdf", "lancamentos:editar", "usuarios:gerenciar", "pratos:gerenciar"]
        },
        # =========================================================
        # NOVOS PERFIS DE COZINHA
        # =========================================================
        "cozinha_escala_1": {
            "nome": "Cozinha - Escala 1",
            "permissoes": [
                "pesagem:visualizar", # Permite acessar a tela de lançamentos
                "pesagem:criar",      # Permite salvar formulários
                "campo:prato",        # Acesso ao campo de seleção de pratos
                "campo:pesos",        # Acesso aos campos de medições (kg)
                "campo:obs",          # Acesso ao campo de observações
                "pratos:gerenciar"    # PERMISSÃO CHAVE: Permite criar novos pratos no menu Configurações
            ]
        },
        "cozinha_escala_2": {
            "nome": "Cozinha - Escala 2",
            "permissoes": [
                "pesagem:visualizar", # Permite acessar a tela de lançamentos
                "pesagem:criar",      # Permite salvar formulários
                "campo:prato",        # Acesso ao campo de seleção de pratos
                "campo:pesos",        # Acesso aos campos de medições (kg)
                "campo:obs"           # Acesso ao campo de observações
                # (SEM 'pratos:gerenciar' e SEM 'usuarios:gerenciar')
            ]
        },
        # Perfil Caixa tradicional
        "caixa": {
            "nome": "Caixa",
            "permissoes": [
                "pesagem:visualizar", "pesagem:criar", "campo:clientes", "campo:obs"
            ]
        }
    }

def tem_permissao(chave_permissao):
    """Retorna True se o usuário logado tiver a permissão informada."""
    if not st.session_state.get("usuario_logado"):
        return False
        
    permissoes_usuario = st.session_state.get("permissoes_usuario", [])
    
    if "ALL" in permissoes_usuario:
        return True
        
    return chave_permissao in permissoes_usuario