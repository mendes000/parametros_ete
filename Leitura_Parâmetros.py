import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import time as st_time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Monitoramento ETE v2", layout="wide")

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

# --- INICIALIZAÇÃO DO ESTADO (SESSION STATE) ---
if 'hora_ini_val' not in st.session_state:
    st.session_state.hora_ini_val = datetime.now().time()
if 'hora_fim_val' not in st.session_state:
    st.session_state.hora_fim_val = (datetime.now() + timedelta(minutes=15)).time()

# --- INTERFACE LATERAL: INSERÇÃO ---
st.sidebar.header("📋 Nova Leitura")

locais_opcoes = ['Trat. Preliminar', 'Reator UASB', 'Filtro Aeróbio', 'Calha Parshall']
selecionar_local = st.sidebar.selectbox('Escolha o Local', locais_opcoes)

with st.sidebar.form("form_parametros", clear_on_submit=True):
    h_inicio = st.time_input("Horário de início:", value=st.session_state.hora_ini_val)
    st.markdown("---")
    
    v_cloro = 0.0
    if selecionar_local == 'Calha Parshall':
        st.subheader("🧪 Parâmetro Específico")
        v_cloro = st.number_input("Cloro Residual (mg/L)", value=0.0, format="%.2f", key="v_cloro_exclusivo")
        st.markdown("---")

    def trio_inputs(label):
        st.subheader(label)
        c1, c2 = st.columns(2)
        val = c1.number_input(f"Valor {label}", value=0.0, format="%.2f", key=f"v_{label}")
        temp = c2.number_input(f"Temp. {label}", value=0.0, format="%.1f", key=f"t_{label}")
        obs = st.text_input(f"Obs. {label}", key=f"o_{label}")
        st.markdown("---")
        return val, temp, obs

    v_orp, t_orp, o_orp = trio_inputs("ORP")
    v_ph, t_ph, o_ph = trio_inputs("pH")
    v_std, t_std, o_std = trio_inputs("STD")
    v_condut, t_condut, o_condut = trio_inputs("Condutividade")
    v_od, t_od, o_od = trio_inputs("OD")

    h_fim = st.time_input("Horário de fim:", value=st.session_state.hora_fim_val)
    btn_salvar = st.form_submit_button("✅ Salvar Leitura")

# --- LÓGICA DE SALVAMENTO ---
if btn_salvar:
    dados_formatados = {
        'Data_Registro': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Local': str(selecionar_local),
        'Inicio': h_inicio.strftime("%H:%M"),
        'Fim': h_fim.strftime("%H:%M"),
        'Cloro_Residual': float(v_cloro),
        'ORP_Valor': float(v_orp), 'ORP_Temp': float(t_orp), 'ORP_Obs': str(o_orp),
        'pH_Valor': float(v_ph), 'pH_Temp': float(t_ph), 'pH_Obs': str(o_ph),
        'STD_Valor': float(v_std), 'STD_Temp': float(t_std), 'STD_Obs': str(o_std),
        'Condut_Valor': float(v_condut), 'Condut_Temp': float(t_condut), 'Condut_Obs': str(o_condut),
        'OD_Valor': float(v_od), 'OD_Temp': float(t_od), 'OD_Obs': str(o_od)
    }
    df_nova_linha = pd.DataFrame([dados_formatados])
    df_final = pd.concat([df_ete, df_nova_linha], ignore_index=True) if not df_ete.empty else df_nova_linha
    
    try:
        df_final.to_parquet(caminho_parquet, engine='pyarrow', index=False)
        st.cache_data.clear()
        st.session_state.hora_ini_val = datetime.now().time()
        st.session_state.hora_fim_val = (datetime.now() + timedelta(minutes=15)).time()
        st.sidebar.success("✅ Dados salvos!")
        st_time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# --- INTERFACE LATERAL: EXCLUSÃO SELECIONADA ---
st.sidebar.markdown("---")
st.sidebar.subheader("🗑️ Eliminar Registo")

if not df_ete.empty:
    # Criamos uma lista de opções amigável para o utilizador escolher
    opcoes_exclusao = df_ete.apply(lambda x: f"{x.name} | {x['Data_Registro']} | {x['Local']}", axis=1).tolist()
    selecionado_para_excluir = st.sidebar.selectbox("Selecione a linha para apagar:", options=opcoes_exclusao)
    
    # Extraímos o índice original (que está antes do primeiro '|')
    indice_para_excluir = int(selecionado_para_excluir.split(" | ")[0])
    
    if st.sidebar.button("⚠️ Confirmar Eliminação"):
        try:
            # Removemos a linha pelo índice
            df_final = df_ete.drop(indice_para_excluir)
            # Resetamos o index para não haver buracos e salvar corretamente
            df_final = df_final.reset_index(drop=True)
            df_final.to_parquet(caminho_parquet, engine='pyarrow', index=False)
            
            st.cache_data.clear()
            st.sidebar.warning(f"Registo {indice_para_excluir} removido!")
            st_time.sleep(1)
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Erro ao excluir: {e}")
else:
    st.sidebar.info("Sem dados para eliminar.")

# --- ÁREA PRINCIPAL ---
st.title("🧪 Controle de Parâmetros ETE")
if not df_ete.empty:
    # Exibimos a tabela com o índice visível para facilitar a identificação
    st.dataframe(df_ete.iloc[::-1], use_container_width=True)
else:
    st.info("Aguardando registos...")