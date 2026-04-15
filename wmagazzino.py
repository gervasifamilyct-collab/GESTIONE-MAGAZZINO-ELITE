import streamlit as st
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Elite Estetica - Gestionale", layout="wide")

# --- DATABASE ---
@st.cache_resource
def get_connection():
    conn = sqlite3.connect("magazzino.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prodotti (
            codice TEXT PRIMARY KEY, nome TEXT, fornitore TEXT,
            prezzo_acquisto REAL, prezzo_rivendita REAL,
            prezzo_rivendita_iva REAL, prezzo_pubblico REAL, quantita INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    return conn

conn = get_connection()
cursor = conn.cursor()

# --- LOGICA DI RESET (SOLUZIONE DEFINITIVA) ---
# Usiamo un contatore per cambiare le chiavi dei widget e forzare il reset visivo
if 'form_iteration' not in st.session_state:
    st.session_state.form_iteration = 0
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"codice": "", "nome": "", "fornitore": "", "acquisto": 0.0, "rivendita": 0.0, "pubblico": 0.0, "qty": 0}

def forza_reset_totale():
    # Cambiamo i dati e incrementiamo l'iteratore delle chiavi
    st.session_state.form_data = {"codice": "", "nome": "", "fornitore": "", "acquisto": 0.0, "rivendita": 0.0, "pubblico": 0.0, "qty": 0}
    st.session_state.form_iteration += 1
    st.rerun()

# --- FUNZIONE PDF ---
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

# --- SIDEBAR (SCHEDA PRODOTTO) ---
st.sidebar.header("🛡️ SCHEDA PRODOTTO")

# Creiamo le chiavi dinamiche basate su form_iteration
iter = st.session_state.form_iteration
is_edit = st.session_state.form_data["codice"] != ""

with st.sidebar:
    cod = st.text_input("Codice Prodotto", value=st.session_state.form_data["codice"], disabled=is_edit, key=f"cod_{iter}")
    nom = st.text_input("Nome/Descrizione", value=st.session_state.form_data["nome"], key=f"nom_{iter}")
    forn = st.text_input("Fornitore", value=st.session_state.form_data["fornitore"], key=f"forn_{iter}")
    
    col1, col2 = st.columns(2)
    acq = col1.number_input("Acquisto (€)", value=float(st.session_state.form_data["acquisto"]), step=0.01, key=f"acq_{iter}")
    riv = col2.number_input("Rivendita (€)", value=float(st.session_state.form_data["rivendita"]), step=0.01, key=f"riv_{iter}")
    pub = col1.number_input("Pubblico (€)", value=float(st.session_state.form_data["pubblico"]), step=0.01, key=f"pub_{iter}")
    qta = col2.number_input("Q.tà", value=int(st.session_state.form_data["qty"]), step=1, key=f"qty_{iter}")

    st.write("---")
    
    # PULSANTI
    if st.button("➕ Inserisci Nuovo", use_container_width=True, type="primary"):
        if cod and nom:
            iva = round(riv * 1.22, 2)
            try:
                cursor.execute('INSERT INTO prodotti VALUES (?,?,?,?,?,?,?,?)', (cod, nom, forn, acq, riv, iva, pub, qta))
                conn.commit()
                st.success("Inserito!")
                forza_reset_totale()
            except: st.error("Errore: Codice già presente")
            
    if st.button("💾 Salva Modifiche", use_container_width=True):
        if is_edit:
            iva = round(riv * 1.22, 2)
            cursor.execute('UPDATE prodotti SET nome=?, fornitore=?, prezzo_acquisto=?, prezzo_rivendita=?, prezzo_rivendita_iva=?, prezzo_pubblico=?, quantita=? WHERE codice=?', 
                           (nom, forn, acq, riv, iva, pub, qta, cod))
            conn.commit()
            st.info("Modificato!")
            forza_reset_totale()

    if st.button("🗑️ Elimina", use_container_width=True):
        if is_edit:
            cursor.execute("DELETE FROM prodotti WHERE codice=?", (cod,))
            conn.commit()
            forza_reset_totale()

    if st.button("🧹 Svuota Campi", use_container_width=True):
        forza_reset_totale()

# --- AREA PRINCIPALE ---
st.header("🔍 Ricerca e Magazzino")
search = st.text_input("Cerca per nome o codice...")

query = "SELECT * FROM prodotti"
if search:
    query += f" WHERE codice LIKE '%{search}%' OR nome LIKE '%{search}%'"

df = pd.read_sql_query(query, conn)

# Visualizzazione Tabella
if not df.empty:
    st.dataframe(df.rename(columns={
        'codice': 'Codice', 'nome': 'Nome', 'fornitore': 'Fornitore',
        'prezzo_acquisto': 'Acquisto', 'prezzo_rivendita': 'Rivendita',
        'prezzo_rivendita_iva': 'Riv+IVA', 'prezzo_pubblico': 'Pubblico', 'quantita': 'Q.tà'
    }), use_container_width=True, hide_index=True)

    # Caricamento dati per Modifica
    sel = st.selectbox("Seleziona Prodotto per Modificare/Eliminare", [""] + df['codice'].tolist())
    if sel:
        r = df[df['codice'] == sel].iloc[0]
        if st.button("Carica Dati nella Scheda"):
            st.session_state.form_data = {
                "codice": r['codice'], "nome": r['nome'], "fornitore": r['fornitore'],
                "acquisto": r['prezzo_acquisto'], "rivendita": r['prezzo_rivendita'],
                "pubblico": r['prezzo_pubblico'], "qty": r['quantita']
            }
            st.rerun()

# --- PDF ---
st.write("---")
st.header("🖨️ Stampa PDF")
c1, c2 = st.columns([2, 1])
with c1:
    tit = st.text_input("Titolo Report", "LISTINO ELITE")
    campi = st.multiselect("Colonne", ["Codice", "Nome", "Fornitore", "P. Acquisto", "P. Rivendita", "P. Pubblico", "Quantità"], default=["Codice", "Nome", "P. Pubblico"])
with c2:
    st.write("###")
    if st.button("Genera PDF", use_container_width=True):
        pdf_file = genera_pdf(tit, campi)
        st.download_button("Scarica PDF", data=pdf_file, file_name="listino.pdf")
