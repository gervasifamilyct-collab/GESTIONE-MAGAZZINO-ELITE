import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestione Magazzino Elite", layout="wide")
st.title("📦 Gestione Magazzino - Centri Elite")

# Inizializzazione dati
if 'magazzino' not in st.session_state:
    st.session_state.magazzino = pd.DataFrame(columns=["Prodotto", "Quantità", "Centro"])

# Sezione Inserimento
with st.expander("➕ Aggiungi Nuovo Prodotto"):
    col1, col2, col3 = st.columns(3)
    with col1:
        prod = st.text_input("Nome Prodotto")
    with col2:
        qta = st.number_input("Quantità", min_value=1, step=1)
    with col3:
        centro = st.selectbox("Centro", ["Catania", "Scordia", "Altro"])
    
    if st.button("Salva"):
        nuovo_dato = pd.DataFrame([[prod, qta, centro]], columns=["Prodotto", "Quantità", "Centro"])
        st.session_state.magazzino = pd.concat([st.session_state.magazzino, nuovo_dato], ignore_index=True)
        st.success("Prodotto aggiunto!")

# Visualizzazione e Azioni
st.subheader("📋 Inventario Attuale")
if not st.session_state.magazzino.empty:
    for index, row in st.session_state.magazzino.iterrows():
        cols = st.columns([3, 2, 2, 1, 1])
        cols[0].write(row["Prodotto"])
        cols[1].write(f"Quantità: {row['Quantità']}")
        cols[2].write(f"Sede: {row['Centro']}")
        
        # Tasto Elimina
        if cols[3].button("🗑️", key=f"del_{index}"):
            st.session_state.magazzino = st.session_state.magazzino.drop(index).reset_index(drop=True)
            st.rerun()
            
        # Tasto Modifica (Esempio rapido)
        if cols[4].button("✏️", key=f"edit_{index}"):
            st.info(f"Per modificare '{row['Prodotto']}', usa la sezione sopra e poi elimina questa riga.")
else:
    st.info("Il magazzino è vuoto.")
