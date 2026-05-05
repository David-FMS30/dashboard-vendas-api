import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    layout='wide',
    page_title='Dashboard de Vendas',
    page_icon='📊',
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

  .stApp { background-color: #F4F6FB; }

  [data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E8ECF4;
  }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stMultiSelect label,
  [data-testid="stSidebar"] .stCheckbox label,
  [data-testid="stSidebar"] .stSlider label {
    font-weight: 600;
    color: #3D4A6B;
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  [data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #E8ECF4;
    border-radius: 14px;
    padding: 20px 24px !important;
    box-shadow: 0 2px 8px rgba(60,80,140,0.06);
  }
  [data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8A96B0;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1E2D55;
    font-family: 'DM Mono', monospace;
  }

  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #EAEEF7;
    padding: 4px;
    border-radius: 12px;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 9px;
    padding: 8px 24px;
    font-weight: 500;
    font-size: 0.88rem;
    color: #6B7A9F;
    border: none;
    background: transparent;
  }
  .stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #1E2D55 !important;
    box-shadow: 0 2px 8px rgba(60,80,140,0.10);
  }

  [data-testid="stPlotlyChart"] {
    background: #FFFFFF;
    border-radius: 14px;
    border: 1px solid #E8ECF4;
    padding: 8px;
    box-shadow: 0 2px 8px rgba(60,80,140,0.05);
  }

  h1 {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #1E2D55 !important;
    letter-spacing: -0.02em;
  }
</style>
""", unsafe_allow_html=True)

# ── Paleta ────────────────────────────────────────────────────────────────────
PALETTE    = ['#2563EB', '#7C3AED', '#059669', '#D97706', '#DC2626', '#0891B2', '#BE185D', '#065F46']
TEMPLATE   = 'plotly_white'
PRIMARY    = '#2563EB'
PURPLE     = '#7C3AED'
FONT_COLOR = '#1E2D55'
GRID_COLOR = '#E8ECF4'

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_brl(valor):
    """R$ 1.234.567,89"""
    s = f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f'R$ {s}'

def fmt_brl_curto(valor):
    """R$ 2,5 mi  /  R$ 771 mil  /  R$ 999"""
    if valor >= 1_000_000:
        return f'R$ {valor/1_000_000:.1f} mi'
    if valor >= 1_000:
        return f'R$ {valor/1_000:.0f} mil'
    return f'R$ {valor:.0f}'

def estilo_base(fig):
    fig.update_layout(
        template=TEMPLATE,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans, sans-serif', color=FONT_COLOR, size=12),
        title=dict(font=dict(size=14, color=FONT_COLOR), x=0.01, xanchor='left'),
        margin=dict(l=16, r=16, t=48, b=16),
        legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='rgba(0,0,0,0)', font=dict(size=11)),
        xaxis=dict(showgrid=False, linecolor=GRID_COLOR, tickfont=dict(size=11)),
        yaxis=dict(gridcolor=GRID_COLOR, linecolor='rgba(0,0,0,0)', tickfont=dict(size=11)),
    )
    return fig

def estilo_linha(fig):
    fig.update_layout(
        template=TEMPLATE,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans, sans-serif', color=FONT_COLOR, size=12),
        title=dict(font=dict(size=14, color=FONT_COLOR), x=0.01, xanchor='left'),
        margin=dict(l=16, r=16, t=48, b=16),
        legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='rgba(0,0,0,0)', font=dict(size=11)),
        xaxis=dict(showgrid=False, linecolor=GRID_COLOR, tickfont=dict(size=10), tickangle=-30),
        yaxis=dict(gridcolor=GRID_COLOR, linecolor='rgba(0,0,0,0)', tickfont=dict(size=11)),
    )
    return fig

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## Filtros")
st.sidebar.markdown("---")

regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']
regiao = st.sidebar.selectbox('Região', regioes)
if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Todo o período', value=True)
ano = '' if todos_anos else st.sidebar.slider('Ano', 2020, 2023)

# ── Dados ─────────────────────────────────────────────────────────────────────
url = 'https://labdados.com/produtos'
with st.spinner('Carregando dados...'):
    response = requests.get(url, params={'regiao': regiao.lower(), 'ano': ano})
    dados = pd.DataFrame.from_dict(response.json())

dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', sorted(dados['Vendedor'].unique()))
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

st.sidebar.markdown("---")
st.sidebar.caption(f"{len(dados):,} registros carregados")

# ── Tabelas ───────────────────────────────────────────────────────────────────
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = (
    dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']]
    .merge(receita_estados, left_on='Local da compra', right_index=True)
    .sort_values('Preço', ascending=False)
)
receita_estados['Preço_fmt'] = receita_estados['Preço'].apply(fmt_brl_curto)

receita_mensal = (
    dados.set_index('Data da Compra')
    .groupby(pd.Grouper(freq='ME'))['Preço'].sum()
    .reset_index()
)
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()
receita_mensal['Mes_num'] = receita_mensal['Data da Compra'].dt.month
receita_mensal = receita_mensal.sort_values(['Ano', 'Mes_num'])

receita_categorias = (
    dados.groupby('Categoria do Produto')[['Preço']].sum()
    .sort_values('Preço', ascending=False)
    .reset_index()
)
receita_categorias['Preço_fmt'] = receita_categorias['Preço'].apply(fmt_brl_curto)

vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = (
    dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']]
    .merge(vendas_estados, left_on='Local da compra', right_index=True)
    .sort_values('Preço', ascending=False)
)

vendas_mensal = (
    dados.set_index('Data da Compra')
    .groupby(pd.Grouper(freq='ME'))['Preço'].count()
    .reset_index()
)
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()
vendas_mensal['Mes_num'] = vendas_mensal['Data da Compra'].dt.month
vendas_mensal = vendas_mensal.sort_values(['Ano', 'Mes_num'])

vendas_categorias = (
    dados.groupby('Categoria do Produto')['Preço'].count()
    .sort_values(ascending=False)
    .reset_index()
)
vendas_categorias.columns = ['Categoria do Produto', 'Qtd']

vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))
vendedores.columns = ['Receita Total', 'Qtd Vendas']
vendedores['Ticket Médio'] = vendedores['Receita Total'] / vendedores['Qtd Vendas']

# ── KPIs ──────────────────────────────────────────────────────────────────────
receita_total        = dados['Preço'].sum()
qtd_vendas           = dados.shape[0]
ticket_medio         = receita_total / qtd_vendas if qtd_vendas else 0
qtd_vendedores_total = dados['Vendedor'].nunique()

# ── Header ────────────────────────────────────────────────────────────────────
st.title('Dashboard de Vendas')
st.caption('Análise interativa de receita, quantidade de vendas e performance de vendedores.')
st.markdown("---")

k1, k2, k3, k4 = st.columns(4)
k1.metric('Receita Total',   fmt_brl(receita_total))
k2.metric('Total de Vendas', f'{qtd_vendas:,}')
k3.metric('Ticket Médio',    fmt_brl(ticket_medio))
k4.metric('Vendedores',      f'{qtd_vendedores_total}')

st.markdown("<br>", unsafe_allow_html=True)

aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

# ═══════════════════════ ABA 1 — RECEITA ═════════════════════════════════════
with aba1:
    col1, col2 = st.columns(2, gap='medium')

    with col1:
        fig_mapa_receita = px.scatter_geo(
            receita_estados, lat='lat', lon='lon',
            scope='south america', size='Preço',
            template=TEMPLATE,
            hover_name='Local da compra',
            hover_data={'lat': False, 'lon': False, 'Preço_fmt': True, 'Preço': False},
            title='Receita por Estado',
            color_discrete_sequence=[PRIMARY],
            size_max=45,
        )
        fig_mapa_receita.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=40, b=0),
            title=dict(font=dict(size=14, color=FONT_COLOR), x=0.01),
        )
        fig_mapa_receita.update_geos(
            bgcolor='rgba(0,0,0,0)', landcolor='#E8ECF4',
            oceancolor='#F4F6FB', showocean=True, showframe=False,
        )
        st.plotly_chart(fig_mapa_receita, use_container_width=True)

        # Barras horizontais — label DENTRO da barra
        top_est = receita_estados.head(7).copy()
        fig_est = go.Figure(go.Bar(
            x=top_est['Preço'],
            y=top_est['Local da compra'],
            orientation='h',
            text=top_est['Preço_fmt'],
            textposition='inside',
            insidetextanchor='end',
            textfont=dict(color='white', size=12),
            marker=dict(
                color=top_est['Preço'],
                colorscale=[[0, '#93C5FD'], [1, PRIMARY]],
                showscale=False,
            ),
            hovertemplate='%{y}: %{text}<extra></extra>',
        ))
        fig_est.update_layout(
            title='Top 7 Estados — Receita',
            yaxis=dict(categoryorder='total ascending'),
            xaxis_title='', yaxis_title='',
            xaxis=dict(showticklabels=False, showgrid=False),
        )
        fig_est = estilo_base(fig_est)
        st.plotly_chart(fig_est, use_container_width=True)

    with col2:
        fig_rec_mensal = px.line(
            receita_mensal, x='Mes', y='Preço',
            markers=True, color='Ano', line_dash='Ano',
            title='Receita Mensal por Ano',
            color_discrete_sequence=PALETTE,
        )
        fig_rec_mensal.update_traces(line_width=2.5, marker_size=7)
        fig_rec_mensal = estilo_linha(fig_rec_mensal)
        fig_rec_mensal.update_layout(yaxis_title='Receita (R$)', xaxis_title='')
        st.plotly_chart(fig_rec_mensal, use_container_width=True)

        fig_cat = go.Figure(go.Bar(
            x=receita_categorias['Preço'],
            y=receita_categorias['Categoria do Produto'],
            orientation='h',
            text=receita_categorias['Preço_fmt'],
            textposition='inside',
            insidetextanchor='end',
            textfont=dict(color='white', size=12),
            marker=dict(color=PALETTE[:len(receita_categorias)]),
            hovertemplate='%{y}: %{text}<extra></extra>',
        ))
        fig_cat.update_layout(
            title='Receita por Categoria',
            yaxis=dict(categoryorder='total ascending'),
            xaxis_title='', yaxis_title='',
            xaxis=dict(showticklabels=False, showgrid=False),
        )
        fig_cat = estilo_base(fig_cat)
        st.plotly_chart(fig_cat, use_container_width=True)

# ═══════════════════════ ABA 2 — VENDAS ══════════════════════════════════════
with aba2:
    col1, col2 = st.columns(2, gap='medium')

    with col1:
        fig_mapa_vendas = px.scatter_geo(
            vendas_estados, lat='lat', lon='lon',
            scope='south america', size='Preço',
            template=TEMPLATE,
            hover_name='Local da compra',
            hover_data={'lat': False, 'lon': False},
            title='Vendas por Estado',
            color_discrete_sequence=[PURPLE],
            size_max=45,
        )
        fig_mapa_vendas.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=40, b=0),
            title=dict(font=dict(size=14, color=FONT_COLOR), x=0.01),
        )
        fig_mapa_vendas.update_geos(
            bgcolor='rgba(0,0,0,0)', landcolor='#EDE9FE',
            oceancolor='#F4F6FB', showocean=True, showframe=False,
        )
        st.plotly_chart(fig_mapa_vendas, use_container_width=True)

        top_vend_est = vendas_estados.head(7).copy()
        fig_vest = go.Figure(go.Bar(
            x=top_vend_est['Preço'],
            y=top_vend_est['Local da compra'],
            orientation='h',
            text=[f'{v:,}' for v in top_vend_est['Preço']],
            textposition='inside',
            insidetextanchor='end',
            textfont=dict(color='white', size=12),
            marker=dict(
                color=top_vend_est['Preço'],
                colorscale=[[0, '#C4B5FD'], [1, PURPLE]],
                showscale=False,
            ),
            hovertemplate='%{y}: %{text} vendas<extra></extra>',
        ))
        fig_vest.update_layout(
            title='Top 7 Estados — Quantidade de Vendas',
            yaxis=dict(categoryorder='total ascending'),
            xaxis_title='', yaxis_title='',
            xaxis=dict(showticklabels=False, showgrid=False),
        )
        fig_vest = estilo_base(fig_vest)
        st.plotly_chart(fig_vest, use_container_width=True)

    with col2:
        fig_vend_mensal = px.line(
            vendas_mensal, x='Mes', y='Preço',
            markers=True, color='Ano', line_dash='Ano',
            title='Quantidade de Vendas Mensal por Ano',
            color_discrete_sequence=PALETTE,
        )
        fig_vend_mensal.update_traces(line_width=2.5, marker_size=7)
        fig_vend_mensal = estilo_linha(fig_vend_mensal)
        fig_vend_mensal.update_layout(yaxis_title='Quantidade de Vendas', xaxis_title='')
        st.plotly_chart(fig_vend_mensal, use_container_width=True)

        fig_vcat = go.Figure(go.Bar(
            x=vendas_categorias['Qtd'],
            y=vendas_categorias['Categoria do Produto'],
            orientation='h',
            text=[f'{v:,}' for v in vendas_categorias['Qtd']],
            textposition='inside',
            insidetextanchor='end',
            textfont=dict(color='white', size=12),
            marker=dict(color=PALETTE[:len(vendas_categorias)]),
            hovertemplate='%{y}: %{text}<extra></extra>',
        ))
        fig_vcat.update_layout(
            title='Vendas por Categoria',
            yaxis=dict(categoryorder='total ascending'),
            xaxis_title='', yaxis_title='',
            xaxis=dict(showticklabels=False, showgrid=False),
        )
        fig_vcat = estilo_base(fig_vcat)
        st.plotly_chart(fig_vcat, use_container_width=True)

# ═══════════════════════ ABA 3 — VENDEDORES ══════════════════════════════════
with aba3:
    qtd_show = st.slider('Número de vendedores exibidos', 2, 15, 10)
    st.markdown("<br>", unsafe_allow_html=True)

    top_rec = vendedores.sort_values('Receita Total', ascending=False).head(qtd_show).reset_index()
    top_qtd = vendedores.sort_values('Qtd Vendas',    ascending=False).head(qtd_show).reset_index()

    col1, col2 = st.columns(2, gap='medium')

    with col1:
        fig_rv = go.Figure(go.Bar(
            x=top_rec['Receita Total'],
            y=top_rec['Vendedor'],
            orientation='h',
            text=[fmt_brl_curto(v) for v in top_rec['Receita Total']],
            textposition='inside',
            insidetextanchor='end',
            textfont=dict(color='white', size=12),
            marker=dict(
                color=top_rec['Receita Total'],
                colorscale=[[0, '#93C5FD'], [1, PRIMARY]],
                showscale=False,
            ),
            hovertemplate='%{y}: %{text}<extra></extra>',
        ))
        fig_rv.update_layout(
            title=f'Top {qtd_show} Vendedores — Receita',
            yaxis=dict(categoryorder='total ascending'),
            xaxis_title='', yaxis_title='',
            xaxis=dict(showticklabels=False, showgrid=False),
        )
        fig_rv = estilo_base(fig_rv)
        st.plotly_chart(fig_rv, use_container_width=True)

        st.markdown("**Ticket Médio por Vendedor**")
        df_ticket = (
            vendedores.sort_values('Ticket Médio', ascending=False)
            .head(qtd_show).reset_index()
            [['Vendedor', 'Receita Total', 'Qtd Vendas', 'Ticket Médio']]
        )
        df_ticket['Receita Total'] = df_ticket['Receita Total'].apply(fmt_brl)
        df_ticket['Ticket Médio']  = df_ticket['Ticket Médio'].apply(fmt_brl)
        df_ticket['Qtd Vendas']    = df_ticket['Qtd Vendas'].apply(lambda x: f'{x:,}')
        st.dataframe(df_ticket, use_container_width=True, hide_index=True)

    with col2:
        fig_qv = go.Figure(go.Bar(
            x=top_qtd['Qtd Vendas'],
            y=top_qtd['Vendedor'],
            orientation='h',
            text=[f'{v:,}' for v in top_qtd['Qtd Vendas']],
            textposition='inside',
            insidetextanchor='end',
            textfont=dict(color='white', size=12),
            marker=dict(
                color=top_qtd['Qtd Vendas'],
                colorscale=[[0, '#C4B5FD'], [1, PURPLE]],
                showscale=False,
            ),
            hovertemplate='%{y}: %{text} vendas<extra></extra>',
        ))
        fig_qv.update_layout(
            title=f'Top {qtd_show} Vendedores — Quantidade de Vendas',
            yaxis=dict(categoryorder='total ascending'),
            xaxis_title='', yaxis_title='',
            xaxis=dict(showticklabels=False, showgrid=False),
        )
        fig_qv = estilo_base(fig_qv)
        st.plotly_chart(fig_qv, use_container_width=True)

        fig_scatter = px.scatter(
            vendedores.reset_index(),
            x='Qtd Vendas', y='Receita Total',
            hover_name='Vendedor',
            size='Ticket Médio',
            color='Ticket Médio',
            color_continuous_scale=['#93C5FD', PRIMARY],
            title='Receita × Quantidade de Vendas',
        )
        fig_scatter = estilo_linha(fig_scatter)
        fig_scatter.update_layout(
            xaxis_title='Qtd de Vendas',
            yaxis_title='Receita Total (R$)',
            coloraxis_colorbar=dict(title='Ticket Médio'),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)