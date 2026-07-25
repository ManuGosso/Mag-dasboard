"""
Scraper "robusto" usando Playwright (navegador real headless).

Se usa como respaldo si `requests_scraper.py` falla (por ejemplo, por
proteccion anti-bot), y tambien para la carga HISTORICA: permite
completar el formulario de "Fecha Inicial / Fecha Final" que tiene la
pagina de precios y navegar rueda por rueda o rango por rango.

Requisitos (una sola vez):
    pip install playwright
    playwright install chromium

Uso:
    # precios de hoy
    python -m app.scraper.playwright_scraper

    # backfill historico por rango de fechas
    python -m app.scraper.playwright_scraper --desde 2021-07-01 --hasta 2026-07-19

NOTA: igual que el scraper liviano, esto no se pudo probar en vivo desde
este entorno de desarrollo por la lista blanca de red del sandbox. El
codigo intenta ser robusto (busca los campos de fecha por su label/
placeholder en vez de por un id fijo) pero puede necesitar un ajuste
puntual de selectores la primera vez que se corra contra el sitio real;
para eso sirve --debug-save, que guarda screenshot + HTML de cada paso.
"""
from __future__ import annotations

import argparse
import logging
import os
from datetime import date, datetime, timedelta
from typing import Optional

from app.config import get_settings
from app.scraper.parser import parsear_tabla_precios, extraer_fecha_periodo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mag_scraper_playwright")

settings = get_settings()
PATH_PRECIOS = "/dll/hacienda1.dll/haciinfo000002"

# Textos candidatos para ubicar los inputs de fecha y el boton de buscar.
# Se prueban en orden hasta que uno funcione.
CANDIDATOS_LABEL_DESDE = ["Fecha Inicial", "Desde", "Fecha desde"]
CANDIDATOS_LABEL_HASTA = ["Fecha Final", "Hasta", "Fecha hasta"]
CANDIDATOS_BOTON_BUSCAR = ["Buscar", "Consultar", "Ver", "Filtrar"]


def _guardar_debug(page, etiqueta: str):
    os.makedirs("data/debug", exist_ok=True)
    page.screenshot(path=f"data/debug/{etiqueta}.png", full_page=True)
    with open(f"data/debug/{etiqueta}.html", "w", encoding="utf-8") as fh:
        fh.write(page.content())


def _completar_formulario_fecha(page, desde: date, hasta: date, debug: bool) -> bool:
    """Intenta encontrar y completar los campos de fecha. Devuelve True si
    pudo enviar el formulario."""
    from playwright.sync_api import TimeoutError as PWTimeout

    input_desde = None
    for label in CANDIDATOS_LABEL_DESDE:
        try:
            candidato = page.get_by_label(label, exact=False)
            if candidato.count() > 0:
                input_desde = candidato.first
                break
        except Exception:  # noqa: BLE001
            continue

    input_hasta = None
    for label in CANDIDATOS_LABEL_HASTA:
        try:
            candidato = page.get_by_label(label, exact=False)
            if candidato.count() > 0:
                input_hasta = candidato.first
                break
        except Exception:  # noqa: BLE001
            continue

    if input_desde is None or input_hasta is None:
        # Fallback: cualquier input type=date o type=text cerca de texto "fecha"
        inputs = page.locator("input[type='date'], input[type='text']")
        if inputs.count() >= 2:
            input_desde = inputs.nth(0)
            input_hasta = inputs.nth(1)

    if input_desde is None or input_hasta is None:
        logger.error(
            "No se encontraron los campos de fecha automaticamente. "
            "Revisa data/debug/formulario.png y ajusta los selectores."
        )
        if debug:
            _guardar_debug(page, "formulario_no_encontrado")
        return False

    input_desde.fill(desde.strftime("%d/%m/%Y"))
    input_hasta.fill(hasta.strftime("%d/%m/%Y"))

    for texto_boton in CANDIDATOS_BOTON_BUSCAR:
        boton = page.get_by_role("button", name=texto_boton, exact=False)
        if boton.count() == 0:
            boton = page.get_by_text(texto_boton, exact=False)
        if boton.count() > 0:
            try:
                boton.first.click()
                page.wait_for_load_state("networkidle", timeout=15000)
                return True
            except PWTimeout:
                continue

    logger.error("No se encontro el boton de busqueda. Revisa data/debug/.")
    if debug:
        _guardar_debug(page, "boton_no_encontrado")
    return False


def scrapear_rango(desde: date, hasta: date, debug: bool = False) -> list[dict]:
    """Scrapea precios para un rango de fechas usando un navegador real.
    Devuelve una lista de dicts (mismo formato que parsear_tabla_precios)."""
    from playwright.sync_api import sync_playwright

    resultados = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(settings.mag_base_url + PATH_PRECIOS, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)

            if debug:
                _guardar_debug(page, "pagina_inicial")

            ok = _completar_formulario_fecha(page, desde, hasta, debug)
            if not ok:
                # Igual intentamos parsear lo que haya (puede ser el
                # periodo por defecto)
                logger.warning("Uso el periodo por defecto de la pagina (sin filtrar fechas).")

            html = page.content()
            if debug:
                _guardar_debug(page, "resultado")

            fecha_periodo = extraer_fecha_periodo(html) or hasta
            filas = parsear_tabla_precios(html)
            for f in filas:
                f["fecha"] = fecha_periodo
            resultados.extend(filas)
        finally:
            browser.close()

    return resultados


def scrapear_dia(dia: date, debug: bool = False) -> list[dict]:
    return scrapear_rango(dia, dia, debug=debug)


def backfill_historico(desde: date, hasta: date, debug: bool = False) -> list[dict]:
    """
    Recorre el rango semana a semana (para no pedirle al sitio un rango
    gigante de una sola vez, lo cual muchas paginas legacy no soportan
    bien) y devuelve todos los registros encontrados.
    """
    todos = []
    cursor = desde
    while cursor <= hasta:
        fin_semana = min(cursor + timedelta(days=6), hasta)
        logger.info("Scrapeando semana %s a %s", cursor, fin_semana)
        try:
            filas = scrapear_rango(cursor, fin_semana, debug=debug)
            todos.extend(filas)
        except Exception as exc:  # noqa: BLE001
            logger.error("Fallo la semana %s-%s: %s", cursor, fin_semana, exc)
        cursor = fin_semana + timedelta(days=1)
    return todos


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper robusto (Playwright) de precios del MAG")
    parser.add_argument("--desde", type=str, default=None)
    parser.add_argument("--hasta", type=str, default=None)
    parser.add_argument("--debug-save", action="store_true", dest="debug")
    args = parser.parse_args()

    if args.desde and args.hasta:
        d = datetime.strptime(args.desde, "%Y-%m-%d").date()
        h = datetime.strptime(args.hasta, "%Y-%m-%d").date()
        filas = backfill_historico(d, h, debug=args.debug)
    else:
        filas = scrapear_dia(date.today(), debug=args.debug)

    print(f"Filas obtenidas: {len(filas)}")
    for f in filas[:20]:
        print(f)
