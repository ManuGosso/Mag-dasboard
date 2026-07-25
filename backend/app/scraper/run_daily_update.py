"""
Script pensado para ejecutarse una vez por dia (via cron, Task Scheduler
o GitHub Actions) y actualizar la base con los precios del dia.

Estrategia:
  1) Intenta el scraper liviano (requests). Es rapido y no necesita
     navegador instalado.
  2) Si falla (excepcion, 0 filas, o todas las categorias sin mapear),
     intenta el scraper robusto (Playwright).
  3) Si ambos fallan, no toca la base de datos (el historico existente
     nunca se borra) y termina con codigo de salida distinto de 0 para
     que el cron / la Action puedan avisar del fallo.

Uso:
    python -m app.scraper.run_daily_update
"""
from __future__ import annotations

import logging
import sys
from datetime import date

from app.database import SessionLocal, Base, engine
from app import crud
from app.scraper.requests_scraper import scrapear_precios_actuales

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_daily_update")


def _guardar_filas(fecha, filas: list[dict]) -> tuple[int, int, int]:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    insertadas = actualizadas = ignoradas = 0
    try:
        for fila in filas:
            if fila.get("categoria") is None:
                ignoradas += 1
                continue
            data = {
                "fecha": fecha,
                "categoria": fila["categoria"],
                "precio_promedio": fila["precio_promedio"],
                "peso_promedio": fila.get("peso_promedio"),
                "precio_maximo": fila.get("precio_maximo"),
                "precio_minimo": fila.get("precio_minimo"),
                "cabezas": fila.get("cabezas"),
                "kg_comercializados": fila.get("kg_comercializados"),
                "fuente": "scraper",
            }
            _, creado = crud.upsert_price_record(db, data)
            if creado:
                insertadas += 1
            else:
                actualizadas += 1
    finally:
        db.close()
    return insertadas, actualizadas, ignoradas


def main() -> int:
    fecha_periodo, filas = None, []

    try:
        fecha_periodo, filas = scrapear_precios_actuales()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Scraper liviano fallo (%s). Probando con Playwright...", exc)

    if not filas:
        try:
            from app.scraper.playwright_scraper import scrapear_dia

            hoy = date.today()
            filas = scrapear_dia(hoy)
            fecha_periodo = fecha_periodo or hoy
        except Exception as exc:  # noqa: BLE001
            logger.error("Scraper robusto (Playwright) tambien fallo: %s", exc)

    if not filas:
        logger.error(
            "No se pudo obtener ningun dato hoy. La base NO se modifico. "
            "Considera cargar el dia manualmente via /api/import/archivo."
        )
        return 1

    fecha_final = fecha_periodo or date.today()
    insertadas, actualizadas, ignoradas = _guardar_filas(fecha_final, filas)

    logger.info(
        "Actualizacion %s completa: %d insertadas, %d actualizadas, %d ignoradas (categoria sin mapear)",
        fecha_final,
        insertadas,
        actualizadas,
        ignoradas,
    )
    if ignoradas:
        logger.warning(
            "Hay %d fila(s) con categorias que no se pudieron mapear. "
            "Revisa los logs de WARNING mas arriba y completa MAPA_CATEGORIAS "
            "en app/scraper/parser.py",
            ignoradas,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
