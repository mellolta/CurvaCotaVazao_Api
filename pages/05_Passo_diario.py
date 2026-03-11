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

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Configurações iniciais
fc.configuracoes_iniciais()

#- Título e descrição da página
st.subheader("Compara cotas e vazões do banco SQL com o dia anterior")

#- Verifica se os dados foram carregados na página principal, caso contrário, exibe uma mensagem de erro e interrompe a execução.
if 'outliers' not in st.session_state:
    st.error("Dados não carregados.")
    st.stop()

#- DataFrame outliers 
outliers = st.session_state['outliers']

#- Chama a função que retorna o dataframe já filtrado
df_filtrado = fc.menu_filtros_multi(outliers)

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
exibe_outliers = df_filtrado.copy()

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Limite de segurança para exibição com formatação condicional
#- Limite de segurança para a exibição das linhas com formatação condicional (Styler)
LIMITE_ESTILO = 1000
total_linhas = len(exibe_outliers)

#- Se for maior que o limite, pegamos apenas o topo para o Styler não quebrar
if total_linhas > LIMITE_ESTILO:
    df_para_estilizar = exibe_outliers.head(LIMITE_ESTILO)
    aviso_limite = f"⚠️ Exibindo as primeiras {LIMITE_ESTILO} linhas. Use os filtros para ver mais dados."
else:
    df_para_estilizar = exibe_outliers
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
    # Exibe a coluna 'Data' do DataFrame para o formato de string 'dd/mm/aaaa'.
    'Data': lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "",
    'Vazao': "{:.1f}",
    'Vazao_Anterior': "{:.1f}",
    'Diferença_vazao': "{:.1f}",
    'DifPer_vazao': "{:.1f}",
    'DifPer_cota': "{:.1f}",
}, decimal=',', thousands='.') \
.map(colorir_desvio, subset=['DifPer_cota','DifPer_vazao']) # <--- Aplica a cor apenas na coluna

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Exibe o DataFrame resultante

#- Descrição do DataFrame exibido
st.markdown(f"**Número de registros:** {len(exibe_outliers)}")
st.markdown("<br>", unsafe_allow_html=True) #- quebra de linha usando HTML para espaçamento

#- Exibe o DataFrame ocultando o índice e usando a largura total do contêiner
st.dataframe(
    df_estilizado,
    hide_index=True,
    width="stretch",
    column_config={
        "Codigo": st.column_config.NumberColumn("Código", format="%d"),
        # "Status": st.column_config.NumberColumn("Status", format="%d"),
        "Cota": st.column_config.NumberColumn("Cota (cm)", format="%d"),
        "Cota_Anterior": st.column_config.NumberColumn("Cota Anterior (cm)", format="%d"),
        "Vazao": "Vazão (m³/s)",
        "Status": "Status Cota",
        "Vazao_Anterior": "Vazão Anterior (m³/s)",
        "Diferença_vazao": "Diferença Vazao (m³/s)",
        "DifPer_vazao": "Diferença Vazao (%)",
        "DifPer_cota": "Diferença Cota (%)",
        "Diferença_cota": st.column_config.NumberColumn("Diferença Cota (cm)", format="%d"),
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
            **'Status Cota':** Classificação da cota do dia.  
            **'Diferença Vazão (%)':** Diferença percentual entre a vazão do dia e a vazão do dia anterior.  
            **'Diferença Cota (%)':** Diferença percentual entre a cota do dia e a cota do dia anterior.  
            """)
# < ------------------------------------------------------------------------------------------------------------------------------


