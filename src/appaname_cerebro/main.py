import requests
import json
import logging

# --- Configuración "Brutal" ---
# La URL "cruda" (raw) de nuestro Mapa de Blancos (Repo A)
REPO_A_URL = "https://raw.githubusercontent.com/FranciscoJavier-tecnologia/appaname-mapa/main/targets.json"

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fetch_targets(url: str) -> list[dict]:
    """
    Paso 1: Lee el "Mapa de Blancos" (Repo A) v3.0 desde GitHub.
    """
    logger.info(f"Conectando al Mapa de Blancos v3.0 en: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status() 
        
        targets = response.json()
        logger.info(f"Mapa de Blancos leído. {len(targets)} emisores (targets) encontrados.")
        return targets

    except requests.exceptions.RequestException as e:
        logger.error(f"¡ERROR BRUTAL! No se pudo leer el Mapa de Blancos: {e}")
        return []
    except json.JSONDecodeError:
        logger.error("¡ERROR BRUTAL! El Mapa de Blancos (targets.json) no es un JSON válido.")
        return []

def run_engine():
    """
    El orquestador principal del "Cerebro Maléfico" v2.0.
    Ahora entiende la estructura de "segment" y "sources".
    """
    logger.info("--- [Cerebro Maléfico (Repo B) v2.0 INICIADO] ---")
    
    # 1. Leer el Mapa
    targets = fetch_targets(REPO_A_URL)
    
    if not targets:
        logger.warning("No hay objetivos para procesar. Apagando.")
        return

    # 2. Iterar sobre los EMISORES (targets)
    for target in targets:
        issuer_id = target.get('issuer_id')
        strategy = target.get('parser_strategy')
        segment = target.get('segment', 'Desconocido') # Obtenemos el nuevo campo
        sources = target.get('sources', [])         # Obtenemos la "chorrera" de URLs

        if not issuer_id or not strategy:
            logger.warning(f"Emisor inválido, saltando: {target}")
            continue
            
        logger.info(f"--- Procesando Emisor: '{issuer_id}' (Segmento: {segment}) ---")
        logger.info(f"Usando estrategia de hacking: '{strategy}'")

        if not sources:
            logger.warning(f"Emisor '{issuer_id}' no tiene 'sources' (URLs) definidas. Saltando.")
            continue
        
        # 3. Iterar sobre el "Banco de URLs" (sources) de CADA emisor
        for source in sources:
            source_id = source.get('source_id')
            source_url = source.get('url')
            category_hint = source.get('category_hint', 'N/A')

            if not source_id or not source_url:
                logger.warning(f"Fuente inválida para '{issuer_id}', saltando: {source}")
                continue

            logger.info(f"  -> Atacando fuente: '{source_id}' | URL: {source_url} | Pista: {category_hint}")
            
            # --- PRÓXIMO PASO: Aquí llamaremos al "parser" (el script de hacking) ---
            # try:
            #   botin_parcial = parsers.run(strategy, source_url, category_hint)
            #   botin_total_del_emisor.append(botin_parcial)
            # except Exception as e:
            #   logger.error(f"Falló el hacking para '{source_id}': {e}")
            pass

        # --- PRÓXIMO PASO 2: Aquí guardaremos el botín en el Repo C ---
        # logger.info(f"Guardando botín total para '{issuer_id}' en la Bóveda (Repo C)...")
        # vault.save(botin_total_del_emisor, issuer_id)
        
    logger.info("--- [Cerebro Maléfico (Repo B) v2.0 FINALIZADO] ---")


if __name__ == "__main__":
    run_engine()
