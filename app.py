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
st.set_page_config(page_title="Extractor MSD Fuerza Bruta", page_icon="🧪", layout="wide")

st.title("🧪 Extractor de Datos MSD: Modo Fuerza Bruta")
st.markdown("**Instrucciones:** Pega la URL del artículo final (ej. el de *Dolor abdominal agudo*).")

def extraer_msd_fuerza_bruta(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        # Pausa aleatoria para evitar detección
        time.sleep(random.uniform(2, 4))
        session = requests.Session()
        r = session.get(url, headers=headers, timeout=25)
        
        if r.status_code != 200:
            return {"tipo": "error", "contenido": f"Bloqueo del Servidor (Código {r.status_code})"}
        
        soup = BeautifulSoup(r.content, 'html.parser')

        # --- LIMPIEZA RADICAL ---
        # Eliminamos todo lo que NO sea contenido para que no nos confunda
        for basura in soup(['nav', 'header', 'footer', 'script', 'style', 'aside', 'form', 'button']):
            basura.decompose()

        # --- BÚSQUEDA MULTI-CAPA ---
        # 1. Intentamos por la clase principal de MSD
        cuerpo = soup.select_one('.topic__explanation') or soup.select_one('.topic__full') or soup.select_one('#topic-content')
        
        # 2. Si falla, buscamos cualquier div que contenga muchos párrafos
        if not cuerpo:
            divs = soup.find_all('div')
            cuerpo = max(divs, key=lambda d: len(d.find_all('p')), default=None)

        if cuerpo:
            # Extraemos párrafos y títulos
            elementos = cuerpo.find_all(['p', 'h2', 'h3', 'h4', 'li'])
            texto_final = []
            for el in elementos:
                limpio = el.get_text(" ", strip=True)
                if len(limpio) > 35: # Filtro para evitar menús cortos
                    texto_final.append(limpio)
            
            if len(texto_final) > 3:
                return {"tipo": "articulo", "contenido": "\n\n".join(texto_final)}

        # --- SI TODO FALLA, BUSCAMOS ENLACES ---
        enlaces = soup.find_all('a', href=True)
        links_validos = []
        for l in enlaces:
            nombre = l.get_text(strip=True)
            href = l.get('href')
            if "/professional/" in href and len(nombre) > 10:
                links_validos.append({"Tema": nombre, "URL": f"https://www.msdmanuals.com{href}" if href.startswith('/') else href})
        
        if links_validos:
            return {"tipo": "indice", "contenido": links_validos}
            
        return {"tipo": "error", "contenido": "Página protegida o vacía. MSD ha bloqueado la IP del servidor."}

    except Exception as e:
        return {"tipo": "error", "contenido": str(e)}

# --- INTERFAZ ---
url_input = st.text_input("URL Final del Artículo:", placeholder="Pega aquí el enlace del tema...")

if st.button("🚀 EXTRAER TEXTO AHORA"):
    if url_input:
        with st.spinner("Intentando romper el bloqueo de MSD..."):
            res = extraer_msd_fuerza_bruta(url_input)
            
            if res["tipo"] == "articulo":
                st.success("✅ ¡ÉXITO! Texto capturado.")
                st.text_area("Resultado:", res["contenido"], height=500)
                
                # Descarga Excel
                df = pd.DataFrame([{"URL": url_input, "Contenido": res["contenido"]}])
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button("📥 Descargar Excel", data=output.getvalue(), file_name="msd_extraido.xlsx")
                
            elif res["tipo"] == "indice":
                st.warning("⚠️ No se encontró el texto, pero sí estos temas:")
                st.table(pd.DataFrame(res["contenido"]).drop_duplicates())
            else:
                st.error(res["contenido"])