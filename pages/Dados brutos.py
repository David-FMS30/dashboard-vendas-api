import re
import time
from datetime import date

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="Painel de Vendas",
    layout="wide",
)


URL_DADOS = "https://labdados.com/produtos"


st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 14px 16px;
        }

        [data-testid="stSidebar"] {
            background: #f8fafc;
        }

        div[data-testid="stDownloadButton"] > button,
        div[data-testid="stFormSubmitButton"] > button {
            width: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=600, show_spinner=False)
def carregar_dados() -> pd.DataFrame:
    response = requests.get(URL_DADOS, timeout=20)
    response.raise_for_status()

    dados = pd.DataFrame.from_dict(response.json())
    dados["Data da Compra"] = pd.to_datetime(
        dados["Data da Compra"],
        format="%d/%m/%Y",
        errors="coerce",
    )

    return dados.dropna(subset=["Data da Compra"])


@st.cache_data(show_spinner=False)
def converter_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def lista_ordenada(serie: pd.Series) -> list:
    return sorted(serie.dropna().unique().tolist())


def limpar_nome_arquivo(nome: str) -> str:
    nome_limpo = re.sub(r"[^a-zA-Z0-9_-]+", "_", nome.strip())
    return nome_limpo or "dados_filtrados"


def mostrar_sucesso() -> None:
    mensagem = st.success("Arquivo preparado com sucesso.")
    time.sleep(3)
    mensagem.empty()


try:
    with st.spinner("Carregando dados..."):
        dados = carregar_dados()
except requests.RequestException as erro:
    st.error("Não foi possível carregar os dados. Verifique sua conexão e tente novamente.")
    st.caption(f"Detalhes técnicos: {erro}")
    st.stop()


data_min = dados["Data da Compra"].min().date()
data_max = dados["Data da Compra"].max().date()
produtos_disponiveis = lista_ordenada(dados["Produto"])


st.title("Painel de Vendas")
st.caption("Explore os dados brutos, refine os filtros e exporte somente o recorte necessário.")


with st.sidebar:
    st.header("Filtros")

    with st.form("formulario_filtros"):
        produtos = st.multiselect(
            "Produto",
            produtos_disponiveis,
            default=[],
            placeholder="Digite para buscar e selecione",
            help="Deixe em branco para considerar todos os produtos.",
        )

        categorias = st.multiselect(
            "Categoria",
            lista_ordenada(dados["Categoria do Produto"]),
            default=lista_ordenada(dados["Categoria do Produto"]),
        )

        vendedores = st.multiselect(
            "Vendedor",
            lista_ordenada(dados["Vendedor"]),
            default=lista_ordenada(dados["Vendedor"]),
        )

        locais = st.multiselect(
            "Local da compra",
            lista_ordenada(dados["Local da compra"]),
            default=lista_ordenada(dados["Local da compra"]),
        )

        pagamentos = st.multiselect(
            "Tipo de pagamento",
            lista_ordenada(dados["Tipo de pagamento"]),
            default=lista_ordenada(dados["Tipo de pagamento"]),
        )

        preco = st.slider(
            "Preço",
            min_value=float(dados["Preço"].min()),
            max_value=float(dados["Preço"].max()),
            value=(float(dados["Preço"].min()), float(dados["Preço"].max())),
        )

        frete = st.slider(
            "Frete",
            min_value=float(dados["Frete"].min()),
            max_value=float(dados["Frete"].max()),
            value=(float(dados["Frete"].min()), float(dados["Frete"].max())),
        )

        avaliacao = st.slider("Avaliação", 1, 5, value=(1, 5))

        parcelas = st.slider(
            "Quantidade de parcelas",
            min_value=int(dados["Quantidade de parcelas"].min()),
            max_value=int(dados["Quantidade de parcelas"].max()),
            value=(
                int(dados["Quantidade de parcelas"].min()),
                int(dados["Quantidade de parcelas"].max()),
            ),
        )

        periodo = st.date_input(
            "Período da compra",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max,
        )

        aplicar_filtros = st.form_submit_button("Aplicar filtros", use_container_width=True)


if isinstance(periodo, tuple) and len(periodo) == 2:
    data_inicio, data_fim = periodo
else:
    data_inicio = periodo if isinstance(periodo, date) else data_min
    data_fim = data_inicio


produtos_filtrados = produtos or produtos_disponiveis

mascara = (
    dados["Produto"].isin(produtos_filtrados)
    & dados["Categoria do Produto"].isin(categorias)
    & dados["Vendedor"].isin(vendedores)
    & dados["Local da compra"].isin(locais)
    & dados["Tipo de pagamento"].isin(pagamentos)
    & dados["Preço"].between(preco[0], preco[1])
    & dados["Frete"].between(frete[0], frete[1])
    & dados["Avaliação da compra"].between(avaliacao[0], avaliacao[1])
    & dados["Quantidade de parcelas"].between(parcelas[0], parcelas[1])
    & dados["Data da Compra"].between(pd.Timestamp(data_inicio), pd.Timestamp(data_fim))
)

dados_filtrados = dados.loc[mascara].copy()


colunas_disponiveis = list(dados.columns)
colunas_padrao = [
    "Produto",
    "Categoria do Produto",
    "Preço",
    "Frete",
    "Data da Compra",
    "Vendedor",
    "Local da compra",
    "Avaliação da compra",
    "Tipo de pagamento",
]

colunas_selecionadas = st.multiselect(
    "Colunas exibidas",
    colunas_disponiveis,
    default=[coluna for coluna in colunas_padrao if coluna in colunas_disponiveis],
)

if not colunas_selecionadas:
    st.warning("Selecione ao menos uma coluna para visualizar a tabela.")
    st.stop()

dados_visiveis = dados_filtrados[colunas_selecionadas]


total_linhas = len(dados_visiveis)
total_colunas = len(colunas_selecionadas)
ticket_medio = dados_filtrados["Preço"].mean() if total_linhas else 0
frete_medio = dados_filtrados["Frete"].mean() if total_linhas else 0

metrica_1, metrica_2, metrica_3, metrica_4 = st.columns(4)
metrica_1.metric("Linhas", f"{total_linhas:,}".replace(",", "."))
metrica_2.metric("Colunas", total_colunas)
metrica_3.metric("Preço médio", f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
metrica_4.metric("Frete médio", f"R$ {frete_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


aba_tabela, aba_resumo, aba_exportar = st.tabs(["Tabela", "Resumo", "Exportar"])

with aba_tabela:
    if dados_visiveis.empty:
        st.info("Nenhum registro encontrado para os filtros selecionados.")
    else:
        st.dataframe(
            dados_visiveis,
            use_container_width=True,
            hide_index=True,
        )

with aba_resumo:
    if dados_filtrados.empty:
        st.info("Ajuste os filtros para visualizar o resumo.")
    else:
        coluna_a, coluna_b = st.columns(2)

        with coluna_a:
            st.subheader("Vendas por categoria")
            resumo_categoria = (
                dados_filtrados.groupby("Categoria do Produto")["Preço"]
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(resumo_categoria)

        with coluna_b:
            st.subheader("Formas de pagamento")
            resumo_pagamento = dados_filtrados["Tipo de pagamento"].value_counts()
            st.bar_chart(resumo_pagamento)

with aba_exportar:
    st.subheader("Exportar dados filtrados")

    nome_arquivo = st.text_input(
        "Nome do arquivo",
        value="dados_filtrados",
        help="O arquivo será salvo em formato CSV.",
    )

    nome_final = f"{limpar_nome_arquivo(nome_arquivo)}.csv"

    st.download_button(
        "Baixar CSV",
        data=converter_csv(dados_visiveis),
        file_name=nome_final,
        mime="text/csv",
        disabled=dados_visiveis.empty,
        on_click=mostrar_sucesso,
        use_container_width=True,
    )
