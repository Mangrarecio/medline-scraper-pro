import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Extractor Médico Pro", page_icon="🩺", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, b, strong { color: #1e293b; font-weight: bold; }
    .stButton>button { background-color: #2563eb; color: white; font-weight: bold; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🩺 Extractor Médico Inteligente (A-Z)")

with st.sidebar:
    st.header("⚙️ Configuración")
    modo = st.selectbox("Fuente de datos:", ["MedlinePlus (A-Z)", "Mayo Clinic (A-Z)"])
    st.info("Este script separa cada enfermedad en una fila distinta para evitar que el texto se agolpe.")

# --- MOTOR DE EXTRACCIÓN MEJORADO ---
def obtener_texto_limpio(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0'}
    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Seleccionar el área de texto según la web
        contenedor = soup.find('div', id='topic-summary') or soup.find('article') or soup.find('div', class_='main')
        
        if contenedor:
            # Extraer solo párrafos con contenido real
            parrafos = [p.get_text(" ", strip=True) for p in contenedor.find_all('p') if len(p.get_text()) > 40]
            # Unir con saltos de línea dobles para que en Excel se vea ordenado
            return "\n\n".join(parrafos)
    except: return None
    return None

def formatear_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Diccionario_Medico')
        ws = writer.sheets['Diccionario_Medico']
        
        # Configuración de columnas para lectura cómoda
        ws.column_dimensions['A'].width = 10  # Letra
        ws.column_dimensions['B'].width = 40  # Enfermedad
        ws.column_dimensions['C'].width = 110 # Texto (Ancho máximo)
        ws.column_dimensions['D'].width = 30  # Enlace
        
        for row in ws.iter_rows():
            for cell in row:
                # Alineación Superior (TOP) para evitar que el texto "flote"
                cell.alignment = Alignment(wrap_text=True, vertical='top', horizontal='left')
                if cell.row == 1:
                    cell.font = Font(bold=True, size=12)
                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    return output.getvalue()

# --- PROCESO ---
if st.button("🚀 INICIAR EXTRACCIÓN ORGANIZADA"):
    datos = []
    progreso = st.progress(0)
    status = st.empty()

    if modo == "MedlinePlus (A-Z)":
        url_base = "https://medlineplus.gov/spanish/healthtopics_"
        selector = 'section li a'
        suffix = ".html"
    else: # Mayo Clinic
        url_base = "https://www.mayoclinic.org/es/diseases-conditions/index?letter="
        selector = '.index ol li a'
        suffix = ""

    letras = "abcdefghijklmnopqrstuvw" # Barrido completo
    
    for i, letra in enumerate(letras):
        status.markdown(f"🔍 Minando letra: **{letra.upper()}**")
        try:
            r = requests.get(f"{url_base}{letra}{suffix}", timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            links = soup.select(selector)
            
            for l in links:
                nombre = l.get_text(strip=True)
                href = l.get('href')
                if not href or "healthtopics" in href: continue
                
                # Construir URL completa
                full_url = href if href.startswith('http') else f"https://medlineplus.gov{href}" if "Medline" in modo else f"https://www.mayoclinic.org{href}"
                
                texto = obtener_texto_limpio(full_url)
                if texto:
                    datos.append({
                        "Letra": letra.upper(),
                        "Enfermedad": nombre,
                        "Contenido": texto,
                        "Fuente": full_url
                    })
        except: continue
        progreso.progress((i + 1) / len(letras))

    if datos:
        df = pd.DataFrame(datos)
        st.success(f"✅ ¡Hecho! {len(df)} temas organizados.")
        
        # Botón de descarga
        excel_data = formatear_excel(df)
        st.download_button(
            label="📥 DESCARGAR EXCEL DE ALTA CALIDAD",
            data=excel_data,
            file_name="Diccionario_Medico_Pro.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.dataframe(df.head(20))
    else:
        st.error("No se pudieron extraer datos. Prueba a recargar la web.")