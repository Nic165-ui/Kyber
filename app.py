import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Kyber", layout="centered")
st.title("KYBER")

# Connessione sicura al foglio Google
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read().dropna(how='all') 
except:
    st.error("Errore di connessione. Controlla i Secrets e i permessi del foglio.")
    st.stop()

# Recupero dati dell'ultimo inserimento
if not df.empty:
    last_entry = df.iloc[-1]
    last_calorie = int(pd.to_numeric(last_entry.get('Calorie', 2500), errors='coerce') or 2500)
    last_fase = int(pd.to_numeric(last_entry.get('ID_Fase', 1), errors='coerce') or 1)
    last_sgarro = int(pd.to_numeric(last_entry.get('Sgarro', 0), errors='coerce') or 0)
else:
    last_calorie, last_fase, last_sgarro = 2500, 1, 0

# --- INSERIMENTO DATI ---
st.subheader("Inserimento Dati")
data_selezionata = st.date_input("Seleziona il giorno", datetime.now())

peso = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, step=0.1, format="%.1f")
calorie_base = st.number_input("Calorie", value=last_calorie, step=50)

st.write("Sgarro")
col1, col2, col3, col4 = st.columns(4)
sgarro_val = 0
if col1.button("+0"): sgarro_val = 0
if col2.button("+500"): sgarro_val = 500
if col3.button("+1500"): sgarro_val = 1500
if col4.button("+3000"): sgarro_val = 3000

if st.button("SALVA DATI", type="primary"):
    id_fase = last_fase + 1 if calorie_base != last_calorie else last_fase
    smoothing = "Sì" if last_sgarro > 0 else "No"
    
    new_data = pd.DataFrame([{
        "Data": data_selezionata.strftime("%d/%m/%Y"),
        "Peso": peso,
        "Calorie": calorie_base,
        "Sgarro": sgarro_val,
        "Trend_Smoothing": smoothing,
        "ID_Fase": id_fase
    }])
    
    updated_df = pd.concat([df, new_data], ignore_index=True)
    conn.update(data=updated_df)
    st.success(f"Dati salvati!")
    st.rerun()

# --- SEZIONE GRAFICO ---
if not df.empty:
    st.divider()
    df_fase = df[df['ID_Fase'] == last_fase].copy()
    df_clean = df_fase[df_fase['Trend_Smoothing'] == "No"].copy()
    
    if not df_clean.empty:
        st.subheader(f"Andamento Fase {last_fase}")
        df_clean['Peso'] = pd.to_numeric(df_clean['Peso'], errors='coerce')
        df_clean['Data_dt'] = pd.to_datetime(df_clean['Data'], format='%d/%m/%Y')
        df_clean = df_clean.sort_values('Data_dt')

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_clean['Data'],
            y=df_clean['Peso'],
            mode='lines+markers+text',
            text=df_clean['Peso'],
            textposition="top center",
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=10, symbol='circle'),
            textfont=dict(size=12)
        ))
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # --- NUOVA SEZIONE: GESTIONE DATI ---
    st.divider()
    with st.expander("🗑️ Gestione Dati (Elimina o Modifica)"):
        st.write("Ultimi inserimenti effettuati:")
        st.table(df.tail(5)[['Data', 'Peso', 'Calorie', 'Sgarro']])
        
        if st.button("ELIMINA L'ULTIMA RIGA"):
            if len(df) > 0:
                updated_df = df.drop(df.index[-1])
                conn.update(data=updated_df)
                st.warning("Ultima riga eliminata correttamente!")
                st.rerun()
            else:
                st.info("Nessun dato da eliminare.")
