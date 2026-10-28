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
import numpy as np
import plotly.graph_objects as go
import funcoes as fc

# < ------------------------------------------------------------------------------------------------------------------------------
#- Configurações iniciais da página
fc.configuracoes_iniciais()

#- Título e descrição da página
st.subheader("Desvio das medições em relação à curva-chave que está no banco SQL")
st.markdown(""" 
             :yellow[✍️Atenção]: medições com desvio superior a 20% estão destacadas em vermelho.
             """)
st.divider() # Linha visual para separar das tabelas

#- Carrega os dados necessários para essa página
fc.gerenciar_pagina_e_carregar("03_Medicoes", ["medicoes", "curvas"])

#- Verifica se os dados foram carregados na página principal, caso contrário, exibe uma mensagem de erro e interrompe a execução.
if 'medicoes' not in st.session_state or 'curvas' not in st.session_state:
    st.error("Dados não carregados.")
    st.stop()

#- DataFrame medicoes e curvas
medicoes = st.session_state['medicoes']
curvas = st.session_state['curvas']

# --- 1. FILTRO GLOBAL ---
#- Chama a função que retorna o dataframe já filtrado
df_med_filtrado, df_curvas_filtrado = fc.menu_filtros_multi([medicoes, curvas])

# < ------------------------------------------------------------------------------------------------------------------------------
# --- BLOCO DE FILTROS DE AVANÇADOS ---
with st.expander("🔍 Filtros Avançados"):
    st.markdown(":gray[Selecione 'Intervalo' para ativar os filtros por coluna.]")
    
    if not df_med_filtrado.empty:
        # Coluna 1
        c_filtros_1, c_filtros_2 = st.columns(2)
        
        with c_filtros_1:
            # Cada chamada "lapida" o df_med_filtrado (recursividade)
            df_med_filtrado = fc.filtro_numerico(df_med_filtrado, 'Cota', 'Cota (cm)')
            st.divider() # Pequena linha separadora entre os filtros
            df_med_filtrado = fc.filtro_numerico(df_med_filtrado, 'Vazao', 'Vazão (m³/s)')
            st.divider() # Pequena linha separadora entre os filtros
            df_med_filtrado = fc.filtro_numerico(df_med_filtrado, 'Qcalc', 'QCalc (m³/s)')
            st.divider() # Pequena linha separadora entre os filtros
            df_med_filtrado = fc.filtro_numerico(df_med_filtrado, 'Desvio', 'Desvio (%)')
            
        with c_filtros_2:
            df_med_filtrado = fc.filtro_numerico(df_med_filtrado, 'AreaMolh', 'AreaMolh (m²)')
            st.divider()
            df_med_filtrado = fc.filtro_numerico(df_med_filtrado, 'Largura', 'Largura (m)')
            st.divider()
            df_med_filtrado = fc.filtro_numerico(df_med_filtrado, 'VelMedia', 'VelMedia (m/s)')
            st.divider()
            df_med_filtrado = fc.filtro_numerico(df_med_filtrado, 'Prof', 'Prof (m)')

# < ------------------------------------------------------------------------------------------------------------------------------
# --- 2. APLICAÇÃO DOS FILTROS NA CURVA (ESTAÇÃO + TEMPO) ---
ur_sel = st.session_state.filtro_ur
estacoes_sel = st.session_state.filtro_cod
anos_sel = st.session_state.filtro_ano
meses_sel = st.session_state.filtro_mes

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Botões para limpar filtros e exibir resultado

c_btn1, _, c_btn2 = st.columns([1, 3, 2]) # Ajustado o espaçamento para acomodar o checkbox de ordenação

# --- Botão para limpar todos os filtros ---
c_btn1.button("Limpar Filtros",             # legenda do botão
              on_click=fc.limpar_filtros,   # função a ser chamada quando o botão for clicado
              width='content',              # faz o botão ocupar toda a largura da coluna
              type= "secondary")            # estilo do botão (opcional)

# < ------------------------------------------------------------------------------------------------------------------------------
#- Se o DF estiver vazio, paramos a execução aqui para não dar erro nas métricas abaixo
if df_med_filtrado.empty:
    st.stop()

#- Aplicação do filtro no DataFrame da página usando o que a função retornou
exibe_medicoes = df_med_filtrado.copy()

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

# REQUISITO 3: Substituição do botão por Checkbox para manter o estado da ordenação estável
ordenar_desvio = c_btn2.checkbox("🔥 Ordenar por Maior Desvio", value=False)

if ordenar_desvio:
    exibe_medicoes = exibe_medicoes.sort_values(by='Desvio_Abs', ascending=False)
else:
    # Ordem padrão (geralmente por data ou como vier do banco)
    exibe_medicoes = exibe_medicoes.sort_values(by='Data', ascending=False)

#- Remove a coluna temporária para não poluir a tabela final
exibe_medicoes = exibe_medicoes.drop(columns=['Desvio_Abs'])

# < ------------------------------------------------------------------------------------------------------------------------------
# --- BLOCO DE MÉTRICAS --- 

if not exibe_medicoes.empty:
    # 1. Injeta CSS para reduzir as margens das colunas e das métricas
    st.markdown(
        """
        <style>
            /* Reduz a margem superior e inferior do bloco de colunas */
            [data-testid="stHorizontalBlock"] {
                margin-top: -10px !important;
                margin-bottom: -10px !important;
                gap: 0px !important;
            }
            /* Reduz o espaçamento interno (padding) das métricas */
            [data-testid="stMetric"] {
                padding-top: 0px !important;
                padding-bottom: 0px !important;
            }
            /* Ajusta o espaçamento do título do Resumo */
            .resumo-title {
                margin-bottom: -5px !important;
                margin-top: 0px !important;
            }
            /* 2. Redução do Tamanho da Fonte dos Metric Cards */
            
            /* Diminui o Título (Ex: "Total de Registros") */
            [data-testid="stMetricLabel"] p {
                font-size: 0.85rem !important; /* Ajuste este valor como preferir */
            }
            
            /* Diminui o Valor Principal (Ex: "150") */
            [data-testid="stMetricValue"] {
                font-size: 1.6rem !important;  /* Padrão do Streamlit costuma ser bem maior */
            }

            /* Opcional: Se usar variação de delta (setinhas de alta/baixa) */
            [data-testid="stMetricDelta"] {
                font-size: 0.8rem !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 2. Divisor customizado com menos espaço (substituindo o st.divider())
    st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)

    # Título usando HTML para podermos controlar a margem exata via CSS acima
    st.markdown("<h5 class='resumo-title'>Resumo</h3>", unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    
    #- Cálculos
    desvio_medio = exibe_medicoes['Desvio'].mean()
    maior_erro = exibe_medicoes['Desvio'].abs().max()
    qtd_critica = len(exibe_medicoes[exibe_medicoes['Desvio'].abs() > 20])

    #- Exibição dos Metric Cards
    m1.metric("Total de Registros", f"{len(exibe_medicoes)}")
    m2.metric("Desvio Médio", f"{desvio_medio:.2f}")
    m3.metric("Maior Desvio Encontrado", f"{maior_erro:.2f}")
    m4.metric("Alertas (> 20%)", f"{qtd_critica} registros")
    
    # Segundo divisor customizado compacto
    st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)

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
    'Vazao': "{:.3f}",
    'AreaMolh': "{:.2f}",
    'VelMedia': "{:.2f}",
    'Largura': "{:.2f}",
    'Prof': "{:.2f}",
    'Qcalc': "{:.3f}",
    'Desvio': "{:.2f}",
}, decimal=',', thousands='.') \
.map(colorir_desvio, subset=['Desvio']) # <--- Aplica a cor apenas na coluna Desvio

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Exibe o DataFrame resultante com a formatação applied

#- Exibe o DataFrame ocultando o índice e usando a largura total do contêiner
with st.expander("Medições de Descarga Líquida (Vigência filtrada)"):
    st.dataframe(
        df_estilizado,
        hide_index=True,
        width="stretch",
        column_config={
            "UR": st.column_config.Column("UR", help="Unidade Regional"),
            "Codigo": st.column_config.NumberColumn("Código", format="%d", 
                                                    help="Código da estação"),
            "Nome": st.column_config.Column("Nome", 
                                            help="Nome da estação"),
            "Data": st.column_config.DatetimeColumn(
                "Data", format="DD/MM/YYYY", 
                help="Data da medição"),
            "NumMed": st.column_config.NumberColumn(
                "Nº Medição", format="%d",
                help="Número da medição de descarga"
                ),
            "Cota": st.column_config.NumberColumn(
                "Cota (cm)", format="%d",
                help="Nível d'água observado no momento da medição"
                ),
            "Vazao": st.column_config.NumberColumn(
                "Vazão (m³/s)", 
                help="Vazão medida em campo."
                ),
            "AreaMolh": st.column_config.NumberColumn(
                "Área Molh (m²)", 
                help="Área Molhada da seção de medição"
            ),
            "Largura": st.column_config.NumberColumn(
                "Largura (m)", 
                help="Profundidade da seção de medição"
            ),
            "VelMedia": st.column_config.NumberColumn(
                "VelMédia (m/s)", 
                help="Vel. Média da água (m/s)"
            ),
            "Prof": st.column_config.NumberColumn(
                "Prof (m)", 
                help="Profundidade da seção de medição"
            ),
            "Qcalc": st.column_config.NumberColumn(
                "QCalc (m³/s)", 
                help="Vazão calculada através da equação da curva chave vigente para a cota lida"
            ),
            "Desvio": st.column_config.NumberColumn("Desvio (%)", 
                help="Diferença entre vazão calculada pela curva chave (Qcalc) e a vazão que está no banco SQL" 
                ),
            "Curva": st.column_config.NumberColumn(
                "Nº Curva", format="%d", 
                help="Numeração da curva chave associada a esta estação"
            ),
            "ValidadeInicio": st.column_config.DatetimeColumn(
                "Validade Início", format="DD/MM/YYYY",
                help="Início da validade da curva chave"
                ),
            "ValidadeFim": st.column_config.DatetimeColumn(
                "Validade Fim", format="DD/MM/YYYY",
                help="Fim da validade da curva chave"
                ),

            "Lim_inf": st.column_config.NumberColumn(
                "Limite Inf. (cm)", format="%d", 
                help="Limite inferior da curva chave"
                ),
            "Lim_sup": st.column_config.NumberColumn(
                "Limite Sup. (cm)", format="%d", 
                help="Limite superior da curva chave"
                ),
            "medidorvazao": st.column_config.NumberColumn("Medidor Vazão", format="%d", 
                help="Equipamento usado para a medição de descarga"),
        }
    )

#- Exibição de Alerta
if aviso_limite:
    st.info(aviso_limite)

# < ------------------------------------------------------------------------------------------------------------------------------
# --- LOGICA DE TRAVA (APENAS UMA ESTAÇÃO) ---
if not estacoes_sel:
    st.warning("⚠️ Selecione **uma Estação** no filtro acima para visualizar o gráfico.")
    st.stop()

if len(estacoes_sel) > 1:
    st.error(f"❌ Você selecionou {len(estacoes_sel)} estações. Por favor, selecione **apenas uma** para analisar a Curva Chave.")
    st.stop()

# < ------------------------------------------------------------------------------------------------------------------------------
# $ Lógica do Gráfico

# --- 3. GERAÇÃO DA LINHA DA CURVA ---
def gerar_pontos_curva(df_curvas):
    pontos = []
    df_curvas = df_curvas.sort_values(['Curva', 'TramoCotaMin'])
    
    for _, tramo in df_curvas.iterrows():
        h_range = np.linspace(tramo['TramoCotaMin'], tramo['TramoCotaMax'], 100)
        q_calc = tramo['CoefA'] * ((np.maximum(h_range/100 - tramo['CoefH0'], 0.001)) ** tramo['CoefN'])
        
        df_t = pd.DataFrame({'Cota': h_range, 'Vazao': q_calc})
        df_t['Curva'] = tramo['Curva']
        pontos.append(df_t)
    
    return pd.concat(pontos) if pontos else pd.DataFrame()

# Dicionário auxiliar para mapear e desenhar as legendas das cores de forma idêntica nos dois gráficos
config_legendas = [
    {"nome": "Desvio < |10%|", "cor": "blue"},
    {"nome": "Desvio |10%| a |20%|", "cor": "yellow"},
    {"nome": "Desvio |20%| a |30%|", "cor": "orange"},
    {"nome": "Desvio > |30%|", "cor": "red"}
]

# --- 4. CONSTRUÇÃO DO PLOTLY (COTA VS VAZÃO) ---

#- Checkboxes para alternar as escalas logarítmicas
st.markdown("### Configurações de Escala do Gráfico Cota vs Vazão")
col_log1, col_log2 = st.columns(2)
with col_log1:
    log_cota = st.checkbox("Log Cota (Eixo Y)")
with col_log2:
    log_vazao = st.checkbox("Log Vazão (Eixo X)")

#- Criando a lista de cores
cores_cota_vazao = []
for desvio in df_med_filtrado['Desvio']:
    mod_desvio = abs(desvio)
    if mod_desvio < 10:
        cores_cota_vazao.append('blue')
    elif 10 <= mod_desvio <= 20:
        cores_cota_vazao.append('yellow')
    elif mod_desvio > 30:
        cores_cota_vazao.append('red')
    else:
        cores_cota_vazao.append('orange')


fig = go.Figure()

#- Medições (Cota vs Vazão)
if not df_med_filtrado.empty:
    fig.add_trace(go.Scatter(
        x=df_med_filtrado['Vazao'],
        y=df_med_filtrado['Cota'],
        mode='markers',
        name='Medições',
        legendgroup="medicoes",     # Agrupa o rastro principal
        showlegend=False,           # Oculta o rastro bruto para usar os itens da legenda colorida
        marker=dict(
            size=10, 
            color=cores_cota_vazao,  # <--- Aplicando as cores corretas para esta ordenação
            line=dict(width=1, color='black')  # Borda preta ajuda a enxergar pontos amarelos
        ),
        text=df_med_filtrado['Data'],
        customdata=df_med_filtrado['Desvio'],
        hovertemplate="<b>Data:</b> %{text}<br><b>Vazão:</b> %{x:.2f}<br><b>Cota:</b> %{y:.0f}<br><b>Desvio:</b> %{customdata:.1f}%<extra></extra>"
    ))

    #- Adiciona as legendas das faixas de desvio no gráfico de Cota vs Vazão
    for item in config_legendas:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],     # Pontos invisíveis (não aparecem no gráfico)
            mode='markers',
            name=item["nome"],
            marker=dict(size=10, color=item["cor"], line=dict(width=1, color='black')),
            legendgroup="medicoes",
            showlegend=True
        ))

#- Linhas das Curvas
if not df_curvas_filtrado.empty:
    df_linhas = gerar_pontos_curva(df_curvas_filtrado)
    for num in df_linhas['Curva'].unique():
        df_c = df_linhas[df_linhas['Curva'] == num]
        fig.add_trace(go.Scatter(
            x=df_c['Vazao'], y=df_c['Cota'],
            mode='lines', name=f'Curva {num}',
            line=dict(width=3)
        ))

#- Estilização e definição de escalas dinâmicas
mapa_nomes = st.session_state['medicoes'].drop_duplicates('Codigo').set_index('Codigo')['Nome'].to_dict()
nome_estacao = mapa_nomes.get(estacoes_sel[0], "Não encontrada")

#- Define dinamicamente o tipo dos eixos com base nos checkboxes do Requisito 2
tipo_eixo_x = "log" if log_vazao else "linear"
tipo_eixo_y = "log" if log_cota else "linear"

fig.update_layout(
    title={
        'text': f"Medições de descarga x Curva chave<br><sup>Estação: {estacoes_sel[0]} - {nome_estacao}</sup>",
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    xaxis_title="Vazão (m³/s)" if not log_vazao else "Log Vazão (m³/s)", 
    yaxis_title="Cota (cm)" if not log_cota else "Log Cota (cm)",
    xaxis=dict(type=tipo_eixo_x),
    yaxis=dict(type=tipo_eixo_y),
    height=600, 
    template="plotly_white",
    hovermode="closest",
    legend=dict(title_text="<b>Legenda</b>") # Título do bloco da legenda
)

st.plotly_chart(fig, width='stretch')


# --- REQUISITO 1: GRÁFICO DE DESVIO PERCENTUAL AO LONGO DO TEMPO ---
st.divider()
fig_desvio = go.Figure()

if not df_med_filtrado.empty:
    # Garante ordenação cronológica estrita apenas para a plotagem da linha temporal
    df_desvio_temporal = df_med_filtrado.sort_values(by='Data')
    
    # Geramos a lista de cores baseada estritamente no DataFrame já ordenado!
    cores_desvio_temporal = []
    for desvio in df_desvio_temporal['Desvio']:
        mod_desvio = abs(desvio)
        if mod_desvio < 10:
            cores_desvio_temporal.append('blue')
        elif 10 <= mod_desvio <= 20:
            cores_desvio_temporal.append('yellow')
        elif mod_desvio > 30:
            cores_desvio_temporal.append('red')
        else:
            cores_desvio_temporal.append('orange')

    # Adiciona linha de dispersão dos desvios ao longo do tempo
    fig_desvio.add_trace(go.Scatter(
        x=df_desvio_temporal['Data'],
        y=df_desvio_temporal['Desvio'],
        mode='markers',
        name='Desvio Mensurado',
        showlegend=False,           # Oculta o rastro bruto para usar os itens da legenda colorida
        marker=dict(
            size=10,
            color=cores_desvio_temporal,  # <--- Agora a correspondência linha/cor está 100% correta
            line=dict(width=1, color='black')
        ),
        text=df_desvio_temporal['Cota'],
        customdata=df_desvio_temporal['Vazao'],
        hovertemplate="<b>Data:</b> %{x|%Y-%m-%d}<br><b>Desvio:</b> %{y:.2f}%<br><b>Cota:</b> %{text:.0f} cm<br><b>Vazão:</b> %{customdata:.2f} m³/s<extra></extra>"
    ))

    # Adiciona as legendas das faixas de desvio no gráfico Temporal
    for item in config_legendas:
        fig_desvio.add_trace(go.Scatter(
            x=[None], y=[None],     # Pontos invisíveis
            mode='markers',
            name=item["nome"],
            marker=dict(size=10, color=item["cor"], line=dict(width=1, color='black')),
            showlegend=True
        ))
    
    #- 4. Configuração dos Eixos 
    fig_desvio.update_xaxes(
        tickangle=45,
        title_text="Data",
        title_font={"size": 20},
        title_standoff=25,
        tickformat="%Y",
        dtick="M12",  # Intervalo de 1 ano (12 meses)
        showgrid=True,
    )

    fig_desvio.update_yaxes(
        tickangle=0,
        title_text="Desvio(%)",
        title_font={"size": 20},
        title_standoff=25,
        #- 1. Linha do ZERO super destacada
        zeroline=True,
        zerolinecolor="black",
        zerolinewidth=1.0,
        #- 2. Grade Principal (de 10 em 10) - Mais escura
        dtick=10,
        showgrid=True,
        gridcolor="rgba(120, 120, 120, 0.6)",  # Cinza intermediário/escuro
        gridwidth=1.2,
        #- 3. Grade Secundária (de 5 em 5) - Mais clara
        minor=dict(
            dtick=5,
            showgrid=True,
            gridcolor="rgba(220, 220, 220, 0.4)",  # Cinza bem suave
            gridwidth=0.8,
        ),
    )

fig_desvio.update_layout(
    title={
        'text': f"Evolução do Desvio Percentual ao Longo do Tempo<br><sup>Estação: {estacoes_sel[0]} - {nome_estacao}</sup>",
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    xaxis_title="Data da Medição",
    yaxis_title="Desvio (%)",
    height=500,
    hovermode="closest"
)

st.plotly_chart(fig_desvio, width='stretch')


#- Tabela de conferência com Tooltips
# with st.expander("Parâmetros das Curvas (Vigência filtrada)"):
st.markdown("Parâmetros das Curvas da Estação selecionada")
st.dataframe(
    df_curvas_filtrado[['Curva', 'ValidadeInicio', 'ValidadeFim', 'Tramo', 'TramoCotaMax', 'TramoCotaMin', 'CoefA', 'CoefH0', 'CoefN']], 
    hide_index=True,
    column_config={
        "Curva": st.column_config.TextColumn("Curva", help="Número de identificação da curva chave."),
        "ValidadeInicio": st.column_config.DateColumn("Início", help="Data de início da vigência da curva."),
        "ValidadeFim": st.column_config.DateColumn("Fim", help="Data de término da vigência da curva."),
        "Tramo": st.column_config.NumberColumn("Tramo", help="Segmento da curva."),
        "TramoCotaMax": st.column_config.NumberColumn("Cota Máx. (cm)", help="Cota máxima do tramo."),
        "TramoCotaMin": st.column_config.NumberColumn("Cota Mín. (cm)", help="Cota mínima do tramo."),
        "CoefA": st.column_config.NumberColumn("Cof. A", help="Coeficiente de escala da equação Q = A * (H - H0)^N."),
        "CoefH0": st.column_config.NumberColumn("Cof. H0", help="Cota de vazão nula (cm)."),
        "CoefN": st.column_config.NumberColumn("Cof. N", help="Expoente da equação (declividade da curva no papel logarítmico)."),
    }
)


