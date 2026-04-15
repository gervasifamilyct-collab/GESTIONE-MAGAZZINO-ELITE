import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

# Configurazione pagina per layout largo (stile dashboard)
st.set_page_config(layout="wide", page_title="Gestione Magazzino Elite")

# Titolo principale
st.title("📦 SCHEDA PRODOTTO - Centri Elite")

# Inizializzazione del database (se non esiste)
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        "Codice", "Nome", "Fornitore", "Acquisto", "Rivendita", "Riv_iva", "Pubblico", "Qty"
    ])

# --- BARRA LATERALE (SCHEDA PRODOTTO) ---
with st.sidebar:
    st.header("📋 DATI PRODOTTO")
    
    codice = st.text_input("Codice Prodotto:")
    nome = st.text_input("Nome/Descrizione Prodotto:")
    fornitore = st.text_input("Fornitore:")
    
    col1, col2 = st.columns(2)
    with col1:
        acquisto = st.number_input("Acquisto (€):", format="%.2f")
        pubblico = st.number_input("Pubblico (€):", format="%.2f")
    with col2:
        rivendita = st.number_input("Rivendita (€):", format="%.2f")
        qty = st.number_input("Q.tà:", step=1)
    
    # Calcolo automatico IVA (22%)
    riv_iva = rivendita * 1.22
    st.write(f"**Rivendita + IVA:** {riv_iva:.2f} €")

    st.write("---")
    
    # Pulsanti in colonna
    if st.button("✅ Inserisci Nuovo", use_container_width=True):
        nuovo_prodotto = {
            "Codice": codice, "Nome": nome, "Fornitore": fornitore,
            "Acquisto": acquisto, "Rivendita": rivendita, 
            "Riv_iva": round(riv_iva, 2), "Pubblico": pubblico, "Qty": qty
        }
        st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([nuovo_prodotto])], ignore_index=True)
        st.success("Prodotto inserito!")

    if st.button("🗑️ Elimina Selezionato", use_container_width=True):
        st.warning("Seleziona il prodotto dalla tabella a destra (prossima versione)")

    if st.button("📄 STAMPA PDF", use_container_width=True):
        st.info("Funzione PDF in preparazione...")

# --- AREA PRINCIPALE (TABELLA INVENTARIO) ---
st.subheader("📊 Inventario Attuale")

if not st.session_state.db.empty:
    # Barra di ricerca
    ricerca = st.text_input("🔍 Cerca per nome o codice...")
    df_mostra = st.session_state.db
    if ricerca:
        df_mostra = df_mostra[df_mostra['Nome'].str.contains(ricerca, case=False) | df_mostra['Codice'].str.contains(ricerca, case=False)]
    
    # Visualizzazione tabella (simile alla tua foto)
    st.dataframe(df_mostra, use_container_width=True, hide_index=True)
else:
    st.info("Il magazzino è vuoto. Usa la scheda a sinistra per aggiungere prodotti.")
