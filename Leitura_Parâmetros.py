import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime, time, timedelta
import time as st_time


caminho = Path.cwd()
df_ete = pd.read_excel(caminho/'ete_analises.xlsx',
                       index_col=0,
                       decimal=',',
                       parse_dates=['Data'],
                       na_values=['-'])

colunas = list(df_ete.columns)

data_hoje = datetime.now()
locais = ['Trat. Preliminar','Reator UASB','Filtro Aeróbio','Reator UASB']
selecionar_local = st.sidebar.selectbox('Escolha o Local', locais)

hora_inicio = st.sidebar.time_input("Horário de início:", value=datetime.now())

col1, col2, col3 = st.sidebar.columns(3)
# ORP
valor_orp = col1.text_input('Valor OPR',0)
temp_orp = col2.text_input('Temp. OPR',0)
obs_orp = col3.text_input('Obs. OPR')

# ORP
valor_ph = col1.text_input('Valor pH',0)
temp_ph = col2.text_input('Temp. pH',0)
obs_ph = col3.text_input('Obs. pH')

# Sólidos Totais Dissolvidos
valor_std = col1.text_input('Valor STD',0)
temp_std = col2.text_input('Temp. STD',0)
obs_std = col3.text_input('Obs. STD')

# Condutibilidade
valor_condut = col1.text_input('Valor condut.',0)
temp_condut = col2.text_input('Temp. condut.',0)
obs_condut = col3.text_input('Obs. condut.')

# Oxigênio Dissolvido
valor_od = col1.text_input('Valor OD',0)
temp_od = col2.text_input('Temp. OD',0)
obs_od = col3.text_input('Obs. OD')

hora_fim = st.sidebar.time_input("Horário de fim:", value=datetime.now() + timedelta(hours=0, minutes=15))

if st.sidebar.button('Adicionar nova Leitura'):
    lista_adicionar = [selecionar_local,
                       hora_inicio,
                       hora_fim,
                       float(valor_orp), float(temp_orp), str(obs_orp),
                       float(valor_ph), float(temp_ph), str(obs_ph),
                       float(valor_std), float(temp_std), str(obs_std),
                       float(valor_condut), float(temp_condut), str(obs_condut),
                       float(valor_od), float(temp_od), str(obs_od)]
    df_ete.loc[str(data_hoje)] = lista_adicionar  # na leitura do df_vendas foi colocado a coluna 'data' como índice
                                                    # com isso, qdo ele busca a coluna com data e hora atual e não encontra
                                                    # ele cria uma nova, adicionando os demais itens listados na lista_adicionar
    df_ete.to_excel(caminho/'ete_analises.xlsx')
    
    # Mensagem de sucesso
    placeholder = st.empty() # Cria um espaço vazio
    placeholder.success('Leitura Adicionada') # Exibe o sucesso no espaço
    st_time.sleep(1) # Aguarda 1 segundos
    placeholder.empty() # Remove a mensagem (limpa o espaço)


st.dataframe(df_ete)