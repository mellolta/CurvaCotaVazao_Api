# -*- coding: utf-8 -*-
"""
Funções importantes
"""
#$ Bibliotecas
import streamlit as st
import pandas as pd
import locale
from pathlib import Path

#< ------------------------------------------------------------------------------------------------------------------------------
def configuracoes_iniciais():
    """ Comandos que se repetem em todas as páginas 
    """
    #- Aumenta o limite de elementos para formatação do Styler
    pd.set_option("styler.render.max_elements", 1000000)

    #- Tenta configurar o locale para Português (Brasil)
    try:
        # Tenta o padrão Linux/Unix (Streamlit Cloud)
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        try:
            # Tenta o padrão Windows
            locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
        except locale.Error:
            # Se ambos falharem, mantém o padrão do sistema
            locale.setlocale(locale.LC_ALL, '')

    # - para usar a largura total da página
    st.set_page_config(layout="wide")

    #- logo CPRM no canto superior direito
    st.image("https://intranet.sgb.gov.br/publique/media/marketing/logosgb_horizontal_original_v2.png", width=200)

    #- Chama a função (se já rodou, ele pega do cache instantaneamente)
    # carregar_dados_globais()
    #- Garante que os dados existam antes da página renderizar
    verificar_e_carregar_dados()

#< ------------------------------------------------------------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def obter_dados_base():
    """
    Esta função carrega os dados e os mantém em cache.
    Ela retorna o dicionário de DataFrames.
    """
    mapeamento_arquivos = {
        'balanceamento': st.secrets["id_balanceamento"],
        'cota': st.secrets["id_cota"],
        'medicoes': st.secrets["id_medicoes"],
        'outliers': st.secrets["id_outliers"],
        'vazao': st.secrets["id_vazao"],
        'curvas': st.secrets["id_curvas"]
    }
    
    datasets = {}
    for chave, file_id in mapeamento_arquivos.items():
        try:
            df = carregaCSV_drive(file_id)
            if df is not None:
                # Padronizações comuns
                if 'EstacaoCodigo' in df.columns:
                    df.rename(columns={'EstacaoCodigo': 'Codigo'}, inplace=True)
                
                # Conversão de datas
                for col in ['Data', 'ValidadeInicio', 'ValidadeFim']:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                
                datasets[chave] = df
        except Exception as e:
            st.error(f"Erro ao carregar {chave}: {e}")
    return datasets

#< ------------------------------------------------------------------------------------------------------------------------------
def verificar_e_carregar_dados():
    """
    Garante que os dados estejam no session_state em todas as execuções.
    """
    # Se uma chave essencial não estiver no estado, recarrega tudo
    if 'medicoes' not in st.session_state or st.session_state['medicoes'] is None:
        with st.spinner("Carregando dados do Drive..."):
            dados = obter_dados_base()
            for chave, df in dados.items():
                st.session_state[chave] = df

#< ------------------------------------------------------------------------------------------------------------------------------
# --- FUNÇÃO DE CARREGAMENTO COM CACHE ---
@st.cache_data(ttl=3600) # Expira em 3600 segundos (1 hora)
def carregar_dados_globais():
    """
    Carrega todos os arquivos necessários de uma vez só.
    O uso do cache_data garante que o processamento pesado ocorra apenas uma vez.
    """
    #- 1. Mapeia as chaves aos IDs dos segredos (IDs dos arquivos no Google Drive)
    mapeamento_arquivos = {
        'balanceamento': st.secrets["id_balanceamento"],
        'cota': st.secrets["id_cota"],
        'medicoes': st.secrets["id_medicoes"],
        'outliers': st.secrets["id_outliers"],
        'vazao': st.secrets["id_vazao"],
        'curvas': st.secrets["id_curvas"]
    }
    # mapeamento_arquivos = {
    #     'balanceamento': 'balanceamento.csv',
    #     'cota': 'cota.csv',
    #     'medicoes': 'medicoes.csv',
    #     'outliers': 'outliers.csv',
    #     'vazao': 'vazao.csv'
    #     'curvas': 'curvas.csv'
    # }
    
    datasets = {}
    
    for chave, file_id in mapeamento_arquivos.items():
        try:
            df = carregaCSV_drive(file_id)
            # df = carregaCSV_local(file_id) 
            
            # Padronização: Já faz o rename aqui para evitar erros nas páginas
            if 'EstacaoCodigo' in df.columns:
                df.rename(columns={'EstacaoCodigo': 'Codigo'}, inplace=True)
            
            #- lista de colunas para converter para DateTime
            colunas_data = ['Data', 'ValidadeInicio', 'ValidadeFim']
            for col in colunas_data:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], format='%Y-%m-%d', errors='coerce')
            
            #- status da cota
            mapa_status = {
                0: "Em branco",
                1: "1: Validado",
                2: "2: * (Estimado)",
                3: "3: ? (Duvidoso)",
                4: "4: # (Régua seca)",
                5: "5: ! (Régua coberta)",
                6: "6: @ (Rio seco)",
                7: "7: / (Rio cortado)"
                }
            if 'Status' in df.columns:
                # 1. Converte para numérico (caso venha como string ou float do CSV)
                df['Status'] = pd.to_numeric(df['Status'], errors='coerce')
                
                # 2. Mapeia os valores e preenche o que sobrar (nulos) com "Em branco"
                df['Status'] = df['Status'].map(mapa_status).fillna("Em branco")

            datasets[chave] = df
        except Exception as e:
            st.error(f"Erro crítico ao carregar {chave}: {e}")
            datasets[chave] = None
    
    
    #- Grava no session_state para garantir compatibilidade
    for chave, df in datasets.items():
        st.session_state[chave] = df

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

        #- Lista de colunas para converter para DateTime
        colunas_data = ['Data', 'ValidadeInicio', 'ValidadeFim']

        #- Conversão de Data
        for col in colunas_data:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%Y-%m-%d', errors='coerce')

        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None

#< ------------------------------------------------------------------------------------------------------------------------------
def menu_filtros_multi(df_input):
    """
    Cria menu superior global que preserva seleção em todas as páginas.
    Trata automaticamente a lógica de Ano/Mês para Data ou ValidadeInicio/Fim.
    """
    # 1. INICIALIZAÇÃO DE ESTADO PERSISTENTE
    # chaves_globais = ['filtro_ur', 'filtro_cod', 'filtro_ano', 'filtro_mes', 
    #                 'w_ur', 'w_cod', 'w_ano', 'w_mes']

    # for k in chaves_globais:
    #     if k not in st.session_state:
    #         st.session_state[k] = []
    
    #- 1. INICIALIZAÇÃO DE ESTADOS GLOBAIS (Se não existirem)
    chaves_globais = ['filtro_ur', 'filtro_cod', 'filtro_ano', 'filtro_mes']
    for k in chaves_globais:
        if k not in st.session_state:
            st.session_state[k] = []
        
        # Sincronização: Se o widget (w_...) foi resetado pela troca de página, 
        # mas temos valor no filtro global, repopulamos o widget.
        chave_w = 'w_' + k.split('_')[1]
        if chave_w not in st.session_state:
            st.session_state[chave_w] = st.session_state[k]

    df = df_input.copy()
        
    #- Padronização de nomes de colunas
    if 'EstacaoCodigo' in df.columns:
        df.rename(columns={'EstacaoCodigo': 'Codigo'}, inplace=True)

    mapa_nomes = df.drop_duplicates('Codigo').set_index('Codigo')['Nome'].to_dict()

    # --- FUNÇÃO INTERNA PARA GERAR AS OPÇÕES DOS DROPDOWNS ---
    def obter_opcoes(coluna_alvo):
        temp = df.copy()
        
        # Lógica para gerar opções de Ano/Mês quando as colunas não existem (Balanceamento)
        if coluna_alvo in ['Ano', 'Mes'] and 'Data' not in temp.columns and 'ValidadeInicio' in temp.columns:
            if coluna_alvo == 'Ano':
                # Criamos um set para armazenar todos os anos únicos dentro de cada intervalo
                anos_totais = set()
                for _, row in temp[['ValidadeInicio', 'ValidadeFim']].dropna().iterrows():
                    # Gera a lista de anos entre o início e o fim (ex: 2022, 2023, 2024)
                    for ano in range(row['ValidadeInicio'].year, row['ValidadeFim'].year + 1):
                        anos_totais.add(ano)
                return sorted(list(anos_totais), reverse=True)
            
            if coluna_alvo == 'Mes':
                # Para meses, geralmente mostramos de 1 a 12 se houver dados
                return sorted(temp['ValidadeInicio'].dt.month.dropna().unique().tolist())

        # Filtragem cruzada para as opções (se selecionar UR, limita as Estações)
        if coluna_alvo != 'UR' and st.session_state.filtro_ur:
            temp = temp[temp['UR'].isin(st.session_state.filtro_ur)]
        if coluna_alvo != 'Codigo' and st.session_state.filtro_cod:
            temp = temp[temp['Codigo'].isin(st.session_state.filtro_cod)]
        
        # Filtro de Ano/Mes só se a coluna existir no DataFrame atual
        if 'Ano' in temp.columns and coluna_alvo != 'Ano' and st.session_state.filtro_ano:
            temp = temp[temp['Ano'].isin(st.session_state.filtro_ano)]
        if 'Mes' in temp.columns and coluna_alvo != 'Mes' and st.session_state.filtro_mes:
            temp = temp[temp['Mes'].isin(st.session_state.filtro_mes)]

        if coluna_alvo in temp.columns:
            return sorted(temp[coluna_alvo].unique().tolist())
        return []

    # Auxiliar para evitar erro de StreamlitAPIException (default fora das options)
    # def validar_default(selecionados, opcoes_disponiveis):
    #     return [item for item in selecionados if item in opcoes_disponiveis]

    # --- RENDERIZAÇÃO DA INTERFACE ---
    # Função auxiliar para o callback (resolve o problema do clique duplo)
    def atualizar_filtros():
        st.session_state.filtro_ur = st.session_state.w_ur
        st.session_state.filtro_cod = st.session_state.w_cod
        st.session_state.filtro_ano = st.session_state.w_ano
        st.session_state.filtro_mes = st.session_state.w_mes

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ops = obter_opcoes('UR')
        st.multiselect(
            'Unidade Regional', options=ops, 
            key='w_ur', # Chave do widget
            # default=validar_default(st.session_state.filtro_ur, ops),
            on_change=atualizar_filtros
        )

    with col2:
        ops = obter_opcoes('Codigo')
        st.multiselect(
            'Estação', options=ops, 
            key='w_cod',
            # default=validar_default(st.session_state.filtro_cod, ops),
            format_func=lambda c: f"{c} - {mapa_nomes.get(c, 'N/A')}",
            on_change=atualizar_filtros
        )

    with col3:
        ops = sorted(obter_opcoes('Ano'), reverse=True)
        st.multiselect(
            'Ano', options=ops, 
            key='w_ano',
            # default=validar_default(st.session_state.filtro_ano, ops),
            on_change=atualizar_filtros
        )

    with col4:
        ops = obter_opcoes('Mes')
        st.multiselect(
            'Mês', options=ops, 
            key='w_mes',
            # default=validar_default(st.session_state.filtro_mes, ops),
            on_change=atualizar_filtros
        )
    
    #- Sincroniza os valores após a renderização para garantir que o DF use o dado atual
    atualizar_filtros()

    # --- APLICAÇÃO DOS FILTROS NO DATAFRAME FINAL ---
    df_filtrado = df.copy()
    
    #- Filtros de UR e Codigo
    if st.session_state.filtro_ur:
        df_filtrado = df_filtrado[df_filtrado['UR'].isin(st.session_state.filtro_ur)]
    if st.session_state.filtro_cod:
        df_filtrado = df_filtrado[df_filtrado['Codigo'].isin(st.session_state.filtro_cod)]

    # Filtros de Tempo (Lógica Dual: Data vs Intervalo)
    if st.session_state.filtro_ano or st.session_state.filtro_mes:
        # CASO A: Balanceamento (ValidadeInicio e ValidadeFim)
        if 'ValidadeInicio' in df_filtrado.columns and 'Data' not in df_filtrado.columns:
            
            #- FILTRO DE ANO POR INTERSEÇÃO
            if st.session_state.filtro_ano:
                ano_min = min(st.session_state.filtro_ano)
                ano_max = max(st.session_state.filtro_ano)
                
                # Uma curva é válida se o seu início ocorre até o fim do período filtrado
                # E o seu fim ocorre após o início do período filtrado.
                mask_ano = (df_filtrado['ValidadeInicio'].dt.year <= ano_max) & \
                           (df_filtrado['ValidadeFim'].dt.year >= ano_min)
                df_filtrado = df_filtrado[mask_ano]

            #- FILTRO DE MÊS
            if st.session_state.filtro_mes:
                # Para meses, a lógica de intervalo é mais complexa se cruzar anos,
                # mas se o objetivo é ver curvas que estiveram ativas naqueles meses:
                mes_min = min(st.session_state.filtro_mes)
                mes_max = max(st.session_state.filtro_mes)
                
                # Simplificando: a curva deve ter meses que se sobreponham ao range selecionado
                mask_mes = (df_filtrado['ValidadeInicio'].dt.month <= mes_max) & \
                           (df_filtrado['ValidadeFim'].dt.month >= mes_min)
                df_filtrado = df_filtrado[mask_mes]
        
        # CASO B: Páginas Padrão (Coluna 'Ano' e 'Mes' existentes)
        else:
            if st.session_state.filtro_ano:
                df_filtrado = df_filtrado[df_filtrado['Ano'].isin(st.session_state.filtro_ano)]
            if st.session_state.filtro_mes:
                df_filtrado = df_filtrado[df_filtrado['Mes'].isin(st.session_state.filtro_mes)]

    #- Aviso de dados não encontrados
    if df_filtrado.empty:
        st.warning("⚠️ **Nenhum dado encontrado para os filtros selecionados nesta página.**")
        st.info("💡 Clique em 'Limpar Filtros' para resetar a visão.")

    return df_filtrado

#< ------------------------------------------------------------------------------------------------------------------------------
# --- Função para limpar os filtros ---
def limpar_filtros():
    """Reseta os filtros globais e limpa os widgets da tela."""
    chaves = [
        'filtro_ur', 'filtro_cod', 'filtro_ano', 'filtro_mes',
        'w_ur', 'w_cod', 'w_ano', 'w_mes'
    ]
    for k in chaves:
        if k in st.session_state:
            st.session_state[k] = []

#< ------------------------------------------------------------------------------------------------------------------------------
#< ------------------------------------------------------------------------------------------------------------------------------
#< ------------------------------------------------------------------------------------------------------------------------------
#< ------------------------------------------------------------------------------------------------------------------------------




