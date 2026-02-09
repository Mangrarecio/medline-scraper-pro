import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import json
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Extractor Médico Pro", page_icon="🩺", layout="wide")

# Diseño profesional claro con texto en negrita
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, h3 { color: #1e293b; font-weight: bold; }
    b, strong { color: #1e293b; }
    .stButton>button { background-color: #2563eb; color: white; font-weight: bold; border-radius: 8px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🩺 Extractor Médico Universal v10.0 (Edición Web)")
st.markdown("**Bienvenido.** Esta versión está optimizada para ejecutarse desde la nube y generar archivos limpios.")

# --- FUNCIONES TÉCNICAS (Sin Tkinter) ---
def limpiar_excel_en_memoria(df):
    """Aplica formato profesional al Excel directamente en la RAM."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
        ws = writer.sheets['Resultados']
        
        # Ajustes de columna
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 100
        ws.column_dimensions['D'].width = 40
        
        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')
                if cell.row == 1:
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    return output.getvalue()

def obtener_texto(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            s = BeautifulSoup(r.content, 'html.parser')
            cuerpo = s.find('div', id="topic-summary") or s.find('div', class_="main")
            if cuerpo:
                parrafos = [p.get_text(strip=True) for p in cuerpo.find_all('p') if len(p.get_text()) > 30]
                return "\n\n".join(parrafos)
    except: return None
    return None

# --- INTERFAZ DE USUARIO ---
url_input = st.text_input("URL de inicio (Índice A-Z):", "https://medlineplus.gov/spanish/healthtopics.html")

if st.button("🚀 INICIAR EXTRACCIÓN"):
    base_url = "https://medlineplus.gov/spanish/healthtopics_"
    letras = "abcdefghijklmnopqrstuvw"
    datos_finales = []
    
    progreso = st.progress(0)
    status = st.empty()
    
    # Bucle de extracción
    for i, letra in enumerate(letras):
        status.markdown(f"🔍 Procesando letra: **{letra.upper()}**")
        try:
            r = requests.get(f"{base_url}{letra}.html", timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            enlaces = soup.select('section li a')
            
            for enlace in enlaces:
                nombre = enlace.get_text(strip=True)
                href = enlace.get('href', '')
                if "/spanish/" in href and "healthtopics" not in href:
                    url_tema = f"https://medlineplus.gov{href}" if href.startswith('/') else href
                    texto = obtener_texto(url_tema)
                    if texto:
                        datos_finales.append({
                            "Letra": letra.upper(),
                            "Tema": nombre,
                            "Contenido": texto,
                            "URL": url_tema
                        })
        except: continue
        
        progreso.progress((i + 1) / len(letras))
    
    if datos_finales:
        df = pd.DataFrame(datos_finales)
        st.success(f"✅ ¡Extracción completa! Se han encontrado {len(datos_finales)} temas.")
        
        st.subheader("📊 Previsualización de Datos")
        st.dataframe(df.head(10), use_container_width=True)

        # Botones de descarga
        col1, col2 = st.columns(2)
        with col1:
            excel_limpio = limpiar_excel_en_memoria(df)
            st.download_button(
                label="📥 Descargar EXCEL FORMATEADO",
                data=excel_limpio,
                file_name="medicina_limpia.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col2:
            st.download_button(
                label="📄 Descargar JSON",
                data=df.to_json(orient="records", force_ascii=False, indent=4),
                file_name="medicina_data.json",
                mime="application/json"
            )
    else:
        st.error("No se pudieron extraer datos. Revisa la URL.")