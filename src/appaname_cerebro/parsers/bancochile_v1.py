import requests # <--- IMPORT ARREGLADO
from bs4 import BeautifulSoup, Tag
import logging
import time
from urllib.parse import urljoin
from typing import List, Dict, Optional
try:
    # Importamos Playwright y añadimos BrowserContext para manejar pestañas
    from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError
except ImportError:
    sync_playwright = None
    PlaywrightTimeoutError = Exception

logger = logging.getLogger(__name__)

BenefitSchema = dict # Placeholder

# --- Constantes Playwright ---
WAIT_FOR_SELECTOR_TIMEOUT = 15000 # 15 segundos (en milisegundos)

# --- Selectores CSS (Base + Intentos Genéricos) ---
CARD_SELECTOR_BASE = "a.card.group.border-gray-background"
CARD_TEXT_SELECTORS = "p"
DETAIL_TITLE_SELECTOR = "h1"
DETAIL_RULES_SELECTOR = "div.rules-section-class-example"
DETAIL_LOCATION_SELECTOR = "div.location-info-class-example p"

# --- Helper Functions ---
def safe_get_text(element: Optional[Tag]) -> Optional[str]:
    return ' '.join(element.text.split()) if element else None

def safe_get_attribute(element: Optional[Tag], attribute: str) -> Optional[str]:
    return element.get(attribute) if element else None

# --- Nivel 2: Scraping Detalle (Ahora con Playwright) ---
def scrape_detail_page(context: BrowserContext, detail_url: str) -> Dict:
    """
    Intenta extraer info de detalle usando una NUEVA PESTAÑA de Playwright.
    ¡Selectores necesitan validación!
    """
    logger.info(f"    -> [Nivel 2] Abriendo detalle en nueva pestaña: {detail_url}")
    details = {"detail_title": None, "rules_text": None, "locations": []}
    page = None
    try:
        page = context.new_page()
        page.goto(detail_url, timeout=30000, wait_until='domcontentloaded')
        logger.info(f"      -> Conexión detalle OK. Analizando...")

        # Extraer Título Detalle (h1 como intento inicial)
        title_element = page.query_selector(DETAIL_TITLE_SELECTOR)
        details["detail_title"] = title_element.text_content().strip() if title_element else None
        # ... (Lógica extracción reglas/ubicación pendiente) ...

        return details

    except PlaywrightTimeoutError:
        logger.error(f"      -> TIMEOUT al cargar página de detalle: {detail_url}")
        return details
    except Exception as e:
        logger.exception(f"      -> Error inesperado durante análisis de detalle: {e}")
        return details
    finally:
         if page:
             page.close()

# --- Nivel 1: Scraping Lista con Playwright (Función Principal v4.0) ---
def parse(source_url: str, category_hint: str, headers: dict = None) -> List[Dict]:
    """Extractor (Parser) Resiliente para Banco de Chile v4.0."""
    logger.info(f"  [Extractor 'bancochile_v1' v4.0 Resiliente iniciado]")
    logger.info(f"  -> [Nivel 1] Accediendo a URL lista: {source_url}")

    if sync_playwright is None:
         logger.error("¡Playwright no está instalado!")
         return []

    extracted_benefits = []

    # Usamos el selector base ahora definido globalmente
    card_selector = CARD_SELECTOR_BASE
    logger.info(f"    -> Usando selector de tarjeta base: '{card_selector}'")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=headers.get('User-Agent') if headers else None)
        page = context.new_page()

        try:
            logger.info(f"  -> Navegando a {source_url} con navegador virtual...")
            page.goto(source_url, timeout=30000, wait_until='domcontentloaded')

            logger.info(f"  -> Página base cargada. Esperando tarjetas ('{card_selector}')...")
            try:
                page.wait_for_selector(card_selector, timeout=WAIT_FOR_SELECTOR_TIMEOUT)
                logger.info(f"  -> ¡Tarjetas detectadas con selector base!")
            except PlaywrightTimeoutError:
                logger.error(f"  -> ¡TIMEOUT! No aparecieron tarjetas ('{card_selector}') tras {WAIT_FOR_SELECTOR_TIMEOUT/1000} seg.")

            logger.info(f"  -> Obteniendo HTML renderizado...")
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            benefit_cards = soup.select(card_selector)
            logger.info(f"  -> Se encontraron {len(benefit_cards)} tarjetas con selector '{card_selector}' en el HTML final.")

            if not benefit_cards:
                logger.warning("  -> No se procesarán tarjetas.")

            for i, card_link in enumerate(benefit_cards):
                logger.info(f"    -> Procesando tarjeta {i+1}/{len(benefit_cards)}...")

                card_texts = [safe_get_text(p) for p in card_link.select(CARD_TEXT_SELECTORS)]
                card_texts = [text for text in card_texts if text]

                list_title = card_texts[0] if card_texts else "Título no encontrado"
                list_discount_text = card_texts[1] if len(card_texts) > 1 else "Descuento no encontrado"
                list_desc_short = card_texts[2] if len(card_texts) > 2 else None

                detail_url_relative = safe_get_attribute(card_link, 'href')

                if detail_url_relative:
                    detail_url_absolute = urljoin(source_url, detail_url_relative)
                    logger.info(f"      -> Info Nivel 1: Título='{list_title}', Dcto='{list_discount_text}', Desc='{list_desc_short}'")

                    detail_info = scrape_detail_page(context, detail_url_absolute)

                    benefit_data = { # Mapeo igual que antes
                       "issuer_id": "banco_de_chile",
                        "benefit_uid": f"bch-{int(time.time()*1000)}-{len(extracted_benefits)}",
                        "title": detail_info.get("detail_title") or list_title,
                        "description_short": list_desc_short or list_discount_text,
                        "description_rules": detail_info.get("rules_text"),
                        "discount": {"type": "TEXT", "value": list_discount_text},
                        "validity": {"from": "TBD", "to": "TBD"},
                        "redemption": {"type": "TBD"},
                        "geo_scope": "TBD" if not detail_info.get("locations") else "SPECIFIC_STORES",
                        "locations": detail_info.get("locations", []),
                        "provenance": {
                            "source_url": detail_url_absolute,
                            "last_verified_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                            "parser_strategy_used": "bancochile_v1"
                        },
                        "category_hint": category_hint
                    }
                    extracted_benefits.append(benefit_data)
                else:
                    logger.warning(f"  -> Tarjeta {i+1} encontrada pero falta link detalle ('href').")

        except PlaywrightTimeoutError:
             logger.error(f"  -> ¡TIMEOUT INICIAL! No aparecieron tarjetas ('{card_selector}') tras {WAIT_FOR_SELECTOR_TIMEOUT/1000} seg.")
        except Exception as e:
            logger.exception(f"  -> Error inesperado durante ejecución con Playwright: {e}")
        finally:
            if 'browser' in locals() and browser.is_connected():
                browser.close()
                logger.info("  -> Navegador virtual cerrado.")

    logger.info(f"  -> Extracción completada para {source_url}. {len(extracted_benefits)} beneficios encontrados.")
    return extracted_benefits

