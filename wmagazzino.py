import streamlit as st
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# --- 1. CONFIGURAZIONE PAGINA (TEMA CHIARO PER LEGGIBILITÀ) ---
st.set_page_config(page_title="Elite Estetica - Gestionale", layout="wide", initial_sidebar_state="expanded")

# --- 2. GESTIONE DATABASE CON CACHING ---
@st.cache_resource
def get_connection():
    # check_same_thread=False è fondamentale per Streamlit
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

conn = get_connection()
cursor = conn.cursor()

# --- 3. GESTIONE STATO E RESET CAMPI (SOLUZIONE AL PROBLEMA) ---
# Inizializziamo lo stato se non esiste
if 'form_data' not in st.session_state:
    st.session_state.form_data = {
        "codice": "", "nome": "", "fornitore": "",
        "acquisto": 0.0, "rivendita": 0.0, "pubblico": 0.0, "qty": 0
    }

# Questa funzione forza lo svuotamento dei campi
def resetta_e_ricarica():
    st.session_state.form_data = {
        "codice": "", "nome": "", "fornitore": "",
        "acquisto": 0.0, "rivendita": 0.0, "pubblico": 0.0, "qty": 0
    }
    # Riavvia l'app per applicare i campi vuoti
    st.rerun()

# --- 4. FUNZIONE PDF ---
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

# --- 5. INTERFACCIA UTENTE (SIDEBAR) ---
st.sidebar.markdown("## 🛡️ SCHEDA PRODOTTO")

with st.sidebar:
    is_edit = st.session_state.form_data["codice"] != ""
    
    # Input Campi (con valori presi dallo stato)
    # Usiamo parametri 'key' unici per ogni widget per una migliore gestione
    cod = st.text_input("Codice Prodotto:", value=st.session_state.form_data["codice"], disabled=is_edit, key="in_cod")
    nom = st.text_input("Nome/Descrizione Prodotto:", value=st.session_state.form_data["nome"], key="in_nom")
    forn = st.text_input("Fornitore:", value=st.session_state.form_data["fornitore"], key="in_forn")
    
    col_a, col_b = st.columns(2)
    acq = col_a.number_input("Acquisto (€):", value=float(st.session_state.form_data["acquisto"]), step=0.01, key="in_acq")
    riv = col_b.number_input("Rivendita (€):", value=float(st.session_state.form_data["rivendita"]), step=0.01, key="in_riv")
    pub = col_a.number_input("Pubblico (€):", value=float(st.session_state.form_data["pubblico"]), step=0.01, key="in_pub")
    qta = col_b.number_input("Q.tà:", value=int(st.session_state.form_data["qty"]), step=1, key="in_qta")

    st.markdown("---")
    
    # AZIONI (Colori simili al PC)
    # Pulsante INSERISCI (Verde)
    btn_inserisci = st.button("➕ Inserisci Nuovo", use_container_width=True, type="primary")
    
    # Pulsante SALVA (Blu)
    btn_salva = st.button("💾 Salva Modifiche", use_container_width=True)
    
    # Pulsante ELIMINA (Rosso)
    btn_elimina = st.button("🗑️ Elimina", use_container_width=True)
    
    # Pulsante SVUOTA (Grigio)
    btn_svuota = st.button("🧹 Svuota Campi", use_container_width=True)

    # Logica dei pulsanti
    if btn_inserisci:
        if cod and nom:
            iva = round(riv * 1.22, 2)
            try:
                cursor.execute('INSERT INTO prodotti VALUES (?,?,?,?,?,?,?,?)', (cod, nom, forn, acq, riv, iva, pub, qta))
                conn.commit()
                st.sidebar.success(f"Prodotto {cod} inserito!")
                resetta_e_ricarica() # <--- SOLUZIONE: Svuota tutto
            except sqlite3.IntegrityError:
                st.sidebar.error("Errore: Codice già esistente!")
        else:
            st.sidebar.warning("Mancano Codice o Nome!")

    if btn_salva:
        if is_edit:
            iva = round(riv * 1.22, 2)
            cursor.execute('UPDATE prodotti SET nome=?, fornitore=?, prezzo_acquisto=?, prezzo_rivendita=?, prezzo_rivendita_iva=?, prezzo_pubblico=?, quantita=? WHERE codice=?', 
                           (nom, forn, acq, riv, iva, pub, qta, cod))
            conn.commit()
            st.sidebar.info("Modificato con successo!")
            resetta_e_ricarica() # <--- SOLUZIONE: Svuota tutto
        else:
            st.sidebar.warning("Seleziona prima un prodotto dalla tabella!")

    if btn_elimina:
        if is_edit:
            cursor.execute("DELETE FROM prodotti WHERE codice=?", (cod,))
            conn.commit()
            st.sidebar.warning("Prodotto Eliminato!")
            resetta_e_ricarica() # <--- SOLUZIONE: Svuota tutto
        else:
            st.sidebar.warning("Seleziona prima un prodotto!")

    if btn_svuota:
        resetta_e_ricarica() # <--- SOLUZIONE: Svuota tutto

# --- 6. AREA VISUALIZZAZIONE PRINCIPALE (SOLUZIONE AL PROBLEMA LEGGIBILITÀ) ---
st.markdown("## 🔍 Ricerca e Magazzino")

# Barra di ricerca
search = st.text_input("Cerca per nome o codice...", key="search_bar")

# Query per i dati
query = "SELECT * FROM prodotti"
if search:
    # Usiamo parametri per evitare SQL Injection
    query += " WHERE codice LIKE ? OR nome LIKE ?"
    params = (f'%{search}%', f'%{search}%')
    df = pd.read_sql_query(query, conn, params=params)
else:
    df = pd.read_sql_query(query, conn)

# Rinominiamo le colonne per la tabella web
df_display = df.rename(columns={
    'codice': 'Codice',
    'nome': 'Nome',
    'fornitore': 'Fornitore',
    'prezzo_acquisto': 'Acquisto (€)',
    'prezzo_rivendita': 'Rivendita (€)',
    'prezzo_rivendita_iva': 'Riv+IVA (€)',
    'prezzo_pubblico': 'Pubblico (€)',
    'quantita': 'Q.tà'
})

# Visualizzazione come Tabella Interattiva (Molto più leggibile)
st.markdown("### Inventario Attuale")
st.markdown("Cerca e seleziona un prodotto per caricarlo nella scheda a sinistra:")

# Creiamo colonne: una per il pulsante di selezione, una per la tabella
col_btn_space, col_table_space = st.columns([0.1, 4])

with col_table_space:
    # Mostriamo la tabella (senza l'indice automatico di pandas)
    st.dataframe(df_display, use_container_width=True, hide_index=True)

with col_btn_space:
    # Aggiungiamo un pulsante per ogni riga per selezionarla
    st.write("") # Spazio per allineare coi titoli
    st.write("") 
    st.write("")
    for index, row in df.iterrows():
        # Cliccando questo pulsante, carichiamo i dati nello stato
        if st.button("📝", key=f"select_{row['codice']}"):
            st.session_state.form_data = {
                "codice": row['codice'], 
                "nome": row['nome'], 
                "fornitore": row['fornitore'],
                "acquisto": row['prezzo_acquisto'], 
                "rivendita": row['prezzo_rivendita'],
                "pubblico": row['prezzo_pubblico'], 
                "qty": row['quantita']
            }
            # Ricarichiamo per mostrare i dati nei campi di input
            st.rerun()

st.markdown("---")

# --- 7. AREA PDF (Separata e pulita) ---
st.markdown("## 🖨️ Stampa PDF")
col_pdf_inputs, col_pdf_btn = st.columns([3, 1])

with col_pdf_inputs:
    tit_pdf = st.text_input("Titolo del Listino PDF:", "LISTINO ELITE", key="pdf_title")
    campi_pdf = st.multiselect("Colonne da includere nel PDF:", 
                                ["Codice", "Nome", "Fornitore", "P. Acquisto", "P. Rivendita", "P. Pubblico", "Quantità"], 
                                default=["Codice", "Nome", "P. Pubblico"],
                                key="pdf_cols")

with col_pdf_btn:
    st.write("") # Spazio per allineare
    st.write("")
    if st.button("📄 Genera Listino PDF", use_container_width=True):
        if campi_pdf:
            pdf_out = genera_pdf(tit_pdf, campi_pdf)
            st.download_button(label="⬇️ Scarica PDF", 
                               data=pdf_out, 
                               file_name=f"{tit_pdf.replace(' ','_')}.pdf", 
                               mime="application/pdf",
                               use_container_width=True)
        else:
            st.error("Seleziona almeno una colonna!")
