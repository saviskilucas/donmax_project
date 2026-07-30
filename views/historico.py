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
    st.markdown("<div class='section-header'>📊 DASHBOARD COMPLETO DA COZINHA</div>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([0.6, 0.4])
    with col_b:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    dados = carregar_dados_painel()
    
    if dados:
        df = pd.DataFrame(dados)
        
        # Tratamento e conversão de colunas numéricas
        colunas_num = ['Produção Inicial', 'Reposição Total', 'Sobra Limpa', 'Sobra Buffet', 'Descarte Total', 'Clientes']
        for col in colunas_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

        # Cálculos Derivados
        if 'Produção Inicial' in df.columns and 'Reposição Total' in df.columns:
            df['Produção Total'] = df['Produção Inicial'] + df['Reposição Total']
        else:
            df['Produção Total'] = 0

        # Totais para os Cards
        tot_prod = df['Produção Total'].sum()
        tot_descarte = df['Descarte Total'].sum() if 'Descarte Total' in df.columns else 0
        tot_sobra_limpa = df['Sobra Limpa'].sum() if 'Sobra Limpa' in df.columns else 0
        tot_sobra_buffet = df['Sobra Buffet'].sum() if 'Sobra Buffet' in df.columns else 0
        tot_clientes = df['Clientes'].max() if 'Clientes' in df.columns else 0
        
        # Cálculo de Descarte Médio por Cliente (g/cliente)
        descarte_por_cliente_g = (tot_descarte / tot_clientes * 1000) if tot_clientes > 0 else 0

        # =========================================================
        # CARDS E MÉTRICAS
        # =========================================================
        st.markdown("##### 📌 **Resumo de Produção e Sobras**")
        kpi1, kpi2 = st.columns(2)
        with kpi1:
            st.metric("Produção Total", f"{tot_prod:.3f} kg")
            st.metric("Sobra Limpa (Reaproveitável)", f"{tot_sobra_limpa:.3f} kg")
        with kpi2:
            st.metric("Descarte Total", f"{tot_descarte:.3f} kg")
            st.metric("Sobra Buffet", f"{tot_sobra_buffet:.3f} kg")

        st.markdown("##### 👥 **Eficiência e Atendimento**")
        kpi3, kpi4 = st.columns(2)
        with kpi3:
            st.metric("Clientes Atendidos", f"{int(tot_clientes)}")
        with kpi4:
            st.metric("Descarte p/ Cliente", f"{descarte_por_cliente_g:.1f} g/pess.")

        st.markdown("---")

        # =========================================================
        # GRÁFICO 1: BALANÇO GERAL DE PRODUÇÃO (Produção vs Sobras vs Descarte)
        # =========================================================
        st.markdown("##### ⚖️ **Balanço Geral de Produção (kg)**")
        df_balanco = pd.DataFrame({
            'Categoria': ['Prod. Inicial', 'Reposição', 'Sobra Limpa', 'Sobra Buffet', 'Descarte Total'],
            'Peso (kg)': [
                df['Produção Inicial'].sum() if 'Produção Inicial' in df.columns else 0,
                df['Reposição Total'].sum() if 'Reposição Total' in df.columns else 0,
                tot_sobra_limpa,
                tot_sobra_buffet,
                tot_descarte
            ]
        })
        fig_balanco = px.bar(
            df_balanco, x='Categoria', y='Peso (kg)',
            text_auto='.3f',
            color='Categoria',
            color_discrete_sequence=['#2196F3', '#03A9F4', '#4CAF50', '#FF9800', '#F44336']
        )
        fig_balanco.update_layout(
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#FFFFFF"), margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig_balanco, use_container_width=True, config={'displayModeBar': False})

        # =========================================================
        # GRÁFICO 2: DESCARTE POR PRATO (BARRAS HORIZONTAIS MOBILE)
        # =========================================================
        if 'Prato' in df.columns and 'Descarte Total' in df.columns:
            st.markdown("##### 🍲 **Ranking de Descarte por Prato (kg)**")
            df_prato = df.groupby('Prato')['Descarte Total'].sum().reset_index().sort_values(by='Descarte Total', ascending=True)
            
            fig_bar = px.bar(
                df_prato, x='Descarte Total', y='Prato', orientation='h',
                color='Descarte Total', color_continuous_scale='Reds', text_auto='.3f'
            )
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#FFFFFF"), margin=dict(l=10, r=10, t=10, b=10),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

        # =========================================================
        # GRÁFICO 3: PROPORÇÃO DE SOBRAS E DESCARTE (ROSCA)
        # =========================================================
        st.markdown("##### 🍕 **Proporção do Destino dos Alimentos**")
        df_rosca = pd.DataFrame({
            'Tipo': ['Descarte', 'Sobra Limpa', 'Sobra Buffet'],
            'Peso': [tot_descarte, tot_sobra_limpa, tot_sobra_buffet]
        })
        fig_pie = px.pie(
            df_rosca, names='Tipo', values='Peso', hole=0.45,
            color_discrete_sequence=['#F44336', '#4CAF50', '#FF9800']
        )
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#FFFFFF"),
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

        # =========================================================
        # GRÁFICO 4: EVOLUÇÃO TEMPORAL (POR DATA E HORA)
        # =========================================================
        if 'Data' in df.columns and 'Descarte Total' in df.columns:
            st.markdown("##### 📈 **Evolução do Descarte Diário (kg)**")
            df_data = df.groupby('Data')['Descarte Total'].sum().reset_index()
            
            fig_line = px.line(
                df_data, x='Data', y='Descarte Total', markers=True
            )
            fig_line.update_traces(line_color='#FF5252', marker=dict(size=8))
            fig_line.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#FFFFFF"), margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})

        # =========================================================
        # GRÁFICO 5: REGISTROS POR RESPONSÁVEL DO TURNO
        # =========================================================
        if 'Responsavel' in df.columns:
            st.markdown("##### 👤 **Pesagens Registradas por Responsável**")
            df_resp = df.groupby('Responsavel').size().reset_index(name='Registros')
            fig_resp = px.pie(df_resp, names='Responsavel', values='Registros', hole=0.3)
            fig_resp.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#FFFFFF"),
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_resp, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        st.write("📋 **Últimas Pesagens Registradas:**")
        st.dataframe(df.tail(10).iloc[::-1], use_container_width=True, hide_index=True)

    else:
        st.info("Nenhum registro encontrado na planilha ainda.")