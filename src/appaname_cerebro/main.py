import requests
import json
import logging
import time
import os # Necesario para variables de entorno (futuro)

# --- ¡Importamos a nuestros "Hackers"! ---
# Esta línea le dice a main.py que "sabe" cómo funciona el parser de bancochile
from appaname_cerebro.parsers import bancochile_v1

# --- Configuración "Brutal" ---
REPO_A_URL = "https://raw.githubusercontent.com/FranciscoJavier-tecnologia/appaname-mapa/main/targets.json"

# --- TU NUEVO TOKEN (¡Reemplázalo SOLO LOCALMENTE si el repo es PÚBLICO!) ---
# !! Temporalmente aquí para probar. Luego lo moveremos !!
GITHUB_TOKEN = "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"

# --- Cabeceras con Disfraz Y Token ---
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Authorization': f'token {GITHUB_TOKEN}' # Así nos autenticamos
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PARSER_MAP = {
    'bancochile_v1': bancochile_v1.parse,
    # ... otros parsers (los añadiremos después)
}

def fetch_targets(url: str) -> list[dict]:
    """Paso 1: Lee el "Mapa" (Repo A) v3.0, ¡autenticado con token!"""
    logger.info(f"Conectando al Mapa de Blancos v3.0 en: {url} (AUTENTICADO)")
    # --- Modificación: Usar token solo si está definido ---
    headers_to_use = REQUEST_HEADERS.copy()
    if not GITHUB_TOKEN or GITHUB_TOKEN == "TU_NUEVO_TOKEN_AQUI":
        logger.warning("Token de GitHub no configurado. Realizando petición anónima.")
        headers_to_use.pop('Authorization', None) # Elimina la cabecera si no hay token
    # --- Fin Modificación ---
    
    try:
        # --- ¡Aplicamos cabeceras (con o sin token)! ---
        response = requests.get(url, headers=headers_to_use, timeout=15)
        
        response.raise_for_status() # Lanza error si no es 200 OK
        
        targets = response.json()
        logger.info(f"Mapa de Blancos leído. {len(targets)} emisores (targets) encontrados.")
        return targets
    except requests.exceptions.RequestException as e:
        # Si el error es 401, el token está mal
        if e.response is not None and e.response.status_code == 401:
             logger.error("¡ERROR BRUTAL! Token de GitHub inválido o expirado (Error 401). Verifica el GITHUB_TOKEN.")
        # Si el error es 404, el repo o archivo no existe
        elif e.response is not None and e.response.status_code == 404:
             logger.error(f"¡ERROR BRUTAL! No se encontró el Mapa de Blancos en la URL (Error 404): {url}")
        # Si el error es 429 (incluso con token?), informarlo
        elif e.response is not None and e.response.status_code == 429:
             logger.error(f"¡ERROR BRUTAL! Rate Limit (429) incluso con autenticación. Revisa conexión/IP. Error: {e}")
        else:
            logger.error(f"¡ERROR BRUTAL! No se pudo leer el Mapa de Blancos: {e}")
        return []
    except json.JSONDecodeError:
        logger.error("¡ERROR BRUTAL! El Mapa de Blancos (targets.json) descargado no es un JSON válido.")
        return []

def run_engine():
    """El orquestador principal del "Cerebro Maléfico" v2.3 (con token)."""
    logger.info("--- [Cerebro Maléfico (Repo B) v2.3 INICIADO] ---")
    
    targets = fetch_targets(REPO_A_URL)
    if not targets:
        logger.warning("No hay objetivos para procesar. Apagando.")
        return

    botin_total_general = []

    for target in targets:
        issuer_id = target.get('issuer_id')
        strategy = target.get('parser_strategy')
        segment = target.get('segment', 'Desconocido')
        sources = target.get('sources', [])

        if not issuer_id or not strategy:
            logger.warning(f"Emisor inválido, saltando: {target}")
            continue
            
        logger.info(f"--- Procesando Emisor: '{issuer_id}' (Segmento: {segment}) ---")
        
        if strategy not in PARSER_MAP:
            logger.warning(f"Estrategia de hacking '{strategy}' NO ENCONTRADA. Saltando emisor.")
            continue
        
        parser_function = PARSER_MAP[strategy]
        logger.info(f"Usando estrategia de hacking: '{strategy}' (Función: {parser_function.__name__})")

        botin_total_emisor = []
        for source in sources:
            source_id = source.get('source_id')
            source_url = source.get('url')
            category_hint = source.get('category_hint', 'N/A')

            if not source_id or not source_url:
                logger.warning(f"Fuente inválida para '{issuer_id}', saltando: {source}")
                continue

            logger.info(f"  -> Atacando fuente: '{source_id}' | Pista: {category_hint}")
            
            try:
                time.sleep(1) # Pequeño retraso cortés
                botin_parcial = parser_function(source_url, category_hint)
                
                if botin_parcial:
                    logger.info(f"  -> ÉXITO. {len(botin_parcial)} beneficios encontrados en esta fuente.")
                    botin_total_emisor.extend(botin_parcial)
                else:
                    logger.warning(f"  -> Fuente '{source_id}' no arrojó beneficios.")

            except Exception as e:
                logger.error(f"  -> ¡FALLÓ EL HACKING en '{source_id}'! Error: {e}")
            
        if botin_total_emisor:
            logger.info(f"Total para '{issuer_id}': {len(botin_total_emisor)} beneficios. (Pendiente guardar en Repo C)")
            botin_total_general.extend(botin_total_emisor)
        
    logger.info("--- [Cerebro Maléfico (Repo B) v2.3 FINALIZADO] ---")
    logger.info(f"Botín Total General Encontrado: {len(botin_total_general)} beneficios.")


if __name__ == "__main__":
    run_engine()
