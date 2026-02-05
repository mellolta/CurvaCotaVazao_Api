# -*- coding: utf-8 -*-
"""
Api de visualização
Visualiza os arquivos .csv resultante do módulo VerificaVazaoGerada.py

Modificações:
a função de carregamento dos csv foi para Funcoes_Diversas.py

"""
 #<===============================================================================================================================
# $ Bibliotecas
import streamlit as st
import pandas as pd

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Configurações iniciais
# - para usar a largura total da página
st.set_page_config(layout="wide")

#- logo CPRM no canto superior direito
st.image("https://intranet.sgb.gov.br/publique/media/marketing/logosgb_horizontal_original_v2.png", width=200)

#- Inicializa as chaves no st.session_state se não existirem, para evitar KeyError
#< Isso garante que os valores persistam entre as re-execuções do script.
if 'selected_UR' not in st.session_state:
    st.session_state['selected_UR'] = None
if 'selected_station' not in st.session_state:
    st.session_state['selected_station'] = None
if 'selected_ano' not in st.session_state:
    st.session_state['selected_ano'] = None
if 'selected_mes' not in st.session_state:
    st.session_state['selected_mes'] = None

#- DataFrame medicoes (carregado na página principal e já definido no session_state)
medicoes = st.session_state['medicoes']

#- Renomea a coluna 'EstacaoCodigo' para 'Codigo' para manter a consistência
medicoes.rename(columns={'EstacaoCodigo': 'Codigo'}, inplace=True)
medicoes.rename(columns={'NumMedicao': 'NumMed'}, inplace=True)
medicoes.rename(columns={'AreaMolhada': 'AreaMolh'}, inplace=True)
medicoes.rename(columns={'Profundidade': 'Prof'}, inplace=True)

#- Título e descrição da página
st.subheader("Medição e desvio em relação à curva-chave que está no banco SQL")

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Filtros interdependentes (UR, Estação, Ano, Mês)
#< A lista de seleção exibida depende das seleções feitas nos outros filtros.
#< Exemplo: A lista de estações depende da UR selecionada, do ano e do mês.

#- Define 4 colunas para os selectboxes: UR | Estação | Ano | Mes
col1, col2, col3, col4 = st.columns(4)

# --- Função para limpar os filtros ---
def limpar_filtros():
    """Reseta os valores dos filtros no st.session_state."""
    st.session_state['selected_UR'] = None
    st.session_state['selected_station'] = None
    st.session_state['selected_ano'] = None
    st.session_state['selected_mes'] = None

#- Obtém as seleções atuais do estado da sessão para cada filtro
current_UR_selection = st.session_state['selected_UR']
current_codigo_selection = st.session_state['selected_station']
current_ano_selection = st.session_state['selected_ano']
current_mes_selection = st.session_state['selected_mes']

# --- Função auxiliar para filtrar o DataFrame e obter opções dinâmicas ---
# Esta função recebe o DataFrame completo e as seleções atuais dos outros filtros.
# Ela retorna um DataFrame filtrado que será usado para extrair as opções para um selectbox específico.
def get_filtered_df_for_options(df, ur=None, codigo=None, ano=None, mes=None):
    temp_df = df.copy()
    if ur is not None:
        temp_df = temp_df[temp_df['UR'] == ur]
    if codigo is not None:
        temp_df = temp_df[temp_df['Codigo'] == codigo]
    if ano is not None:
        temp_df = temp_df[temp_df['Ano'] == ano]
    if mes is not None:
        temp_df = temp_df[temp_df['Mes'] == mes]
    return temp_df

# --- Determina as opções para cada caixa de seleção com base nas outras seleções ---
# Opções para 'UR': Filtrado por Codigo, Ano e Mes
df_for_UR_options = get_filtered_df_for_options(medicoes,
                                                codigo=current_codigo_selection,
                                                ano=current_ano_selection,
                                                mes=current_mes_selection)
# Obtém os valores únicos de 'UR' e os ordena para exibição
lista_UR_options = sorted(df_for_UR_options['UR'].unique().tolist())

# Opções para 'Codigo': Filtrado por UR, Ano e Mes
df_for_codigo_options = get_filtered_df_for_options(medicoes,
                                                    ur=current_UR_selection,
                                                    ano=current_ano_selection,
                                                    mes=current_mes_selection)
# Obtém os valores únicos de 'Codigo' e os ordena
lista_codigo_options = sorted(df_for_codigo_options['Codigo'].unique().tolist())

# Opções para 'Ano': Filtrado por UR, Codigo e Mes
df_for_ano_options = get_filtered_df_for_options(medicoes,
                                                 ur=current_UR_selection,
                                                 codigo=current_codigo_selection,
                                                 mes=current_mes_selection)
# Obtém os valores únicos de 'Ano' e os ordena
lista_ano_options = sorted(df_for_ano_options['Ano'].unique().tolist(), reverse=True)

# Opções para 'Mes': Filtrado por UR, Codigo e Ano
df_for_mes_options = get_filtered_df_for_options(medicoes,
                                                 ur=current_UR_selection,
                                                 codigo=current_codigo_selection,
                                                 ano=current_ano_selection)
# Obtém os valores únicos de 'Mes' e os ordena
lista_mes_options = sorted(df_for_mes_options['Mes'].unique().tolist())

# --- Define o índice inicial para cada caixa de seleção para manter a seleção anterior, se válida ---
# Se o valor selecionado anteriormente ainda estiver na nova lista de opções, mantém-no selecionado.
# Caso contrário, define o índice como None (nenhuma seleção inicial).
def get_initial_index(current_selection, options_list):
    if current_selection is not None and current_selection in options_list:
        return options_list.index(current_selection)
    return None

index_UR = get_initial_index(current_UR_selection, lista_UR_options)
index_codigo = get_initial_index(current_codigo_selection, lista_codigo_options)
index_ano = get_initial_index(current_ano_selection, lista_ano_options)
index_mes = get_initial_index(current_mes_selection, lista_mes_options)

# --- Define as caixas de seleção com opções dinâmicas e seleções iniciais ---
ur_select = col1.selectbox(
    'Unidade Regional',               # Rótulo do selectbox
    lista_UR_options,                 # Opções disponíveis (dinâmicas)
    key='selected_UR',                # Chave única para o widget
    index=index_UR                    # Índice da opção selecionada inicialmente
)

codigo_select = col2.selectbox(
    'Estação',                        # Rótulo do selectbox
    lista_codigo_options,             # Opções disponíveis (dinâmicas)
    key='selected_station',           # Chave única para o widget
    index=index_codigo                # Índice da opção selecionada inicialmente
)

ano_select = col3.selectbox(
    'Ano',                            # Rótulo do selectbox
    lista_ano_options,                # Opções disponíveis (dinâmicas)
    key='selected_ano',               # Chave única para o widget
    index=index_ano                   # Índice da opção selecionada inicialmente
)

mes_select = col4.selectbox(
    'Mes',                            # Rótulo do selectbox
    lista_mes_options,                # Opções disponíveis (dinâmicas)
    key='selected_mes',               # Chave única para o widget
    index=index_mes                   # Índice da opção selecionada inicialmente
)

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Botões para limpar filtros e exibir resultado

col1, col2, col3 = st.columns(3)
# --- Botão para limpar todos os filtros ---
col1.button("Limpar Filtros", on_click=limpar_filtros)

# --- Botão Exibir Resultado ---
col2.button("Exibir Resultado após seleção", type="primary")

# --- Aplica os filtros finais ao DataFrame a ser exibido ---
# Começa com uma cópia do DataFrame original.
exibe_medicoes = medicoes.copy()

#- Aplica cada filtro, se selecionado
if ur_select:
    exibe_medicoes = exibe_medicoes[exibe_medicoes['UR'] == ur_select]
if codigo_select:
    exibe_medicoes = exibe_medicoes[exibe_medicoes['Codigo'] == codigo_select]
if ano_select:
    exibe_medicoes = exibe_medicoes[exibe_medicoes['Ano'] == ano_select]
if mes_select:
    exibe_medicoes = exibe_medicoes[exibe_medicoes['Mes'] == mes_select]

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Formatação das colunas do DataFrame exibido

#< Isso é feito após a filtragem para garantir que apenas os dados finais sejam formatados.
#- Transforma a coluna 'Data' do DataFrame filtrado para o formato de string 'dd/mm/aaaa'.
exibe_medicoes['Data'] = exibe_medicoes['Data'].dt.strftime(date_format='%d/%m/%Y')

#- Substitui ponto por virgula nas colunas numéricas para exibição
colunas_numericas = ['Vazao', 'AreaMolh', 'Largura', 'VelMedia', 'Prof', 'Qcalc', 'Desvio', 'Desvio_ABS', 'h0']
for col in colunas_numericas:
    if col in exibe_medicoes.columns:
        exibe_medicoes[col] = exibe_medicoes[col].apply(lambda x: f"{x:.2f}".replace('.', ',') if pd.notnull(x) else x) 

#- Substitui ponto por virgula nas colunas 'a', 'h0' e 'n'
colunas_numericas = ['a', 'h0', 'n']
for col in colunas_numericas:
    if col in exibe_medicoes.columns:
        exibe_medicoes[col] = exibe_medicoes[col].apply(lambda x: f"{x}".replace('.', ',') if pd.notnull(x) else x) 

#- Substitui virgula por nada nas colunas numéricas para exibição
# colunas_numericas = ['Codigo', 'Ano']
# for col in colunas_numericas:
#     if col in exibe_medicoes.columns:
#         exibe_medicoes[col] = exibe_medicoes[col].apply(lambda x: f"{x}".replace(',', '') if pd.notnull(x) else x)

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Exibe o DataFrame resultante

#- Descrição do DataFrame exibido
st.markdown(f"**Número de registros:** {len(exibe_medicoes)}")

#- Adiciona um espaço vertical antes do DataFrame para melhor separação visual
st.markdown("<br>", unsafe_allow_html=True)

#- Exibe o DataFrame ocultando o índice e usando a largura total do contêiner
st.dataframe(exibe_medicoes, hide_index=True, width='stretch')

# < ------------------------------------------------------------------------------------------------------------------------------



