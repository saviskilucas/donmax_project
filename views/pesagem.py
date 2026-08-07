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
        return sorted([p for p in lista if p])
    except Exception:
        return sorted(["Arroz", "Feijão", "Barreado", "Carne 1", "Carne 2", "Salada", "Sobremesa"])

def render():
    # 1. TRAVA PRINCIPAL DE ACESSO
    if not tem_permissao("pesagem:visualizar"):
        st.error("⛔ Você não tem permissão para acessar a tela de Lançamentos.")
        return

    pratos_lista = buscar_pratos_cadastrados()
    fuso_brasilia = ZoneInfo("America/Sao_Paulo")
    agora_br = datetime.now(fuso_brasilia)

    pode_data = tem_permissao("campo:data")
    pode_prato = tem_permissao("campo:prato")
    pode_pesos = tem_permissao("campo:pesos")
    pode_clientes = tem_permissao("campo:clientes")
    pode_obs = tem_permissao("campo:obs")

    # Divisão do Formulário em duas Abas
    aba_prato, aba_cliente = st.tabs(["🍲 LANÇAMENTO DE PRATOS (COZINHA)", "👥 CLIENTES ATENDIDOS (CAIXA)"])

    # =========================================================
    # ABA 1: FORMULÁRIO DE PRATOS / PESAGEM
    # =========================================================
    with aba_prato:
        if not pode_prato and not pode_pesos:
            st.warning("🔒 Seu perfil não tem permissão para lançar pratos e medições de pesagem.")
        else:
            with st.form("form_pesagem_pratos", clear_on_submit=True):
                st.markdown("<div class='section-header'>1. INFORMAÇÕES DO SERVIÇO</div>", unsafe_allow_html=True)
                
                col_dt, col_hr = st.columns(2)
                with col_dt:
                    if pode_data:
                        data_sel = st.date_input("Data do Serviço", value=agora_br.date(), format="DD/MM/YYYY", key="dt_prato")
                    else:
                        data_sel = agora_br.date()
                        st.text_input("Data do Serviço", value=data_sel.strftime("%d/%m/%Y"), disabled=True, key="dt_prato_dis")
                        
                with col_hr:
                    hora_atual_str = agora_br.strftime("%H:%M")
                    st.text_input("Hora do Registro", value=hora_atual_str, disabled=True, key="hr_prato")

                responsavel = st.text_input("Responsável pelo Turno", value=st.session_state.get("usuario_logado", ""), key="resp_prato")
                
                st.markdown("<div class='section-header'>2. PREPARAÇÃO / PRATO</div>", unsafe_allow_html=True)
                prato_sel = st.selectbox("Selecione o Prato", pratos_lista if pratos_lista else ["Nenhum prato cadastrado"], key="sel_prato")

                st.markdown("<div class='section-header'>3. MEDIÇÕES DA BALANÇA (KG)</div>", unsafe_allow_html=True)
                st.caption("ℹ️ Pressione + ou - para alterar de 100g em 100g (0.100 kg)")
                
                col1, col2 = st.columns(2)
                with col1:
                    prod_inicial = st.number_input("Produção Inicial (kg)", min_value=0.0, step=0.100, format="%.3f", key="p_ini")
                    reposicao = st.number_input("Reposição Total (kg)", min_value=0.0, step=0.100, format="%.3f", key="repo")
                with col2:
                    sobra_buffet = st.number_input("Sobra Buffet (kg)", min_value=0.0, step=0.100, format="%.3f", key="sobra")
                    descarte = st.number_input("Descarte Total (kg)", min_value=0.0, step=0.100, format="%.3f", key="desc")

                observacoes = st.text_area("Observações (Opcional)", placeholder="Ex: Sobra de carne devido ao tempo chuvoso...", key="obs_prato")

                btn_salvar_prato = st.form_submit_button("💾 SALVAR LANÇAMENTO DO PRATO")

                if btn_salvar_prato:
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
                            
                            nova_linha = [
                                data_br,                         # Data
                                hora_registro,                   # Hora (formato original do formulário)
                                responsavel.strip(),             # Responsavel
                                "",                              # Clientes_Atendidos
                                prato_sel,                       # ID_Prato
                                round(float(prod_inicial), 3),   # Prod_Inicial_KG
                                round(float(reposicao), 3),      # Reposicao_KG
                                round(float(sobra_buffet), 3),   # Sobra_Buffet_KG
                                round(float(descarte), 3),       # Descarte_KG
                                observacoes.strip()              # Observacoes
                            ]
                            sheet.append_row(nova_linha)
                            st.cache_data.clear()
                            st.success(f"✅ Prato **{prato_sel}** registrado às {hora_registro}!")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar na planilha: {e}")

    # =========================================================
    # ABA 2: FORMULÁRIO DE CLIENTES / CAIXA
    # =========================================================
    with aba_cliente:
        if not pode_clientes:
            st.warning("🔒 Seu perfil não tem permissão para lançar quantidade de clientes.")
        else:
            with st.form("form_pesagem_clientes", clear_on_submit=True):
                st.markdown("<div class='section-header'>1. INFORMAÇÕES DO SERVIÇO</div>", unsafe_allow_html=True)
                
                col_dt_c, col_hr_c = st.columns(2)
                with col_dt_c:
                    if pode_data:
                        data_sel_c = st.date_input("Data do Serviço", value=agora_br.date(), format="DD/MM/YYYY", key="dt_cli")
                    else:
                        data_sel_c = agora_br.date()
                        st.text_input("Data do Serviço", value=data_sel_c.strftime("%d/%m/%Y"), disabled=True, key="dt_cli_dis")
                        
                with col_hr_c:
                    hora_atual_str_c = agora_br.strftime("%H:%M")
                    st.text_input("Hora do Registro", value=hora_atual_str_c, disabled=True, key="hr_cli")

                responsavel_c = st.text_input("Responsável pelo Turno", value=st.session_state.get("usuario_logado", ""), key="resp_cli")
                
                st.markdown("<div class='section-header'>2. REGISTRO DE ATENDIMENTO</div>", unsafe_allow_html=True)
                clientes_c = st.number_input("Clientes Atendidos no Dia", min_value=0, step=1, value=0, key="num_cli")
                observacoes_c = st.text_area("Observações (Opcional)", placeholder="Ex: Baixo movimento devido ao feriado...", key="obs_cli")

                btn_salvar_cliente = st.form_submit_button("💾 SALVAR REGISTRO DE CLIENTES")

                if btn_salvar_cliente:
                    if not tem_permissao("pesagem:criar"):
                        st.error("⛔ Seu perfil não tem permissão para salvar registros.")
                    elif not responsavel_c.strip():
                        st.error("⚠️ Preencha o nome do Responsável antes de salvar.")
                    elif clientes_c <= 0:
                        st.warning("⚠️ Informe uma quantidade válida de clientes atendidos.")
                    else:
                        try:
                            sheet = conectar_gsheets().worksheet("Lancamentos_Diarios")
                            agora_salvamento = datetime.now(fuso_brasilia)
                            data_br_c = data_sel_c.strftime("%d/%m/%Y")
                            hora_registro_c = agora_salvamento.strftime("%H:%M")
                            
                            nova_linha = [
                                data_br_c,                       # Data
                                hora_registro_c,                 # Hora (formato original do formulário)
                                responsavel_c.strip(),           # Responsavel
                                int(clientes_c),                 # Clientes_Atendidos
                                "",                              # ID_Prato
                                "",                              # Prod_Inicial_KG
                                "",                              # Reposicao_KG
                                "",                              # Sobra_Buffet_KG
                                "",                              # Descarte_KG
                                observacoes_c.strip()            # Observacoes
                            ]
                            sheet.append_row(nova_linha)
                            st.cache_data.clear()
                            st.success(f"✅ Registro de **{int(clientes_c)} clientes** salvo às {hora_registro_c}!")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar na planilha: {e}")