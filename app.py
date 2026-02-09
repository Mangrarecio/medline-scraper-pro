import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Extractor Médico Universal", page_icon="🌐", layout="wide")

# Estilos
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, b, strong { color: #0f172a; font-weight: bold; }
    .stButton>button { background-color: #0284c7; color: white; font-weight: bold; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌐 Extractor de Datos Médico & Universal")

with st.sidebar:
    st.header("⚙️ Configuración")
    modo = st.selectbox(
        "Selecciona el objetivo:",
        ["MedlinePlus (A-Z)", "Mayo Clinic (A-Z)", "Modo Universal"]
    )

# --- MOTOR DE EXTRACCIÓN MEJORADO ---
def obtener_contenido_limpio(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9'
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Eliminar elementos basura antes de extraer
        for basura in soup(['nav', 'header', 'footer', 'script', 'style', 'aside']):
            basura.decompose()

        # Estrategia de búsqueda multizona
        contenedor = (
            soup.find('div', id='topic-summary') or  # Medline
            soup.find('article') or                 # Mayo / Universal
            soup.find('div', class_='content') or
            soup.find('main')
        )
        
        if contenedor:
            p_list = [p.get_text(strip=True) for p in contenedor.find_all('p') if len(p.get_text()) > 45]
            return "\n\n".join(p_list)
        return None
    except: return None

def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
        ws = writer.sheets['Resultados']
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 100
        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')
                if cell.row == 1: cell.font = Font(bold=True)
    return output.getvalue()

# --- EJECUCIÓN ---
if st.button("🚀 INICIAR EXTRACCIÓN"):
    datos = []
    progreso = st.progress(0)
    status = st.empty()
    
    # Configuración de rutas según el modo
    if modo == "MedlinePlus (A-Z)":
        url_base = "https://medlineplus.gov/spanish/healthtopics_"
        selector = 'section li a'
        suffix = ".html"
    elif modo == "Mayo Clinic (A-Z)":
        url_base = "https://www.mayoclinic.org/es/diseases-conditions/index?letter="
        selector = '.index ol li a' # Selector específico de Mayo
        suffix = ""
    else:
        url_base = None

    if url_base:
        letras = "abc" # Prueba corta, cámbialo a "abcdefghijklmnopqrstuvw" para completo
        for i, letra in enumerate(letras):
            status.markdown(f"🔍 Minando letra: **{letra.upper()}**")
            target = f"{url_base}{letra}{suffix}"
            try:
                r = requests.get(target, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                soup = BeautifulSoup(r.content, 'html.parser')
                links = soup.select(selector)
                
                for l in links[:10]: # Límite para no saturar la web app
                    nombre = l.get_text(strip=True)
                    href = l.get('href')
                    if not href: continue
                    
                    # Limpieza de URLs relativas
                    if href.startswith('/'):
                        if "mayo" in modo.lower(): full_url = f"https://www.mayoclinic.org{href}"
                        else: full_url = f"https://medlineplus.gov{href}"
                    else: full_url = href
                    
                    texto = obtener_contenido_limpio(full_url)
                    if texto:
                        datos.append({"Letra": letra.upper(), "Tema": nombre, "Contenido": texto, "URL": full_url})
            except: continue
            progreso.progress((i + 1) / len(letras))
    
    if datos:
        df = pd.DataFrame(datos)
        st.success(f"✅ ¡Éxito! Se han extraído {len(datos)} registros.")
        st.dataframe(df.head(10), use_container_width=True)
        st.download_button("📥 Descargar Excel Formateado", data=generar_excel(df), file_name="extraccion_pro.xlsx")
    else:
        st.error("No se detectaron datos. Mayo Clinic puede estar bloqueando la petición o el selector ha cambiado.")