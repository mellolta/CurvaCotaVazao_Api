# -*- coding: utf-8 -*-
"""
Api de visualização
Visualiza os arquivos .csv resultante do módulo VerificaVazaoGerada.py

Modificações:
a função de carregamento dos csv foi para Funcoes_Diversas.py

Para rodar a aplicação use o comando:
streamlit run .\Home.py
"""
 #<===============================================================================================================================

#$ Bibliotecas
import streamlit as st
import pandas as pd
import Funcoes as fc

#< ------------------------------------------------------------------------------------------------------------------------------
#$ Configurações iniciais
#- para usar a largura total da página
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

#< ------------------------------------------------------------------------------------------------------------------------------
#$ Carregamento dos arquivos de dados

#- 1. Mapeia as chaves aos IDs dos segredos (IDs dos arquivos no Google Drive)
mapeamento_arquivos = {
    'balanceamento': st.secrets["id_balanceamento"],
    'cota': st.secrets["id_cota"],
    'medicoes': st.secrets["id_medicoes"],
    'outlyers_cotas': st.secrets["id_outlyers_cotas"],
    'vazao': st.secrets["id_vazao"]
}

#- 2. Inicializa e Carrega em um único loop
for chave, file_id in mapeamento_arquivos.items():
    
    #- cria as chaves no st.session_state
    if chave not in st.session_state:
        st.session_state[chave] = None
    
    #- carrega os arquivos
    if st.session_state[chave] is None:
        try:
            st.session_state[chave] = fc.carregaCSV_drive(file_id)
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo de {chave}: {e}")

#< ------------------------------------------------------------------------------------------------------------------------------
#$ Título e descrição da aplicação

#- texto centralizado (h1 se refere ao título principal, h4 aos subtítulos)
st.markdown("""<h1 style='text-align: center; color: blue;'
            >Análise e verificação do banco SQL das URs</h1>""", 
            unsafe_allow_html=True)

st.markdown(""":blue[Selecione a página na aba lateral conforme a descrição abaixo:]""")

st.markdown(""":green[Cota] :grey[: Comparação entre a cota e os limites de abrangência da curva chave para a data correspondente]""")

st.markdown(""":green[Vazao] :grey[: Comparação entre vazão do banco SQL X Vazão calculada pela curva-chave (Qcalc)]""")

st.markdown(""":green[Medicoes] :grey[: Resultado de cada medição do banco com o desvio em relação à vazão calculada pela curva chave que está no banco]""")

st.markdown(""":green[Balanceamento] :grey[: Resultado equivalente à saída 449 do SIADH "449_Características das Curva-Chave_Por Periodo Validade.xls"]""")

st.markdown(""":green[Outlyers_cotas] :grey[: Compara a cota com a do dia anterior ]""")


#< ------------------------------------------------------------------------------------------------------------------------------


