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
#$ Configurações iniciais
fc.configuracoes_iniciais()

#- Título e descrição da página
st.subheader("Medição e desvio em relação à curva-chave que está no banco SQL")

#- Verifica se os dados foram carregados na página principal, caso contrário, exibe uma mensagem de erro e interrompe a execução.
# if 'medicoes' not in st.session_state:
if 'medicoes' not in st.session_state or 'curvas' not in st.session_state:
    st.error("Dados não carregados.")
    st.stop()

#- DataFrame medicoes
medicoes = st.session_state['medicoes']

# --- 1. FILTRO GLOBAL ---
#- Chama a função que retorna o dataframe já filtrado
df_med_filtrado = fc.menu_filtros_multi(medicoes)

# < ------------------------------------------------------------------------------------------------------------------------------
# --- 2. APLICAÇÃO DOS FILTROS NA CURVA (ESTAÇÃO + TEMPO) ---
estacoes_sel = st.session_state.filtro_cod
anos_sel = st.session_state.filtro_ano
meses_sel = st.session_state.filtro_mes

df_curvas_filtrado = st.session_state['curvas'].copy()

# Filtro por Estação
if estacoes_sel:
    df_curvas_filtrado = df_curvas_filtrado[df_curvas_filtrado['Codigo'].isin(estacoes_sel)]

# --- CORREÇÃO DA LÓGICA DE INTERVALO (ANOS) ---
if anos_sel:
    # Pegamos o menor e o maior ano selecionados no multiselect
    ano_min_user = min(anos_sel)
    ano_max_user = max(anos_sel)
    
    # Lógica de Interseção:
    # A curva é válida se começou ANTES ou DURANTE o último ano filtrado
    # E se terminou DEPOIS ou DURANTE o primeiro ano filtrado
    mask_ano = (df_curvas_filtrado['ValidadeInicio'].dt.year <= ano_max_user) & \
               (df_curvas_filtrado['ValidadeFim'].dt.year >= ano_min_user)
    
    df_curvas_filtrado = df_curvas_filtrado[mask_ano]

# --- CORREÇÃO DA LÓGICA DE INTERVALO (MESES) ---
if meses_sel:
    # Para meses, se quisermos ser rigorosos na interseção dentro do ano:
    mes_min_user = min(meses_sel)
    mes_max_user = max(meses_sel)
    
    # A curva deve ter algum mês de validade que se sobreponha ao range de meses selecionado
    mask_mes = (df_curvas_filtrado['ValidadeInicio'].dt.month <= mes_max_user) & \
               (df_curvas_filtrado['ValidadeFim'].dt.month >= mes_min_user)
    
    df_curvas_filtrado = df_curvas_filtrado[mask_mes]

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
    m2.metric("Desvio Médio", f"{desvio_medio:.2f}")
    m3.metric("Maior Desvio Encontrado", f"{maior_erro:.2f}")
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
    'Vazao': "{:.3f}",
    'AreaMolh': "{:.3f}",
    'Largura': "{:.3f}",
    'Prof': "{:.3f}",
    'Qcalc': "{:.3f}",
    'Desvio': "{:.2f}",
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
        "UR": st.column_config.Column("UR", help="Unidade Regional"),
        "Codigo": st.column_config.NumberColumn("Código", format="%d", 
                                                help="Código da estação."),
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
            help="Nível d'água observado no momento da medição."
            ),
        "Vazao": st.column_config.NumberColumn(
            "Vazão (m³/s)", 
            help="Vazão medida em campo."
            ),
        "Qcalc": st.column_config.NumberColumn(
            "QCalc (m³/s)", 
            help="Vazão calculada através da equação da curva chave vigente para a cota lida."
        ),
        "Desvio": st.column_config.NumberColumn("Desvio (m³/s)", 
            help="Diferença entre vazão calculada pela curva chave (Qcalc) e a vazão que está no banco SQL." 
            ),
        "Curva": st.column_config.NumberColumn(
            "Nº Curva", format="%d", 
            help="Numeração da curva chave associada a esta estação."
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
        "Ano": st.column_config.NumberColumn("Ano", format="%d", 
                                             help="Ano da leitura"),
        "Mes": st.column_config.NumberColumn("Mês", format="%d", 
                                             help="Mês da leitura"),
        # Notas: Quando usamos .style.format, o 'format' do column_config 
        # pode ser omitido para as colunas numéricas estilizadas.
        # Datas formatadas (O Styler não mexe nestas se não estiverem no .format)

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
    st.error(f"❌ Você selecionou {len(estacoes_sel)} estações. Por favor, selecione **apenas uma** para analisar a Curva-Chave.")
    # st.info("💡 O gráfico de Curva-Chave requer uma análise individual por seção do rio.")
    st.stop()

# < ------------------------------------------------------------------------------------------------------------------------------
# $ Lógica do Gráfico

# --- 3. GERAÇÃO DA LINHA DA CURVA ---
def gerar_pontos_curva(df_curvas):
    pontos = []
    # Ordenar por curva e tramo para a linha não "saltar" no gráfico
    df_curvas = df_curvas.sort_values(['Curva', 'TramoCotaMin'])
    
    for _, tramo in df_curvas.iterrows():
        # Gerar 100 pontos entre o mínimo e máximo do tramo
        h_range = np.linspace(tramo['TramoCotaMin'], tramo['TramoCotaMax'], 100)
        
        # Fórmula: Q = A * (H/100 - H0)^N
        # np.maximum evita erros matemáticos se H/100 < H0
        q_calc = tramo['CoefA'] * ((np.maximum(h_range/100 - tramo['CoefH0'], 0.001)) ** tramo['CoefN'])
        
        df_t = pd.DataFrame({'Cota': h_range, 'Vazao': q_calc})
        df_t['Curva'] = tramo['Curva']
        pontos.append(df_t)
    
    return pd.concat(pontos) if pontos else pd.DataFrame()

# --- 4. CONSTRUÇÃO DO PLOTLY ---
fig = go.Figure()

# Medições
if not df_med_filtrado.empty:
    fig.add_trace(go.Scatter(
        x=df_med_filtrado['Vazao'],
        y=df_med_filtrado['Cota'],
        mode='markers',
        name='Medições',
        marker=dict(
            size=10, color=df_med_filtrado['Desvio'].abs(),
            colorscale='Viridis', showscale=True,
            colorbar=dict(title="Desvio %", x=1.1)
        ),
        text=df_med_filtrado['Data'],
        customdata=df_med_filtrado['Desvio'],
        hovertemplate="<b>Data:</b> %{text}<br><b>Vazão:</b> %{x:.2f}<br><b>Cota:</b> %{y:.0f}<br><b>Desvio:</b> %{customdata:.1f}%<extra></extra>"
    ))

# Linhas das Curvas
if not df_curvas_filtrado.empty:
    df_linhas = gerar_pontos_curva(df_curvas_filtrado)
    for num in df_linhas['Curva'].unique():
        df_c = df_linhas[df_linhas['Curva'] == num]
        fig.add_trace(go.Scatter(
            x=df_c['Vazao'], y=df_c['Cota'],
            mode='lines', name=f'Curva {num}',
            line=dict(width=3)
        ))

# Estilização
mapa_nomes = st.session_state['medicoes'].drop_duplicates('Codigo').set_index('Codigo')['Nome'].to_dict()
nome_estacao = mapa_nomes.get(estacoes_sel[0], "Não encontrada")

fig.update_layout(
    title={
        'text': f"Medições de descarga x Curva chave<br><sup>Estação: {estacoes_sel[0]} - {nome_estacao}</sup>",
        'x': 0.5,           # Posiciona o título no meio da largura do gráfico
        'xanchor': 'center', # Garante que o ponto de ancoragem seja o centro do texto
        'yanchor': 'top'    # Garante o alinhamento vertical no topo
    },
    xaxis_title="Vazão (m³/s)", 
    yaxis_title="Cota (cm)",
    height=700, 
    template="plotly_white",
    hovermode="closest"
)

st.plotly_chart(fig, width='stretch')

# Tabela de conferência com Tooltips (ajuda ao passar o mouse)
with st.expander("Parâmetros das Curvas (Vigência filtrada)"):
    st.dataframe(
        df_curvas_filtrado[['Curva', 'ValidadeInicio', 'ValidadeFim', 'Tramo', 'CoefA', 'CoefH0', 'CoefN']], 
        hide_index=True,
        column_config={
            "Curva": st.column_config.TextColumn("Curva", help="Número de identificação da curva chave."),
            "ValidadeInicio": st.column_config.DateColumn("Início", help="Data de início da vigência desta curva."),
            "ValidadeFim": st.column_config.DateColumn("Fim", help="Data de término da vigência desta curva."),
            "Tramo": st.column_config.NumberColumn("Tramo", help="Segmento da curva (ex: 1º tramo para vazões baixas, 2º para médias)."),
            "CoefA": st.column_config.NumberColumn("Cof. A", help="Coeficiente de escala da equação Q = A * (H - H0)^N."),
            "CoefH0": st.column_config.NumberColumn("Cof. H0", help="Cota de vazão nula (em metros)."),
            "CoefN": st.column_config.NumberColumn("Cof. N", help="Expoente da equação (declividade da curva no papel logarítmico)."),
        }
    )

