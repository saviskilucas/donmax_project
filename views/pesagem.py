import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime
from zoneinfo import ZoneInfo
from auth import tem_permissao

@st.cache_resource
def conectar_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(credentials).open("Planilha Don Max")

@st.cache_data(ttl=300)
def buscar_pratos_cadastrados():
    try:
        sheet = conectar_gsheets().worksheet("Alimentos")
        registros = sheet.get_all_records()
        lista = [str(r.get("Prato", "")).strip() for r in registros if r.get("Prato")]
        return [p for p in lista if p]
    except Exception:
        return ["Arroz", "Feijão", "Barreado", "Carne 1", "Carne 2", "Salada", "Sobremesa"]

def render():
    # 1. TRAVA PRINCIPAL DE ACESSO
    if not tem_permissao("pesagem:visualizar"):
        st.error("⛔ Você não tem permissão para acessar a tela de Lançamentos.")
        return

    pratos_lista = buscar_pratos_cadastrados()
    fuso_brasilia = ZoneInfo("America/Sao_Paulo")
    agora_br = datetime.now(fuso_brasilia)

    # 2. DEFINIÇÃO DINÂMICA DE VISIBILIDADE DE CAMPOS
    pode_data = tem_permissao("campo:data")
    pode_prato = tem_permissao("campo:prato")
    pode_pesos = tem_permissao("campo:pesos")
    pode_clientes = tem_permissao("campo:clientes")
    pode_obs = tem_permissao("campo:obs")

    with st.form("form_pesagem", clear_on_submit=True):
        st.markdown("<div class='section-header'>1. INFORMAÇÕES DO DIA</div>", unsafe_allow_html=True)
        
        col_dt, col_hr = st.columns(2)
        with col_dt:
            if pode_data:
                data_sel = st.date_input("Data do Serviço", value=agora_br.date(), format="DD/MM/YYYY")
            else:
                # Mostra a data do sistema de forma bloqueada
                data_sel = agora_br.date()
                st.text_input("Data do Serviço", value=data_sel.strftime("%d/%m/%Y"), disabled=True)
                
        with col_hr:
            hora_atual_str = agora_br.strftime("%H:%M")
            st.text_input("Hora do Registro", value=hora_atual_str, disabled=True)

        responsavel = st.text_input("Responsável pelo Turno", value=st.session_state.get("usuario_logado", ""))
        
        if pode_clientes:
            clientes = st.number_input("Clientes Atendidos no Dia", min_value=0, step=1, value=0)
        else:
            clientes = 0

        # SÓ APARECE PARA COZINHA E ADMIN
        if pode_prato:
            st.markdown("<div class='section-header'>2. PREPARAÇÃO / PRATO</div>", unsafe_allow_html=True)
            prato_sel = st.selectbox("Selecione o Prato", pratos_lista if pratos_lista else ["Nenhum prato cadastrado"])
        else:
            prato_sel = "Registro de Salão / Caixa"

        # SÓ APARECE PARA COZINHA E ADMIN
        if pode_pesos:
            st.markdown("<div class='section-header'>3. MEDIÇÕES DA BALANÇA (KG)</div>", unsafe_allow_html=True)
            st.caption("ℹ️ Pressione + ou - para alterar de 100g em 100g (0.100 kg)")
            
            col1, col2 = st.columns(2)
            with col1:
                prod_inicial = st.number_input("Produção Inicial (kg)", min_value=0.0, step=0.100, format="%.3f")
                reposicao = st.number_input("Reposição Total (kg)", min_value=0.0, step=0.100, format="%.3f")
            with col2:
                sobra_buffet = st.number_input("Sobra Buffet (kg)", min_value=0.0, step=0.100, format="%.3f")
                descarte = st.number_input("Descarte Total (kg)", min_value=0.0, step=0.100, format="%.3f")
        else:
            prod_inicial, reposicao, sobra_buffet, descarte = 0.0, 0.0, 0.0, 0.0

        # SÓ APARECE PARA CAIXA E ADMIN
        if pode_obs:
            observacoes = st.text_area("Observações (Opcional)", placeholder="Ex: Sobra de carne devido ao tempo chuvoso...")
        else:
            observacoes = ""

        btn_salvar = st.form_submit_button("SALVAR REGISTRO")

        if btn_salvar:
            if not tem_permissao("pesagem:criar"):
                st.error("⛔ Seu perfil não tem permissão para salvar registros.")
            elif not responsavel.strip():
                st.error("⚠️ Preencha o nome do Responsável antes de salvar.")
            else:
                try:
                    sheet = conectar_gsheets().worksheet("Lancamentos_Diarios")
                    agora_salvamento = datetime.now(fuso_brasilia)
                    data_br = data_sel.strftime("%d/%m/%Y")
                    hora_registro = agora_salvamento.strftime("%H:%M")
                    
                    # LINHA DE ACORDO COM A SUA ESTRUTURA MAIS RECENTE
                    nova_linha = [
                        data_br,                         # Data
                        hora_registro,                   # Hora
                        responsavel.strip(),             # Responsavel
                        int(clientes),                   # Clientes_Atendidos
                        prato_sel,                       # ID_Prato
                        round(float(prod_inicial), 3),   # Prod_Inicial_KG
                        round(float(reposicao), 3),      # Reposicao_KG
                        round(float(sobra_buffet), 3),   # Sobra_Buffet_KG
                        round(float(descarte), 3),       # Descarte_KG
                        observacoes.strip()              # Observacoes
                    ]
                    sheet.append_row(nova_linha)
                    st.cache_data.clear()
                    st.success(f"✅ **{prato_sel}** registrado às {hora_registro}!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar na planilha: {e}")