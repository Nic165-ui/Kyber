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

if st.button("SALVA DATI"):
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
    st.success(f"Dati salvati per il giorno {data_selezionata.strftime('%d/%m/%Y')}!")
    st.rerun()

# --- SEZIONE GRAFICO AVANZATO ---
if not df.empty:
    st.divider()
    # Filtro dati fase attuale e pulizia sgarri
    df_fase = df[df['ID_Fase'] == last_fase].copy()
    df_clean = df_fase[df_fase['Trend_Smoothing'] == "No"].copy()
    
    if not df_clean.empty:
        st.subheader(f"Andamento Fase {last_fase}")
        
        # Assicuriamoci che i dati siano nel formato corretto
        df_clean['Peso'] = pd.to_numeric(df_clean['Peso'], errors='coerce')
        # Ordiniamo per data per evitare linee "incrociate"
        df_clean['Data_dt'] = pd.to_datetime(df_clean['Data'], format='%d/%m/%Y')
        df_clean = df_clean.sort_values('Data_dt')

        # Creazione grafico con Plotly
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_clean['Data'],
            y=df_clean['Peso'],
            mode='lines+markers+text', # Linea + Pallini + Testo
            text=df_clean['Peso'],      # Il numero da mostrare
            textposition="top center", # Posizione del numero
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=10, symbol='circle'),
            textfont=dict(size=12, color="white" if st.get_option("theme.base") == "dark" else "black")
        ))

        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Data",
            yaxis_title="Peso (kg)",
            hovermode="x unified",
            showlegend=False,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # LOGICA ALERT STALLO
        if len(df_clean) >= 21:
            y_vals = df_clean['Peso'].values
            x_vals = np.arange(len(y_vals))
            m, b = np.polyfit(x_vals, y_vals, 1)
            if abs(m) < 0.005: 
                st.error("🚨 Stallo rilevato (21 giorni), contatta il nutrizionista")
            else:
                st.info("📉 Il trend è in movimento. Continua così!")
