import requests # <--- ¡EL IMPORT ARREGLADO!
from bs4 import BeautifulSoup, Tag 
import logging
import time
from urllib.parse import urljoin
from typing import List, Dict, Optional
try:
    from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError
except ImportError:
    sync_playwright = None
    PlaywrightTimeoutError = Exception 

logger = logging.getLogger(__name__)

BenefitSchema = dict # Placeholder

# --- Constantes Playwright ---
WAIT_FOR_SELECTOR_TIMEOUT = 30000 # 30 segundos

# --- Selectores CSS Refinados (¡Tu Inteligencia!) ---
CARD_SELECTOR_BASE = "a.card.group.border-gray-background" 
# Patrón 1 (/mascotas)
MASCOTAS_TITLE_SELECTOR = "p.font-400.text-3.text-gray-dark" 
MASCOTAS_DISCOUNT_SELECTOR = "p.font-700.text-3.text-primary" 
# Patrón 2 (/sabores, /panoramas, /viajes, /bienestar, etc.)
PATRON2_TITLE_SELECTOR = "p.font-700.text-3.text-gray-dark.mb-2.overflow-ellipsis"
PATRON2_DISCOUNT_SELECTOR = "p.font-700.text-3.text-primary.mb-2.overflow-ellipsis"

# --- Selectores Nivel 2 (Detalle - ¡Tu Inteligencia!) ---
DETAIL_TITLE_SELECTOR = "h2.beneficio-title" # ej. "50% dto. todos los lunes..."
DETAIL_VIGENCIA_SELECTOR = "p#validez.beneficio-vigencia"
DETAIL_RULES_CONTAINER_SELECTOR = "div.text-gray.mb-5 ul" # El <ul> que contiene los <li>
DETAIL_LOCATION_CARD_SELECTOR = "div.sucursal.shadow-md" # El contenedor de la sucursal
DETAIL_LOCATION_ADDRESS_SELECTOR = "h4.text-1.font-600" # ej. "Isidora Goyenechea #3477"
DETAIL_LOCATION_COMMUNE_SELECTOR = "p.text-1.text-gray-light" # ej. "Región Metropolitana - Las Condes"

# --- Helper Functions ---
def safe_get_text(element: Optional[Tag]) -> Optional[str]:
    return ' '.join(element.text.split()) if element else None
def safe_get_attribute(element: Optional[Tag], attribute: str) -> Optional[str]:
    return element.get(attribute) if element else None

# --- Nivel 2: Scraping Detalle (¡Ahora con esteroides!) ---
def scrape_detail_page(detail_url: str, headers: dict) -> Dict:
    """Intenta extraer info de detalle usando requests."""
    logger.info(f"    -> [Nivel 2] Procesando detalle: {detail_url}")
    details = {
        "detail_title": None,
        "rules": [], # Lista para reglas
        "validity_text": None,
        "locations": [] # Lista para direcciones
    }
    try:
        time.sleep(0.7) 
        response = requests.get(detail_url, headers=headers, timeout=20) 
        response.raise_for_status()
        logger.info(f"      -> Conexión detalle OK (200). Analizando...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- Extraer Título Detalle ---
        title_element = soup.select_one(DETAIL_TITLE_SELECTOR) 
        details["detail_title"] = safe_get_text(title_element)
        if details["detail_title"]:
             logger.info(f"        -> Título detalle (h2.beneficio-title): '{details['detail_title']}'")
        else:
             logger.warning(f"        -> No se encontró título de detalle con selector '{DETAIL_TITLE_SELECTOR}'")
        
        # --- Extraer Vigencia ---
        validity_element = soup.select_one(DETAIL_VIGENCIA_SELECTOR)
        details["validity_text"] = safe_get_text(validity_element)

        # --- Extraer Reglas ---
        rules_container = soup.select_one(DETAIL_RULES_CONTAINER_SELECTOR)
        if rules_container:
            rules_list = rules_container.select("li") # Buscamos todos los <li> dentro del <ul>
            details["rules"] = [safe_get_text(rule) for rule in rules_list if safe_get_text(rule)]
            logger.info(f"        -> {len(details['rules'])} reglas encontradas.")
        else:
            logger.warning(f"        -> No se encontró contenedor de reglas con '{DETAIL_RULES_CONTAINER_SELECTOR}'")

        # --- Extraer Ubicaciones ---
        location_cards = soup.select(DETAIL_LOCATION_CARD_SELECTOR)
        if location_cards:
            for card in location_cards:
                address_element = card.select_one(DETAIL_LOCATION_ADDRESS_SELECTOR)
                commune_element = card.select_one(DETAIL_LOCATION_COMMUNE_SELECTOR)
                
                address = safe_get_text(address_element)
                commune = safe_get_text(commune_element)
                full_address = f"{address}, {commune}" if address and commune else address
                
                if full_address:
                    logger.info(f"        -> Ubicación encontrada: '{full_address}'")
                    details["locations"].append({
                        "address": full_address,
                        "lat": None, # Geocoding pendiente
                        "lon": None  # Geocoding pendiente
                    })
        else:
            logger.warning(f"        -> No se encontraron tarjetas de ubicación con '{DETAIL_LOCATION_CARD_SELECTOR}'")
        
        return details
    except requests.exceptions.RequestException as e:
        logger.error(f"      -> Error de conexión en detalle: {e}")
        return details
    except Exception as e:
        logger.error(f"      -> Error durante análisis de detalle: {e}")
        return details


# --- Nivel 1: Scraping Lista (Adaptativo v5.0) ---
def parse(source_url: str, category_hint: str, headers: dict = None) -> List[Dict]:
    """Extractor (Parser) Adaptativo para Banco de Chile v5.0 (Completo)."""
    logger.info(f"  [Extractor 'bancochile_v1' v5.0 iniciado]")
    logger.info(f"  -> [Nivel 1] Procesando URL lista: {source_url}")

    if sync_playwright is None:
         logger.error("¡Playwright no está instalado!")
         return []

    extracted_benefits = []
    
    # --- Lógica de Selección Adaptativa ---
    card_selector = CARD_SELECTOR_BASE 
    if "/mascotas" in source_url:
        title_selector = MASCOTAS_TITLE_SELECTOR
        discount_selector = MASCOTAS_DISCOUNT_SELECTOR
        logger.info("    -> Usando selectores 'Patrón 1' (Mascotas)")
    elif any(s in source_url for s in ["/sabores", "/panoramas", "/viajes", "/bienestar", "/sustentable", "/delivery", "/marcas"]):
        title_selector = PATRON2_TITLE_SELECTOR
        discount_selector = PATRON2_DISCOUNT_SELECTOR
        logger.info(f"    -> Usando selectores 'Patrón 2' (Sabores, Panoramas, etc.)")
    else: # Default
        title_selector = MASCOTAS_TITLE_SELECTOR 
        discount_selector = MASCOTAS_DISCOUNT_SELECTOR
        logger.warning(f"    -> URL no reconocida. Usando selectores por defecto (Patrón 1).")
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context(user_agent=headers.get('User-Agent') if headers else None)
        page = context.new_page()

        try:
            logger.info(f"  -> Navegando a {source_url} con navegador virtual...")
            page.goto(source_url, timeout=30000, wait_until='domcontentloaded') 

            logger.info(f"  -> Página base cargada. Esperando tarjetas ('{card_selector}')...")
            page.wait_for_selector(card_selector, timeout=WAIT_FOR_SELECTOR_TIMEOUT) 
            logger.info(f"  -> ¡Tarjetas detectadas! Obteniendo HTML...")

            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            benefit_cards = soup.select(card_selector) 
            logger.info(f"  -> Se encontraron {len(benefit_cards)} tarjetas con selector '{card_selector}'.")

            if not benefit_cards:
                logger.warning("  -> No se encontraron tarjetas.")
            
            for card_link in benefit_cards:
                title_element = card_link.select_one(title_selector) 
                discount_element = card_link.select_one(discount_selector) 
                detail_url_relative = safe_get_attribute(card_link, 'href') 

                if title_element and detail_url_relative:
                    list_title = safe_get_text(title_element)
                    list_discount_text = safe_get_text(discount_element)
                    detail_url_absolute = urljoin(source_url, detail_url_relative) 
                    
                    logger.info(f"    * Título: '{list_title}' | Dcto: '{list_discount_text}'")
                    
                    detail_info = scrape_detail_page(detail_url_absolute, headers)
                    
                    # --- Mapeo a Schema v1.0 (Más completo) ---
                    benefit_data = {
                        "issuer_id": "banco_de_chile",
                        "benefit_uid": f"bch-{int(time.time()*1000)}-{len(extracted_benefits)}", 
                        "title": detail_info.get("detail_title") or list_title, # Título de detalle es mejor
                        "description_short": list_discount_text, 
                        "description_rules": ' '.join(detail_info.get("rules", [])) or detail_info.get("validity_text"), # Une todas las reglas
                        "discount": {"type": "TEXT", "value": list_discount_text if list_discount_text else 0}, 
                        "validity": {"from": "TBD", "to": "TBD", "text": detail_info.get("validity_text")}, # Guardamos texto vigencia
                        "redemption": {"type": "TBD"}, 
                        "geo_scope": "SPECIFIC_STORES" if detail_info.get("locations") else "NATIONAL", 
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
                    missing = []
                    if not title_element: missing.append(f"título (selector: {title_selector})")
                    if not detail_url_relative: missing.append("link detalle")
                    logger.warning(f"  -> Tarjeta encontrada pero falta { ' y '.join(missing) }.")

        except PlaywrightTimeoutError:
             logger.error(f"  -> ¡TIMEOUT! No aparecieron tarjetas ('{card_selector}') tras {WAIT_FOR_SELECTOR_TIMEOUT/1000} seg.")
        except Exception as e:
            logger.exception(f"  -> Error inesperado durante ejecución Playwright: {e}") 
        finally:
            browser.close() 
            logger.info("  -> Navegador virtual cerrado.")

    logger.info(f"  -> Extracción completada para {source_url}. {len(extracted_benefits)} beneficios encontrados.")
    return extracted_benefits
    
