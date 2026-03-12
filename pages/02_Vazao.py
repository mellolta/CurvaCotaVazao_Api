# -*- coding: utf-8 -*-
"""
Api de visualização
Visualiza os arquivos .csv resultante do módulo VerificaVazaoGerada.py
a função de carregamento do csv está em Home.py

"""
 #<===============================================================================================================================
# $ Bibliotecas
import streamlit as st
import pandas as pd
import funcoes as fc

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Configurações iniciais
fc.configuracoes_iniciais()

#- Título e descrição da página
st.subheader("Vazão do banco SQL X Vazão calculada pela curva-chave (Qcalc)")

#- Verifica se os dados foram carregados na página principal, caso contrário, exibe uma mensagem de erro e interrompe a execução.
if 'vazao' not in st.session_state:
    st.error("Dados não carregados.")
    st.stop()

#- DataFrame vazao (carregado na página principal e já definido no session_state)
vazao = st.session_state['vazao']

#- Chama a função que retorna o dataframe já filtrado
df_filtrado = fc.menu_filtros_multi(vazao)

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Botões para limpar filtros e exibir resultado

c_btn1, _, c_btn2 = st.columns([1, 4, 1])

# --- Botão para limpar todos os filtros ---
c_btn1.button("Limpar Filtros",          # legenda do botão
              on_click=fc.limpar_filtros,   # função a ser chamada quando o botão for clicado
              use_container_width=False, # faz o botão ocupar toda a largura da coluna
              type= "secondary")         # estilo do botão (opcional)

# < ------------------------------------------------------------------------------------------------------------------------------
#- Se o DF estiver vazio, paramos a execução aqui para não dar erro nas métricas abaixo
if df_filtrado.empty:
    st.stop()

#- Aplicação do filtro no DataFrame da página usando o que a função retornou
exibe_vazao = df_filtrado.copy()

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Ordenação dos Dados críticos
#- Cria uma coluna temporária para o desvio absoluto (facilita a ordenação)
exibe_vazao['Desvio_Abs'] = exibe_vazao['Desvio'].abs()

#- Botão para ordenar pelos casos mais críticos
if c_btn2.button("🔥 Ordenar por Maior Desvio", 
                 use_container_width=True, 
                 type="primary"):
    exibe_vazao = exibe_vazao.sort_values(by='Desvio_Abs', ascending=False)
    st.success("Ordenado pelos maiores desvios absolutos.")
else:
    # Ordem padrão (geralmente por data ou como vier do banco)
    exibe_vazao = exibe_vazao.sort_values(by='Data', ascending=False)

#- Remove a coluna temporária para não poluir a tabela final
exibe_vazao = exibe_vazao.drop(columns=['Desvio_Abs'])

# < ------------------------------------------------------------------------------------------------------------------------------
# --- BLOCO DE MÉTRICAS --- 

if not exibe_vazao.empty:
    st.divider() # Linha visual para separar das tabelas

    st.markdown("### Resumo")
    m1, m2, m3, m4 = st.columns(4)
    
    # Cálculos
    desvio_medio = exibe_vazao['Desvio'].mean()
    maior_erro = exibe_vazao['Desvio'].abs().max()
    # Conta quantos registros estão com desvio acima de 10% (positivo ou negativo)
    qtd_critica = len(exibe_vazao[exibe_vazao['Desvio'].abs() > 10])

    # Exibição dos Metric Cards
    m1.metric("Total de Registros", f"{len(exibe_vazao)}")
    m2.metric("Desvio Médio", f"{desvio_medio:.2f}")
    m3.metric("Maior Desvio Encontrado", f"{maior_erro:.2f}")
    m4.metric("Alertas (> 10%)", f"{qtd_critica} registros")
    
    st.divider() # Linha visual para separar das tabelas

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Limite de segurança para exibição com formatação condicional
#- Limite de segurança para a exibição das linhas com formatação condicional (Styler)
LIMITE_ESTILO = 1000
total_linhas = len(exibe_vazao)

#- Se for maior que o limite, pegamos apenas o topo para o Styler não quebrar
if total_linhas > LIMITE_ESTILO:
    df_para_estilizar = exibe_vazao.head(LIMITE_ESTILO)
    aviso_limite = f"⚠️ Exibindo as primeiras {LIMITE_ESTILO} linhas. Use os filtros para ver mais dados."
else:
    df_para_estilizar = exibe_vazao
    aviso_limite = None

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Formatação das colunas do DataFrame exibido
#- Função para definir a cor do texto baseada no valor
def colorir_desvio(valor):
    try:
        # Se o desvio (em módulo) for maior que 10%, pinta de vermelho
        cor = 'red' if abs(valor) > 10 else 'black'
        return f'color: {cor}'
    except:
        return 'color: black'

#- Formatação Brasileira via Pandas Styler e o estilo condicional
#< Isso mantém os dados como números (para ordenar), mas exibe com vírgula e ponto
df_estilizado = df_para_estilizar.style.format({
    'Vazao': "{:.3f}",
    'Qcalc': "{:.3f}",
    'Desvio': "{:.2f}",
    'Ano': "{:.0f}",
    'Mes': "{:.0f}",
}, decimal=',', thousands='.') \
.map(colorir_desvio, subset=['Desvio'])

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Exibe o DataFrame resultante

#- Exibe o DataFrame ocultando o índice e usando a largura total do contêiner
st.dataframe(
    df_estilizado,
    hide_index=True,
    width="stretch",
    column_config={
        "UR": st.column_config.Column("UR", help="Unidade Regional"),
        "Codigo": st.column_config.NumberColumn("Código", format="%d", 
                                                help="Código da estação."),
        "Nome": st.column_config.Column("Nome", help="Nome da estação"),
        "Data": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY", 
                                                help="Data da leitura."),
        "Cota": st.column_config.NumberColumn("Cota (cm)", format="%d", 
                                              help="Cota lida."),
        "Status": st.column_config.Column("Status Cota", 
                                          help="Classificação da cota do dia."),
        "Vazao": st.column_config.NumberColumn("Vazão (m³/s)", 
            help="Vazão presente no banco SQL."),
        "Qcalc": st.column_config.NumberColumn("QCalc (m³/s)", 
            help="Vazão calculada através da equação da curva chave vigente para a cota lida."),
        "Desvio": st.column_config.NumberColumn("Desvio (m³/s)", 
            help="Diferença entre vazão calculada pela curva chave (Qcalc) e a vazão que está no banco SQL."),
        "ValidadeInicio": st.column_config.DatetimeColumn("Validade Início", 
            format="DD/MM/YYYY", 
            help="Início da validade da curva chave"),
        "ValidadeFim": st.column_config.DatetimeColumn("Validade Fim", 
            format="DD/MM/YYYY", 
            help="Fim da validade da curva chave"),
        "Lim_inf": st.column_config.NumberColumn("Limite Inf. (cm)", 
            format="%d", 
            help="Limite inferior da curva chave"),
        "Lim_sup": st.column_config.NumberColumn(
            "Limite Sup. (cm)", 
            format="%d", 
            help="Limite superior da curva chave"),
        "Ano": st.column_config.NumberColumn("Ano", format="%d", 
                                             help="Ano da leitura"),
        "Mes": st.column_config.NumberColumn("Mês", format="%d", 
                                             help="Mês da leitura"),
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
