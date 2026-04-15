import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

# Configurazione Pagina
st.set_page_config(page_title="Gestione Magazzino - Centri Elite", layout="wide")

# Percorso del file per salvare i dati
DATA_FILE = "magazzino.csv"

# Funzione per caricare i dati
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=['Codice', 'Nome', 'Fornitore', 'Acquisto', 'Rivendita', 'Riv_iva', 'Pubblico', 'Qty'])

# Funzione per salvare i dati
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Inizializzazione dati
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- SIDEBAR (SCHEDA PRODOTTO) ---
with st.sidebar:
    st.header("SCHEDA PRODOTTO")
    
    codice = st.text_input("Codice Prodotto:", placeholder="es. PE001")
    nome = st.text_input("Nome/Descrizione Prodotto:")
    fornitore = st.text_input("Fornitore:")
    
    col1, col2 = st.columns(2)
    with col1:
        acquisto = st.number_input("Acquisto (€):", format="%.2f")
        pubblico = st.number_input("Pubblico (€):", format="%.2f")
    with col2:
        rivendita = st.number_input("Rivendita (€):", format="%.2f")
        qty = st.number_input("Q.tà:", step=1)

    riv_iva = rivendita * 1.22
    st.write(f"**Rivendita + IVA: {riv_iva:.2f} €**")
    
    st.markdown("---")
    
    # PULSANTI
    if st.button("✅ Inserisci Nuovo", use_container_width=True):
        nuovo_dato = {
            'Codice': codice, 'Nome': nome, 'Fornitore': fornitore,
            'Acquisto': acquisto, 'Rivendita': rivendita, 
            'Riv_iva': round(riv_iva, 2), 'Pubblico': pubblico, 'Qty': qty
        }
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([nuovo_dato])], ignore_index=True)
        save_data(st.session_state.df)
        st.success("Prodotto Inserito e Salvato!")
        st.rerun()

    if st.button("💾 Salva Modifiche", type="primary", use_container_width=True):
        mask = st.session_state.df['Codice'] == codice
        if mask.any():
            st.session_state.df.loc[mask, ['Nome', 'Fornitore', 'Acquisto', 'Rivendita', 'Riv_iva', 'Pubblico', 'Qty']] = [
                nome, fornitore, acquisto, rivendita, round(riv_iva, 2), pubblico, qty
            ]
            save_data(st.session_state.df)
            st.info("Prodotto Aggiornato!")
            st.rerun()
        else:
            st.error("Codice non trovato.")

    if st.button("🗑️ Elimina Selezionato", use_container_width=True):
        st.session_state.df = st.session_state.df[st.session_state.df['Codice'] != codice]
        save_data(st.session_state.df)
        st.warning(f"Prodotto {codice} eliminato.")
        st.rerun()

    if st.button("📄 STAMPA PDF", use_container_width=True):
        if not st.session_state.df.empty:
            pdf_file = "inventario_elite.pdf"
            c = canvas.Canvas(pdf_file, pagesize=letter)
            c.drawString(100, 750, "INVENTARIO MAGAZZINO - CENTRI ELITE")
            y = 720
            for index, row in st.session_state.df.iterrows():
                c.drawString(100, y, f"{row['Codice']} - {row['Nome']} - Qty: {row['Qty']}")
                y -= 20
            c.save()
            with open(pdf_file, "rb") as f:
                st.download_button("Scarica il PDF", f, file_name=pdf_file)
        else:
            st.error("Il magazzino è vuoto!")

# --- MAIN CONTENT ---
st.title("📦 GESTIONE MAGAZZINO - Centri Elite")

# BARRA DI RICERCA
cerca = st.text_input("🔍 Cerca per nome o codice del prodotto...")

st.subheader("📊 Inventario Attuale")

if cerca:
    display_df = st.session_state.df[
        st.session_state.df['Nome'].str.contains(cerca, case=False, na=False) | 
        st.session_state.df['Codice'].str.contains(cerca, case=False, na=False)
    ]
else:
    display_df = st.session_state.df

if display_df.empty:
    st.info("Nessun prodotto trovato.")
else:
    st.table(display_df)
