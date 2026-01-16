import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import time as st_time

st.set_page_config(page_title="Monitoramento ETE", layout="wide")

caminho_parquet = Path.cwd() / 'ete_analises.parquet'

@st.cache_data
def carregar_dados(caminho):
    if caminho.exists():
        try:
            return pd.read_parquet(caminho)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

df_ete = carregar_dados(caminho_parquet)

# --- Formulário ---
with st.sidebar.form("novo_registro"):
    st.header("Entrada de Dados")
    local = st.selectbox('Local', ['Trat. Preliminar', 'Reator UASB', 'Filtro Aeróbio','Calha Parshall'])
    h_ini = st.time_input("Início", value=datetime.now().time())
    
    # Inputs numéricos explícitos
    v_ph = st.number_input('pH', value=7.0, step=0.1)
    v_od = st.number_input('OD', value=0.0, step=0.1)
    v_orp = st.number_input('ORP', value=0.0, step=1.0)
    
    h_fim = st.time_input("Fim", value=(datetime.now() + timedelta(minutes=15)).time())
    
    salvar = st.form_submit_button("Salvar")

if salvar:
    # 1. Criar dicionário com tipos forçados
    novo_dado = {
        'Data_Registro': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Local': str(local),
        'Inicio': h_ini.strftime("%H:%M"),
        'Fim': h_fim.strftime("%H:%M"),
        'pH': float(v_ph),
        'OD': float(v_od),
        'ORP': float(v_orp)
    }
    
    # 2. Transformar em DataFrame
    df_nova_linha = pd.DataFrame([novo_dado])
    
    # 3. Concatenar (Garante que se df_ete estiver vazio, ele assume a estrutura da nova linha)
    if df_ete.empty:
        df_final = df_nova_linha
    else:
        df_final = pd.concat([df_ete, df_nova_linha], ignore_index=True)
    
    # 4. Salvar com tratamento de erro
    try:
        # Forçamos a conversão para strings/floats antes de salvar para evitar o ArrowTypeError
        df_final.to_parquet(caminho_parquet, engine='pyarrow', index=False)
        st.cache_data.clear()
        st.success("Salvo com sucesso!")
        st_time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# --- Exibição ---
st.title("Histórico ETE")
if not df_ete.empty:
    st.dataframe(df_ete, use_container_width=True)
else:
    st.write("Aguardando registros...")