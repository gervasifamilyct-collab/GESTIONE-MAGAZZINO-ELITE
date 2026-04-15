import streamlit as st
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# --- LOGICA DATABASE ---
def inizializza_db():
    conn = sqlite3.connect("magazzino.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prodotti (
            codice TEXT PRIMARY KEY,
            nome TEXT,
            fornitore TEXT,
            prezzo_acquisto REAL,
            prezzo_rivendita REAL,
            prezzo_rivendita_iva REAL,
            prezzo_pubblico REAL,
            quantita INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    return conn

conn = inizializza_db()

# --- FUNZIONI PDF ---
def genera_pdf(titolo, campi_scelti):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, titolo.upper())
    
    y = height - 100
    x_pos = 50
    larghezze = {"Codice": 60, "Nome": 180, "Fornitore": 80, "P. Acquisto": 60, "P. Rivendita": 60, "P. Pubblico": 60, "Quantità": 50}
    
    c.setFont("Helvetica-Bold", 10)
    for campo in campi_scelti:
        c.drawString(x_pos, y, campo)
        x_pos += larghezze.get(campo, 70)
    
    c.line(50, y-5, width-50, y-5)
    y -= 25
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prodotti")
    for p in cursor.fetchall():
        mappa = {"Codice": str(p[0]), "Nome": str(p[1]), "Fornitore": str(p[2]), "P. Acquisto": f"{p[3]}€", 
                 "P. Rivendita": f"{p[4]}€", "P. Pubblico": f"{p[6]}€", "Quantità": str(p[7])}
        x_pos = 50
        c.setFont("Helvetica", 9)
        for campo in campi_scelti:
            c.drawString(x_pos, y, mappa[campo][:30])
            x_pos += larghezze.get(campo, 70)
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
            
    c.save()
    buffer.seek(0)
    return buffer

# --- INTERFACCIA WEB ---
st.set_page_config(page_title="Elite Estetica - Gestionale", layout="wide")
st.title("📦 Elite Estetica - Gestionale Magazzino")

menu = ["Visualizza/Ricerca", "Aggiungi Prodotto", "Stampa PDF"]
scelta = st.sidebar.selectbox("Menu", menu)

if scelta == "Visualizza/Ricerca":
    st.subheader("Inventario Prodotti")
    search = st.text_input("🔍 Cerca per nome o codice")
    df = pd.read_sql_query("SELECT * FROM prodotti", conn)
    
    if search:
        df = df[df['nome'].str.contains(search, case=False) | df['codice'].str.contains(search, case=False)]
    
    st.dataframe(df, use_container_width=True)

    # Eliminazione
    with st.expander("Azioni Rapide (Modifica/Elimina)"):
        cod_mod = st.selectbox("Seleziona Codice Prodotto", df['codice'].tolist() if not df.empty else [])
        if cod_mod:
            if st.button("Elimina Prodotto", type="secondary"):
                conn.execute("DELETE FROM prodotti WHERE codice=?", (cod_mod,))
                conn.commit()
                st.rerun()

elif scelta == "Aggiungi Prodotto":
    st.subheader("Inserimento Nuovo Prodotto")
    with st.form("form_prodotto"):
        col1, col2 = st.columns(2)
        with col1:
            c = st.text_input("Codice Prodotto")
            n = st.text_input("Nome/Descrizione")
            f = st.text_input("Fornitore")
        with col2:
            ac = st.number_input("Prezzo Acquisto (€)", min_value=0.0, step=0.01)
            ri = st.number_input("Prezzo Rivendita (€)", min_value=0.0, step=0.01)
            pu = st.number_input("Prezzo Pubblico (€)", min_value=0.0, step=0.01)
            q = st.number_input("Quantità", min_value=0, step=1)
        
        if st.form_submit_button("Salva Prodotto"):
            iva = round(ri * 1.22, 2)
            try:
                conn.execute('INSERT INTO prodotti VALUES (?,?,?,?,?,?,?,?)', (c, n, f, ac, ri, iva, pu, q))
                conn.commit()
                st.success("Prodotto aggiunto con successo!")
            except:
                st.error("Errore: Il codice esiste già.")

elif scelta == "Stampa PDF":
    st.subheader("Configurazione Report")
    titolo = st.text_input("Titolo Report", "LISTINO PRODOTTI")
    campi = st.multiselect("Campi da includere", ["Codice", "Nome", "Fornitore", "P. Acquisto", "P. Rivendita", "P. Pubblico", "Quantità"], default=["Nome", "P. Pubblico", "Quantità"])
    
    if st.button("Genera Anteprima PDF"):
        pdf_file = genera_pdf(titolo, campi)
        st.download_button(label="⬇️ Scarica Listino PDF", data=pdf_file, file_name=f"{titolo}.pdf", mime="application/pdf")
