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
import funcoes as fc
import plotly.express as px  # Adicionado para o gráfico
import plotly.graph_objects as go  # Adicionado para gráficos com múltiplas camadas

# < ------------------------------------------------------------------------------------------------------------------------------
#- Configurações iniciais da página
fc.configuracoes_iniciais()

#- Título e descrição da página
st.subheader("Série temporal e análise comparativa dos valores de cota e a vazão com o dia anterior")

#- Carrega os dados necessários para essa página
fc.gerenciar_pagina_e_carregar("05_Serie_temporal", ["cota_vazao", "passo_diario", "cotas2L", "medicoes"])

#- Verifica se os dados foram carregados na página principal, caso contrário, exibe uma mensagem de erro e interrompe a execução.
if 'passo_diario' not in st.session_state or \
    'cota_vazao' not in st.session_state or \
    'cotas2L' not in st.session_state or \
    'medicoes' not in st.session_state:
    st.error("Dados não carregados.")
    st.stop()

#- DataFrame
passo_diario = st.session_state['passo_diario']
cota_vazao = st.session_state['cota_vazao']
cotas2L = st.session_state['cotas2L']
medicoes = st.session_state['medicoes']

#- Chama a função que retorna o dataframe já filtrado
df_cv_filtrado, df_pd_filtrado, df_c2l_filtrado, df_medicoes_filtrado = fc.menu_filtros_multi([cota_vazao, passo_diario, cotas2L, medicoes])

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
# if df_pd_filtrado.empty or df_cv_filtrado.empty:
#     st.stop()
#- Modificado: O script só deve parar se os dados de Cota/Vazão (referência do gráfico) sumirem por completo.
if df_cv_filtrado.empty:
    st.warning("⚠️ O DataFrame de cota e vazão está vazio para este filtro. Selecione outros parâmetros.")
    st.stop()

#- Aplicação do filtro no DataFrame da página usando o que a função retornou
exibe_passo_diario = df_pd_filtrado.copy()
exibe_cota_vazao = df_cv_filtrado.copy()
exibe_cotas2L = df_c2l_filtrado.copy()
exibe_medicoes = df_medicoes_filtrado.copy()

# < ------------------------------------------------------------------------------------------------------------------------------
def adicionar_data_hora(df):
    """
    Adiciona a coluna 'Data_Hora' como datetime, 
    definindo o horário fixo de 12:00 com base na coluna 'Data'.
    """
    # .dt.normalize() garante que a data base comece em 00:00:00
    # pd.Timedelta(hours=12) adiciona exatamente 12 horas
    df['Data_Hora'] = df['Data'].dt.normalize() + pd.Timedelta(hours=12)
    return df

# < ------------------------------------------------------------------------------------------------------------------------------
#- Inclui a coluna 'Data_Hora'
exibe_cota_vazao = adicionar_data_hora(exibe_cota_vazao)
exibe_medicoes = adicionar_data_hora(exibe_medicoes)

# < ------------------------------------------------------------------------------------------------------------------------------
#$ GRÁFICO DE SÉRIE TEMPORAL - COTA VS DATA (usando df_cv_filtrado)

#- Verifica quantas estações únicas estão selecionadas no filtro
estacoes_selecionadas = exibe_cota_vazao['Nome'].nunique()

#- Só exibe o gráfico se houver no máximo 3 estações
if estacoes_selecionadas <= 3 and estacoes_selecionadas > 0:
    st.subheader("📈 Cota vs Tempo")
    
    #- Checkbox para controlar a exibição das cotas de 2 leituras
    mostrar_cotas2L = st.checkbox("📊 Mostrar Cota 2 Leituras", value=True)
    
    #- Prepara os dados para o gráfico
    df_grafico_cv = exibe_cota_vazao.copy()
    df_grafico_cv = df_grafico_cv.sort_values('Data_Hora')
    
    #- Cria o gráfico base com plotly.graph_objects para melhor controle
    fig = go.Figure()
    
    #- Obtém as estações únicas para criar séries separadas
    estacoes = df_grafico_cv['Nome'].unique()
    
    #- Cores para as estações (paleta de cores padrão)
    cores = px.colors.qualitative.Plotly
    
    #- Adiciona as séries de Cota Média (linha com marcadores)
    for i, estacao in enumerate(estacoes):
        df_estacao = df_grafico_cv[df_grafico_cv['Nome'] == estacao]
        cor = cores[i % len(cores)]
        
        fig.add_trace(go.Scatter(
            x=df_estacao['Data_Hora'],
            y=df_estacao['Cota'],
            mode='lines',
            name=f'Cota Média - {estacao}',
            line=dict(color=cor, width=2),
            marker=dict(size=6, color=cor),
            legendgroup=f'media_{estacao}',
            hovertemplate='<b>%{text}</b><br>' +
                         'Data: %{x|%d/%m/%Y}<br>' +
                         'Cota Média: %{y:.0f} cm<br>' +
                         '<extra></extra>',
            text=[estacao] * len(df_estacao)
        ))
    
    # Adiciona Cota 2 Leituras (apenas pontos) se o checkbox estiver marcado e houver dados
    if mostrar_cotas2L and not exibe_cotas2L.empty:
        df_grafico_c2l = exibe_cotas2L.copy()
        df_grafico_c2l = df_grafico_c2l.sort_values('Data_Hora')
        
        # Para cada estação, adiciona os pontos de Cota 2 Leituras
        for i, estacao in enumerate(estacoes):
            df_estacao_c2l = df_grafico_c2l[df_grafico_c2l['Nome'] == estacao]
            
            if not df_estacao_c2l.empty:
                cor = cores[i % len(cores)]
                
                fig.add_trace(go.Scatter(
                    x=df_estacao_c2l['Data_Hora'],
                    y=df_estacao_c2l['Cota'],
                    mode='markers',
                    name=f'Cota 2 Leituras - {estacao}',
                    marker=dict(
                        size=4,
                        color=cor,
                        symbol='circle',
                    ),
                    legendgroup=f'c2l_{estacao}',
                    hovertemplate='<b>%{text}</b><br>' +
                                 'Data: %{x|%d/%m/%Y %H:%M}<br>' +
                                 'Cota 2L: %{y:.0f} cm<br>' +
                                 '<extra></extra>',
                    text=[estacao] * len(df_estacao_c2l),
                    showlegend=True
                ))
    
    #- Adiciona Medições (apenas pontos) se houver dados
    if not exibe_medicoes.empty:
        df_grafico_med = exibe_medicoes.copy()
        df_grafico_med = df_grafico_med.sort_values('Data_Hora')
        
        #- Para cada estação, adiciona os pontos de Medições
        for i, estacao in enumerate(estacoes):
            df_estacao_med = df_grafico_med[df_grafico_med['Nome'] == estacao]
            
            if not df_estacao_med.empty:
                cor = cores[i % len(cores)]
                
                fig.add_trace(go.Scatter(
                    x=df_estacao_med['Data_Hora'],
                    y=df_estacao_med['Cota'],
                    mode='markers',
                    name=f'Medições - {estacao}',
                    # https://stackoverflow.com/questions/66257042/getting-list-of-all-available-marker-shapes-in-plotly
                    marker=dict(
                        size=10,
                        color=cor,
                        symbol='circle-dot',
                        line=dict(width=2, color='red')  # contorno do marcador
                    ),
                    legendgroup=f'med_{estacao}',
                    hovertemplate='<b>%{text}</b><br>' +
                                 'Data: %{x|%d/%m/%Y}<br>' +
                                 'Medição: %{y:.0f} cm<br>' +
                                 '<extra></extra>',
                    text=[estacao] * len(df_estacao_med),
                    showlegend=True
                ))
    
    #- Personaliza o layout do gráfico
    fig.update_layout(
        title='Evolução da Cota ao Longo do Tempo',
        xaxis_title='Data',
        yaxis_title='Cota (cm)',
        legend_title='Legenda',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.00,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="Black",
            borderwidth=1
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    #- Formata o eixo X para mostrar datas de forma legível
    fig.update_xaxes(
        tickformat='%d/%m/%Y',
        tickangle=45
    )
    
    #- Exibe o gráfico
    st.plotly_chart(fig, width='stretch')
    
    #- Informação adicional
    info_text = f"📊 Gráfico 'Cota média' com {estacoes_selecionadas} estação(ões) selecionada(s)"
    
    if mostrar_cotas2L and not exibe_cotas2L.empty:
        info_text += " | Cota 2 Leituras"
    elif mostrar_cotas2L and exibe_cotas2L.empty:
        info_text += " | ⚠️ Sem dados de Cota 2 Leituras para o filtro atual"
    
    if not exibe_medicoes.empty:
        info_text += " | ⭕ Medições"
    else:
        info_text += " | ⚠️ Sem dados de Medições para o filtro atual"
    
    st.caption(info_text)
    
    st.markdown("---")  # Linha separadora

else:
    #- Mensagem quando há mais de 3 estações selecionadas
    if estacoes_selecionadas > 3:
        st.info(f"ℹ️ Para visualizar o gráfico, selecione no máximo 3 estações. Atualmente: {estacoes_selecionadas} estações")
        st.markdown("---")  # Linha separadora

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Exibe o DataFrame resultante (Tabela auxiliar)
#- Título da tabela
st.subheader("📋 Descontinuidade no passo das cotas e vazões")

#- Descrição do DataFrame exibido
if exibe_passo_diario.empty:
    st.info("💡 Não existem dados de descontiuidade no passo diário para o período/filtro selecionado.")
else:
    st.markdown("Filtros ativos para diferenças percentuais acima de de 50% (e absolutas maiores que 10).")
    st.markdown(f"**Número de registros:** {len(exibe_passo_diario)}")
    st.markdown("<br>", unsafe_allow_html=True) #- quebra de linha usando HTML para espaçamento

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Limite de segurança para exibição com formatação condicional
#- Limite de segurança para a exibição das linhas com formatação condicional (Styler)
LIMITE_ESTILO = 1000
total_linhas = len(exibe_passo_diario)

#- Se for maior que o limite, pegamos apenas o topo para o Styler não quebrar
if total_linhas > LIMITE_ESTILO:
    df_para_estilizar = exibe_passo_diario.head(LIMITE_ESTILO)
    aviso_limite = f"⚠️ Exibindo as primeiras {LIMITE_ESTILO} linhas. Use os filtros para ver mais dados."
else:
    df_para_estilizar = exibe_passo_diario
    aviso_limite = None

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Formatação do DataFrame exibido
#- Função para definir a cor do texto baseada no valor
def colorir_desvio(valor):
    try:
        # Se o desvio (em módulo) for maior que 50%, pinta de vermelho
        cor = 'red' if abs(valor) > 50 else 'black'
        return f'color: {cor}'
    except:
        return 'color: black'

#- Formatação Brasileira via Pandas Styler e o estilo condicional
#< Isso mantém os dados como números (para ordenar), mas exibe com vírgula e ponto
df_estilizado = df_para_estilizar.style.format({
    'Vazao': "{:.1f}",
    'Vazao_Anterior': "{:.1f}",
    'Diferença_vazao': "{:.1f}",
    'DifPer_vazao': "{:.1f}",
    'DifPer_cota': "{:.1f}",
}, decimal=',', thousands='.') \
.map(colorir_desvio, subset=['DifPer_cota','DifPer_vazao']) # <--- Aplica a cor apenas na coluna

# < ------------------------------------------------------------------------------------------------------------------------------

#- Exibe o DataFrame ocultando o índice e usando a largura total do contêiner
st.dataframe(
    df_estilizado,
    hide_index=True,
    width="stretch",
    column_config={
        "UR": st.column_config.Column("UR", 
                                      help="Unidade Regional"),
        "Codigo": st.column_config.NumberColumn("Código", format="%d", 
                                                help="Código da estação."),
        "Nome": st.column_config.Column("Nome", help="Nome da estação"),
        "Data": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY", 
                                                help="Data da leitura."),
        "Status": st.column_config.Column("Status Cota", 
                                          help="Classificação da cota do dia."),
        "Cota": st.column_config.NumberColumn("Cota (cm)", format="%d", 
                                              help="Cota lida."),
        "Cota_Anterior": st.column_config.NumberColumn("Cota Anterior (cm)", format="%d", 
            help="Cota lida do dia anterior"),
        "Vazao": st.column_config.NumberColumn("Vazão (m³/s)", 
            help="Vazão presente no banco SQL."),
        "Vazao_Anterior": st.column_config.NumberColumn("Vazão Anterior (m³/s)", 
            help="Vazão do dia anterior presente no banco SQL."),
        "Diferença_vazao": st.column_config.NumberColumn("Diferença Vazao (m³/s)", 
            help="Diferença de vazão entre o dia analisado e o dia anterior"), 
        "DifPer_vazao": st.column_config.NumberColumn("Diferença Vazao (%)", 
            help="Diferença percentual entre a vazão do dia analisado e a do dia anterior"), 
        "DifPer_cota": st.column_config.NumberColumn("Diferença Cota (%)", 
            help="Diferença percentual entre a cota do dia analisado e a do dia anterior"), 
        "Diferença_cota": st.column_config.NumberColumn("Diferença Cota (cm)", format="%d", 
            help="Diferença de cota entre o dia analisado e o dia anterior"),
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