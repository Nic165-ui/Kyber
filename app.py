import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Kyber", layout="centered")
st.title("KYBER")

# 1. Connessione al Database (Google Sheets)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
except Exception as e:
    st.error("Errore di connessione al foglio Google. Controlla i Secrets.")
    st.stop()

# Recupero dati dell'ultimo inserimento per pre-compilare
if not df.empty:
    last_entry = df.iloc[-1]
    last_calorie = int(last_entry['Calorie'])
    last_fase = int(last_entry['ID_Fase'])
    last_sgarro = int(last_entry['Sgarro'])
else:
    last_calorie, last_fase, last_sgarro = 2500, 1, 0

# 2. Interfaccia di Inserimento
st.subheader("Inserimento del Giorno")
peso = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, step=0.1, format="%.1f")
calorie_base = st.number_input("Calorie", value=last_calorie, step=50)

st.write("Sgarro")
col1, col2, col3, col4 = st.columns(4)
sgarro_val = 0
if col1.button("+0"): sgarro_val = 0
if col2.button("+500"): sgarro_val = 500
if col3.button("+1500"): sgarro_val = 1500
if col4.button("+3000"): sgarro_val = 3000

# 3. Logica di Salvataggio
if st.button("SALVA DATI"):
    # Cambio Fase: se le calorie cambiano, ID_Fase aumenta
    id_fase = last_fase + 1 if calorie_base != last_calorie else last_fase
    
    # Trend Smoothing: se ieri c'era sgarro, oggi il dato è "Sì" (da ignorare)
    smoothing = "Sì" if last_sgarro > 0 else "No"
    
    new_data = pd.DataFrame([{
        "Data": datetime.now().strftime("%d/%m/%Y"),
        "Peso": peso,
        "Calorie": calorie_base,
        "Sgarro": sgarro_val,
        "Trend_Smoothing": smoothing,
        "ID_Fase": id_fase
    }])
    
    # Unione dati e salvataggio
    updated_df = pd.concat([df, new_data], ignore_index=True)
    conn.update(data=updated_df)
    st.success(f"Dati salvati! Fase attuale: {id_fase}")
    st.rerun()

# 4. Visualizzazione Grafico e Alert
if not df.empty:
    st.divider()
    st.subheader(f"Andamento Fase {last_fase}")
    
    # Filtriamo i dati per la fase attuale e applichiamo il Trend Smoothing
    df_fase = df[df['ID_Fase'] == last_fase].copy()
    df_clean = df_fase[df_fase['Trend_Smoothing'] == "No"]
    
    if not df_clean.empty:
        st.line_chart(df_clean.set_index('Data')['Peso'])
        
        # Logica Alert Stallo (21 giorni)
        if len(df_clean) >= 21:
            # Calcolo pendenza m con regressione lineare semplice
            y = df_clean['Peso'].values
            x = np.arange(len(y))
            m, b = np.polyfit(x, y, 1)
            
            # Se la pendenza m è quasi zero (stallo)
            if abs(m) < 0.005: 
                st.error("🚨 Stallo (21 giorni), contatta il nutrizionista")
