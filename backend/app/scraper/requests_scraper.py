"""
Scraper "liviano" basado en requests + BeautifulSoup.

Sirve para la actualizacion DIARIA: la pagina de precios del MAG muestra
por defecto el periodo/rueda mas reciente sin necesidad de completar
ningun formulario, asi que un GET simple alcanza.

Si el sitio tiene proteccion anti-bot (Cloudflare u otro WAF) este
scraper puede devolver 403 o una pagina de "challenge". En ese caso usar
`playwright_scraper.py`, que abre un navegador real y es mucho mas
robusto ante ese tipo de proteccion (a costa de ser mas lento y requerir
`playwright install chromium` una vez).

NOTA sobre este entorno de desarrollo: el sandbox donde se escribio este
proyecto tiene la salida de red restringida a una lista blanca de
dominios que NO incluye mercadoagroganadero.com.ar, asi que este scraper
no se pudo ejecutar en vivo aca. Probalo desde tu computadora o servidor,
que tiene salida a internet normal.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

import requests

from app.config import get_settings
from app.scraper.parser import parsear_tabla_precios, extraer_fecha_periodo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mag_scraper")

settings = get_settings()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}

# Ruta de la pagina de "Precios por categoria" segun la investigacion
# hecha para este proyecto. Ajustar si el MAG cambia sus URLs.
PATH_PRECIOS_ACTUALES = "/dll/hacienda1.dll/haciinfo000002"


def obtener_html_precios_actuales() -> str:
    session = requests.Session()
    session.headers.update(HEADERS)

    # Primero pisamos la home para levantar cookies de sesion, igual que
    # haria un navegador real.
    session.get(settings.mag_base_url, timeout=20)

    resp = session.get(settings.mag_base_url + PATH_PRECIOS_ACTUALES, timeout=20)
    resp.raise_for_status()
    return resp.text


def scrapear_precios_actuales(guardar_debug: bool = False) -> tuple[Optional[date], list[dict]]:
    """Devuelve (fecha_periodo, lista_de_registros_crudos)."""
    html = obtener_html_precios_actuales()

    if guardar_debug:
        import os

        os.makedirs("data/debug", exist_ok=True)
        ruta = f"data/debug/mag_{date.today().isoformat()}.html"
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write(html)
        logger.info("HTML crudo guardado en %s (para revisar selectores)", ruta)

    fecha_periodo = extraer_fecha_periodo(html)
    filas = parsear_tabla_precios(html)

    no_mapeadas = sorted({f["categoria_original"] for f in filas if f["categoria"] is None})
    if no_mapeadas:
        logger.warning(
            "Categorias sin mapear (agregalas a MAPA_CATEGORIAS en parser.py): %s",
            no_mapeadas,
        )

    return fecha_periodo, filas


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scraper de precios actuales del MAG (requests)")
    parser.add_argument("--debug-save", action="store_true", dest="debug")
    args = parser.parse_args()

    fecha, filas = scrapear_precios_actuales(guardar_debug=args.debug)
    print(f"Fecha detectada: {fecha}")
    for f in filas:
        print(f)
