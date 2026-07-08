# -*- coding: utf-8 -*-
"""
Funções importantes
"""
#$ Bibliotecas
import io
import requests
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
    
    #- logo CPRM no canto superior direito da página
    st.image("https://intranet.sgb.gov.br/publique/media/marketing/logosgb_horizontal_original_v2.png", width=200)

    #- Garante que os dados existam antes da página renderizar
    # verificar_e_carregar_todas_as_tabelas()

#< ------------------------------------------------------------------------------------------------------------------------------
#$ Mapeamento centralizado (fora da função para ficar organizado)

MAPEAMENTO_ARQUIVOS = {
    'balanceamento': "id_balanceamento",
    'cota': "id_cota",
    'curvas': "id_curvas",
    'medicoes': "id_medicoes",
    'vazao': "id_vazao"
}

#< ------------------------------------------------------------------------------------------------------------------------------
@st.cache_data(ttl=3600)  # Mantém o cache por 1 hora por tabela carregada
def obter_tabela_por_chave(chave):
    """
    Carrega, processa e retorna APENAS a tabela solicitada.
    """
    if chave not in MAPEAMENTO_ARQUIVOS:
        st.error(f"Chave '{chave}' não encontrada no mapeamento.")
        return None
        
    secret_id = MAPEAMENTO_ARQUIVOS[chave]
    file_id = st.secrets[secret_id]
    
    try:
        # Carrega apenas o arquivo necessário
        df = carregaCSV_drive(file_id)
        
        if df is not None:
            # 1. Padronização de Colunas
            if 'EstacaoCodigo' in df.columns:
                df.rename(columns={'EstacaoCodigo': 'Codigo'}, inplace=True)
            
            # 2. Tratamento de Status
            if 'Status' in df.columns:
                mapa_status = {
                    0: "Em branco", 1: "1: Validado", 2: "2: * (Estimado)",
                    3: "3: ? (Duvidoso)", 4: "4: # (Régua seca)",
                    5: "5: ! (Régua coberta)", 6: "6: @ (Rio seco)", 7: "7: / (Rio cortado)"
                }
                df['Status'] = pd.to_numeric(df['Status'], errors='coerce')
                df['Status'] = df['Status'].map(mapa_status).fillna("Em branco")
            
            return df
            
    except Exception as e:
        st.error(f"Erro ao carregar a tabela '{chave}': {e}")
        return None

#< ------------------------------------------------------------------------------------------------------------------------------
def gerenciar_pagina_e_carregar(nome_pagina, chaves_da_pagina):
    """
    Gerencia a troca de páginas, limpa tabelas antigas do session_state 
    e carrega apenas as tabelas necessárias para a página atual.
    
    chaves_da_pagina: lista de strings ex: ['balanceamento', 'vazao']
    """
    # 1. Se mudou de página, limpa o session_state das tabelas da página anterior
    if "pagina_atual" in st.session_state and st.session_state.pagina_atual != nome_pagina:
        chaves_para_limpar = [
            'balanceamento', 'cota', 'medicoes', 'vazao', 'curvas'
        ]
        for chave in chaves_para_limpar:
            if chave in st.session_state:
                del st.session_state[chave]
                
    st.session_state.pagina_atual = nome_pagina

    # 2. Carrega apenas o que a página atual precisa (se já não estiver no session_state)
    for chave in chaves_da_pagina:
        if chave not in st.session_state or st.session_state[chave] is None:
            with st.spinner(f"Carregando dados de {chave}..."):
                st.session_state[chave] = obter_tabela_por_chave(chave)

#< ------------------------------------------------------------------------------------------------------------------------------
@st.cache_data(ttl=3600) # Expira em 3600 segundos (1 hora)
def obter_dados_base():
    """
    Esta função carrega os dados e os mantém em cache.
    Ela retorna o dicionário de DataFrames.
    """
    #- Mapeia as chaves aos IDs dos segredos (IDs dos arquivos no Google Drive)
    mapeamento_arquivos = {
        'balanceamento': st.secrets["id_balanceamento"],
        'cota': st.secrets["id_cota"],
        # 'cota_vazao': st.secrets["id_cota_vazao"],
        # 'cotas2L': st.secrets["id_cotas2L"],
        'curvas': st.secrets["id_curvas"],
        'medicoes': st.secrets["id_medicoes"],
        # 'passo_diario': st.secrets["id_passo_diario"],
        'vazao': st.secrets["id_vazao"]
    }
    # mapeamento_arquivos = {
    #     'balanceamento': 'balanceamento.parquet',
    #     'cota': 'cota.parquet',
    #     'medicoes': 'medicoes.parquet',
    #     'passo_diario': 'passo_diario.parquet',
    #     'vazao': 'vazao.parquet',
    #     'curvas': 'curvas.parquet',
    #     'cota_vazao': 'cota_vazao.parquet',
    #     'cotas2L': 'cotas2L.parquet',
    # }
    
    datasets = {}
    for chave, file_id in mapeamento_arquivos.items():
        try:
            # df = carrega_parquet_drive(file_id)
            # df = carrega_parquet_local(file_id)
            df = carregaCSV_drive(file_id)
            # df = carregaCSV_local(file_id) 

            if df is not None:
                #- 1. Padronização de Colunas
                if 'EstacaoCodigo' in df.columns:
                    df.rename(columns={'EstacaoCodigo': 'Codigo'}, inplace=True)
                
                #- 2. Conversão de datas
                # for col in ['Data', 'Data_Hora', 'ValidadeInicio', 'ValidadeFim']:
                #     if col in df.columns:
                #         df[col] = pd.to_datetime(df[col], format='%Y-%m-%d', errors='coerce')
                
            #- 3. Tratamento de Status
            if 'Status' in df.columns:
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
                #- Converte para numérico (caso venha como string ou float do CSV)
                df['Status'] = pd.to_numeric(df['Status'], errors='coerce')
                
                #- Mapeia os valores e preenche o que sobrar (nulos) com "Em branco"
                df['Status'] = df['Status'].map(mapa_status).fillna("Em branco")

            #- Grava no session_state
            datasets[chave] = df

        except Exception as e:
            st.error(f"Erro ao carregar {chave}: {e}")

    return datasets

#< ------------------------------------------------------------------------------------------------------------------------------
def verificar_e_carregar_todas_as_tabelas():
    """
    Garante que TODAS as tabelas essenciais estejam no session_state.
    Se faltar qualquer uma, recarrega o pacote completo.
    """
    #- Lista de chaves que DEVEM existir no session_state
    chaves_essenciais = [
        'balanceamento', 'cota', 'medicoes', 
        # 'passo_diario', 'cota_vazao', 'cotas2L',
        'vazao', 'curvas'
    ]
    
    #- Verifica se alguma chave está faltando ou está vazia (None)
    precisa_carregar = any(
        chave not in st.session_state or st.session_state[chave] is None 
        for chave in chaves_essenciais
    )

    if precisa_carregar:
        #- O spinner mostra uma animação e a mensagem enquanto a função roda
        with st.spinner("Carregando base de dados..."):
            dados = obter_dados_base()
            #- O dicionário 'dados' contém as chaves do mapeamento_arquivos
            for chave, df in dados.items():
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
""" Carrega o arquivo .parquet como um DataFrame"""
def carrega_parquet_local(parquet_file: str) -> pd.DataFrame:
    """ Carrega o arquivo .parquet quando estiver usando a pasta local
        - Remove índices residuais se houverem
        - Transforma as colunas de data para DateTime
    """
    #- 1. Definimos o diretório base como um objeto Path
    base_dir = Path(r'C:\Users\luis.mello\Documents\Python\Scripts\Projetos_CPRM\CurvaCotaVazao\Resultado\parquet')
    
    #- 2. Extraímos apenas o nome do arquivo (caso o usuário passe um caminho relativo)
    nome_arquivo = Path(parquet_file).name
    
    #- 3. Criamos o caminho completo usando o operador '/'
    caminho_completo = base_dir / nome_arquivo
    
    #- Verificação amigável de erro
    if not caminho_completo.exists():
        raise FileNotFoundError(f"⚠️ O arquivo não foi encontrado em: {caminho_completo}")
    
    # O pandas lerá o arquivo parquet preservando os tipos originais
    df = pd.read_parquet(caminho_completo)
    
    #- Tratamento de coluna de índice residual (caso exista)
    if len(df.columns) > 0 and df.columns[0] == 'Unnamed: 0':
        df.drop(columns=[df.columns[0]], inplace=True)
    
    #- Lista de colunas para garantir a conversão para DateTime
    colunas_data = ['Data', 'Data_Hora', 'ValidadeInicio', 'ValidadeFim']

    #- Conversão de Data (Removido o 'format' fixo para evitar quebras com Timestamp completo)
    for col in colunas_data:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
    return df

#< ------------------------------------------------------------------------------------------------------------------------------
""" Carrega o arquivo .parquet como um DataFrame"""
@st.cache_data(ttl=3600)
def carrega_parquet_drive(file_id):

    url = f"https://drive.google.com/uc?export=download&id={file_id}"

    try:
        resposta = requests.get(url)
        resposta.raise_for_status()

        df = pd.read_parquet(io.BytesIO(resposta.content))

        #- Lista de colunas para garantir a conversão para DateTime
        colunas_data = ['Data', 'Data_Hora', 'ValidadeInicio', 'ValidadeFim']

        #- Conversão de Data (Removido o 'format' fixo para evitar quebras com Timestamp completo)
        for col in colunas_data:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        return df

    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None

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
def menu_filtros_multi(lista_dfs):
    """
    Cria menu superior global que preserva seleção em todas as páginas.
    Trata automaticamente a lógica de Ano/Mês para Data ou ValidadeInicio/Fim.

    Recebe um DataFrame ou uma lista
    """
    #- Se receber apenas um DF fora de uma lista, transforma em lista para o loop
    if not isinstance(lista_dfs, list):
        lista_dfs = [lista_dfs]

    #- 1. INICIALIZAÇÃO DE ESTADOS GLOBAIS (Se não existirem)
    for sufixo in ['ur', 'cod', 'ano', 'mes']:
        global_key = f'filtro_{sufixo}'
        widget_key = f'w_{sufixo}'
        
        if global_key not in st.session_state:
            st.session_state[global_key] = []
    
        # FORÇA: O widget deve SEMPRE carregar o que está no global.
        # Isso evita que o 'reset' do Streamlit na mudança de página limpe o dado.
        st.session_state[widget_key] = st.session_state[global_key]

    #- Usamos o primeiro DF da lista para mapear nomes de estações para o widget
    df_ref = lista_dfs[0]
    mapa_nomes = df_ref.drop_duplicates('Codigo').set_index('Codigo')['Nome'].to_dict()

    # --- FUNÇÃO INTERNA PARA GERAR AS OPÇÕES DOS DROPDOWNS ---
    def obter_opcoes(coluna_alvo):
        temp = df_ref.copy()
        
        # Lógica para gerar opções de Ano/Mês quando as colunas não existem (Balanceamento e Curvas)
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

    # --- RENDERIZAÇÃO DA INTERFACE ---
    # Função auxiliar para o callback (resolve o problema do clique duplo)
    def atualizar_filtros():
        st.session_state.filtro_ur = st.session_state.w_ur
        st.session_state.filtro_cod = st.session_state.w_cod
        st.session_state.filtro_ano = st.session_state.w_ano
        st.session_state.filtro_mes = st.session_state.w_mes

    #- colunas de filtro
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ops = obter_opcoes('UR')
        st.multiselect(
            'Unidade Regional', options=ops, 
            key='w_ur', # Chave do widget
            on_change=atualizar_filtros
        )

    with col2:
        ops = obter_opcoes('Codigo')
        st.multiselect(
            'Estação', options=ops, 
            key='w_cod',
            format_func=lambda c: f"{c} - {mapa_nomes.get(c, 'N/A')}",
            on_change=atualizar_filtros
        )

    with col3:
        ops = sorted(obter_opcoes('Ano'), reverse=True)
        st.multiselect(
            'Ano', options=ops, 
            key='w_ano',
            on_change=atualizar_filtros
        )

    with col4:
        ops = obter_opcoes('Mes')
        st.multiselect(
            'Mês', options=ops, 
            key='w_mes',
            on_change=atualizar_filtros
        )
    
    #- Sincroniza os valores após a renderização para garantir que o DF use o dado atual
    atualizar_filtros()

    # --- APLICAÇÃO DOS FILTROS EM TODOS OS DFs ---
    dfs_filtrados = []
    for df in lista_dfs:
        dff = df.copy()
    
        #- Filtros de UR e Codigo
        if st.session_state.filtro_ur:
            dff = dff[dff['UR'].isin(st.session_state.filtro_ur)]
        if st.session_state.filtro_cod:
            dff = dff[dff['Codigo'].isin(st.session_state.filtro_cod)]

        #- Filtros de Tempo (Lógica Dual: Data vs Intervalo)
        if st.session_state.filtro_ano or st.session_state.filtro_mes:
            
            #* CASO A: Balanceamento e Curvas (ValidadeInicio e ValidadeFim)
            if 'ValidadeInicio' in dff.columns and 'Data' not in dff.columns:
                
                # Determinamos o range de anos e meses selecionados
                # Se não houver seleção, usamos o mínimo/máximo possível do dado
                ano_min = min(st.session_state.filtro_ano) if st.session_state.filtro_ano else dff['ValidadeInicio'].dt.year.min()
                ano_max = max(st.session_state.filtro_ano) if st.session_state.filtro_ano else dff['ValidadeFim'].dt.year.max()
                
                mes_min = min(st.session_state.filtro_mes) if st.session_state.filtro_mes else 1
                mes_max = max(st.session_state.filtro_mes) if st.session_state.filtro_mes else 12

                # Criamos datas artificiais de início e fim do período filtrado para comparação real
                # Ex: Se filtrou 2023 e mês 5, o período é de 01/05/2023 até o fim de 2023 (ou fim de maio)
                data_limite_inicio = pd.Timestamp(int(ano_min), int(mes_min), 1)
                
                # Data de Fim: Usamos MonthEnd para garantir o último dia correto do mês
                # Primeiro criamos o dia 1 do mês máximo
                data_base_fim = pd.Timestamp(int(ano_max), int(mes_max), 1)
                # O Pandas calcula o último dia real (28, 29, 30 ou 31)
                data_limite_fim = data_base_fim + pd.offsets.MonthEnd(0)

                # --- FILTRO POR INTERSEÇÃO TOTAL ---
                # A curva é válida se:
                # 1. O início da curva é anterior ou igual ao fim do período filtrado
                # 2. O fim da curva é posterior ou igual ao início do período filtrado
                mask_intersecao = (dff['ValidadeInicio'] <= data_limite_fim) & \
                                 (dff['ValidadeFim'] >= data_limite_inicio)
                
                dff = dff[mask_intersecao]

            #* CASO B: Páginas Padrão (Coluna 'Ano' e 'Mes' existentes)
            else:
                if st.session_state.filtro_ano:
                    dff = dff[dff['Ano'].isin(st.session_state.filtro_ano)]
                if st.session_state.filtro_mes:
                    dff = dff[dff['Mes'].isin(st.session_state.filtro_mes)]
        dfs_filtrados.append(dff)

    #- Aviso de dados não encontrados para a lista principal
    if lista_dfs[0].empty:
        st.warning("⚠️ **Nenhum dado encontrado para os filtros selecionados nesta página.**")
        st.info("💡 Clique em 'Limpar Filtros' para resetar a visão.")

    return dfs_filtrados if len(dfs_filtrados) > 1 else dfs_filtrados[0]

#< ------------------------------------------------------------------------------------------------------------------------------
def filtro_numerico(df, coluna, label):
    """
    Cria um filtro híbrido (Input + Slider) que se auto-ajusta
    conforme os dados filtrados por outros componentes (Estação, UR, etc).
    """
    col_sel, col_inputs = st.columns([1, 2])
    
    with col_sel:
        tipo = st.selectbox(f"Filtrar {label}", ["Todos", "Intervalo"], key=f"tipo_{coluna}")
    
    df_result = df.copy()
    
    if tipo == "Intervalo":
        # 1. Calculamos os limites REAIS dos dados atuais
        v_min_abs = float(df[coluna].min())
        v_max_abs = float(df[coluna].max())

        # Chaves para o session_state
        k_min = f"v_min_{coluna}"
        k_max = f"v_max_{coluna}"
        k_slider = f"slide_widget_{coluna}"

        # 2. VALIDAÇÃO CRÍTICA: Se os limites do session_state estão fora da realidade 
        # dos novos dados (ex: mudou a estação), nós os resetamos.
        if k_min not in st.session_state or st.session_state[k_min] < v_min_abs or st.session_state[k_min] > v_max_abs:
            st.session_state[k_min] = v_min_abs
        if k_max not in st.session_state or st.session_state[k_max] > v_max_abs or st.session_state[k_max] < v_min_abs:
            st.session_state[k_max] = v_max_abs

        # --- FUNÇÕES DE SINCRONIZAÇÃO (CALLBACKS) ---
        def update_slider():
            # Quando o número muda, atualiza o slider
            st.session_state[k_slider] = (st.session_state[f"num_min_{coluna}"], st.session_state[f"num_max_{coluna}"])
            st.session_state[k_min] = st.session_state[f"num_min_{coluna}"]
            st.session_state[k_max] = st.session_state[f"num_max_{coluna}"]

        def update_numbers():
            # Quando o slider muda, atualiza os números
            st.session_state[k_min] = st.session_state[k_slider][0]
            st.session_state[k_max] = st.session_state[k_slider][1]

        with col_inputs:
            c_min, c_max = st.columns(2)
            
            # Usamos os valores validados do session_state
            val_min = c_min.number_input(
                f"Maior que ({label})", 
                min_value=v_min_abs, 
                max_value=v_max_abs,
                value=st.session_state[k_min],
                step=0.001 if v_max_abs < 100 else 1.0,
                key=f"num_min_{coluna}", # Adicionado key única para o widget
                on_change=update_slider # Gatilho: alterou número -> move slider
            )
            
            val_max = c_max.number_input(
                f"Menor que ({label})", 
                min_value=v_min_abs, 
                max_value=v_max_abs,
                value=st.session_state[k_max],
                step=0.001 if v_max_abs < 100 else 1.0,
                key=f"num_max_{coluna}",
                on_change=update_slider # Gatilho: alterou número -> move slider
            )

            # 2. Slider
            # Se as chaves de número mudaram via digitação, o slider precisa nascer com o valor novo
            if k_slider not in st.session_state:
                st.session_state[k_slider] = (st.session_state[k_min], st.session_state[k_max])

            # 3. Slider sincronizado
            val_slider = st.slider(
                f"Ajuste {label}",
                min_value=v_min_abs, 
                max_value=v_max_abs,
                key=k_slider,
                on_change=update_numbers, # Gatilho: moveu slider -> altera números
                label_visibility="collapsed"
            )

            # Atualiza o state para a próxima rodada
            st.session_state[k_min], st.session_state[k_max] = val_slider
            
            # Filtra o DataFrame
            df_result = df_result[(df_result[coluna] >= st.session_state[k_min]) & 
                                  (df_result[coluna] <= st.session_state[k_max])]
            
    return df_result

#< ------------------------------------------------------------------------------------------------------------------------------
# --- Função para limpar os filtros ---
def limpar_filtros():
    """Reseta os filtros globais e limpa os widgets da tela."""
    # 1. Filtros de lista (Multiselect)
    chaves_multi = ['filtro_ur', 'filtro_cod', 'filtro_ano', 'filtro_mes', 'w_ur', 'w_cod', 'w_ano', 'w_mes']
    for k in chaves_multi:
        if k in st.session_state:
            st.session_state[k] = []

    # 2. Filtros de Intervalo e Widgets Numéricos
    # Deletamos tudo que começa com esses prefixos
    prefixos = ['v_min_', 'v_max_', 'tipo_', 'num_min_', 'num_max_', 'slide_widget_']
    
    # Criamos uma lista das chaves para não modificar o dicionário durante o loop
    chaves_atuais = list(st.session_state.keys())
    
    for key in chaves_atuais:
        if any(prefix in key for prefix in prefixos):
            del st.session_state[key]

#< ------------------------------------------------------------------------------------------------------------------------------
def menu_reset_cache():
    """
    Cria um botão no menu lateral para limpar o cache e recarregar os dados.
    """
    with st.sidebar:
        st.subheader("Manutenção")
        if st.button("🔄 Recarregar Base de Dados"):
            # 1. Limpa o cache das funções decoradas com @st.cache_data
            obter_dados_base.clear()
            
            # 2. Limpa as variáveis de dados no session_state para forçar a recarga
            chaves_para_limpar = [
                'balanceamento', 'cota', 'medicoes', 
                # 'passo_diario', 'cota_vazao', 'cotas2L',
                'vazao', 'curvas'
            ]
            for chave in chaves_para_limpar:
                if chave in st.session_state:
                    del st.session_state[chave]
            
            # 3. Notifica o usuário e reinicia o app
            st.success("Cache limpo! Recarregando dados...")
            st.rerun()

#< ------------------------------------------------------------------------------------------------------------------------------
#< ------------------------------------------------------------------------------------------------------------------------------
#< ------------------------------------------------------------------------------------------------------------------------------




