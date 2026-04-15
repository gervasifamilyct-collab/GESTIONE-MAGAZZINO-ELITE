import streamlit as st
import pandas as pd
import os

# Configurazione Pagina
st.set_page_config(page_title="Gestione Magazzino - Centri Elite", layout="wide")

# File per non perdere i dati (Database locale)
DATA_FILE = "magazzino_elite.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=['Codice', 'Nome', 'Fornitore', 'Acquisto', 'Rivendita', 'Riv_iva', 'Pubblico', 'Qty'])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Inizializzazione sessione
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- FUNZIONE PER SVUOTARE I CAMPI ---
def reset_campi():
    st.session_state["codice_input"] = ""
    st.session_state["nome_input"] = ""
    st.session_state["fornitore_input"] = ""
    st.session_state["acquisto_input"] = 0.0
    st.session_state["rivendita_input"] = 0.0
    st.session_state["pubblico_input"] = 0.0
    st.session_state["qty_input"] = 0

# --- SIDEBAR ---
with st.sidebar:
    st.header("SCHEDA PRODOTTO")
    
    # Usiamo le "key" per poter resettare i campi
    codice = st.text_input("Codice Prodotto:", key="codice_input")
    nome = st.text_input("Nome/Descrizione Prodotto:", key="nome_input")
    fornitore = st.text_input("Fornitore:", key="fornitore_input")
    
    col1, col2 = st.columns(2)
    with col1:
        acquisto = st.number_input("Acquisto (€):", format="%.2f", key="acquisto_input")
        pubblico = st.number_input("Pubblico (€):", format="%.2f", key="pubblico_input")
    with col2:
        rivendita = st.number_input("Rivendita (€):", format="%.2f", key="rivendita_input")
        qty = st.number_input("Q.tà:", step=1, key="qty_input")

    riv_iva = rivendita * 1.22
    st.write(f"**Rivendita + IVA: {riv_iva:.2f} €**")
    
    st.markdown("---")
    
    # TASTO INSERISCI
    if st.button("✅ Inserisci Nuovo", use_container_width=True):
        if codice and nome:
            nuovo_prodotto = {
                'Codice': codice, 'Nome': nome, 'Fornitore': fornitore,
                'Acquisto': acquisto, 'Rivendita': rivendita, 
                'Riv_iva': round(riv_iva, 2), 'Pubblico': pubblico, 'Qty': qty
            }
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([nuovo_prodotto])], ignore_index=True)
            save_data(st.session_state.df)
            
            # AZIONE DI RESET
            reset_campi()
            st.success("Prodotto aggiunto!")
            st.rerun() # Ricarica la pagina con i campi puliti
        else:
            st.error("Inserisci almeno Codice e Nome!")

# --- PARTE CENTRALE ---
st.title("📦 GESTIONE MAGAZZINO - Centri Elite")

# BARRA DI RICERCA (Richiesta!)
cerca = st.text_input("🔍 Cerca prodotto per Nome o Codice...")

st.subheader("📊 Inventario Attuale")

# Filtro ricerca
if cerca:
    df_mostra = st.session_state.df[
        st.session_state.df['Nome'].str.contains(cerca, case=False, na=False) | 
        st.session_state.df['Codice'].str.contains(cerca, case=False, na=False)
    ]
else:
    df_mostra = st.session_state.df

st.table(df_mostra)
