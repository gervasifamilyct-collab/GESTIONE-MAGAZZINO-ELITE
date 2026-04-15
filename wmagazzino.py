import streamlit as st
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# --- DATABASE ---
def get_connection():
    conn = sqlite3.connect("magazzino.db", check_same_thread=False)
    return conn

conn = get_connection()
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS prodotti (
        codice TEXT PRIMARY KEY, nome TEXT, fornitore TEXT,
        prezzo_acquisto REAL, prezzo_rivendita REAL,
        prezzo_rivendita_iva REAL, prezzo_pubblico REAL, quantita INTEGER DEFAULT 0
    )
''')
conn.commit()

# --- FUNZIONI DI SERVIZIO ---
def reset_campi():
    st.session_state.form_data = {
        "codice": "", "nome": "", "fornitore": "", 
        "acquisto": 0.0, "rivendita": 0.0, "pubblico": 0.0, "qty": 0
    }

def genera_pdf(titolo, campi_scelti):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, titolo.upper())
    
    y = height - 80
    x_pos = 50
    larghezze = {"Codice": 70, "Nome": 150, "Fornitore": 80, "P. Acquisto": 60, "P. Rivendita": 60, "P. Pubblico": 60, "Quantità": 50}
    
    c.setFont("Helvetica-Bold", 10)
    for campo in campi_scelti:
        c.drawString(x_pos, y, campo)
        x_pos += larghezze.get(campo, 70)
    
    c.line(50, y-5, width-50, y-5)
    y -= 25
    
    cursor.execute("SELECT * FROM prodotti")
    for p in cursor.fetchall():
        if y < 50:
            c.showPage()
            y = height - 50
        mappa = {"Codice": str(p[0]), "Nome": str(p[1]), "Fornitore": str(p[2]), "P. Acquisto": f"{p[3]}€", 
                 "P. Rivendita": f"{p[4]}€", "P. Pubblico": f"{p[6]}€", "Quantità": str(p[7])}
        x_pos = 50
        c.setFont("Helvetica", 9)
        for campo in campi_scelti:
            c.drawString(x_pos, y, str(mappa[campo])[:25])
            x_pos += larghezze.get(campo, 70)
        y -= 20
    c.save()
    buffer.seek(0)
    return buffer

# --- INTERFACCIA ---
st.set_page_config(page_title="Elite Estetica", layout="wide")

if 'form_data' not in st.session_state:
    reset_campi()

st.sidebar.header("🛡️ SCHEDA PRODOTTO")

with st.sidebar:
    is_edit = st.session_state.form_data["codice"] != ""
    
    # Input Campi
    cod = st.text_input("Codice Prodotto", value=st.session_state.form_data["codice"], disabled=is_edit)
    nom = st.text_input("Nome/Descrizione", value=st.session_state.form_data["nome"])
    forn = st.text_input("Fornitore", value=st.session_state.form_data["fornitore"])
    
    col_a, col_b = st.columns(2)
    acq = col_a.number_input("Acquisto (€)", value=float(st.session_state.form_data["acquisto"]), step=0.01)
    riv = col_b.number_input("Rivendita (€)", value=float(st.session_state.form_data["rivendita"]), step=0.01)
    pub = col_a.number_input("Pubblico (€)", value=float(st.session_state.form_data["pubblico"]), step=0.01)
    qta = col_b.number_input("Q.tà", value=int(st.session_state.form_data["qty"]), step=1)

    st.markdown("---")
    
    # AZIONI
    if st.button("➕ Inserisci Nuovo", use_container_width=True, type="primary"):
        if cod and nom:
            iva = round(riv * 1.22, 2)
            try:
                cursor.execute('INSERT INTO prodotti VALUES (?,?,?,?,?,?,?,?)', (cod, nom, forn, acq, riv, iva, pub, qta))
                conn.commit()
                st.success("Prodotto Inserito!")
                reset_campi()
                st.rerun()
            except: st.error("Errore: Codice già esistente")
        else: st.warning("Mancano Codice o Nome")

    if st.button("💾 Salva Modifiche", use_container_width=True):
        if is_edit:
            iva = round(riv * 1.22, 2)
            cursor.execute('UPDATE prodotti SET nome=?, fornitore=?, prezzo_acquisto=?, prezzo_rivendita=?, prezzo_rivendita_iva=?, prezzo_pubblico=?, quantita=? WHERE codice=?', 
                           (nom, forn, acq, riv, iva, pub, qta, cod))
            conn.commit()
            st.info("Modificato con successo!")
            reset_campi()
            st.rerun()

    if st.button("🗑️ Elimina", use_container_width=True):
        if is_edit:
            cursor.execute("DELETE FROM prodotti WHERE codice=?", (cod,))
            conn.commit()
            st.warning("Prodotto Eliminato")
            reset_campi()
            st.rerun()

    if st.button("🧹 Svuota Campi", use_container_width=True):
        reset_campi()
        st.rerun()

# --- AREA VISUALIZZAZIONE ---
col_main, col_report = st.columns([3, 1])

with col_main:
    st.subheader("🔍 Ricerca e Magazzino")
    search = st.text_input("Cerca per nome o codice...")
    
    query = "SELECT * FROM prodotti"
    if search:
        query += f" WHERE codice LIKE '%{search}%' OR nome LIKE '%{search}%'"
    
    df = pd.read_sql_query(query, conn)
    
    for index, row in df.iterrows():
        c_btn, c_txt = st.columns([0.3, 5])
        if c_btn.button("📝", key=f"btn_{row['codice']}"):
            st.session_state.form_data = {
                "codice": row['codice'], "nome": row['nome'], "fornitore": row['fornitore'],
                "acquisto": row['prezzo_acquisto'], "rivendita": row['prezzo_rivendita'],
                "pubblico": row['prezzo_pubblico'], "qty": row['quantita']
            }
            st.rerun()
        c_txt.text(f"{row['codice']} | {row['nome']} | {row['quantita']}pz | {row['prezzo_pubblico']}€")

with col_report:
    st.subheader("🖨️ PDF")
    tit_pdf = st.text_input("Titolo PDF", "LISTINO ELITE")
    campi_pdf = st.multiselect("Colonne", ["Codice", "Nome", "Fornitore", "P. Acquisto", "P. Rivendita", "P. Pubblico", "Quantità"], default=["Codice", "Nome", "P. Pubblico"])
    
    if st.button("Genera Listino"):
        pdf_out = genera_pdf(tit_pdf, campi_pdf)
        st.download_button("Scarica PDF", data=pdf_out, file_name="listino.pdf")
