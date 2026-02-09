import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Extractor MSD Quirúrgico", page_icon="🔬", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, b, strong { color: #1e293b; font-weight: bold; }
    .stButton>button { background-color: #059669; color: white; font-weight: bold; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔬 Extractor Quirúrgico: Manual MSD")

# --- MOTOR DE EXTRACCIÓN MEJORADO ---
def extraer_msd_definitivo(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        time.sleep(random.uniform(1.0, 2.0))
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code != 200:
            return {"tipo": "error", "contenido": f"Error {r.status_code}"}
        
        soup = BeautifulSoup(r.content, 'html.parser')

        # --- PRIORIDAD 1: BUSCAR TEXTO (ARTÍCULO) ---
        # MSD usa estas clases para el contenido real
        cuerpo = (
            soup.find('div', class_='topic__explanation') or 
            soup.find('section', class_='topic__full') or
            soup.find('div', id='topic-content') or
            soup.find('div', class_='para') # A veces el texto está en paras sueltos
        )

        # Si encontramos suficientes párrafos, es un ARTÍCULO
        if cuerpo:
            parrafos = [p.get_text(" ", strip=True) for p in cuerpo.find_all(['p', 'h2', 'h3']) if len(p.get_text()) > 40]
            if len(parrafos) > 2: # Si hay más de 2 párrafos, es contenido
                return {"tipo": "articulo", "contenido": "\n\n".join(parrafos)}

        # --- PRIORIDAD 2: BUSCAR ENLACES (ÍNDICE) ---
        enlaces = soup.select('.topic__link') or soup.select('.moduletable a') or soup.select('a[href*="/professional/"]')
        if enlaces:
            lista = []
            for e in enlaces:
                nombre = e.get_text(strip=True)
                href = e.get('href')
                if href and "/professional/" in href and len(nombre) > 3:
                    full_url = f"https://www.msdmanuals.com{href}" if href.startswith('/') else href
                    if full_url != url: # Evitar bucle infinito a la misma página
                        lista.append({"Tema": nombre, "URL": full_url})
            
            if lista:
                return {"tipo": "indice", "contenido": lista}

        return {"tipo": "error", "contenido": "No se encontró ni texto ni enlaces útiles."}
    except Exception as e:
        return {"tipo": "error", "contenido": str(e)}

def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
        ws = writer.sheets['Sheet1']
        ws.column_dimensions['B'].width = 110
        for cell in ws['B']:
            cell.alignment = Alignment(wrap_text=True, vertical='top')
    return output.getvalue()

# --- INTERFAZ ---
url_input = st.text_input("URL de MSD (Índice o Tema):", "https://www.msdmanuals.com/es/professional/health-topics")

if st.button("🚀 EXTRAER AHORA"):
    with st.spinner("Accediendo a la base de datos de MSD..."):
        res = extraer_msd_definitivo(url_input)
        
        if res["tipo"] == "articulo":
            st.success("✅ ¡CONTENIDO EXTRAÍDO!")
            st.markdown(f"**URL:** {url_input}")
            st.text_area("Texto del Manual:", res["contenido"], height=450)
            
            df = pd.DataFrame([{"URL": url_input, "Contenido": res["contenido"]}])
            st.download_button("📥 Guardar en Excel", data=generar_excel(df), file_name="manual_msd_texto.xlsx")
            
        elif res["tipo"] == "indice":
            st.info("📂 Has entrado en una CATEGORÍA. Selecciona un tema específico:")
            df_links = pd.DataFrame(res["contenido"]).drop_duplicates(subset=['Tema'])
            st.table(df_links)
            st.markdown("👇 **Copia la URL del tema que quieras y pégala arriba para extraer su texto.**")
            
        else:
            st.error(res["contenido"])