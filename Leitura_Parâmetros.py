import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import time as st_time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Monitoramento ETE v2", layout="wide")

caminho_parquet = Path.cwd() / 'ete_analises.parquet'

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados(caminho):
    if caminho.exists():
        try:
            return pd.read_parquet(caminho)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

df_ete = carregar_dados(caminho_parquet)

# --- INTERFACE LATERAL (ENTRADA) ---
st.sidebar.header("📋 Nova Leitura")

# O clear_on_submit limpa os textos, o rerun reseta os números para o 'value=0.0'
with st.sidebar.form("form_parametros", clear_on_submit=True):
    locais = ['Trat. Preliminar', 'Reator UASB', 'Filtro Aeróbio', 'Calha Parshall']
    selecionar_local = st.selectbox('Escolha o Local', locais)
    
    hora_atual = datetime.now()
    h_inicio = st.time_input("Horário de início:", value=hora_atual.time())
    
    st.markdown("---")
    
    def trio_inputs(label):
        st.subheader(label)
        c1, c2 = st.columns(2)
        val = c1.number_input(f"Valor {label}", value=0.0, format="%.2f", key=f"v_{label}")
        temp = c2.number_input(f"Temp. {label}", value=0.0, format="%.1f", key=f"t_{label}")
        obs = st.text_input(f"Obs. {label}", key=f"o_{label}")
        st.markdown("---")
        return val, temp, obs

    # Atribuição correta das variáveis
    v_orp, t_orp, o_orp = trio_inputs("ORP")
    v_ph, t_ph, o_ph = trio_inputs("pH")
    v_std, t_std, o_std = trio_inputs("STD")
    v_condut, t_condut, o_condut = trio_inputs("Condutividade") # Ajustado o nome da variável
    v_od, t_od, o_od = trio_inputs("OD")

    h_fim = st.time_input("Horário de fim:", value=(hora_atual + timedelta(minutes=15)).time())
    
    # O BOTÃO DEVE ESTAR DENTRO DO 'WITH' (identado)
    btn_salvar = st.form_submit_button("✅ Salvar Leitura")

# --- LÓGICA DE SALVAMENTO (FORA DO WITH) ---
if btn_salvar:
    dados_formatados = {
        'Data_Registro': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Local': str(selecionar_local),
        'Inicio': h_inicio.strftime("%H:%M"),
        'Fim': h_fim.strftime("%H:%M"),
        'ORP_Valor': float(v_orp), 'ORP_Temp': float(t_orp), 'ORP_Obs': str(o_orp),
        'pH_Valor': float(v_ph), 'pH_Temp': float(t_ph), 'pH_Obs': str(o_ph),
        'STD_Valor': float(v_std), 'STD_Temp': float(t_std), 'STD_Obs': str(o_std),
        'Condut_Valor': float(v_condut), 'Condut_Temp': float(t_condut), 'Condut_Obs': str(o_condut),
        'OD_Valor': float(v_od), 'OD_Temp': float(t_od), 'OD_Obs': str(o_od)
    }
    
    df_nova_linha = pd.DataFrame([dados_formatados])
    
    if df_ete.empty:
        df_final = df_nova_linha
    else:
        df_final = pd.concat([df_ete, df_nova_linha], ignore_index=True)
    
    try:
        df_final.to_parquet(caminho_parquet, engine='pyarrow', index=False)
        st.cache_data.clear()
        st.sidebar.success("✅ Dados salvos com sucesso!")
        st_time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# --- ÁREA PRINCIPAL ---
st.title("🧪 Controle de Parâmetros ETE")

if not df_ete.empty:
    filtro_local = st.multiselect("Filtrar por Local:", options=df_ete['Local'].unique(), default=df_ete['Local'].unique())
    df_filtrado = df_ete[df_ete['Local'].isin(filtro_local)]
    
    # Exibe a tabela invertida (mais recentes no topo)
    st.dataframe(df_filtrado.iloc[::-1], use_container_width=True, hide_index=True)
    
    import io
    buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_ete.to_excel(writer, index=False, sheet_name='Analises')
        st.download_button(label="📥 Baixar Excel", data=buffer.getvalue(), 
                           file_name="relatorio_ete.xlsx", mime="application/vnd.ms-excel")
    except:
        st.info("Para exportar, instale: pip install xlsxwriter")
else:
    st.info("Aguardando registros...")