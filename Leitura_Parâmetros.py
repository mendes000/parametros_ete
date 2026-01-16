import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import time as st_time

# Configuração da página
st.set_page_config(layout="wide")

caminho = Path.cwd() / 'ete_analises.xlsx'

# 1. Função de carregamento com Cache
@st.cache_data
def load_data(file_path):
    try:
        return pd.read_excel(file_path, index_col=0, decimal=',', parse_dates=['Data'], na_values=['-'])
    except:
        # Cria um DF inicial se o arquivo não existir
        return pd.DataFrame(columns=['Local', 'Início', 'Fim', 'ORP', 'T_ORP', 'Obs_ORP', 'pH', 'T_pH', 'Obs_pH', 'STD', 'T_STD', 'Obs_STD', 'Condut', 'T_Condut', 'Obs_Condut', 'OD', 'T_OD', 'Obs_OD'])

df_ete = load_data(caminho)

# 2. Sidebar com Formulário (Evita reruns desnecessários)
st.sidebar.header("Cadastro de Análises")
with st.sidebar.form("input_form"):
    locais = ['Trat. Preliminar','Reator UASB','Filtro Aeróbio']
    selecionar_local = st.selectbox('Escolha o Local', locais)
    
    hora_inicio = st.time_input("Horário de início:", value=datetime.now().time())
    
    st.divider()
    
    # Organização visual melhorada
    def input_row(label):
        col1, col2, col3 = st.columns([1, 1, 1.5])
        v = col1.number_input(f'Valor {label}', value=0.0, format="%.2f")
        t = col2.number_input(f'Temp {label}', value=0.0, format="%.1f")
        o = col3.text_input(f'Obs {label}', key=f"obs_{label}")
        return v, t, o

    v_orp, t_orp, o_orp = input_row("ORP")
    v_ph, t_ph, o_ph = input_row("pH")
    v_std, t_std, o_std = input_row("STD")
    v_cond, t_cond, o_cond = input_row("Condut")
    v_od, t_od, o_od = input_row("OD")

    hora_fim = st.time_input("Horário de fim:", value=(datetime.now() + timedelta(minutes=15)).time())
    
    submit = st.form_submit_button('Adicionar nova Leitura')

# 3. Processamento do Clique
if submit:
    nova_linha = [selecionar_local, hora_inicio, hora_fim, 
                  v_orp, t_orp, o_orp, v_ph, t_ph, o_ph, 
                  v_std, t_std, o_std, v_cond, t_cond, o_cond, 
                  v_od, t_od, o_od]
    
    # Adiciona ao dataframe atual
    df_ete.loc[datetime.now().strftime("%Y-%m-%d %H:%M:%S")] = nova_linha
    
    # Salva no arquivo
    df_ete.to_parquet(caminho)
    
    # LIMPA O CACHE para forçar a leitura do novo arquivo
    st.cache_data.clear()
    
    st.success('Leitura Adicionada com sucesso!')
    st_time.sleep(1)
    st.rerun()

# Exibição
st.subheader("Histórico de Análises")