import json
import logging
import time
import os

# --- ¡Importamos a nuestros "Hackers"! ---
from appaname_cerebro.parsers import bancochile_v1

# --- Configuración "Brutal" - PLAN B (v2.6 - Ruta Corregida a appaname-mapa) ---
# Ruta al archivo targets.json LOCAL (sube DOS niveles desde src/appaname_cerebro/main.py, entra a appaname-mapa)
LOCAL_TARGETS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'appaname-mapa', 'targets.json'))

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
             logger.error(f"¡ERROR BRUTAL! No se encontró el archivo local: {file_path}")
             logger.error("Asegúrate de que targets.json esté DENTRO de la carpeta 'appaname-mapa'.")
             return []

        with open(file_path, 'r', encoding='utf-8') as f:
            targets = json.load(f)

        logger.info(f"Mapa de Blancos local leído. {len(targets)} emisores (targets) encontrados.")
        return targets
    except json.JSONDecodeError as e:
        logger.error(f"¡ERROR BRUTAL! El archivo local targets.json ({file_path}) no es un JSON válido. Error: {e}")
        return []
    except Exception as e:
         logger.error(f"¡ERROR BRUTAL! No se pudo leer el archivo local: {e}")
         return []


def run_engine():
    """El orquestador principal del "Cerebro Maléfico" v2.6 (Plan B - Ruta Corregida)."""
    logger.info("--- [Cerebro Maléfico (Repo B) v2.6 INICIADO - MODO LOCAL] ---")

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
                time.sleep(1)
                botin_parcial = parser_function(source_url, category_hint, headers=REQUEST_HEADERS)

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

    logger.info("--- [Cerebro Maléfico (Repo B) v2.6 FINALIZADO - MODO LOCAL] ---")
    logger.info(f"Botín Total General Encontrado: {len(botin_total_general)} beneficios.")


if __name__ == "__main__":
    run_engine()
