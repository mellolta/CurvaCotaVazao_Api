# -*- coding: utf-8 -*-
"""
Api de visualização
Visualiza os arquivos .csv resultante do módulo VerificaVazaoGerada.py da pasta CurvaCotaVazao

Página inicial da aplicação Streamlit
Aqui é feito o carregamento dos arquivos, a exibição do título e descrição da aplicação.
Os arquivos são carregados do Google Drive usando os IDs armazenados em st.secrets.


Para rodar a aplicação use o comando:
streamlit run .\Home.py
"""
 #<===============================================================================================================================

#$ Bibliotecas
import streamlit as st
import Funcoes as fc

#< ------------------------------------------------------------------------------------------------------------------------------
#$ Configurações iniciais
#- usa a largura total da página
st.set_page_config(layout="wide")

#- logo CPRM no canto superior direito
st.image("https://intranet.sgb.gov.br/publique/media/marketing/logosgb_horizontal_original_v2.png", width=200)

#- Inicializa as chaves no st.session_state se não existirem (evita KeyError)
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
#$ Título e descrição da aplicação

#- texto centralizado (h1 se refere ao título principal, h4 aos subtítulos)
st.markdown("""<h1 style='text-align: center; color: blue;'
            >Análise e verificação do banco SQL das URs</h1>""", 
            unsafe_allow_html=True)

st.markdown(""":blue[Selecione a página na aba lateral conforme a descrição abaixo:]""")

st.markdown("""
            :green[Cota] :grey[: Exibe as estações cujas cotas não estão dentro dos limites de abrangência da curva chave para a data correspondente]  
            :yellow[==== >>>> Ação necessária]: revisar a cota do dia ou atualizar a curva-chave no banco SQL.

            :green[Vazao] :grey[: Exibe as estações cuja vazão do banco SQL se difere da vazão calculada pela curva-chave (Qcalc) para a data correspondente]  
            :yellow[==== >>>> Ação necessária]: reprocessar a vazão no banco SQL para o período correspondente.

            :green[Medicoes] :grey[: Resultado de cada medição com o desvio em relação a vazão calculada pela curva chave que está no banco SQL.]  
            :yellow[==== >>>> Atenção]: medições com desvio superior a 20% estão destacadas em vermelho.

            :green[Balanceamento] :grey[: Resultado equivalente à saída 449 do SIADH "449_Características das Curva-Chave_Por Periodo Validade.xls"]  
            :yellow[==== >>>> Atenção]: curvas com desvio superior a 20% ou balanceamento das medições superior a 30%-70% estão destacadas em vermelho.

            :green[Passo diário] :grey[: Compara a cota e a vazão com o dia anterior ]
            """)

#< ------------------------------------------------------------------------------------------------------------------------------
#$ Carregamento dos arquivos de dados

#- O spinner mostra uma animação e a mensagem enquanto a função roda
with st.spinner('Carregando bases de dados...'):
    dados = fc.carregar_dados_globais()
    for chave, df in dados.items():
        st.session_state[chave] = df

#< ------------------------------------------------------------------------------------------------------------------------------

