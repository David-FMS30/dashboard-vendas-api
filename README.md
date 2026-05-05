# Projeto Dashboard de Vendas - Python e Streamlit

Este projeto consiste em um dashboard interativo desenvolvido em Python para a análise de dados de vendas de uma rede de livrarias. O sistema consome informações diretamente de uma API, processa os dados e os apresenta de forma visual e dinâmica para suporte à decisão gerencial.

## Objetivos do Projeto

O objetivo principal deste sistema é automatizar a visualização de métricas de desempenho de vendas, permitindo:
* Acompanhamento do faturamento total, ticket médio e volume de vendas em tempo real.
* Monitoramento da performance individual de cada vendedor.
* Análise da distribuição geográfica das vendas por meio de mapas interativos.
* Observação de tendências temporais e variações mensais de faturamento.

## Tecnologias Utilizadas

* **Python**: Linguagem base do projeto.
* **Streamlit**: Biblioteca utilizada para a criação da interface web e estrutura de navegação[cite: 5].
* **Pandas**: Utilizada para a manipulação, limpeza e estruturação dos dados vindos da API[cite: 5].
* **Plotly**: Responsável pela geração de gráficos interativos e mapas de calor[cite: 5].
* **Requests**: Utilizada para realizar a integração e o consumo de dados da URL externa[cite: 5].

## Estrutura do Repositório

Para o funcionamento correto do recurso de múltiplas páginas do Streamlit, os arquivos estão organizados da seguinte forma:

* **Dashboard.py**: Arquivo principal contendo a visão geral e os indicadores do dashboard.
* **requirements.txt**: Lista de bibliotecas necessárias para a execução do projeto (streamlit, pandas, plotly, requests).
* **pages/**: Pasta que contém as páginas adicionais do sistema.
    * **01_Dados_brutos.py**: Página dedicada à visualização e filtragem da base de dados completa[cite: 5].
* **img/**: Pasta contendo capturas de tela do sistema para documentação.

## Funcionalidades e Análises

1. **Indicadores de Desempenho (KPIs)**: Exibição centralizada de métricas como Faturamento Total, Quantidade de Vendas e Ticket Médio.
2. **Filtros Dinâmicos**: Painel lateral que permite segmentar os dados por região, período e vendedor.
3. **Análise Geográfica**: Mapa do Brasil com a distribuição da receita por estado.
4. **Séries Temporais**: Gráfico de linhas comparando o faturamento mensal ao longo dos anos de 2020 a 2023.
5. **Layout Responsivo**: Interface adaptada para visualização em diferentes dispositivos, incluindo suporte para visualização móvel[cite: 3].

## Como Executar o Projeto

1. Instalar as dependências listadas no arquivo de requisitos:
   `pip install -r requirements.txt`

2. Executar a aplicação através do terminal:
   `streamlit run Dashboard.py`

---
