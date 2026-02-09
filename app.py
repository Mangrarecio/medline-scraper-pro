import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Extractor MSD Élite", page_icon="🔬", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1, h2, b, strong { color: #1e293b; font-weight: bold; }
    .stButton>button { background-color: #d97706; color: white; font-weight: bold; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔬 Extractor Especializado: Manual MSD")
st.info("Pega una URL de MSD. Puede ser el índice general o un tema específico.")

# --- MOTOR DE NAVEGACIÓN PROFUNDA ---
def extraer_msd(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        # Pausa para no ser detectado como bot
        time.sleep(random.uniform(1.5, 3.0))
        r = requests.get(url, headers=headers, timeout=20)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # CASO 1: Es una página de artículo
            contenedor = soup.find('section', class_='topic__full') or soup.find('div', class_='topic__explanation')
            if contenedor:
                parrafos = [p.get_text(" ", strip=True) for p in contenedor.find_all(['p', 'h2', 'h3']) if len(p.get_text()) > 40]
                return {"tipo": "articulo", "contenido": "\n\n".join(parrafos)}
            
            # CASO 2: Es una página de índice (lista de enlaces)
            enlaces = soup.select('.topic__link') or soup.select('a[href*="/professional/"]')
            if enlaces:
                lista_temas = []
                for e in enlaces[:20]: # Limitamos para evitar bloqueos
                    nombre = e.get_text(strip=True)
                    href = e.get('href')
                    if href and "/professional/" in href:
                        full_url = f"https://www.msdmanuals.com{href}" if href.startswith('/') else href
                        lista_temas.append({"Tema": nombre, "URL": full_url})
                return {"tipo": "indice", "contenido": lista_temas}
                
        return {"tipo": "error", "contenido": f"Código de respuesta: {r.status_code}"}
    except Exception as e:
        return {"tipo": "error", "contenido": str(e)}

# --- INTERFAZ DE USUARIO ---
url_input = st.text_input("URL de MSD:", "https://www.msdmanuals.com/es/professional/health-topics")

if st.button("🚀 INICIAR EXTRACCIÓN MSD"):
    with st.spinner("Analizando estructura de MSD..."):
        resultado = extraer_msd(url_input)
        
        if resultado["tipo"] == "articulo":
            st.success("✅ Artículo extraído.")
            st.text_area("Contenido:", resultado["contenido"], height=400)
            df = pd.DataFrame([{"URL": url_input, "Contenido": resultado["contenido"]}])
            st.download_button("📥 Descargar Tema", data=df.to_csv(index=False), file_name="msd_tema.csv")
            
        elif resultado["tipo"] == "indice":
            st.warning("📂 Has pegado un ÍNDICE. Aquí tienes los temas encontrados (primeros 20):")
            df_enlaces = pd.DataFrame(resultado["contenido"])
            st.table(df_enlaces)
            st.info("Para extraer el contenido de uno de estos, copia su URL y pégala arriba.")
            
        else:
            st.error(f"No se pudo acceder: {resultado['contenido']}")
            st.markdown("**Nota:** MSD bloquea a veces las conexiones desde la nube. Si falla, intenta con una URL de un tema concreto.")