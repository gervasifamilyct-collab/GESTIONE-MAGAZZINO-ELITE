import streamlit as st
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

# Configurazione Pagina
st.set_page_config(page_title="Elite Estetica - Magazzino", layout="wide")

# --- DATABASE ---
def get_connection():
    conn = sqlite3.connect("magazzino_web.db")
    return conn

def inizializza_db():
    conn = get_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS prodotti 
                 (codice TEXT PRIMARY KEY, nome TEXT, fornitore TEXT, 
                 prezzo_acquisto REAL, prezzo_rivendita REAL, prezzo_pubblico REAL, qty INTEGER)''')
    conn.close()

# --- LOGICA PDF ---
def genera_pdf(df, titolo_listino):
    nome_file = f"{titolo_listino.replace(' ', '_')}.pdf"
    c = canvas.Canvas(nome_file, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, titolo_listino.upper())
    
    y = 750
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "CODICE")
    c.drawString(130, y, "DESCRIZIONE PRODOTTO")
    c.drawString(450, y, "PREZZO")
    c.drawString(520, y, "Q.TÀ")
    c.line(50, y-5, 550, y-5)
    
    y -= 25
    c.setFont("Helvetica", 10)
    for index, row in df.iterrows():
        c.drawString(50, y, str(row['codice']))
        c.drawString(130, y, str(row['nome'])[:45])
        c.drawString(450, y, f"{row['prezzo_pubblico']}€")
        c.drawString(520, y, str(row['qty']))
        y -= 20
        if y < 50:
            c.showPage()
            y = 800
    c.save()
    return nome_file

# --- INTERFACCIA ---
inizializza_db()
st.title("✨ Elite Estetica - Gestionale Web")

# Sidebar per inserimento
with st.sidebar:
    st.header("Nuovo Prodotto")
    with st.form("inserimento_form", clear_on_submit=True):
        cod = st.text_input("Codice")
        nome = st.text_input("Nome/Descrizione")
        forn = st.text_input("Fornitore")
        
        col1, col2 = st.columns(2)
        with col1:
            acq = st.number_input("Prezzo Acq. (€)", min_value=0.0)
            riv = st.number_input("Prezzo Riv. (€)", min_value=0.0)
        with col2:
            pub = st.number_input("Prezzo Pub. (€)", min_value=0.0)
            qta = st.number_input("Quantità", min_value=0, step=1)
            
        submit = st.form_submit_button("Salva nel Magazzino")
        
        if submit and cod and nome:
            conn = get_connection()
            try:
                conn.execute("INSERT INTO prodotti VALUES (?,?,?,?,?,?,?)", (cod, nome, forn, acq, riv, pub, qta))
                conn.commit()
                st.success("Prodotto aggiunto!")
            except:
                st.error("Errore: Codice già esistente")
            conn.close()

# Area Principale: Visualizzazione e Ricerca
conn = get_connection()
df = pd.read_sql_query("SELECT * FROM prodotti", conn)
conn.close()

search = st.text_input("🔍 Cerca prodotto per nome o codice...")
if search:
    df = df[df['nome'].str.contains(search, case=False) | df['codice'].str.contains(search, case=False)]

st.dataframe(df, use_container_width=True, hide_index=True)

# Sezione Stampa
st.divider()
st.subheader("🖨️ Stampa Listino")
col_p1, col_p2 = st.columns([2, 1])
with col_p1:
    titolo_report = st.text_input("Nome del listino per il PDF", "LISTINO ELITE")
with col_p2:
    if st.button("Genera Report PDF"):
        file_pdf = genera_pdf(df, titolo_report)
        with open(file_pdf, "rb") as f:
            st.download_button("Scarica il tuo PDF", f, file_name=file_pdf)