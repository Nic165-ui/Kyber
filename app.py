import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Kyber", layout="centered")
st.title("KYBER")

# Connessione sicura
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read().dropna(how='all') # Ignora le righe completamente vuote
except:
    st.error("Errore di connessione. Controlla i Secrets.")
    st.stop()

# Recupero dati con "protezione" contro i valori vuoti
if not df.empty:
    last_entry = df.iloc[-1]
    # Usiamo pd.to_numeric per evitare errori se la cella è vuota o scritta male
    last_calorie = int(pd.to_numeric(last_entry.get('Calorie', 2500), errors='coerce') or 2500)
    last_fase = int(pd.to_numeric(last_entry.get('ID_Fase', 1), errors='coerce') or 1)
    last_sgarro = int(pd.to_numeric(last_entry.get('Sgarro', 0), errors='coerce') or 0)
else:
    last_calorie, last_fase, last_sgarro = 2500, 1, 0

# Interfaccia Inserimento
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

# Grafico
if not df.empty:
    st.divider()
    df_clean = df[df['Trend_Smoothing'] == "No"]
    if not df_clean.empty:
        st.subheader(f"Andamento Fase {last_fase}")
        st.line_chart(df_clean.set_index('Data')['Peso'])
