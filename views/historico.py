import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from zoneinfo import ZoneInfo
import io

# ReportLab para geração do PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

@st.cache_resource
def conectar_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(credentials).open("Planilha Don Max")

@st.cache_data(ttl=30)
def carregar_dados_painel():
    try:
        sheet = conectar_gsheets().worksheet("Lancamentos_Diarios")
        registros = sheet.get_all_records()
        
        if not registros:
            valores = sheet.get_all_values()
            if len(valores) > 1:
                cabecalho = [str(c).strip() for c in valores[0]]
                linhas = valores[1:]
                registros = [dict(zip(cabecalho, linha)) for linha in linhas]
        else:
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
    return pd.to_numeric(
        serie.astype(str)
        .str.replace('kg', '', case=False)
        .str.replace('R$', '', case=False)
        .str.replace(' ', '')
        .str.replace(',', '.'), 
        errors='coerce'
    ).fillna(0.0)

# =========================================================
# GERADOR DE PDF MODERNO COM GRÁFICOS E FUSO DE BRASÍLIA
# =========================================================
def gerar_pdf_relatorio(df, tot_prod, tot_descarte, tot_sobra, tot_clientes, dt_inicio, dt_fim, figuras_dict):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    elements = []
    styles = getSampleStyleSheet()

    # Estilos Customizados
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#B71C1C'),
        spaceAfter=4
    )
    
    style_sub = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12
    )

    style_sec_title = ParagraphStyle(
        'SecTitle',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#B71C1C'),
        spaceAfter=8,
        spaceBefore=12
    )

    style_card_title = ParagraphStyle(
        'CardTitle',
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor('#888888'),
        alignment=1
    )

    style_card_val = ParagraphStyle(
        'CardVal',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=colors.HexColor('#111111'),
        alignment=1
    )

    # 1. DATA E HORA DE BRASÍLIA
    agora_brasilia = datetime.now(ZoneInfo("America/Sao_Paulo"))
    dt_emissao_str = agora_brasilia.strftime('%d/%m/%Y às %H:%M:%S')

    # CABEÇALHO DO RELATÓRIO
    elements.append(Paragraph("DON MAX BUFFET - RELATÓRIO EXECUTIVO", style_title))
    dt_str = f"Período: {dt_inicio.strftime('%d/%m/%Y')} até {dt_fim.strftime('%d/%m/%Y')} | Gerado em: {dt_emissao_str} (Horário de Brasília)"
    elements.append(Paragraph(dt_str, style_sub))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#B71C1C'), spaceAfter=15))

    # 2. CARDS DE INDICADORES (RESUMO)
    cards_data = [
        [
            Paragraph("PRODUÇÃO TOTAL", style_card_title),
            Paragraph("DESCARTE TOTAL", style_card_title),
            Paragraph("SOBRA BUFFET", style_card_title),
            Paragraph("ATENDIMENTO", style_card_title)
        ],
        [
            Paragraph(f"<b>{tot_prod:.3f} kg</b>", style_card_val),
            Paragraph(f"<font color='#B71C1C'><b>{tot_descarte:.3f} kg</b></font>", style_card_val),
            Paragraph(f"<b>{tot_sobra:.3f} kg</b>", style_card_val),
            Paragraph(f"<b>{int(tot_clientes)} clientes</b>", style_card_val)
        ]
    ]

    t_cards = Table(cards_data, colWidths=[130, 130, 130, 130])
    t_cards.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#E0E0E0')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_cards)
    elements.append(Spacer(1, 10))

    # 3. RENDERIZAÇÃO DOS GRÁFICOS NO PDF
    for titulo, fig in figuras_dict.items():
        if fig is not None:
            elements.append(Paragraph(f"<b>{titulo}</b>", style_sec_title))
            try:
                # Converte figura do Plotly para PNG em memória
                img_bytes = fig.to_image(format="png", width=700, height=350, scale=2)
                img_stream = io.BytesIO(img_bytes)
                elements.append(Image(img_stream, width=520, height=260))
                elements.append(Spacer(1, 10))
            except Exception as e:
                elements.append(Paragraph(f"<i>[Não foi possível renderizar este gráfico no PDF: {e}]</i>", style_sub))

    # 4. TABELA DE LANÇAMENTOS
    elements.append(Paragraph("<b>Detalhamento de Lançamentos</b>", style_sec_title))

    col_names_pdf = ['Data', 'Prato / Item', 'Prod. Ini', 'Reposição', 'Sobra Buf.', 'Descarte']
    table_data = [col_names_pdf]

    for _, row in df.iterrows():
        linha = [
            str(row.get('Data', '')),
            str(row.get('ID_Prato', '-'))[:22],
            f"{float(converter_para_numero(pd.Series([row.get('Prod_Inicial_KG', 0)]))[0]):.3f} kg",
            f"{float(converter_para_numero(pd.Series([row.get('Reposicao_KG', 0)]))[0]):.3f} kg",
            f"{float(converter_para_numero(pd.Series([row.get('Sobra_Buffet_KG', 0)]))[0]):.3f} kg",
            f"{float(converter_para_numero(pd.Series([row.get('Descarte_KG', 0)]))[0]):.3f} kg",
        ]
        table_data.append(linha)

    t_table = Table(table_data, colWidths=[65, 165, 70, 70, 75, 75])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#B71C1C')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'LEFT'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0E0E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9F9F9')]),
        ('TOPPADDING', (0,1), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
    ]))

    elements.append(t_table)

    # CONSTRÓI O DOCUMENTO
    doc.build(elements)
    buffer.seek(0)
    return buffer


def render():
    st.markdown("""
        <style>
        div[data-baseweb="input"] input {
            caret-color: transparent !important;
            user-select: none !important;
        }

        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 8px !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            width: 50% !important;
            min-width: 0 !important;
            flex: 1 1 0% !important;
        }

        .js-plotly-plot .plotly .draglayer {
            pointer-events: none !important;
        }

        .metric-card {
            background-color: #1E1E1E;
            border: 1px solid #2D2D2D;
            border-left: 4px solid #B71C1C;
            border-radius: 12px;
            padding: 10px 6px;
            text-align: center;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.4);
            margin-bottom: 8px;
            width: 100%;
            box-sizing: border-box;
        }
        .metric-card-title {
            font-size: 0.70rem;
            font-weight: 700;
            color: #A0A0A0;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            margin-bottom: 3px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .metric-card-value {
            font-size: 1.10rem;
            font-weight: 800;
            color: #FFFFFF;
            line-height: 1.1;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>DASHBOARD</div>", unsafe_allow_html=True)

    dados = carregar_dados_painel()
    
    if dados:
        df = pd.DataFrame(dados)
        
        if 'Data' in df.columns:
            df['Data_DT'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce').dt.date
        else:
            df['Data_DT'] = date.today()

        # FILTRO DE DATA
        data_min = df['Data_DT'].min() if not df['Data_DT'].dropna().empty else date.today()
        data_max = df['Data_DT'].max() if not df['Data_DT'].dropna().empty else date.today()

        st.markdown("##### Filtrar por Período")
        filtro_datas = st.date_input(
            "Selecione o intervalo no calendário:",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max,
            format="DD/MM/YYYY"
        )

        if isinstance(filtro_datas, tuple) and len(filtro_datas) == 2:
            dt_inicio, dt_fim = filtro_datas
            df = df[(df['Data_DT'] >= dt_inicio) & (df['Data_DT'] <= dt_fim)]

        if df.empty:
            st.warning("⚠️ Nenhum registro encontrado para o período selecionado.")
            return

        # CONVERSÃO DOS DADOS
        prod_ini = converter_para_numero(df['Prod_Inicial_KG']) if 'Prod_Inicial_KG' in df.columns else pd.Series([0]*len(df))
        reposicao = converter_para_numero(df['Reposicao_KG']) if 'Reposicao_KG' in df.columns else pd.Series([0]*len(df))
        sobra_buffet = converter_para_numero(df['Sobra_Buffet_KG']) if 'Sobra_Buffet_KG' in df.columns else pd.Series([0]*len(df))
        descarte = converter_para_numero(df['Descarte_KG']) if 'Descarte_KG' in df.columns else pd.Series([0]*len(df))
        clientes = converter_para_numero(df['Clientes_Atendidos']) if 'Clientes_Atendidos' in df.columns else pd.Series([0]*len(df))

        df['Prod_Total_Calc'] = prod_ini + reposicao
        df['Descarte_Calc'] = descarte
        df['Sobra_Buffet_Calc'] = sobra_buffet

        tot_prod = float(df['Prod_Total_Calc'].sum())
        tot_descarte = float(descarte.sum())
        tot_sobra_buffet = float(sobra_buffet.sum())
        tot_clientes = float(clientes.sum())

        figuras_pdf = {}

        config_plotly_mobile = {
            'staticPlot': True,
            'displayModeBar': False
        }

        # INDICADORES DO PERÍODO
        st.markdown("##### Indicadores")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-card-title">Produção Total</div>
                    <div class="metric-card-value">{tot_prod:.3f} <span style="font-size:0.75rem">kg</span></div>
                </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #FF5252;">
                    <div class="metric-card-title">Descarte Total</div>
                    <div class="metric-card-value" style="color:#FF5252">{tot_descarte:.3f} <span style="font-size:0.75rem">kg</span></div>
                </div>
            """, unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #FFB74D;">
                    <div class="metric-card-title">Sobra Buffet</div>
                    <div class="metric-card-value" style="color:#FFB74D">{tot_sobra_buffet:.3f} <span style="font-size:0.75rem">kg</span></div>
                </div>
            """, unsafe_allow_html=True)
            
        with c4:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #AB47BC;">
                    <div class="metric-card-title">Atendimento</div>
                    <div class="metric-card-value" style="color:#E1BEE7">{int(tot_clientes)} <span style="font-size:0.75rem">clientes</span></div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 1. MATRIZ DE CALOR (HEATMAP) POR PRODUTO
        if 'ID_Prato' in df.columns:
            st.markdown("##### Matriz de Desempenho por Produto")

            df_matriz = df.groupby('ID_Prato').agg({
                'Prod_Total_Calc': 'sum',
                'Sobra_Buffet_Calc': 'sum',
                'Descarte_Calc': 'sum'
            }).reset_index()

            df_matriz['Perda_%'] = (df_matriz['Descarte_Calc'] / df_matriz['Prod_Total_Calc'] * 100).fillna(0)
            df_matriz = df_matriz.sort_values(by='Descarte_Calc', ascending=True)

            pratos = df_matriz['ID_Prato'].tolist()
            colunas_heatmap = ['Produção Total', 'Sobra Buffet', 'Descarte Total', '% Perda/Prod.']

            z_values = []
            text_values = []

            for _, row in df_matriz.iterrows():
                p_tot = row['Prod_Total_Calc']
                s_buf = row['Sobra_Buffet_Calc']
                desc = row['Descarte_Calc']
                pct = row['Perda_%']

                z_values.append([p_tot, s_buf, desc, pct])
                text_values.append([
                    f"{p_tot:.2f} kg",
                    f"{s_buf:.2f} kg",
                    f"{desc:.2f} kg",
                    f"{pct:.1f}%"
                ])

            fig_heatmap = go.Figure(data=go.Heatmap(
                z=z_values,
                x=colunas_heatmap,
                y=pratos,
                text=text_values,
                texttemplate="%{text}",
                textfont={"size": 11, "color": "#FFFFFF"},
                colorscale=[
                    [0.0, '#1E1E1E'],
                    [0.3, '#37474F'],
                    [0.6, '#D84315'],
                    [1.0, '#B71C1C']
                ],
                showscale=False
            ))

            altura_matriz = max(280, len(pratos) * 45)

            fig_heatmap.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#E0E0E0"),
                margin=dict(l=10, r=10, t=20, b=20),
                height=altura_matriz,
                xaxis=dict(fixedrange=True, side='top'),
                yaxis=dict(fixedrange=True)
            )

            st.plotly_chart(fig_heatmap, use_container_width=True, config=config_plotly_mobile)
            figuras_pdf['Matriz de Desempenho por Produto'] = fig_heatmap

        # 2. GRÁFICO 1: BALANÇO DE PRODUÇÃO
        st.markdown("##### Balanço da Cozinha")
        df_balanco = pd.DataFrame({
            'Categoria': ['Prod. Inicial', 'Reposição', 'Sobra Buffet', 'Descarte'],
            'Peso (kg)': [
                float(prod_ini.sum()),
                float(reposicao.sum()),
                tot_sobra_buffet,
                tot_descarte
            ]
        })
        fig_balanco = px.bar(
            df_balanco, x='Categoria', y='Peso (kg)',
            text_auto='.3f',
            color='Categoria',
            color_discrete_sequence=['#1E88E5', '#00ACC1', '#FB8C00', '#E53935']
        )
        fig_balanco.update_layout(
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#E0E0E0"),
            margin=dict(l=5, r=5, t=25, b=5),
            xaxis=dict(showgrid=False, fixedrange=True),
            yaxis=dict(showgrid=True, gridcolor='#2D2D2D', fixedrange=True)
        )
        st.plotly_chart(fig_balanco, use_container_width=True, config=config_plotly_mobile)
        figuras_pdf['Balanço da Cozinha'] = fig_balanco

        # 3. GRÁFICO 2: PROPORÇÃO SOBRA BUFFET VS DESCARTE
        st.markdown("##### Proporção Sobra Buffet vs Descarte")
        df_rosca = pd.DataFrame({
            'Tipo': ['Descarte Total', 'Sobra Buffet'],
            'Peso': [tot_descarte, tot_sobra_buffet]
        })
        if df_rosca['Peso'].sum() > 0:
            fig_pie = px.pie(
                df_rosca, names='Tipo', values='Peso', hole=0.5,
                color_discrete_sequence=['#E53935', '#FB8C00']
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#E0E0E0"),
                margin=dict(l=5, r=5, t=10, b=5),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True, config=config_plotly_mobile)
            figuras_pdf['Proporção Sobra Buffet vs Descarte'] = fig_pie

        # 4. GRÁFICO 3: EVOLUÇÃO TEMPORAL
        if 'Data' in df.columns:
            st.markdown("##### Linha do Tempo de Descarte")
            df_temp_data = pd.DataFrame({'Data': df['Data'], 'Descarte': descarte})
            df_temp_data['Data_DT'] = pd.to_datetime(df_temp_data['Data'], format='%d/%m/%Y', errors='coerce')
            df_data = df_temp_data.groupby(['Data_DT', 'Data'])['Descarte'].sum().reset_index()
            df_data = df_data.sort_values('Data_DT', ascending=True)
            
            fig_line = px.line(
                df_data, x='Data', y='Descarte', markers=True
            )
            fig_line.update_traces(line_color='#FF5252', marker=dict(size=7, color='#FFFFFF'))
            fig_line.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#E0E0E0"),
                margin=dict(l=5, r=5, t=10, b=5),
                xaxis=dict(showgrid=False, fixedrange=True, type='category'),
                yaxis=dict(showgrid=True, gridcolor='#2D2D2D', fixedrange=True)
            )
            st.plotly_chart(fig_line, use_container_width=True, config=config_plotly_mobile)
            figuras_pdf['Linha do Tempo de Descarte'] = fig_line

        # BOTÕES SUPERIORES: ATUALIZAR E GERAR PDF
        col_hdr_left, col_hdr_right = st.columns([0.5, 0.5])
        with col_hdr_left:
            if st.button("🔄 Atualizar", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        with col_hdr_right:
            # GERA O PDF COMPLETO COM GRÁFICOS E HORA DE BRASÍLIA
            pdf_bytes = gerar_pdf_relatorio(
                df, tot_prod, tot_descarte, tot_sobra_buffet, tot_clientes,
                filtro_datas[0] if isinstance(filtro_datas, tuple) else data_min,
                filtro_datas[1] if isinstance(filtro_datas, tuple) else data_max,
                figuras_pdf
            )
            st.download_button(
                label="📄 Baixar PDF",
                data=pdf_bytes,
                file_name=f"Relatorio_DonMax_{datetime.now().strftime('%d%m%Y')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        # TABELA DE REGISTROS
        st.markdown("---")
        st.markdown("##### Lançamentos")
        
        df_exibicao = df.copy()
        if 'Data_DT' in df_exibicao.columns:
            df_exibicao.drop(columns=['Data_DT'], inplace=True)
        if 'Prod_Total_Calc' in df_exibicao.columns:
            df_exibicao.drop(columns=['Prod_Total_Calc', 'Descarte_Calc', 'Sobra_Buffet_Calc'], inplace=True)

        cols_peso = ['Prod_Inicial_KG', 'Reposicao_KG', 'Sobra_Buffet_KG', 'Descarte_KG']
        
        for c in cols_peso:
            if c in df_exibicao.columns:
                df_exibicao[c] = converter_para_numero(df_exibicao[c]).apply(lambda x: f"{x:.3f} kg")

        st.dataframe(df_exibicao.tail(10).iloc[::-1], use_container_width=True, hide_index=True)

    else:
        st.info("Nenhum registro encontrado na planilha ainda.")