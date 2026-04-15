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

# --- LOGICA DI RESET ---
if 'reset_trigger' not in st.session_state:
    st.session_state.reset_trigger = 0

def reset_campi():
    st.session_state.reset_trigger += 1
    st.rerun()

# --- FUNZIONE PDF ---
def genera_pdf(titolo, campi_scelti):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16); c.drawString(50, height - 50, titolo.upper())
    y = height - 80; x_pos = 50
    larghezze = {"Codice": 70, "Nome": 150, "Fornitore": 80, "P. Acquisto": 60, "P. Rivendita": 60, "P. Pubblico": 60, "Quantità": 50}
    c.setFont("Helvetica-Bold", 10)
    for campo in campi_scelti:
        c.drawString(x_pos, y, campo); x_pos += larghezze.get(campo, 70)
    c.line(50, y-5, width-50, y-5); y -= 25
    cursor.execute("SELECT * FROM prodotti")
    for p in cursor.fetchall():
        if y < 50: c.showPage(); y = height - 50
        mappa = {"Codice": str(p[0]), "Nome": str(p[1]), "Fornitore": str(p[2]), "P. Acquisto": f"{p[3]}€", 
                 "P. Rivendita": f"{p[4]}€", "P. Pubblico": f"{p[6]}€", "Quantità": str(p[7])}
        x_pos = 50; c.setFont("Helvetica", 9)
        for campo in campi_scelti:
            c.drawString(x_pos, y, str(mappa[campo])[:25]); x_pos += larghezze.get(campo, 70)
        y -= 20
    c.save(); buffer.seek(0)
    return buffer

# --- AREA PRINCIPALE (CARICAMENTO DATI) ---
st.header("🔍 Magazzino Elite Estetica")
search = st.text_input("Filtra per nome o codice...")

query = "SELECT * FROM prodotti"
if search:
    query += f" WHERE codice LIKE '%{search}%' OR nome LIKE '%{search}%'"
df = pd.read_sql_query(query, conn)

# Rinominiamo per la tabella
df_display = df.rename(columns={
    'codice': 'Codice', 'nome': 'Nome', 'fornitore': 'Fornitore',
    'prezzo_acquisto': 'Acquisto', 'prezzo_rivendita': 'Rivendita',
    'prezzo_rivendita_iva': 'Riv+IVA', 'prezzo_pubblico': 'Pubblico', 'quantita': 'Q.tà'
})

# TABELLA CLICCABILE
selected_rows = st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    on_select="rerun", # Questo permette di cliccare la riga
    selection_mode="single-row"
)

# Recuperiamo i dati della riga selezionata
selected_data = None
if len(selected_rows.selection.rows) > 0:
    row_idx = selected_rows.selection.rows[0]
    selected_data = df.iloc[row_idx]

# --- SIDEBAR (SCHEDA PRODOTTO) ---
st.sidebar.header("🛡️ SCHEDA PRODOTTO")
key_suf = st.session_state.reset_trigger

# Se abbiamo selezionato una riga, usiamo quei dati, altrimenti campi vuoti
d = selected_data if selected_data is not None else {"codice": "", "nome": "", "fornitore": "", "prezzo_acquisto": 0.0, "prezzo_rivendita": 0.0, "prezzo_pubblico": 0.0, "quantita": 0}

with st.sidebar:
    cod = st.text_input("Codice Prodotto", value=str(d["codice"]), key=f"c_{key_suf}")
    nom = st.text_input("Nome/Descrizione", value=str(d["nome"]), key=f"n_{key_suf}")
    forn = st.text_input("Fornitore", value=str(d["fornitore"]), key=f"f_{key_suf}")
    
    c1, c2 = st.columns(2)
    acq = c1.number_input("Acquisto (€)", value=float(d["prezzo_acquisto"]), step=0.01, key=f"a_{key_suf}")
    riv = c2.number_input("Rivendita (€)", value=float(d["prezzo_rivendita"]), step=0.01, key=f"r_{key_suf}")
    pub = c1.number_input("Pubblico (€)", value=float(d["prezzo_pubblico"]), step=0.01, key=f"p_{key_suf}")
    qta = c2.number_input("Q.tà", value=int(d["quantita"]), step=1, key=f"q_{key_suf}")

    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns(2)
    
    if col_btn1.button("➕ Inserisci", use_container_width=True, type="primary"):
        if cod and nom:
            iva = round(riv * 1.22, 2)
            try:
                cursor.execute('INSERT INTO prodotti VALUES (?,?,?,?,?,?,?,?)', (cod, nom, forn, acq, riv, iva, pub, qta))
                conn.commit(); st.success("Inserito!"); reset_campi()
            except: st.error("Errore: Codice presente!")

    if col_btn2.button("💾 Modifica", use_container_width=True):
        iva = round(riv * 1.22, 2)
        cursor.execute('UPDATE prodotti SET nome=?, fornitore=?, prezzo_acquisto=?, prezzo_rivendita=?, prezzo_rivendita_iva=?, prezzo_pubblico=?, quantita=? WHERE codice=?', 
                       (nom, forn, acq, riv, iva, pub, qta, cod))
        conn.commit(); st.info("Modificato!"); reset_campi()

    if col_btn1.button("🗑️ Elimina", use_container_width=True):
        cursor.execute("DELETE FROM prodotti WHERE codice=?", (cod,))
        conn.commit(); st.warning("Eliminato!"); reset_campi()

    if col_btn2.button("🧹 Svuota", use_container_width=True):
        reset_campi()

# --- PDF ---
st.divider()
st.header("🖨️ Stampa PDF")
cp1, cp2 = st.columns([2, 1])
with cp1:
    tit = st.text_input("Titolo Report", "LISTINO ELITE", key="t_pdf")
    campi = st.multiselect("Colonne", ["Codice", "Nome", "Fornitore", "P. Acquisto", "P. Rivendita", "P. Pubblico", "Quantità"], default=["Codice", "Nome", "P. Pubblico"])
with cp2:
    st.write("###")
    if st.button("Genera PDF", use_container_width=True):
        f = genera_pdf(tit, campi)
        st.download_button("Scarica PDF", data=f, file_name="listino.pdf")
