# -*- coding: utf-8 -*-
"""
Funções
"""
#$ Bibliotecas
import pandas as pd
import streamlit as st
from pathlib import Path
import os
import sys

#< ------------------------------------------------------------------------------------------------------------------------------
""" Carrega o arquivo .csv como um DataFrame"""
def carregaCSV_local(csv_file:str)-> pd.DataFrame:
    """ Carrega o arquivo .csv quando estiver usando a pasta local
        - transforma a coluna 'Data' para DateTime
    """
    #- 1. Definimos o diretório base como um objeto Path
    base_dir = Path(r'C:\Users\luis.mello\Documents\Python\Scripts\Projetos_CPRM\CurvaCotaVazao\Resultado\csv')
    
    #- 2. Extraímos apenas o nome do arquivo (caso o usuário passe um caminho relativo)
    # Exemplo: './dados.csv' vira 'dados.csv'
    nome_arquivo = Path(csv_file).name
    
    #- 3. Criamos o caminho completo usando o operador '/' (exclusivo do pathlib)
    caminho_completo = base_dir / nome_arquivo
    
    #- Verificação amigável de erro
    if not caminho_completo.exists():
        raise FileNotFoundError(f"⚠️ O arquivo não foi encontrado em: {caminho_completo}")
    
    # O pandas tentará ler o arquivo do caminho_completo
    df = pd.read_csv(caminho_completo, 
                     sep=';', 
                     header=0,
                     decimal=',',
                     encoding='utf-8',
                     na_values='N/A',
                     )
    
    if df.columns[0] == 'Unnamed: 0':
        df.drop(columns=[df.columns[0]], inplace=True)

    #- Lista de colunas para converter para DateTime
    colunas_data = ['Data', 'ValidadeInicio', 'ValidadeFim']

    #- Conversão de Data
    for col in colunas_data:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%Y-%m-%d', errors='coerce')
        
    return df

#< ------------------------------------------------------------------------------------------------------------------------------
"""st.cache_data(ttl=3600): Como o arquivo CSV está na web, carregar ele toda vez que você clica em um botão deixaria o app lento. 
    Com isso, o Streamlit baixa o arquivo uma vez e o guarda na memória por 1 hora.
"""
@st.cache_data(ttl=3600)
def carregaCSV_drive(file_id):
    """
    Carrega o CSV. Se for um ID do Google Drive, formata a URL.
    """
    url = f'https://drive.google.com/uc?export=download&id={file_id}'

    try:
        df = pd.read_csv(url, 
                     sep=';', 
                     header=0,
                     decimal=',',
                     encoding='utf-8',
                     na_values='N/A',
                     )
        
        if df.columns[0] == 'Unnamed: 0':
            df.drop(columns=[df.columns[0]], inplace=True)

        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], format='%Y-%m-%d', errors='coerce')

        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None
