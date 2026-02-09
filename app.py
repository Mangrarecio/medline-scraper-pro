import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="Extractor Médico Universal", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, b, strong { color: #0f172a; font-weight: bold; }
    .stButton>button { background-color: #0284c7; color: white; font-weight: bold; border-radius: 10px; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌐 Extractor de Datos Médico & Universal")

# --- BARRA LATERAL: SELECTOR DE MODO ---
with st.sidebar:
    st.header("⚙️ Configuración del Minero")
    modo = st.selectbox(
        "Selecciona el objetivo:",
        ["MedlinePlus (A-Z)", "Mayo Clinic (A-Z)", "Modo Universal (Cualquier URL)"]
    )
    st.divider()
    st.info("El **Modo Universal** intentará extraer el texto principal de cualquier página que le proporciones.")

# --- FUNCIONES DE EXTRACCIÓN INTELIGENTE ---
def limpiar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
        ws = writer.sheets['Datos']
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 90
        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')
                if cell.row == 1: cell.font = Font(bold=True)
    return output.getvalue()

def extraer_cuerpo_universal(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        # Buscamos en etiquetas comunes de contenido
        contenedor = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
        if not contenedor: contenedor = soup.body
        
        parrafos = [p.get_text(strip=True) for p in contenedor.find_all('p') if len(p.get_text()) > 40]
        return "\n\n".join(parrafos)
    except: return None

# --- LÓGICA POR MODOS ---
if modo == "MedlinePlus (A-Z)":
    url_base = "https://medlineplus.gov/spanish/healthtopics_"
    selector_enlaces = 'section li a'
    suffix = ".html"
elif modo == "Mayo Clinic (A-Z)":
    url_base = "https://www.mayoclinic.org/es/diseases-conditions/index?letter="
    selector_enlaces = '.index ol li a'
    suffix = ""
else:
    url_base = st.text_input("Introduce URL para extraer:", "https://ejemplo.com/articulo")

if st.button("🚀 INICIAR MINERÍA"):
    datos = []
    progreso = st.progress(0)
    status = st.empty()

    if "A-Z" in modo:
        letras = "abcdefghijklmnopqrstuvw"
        for i, letra in enumerate(letras):
            status.markdown(f"🔍 Escaneando letra: **{letra.upper()}**")
            target = f"{url_base}{letra}{suffix}"
            try:
                r = requests.get(target, timeout=10)
                soup = BeautifulSoup(r.content, 'html.parser')
                enlaces = soup.select(selector_enlaces)
                
                for link in enlaces[:15]: # Limitamos a 15 por letra para velocidad en la web
                    nombre = link.get_text(strip=True)
                    href = link.get('href')
                    if href:
                        full_url = href if href.startswith('http') else f"https://www.mayoclinic.org{href}" if "mayo" in modo.lower() else f"https://medlineplus.gov{href}"
                        texto = extraer_cuerpo_universal(full_url)
                        if texto:
                            datos.append({"Letra": letra.upper(), "Tema": nombre, "Contenido": texto, "URL": full_url})
            except: continue
            progreso.progress((i + 1) / len(letras))
    else:
        # MODO UNIVERSAL
        status.markdown(f"🔍 Extrayendo datos de: **{url_base}**")
        texto = extraer_cuerpo_universal(url_base)
        if texto:
            datos.append({"Tema": "Extracción Manual", "Contenido": texto, "URL": url_base})
        progreso.progress(100)

    if datos:
        df = pd.DataFrame(datos)
        st.success("✅ ¡Proceso finalizado!")
        st.dataframe(df.head(20), use_container_width=True)
        
        st.download_button(
            "📥 Descargar EXCEL ORGANIZADO",
            data=limpiar_excel(df),
            file_name="extraccion_medica_pro.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("No se encontraron datos. Verifica la conexión o la URL.")