# -*- coding: utf-8 -*-
"""
Api de visualização
Visualiza os arquivos .csv resultante do módulo VerificaVazaoGerada.py


Balanceamento não tem a coluna 'Data' e por isso o filtro por 'Ano' e 'Mês' é diferente:
Aqui o filtro buscará pelo intervalo entre 'ValidadeInicio' e 'ValidadeFim'

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

#- DataFrame balanceamento (carregado na página principal e já definido no session_state)
balanceamento = st.session_state['balanceamento']

#- Converte as colunas de data para o formato datetime
balanceamento['ValidadeInicio'] = pd.to_datetime(balanceamento['ValidadeInicio'])
balanceamento['ValidadeFim'] = pd.to_datetime(balanceamento['ValidadeFim'])

#- Gera lista de ANOS baseada no range total do arquivo
ano_min = balanceamento['ValidadeInicio'].min().year
ano_max = balanceamento['ValidadeFim'].max().year
lista_ano_options = list(range(ano_min, ano_max + 1))

#- Lista fixa de meses
lista_mes_options = list(range(1, 13))

#- Renomea a coluna 'EstacaoCodigo' para 'Codigo' para manter a consistência
balanceamento.rename(columns={'EstacaoCodigo': 'Codigo'}, inplace=True)

#- Título e descrição da página
st.subheader("Balanceamento das medições por período de validade da curva-chave no banco SQL")

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
#- A função modificada para considerar a lógica de intervalo para Ano e Mês, 
# já que o balanceamento não tem uma coluna 'Data' específica, mas sim um período de validade definido por 'ValidadeInicio' e 'ValidadeFim'.
def get_filtered_df_for_options(df, ur=None, codigo=None, ano=None, mes=None):
    temp_df = df.copy()
    if ur is not None:
        temp_df = temp_df[temp_df['UR'] == ur]
    if codigo is not None:
        temp_df = temp_df[temp_df['Codigo'] == codigo]
    
    # Lógica de Intervalo para Ano e Mês
    if ano is not None:
        # Criamos uma data base para comparação (ex: dia 15 do mês selecionado ou janeiro se mês for None)
        m = mes if mes is not None else 1
        data_ref = pd.Timestamp(year=int(ano), month=int(m), day=1)
        
        # Filtra linhas onde a data de referência está dentro do intervalo de validade
        temp_df = temp_df[(temp_df['ValidadeInicio'] <= data_ref) & 
                          (temp_df['ValidadeFim'] >= data_ref)]
    return temp_df

# --- Determina as opções para cada caixa de seleção com base nas outras seleções ---
# Opções para 'UR': Filtrado por Codigo, Ano e Mes
df_for_UR_options = get_filtered_df_for_options(balanceamento,
                                                codigo=current_codigo_selection,
                                                ano=current_ano_selection,
                                                mes=current_mes_selection)
# Obtém os valores únicos de 'UR' e os ordena para exibição
lista_UR_options = sorted(df_for_UR_options['UR'].unique().tolist())

# Opções para 'Codigo': Filtrado por UR, Ano e Mes
df_for_codigo_options = get_filtered_df_for_options(balanceamento,
                                                    ur=current_UR_selection,
                                                    ano=current_ano_selection,
                                                    mes=current_mes_selection)
# Obtém os valores únicos de 'Codigo' e os ordena
lista_codigo_options = sorted(df_for_codigo_options['Codigo'].unique().tolist())

# Opções para 'Ano': Filtrado por UR, Codigo e Mes
df_for_ano_options = get_filtered_df_for_options(balanceamento,
                                                 ur=current_UR_selection,
                                                 codigo=current_codigo_selection,
                                                 mes=current_mes_selection)

#- Obtém os valores únicos de 'Ano' a partir da coluna 'ValidadeFim' e os ordena
anos_disponiveis = pd.DatetimeIndex(df_for_ano_options['ValidadeFim']).year.unique()
lista_ano_options = sorted(anos_disponiveis.tolist(), reverse=True)

# Opções para 'Mes': Filtrado por UR, Codigo e Ano
df_for_mes_options = get_filtered_df_for_options(balanceamento,
                                                 ur=current_UR_selection,
                                                 codigo=current_codigo_selection,
                                                 ano=current_ano_selection)
# Obtém os valores únicos de 'Mes' e os ordena
lista_mes_options = list(range(1, 13))

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
exibe_balanceamento = balanceamento.copy()

#- Filtros aplicados com lógica de intervalo para Ano e Mês
if ur_select:
    exibe_balanceamento = exibe_balanceamento[exibe_balanceamento['UR'] == ur_select]
if codigo_select:
    exibe_balanceamento = exibe_balanceamento[exibe_balanceamento['Codigo'] == codigo_select]

#- Filtro por Intervalo de Datas (Lógica Principal)
if ano_select:
    # Se houver mês, usa o dia 1º. Se não, filtra o ano inteiro
    m = mes_select if mes_select else 1
    data_alvo = pd.Timestamp(year=int(ano_select), month=int(m), day=1)
    
    # Se o mês foi selecionado, queremos linhas que cubram aquele mês específico
    if mes_select:
        mask = (exibe_balanceamento['ValidadeInicio'] <= data_alvo) & \
               (exibe_balanceamento['ValidadeFim'] >= data_alvo)
    else:
        # Se só o ano foi selecionado, queremos qualquer linha que tenha interseção com aquele ano
        inicio_ano = pd.Timestamp(year=int(ano_select), month=1, day=1)
        fim_ano = pd.Timestamp(year=int(ano_select), month=12, day=31)
        mask = (exibe_balanceamento['ValidadeInicio'] <= fim_ano) & \
               (exibe_balanceamento['ValidadeFim'] >= inicio_ano)
    
    exibe_balanceamento = exibe_balanceamento[mask]
# < ------------------------------------------------------------------------------------------------------------------------------
#$ Formatação das colunas do DataFrame exibido

#< Isso é feito após a filtragem para garantir que apenas os dados finais sejam formatados.
#- Transforma colunas de data do DataFrame filtrado para o formato de string 'dd/mm/aaaa'.
exibe_balanceamento['ValidadeInicio'] = exibe_balanceamento['ValidadeInicio'].dt.strftime(date_format='%d/%m/%Y')
exibe_balanceamento['ValidadeFim'] = exibe_balanceamento['ValidadeFim'].dt.strftime(date_format='%d/%m/%Y')

#- Formata a coluna 'DesvioMedio' para uma casa após a vírgula
if 'DesvioMedio' in exibe_balanceamento.columns:
    exibe_balanceamento['DesvioMedio'] = exibe_balanceamento['DesvioMedio'].apply(lambda x: f"{x:.1f}".replace('.', ',') if pd.notnull(x) else x)

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Exibe o DataFrame resultante

#- Descrição do DataFrame exibido
st.markdown(f"**Número de registros:** {len(exibe_balanceamento)}")

#- Adiciona um espaço vertical antes do DataFrame para melhor separação visual
st.markdown("<br>", unsafe_allow_html=True)

#- Exibe o DataFrame ocultando o índice e usando a largura total do contêiner
st.dataframe(exibe_balanceamento, hide_index=True, width='stretch')

# < ------------------------------------------------------------------------------------------------------------------------------



