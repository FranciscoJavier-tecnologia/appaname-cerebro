import json
import logging
import time
import os

# --- ¡Importamos a nuestros "Hackers"! ---
from appaname_cerebro.parsers import bancochile_v1

# --- Configuración "Brutal" - PLAN B ---
LOCAL_TARGETS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'appaname-mapa', 'targets.json'))
LOCAL_VAULT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'appaname-catalogo', 'data', 'by-issuer'))

# --- Cabeceras SOLO con Disfraz ---
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PARSER_MAP = {
    'bancochile_v1': bancochile_v1.parse,
    # ... otros parsers
}

def fetch_targets(file_path: str) -> list[dict]:
    """Paso 1: Lee el "Mapa" (targets.json) desde un archivo LOCAL."""
    logger.info(f"Leyendo Mapa de Blancos LOCAL desde: {file_path}")
    try:
        if not os.path.exists(file_path):
             logger.error(f"¡ERROR CRÍTICO! No se encontró el archivo local: {file_path}")
             return []

        with open(file_path, 'r', encoding='utf-8') as f:
            targets = json.load(f)

        logger.info(f"Mapa local leído. {len(targets)} emisores (targets) encontrados.")
        return targets
    except json.JSONDecodeError as e:
        logger.error(f"¡ERROR CRÍTICO! El archivo local targets.json ({file_path}) no es un JSON válido. Error: {e}")
        return []
    except Exception as e:
         logger.error(f"¡ERROR CRÍTICO! No se pudo leer el archivo local: {e}")
         return []

# --- ¡NUEVA FUNCIÓN PARA GUARDAR EL BOTÍN! ---
def save_booty_to_vault(issuer_id: str, benefits: list, vault_path: str):
    """Guarda la lista de beneficios en el archivo JSON correspondiente en la Bóveda (Repo C)."""
    if not benefits:
        logger.warning(f"No hay botín para guardar para {issuer_id}.")
        return

    os.makedirs(vault_path, exist_ok=True)
    file_name = f"{issuer_id}.json"
    file_path = os.path.join(vault_path, file_name)
    logger.info(f"Guardando {len(benefits)} beneficios para '{issuer_id}' en: {file_path}")

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(benefits, f, ensure_ascii=False, indent=2) 
        logger.info(f"¡ÉXITO! Botín para '{issuer_id}' guardado.")
    except Exception as e:
        logger.error(f"¡FALLO AL GUARDAR! No se pudo escribir el botín para '{issuer_id}' en {file_path}. Error: {e}")


def run_engine():
    """El orquestador principal del "Cerebro Maléfico" v2.7 (Plan B - Con Guardado)."""
    logger.info("--- [Cerebro Maléfico (Repo B) v2.7 INICIADO - MODO LOCAL] ---") # <-- ¡VERSIÓN 2.7!

    targets = fetch_targets(LOCAL_TARGETS_PATH) 
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
            logger.warning(f"Estrategia de extracción '{strategy}' NO ENCONTRADA. Saltando emisor.")
            continue

        parser_function = PARSER_MAP[strategy]
        logger.info(f"Usando extractor: '{strategy}' (Función: {parser_function.__name__})")

        botin_total_emisor = []

        for source in sources:
            source_id = source.get('source_id')
            source_url = source.get('url')
            category_hint = source.get('category_hint', 'N/A')

            if not source_id or not source_url:
                logger.warning(f"Fuente inválida para '{issuer_id}', saltando: {source}")
                continue

            logger.info(f"  -> Procesando fuente: '{source_id}' | Pista: {category_hint}")

            try:
                time.sleep(1) 
                botin_parcial = parser_function(source_url, category_hint, headers=REQUEST_HEADERS) 

                if botin_parcial:
                    logger.info(f"  -> ÉXITO. {len(botin_parcial)} beneficios encontrados en esta fuente.")
                    botin_total_emisor.extend(botin_parcial)
                else:
                    logger.warning(f"  -> Fuente '{source_id}' no arrojó beneficios.")

            except Exception as e:
                logger.error(f"  -> ¡FALLO EXTRACCIÓN en '{source_id}'! Error: {e}")

        if botin_total_emisor:
            logger.info(f"Total para '{issuer_id}': {len(botin_total_emisor)} beneficios.")
            save_booty_to_vault(issuer_id, botin_total_emisor, LOCAL_VAULT_PATH)
            botin_total_general.extend(botin_total_emisor)
        else:
            logger.info(f"Total para '{issuer_id}': 0 beneficios.")

    logger.info("--- [Cerebro Maléfico (Repo B) v2.7 FINALIZADO - MODO LOCAL] ---") # <-- ¡VERSIÓN 2.7!
    logger.info(f"Botín Total General Encontrado: {len(botin_total_general)} beneficios.")


if __name__ == "__main__":
    run_engine()
