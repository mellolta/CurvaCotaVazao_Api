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
import funcoes as fc

# < ------------------------------------------------------------------------------------------------------------------------------
#- Configurações iniciais da página
fc.configuracoes_iniciais()

#- Carrega os dados necessários para essa página
fc.gerenciar_pagina_e_carregar("01_Cota", ["cota"])

#- Título e descrição da página
st.subheader("Cota fora do intervalo da curva chave que está no banco SQL")

#- Verifica se os dados foram carregados na página principal, caso contrário, exibe uma mensagem de erro e interrompe a execução.
if 'cota' not in st.session_state:
    st.error("Dados não carregados.")
    st.stop()

#- DataFrame cota 
cota = st.session_state['cota']

#- Chama a função que retorna o dataframe já filtrado
df_filtrado = fc.menu_filtros_multi(cota)

# < ------------------------------------------------------------------------------------------------------------------------------
# --- BLOCO DE FILTROS DE AVANÇADOS ---
with st.expander("🔍 Filtros Avançados"):
    st.markdown(":gray[Selecione 'Intervalo' para ativar os filtros por coluna.]")
    
    if not df_filtrado.empty:
        # Coluna 1
        c_filtros_1, c_filtros_2 = st.columns(2)
        
        with c_filtros_1:
            # Cada chamada "lapida" o df_filtrado (recursividade)
            df_filtrado = fc.filtro_numerico(df_filtrado, 'Cota', 'Cota (cm)')

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
exibe_cota = df_filtrado.copy()

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Limite de segurança para exibição com formatação condicional

#- Limite de segurança para a exibição das linhas com formatação condicional (Styler)
LIMITE_ESTILO = 1000
total_linhas = len(exibe_cota)

#- Se for maior que o limite, pegamos apenas o topo para o Styler não quebrar
if total_linhas > LIMITE_ESTILO:
    df_para_estilizar = exibe_cota.head(LIMITE_ESTILO)
    aviso_limite = f"⚠️ Exibindo as primeiras {LIMITE_ESTILO} linhas. Use os filtros para ver mais dados."
else:
    df_para_estilizar = exibe_cota
    aviso_limite = None

# < ------------------------------------------------------------------------------------------------------------------------------
#$ Exibe o DataFrame resultante

#- Descrição do DataFrame exibido
st.markdown(f"**Número de registros:** {len(exibe_cota)}")
st.markdown("<br>", unsafe_allow_html=True) #- quebra de linha usando HTML para espaçamento

#- Exibe o DataFrame ocultando o índice e usando a largura total do contêiner 
st.dataframe(
    df_para_estilizar,
    hide_index=True, # Esconde o índice
    width="stretch", # Faz a tabela ocupar toda a largura disponível
    column_config={
        "UR": st.column_config.Column("UR", 
                                      help="Unidade Regional"),
        "Codigo": st.column_config.NumberColumn("Código", format="%d", 
                                                help="Código da estação."),
        "Nome": st.column_config.Column("Nome", help="Nome da estação"),
        "Data": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY", 
                                                help="Data da leitura."),
        "Cota": st.column_config.NumberColumn("Cota (cm)", format="%d", 
                                              help="Cota lida."),
        "Status": st.column_config.Column("Status Cota", 
                                          help="Classificação da cota do dia."),
        "ValidadeInicio": st.column_config.DatetimeColumn("Validade Início", 
            format="DD/MM/YYYY", 
            help="Início da validade da curva chave"),
        "ValidadeFim": st.column_config.DatetimeColumn("Validade Fim", 
            format="DD/MM/YYYY", 
            help="Fim da validade da curva chave"),
        "Lim_inf": st.column_config.NumberColumn("Limite Inf. (cm)", 
            format="%d", 
            help="Limite inferior da curva chave"),
        "Lim_sup": st.column_config.NumberColumn(
            "Limite Sup. (cm)", 
            format="%d", 
            help="Limite superior da curva chave"),
        "Ano": st.column_config.NumberColumn("Ano", format="%d", 
                                             help="Ano da leitura"),
        "Mes": st.column_config.NumberColumn("Mês", format="%d", 
                                             help="Mês da leitura"),
    }
)

#- Exibição de Alerta
if aviso_limite:
    st.info(aviso_limite)

#- Descrição do DataFrame exibido
st.markdown(":small[💡 Colocar o ponteiro do mouse sobre o cabeçalho para obter a descrição das colunas]")            
# < ------------------------------------------------------------------------------------------------------------------------------

