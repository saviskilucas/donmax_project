import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from zoneinfo import ZoneInfo
import io
import numpy as np

from auth import tem_permissao

@st.cache_resource
def conectar_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(credentials).open("Planilha Don Max")

# CACHE DE ALTA VELOCIDADE PARA TROCA INSTANTÂNEA DE TELAS
@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados_painel():
    try:
        doc = conectar_gsheets()
        sheet = doc.worksheet("Lancamentos_Diarios")
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
# MONTADOR DA MATRIZ DE DESEMPENHO NATIVA DO PDF (SEMS ERROS)
# =========================================================
def montar_tabela_heatmap_pdf(df_matriz):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    if df_matriz is None or df_matriz.empty:
        return None

    try:
        # Separa os pratos e ordena em Ordem Alfabética (A-Z)
        df_pratos = df_matriz[df_matriz['ID_Prato'] != 'TOTAL GERAL'].copy()
        df_pratos = df_pratos.sort_values(by='ID_Prato', ascending=True)

        df_total = df_matriz[df_matriz['ID_Prato'] == 'TOTAL GERAL'].copy()

        df_exibicao = pd.concat([df_pratos, df_total], ignore_index=True)

        colunas_hdr = ['Prato / Item', 'Prod. Ini.', 'Reposição', 'Sobra Buf.', 'Descarte Total', '% Perda']
        table_data = [colunas_hdr]

        raw_matrix = []
        for _, row in df_exibicao.iterrows():
            p_ini = float(row.get('Prod_Ini_Calc', 0.0))
            repo = float(row.get('Reposicao_Calc', 0.0))
            s_buf = float(row.get('Sobra_Buffet_Calc', 0.0))
            desc = float(row.get('Descarte_Calc', 0.0))
            pct = float(row.get('Perda_%', 0.0))
            
            raw_matrix.append([p_ini, repo, s_buf, desc, pct])

            prato_nome = str(row.get('ID_Prato', ''))[:24]
            linha_txt = [
                prato_nome,
                f"{p_ini:.2f} kg",
                f"{repo:.2f} kg",
                f"{s_buf:.2f} kg",
                f"{desc:.2f} kg",
                f"{pct:.1f}%"
            ]
            table_data.append(linha_txt)

        raw_arr = np.array(raw_matrix, dtype=float)
        n_pratos = len(df_pratos)
        num_cols = 5

        # Estilo base da tabela
        t_style = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#B71C1C')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D6D6D6')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]

        # Aplicação dinâmica das cores de Heatmap célula a célula
        for j in range(num_cols):
            if n_pratos > 0:
                col_vals = raw_arr[:n_pratos, j]
                c_min = col_vals.min()
                c_max = col_vals.max()

                for i in range(n_pratos):
                    v = raw_arr[i, j]
                    col_idx = j + 1
                    row_idx = i + 1

                    if v == 0:
                        t_style.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.white))
                        t_style.append(('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#888888')))
                    else:
                        ratio = (v - c_min) / (c_max - c_min) if c_max > c_min else 0.5
                        if ratio < 0.30:
                            bg = colors.HexColor('#FFF9C4')  # Amarelo
                            txt = colors.HexColor('#111111')
                        elif ratio < 0.70:
                            bg = colors.HexColor('#FFE0B2')  # Laranja
                            txt = colors.HexColor('#111111')
                        else:
                            bg = colors.HexColor('#EF5350')  # Vermelho
                            txt = colors.white

                        t_style.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), bg))
                        t_style.append(('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), txt))
                        t_style.append(('FONTNAME', (col_idx, row_idx), (col_idx, row_idx), 'Helvetica-Bold'))

        # Estilo exclusivo para a linha TOTAL GERAL
        if len(df_total) > 0:
            last_row = len(table_data) - 1
            t_style.append(('BACKGROUND', (0, last_row), (-1, last_row), colors.HexColor('#262626')))
            t_style.append(('TEXTCOLOR', (0, last_row), (-1, last_row), colors.white))
            t_style.append(('FONTNAME', (0, last_row), (-1, last_row), 'Helvetica-Bold'))

        t_heatmap = Table(table_data, colWidths=[150, 70, 70, 70, 70, 70])
        t_heatmap.setStyle(TableStyle(t_style))
        return t_heatmap
    except Exception as e:
        return None

def gerar_img_balanco(prod_ini, reposicao, tot_sobra, tot_descarte):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    try:
        fig, ax = plt.subplots(figsize=(3.2, 2.2), facecolor='#FFFFFF')
        ax.set_facecolor('#FFFFFF')
        
        categorias = ['Prod.', 'Repo.', 'Sobra', 'Desc.']
        p_val = float(prod_ini.sum()) if hasattr(prod_ini, 'sum') else float(prod_ini)
        r_val = float(reposicao.sum()) if hasattr(reposicao, 'sum') else float(reposicao)
        s_val = float(tot_sobra)
        d_val = float(tot_descarte)
        
        valores = [p_val, r_val, s_val, d_val]
        cores = ['#1565C0', '#00838F', '#EF6C00', '#C62828']
        
        bars = ax.bar(categorias, valores, color=cores, width=0.55)
        
        max_v = max(valores) if max(valores) > 0 else 1.0
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2.0, yval + (max_v * 0.02), 
                    f'{yval:.2f}', ha='center', va='bottom', color='#111111', fontsize=7, fontweight='bold')
            
        ax.tick_params(colors='#333333', labelsize=7.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')
        ax.grid(axis='y', color='#E0E0E0', linestyle='--', alpha=0.7)
        
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=220, facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception as e:
        return None

def gerar_img_rosca(tot_descarte, tot_sobra):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    try:
        fig, ax = plt.subplots(figsize=(3.2, 2.2), facecolor='#FFFFFF')
        ax.set_facecolor('#FFFFFF')
        
        labels = ['Descarte', 'Sobra']
        valores = [float(tot_descarte), float(tot_sobra)]
        cores = ['#C62828', '#EF6C00']
        
        tot = sum(valores)
        if tot > 0:
            def make_fmt(vals):
                def my_fmt(pct):
                    val = (pct / 100.0) * tot
                    return f'{val:.1f}kg\n({pct:.1f}%)'
                return my_fmt

            # Aumentada a fonte do gráfico de rosca no PDF para 8.5pt em negrito
            wedges, texts, autotexts = ax.pie(
                valores, labels=labels, colors=cores, autopct=make_fmt(valores),
                startangle=90, pctdistance=0.62,
                textprops=dict(color="#222222", fontsize=8.5, weight="bold")
            )
            for autotext in autotexts:
                autotext.set_color('#FFFFFF')
                autotext.set_fontsize(8.5)
                autotext.set_weight('bold')
            centre_circle = plt.Circle((0,0), 0.40, fc='#FFFFFF')
            fig.gca().add_artist(centre_circle)
        else:
            ax.text(0, 0, 'Sem dados', color='#888888', ha='center', va='center')
            
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=220, facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception as e:
        return None


def gerar_img_linha(df_data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    if df_data is None or df_data.empty:
        return None

    try:
        fig, ax = plt.subplots(figsize=(6.5, 2.2), facecolor='#FFFFFF')
        ax.set_facecolor('#FFFFFF')
        
        # Descarte: Rótulo sempre acima da bolinha
        if 'Descarte' in df_data.columns:
            ax.plot(df_data['Data'], df_data['Descarte'], color='#C62828', marker='o', linewidth=2, markersize=4, label='Descarte')
            for x, y in zip(df_data['Data'], df_data['Descarte']):
                if y > 0:
                    ax.annotate(f'{y:.1f}kg', (x, y), textcoords="offset points", xytext=(0, 6), 
                                ha='center', fontsize=7, fontweight='bold', color='#C62828')

        # Sobra Buffet: Rótulo sempre acima da bolinha
        if 'Sobra Buffet' in df_data.columns:
            ax.plot(df_data['Data'], df_data['Sobra Buffet'], color='#EF6C00', marker='o', linewidth=2, markersize=4, label='Sobra Buffet')
            for x, y in zip(df_data['Data'], df_data['Sobra Buffet']):
                if y > 0:
                    ax.annotate(f'{y:.1f}kg', (x, y), textcoords="offset points", xytext=(0, 6), 
                                ha='center', fontsize=7, fontweight='bold', color='#EF6C00')
        
        ax.legend(fontsize=7, loc='upper right', frameon=False)
        ax.tick_params(colors='#333333', labelsize=7.5)
        plt.xticks(rotation=30)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')
        ax.grid(axis='y', color='#E0E0E0', linestyle='--', alpha=0.7)
        
        # Dá folga no eixo Y para que o rótulo do maior valor não fique cortado
        max_val = max(df_data[['Descarte', 'Sobra Buffet']].max()) if not df_data.empty else 10
        max_y = max_val * 1.25 if max_val > 0 else 10
        ax.set_ylim(0, max_y)

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=220, facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception as e:
        return None

def criar_banner_titulo(texto):
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle

    style_title_banner = ParagraphStyle(
        'TitleBanner',
        fontName='Helvetica-Bold',
        fontSize=10.5,
        textColor=colors.HexColor('#B71C1C'),
        alignment=0
    )
    
    t_banner = Table([[Paragraph(f"<b>{texto.upper()}</b>", style_title_banner)]], colWidths=[540])
    t_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFEBEE')),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#FFCDD2')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    return t_banner

# =========================================================
# GERADOR DE PDF EXECUTIVO (REPORTLAB) - 100% ESTÁVEL
# =========================================================
def gerar_pdf_relatorio(df, tot_prod, tot_descarte, tot_sobra, tot_clientes, dt_inicio, dt_fim, prod_ini, reposicao, df_data, df_matriz):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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

    style_header_app = ParagraphStyle('HeaderAppTitle', fontName='Helvetica-Bold', fontSize=14, textColor=colors.white, alignment=0)
    style_sub = ParagraphStyle('DocSub', fontName='Helvetica', fontSize=8.5, textColor=colors.HexColor('#555555'), spaceAfter=8, spaceBefore=6)
    style_note = ParagraphStyle('DocNote', fontName='Helvetica-Oblique', fontSize=7.5, textColor=colors.HexColor('#666666'), spaceBefore=3, spaceAfter=8)
    
    style_card_title = ParagraphStyle('CardTitle', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#B71C1C'), alignment=1)
    style_card_val = ParagraphStyle('CardVal', fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#111111'), alignment=1)

    agora_brasilia = datetime.now(ZoneInfo("America/Sao_Paulo"))
    dt_emissao_str = agora_brasilia.strftime('%d/%m/%Y às %H:%M:%S')

    LARGURA_MAXIMA = 500

    # 1. CABEÇALHO DO RELATÓRIO
    header_table_data = [[
        Paragraph("<b>DON MAX BUFFET</b>", style_header_app),
        Paragraph("<font color='#FFFFFF'><b>RELATÓRIO EXECUTIVO</b></font>", ParagraphStyle('HRight', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white, alignment=2))
    ]]
    
    t_header = Table(header_table_data, colWidths=[250, 250])
    t_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#B71C1C')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    elements.append(t_header)

    dt_str = f"Período Analisado: <b>{dt_inicio.strftime('%d/%m/%Y')}</b> até <b>{dt_fim.strftime('%d/%m/%Y')}</b> &nbsp;|&nbsp; Emitido em: {dt_emissao_str}"
    elements.append(Paragraph(dt_str, style_sub))

    # 2. CARDS RESUMO
    elements.append(criar_banner_titulo("INDICADORES CHAVE DO PERÍODO"))
    elements.append(Spacer(1, 6))

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

    t_cards = Table(cards_data, colWidths=[125, 125, 125, 125])
    t_cards.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFF5F5')),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#FFCDD2')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))
    elements.append(t_cards)
    elements.append(Spacer(1, 10))

    # 3. BALANÇO E SOBRA VS DESCARTE
    img_b = gerar_img_balanco(prod_ini, reposicao, tot_sobra, tot_descarte)
    img_r = gerar_img_rosca(tot_descarte, tot_sobra)
    
    if img_b is not None and img_r is not None:
        elements.append(criar_banner_titulo("Análise Comparativa de Produção"))
        elements.append(Spacer(1, 6))
        quadros_table_data = [
            [
                Paragraph("<b>Balanço da Cozinha</b>", ParagraphStyle('SubB', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor('#333333'), alignment=1)),
                Paragraph("<b>Sobra vs Descarte</b>", ParagraphStyle('SubR', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor('#333333'), alignment=1))
            ],
            [
                Image(img_b, width=245, height=135),
                Image(img_r, width=245, height=135)
            ]
        ]
        
        t_quadros = Table(quadros_table_data, colWidths=[250, 250])
        t_quadros.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        elements.append(t_quadros)
        elements.append(Spacer(1, 8))

    # 4. LINHA DO TEMPO
    if df_data is not None and not df_data.empty:
        img_l = gerar_img_linha(df_data)
        if img_l is not None:
            elements.append(criar_banner_titulo("Linha do Tempo de Descarte e Sobra"))
            elements.append(Spacer(1, 6))
            elements.append(Image(img_l, width=LARGURA_MAXIMA, height=135))
            elements.append(Spacer(1, 8))

    # 5. MATRIZ DE DESEMPENHO (TABELA NATIVA QUE QUEBRA PÁGINA AUTOMATICAMENTE)
    if df_matriz is not None and not df_matriz.empty:
        elements.append(PageBreak())
        elements.append(criar_banner_titulo("Matriz de Desempenho por Produto"))
        elements.append(Spacer(1, 6))
        
        tabela_heatmap = montar_tabela_heatmap_pdf(df_matriz)
        if tabela_heatmap is not None:
            elements.append(tabela_heatmap)
            elements.append(Paragraph("* A linha TOTAL GERAL indica o Descarte Médio Ponderado Global (Descarte Total / Produção Total).", style_note))

    # 6. DETALHAMENTO DOS LANÇAMENTOS
    elements.append(Spacer(1, 10))
    elements.append(criar_banner_titulo("Detalhamento de Lançamentos"))
    elements.append(Spacer(1, 6))

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

    t_table = Table(table_data, colWidths=[60, 160, 70, 70, 70, 70])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#B71C1C')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('TOPPADDING', (0,0), (-1,0), 5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'LEFT'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0E0E0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9FA')]),
        ('TOPPADDING', (0,1), (-1,-1), 4),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
    ]))

    elements.append(t_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def render():
    if not tem_permissao("dashboard:visualizar"):
        st.error("⛔ Você não tem permissão para visualizar o Dashboard.")
        return

    st.markdown("""
        <style>
        div[data-baseweb="input"] input {
            caret-color: transparent !important;
            cursor: pointer !important;
        }

        div[data-baseweb="input"] {
            cursor: pointer !important;
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
            background-color: #1E1E1E !important;
            border: 1px solid #2D2D2D !important;
            border-left: 4px solid #B71C1C !important;
            border-radius: 12px !important;
            padding: 10px 6px !important;
            text-align: center !important;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.4) !important;
            margin-bottom: 8px !important;
            width: 100% !important;
            box-sizing: border-box !important;
            display: block !important;
        }
        .metric-card-title {
            font-size: 0.70rem !important;
            font-weight: 700 !important;
            color: #A0A0A0 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.3px !important;
            margin-bottom: 3px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .metric-card-value {
            font-size: 1.10rem !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            line-height: 1.1 !important;
        }
        </style>

        <script>
        (function fecharTecladoImediato() {
            const doc = window.parent.document;

            const aplicarDesfoqueRigido = () => {
                const inputs = doc.querySelectorAll('div[data-baseweb="input"] input');
                
                inputs.forEach(input => {
                    if (!input.dataset.blurHardAtivo) {
                        input.dataset.blurHardAtivo = "true";
                        
                        // Captura o toque no exato milissegundo em que o dedo encosta no campo
                        const tirarFoco = () => {
                            requestAnimationFrame(() => {
                                input.blur();
                                if (doc.activeElement) {
                                    doc.activeElement.blur();
                                }
                            });
                        };

                        input.addEventListener('touchstart', tirarFoco, { passive: true });
                        input.addEventListener('pointerdown', tirarFoco, { passive: true });
                        input.addEventListener('focus', tirarFoco, { passive: true });
                    }
                });
            };

            aplicarDesfoqueRigido();
            
            const observer = new MutationObserver(aplicarDesfoqueRigido);
            observer.observe(doc.body, { childList: true, subtree: true });
        })();
        </script>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>DASHBOARD</div>", unsafe_allow_html=True)

    dados = carregar_dados_painel()
    
    if dados:
        df = pd.DataFrame(dados)

        cols_texto = ['ID_Prato', 'Responsavel', 'Data', 'Observacoes']
        for col_t in cols_texto:
            if col_t in df.columns:
                df[col_t] = df[col_t].astype(str).fillna('-')

        df['ID'] = range(1, len(df) + 1)

        if 'Data' in df.columns:
            s_datas = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce').dt.date
            df['Data_DT'] = s_datas
        else:
            df['Data_DT'] = date.today()

        datas_validas = df['Data_DT'].dropna()
        if not datas_validas.empty:
            data_min = min(datas_validas)
            data_max = max(datas_validas)
        else:
            data_min = data_max = date.today()

        st.markdown("##### Filtrar por Período")
        
        if tem_permissao("dashboard:filtrar"):
            filtro_datas = st.date_input(
                "Selecione o intervalo no calendário:",
                value=(data_min, data_max),
                min_value=data_min,
                max_value=data_max,
                format="DD/MM/YYYY"
            )
        else:
            filtro_datas = (data_min, data_max)

        if isinstance(filtro_datas, (list, tuple)):
            if len(filtro_datas) == 2:
                dt_inicio, dt_fim = filtro_datas
            elif len(filtro_datas) == 1:
                dt_inicio = dt_fim = filtro_datas[0]
            else:
                dt_inicio = dt_fim = data_min
        else:
            dt_inicio = dt_fim = filtro_datas

        df = df[(df['Data_DT'] >= dt_inicio) & (df['Data_DT'] <= dt_fim)]

        if df.empty:
            st.warning("⚠️ Nenhum registro encontrado para o período selecionado.")
            return

        prod_ini = converter_para_numero(df['Prod_Inicial_KG']) if 'Prod_Inicial_KG' in df.columns else pd.Series([0]*len(df))
        reposicao = converter_para_numero(df['Reposicao_KG']) if 'Reposicao_KG' in df.columns else pd.Series([0]*len(df))
        sobra_buffet = converter_para_numero(df['Sobra_Buffet_KG']) if 'Sobra_Buffet_KG' in df.columns else pd.Series([0]*len(df))
        descarte = converter_para_numero(df['Descarte_KG']) if 'Descarte_KG' in df.columns else pd.Series([0]*len(df))
        clientes = converter_para_numero(df['Clientes_Atendidos']) if 'Clientes_Atendidos' in df.columns else pd.Series([0]*len(df))

        df['Prod_Ini_Calc'] = prod_ini
        df['Reposicao_Calc'] = reposicao
        df['Prod_Total_Calc'] = prod_ini + reposicao
        df['Descarte_Calc'] = descarte
        df['Sobra_Buffet_Calc'] = sobra_buffet

        tot_prod_ini = float(prod_ini.sum())
        tot_reposicao = float(reposicao.sum())
        tot_prod = float(df['Prod_Total_Calc'].sum())
        tot_descarte = float(descarte.sum())
        tot_sobra_buffet = float(sobra_buffet.sum())
        tot_clientes = float(clientes.sum())

        df_data = pd.DataFrame()
        if 'Data' in df.columns:
            df_temp_data = pd.DataFrame({
                'Data': df['Data'], 
                'Descarte': descarte,
                'Sobra Buffet': sobra_buffet
            })
            df_temp_data['Data_DT'] = pd.to_datetime(df_temp_data['Data'], format='%d/%m/%Y', errors='coerce')
            df_data = df_temp_data.groupby(['Data_DT', 'Data'])[['Descarte', 'Sobra Buffet']].sum().reset_index()
            df_data = df_data.sort_values('Data_DT', ascending=True)

        df_matriz = pd.DataFrame()
        if 'ID_Prato' in df.columns:
            df_matriz = df.groupby('ID_Prato').agg({
                'Prod_Ini_Calc': 'sum',
                'Reposicao_Calc': 'sum',
                'Sobra_Buffet_Calc': 'sum',
                'Descarte_Calc': 'sum'
            }).reset_index()
            df_matriz['Perda_%'] = (df_matriz['Descarte_Calc'] / (df_matriz['Prod_Ini_Calc'] + df_matriz['Reposicao_Calc']) * 100).fillna(0)
            
            df_matriz = df_matriz.sort_values(by='Descarte_Calc', ascending=False)

            pct_total_geral = (tot_descarte / tot_prod * 100) if tot_prod > 0 else 0.0
            linha_total = pd.DataFrame([{
                'ID_Prato': 'TOTAL GERAL',
                'Prod_Ini_Calc': tot_prod_ini,
                'Reposicao_Calc': tot_reposicao,
                'Sobra_Buffet_Calc': tot_sobra_buffet,
                'Descarte_Calc': tot_descarte,
                'Perda_%': pct_total_geral
            }])
            
            df_matriz = pd.concat([df_matriz, linha_total], ignore_index=True)

        config_plotly_mobile = {
            'staticPlot': True,
            'displayModeBar': False
        }

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
                <div class="metric-card" style="border-left-color: #FF5252 !important;">
                    <div class="metric-card-title">Descarte Total</div>
                    <div class="metric-card-value" style="color:#FF5252">{tot_descarte:.3f} <span style="font-size:0.75rem">kg</span></div>
                </div>
            """, unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #FFB74D !important;">
                    <div class="metric-card-title">Sobra Buffet</div>
                    <div class="metric-card-value" style="color:#FFB74D">{tot_sobra_buffet:.3f} <span style="font-size:0.75rem">kg</span></div>
                </div>
            """, unsafe_allow_html=True)
            
        with c4:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #AB47BC !important;">
                    <div class="metric-card-title">Atendimento</div>
                    <div class="metric-card-value" style="color:#E1BEE7">{int(tot_clientes)} <span style="font-size:0.75rem">clientes</span></div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # =========================================================
        # 1. BALANÇO DA COZINHA
        # =========================================================
        st.markdown("##### Balanço da Cozinha (Kg)")
        
        df_balanco = pd.DataFrame({
            'Categoria': ['Prod. Inicial', 'Reposição', 'Sobra Buffet', 'Descarte'],
            'Peso (kg)': [
                round(tot_prod_ini, 3), 
                round(tot_reposicao, 3), 
                round(tot_sobra_buffet, 3), 
                round(tot_descarte, 3)
            ]
        })

        fig_balanco = px.bar(
            df_balanco,
            x='Peso (kg)',
            y='Categoria',
            orientation='h',
            text_auto='.1f',
            color='Categoria',
            color_discrete_map={
                'Prod. Inicial': '#1E88E5',
                'Reposição': '#00ACC1',
                'Sobra Buffet': '#FB8C00',
                'Descarte': '#E53935'
            }
        )

        fig_balanco.update_layout(
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#E0E0E0"),
            height=220,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(showgrid=True, gridcolor='#2D2D2D', fixedrange=True, tickformat='.1f'),
            yaxis=dict(showgrid=False, fixedrange=True, title="", categoryorder='total ascending')
        )

        st.plotly_chart(fig_balanco, width="stretch", config=config_plotly_mobile)

        # =========================================================
        # CONSTRUÇÃO DA MATRIZ (SOMENTE PRATOS COM MOVIMENTAÇÃO)
        # =========================================================
        df_matriz = pd.DataFrame()
        if 'ID_Prato' in df.columns:
            # Agrupa os lançamentos do período
            df_matriz = df.groupby('ID_Prato').agg({
                'Prod_Ini_Calc': 'sum',
                'Reposicao_Calc': 'sum',
                'Sobra_Buffet_Calc': 'sum',
                'Descarte_Calc': 'sum'
            }).reset_index()

            # Filtra pratos inválidos
            df_matriz = df_matriz[df_matriz['ID_Prato'] != '-']

            # FILTRO RÍGIDO: Remove pratos onde TODAS as colunas principais são zeradas
            df_matriz = df_matriz[
                (df_matriz['Prod_Ini_Calc'] > 0) | 
                (df_matriz['Reposicao_Calc'] > 0) | 
                (df_matriz['Sobra_Buffet_Calc'] > 0) | 
                (df_matriz['Descarte_Calc'] > 0)
            ]

            # Calcula a % de perda por prato
            df_matriz['Perda_%'] = (df_matriz['Descarte_Calc'] / (df_matriz['Prod_Ini_Calc'] + df_matriz['Reposicao_Calc']) * 100).fillna(0)
            
            # ORDENAÇÃO ALFABÉTICA ESTÁVEL (A-Z)
            df_matriz = df_matriz.sort_values(by='ID_Prato', ascending=True)

            # Adiciona a linha TOTAL GERAL ao final
            pct_total_geral = (tot_descarte / tot_prod * 100) if tot_prod > 0 else 0.0
            linha_total = pd.DataFrame([{
                'ID_Prato': 'TOTAL GERAL',
                'Prod_Ini_Calc': tot_prod_ini,
                'Reposicao_Calc': tot_reposicao,
                'Sobra_Buffet_Calc': tot_sobra_buffet,
                'Descarte_Calc': tot_descarte,
                'Perda_%': pct_total_geral
            }])
            
            df_matriz = pd.concat([df_matriz, linha_total], ignore_index=True)

        # =========================================================
        # 2. HEATMAP (DASHBOARD)
        # =========================================================
        if tem_permissao("dashboard:matriz") and not df_matriz.empty and len(df_matriz) > 1:
            st.markdown("##### Matriz de Desempenho por Produto")

            # Pratos em ordem alfabética invertida para exibição de A (topo) a Z
            df_pratos = df_matriz[df_matriz['ID_Prato'] != 'TOTAL GERAL'].iloc[::-1].copy()
            df_total = df_matriz[df_matriz['ID_Prato'] == 'TOTAL GERAL'].copy()

            # Index 0 = TOTAL GERAL / Index 1..N = Pratos
            df_matriz_plot = pd.concat([df_total, df_pratos], ignore_index=True)

            pratos = df_matriz_plot['ID_Prato'].tolist()
            colunas_heatmap = ['Prod. Inicial', 'Reposição', 'Sobra Buffet', 'Descarte Total', '% Perda']

            raw_vals = []
            text_vals = []

            for _, row in df_matriz_plot.iterrows():
                p_ini = float(row.get('Prod_Ini_Calc', 0.0))
                repo = float(row.get('Reposicao_Calc', 0.0))
                s_buf = float(row.get('Sobra_Buffet_Calc', 0.0))
                desc = float(row.get('Descarte_Calc', 0.0))
                pct = float(row.get('Perda_%', 0.0))

                raw_vals.append([p_ini, repo, s_buf, desc, pct])
                text_vals.append([
                    f"{p_ini:.2f} kg",
                    f"{repo:.2f} kg",
                    f"{s_buf:.2f} kg",
                    f"{desc:.2f} kg",
                    f"{pct:.1f}%"
                ])

            raw_arr = np.array(raw_vals, dtype=float)
            num_rows = len(pratos)
            num_cols = len(colunas_heatmap)

            z_colors = np.zeros_like(raw_arr)
            n_pratos = len(df_pratos)

            # Linha 0 (TOTAL GERAL) é mantida sem cor (0.0)
            z_colors[0, :] = 0.08

            # Normalização das cores estritamente para as linhas dos pratos (linhas 1 até N)
            for j in range(num_cols):
                if n_pratos > 0:
                    col_data = raw_arr[1:, j]
                    c_min = col_data.min()
                    c_max = col_data.max()
                    for i in range(1, num_rows):
                        v = raw_arr[i, j]
                        if v == 0:
                            z_colors[i, j] = 0.0
                        else:
                            if c_max > c_min:
                                z_colors[i, j] = 0.15 + 0.85 * ((v - c_min) / (c_max - c_min))
                            else:
                                z_colors[i, j] = 0.5

            colorscale_dark = [
                [0.0, '#1e1e1e'],   # Fundo neutro para Células Zeradas
                [0.08, '#661010'],  # Cor de Fundo Destacada do TOTAL GERAL
                [0.15, '#3b3620'],  # 
                [0.4, '#968430'],   # 
                [0.7, '#EF6C00'],   # Laranja Alerta
                [1.0, '#C62828']    # Vermelho Crítico
            ]

            fig_heatmap = go.Figure(data=go.Heatmap(
                z=z_colors,
                x=colunas_heatmap,
                y=pratos,
                text=text_vals,
                texttemplate="%{text}",
                textfont={"size": 10, "color": "#FFFFFF"},
                colorscale=colorscale_dark,
                showscale=False,
                zmin=0,
                zmax=1
            ))

            altura_matriz = max(280, num_rows * 42)

            fig_heatmap.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#E0E0E0"),
                margin=dict(l=10, r=10, t=20, b=20),
                height=altura_matriz,
                xaxis=dict(fixedrange=True, side='top'),
                yaxis=dict(fixedrange=True)
            )

            st.plotly_chart(fig_heatmap, width="stretch", config=config_plotly_mobile)

        # =========================================================
        # 3. SOBRA VS DESCARTE (FONTE MAIOR E NEGRITO)
        # =========================================================
        st.markdown("##### Sobra vs Descarte")
        df_rosca = pd.DataFrame({
            'Tipo': ['Descarte Total', 'Sobra Buffet'],
            'Peso': [tot_descarte, tot_sobra_buffet]
        })
        if df_rosca['Peso'].sum() > 0:
            fig_pie = px.pie(
                df_rosca, names='Tipo', values='Peso', hole=0.5,
                color_discrete_sequence=['#E53935', '#FB8C00']
            )
            # Fonte aumentada para 14px em negrito
            fig_pie.update_traces(
                textinfo='value+percent',
                texttemplate='<b>%{value:.2f} kg</b><br><b>(%{percent})</b>',
                textposition='inside',
                insidetextfont=dict(color='#FFFFFF', size=14, family='Arial Black')
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#E0E0E0"),
                margin=dict(l=5, r=5, t=10, b=5),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, width="stretch", config=config_plotly_mobile)
        else:
            st.info("Sem registros de sobras ou descarte no período selecionado.")

        # =========================================================
        # LINHA DO TEMPO (RÓTULOS SEMPRE ACIMA DA BOLINHA)
        # =========================================================
        if not df_data.empty:
            st.markdown("##### Linha do Tempo de Descarte e Sobra")
            
            fig_line = go.Figure()

            # Descarte: Rótulo posicionado SEMPRE no topo
            if 'Descarte' in df_data.columns:
                fig_line.add_trace(go.Scatter(
                    x=df_data['Data'],
                    y=df_data['Descarte'],
                    name='Descarte',
                    mode='lines+markers+text',
                    text=[f"<b>{v:.1f} kg</b>" if v > 0 else "" for v in df_data['Descarte']],
                    textposition='top center',
                    textfont=dict(color='#FF5252', size=12, family="Arial Black"),
                    line=dict(color='#FF5252', width=3),
                    marker=dict(size=8, color='#FF5252')
                ))

            # Sobra Buffet: Rótulo posicionado SEMPRE no topo
            if 'Sobra Buffet' in df_data.columns:
                fig_line.add_trace(go.Scatter(
                    x=df_data['Data'],
                    y=df_data['Sobra Buffet'],
                    name='Sobra Buffet',
                    mode='lines+markers+text',
                    text=[f"<b>{v:.1f} kg</b>" if v > 0 else "" for v in df_data['Sobra Buffet']],
                    textposition='top center',
                    textfont=dict(color='#FB8C00', size=12, family="Arial Black"),
                    line=dict(color='#FB8C00', width=3),
                    marker=dict(size=8, color='#FB8C00')
                ))

            # Ajusta o topo do gráfico para 130% do valor máximo para o texto do topo não cortar
            max_val = max(df_data[['Descarte', 'Sobra Buffet']].max()) if not df_data.empty else 10
            max_y = max_val * 1.30 if max_val > 0 else 10

            fig_line.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#E0E0E0"),
                margin=dict(l=5, r=5, t=30, b=5),
                xaxis=dict(showgrid=False, fixedrange=True, type='category'),
                yaxis=dict(showgrid=True, gridcolor='#2D2D2D', fixedrange=True, title="", range=[0, max_y]),
                legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_line, width="stretch", config=config_plotly_mobile)

        col_hdr_left, col_hdr_right = st.columns([0.5, 0.5])
        with col_hdr_left:
            if st.button("🔄 Atualizar", width="stretch"):
                st.cache_data.clear()
                st.rerun()

        with col_hdr_right:
            if tem_permissao("relatorios:exportar_pdf"):
                try:
                    pdf_bytes = gerar_pdf_relatorio(
                        df, tot_prod, tot_descarte, tot_sobra_buffet, tot_clientes,
                        dt_inicio, dt_fim,
                        prod_ini, reposicao, df_data, df_matriz
                    )
                    import base64
                    pdf_b64 = base64.b64encode(pdf_bytes.getvalue()).decode('utf-8')
                    
                    st.markdown(f"""
                        <a href="data:application/pdf;base64,{pdf_b64}" target="_blank" download="Relatorio_DonMax.pdf" style="
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            width: 100%;
                            height: 38px;
                            background-color: #262626;
                            color: #FFFFFF !important;
                            font-weight: 700;
                            font-size: 0.85rem;
                            text-decoration: none;
                            border-radius: 8px;
                            border: 1px solid #333333;
                            transition: all 0.2s ease;
                            box-sizing: border-box;
                        ">
                            📄 Gerar PDF
                        </a>
                    """, unsafe_allow_html=True)
                except Exception as err:
                    st.error(f"Erro ao gerar PDF: {err}")

        st.markdown("---")
        st.markdown("##### Lançamentos Registrados")
        
        # =========================================================
        # TABELA DE LANÇAMENTOS
        # =========================================================
        df_exibicao = df.copy()
        
        cols_remover = ['Data_DT', 'Prod_Ini_Calc', 'Reposicao_Calc', 'Prod_Total_Calc', 'Descarte_Calc', 'Sobra_Buffet_Calc']
        for c in cols_remover:
            if c in df_exibicao.columns:
                df_exibicao.drop(columns=[c], inplace=True)

        cols_peso = ['Prod_Inicial_KG', 'Reposicao_KG', 'Sobra_Buffet_KG', 'Descarte_KG']
        for c in cols_peso:
            if c in df_exibicao.columns:
                df_exibicao[c] = converter_para_numero(df_exibicao[c]).apply(lambda x: f"{x:.3f} kg")

        colunas_ordem = ['ID'] + [c for c in df_exibicao.columns if c != 'ID']
        df_exibicao = df_exibicao[colunas_ordem]

        for col in df_exibicao.columns:
            df_exibicao[col] = df_exibicao[col].astype(str)

        # ---------------------------------------------------------------------------------
        # TRECHO ATUALIZADO:
        # Exibe todos os registros ordenados dos mais recentes para os mais antigos (.iloc[::-1]),
        # mantendo a caixa com altura fixa para permitir a rolagem vertical.
        # ---------------------------------------------------------------------------------
        st.dataframe(
            df_exibicao.iloc[::-1], 
            use_container_width=True, 
            hide_index=True,
            height=380
        )

        # =========================================================
        # EDIÇÃO / EXCLUSÃO DE LANÇAMENTOS (ADMIN E MASTER)
        # =========================================================
        perfil_atual = st.session_state.get("perfil_logado", "").lower()
        pode_editar_lancamento = perfil_atual in ["master", "admin"] or tem_permissao("lancamentos:editar")

        if pode_editar_lancamento:
            with st.expander("🛠️ **Gerenciar Lançamentos (Editar / Excluir)**"):
                st.caption("Selecione abaixo o **ID** do lançamento que você deseja alterar ou remover:")
                
                mapa_ids = {}
                for idx, r in df.iterrows():
                    id_visivel = int(r['ID'])
                    linha_planilha = id_visivel + 1
                    mapa_ids[id_visivel] = (linha_planilha, r)

                ids_disponiveis = sorted(list(mapa_ids.keys()), reverse=True)

                if ids_disponiveis:
                    id_selecionado = st.selectbox("Selecione o ID do Lançamento:", options=ids_disponiveis, format_func=lambda x: f"ID #{x}")
                    linha_sel, reg_sel = mapa_ids[id_selecionado]

                    # 1. Leitura e Formatação Rígida de Data e Hora
                    dt_lan_str = str(reg_sel.get('Data', ''))
                    try:
                        dt_lan_obj = datetime.strptime(dt_lan_str, '%d/%m/%Y').date()
                    except Exception:
                        dt_lan_obj = date.today()

                    hora_raw = str(reg_sel.get('Hora', '')).replace("'", "").strip()
                    hora_lan = "00:00"
                    if hora_raw:
                        for fmt in ('%H:%M', '%H:%M:%S', '%I:%M:%S %p', '%I:%M %p'):
                            try:
                                hora_lan = datetime.strptime(hora_raw, fmt).strftime('%H:%M')
                                break
                            except ValueError:
                                pass
                        if hora_lan == "00:00" and ":" in hora_raw:
                            partes_h = hora_raw.split(":")
                            hora_lan = f"{partes_h[0].zfill(2)}:{partes_h[1].zfill(2)[:2]}"

                    prato_lan = str(reg_sel.get('ID_Prato', '-')).strip()
                    resp_lan = str(reg_sel.get('Responsavel', ''))
                    p_ini_num = float(converter_para_numero(pd.Series([reg_sel.get('Prod_Inicial_KG', 0)]))[0])
                    repo_num = float(converter_para_numero(pd.Series([reg_sel.get('Reposicao_KG', 0)]))[0])
                    sobra_num = float(converter_para_numero(pd.Series([reg_sel.get('Sobra_Buffet_KG', 0)]))[0])
                    desc_num = float(converter_para_numero(pd.Series([reg_sel.get('Descarte_KG', 0)]))[0])
                    cli_num = int(converter_para_numero(pd.Series([reg_sel.get('Clientes_Atendidos', 0)]))[0])
                    obs_lan = str(reg_sel.get('Observacoes', ''))

                    # 2. Carrega Todos os Pratos Ativos da Aba Alimentos
                    try:
                        sheet_alimentos = conectar_gsheets().worksheet("Alimentos")
                        registros_alimentos_atuais = sheet_alimentos.get_all_records()
                        lista_pratos_opt = [
                            str(r.get("Prato", r.get("prato", r.get("ID_Prato", "")))).strip()
                            for r in registros_alimentos_atuais
                            if str(r.get("Prato", r.get("prato", r.get("ID_Prato", "")))).strip()
                        ]
                    except Exception:
                        lista_pratos_opt = []

                    if prato_lan and prato_lan not in lista_pratos_opt and prato_lan != '-':
                        lista_pratos_opt.insert(0, prato_lan)

                    if not lista_pratos_opt:
                        lista_pratos_opt = [prato_lan]

                    idx_prato = lista_pratos_opt.index(prato_lan) if prato_lan in lista_pratos_opt else 0

                    st.info(f"**Lançamento ID #{id_selecionado}:** {dt_lan_str} — {prato_lan} ({resp_lan})")

                    with st.form(key=f"form_editar_id_{id_selecionado}"):
                        c_ed1, c_ed2 = st.columns(2)
                        with c_ed1:
                            e_dt = st.date_input("Data", value=dt_lan_obj, format="DD/MM/YYYY")
                            e_prato = st.selectbox("Prato / Item", options=lista_pratos_opt, index=idx_prato)
                            e_p_ini = st.number_input("Prod. Inicial (kg)", value=p_ini_num, step=0.1, format="%.3f")
                            e_repo = st.number_input("Reposição (kg)", value=repo_num, step=0.1, format="%.3f")
                        
                        with c_ed2:
                            e_sobra = st.number_input("Sobra Buffet (kg)", value=sobra_num, step=0.1, format="%.3f")
                            e_desc = st.number_input("Descarte Total (kg)", value=desc_num, step=0.1, format="%.3f")
                            e_cli = st.number_input("Clientes Atendidos", value=cli_num, step=1)
                            e_obs = st.text_input("Observações", value=obs_lan)

                        b_salvar, b_excluir = st.columns(2)
                        with b_salvar:
                            btn_salvar_l = st.form_submit_button("💾 SALVAR", width="stretch")
                        with b_excluir:
                            btn_excluir_l = st.form_submit_button("🗑️ EXCLUIR", width="stretch")

                        if btn_salvar_l:
                            try:
                                dt_formatada = e_dt.strftime('%d/%m/%Y')
                                sheet_lancamentos = conectar_gsheets().worksheet("Lancamentos_Diarios")

                                # Força formato de texto com apóstrofo para manter ex: '14:52
                                hora_para_planilha = f"'{hora_lan}" if not hora_lan.startswith("'") else hora_lan

                                sheet_lancamentos.update_cell(linha_sel, 1, dt_formatada)          # Data
                                sheet_lancamentos.update_cell(linha_sel, 2, hora_para_planilha)    # Hora ('14:52)
                                sheet_lancamentos.update_cell(linha_sel, 3, resp_lan)              # Responsavel
                                sheet_lancamentos.update_cell(linha_sel, 4, str(e_cli))           # Clientes_Atendidos
                                sheet_lancamentos.update_cell(linha_sel, 5, e_prato.strip())       # ID_Prato
                                sheet_lancamentos.update_cell(linha_sel, 6, str(e_p_ini))         # Prod_Inicial_KG
                                sheet_lancamentos.update_cell(linha_sel, 7, str(e_repo))          # Reposicao_KG
                                sheet_lancamentos.update_cell(linha_sel, 8, str(e_sobra))         # Sobra_Buffet_KG
                                sheet_lancamentos.update_cell(linha_sel, 9, str(e_desc))          # Descarte_KG
                                sheet_lancamentos.update_cell(linha_sel, 10, e_obs.strip())        # Observacoes

                                st.cache_data.clear()
                                st.toast(f"🟢 Lançamento ID #{id_selecionado} atualizado com sucesso!", icon="✅")
                                st.info(f"✅ **LOG:** Lançamento ID #{id_selecionado} alterado com sucesso.")
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar lançamento: {e}")

                        if btn_excluir_l:
                            try:
                                sheet_lancamentos = conectar_gsheets().worksheet("Lancamentos_Diarios")
                                sheet_lancamentos.delete_rows(linha_sel)
                                
                                st.cache_data.clear()
                                st.toast(f"🗑️ Lançamento ID #{id_selecionado} excluído!", icon="🗑️")
                                st.info(f"🗑️ **LOG:** Lançamento ID #{id_selecionado} removido do sistema.")
                            except Exception as e:
                                st.error(f"❌ Erro ao excluir lançamento: {e}")