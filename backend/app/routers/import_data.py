"""
Endpoint para importar datos manualmente (CSV o Excel) cuando el scraper
automatico no pueda correr (por ejemplo, si el sitio del MAG cambia de
estructura). Es el mismo mecanismo que usa el scraper por dentro.
"""
import io

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CATEGORIAS
from app.schemas import ImportSummary
from app import crud

router = APIRouter(prefix="/api/import", tags=["import"])

COLUMNAS_REQUERIDAS = {"fecha", "categoria", "precio_promedio"}
COLUMNAS_OPCIONALES = {
    "peso_promedio",
    "precio_maximo",
    "precio_minimo",
    "cabezas",
    "kg_comercializados",
}


def _leer_archivo(nombre: str, contenido: bytes) -> pd.DataFrame:
    if nombre.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(contenido))
    if nombre.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(contenido))
    raise HTTPException(status_code=400, detail="Formato no soportado. Usa .csv o .xlsx")


@router.post("/archivo", response_model=ImportSummary)
async def importar_archivo(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Importa un CSV/Excel con columnas: fecha, categoria, precio_promedio,
    y opcionalmente peso_promedio, precio_maximo, precio_minimo, cabezas,
    kg_comercializados. Hace upsert por (fecha, categoria): no borra
    historico existente.
    """
    contenido = await archivo.read()
    df = _leer_archivo(archivo.filename, contenido)

    columnas = {c.strip().lower() for c in df.columns}
    faltantes = COLUMNAS_REQUERIDAS - columnas
    if faltantes:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan columnas obligatorias: {sorted(faltantes)}",
        )

    df.columns = [c.strip().lower() for c in df.columns]

    insertadas = 0
    actualizadas = 0
    errores = []

    for idx, fila in df.iterrows():
        try:
            categoria = str(fila["categoria"]).strip()
            fecha = pd.to_datetime(fila["fecha"]).date()
            data = {
                "fecha": fecha,
                "categoria": categoria,
                "precio_promedio": float(fila["precio_promedio"]),
                "peso_promedio": _opt_float(fila, "peso_promedio"),
                "precio_maximo": _opt_float(fila, "precio_maximo"),
                "precio_minimo": _opt_float(fila, "precio_minimo"),
                "cabezas": _opt_int(fila, "cabezas"),
                "kg_comercializados": _opt_float(fila, "kg_comercializados"),
                "fuente": "manual",
            }
            _, creado = crud.upsert_price_record(db, data)
            if creado:
                insertadas += 1
            else:
                actualizadas += 1
        except Exception as exc:  # noqa: BLE001
            errores.append(f"Fila {idx + 2}: {exc}")

    return ImportSummary(
        filas_recibidas=len(df),
        filas_insertadas=insertadas,
        filas_actualizadas=actualizadas,
        filas_con_error=len(errores),
        errores=errores[:20],
    )


def _opt_float(fila, columna):
    if columna not in fila or pd.isna(fila[columna]):
        return None
    return float(fila[columna])


def _opt_int(fila, columna):
    if columna not in fila or pd.isna(fila[columna]):
        return None
    return int(fila[columna])


@router.get("/plantilla")
def descargar_plantilla():
    """Devuelve las columnas esperadas para armar un CSV/Excel manual."""
    return {
        "columnas_obligatorias": sorted(COLUMNAS_REQUERIDAS),
        "columnas_opcionales": sorted(COLUMNAS_OPCIONALES),
        "categorias_validas": CATEGORIAS,
        "ejemplo": {
            "fecha": "2026-07-15",
            "categoria": "Terneros",
            "precio_promedio": 2850.5,
            "peso_promedio": 180,
            "precio_maximo": 2950,
            "precio_minimo": 2700,
            "cabezas": 1200,
            "kg_comercializados": 216000,
        },
    }
