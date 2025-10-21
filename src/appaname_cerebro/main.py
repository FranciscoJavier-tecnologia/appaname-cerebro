import requests  # La herramienta para "atacar" HTTP
import json
import logging

# --- Configuración "Brutal" ---
# La URL "cruda" (raw) de nuestro Mapa de Blancos (Repo A)
# Asegúrate de que tu Repo A sea PÚBLICO para que esto funcione.
REPO_A_URL = "https://raw.githubusercontent.com/FranciscoJavier-tecnologia/appaname-mapa/main/targets.json"

# Configuración básica de logging para ver qué está pasando
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fetch_targets(url: str) -> list[dict]:
    """
    Paso 1: Lee el "Mapa de Blancos" (Repo A) desde GitHub.
    """
    logger.info(f"Conectando al Mapa de Blancos en: {url}")
    try:
        response = requests.get(url)
        # Si la petición falla (ej. 404), lanza un error
        response.raise_for_status() 
        
        targets = response.json()
        logger.info(f"Mapa de Blancos leído. {len(targets)} objetivos encontrados.")
        return targets

    except requests.exceptions.RequestException as e:
        logger.error(f"¡ERROR BRUTAL! No se pudo leer el Mapa de Blancos: {e}")
        return []
    except json.JSONDecodeError:
        logger.error("¡ERROR BRUTAL! El Mapa de Blancos (targets.json) no es un JSON válido.")
        return []

def run_engine():
    """
    El orquestador principal del "Cerebro Maléfico".
    """
    logger.info("--- [Cerebro Maléfico (Repo B) INICIADO] ---")
    
    # 1. Leer el Mapa
    targets = fetch_targets(REPO_A_URL)
    
    if not targets:
        logger.warning("No hay objetivos para procesar. Apagando.")
        return

    # 2. Iterar sobre los objetivos
    for target in targets:
        issuer_id = target.get('issuer_id')
        strategy = target.get('parser_strategy')
        
        if not issuer_id or not strategy:
            logger.warning(f"Objetivo inválido, saltando: {target}")
            continue
            
        logger.info(f"Procesando objetivo: '{issuer_id}' usando la estrategia '{strategy}'")
        
        # --- PRÓXIMO PASO: Aquí llamaremos al "parser" (el script de hacking) ---
        # ej: botin = parsers.run(strategy, target.get('source_url'))
        # ej: vault.save(botin, issuer_id)
        pass

    logger.info("--- [Cerebro Maléfico (Repo B) FINALIZADO] ---")


if __name__ == "__main__":
    run_engine()
