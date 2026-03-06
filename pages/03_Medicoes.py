# -*- coding: utf-8 -*-
"""
Api de visualização
Visualiza os arquivos .csv resultante do módulo VerificaVazaoGerada.py
a função de carregamento do csv está em Home.py

"""
 #<===============================================================================================================================
# $ Bibliotecas
import streamlit as st
import locale
import pandas as pd
import Funcoes as fc

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Configurações iniciais
#- Aumenta o limite de elementos para formatação do Styler
pd.set_option("styler.render.max_elements", 1000000)

#- Tenta configurar o locale para Português (Brasil)
try:
    # Tenta o padrão Linux/Unix (Streamlit Cloud)
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        # Tenta o padrão Windows
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        # Se ambos falharem, mantém o padrão do sistema
        locale.setlocale(locale.LC_ALL, '')

# - para usar a largura total da página
st.set_page_config(layout="wide")

#- logo CPRM no canto superior direito
st.image("https://intranet.sgb.gov.br/publique/media/marketing/logosgb_horizontal_original_v2.png", width=200)

#< ------------------------------------------------------------------------------------------------------------------------------
#- Chama a função (se já rodou, ele pega do cache instantaneamente)
dados = fc.carregar_dados_globais()

#- Grava no session_state para garantir compatibilidade
for chave, df in dados.items():
    st.session_state[chave] = df

#- Verifica se os dados foram carregados na página principal, caso contrário, exibe uma mensagem de erro e interrompe a execução.
if 'medicoes' not in st.session_state:
    st.error("Dados não carregados.")
    st.stop()

#- Inicializa as chaves no st.session_state se não existirem, para evitar KeyError
#< Isso garante que os valores persistam entre as re-execuções do script.
for key in ['selected_UR', 'selected_station', 'selected_ano', 'selected_mes']:
    if key not in st.session_state:
        st.session_state[key] = None

#- DataFrame medicoes (carregado na página principal e já definido no session_state)
medicoes = st.session_state['medicoes']

#- Renomea a coluna 'EstacaoCodigo' para 'Codigo' para manter a consistência
medicoes.rename(columns={'EstacaoCodigo': 'Codigo'}, inplace=True)
medicoes.rename(columns={'NumMedicao': 'NumMed'}, inplace=True)
medicoes.rename(columns={'AreaMolhada': 'AreaMolh'}, inplace=True)
medicoes.rename(columns={'Profundidade': 'Prof'}, inplace=True)

#- Cria um dicionário onde a CHAVE é o Código e o VALOR é o Nome
mapa_nomes = medicoes.drop_duplicates('Codigo').set_index('Codigo')['Nome'].to_dict()

#- Título e descrição da página
st.subheader("Medição e desvio em relação à curva-chave que está no banco SQL")

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Filtros interdependentes (UR, Estação, Ano, Mês)
#< A lista de seleção exibida depende das seleções feitas nos outros filtros.
#< Exemplo: A lista de estações depende da UR selecionada, do ano e do mês.

#- Define 4 colunas para os selectboxes: UR | Estação | Ano | Mes
col1, col2, col3, col4 = st.columns(4)

#- Obtém as seleções atuais do estado da sessão para cada filtro
current_UR_selection = st.session_state['selected_UR']
current_codigo_selection = st.session_state['selected_station']
current_ano_selection = st.session_state['selected_ano']
current_mes_selection = st.session_state['selected_mes']

# --- Função auxiliar para filtrar o DataFrame e obter opções dinâmicas ---
# Esta função recebe o DataFrame completo e as seleções atuais dos outros filtros.
def get_filtered_df_for_options(df, ur=None, codigo=None, ano=None, mes=None):
    """Retorna o DataFrame filtrado para gerar listas de opções dinâmicas."""
    temp_df = df.copy()
    if ur is not None: temp_df = temp_df[temp_df['UR'] == ur]
    if codigo is not None: temp_df = temp_df[temp_df['Codigo'] == codigo]
    if ano is not None: temp_df = temp_df[temp_df['Ano'] == ano]
    if mes is not None: temp_df = temp_df[temp_df['Mes'] == mes]
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

# --- Função de formatação para exibir Código - Nome ---
def formatar_estacao(codigo):
    """Formatação para exibição no selectbox.
       Busca o nome correspondente ao código no DataFrame original
    """
    nome = mapa_nomes.get(codigo, "Nome não encontrado")
    return f"{codigo} - {nome}"

# --- Selectbox atualizado ---
codigo_select = col2.selectbox(
    'Estação',                      # Rótulo do selectbox
    lista_codigo_options,           # Opções disponíveis (dinâmicas)
    key='selected_station',         # Chave única para o widget
    index=index_codigo,             # Índice da opção selecionada inicialmente
    format_func=formatar_estacao    # <--- Esta função altera o que o usuário vê
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

# --- Função para limpar os filtros ---
def limpar_filtros():
    """Reseta os valores dos filtros no st.session_state."""
    for key in ['selected_UR', 'selected_station', 'selected_ano', 'selected_mes']:
        st.session_state[key] = None

c_btn1, _, c_btn2 = st.columns([1, 4, 1])

# --- Botão para limpar todos os filtros ---
c_btn1.button("Limpar Filtros",          # legenda do botão
              on_click=limpar_filtros,   # função a ser chamada quando o botão for clicado
              use_container_width=False, # faz o botão ocupar toda a largura da coluna
              type= "secondary")         # estilo do botão (opcional)


# --- Aplica os filtros finais ao DataFrame a ser exibido ---
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

#$ Ordenação dos Dados críticos
#- Cria uma coluna temporária para o desvio absoluto (facilita a ordenação)
exibe_medicoes['Desvio_Abs'] = exibe_medicoes['Desvio'].abs()

#- Botão para ordenar pelos casos mais críticos
if c_btn2.button("🔥 Ordenar por Maior Desvio", 
                 use_container_width=True, 
                 type="primary"):
    exibe_medicoes = exibe_medicoes.sort_values(by='Desvio_Abs', ascending=False)
    st.success("Ordenado pelos maiores desvios absolutos.")
else:
    # Ordem padrão (geralmente por data ou como vier do banco)
    exibe_medicoes = exibe_medicoes.sort_values(by='Data', ascending=False)

#- Remove a coluna temporária para não poluir a tabela final
exibe_medicoes = exibe_medicoes.drop(columns=['Desvio_Abs'])

# < ------------------------------------------------------------------------------------------------------------------------------
# --- BLOCO DE MÉTRICAS --- 

if not exibe_medicoes.empty:
    st.divider() # Linha visual para separar das tabelas

    st.markdown("### Resumo")
    m1, m2, m3, m4 = st.columns(4)
    
    # Cálculos
    desvio_medio = exibe_medicoes['Desvio'].mean()
    maior_erro = exibe_medicoes['Desvio'].abs().max()
    # Conta quantos registros estão com desvio acima de 20% (positivo ou negativo)
    qtd_critica = len(exibe_medicoes[exibe_medicoes['Desvio'].abs() > 20])

    # Exibição dos Metric Cards
    m1.metric("Total de Registros", f"{len(exibe_medicoes)}")
    m2.metric("Desvio Médio", f"{desvio_medio:.2f}%")
    m3.metric("Maior Desvio Encontrado", f"{maior_erro:.2f}%")
    m4.metric("Alertas (> 20%)", f"{qtd_critica} registros")
    
    st.divider() # Linha visual para separar das tabelas

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Limite de segurança para exibição com formatação condicional
#- Limite de segurança para a exibição das linhas com formatação condicional (Styler)
LIMITE_ESTILO = 1000
total_linhas = len(exibe_medicoes)

#- Se for maior que o limite, pegamos apenas o topo para o Styler não quebrar
if total_linhas > LIMITE_ESTILO:
    df_para_estilizar = exibe_medicoes.head(LIMITE_ESTILO)
    aviso_limite = f"⚠️ Exibindo as primeiras {LIMITE_ESTILO} linhas. Use os filtros para ver mais dados."
else:
    df_para_estilizar = exibe_medicoes
    aviso_limite = None

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Formatação das colunas do DataFrame exibido
#- Função para definir a cor do texto baseada no valor
def colorir_desvio(valor):
    try:
        # Se o desvio (em módulo) for maior que 20%, pinta de vermelho
        cor = 'red' if abs(valor) > 20 else 'black'
        return f'color: {cor}'
    except:
        return 'color: black'

#- Formatação Brasileira via Pandas Styler e o estilo condicional
#< Isso mantém os dados como números (para ordenar), mas exibe com vírgula e ponto
df_estilizado = df_para_estilizar.style.format({
    'Codigo': "{:.0f}",
    'NumMed': "{:.0f}",
    'Cota': "{:.0f}",
    'Vazao': "{:.3f}",
    'AreaMolh': "{:.3f}",
    'Largura': "{:.3f}",
    'Prof': "{:.3f}",
    'Qcalc': "{:.3f}",
    'Desvio': "{:.2f}",
    # 'Desvio_ABS': "{:.2f}",
    'a': "{:.4f}",
    'h0': "{:.2f}",
    'n': "{:.3f}",
    'Ano': "{:.0f}",
    'Mes': "{:.0f}",
}, decimal=',', thousands='.') \
.map(colorir_desvio, subset=['Desvio']) # <--- Aplica a cor apenas na coluna Desvio

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Exibe o DataFrame resultante com a formatação aplicada

#- Exibe o DataFrame ocultando o índice e usando a largura total do contêiner
st.dataframe(
    df_estilizado,
    hide_index=True,
    width="stretch",
    column_config={
        "Data": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY"),
        "Codigo": st.column_config.NumberColumn("Código", format="%d"),
        "ValidadeInicio": st.column_config.DatetimeColumn("Validade Início", format="DD/MM/YYYY"),
        "ValidadeFim": st.column_config.DatetimeColumn("Validade Fim", format="DD/MM/YYYY"),
        "Cota": st.column_config.NumberColumn("Cota (cm)", format="%d"),
        "Vazao": "Vazão (m³/s)",
        "NumMed": st.column_config.NumberColumn("NumMed", format="%d"),
        "Curva": st.column_config.NumberColumn("Curva", format="%d"),
        "Lim_inf": st.column_config.NumberColumn("Limite Inf. (cm)", format="%d"),
        "Lim_sup": st.column_config.NumberColumn("Limite Sup. (cm)", format="%d"),
        "medidorvazao": st.column_config.NumberColumn("Medidor Vazão", format="%d"),
        "Ano": st.column_config.NumberColumn("Ano", format="%d"),
        "Mes": st.column_config.NumberColumn("Mês", format="%d"),
        # Notas: Quando usamos .style.format, o 'format' do column_config 
        # pode ser omitido para as colunas numéricas estilizadas.
    }
)

#- Exibição de Alerta
if aviso_limite:
    st.info(aviso_limite)

#- Descrição do DataFrame exibido
st.markdown("""
            **Descrição das Colunas**  
            **'Qcalc':** Vazão calculada pela curva chave.  
            **'Desvio':** Diferença entre a Vazão medida e a Vazão calculada pela curva chave (Qcalc).  
            **'Curva':** Número da curva chave da estação correspondente.
            """)
# < ------------------------------------------------------------------------------------------------------------------------------

