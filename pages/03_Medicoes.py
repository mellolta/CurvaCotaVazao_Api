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
import plotly.graph_objects as go
import funcoes as fc

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Configurações iniciais
fc.configuracoes_iniciais()

#- Título e descrição da página
st.subheader("Medição e desvio em relação à curva-chave que está no banco SQL")

#- Verifica se os dados foram carregados na página principal, caso contrário, exibe uma mensagem de erro e interrompe a execução.
if 'medicoes' not in st.session_state:
    st.error("Dados não carregados.")
    st.stop()

#- DataFrame medicoes
medicoes = st.session_state['medicoes']

#- Chama a função que retorna o dataframe já filtrado
df_filtrado = fc.menu_filtros_multi(medicoes)

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
exibe_medicoes = df_filtrado.copy()

#- Renomea a coluna
exibe_medicoes.rename(columns={
    'NumMedicao': 'NumMed', 
    'AreaMolhada': 'AreaMolh', 
    'Profundidade': 'Prof'
}, inplace=True)

# < ------------------------------------------------------------------------------------------------------------------------------
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
# < ------------------------------------------------------------------------------------------------------------------------------
# $ Lógica do Gráfico

# Pegamos as estações que estão selecionadas no filtro global
estacoes_selecionadas = st.session_state.filtro_cod

if not estacoes_selecionadas:
    st.warning("⚠️ Selecione **uma Estação** no filtro acima para visualizar o gráfico de dispersão.")
    st.stop()

if len(estacoes_selecionadas) > 1:
    st.info("💡 Sugestão: Selecione apenas **uma estação** para uma análise mais clara da Curva-Chave.")
    # Se quiser permitir múltiplas, o código abaixo funciona, mas os pontos ficarão misturados.

# Filtragem dos dados (df_filtrado já contém os filtros de UR, Ano e Mês)
df_plot = df_filtrado.copy()

if df_plot.empty:
    # A mensagem de aviso já é disparada pela função menu_filtros_multi
    st.stop()
else:
    # --- PREPARAÇÃO DOS DADOS ---
    # Criamos um dicionário de nomes para o título (mapa_nomes)
    mapa_nomes = df_plot.drop_duplicates('Codigo').set_index('Codigo')['Nome'].to_dict()
    
    # --- CRIAÇÃO DO SCATTER PLOT ---
    fig = go.Figure()

    # Adicionamos as medições
    fig.add_trace(go.Scatter(
        x=df_plot['Vazao'],
        y=df_plot['Cota'],
        mode='markers',
        name='Medições',
        marker=dict(
            size=10,
            color=df_plot['Desvio'].abs(), # Cor varia conforme o desvio
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Desvio %"),
            opacity=0.8,
            line=dict(width=1, color='DarkSlateGrey')
        ),
        text=df_plot['Data'], 
        customdata=df_plot['Desvio'],
        hovertemplate="<b>Data:</b> %{text}<br><b>Vazão:</b> %{x:.2f} m³/s<br><b>Cota:</b> %{y:.0f} cm<br><b>Desvio:</b> %{customdata:.1f}%<extra></extra>"
    ))

    # Ajustes de Layout
    titulo_estacao = f"Relação Cota x Vazão - Estação: {estacoes_selecionadas[0]}"
    if len(estacoes_selecionadas) == 1:
        titulo_estacao += f" ({mapa_nomes.get(estacoes_selecionadas[0])})"

    fig.update_layout(
        title={'text': titulo_estacao, 'x': 0.5},
        xaxis_title="Vazão (m³/s)",
        yaxis_title="Cota (cm)",
        plot_bgcolor='rgb(245, 245, 245)',
        paper_bgcolor='white',
        height=700,
        hovermode="closest"
    )

    fig.update_xaxes(showgrid=True, gridcolor='lightgray', zeroline=True, zerolinecolor='gray')
    fig.update_yaxes(showgrid=True, gridcolor='lightgray', zeroline=True, zerolinecolor='gray')

    st.plotly_chart(fig, width='stretch')

    # Expander para ver os dados brutos filtrados
    # with st.expander("Ver dados brutos desta seleção"):
    #     st.dataframe(df_plot[['Data', 'Codigo', 'Cota', 'Vazao', 'Desvio']], 
    #                  hide_index=True, width='stretch')

# < ------------------------------------------------------------------------------------------------------------------------------
# st.markdown("""
# ---
# **Dica de Análise:** Observe a dispersão dos pontos. Pontos muito fora da tendência (outliers) podem indicar erros de medição ou mudanças na seção do rio (extravasamento ou erosão).
# """)

