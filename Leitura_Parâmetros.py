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
            df = pd.read_parquet(caminho)
            if 'Cloro_Residual' not in df.columns:
                df['Cloro_Residual'] = 0.0
            if 'Data_Coleta' not in df.columns:
                df['Data_Coleta'] = pd.to_datetime(df['Data_Registro']).dt.date.astype(str)
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

df_ete = carregar_dados(caminho_parquet)

# --- ESTADOS DE SESSÃO (SESSION STATE) ---
if 'modo_edicao' not in st.session_state:
    st.session_state.modo_edicao = False
if 'index_edicao' not in st.session_state:
    st.session_state.index_edicao = None
if 'data_val' not in st.session_state:
    st.session_state.data_val = datetime.now().date()
if 'hora_ini_val' not in st.session_state:
    st.session_state.hora_ini_val = datetime.now().time()
if 'hora_fim_val' not in st.session_state:
    st.session_state.hora_fim_val = (datetime.now() + timedelta(minutes=15)).time()

# --- INTERFACE LATERAL: GESTÃO ---
st.sidebar.header("⚙️ Gestão de Registros")

if not df_ete.empty:
    with st.sidebar.expander("Modificar ou Excluir"):
        # Formatação da data na lista de seleção para DD/MM/YY
        opcoes_lista = df_ete.apply(
            lambda x: f"{x.name} | {datetime.strptime(x['Data_Coleta'], '%Y-%m-%d').strftime('%d/%m/%y')} | {x['Local']}", 
            axis=1
        ).tolist()
        selecionado = st.selectbox("Selecione o registro:", options=opcoes_lista)
        idx_selecionado = int(selecionado.split(" | ")[0])

        col_edit, col_del = st.columns(2)
        
        if col_edit.button("📝 Editar"):
            st.session_state.modo_edicao = True
            st.session_state.index_edicao = idx_selecionado
            st.sidebar.info(f"Editando registro {idx_selecionado}")

        if col_del.button("🗑️ Excluir"):
            df_final = df_ete.drop(idx_selecionado).reset_index(drop=True)
            df_final.to_parquet(caminho_parquet, engine='pyarrow', index=False)
            st.cache_data.clear()
            st.rerun()

# --- FORMULÁRIO DE ENTRADA / EDIÇÃO ---
st.sidebar.header("📋 Formulário")

val_default = df_ete.loc[st.session_state.index_edicao] if st.session_state.modo_edicao else None

locais_opcoes = ['Trat. Preliminar', 'Reator UASB', 'Filtro Aeróbio', 'Calha Parshall']
idx_local = locais_opcoes.index(val_default['Local']) if val_default is not None and val_default['Local'] in locais_opcoes else 0
selecionar_local = st.sidebar.selectbox('Escolha o Local', locais_opcoes, index=idx_local)

with st.sidebar.form("form_parametros", clear_on_submit=True):
    
    # DATA NO FORMATO DD/MM/YYYY NO INPUT
    if val_default is not None:
        d_edit = datetime.strptime(str(val_default['Data_Coleta']), "%Y-%m-%d").date()
    else:
        d_edit = st.session_state.data_val
    
    data_coleta = st.date_input("Data da Coleta:", value=d_edit, format="DD/MM/YYYY")

    h_ini_edit = datetime.strptime(val_default['Inicio'], "%H:%M").time() if val_default is not None else st.session_state.hora_ini_val
    h_inicio = st.time_input("Horário de início:", value=h_ini_edit)
    
    st.markdown("---")
    
    # Parâmetros
    v_cloro_init = float(val_default.get('Cloro_Residual', 0.0)) if val_default is not None else 0.0
    v_cloro = 0.0
    if selecionar_local == 'Calha Parshall':
        v_cloro = st.number_input("Cloro Residual (mg/L)", value=v_cloro_init, format="%.2f")

    def trio_inputs(label, prefix):
        st.subheader(label)
        c1, c2 = st.columns(2)
        v_val = float(val_default[f'{prefix}_Valor']) if val_default is not None else 0.0
        v_tmp = float(val_default[f'{prefix}_Temp']) if val_default is not None else 0.0
        v_obs = str(val_default[f'{prefix}_Obs']) if val_default is not None else ""
        
        val = c1.number_input(f"Valor {label}", value=v_val, format="%.2f", key=f"v_{label}")
        temp = c2.number_input(f"Temp. {label}", value=v_tmp, format="%.1f", key=f"t_{label}")
        obs = st.text_input(f"Obs. {label}", value=v_obs, key=f"o_{label}")
        return val, temp, obs

    v_orp, t_orp, o_orp = trio_inputs("ORP", "ORP")
    v_ph, t_ph, o_ph = trio_inputs("pH", "pH")
    v_std, t_std, o_std = trio_inputs("STD", "STD")
    v_condut, t_condut, o_condut = trio_inputs("Condutividade", "Condut")
    v_od, t_od, o_od = trio_inputs("OD", "OD")

    h_fim_edit = datetime.strptime(val_default['Fim'], "%H:%M").time() if val_default is not None else st.session_state.hora_fim_val
    h_fim = st.time_input("Horário de fim:", value=h_fim_edit)
    
    texto_botao = "💾 Salvar Alterações" if st.session_state.modo_edicao else "✅ Salvar Leitura"
    btn_salvar = st.form_submit_button(texto_botao)

# --- LÓGICA DE SALVAMENTO ---
if btn_salvar:
    dados_novos = {
        'Data_Registro': val_default['Data_Registro'] if st.session_state.modo_edicao else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Data_Coleta': str(data_coleta),
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

    if st.session_state.modo_edicao:
        for col, val in dados_novos.items():
            df_ete.at[st.session_state.index_edicao, col] = val
        df_final = df_ete
        st.session_state.modo_edicao = False
        st.session_state.index_edicao = None
    else:
        df_nova_linha = pd.DataFrame([dados_novos])
        df_final = pd.concat([df_ete, df_nova_linha], ignore_index=True)

    df_final.to_parquet(caminho_parquet, engine='pyarrow', index=False)
    st.cache_data.clear()
    st.rerun()

if st.session_state.modo_edicao:
    if st.sidebar.button("❌ Cancelar Edição"):
        st.session_state.modo_edicao = False
        st.session_state.index_edicao = None
        st.rerun()

# --- VISUALIZAÇÃO ---
st.title("🧪 Controle de Parâmetros ETE")
if not df_ete.empty:
    df_visualizacao = df_ete.copy()
    # Converte a data de 'YYYY-MM-DD' para 'DD/MM/YYYY' apenas para exibição
    df_visualizacao['Data_Coleta'] = pd.to_datetime(df_visualizacao['Data_Coleta']).dt.strftime('%d/%m/%Y')
    
    st.dataframe(df_visualizacao.iloc[::-1], use_container_width=True)
else:
    st.info("Nenhum registro encontrado.")