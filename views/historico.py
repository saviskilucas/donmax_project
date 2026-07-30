import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

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

def render():
    st.markdown("<div class='section-header'>📊 DASHBOARD DE DESCARTE</div>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([0.6, 0.4])
    with col_b:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    dados = carregar_dados_painel()
    
    if dados:
        df = pd.DataFrame(dados)
        
        # Tratamento de colunas numéricas
        colunas_num = ['Descarte Total', 'Produção Inicial', 'Reposição Total', 'Sobra Limpa', 'Sobra Buffet']
        for col in colunas_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

        # Cartões KPI - Layout Mobile
        total_descarte = df['Descarte Total'].sum() if 'Descarte Total' in df.columns else 0
        total_sobra_limpa = df['Sobra Limpa'].sum() if 'Sobra Limpa' in df.columns else 0
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Descarte Total", f"{total_descarte:.3f} kg")
        with c2:
            st.metric("Sobra Limpa", f"{total_sobra_limpa:.3f} kg")

        st.markdown("---")

        # GRÁFICO 1: Descarte por Prato (Barras Horizontais para Leitura no Celular)
        if 'Prato' in df.columns and 'Descarte Total' in df.columns:
            df_prato = df.groupby('Prato')['Descarte Total'].sum().reset_index().sort_values(by='Descarte Total', ascending=True)
            
            fig_bar = px.bar(
                df_prato, 
                x='Descarte Total', 
                y='Prato', 
                orientation='h',
                title="<b>Descarte Acumulado por Prato (kg)</b>",
                color='Descarte Total',
                color_continuous_scale='Reds'
            )
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#FFFFFF"),
                margin=dict(l=10, r=10, t=40, b=10),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

        # GRÁFICO 2: Evolução do Descarte no Tempo (Linhas)
        if 'Data' in df.columns and 'Descarte Total' in df.columns:
            df_data = df.groupby('Data')['Descarte Total'].sum().reset_index()
            
            fig_line = px.line(
                df_data, 
                x='Data', 
                y='Descarte Total', 
                markers=True,
                title="<b>Evolução Diária do Descarte (kg)</b>"
            )
            fig_line.update_traces(line_color='#FF5252', marker=dict(size=8))
            fig_line.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#FFFFFF"),
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})

        # GRÁFICO 3: Proporção de Sobras vs Descarte (Rosca)
        if 'Sobra Buffet' in df.columns and 'Sobra Limpa' in df.columns and 'Descarte Total' in df.columns:
            dados_rosca = {
                'Tipo': ['Descarte', 'Sobra Limpa', 'Sobra Buffet'],
                'Peso': [df['Descarte Total'].sum(), df['Sobra Limpa'].sum(), df['Sobra Buffet'].sum()]
            }
            df_rosca = pd.DataFrame(dados_rosca)
            
            fig_pie = px.pie(
                df_rosca, 
                names='Tipo', 
                values='Peso', 
                hole=0.4,
                title="<b>Distribuição de Sobras e Descarte</b>",
                color_discrete_sequence=['#B71C1C', '#4CAF50', '#FF9800']
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#FFFFFF"),
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        st.write("📋 **Últimas Pesagens Registradas:**")
        st.dataframe(df.tail(10).iloc[::-1], use_container_width=True, hide_index=True)

    else:
        st.info("Nenhum registro encontrado na planilha ainda.")