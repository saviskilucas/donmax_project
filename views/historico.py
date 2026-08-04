import streamlit as st
import pandas as pd
import plotly.express as px
from auth import tem_permissao, conectar_gsheets

def carregar_dados():
    try:
        sheet = conectar_gsheets().worksheet("Lancamentos_Diarios")
        dados = sheet.get_all_records()
        df = pd.DataFrame(dados)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do histórico: {e}")
        return pd.DataFrame()

def render():
    if not tem_permissao("dashboard:visualizar"):
        st.error("⛔ Você não tem permissão para acessar o Dashboard/Histórico.")
        return

    st.markdown("<div class='section-header'>📊 PAINEL E HISTÓRICO</div>", unsafe_allow_html=True)

    df = carregar_dados()

    if df.empty:
        st.info("Nenhum registro encontrado no banco de dados.")
        return

    # Normalização de nomes de colunas
    colunas_map = {
        "Data": "data",
        "Responsável": "responsavel",
        "Clientes": "clientes",
        "Prato": "prato",
        "Produção Inicial": "prod_inicial",
        "Reposição Total": "reposicao",
        "Sobra Limpa": "sobra_limpa",
        "Sobra Buffet": "sobra_buffet",
        "Descarte Total": "descarte",
        "Observações": "observacoes"
    }
    df = df.rename(columns=colunas_map)

    # Converter colunas numéricas
    cols_numericas = ["prod_inicial", "reposicao", "sobra_limpa", "sobra_buffet", "descarte", "clientes"]
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Filtro Rápido por Período
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df = df.sort_values(by="data", ascending=False)

        datas_unicas = df["data"].dt.date.dropna().unique()
        if len(datas_unicas) > 0:
            data_sel = st.selectbox("Selecione o Dia para Análise", options=datas_unicas)
            df_filtrado = df[df["data"].dt.date == data_sel]
        else:
            df_filtrado = df
    else:
        df_filtrado = df

    # =========================================================
    # 1. MÉTRICAS PRINCIPAIS (CARDS)
    # =========================================================
    total_prod = df_filtrado["prod_inicial"].sum() + df_filtrado["reposicao"].sum()
    total_sobra = df_filtrado["sobra_limpa"].sum() + df_filtrado["sobra_buffet"].sum()
    total_descarte = df_filtrado["descarte"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Produção Total", f"{total_prod:.1f} kg")
    m2.metric("Sobras Totais", f"{total_sobra:.1f} kg")
    m3.metric("Descarte Total", f"{total_descarte:.1f} kg")

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================
    # 2. PRIMEIRO GRÁFICO: BALANÇO DA COZINHA (BARRAS HORIZONTAIS)
    # =========================================================
    st.markdown("### ⚖️ Balanço da Cozinha por Prato (Kg)")
    
    # Agrupamento para somar métricas por prato
    df_balanco = df_filtrado.groupby("prato")[["prod_inicial", "reposicao", "sobra_limpa", "sobra_buffet", "descarte"]].sum().reset_index()
    
    # Transformar em formato longo (Melt) para Plotly aceitar barras agrupadas
    df_melted = df_balanco.melt(
        id_vars=["prato"], 
        value_vars=["prod_inicial", "reposicao", "sobra_limpa", "sobra_buffet", "descarte"],
        var_name="Métrica", 
        value_name="Quilogramas"
    )

    # Mapeamento de nomes amigáveis para a legenda
    nomes_metricas = {
        "prod_inicial": "Produção Inicial",
        "reposicao": "Reposição",
        "sobra_limpa": "Sobra Limpa",
        "sobra_buffet": "Sobra Buffet",
        "descarte": "Descarte"
    }
    df_melted["Métrica"] = df_melted["Métrica"].map(nomes_metricas)

    # Gráfico de Barras HORIZONTAIS (x=Quilogramas, y=prato, orientation='h')
    fig_barras = px.bar(
        df_melted,
        x="Quilogramas",
        y="prato",
        color="Métrica",
        barmode="group",
        orientation="h",
        color_discrete_sequence=["#D32F2F", "#FF9800", "#4CAF50", "#2196F3", "#F44336"]
    )

    fig_barras.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="Peso (Kg)",
        yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_barras, use_container_width=True)

    # =========================================================
    # 3. SEGUNDO GRÁFICO: DISTRIBUIÇÃO DE SOBRAS E DESCARTE (PIZZA)
    # =========================================================
    st.markdown("### 🍕 Distribuição de Sobras e Descarte")

    metricas_pizza = {
        "Sobra Limpa": df_filtrado["sobra_limpa"].sum(),
        "Sobra Buffet": df_filtrado["sobra_buffet"].sum(),
        "Descarte": df_filtrado["descarte"].sum()
    }
    
    df_pizza = pd.DataFrame(list(metricas_pizza.items()), columns=["Tipo", "Quantidade"])

    if df_pizza["Quantidade"].sum() > 0:
        fig_pizza = px.pie(
            df_pizza,
            values="Quantidade",
            names="Tipo",
            color="Tipo",
            hole=0.4,
            color_discrete_map={
                "Sobra Limpa": "#4CAF50",
                "Sobra Buffet": "#FF9800",
                "Descarte": "#F44336"
            }
        )

        fig_pizza.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )

        st.plotly_chart(fig_pizza, use_container_width=True)
    else:
        st.info("Sem dados de sobras/descarte para exibir o gráfico de pizza neste dia.")