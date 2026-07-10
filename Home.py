# -*- coding: utf-8 -*-
"""
Api de visualização
Visualiza os arquivos .csv resultante do módulo VerificaVazaoGerada.py da pasta CurvaCotaVazao

Página inicial da aplicação Streamlit
Aqui é feito o carregamento dos arquivos, a exibição do título e descrição da aplicação.
Os arquivos são carregados do Google Drive usando os IDs armazenados em st.secrets.

"""
 #<===============================================================================================================================

#$ Bibliotecas
import streamlit as st
import funcoes as fc

#< ------------------------------------------------------------------------------------------------------------------------------
#$ Configurações iniciais
fc.configuracoes_iniciais()

#< ------------------------------------------------------------------------------------------------------------------------------
#$ Título e descrição da aplicação

#- texto centralizado (h1 se refere ao título principal, h4 aos subtítulos)
st.markdown("""<h1 style='text-align: center; color: blue;'
            >Análise e verificação de Cota, Vazão, Medições e Curva chave do banco SQL das URs</h1>""", 
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

            :green[Série Temporal] :grey[: Série temporal e análise comparativa dos valores de cota e a vazão com o dia anterior ]  
            :yellow[==== >>>> Atenção]: filtros ativos para diferenças percentuais acima de de 50% (e absolutas maiores que 10).  
            """)

#< ------------------------------------------------------------------------------------------------------------------------------

# fc.menu_reset_cache()

#< ------------------------------------------------------------------------------------------------------------------------------

