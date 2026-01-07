import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
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

# Interfaccia di Inserimento
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

if st.button("SALVA DATI"):
    id_fase = last_fase + 1 if calorie_base != last_calorie else last_fase
    smoothing = "Sì" if last_sgarro > 0 else "No"
    
    new_data = pd.DataFrame([{
        "Data": datetime.now().strftime("%d/%m/%Y"),
        "Peso": peso,
        "Calorie": calorie_base,
        "Sgarro": sgarro_val,
        "Trend_Smoothing": smoothing,
        "ID_Fase": id_fase
    }])
    
    updated_df = pd.concat([df, new_data], ignore_index=True)
    conn.update(data=updated_df)
    st.success("Dati salvati!")
    st.rerun()

# --- SEZIONE ANALISI E GRAFICO ---
if not df.empty:
    st.divider()
    # Filtriamo i dati della fase attuale e puliamo dai "Sì" del Trend Smoothing
    df_fase = df[df['ID_Fase'] == last_fase].copy()
    df_clean = df_fase[df_fase['Trend_Smoothing'] == "No"].copy()
    
    if not df_clean.empty:
        st.subheader(f"Andamento Fase {last_fase}")
        # Assicuriamoci che il peso sia visto come numero
        df_clean['Peso'] = pd.to_numeric(df_clean['Peso'], errors='coerce')
        st.line_chart(df_clean.set_index('Data')['Peso'])
        
        # LOGICA ALERT STALLO (21 giorni di dati puliti)
        if len(df_clean) >= 21:
            y = df_clean['Peso'].values
            x = np.arange(len(y))
            # Calcolo della pendenza (m)
            m, b = np.polyfit(x, y, 1)
            
            # Se la variazione è minima (quasi piatta), scatta l'alert
            if abs(m) < 0.005: 
                st.error("🚨 Stallo rilevato (21 giorni), contatta il nutrizionista")
            else:
                st.info("📉 Il trend è in movimento. Continua così!")
