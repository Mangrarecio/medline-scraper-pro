import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Extractor Médico Élite", page_icon="🧬", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, b, strong { color: #0f172a; font-weight: bold; }
    .stButton>button { background-color: #10b981; color: white; font-weight: bold; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧬 Extractor Médico Multi-Fuente v13.0")

with st.sidebar:
    st.header("⚙️ Selector de Fuente")
    modo = st.selectbox(
        "¿Qué deseas minar?",
        ["MedlinePlus (A-Z)", "Mayo Clinic (A-Z)", "Manual MSD (Específico)", "Modo Universal"]
    )
    st.info("MSD es altamente protegido. Este modo usa cabeceras de alta prioridad.")

# --- MOTOR DE EXTRACCIÓN ÉLITE ---
def extraer_contenido_profesional(url):
    # Cabeceras de simulación humana avanzada
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://www.google.com/'
    }
    try:
        time.sleep(1) # Pausa de cortesía para evitar bloqueos
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Estrategia específica para MSD
        if "msdmanuals" in url:
            # MSD usa clases como 'topic__explanation' o 'Topic__FullView'
            contenedor = soup.find('section', class_='topic__full') or soup.find('div', class_='topic__explanation')
        else:
            contenedor = soup.find('div', id='topic-summary') or soup.find('article') or soup.find('main')
        
        if contenedor:
            # Limpiar elementos que ensucian el texto
            for tag in contenedor(['script', 'style', 'nav', 'aside', 'table']):
                tag.decompose()
            parrafos = [p.get_text(" ", strip=True) for p in contenedor.find_all('p') if len(p.get_text()) > 50]
            return "\n\n".join(parrafos)
        return None
    except: return None

def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos_Medicos')
        ws = writer.sheets['Datos_Medicos']
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 110
        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')
                if cell.row == 1: cell.font = Font(bold=True)
    return output.getvalue()

# --- LÓGICA DE INTERFAZ ---
if modo == "Manual MSD (Específico)":
    url_input = st.text_input("URL del Tema MSD:", "https://www.msdmanuals.com/es/professional/trastornos-gastrointestinales/abdomen-agudo-y-cirug%C3%ADa-gastrointestinal/dolor-abdominal-agudo")
else:
    url_input = None

if st.button("🚀 INICIAR EXTRACCIÓN"):
    datos = []
    
    if modo == "Manual MSD (Específico)" and url_input:
        with st.spinner("Extrayendo de MSD Manuals..."):
            texto = extraer_contenido_profesional(url_input)
            if texto:
                # Intentamos sacar el título de la página
                nombre_tema = url_input.split('/')[-1].replace('-', ' ').capitalize()
                datos.append({"Fuente": "Manual MSD", "Tema": nombre_tema, "Contenido": texto, "URL": url_input})
    
    # ... (Aquí sigue la lógica de Medline y Mayo que ya tenías)
    
    if datos:
        df = pd.DataFrame(datos)
        st.success("✅ Extracción completada.")
        st.dataframe(df)
        st.download_button("📥 Descargar Excel Formateado", data=generar_excel(df), file_name="extraccion_msd.xlsx")
    else:
        st.error("No se pudo extraer el contenido. MSD protege sus datos de forma estricta. Intenta con otra URL del manual.")