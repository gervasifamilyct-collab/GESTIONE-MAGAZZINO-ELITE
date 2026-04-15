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

# --- GESTIONE STATO ---
if 'form_iteration' not in st.session_state:
    st.session_state.form_iteration = 0
if 'edit_data' not in st.session_state:
    st.session_state.edit_data = None

def reset_totale():
    st.session_state.edit_data = None
    st.session_state.form_iteration += 1

def carica_prodotto(codice):
    cursor.execute("SELECT * FROM prodotti WHERE codice=?", (codice,))
    res = cursor.fetchone()
    if res:
        st.session_state.edit_data = {
            "codice": res[0], "nome": res[1], "fornitore": res[2],
            "acquisto": res[3], "rivendita": res[4], "pubblico": res[6], "qty": res[7]
        }
        st.session_state.form_iteration += 1

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

# --- SIDEBAR ---
st.sidebar.header("🛡️ SCHEDA PRODOTTO")
iter = st.session_state.form_iteration
d = st.session_state.edit_data if st.session_state.edit_data else {"codice": "", "nome": "", "fornitore": "", "acquisto": 0.0, "rivendita": 0.0, "pubblico": 0.0, "qty": 0}

with st.sidebar:
    cod = st.text_input("Codice Prodotto", value=d["codice"], disabled=(st.session_state.edit_data is not None), key=f"c_{iter}")
    nom = st.text_input("Nome/Descrizione", value=d["nome"], key=f"n_{iter}")
    forn = st.text_input("Fornitore", value=d["fornitore"], key=f"f_{iter}")
    col1, col2 = st.columns(2)
    acq = col1.number_input("Acquisto (€)", value=float(d["acquisto"]), step=0.01, key=f"a_{iter}")
    riv = col2.number_input("Rivendita (€)", value=float(d["rivendita"]), step=0.01, key=f"r_{iter}")
    pub = col1.number_input("Pubblico (€)", value=float(d["pubblico"]), step=0.01, key=f"p_{iter}")
    qta = col2.number_input("Q.tà", value=int(d["qty"]), step=1, key=f"q_{iter}")
    st.write("---")
    
    if st.button("➕ Inserisci Nuovo", use_container_width=True, type="primary"):
        if cod and nom:
            iva = round(riv * 1.22, 2)
            try:
                cursor.execute('INSERT INTO prodotti VALUES (?,?,?,?,?,?,?,?)', (cod, nom, forn, acq, riv, iva, pub, qta))
                conn.commit(); st.success("Inserito!"); reset_totale(); st.rerun()
            except: st.error("Codice duplicato!")
    
    if st.button("💾 Salva Modifiche", use_container_width=True, disabled=(st.session_state.edit_data is None)):
        iva = round(riv * 1.22, 2)
        cursor.execute('UPDATE prodotti SET nome=?, fornitore=?, prezzo_acquisto=?, prezzo_rivendita=?, prezzo_rivendita_iva=?, prezzo_pubblico=?, quantita=? WHERE codice=?', 
                       (nom, forn, acq, riv, iva, pub, qta, d["codice"]))
        conn.commit(); st.info("Modificato!"); reset_totale(); st.rerun()

    if st.button("🗑️ Elimina", use_container_width=True, disabled=(st.session_state.edit_data is None)):
        cursor.execute("DELETE FROM prodotti WHERE codice=?", (d["codice"],))
        conn.commit(); st.warning("Eliminato!"); reset_totale(); st.rerun()

    if st.button("🧹 Svuota Campi", use_container_width=True):
        reset_totale(); st.rerun()

# --- AREA PRINCIPALE ---
st.header("🔍 Ricerca e Magazzino")
search = st.text_input("Filtra per nome o codice...")

query = "SELECT * FROM prodotti"
if search:
    query += f" WHERE codice LIKE '%{search}%' OR nome LIKE '%{search}%'"
df = pd.read_sql_query(query, conn)

if not df.empty:
    # 1. TABELLA BELLA E ORDINATA (Sola lettura)
    df_clean = df.rename(columns={
        'codice': 'Codice', 'nome': 'Nome', 'fornitore': 'Fornitore',
        'prezzo_acquisto': 'Acquisto', 'prezzo_rivendita': 'Rivendita',
        'prezzo_rivendita_iva': 'Riv+IVA', 'prezzo_pubblico': 'Pubblico', 'quantita': 'Q.tà'
    })
    st.table(df_clean) # st.table è più leggibile e ferma di st.dataframe

    # 2. SELETTORE DI RIGA (Semplice e veloce)
    st.write("### 📝 Gestione rapida")
    col_sel, col_btn = st.columns([3, 1])
    prodotto_da_caricare = col_sel.selectbox("Seleziona il codice del prodotto che vuoi modificare o eliminare:", 
                                            ["-- SELEZIONA --"] + df['codice'].tolist())
    
    if col_btn.button("🔄 CARICA NELLA SCHEDA", use_container_width=True):
        if prodotto_da_caricare != "-- SELEZIONA --":
            carica_prodotto(prodotto_da_caricare)
            st.rerun()

# --- PDF ---
st.divider()
st.header("🖨️ Stampa PDF")
c1, c2 = st.columns([2, 1])
with c1:
    tit = st.text_input("Titolo Report", "LISTINO ELITE")
    campi = st.multiselect("Colonne", ["Codice", "Nome", "Fornitore", "P. Acquisto", "P. Rivendita", "P. Pubblico", "Quantità"], default=["Codice", "Nome", "P. Pubblico"])
with c2:
    st.write("###")
    if st.button("Genera PDF", use_container_width=True):
        f = genera_pdf(tit, campi)
        st.download_button("Scarica PDF", data=f, file_name="listino.pdf")
