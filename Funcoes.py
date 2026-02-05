# -*- coding: utf-8 -*-
"""
Funções
"""
#$ Bibliotecas
import pandas as pd
import streamlit as st
import os
import sys

def get_base_path():
    """
    Retorna o diretório onde o executável (Home.exe) ou o script está.
    """
    # Se estiver rodando como executável PyInstaller (--onefile)
    if getattr(sys, 'frozen', False):
        # ⚠️ MUDANÇA: Retorna o diretório onde o EXECUTÁVEL está.
        # Em modo onefile, este é o caminho mais confiável.
        return os.path.dirname(os.path.dirname(sys.executable))
    else:
        # Se for um script Python normal (desenvolvimento)
        # Retorna o diretório do próprio Funcoes.py
        return os.path.dirname(os.path.abspath(__file__))

#< ------------------------------------------------------------------------------------------------------------------------------
""" Carrega o arquivo .csv como um DataFrame"""
def carregaCSV_local(csv_file:str)-> pd.DataFrame:
    """ Carrega o arquivo .csv quando estiver usando a pasta local
        - transforma a coluna 'Data' para DateTime
    """
    
    # 👈 NOVO: Lógica para corrigir o caminho
    base_path = get_base_path()
    
    # Constrói o caminho completo: 
    # Junta o diretório base com o caminho relativo (Ex: ./csv/desvio.csv).
    # O .lstrip('./') remove './' ou '.\' inicial se houver.
    caminho_completo = os.path.join(base_path, csv_file.lstrip('./').lstrip('.\\'))
    
    # ------------------------------------------------------------------------
    
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

    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], format='%Y-%m-%d', errors='coerce')
    
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
