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

@st.cache_data(ttl=60)
def carregar_dados_painel():
    try:
        sheet = conectar_gsheets().worksheet("Lancamentos_Diarios")
        registros = sheet.get_all_records()
        
        # Se get_all_records falhar ou vier vazio, tenta ler via get_all_values
        if not registros:
            valores = sheet.get_all_values()
            if len(valores) > 1:
                cabecalho = [str(c).strip() for c in valores[0]]
                linhas = valores[1:]
                registros = [dict(zip(cabecalho, linha)) for linha in linhas]
        else:
            # Limpa espaços nos nomes das chaves do dicionário
            registros_limpos = []
            for r in registros:
                r_limpo = {str(k).strip(): v for k, v in r.items()}
                registros_limpos.append(r_limpo)
            registros = registros_limpos

        return registros
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        return []

def converter_para_numero(serie):
    """Converte valores com vírgula, texto ou espaços para float limpo."""
    return pd.to_numeric(
        serie.astype(str)
        .str.replace('kg', '', case=False)
        .str.replace('R$', '', case=False)
        .str.replace(' ', '')
        .str.replace(',', '.'), 
        errors='coerce'
    ).fillna(0.0)

def render():
    st.markdown("<div class='section-header'>📊 DASHBOARD COMPLETO DA COZINHA</div>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([0.6, 0.4])
    with col_b:
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    dados = carregar_dados_painel()
    
    if dados:
        df = pd.DataFrame(dados)
        
        # Normaliza o nome das colunas do DataFrame para evitar erros de digitação
        mapa_colunas = {col: col.strip() for col in df.columns}
        df.rename(columns=mapa_colunas, inplace=True)

        # Mapeamento e conversão forçada de todas as colunas numéricas
        colunas_numericas = [
            'Produção Inicial', 'Reposicao Total', 'Reposição Total', 
            'Sobra Limpa', 'Sobra Buffet', 'Descarte Total', 'Clientes'
        ]
        
        for col in colunas_numericas:
            if col in df.columns:
                df[col] = converter_para_numero(df[col])
            else:
                df[col] = 0.0

        # Trata coluna de Reposição caso esteja sem acento no banco
        col_reposicao = 'Reposição Total' if 'Reposição Total' in df.columns else 'Reposicao Total'

        # Cálculo de Produção Total
        df['Produção Total'] = df['Produção Inicial'] + df[col_reposicao]

        # Totais Reais
        tot_prod = float(df['Produção Total'].sum())
        tot_descarte = float(df['Descarte Total'].sum())
        tot_sobra_limpa = float(df['Sobra Limpa'].sum())
        tot_sobra_buffet = float(df['Sobra Buffet'].sum())
        
        # Pega a soma ou o máximo de clientes dependendo dos registros
        tot_clientes = float(df['Clientes'].max()) if df['Clientes'].max() > 0 else float(df['Clientes'].sum())
        
        descarte_por_cliente_g = (tot_descarte / tot_clientes * 1000) if tot_clientes > 0 else 0.0

        # =========================================================
        # CARDS E MÉTRICAS
        # =========================================================
        st.markdown("##### 📌 **Resumo de Produção e Sobras**")
        kpi1, kpi2 = st.columns(2)
        with kpi1:
            st.metric("Produção Total", f"{tot_prod:.3f} kg")
            st.metric("Sobra Limpa (Aproveitável)", f"{tot_sobra_limpa:.3f} kg")
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
        # GRÁFICO 1: BALANÇO GERAL DE PRODUÇÃO
        # =========================================================
        st.markdown("##### ⚖️ **Balanço Geral de Produção (kg)**")
        df_balanco = pd.DataFrame({
            'Categoria': ['Prod. Inicial', 'Reposição', 'Sobra Limpa', 'Sobra Buffet', 'Descarte Total'],
            'Peso (kg)': [
                float(df['Produção Inicial'].sum()),
                float(df[col_reposicao].sum()),
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
        # GRÁFICO 2: DESCARTE POR PRATO
        # =========================================================
        col_prato = 'Prato' if 'Prato' in df.columns else None
        if col_prato:
            st.markdown("##### 🍲 **Ranking de Descarte por Prato (kg)**")
            df_prato = df.groupby(col_prato)['Descarte Total'].sum().reset_index().sort_values(by='Descarte Total', ascending=True)
            
            fig_bar = px.bar(
                df_prato, x='Descarte Total', y=col_prato, orientation='h',
                color='Descarte Total', color_continuous_scale='Reds', text_auto='.3f'
            )
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#FFFFFF"), margin=dict(l=10, r=10, t=10, b=10),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

        # =========================================================
        # GRÁFICO 3: PROPORÇÃO DE SOBRAS E DESCARTE
        # =========================================================
        st.markdown("##### 🍕 **Proporção do Destino dos Alimentos**")
        df_rosca = pd.DataFrame({
            'Tipo': ['Descarte', 'Sobra Limpa', 'Sobra Buffet'],
            'Peso': [tot_descarte, tot_sobra_limpa, tot_sobra_buffet]
        })
        
        # Só exibe se houver algum valor maior que zero
        if df_rosca['Peso'].sum() > 0:
            fig_pie = px.pie(
                df_rosca, names='Tipo', values='Peso', hole=0.45,
                color_discrete_sequence=['#F44336', '#4CAF50', '#FF9800']
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#FFFFFF"),
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
        else:
            st.caption("Sem dados de sobras para exibir gráfico de rosca.")

        # =========================================================
        # GRÁFICO 4: EVOLUÇÃO TEMPORAL
        # =========================================================
        col_data = 'Data' if 'Data' in df.columns else None
        if col_data:
            st.markdown("##### 📈 **Evolução do Descarte Diário (kg)**")
            df_data = df.groupby(col_data)['Descarte Total'].sum().reset_index()
            
            fig_line = px.line(
                df_data, x=col_data, y='Descarte Total', markers=True
            )
            fig_line.update_traces(line_color='#FF5252', marker=dict(size=8))
            fig_line.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#FFFFFF"), margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})

        # =========================================================
        # GRÁFICO 5: REGISTROS POR RESPONSÁVEL
        # =========================================================
        col_resp = 'Responsavel' if 'Responsavel' in df.columns else ('Responsável' if 'Responsável' in df.columns else None)
        if col_resp:
            st.markdown("##### 👤 **Pesagens Registradas por Responsável**")
            df_resp = df.groupby(col_resp).size().reset_index(name='Registros')
            fig_resp = px.pie(df_resp, names=col_resp, values='Registros', hole=0.3)
            fig_resp.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#FFFFFF"),
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_resp, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        st.write("📋 **Tabela dos Registros Encontrados:**")
        st.dataframe(df.tail(10).iloc[::-1], use_container_width=True, hide_index=True)

    else:
        st.info("Nenhum registro encontrado na planilha ainda.")