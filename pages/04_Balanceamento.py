# -*- coding: utf-8 -*-
"""
Api de visualização
Visualiza os arquivos .csv resultante do módulo VerificaVazaoGerada.py
a função de carregamento do csv está em Home.py

Balanceamento não tem a coluna 'Data' e por isso o filtro por 'Ano' e 'Mês' é diferente:
Aqui o filtro buscará pelo intervalo entre 'ValidadeInicio' e 'ValidadeFim'

"""
 #<===============================================================================================================================
# $ Bibliotecas
import streamlit as st
import pandas as pd
import funcoes as fc

# < ------------------------------------------------------------------------------------------------------------------------------
#- Configurações iniciais da página
fc.configuracoes_iniciais()

#- Carrega os dados necessários para essa página
fc.gerenciar_pagina_e_carregar("04_Balanceamento", ["balanceamento"])

#- Título e descrição da página
st.subheader("Balanceamento das medições por período de validade da curva-chave no banco SQL")

#- Verifica se os dados foram carregados na página principal, caso contrário, exibe uma mensagem de erro e interrompe a execução.
if 'balanceamento' not in st.session_state:
    st.error("Dados não carregados.")
    st.stop()

#- DataFrame balanceamento (carregado na página principal e já definido no session_state)
balanceamento = st.session_state['balanceamento']

#- Chama a função que retorna o dataframe já filtrado
df_filtrado = fc.menu_filtros_multi(balanceamento)

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Botões para limpar filtros e exibir resultado

c_btn1, _, c_btn2 = st.columns([1, 4, 1])

# --- Botão para limpar todos os filtros ---
c_btn1.button("Limpar Filtros",             # legenda do botão
              on_click=fc.limpar_filtros,   # função a ser chamada quando o botão for clicado
              use_container_width=False,    # faz o botão ocupar toda a largura da coluna
              type= "secondary")            # estilo do botão (opcional)

# < ------------------------------------------------------------------------------------------------------------------------------
#- Se o DF estiver vazio, paramos a execução aqui para não dar erro nas métricas abaixo
if df_filtrado.empty:
    st.stop()
    
#- Aplicação do filtro no DataFrame da página usando o que a função retornou
exibe_balanceamento = df_filtrado.copy()

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Ordenação dos Dados críticos
#- Cria uma coluna temporária para o desvio absoluto (facilita a ordenação)
exibe_balanceamento['Desvio_Abs'] = exibe_balanceamento['DesvioMedio'].abs()

#- Botão para ordenar pelos casos mais críticos
if c_btn2.button("🔥 Ordenar por Maior Desvio", 
                 use_container_width=True, 
                 type="primary"):
    exibe_balanceamento = exibe_balanceamento.sort_values(by='Desvio_Abs', ascending=False)
    st.success("Ordenado pelos maiores desvios.")
else:
    # Ordem padrão (geralmente por data ou como vier do banco)
    exibe_balanceamento = exibe_balanceamento.sort_values(by='ValidadeFim', ascending=False)

#- Remove a coluna temporária para não poluir a tabela final
exibe_balanceamento = exibe_balanceamento.drop(columns=['Desvio_Abs'])

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Limite de segurança para exibição com formatação condicional
#- Limite de segurança para a exibição das linhas com formatação condicional (Styler)
LIMITE_ESTILO = 1000
total_linhas = len(exibe_balanceamento)

#- Se for maior que o limite, pegamos apenas o topo para o Styler não quebrar
if total_linhas > LIMITE_ESTILO:
    df_para_estilizar = exibe_balanceamento.head(LIMITE_ESTILO)
    aviso_limite = f"⚠️ Exibindo as primeiras {LIMITE_ESTILO} linhas. Use os filtros para ver mais dados."
else:
    df_para_estilizar = exibe_balanceamento
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
    
def colorir_positivos(valor):
    try:
        cor = 'red' if abs(valor) > 70 else 'black'
        return f'color: {cor}'
    except:
        return 'color: black'
    
def colorir_negativos(valor):
    try:
        cor = 'red' if abs(valor) < 30 else 'black'
        return f'color: {cor}'
    except:
        return 'color: black'

#- Formatação Brasileira via Pandas Styler e o estilo condicional
#< Isso mantém os dados como números (para ordenar), mas exibe com vírgula e ponto
df_estilizado = df_para_estilizar.style.format({
    # 'ValidadeInicio': lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "",
    # 'ValidadeFim': lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "",
    'Neg%': "{:.1f}",
    'Pos%': "{:.1f}",
    'DesvioMedio': "{:.1f}",
}, decimal=',', thousands='.') \
.map(colorir_desvio, subset=['DesvioMedio']) \
.map(colorir_positivos, subset=['Pos%']) \
.map(colorir_negativos, subset=['Neg%'])
#-  ^^^ Aplica a cor nas colunas Neg% e Pos%

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Exibe o DataFrame resultante

#- Descrição do DataFrame exibido
st.markdown(f"**Número de registros:** {len(exibe_balanceamento)}")
st.markdown("<br>", unsafe_allow_html=True) #- quebra de linha usando HTML para espaçamento

#- Exibe o DataFrame ocultando o índice e usando a largura total do contêiner
st.dataframe(
    df_estilizado,
    hide_index=True, # Esconde o índice
    width="stretch", # Faz a tabela ocupar toda a largura disponível
    column_config={
        "UR": st.column_config.Column("UR", help="Unidade Regional"),
        "Codigo": st.column_config.NumberColumn("Código", format="%d", 
                                                help="Código da estação."),
        "Nome": st.column_config.Column("Nome", help="Nome da estação"),
        "Curva": st.column_config.NumberColumn("Curva", format="%d", 
                                               help="Numeração da curva (em relação à quantidade total de curvas que existem para a estação.)"),
        "ValidadeInicio": st.column_config.DatetimeColumn(
            "Validade Início", format="DD/MM/YYYY",
            help="Início da validade da curva chave"
            ),
        "ValidadeFim": st.column_config.DatetimeColumn(
            "Validade Fim", format="DD/MM/YYYY",
            help="Fim da validade da curva chave"
            ),
        "QtdPontos": st.column_config.NumberColumn("Qtd medições", format="%d", 
            help="Quantidade de medições que estão dentro do período de validade da curva-chave"),
        "Negativos": st.column_config.NumberColumn("Negativos", format="%d", 
            help="Quantidade de medições com desvio negativo (vazão calculada pela curva-chave é maior que a vazão medida)"),
        "Positivos": st.column_config.NumberColumn("Positivos", format="%d", 
            help="Quantidade de medições com desvio positivo (vazão calculada pela curva-chave é menor que a vazão medida)"),
        "DesvioMedio": st.column_config.NumberColumn("Desvio Médio (%)", 
            help="Desvio médio percentual entre as medições"), 
        "Neg%": st.column_config.NumberColumn("Negativos (%)", 
            help="Percentual de medições localizadas abaixo da curva chave"), 
        "Pos%": st.column_config.NumberColumn("Positivos (%)", 
            help="Percentual de medições localizadas acima da curva chave"), 
        # Notas: Quando usamos .style.format, o 'format' do column_config 
        # pode ser omitido para as colunas numéricas estilizadas.
    }
)

#- Exibição de Alerta
if aviso_limite:
    st.info(aviso_limite)

#- Descrição do DataFrame exibido
st.markdown(":small[💡 Colocar o ponteiro do mouse sobre o cabeçalho para obter a descrição das colunas]")

# < ------------------------------------------------------------------------------------------------------------------------------



