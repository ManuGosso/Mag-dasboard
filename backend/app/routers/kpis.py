from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.services import analytics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
settings = get_settings()


@router.get("")
def dashboard(db: Session = Depends(get_db)):
    """
    Resumen para la pantalla principal: precio y variaciones del ternero
    de compra y el novillo de venta, mas la relacion compra/venta.
    """
    ternero = analytics.calcular_kpi_categoria(db, settings.kpi_categoria_ternero)
    novillo = analytics.calcular_kpi_categoria(db, settings.kpi_categoria_novillo)

    if ternero is None or novillo is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No hay datos suficientes todavia. Corre el seed o el "
                "importador para cargar precios."
            ),
        )

    relacion = None
    if ternero["precio_actual"] and novillo["precio_actual"]:
        relacion = round(ternero["precio_actual"] / novillo["precio_actual"], 3)

    fecha_actualizacion = max(ternero["fecha_actual"], novillo["fecha_actual"])

    return {
        "ternero": ternero,
        "novillo": novillo,
        "relacion_compra_venta": relacion,
        "actualizado_en": fecha_actualizacion,
    }


@router.get("/kpi/{categoria}")
def kpi_categoria(categoria: str, db: Session = Depends(get_db)):
    """KPI (precio actual + variaciones) para cualquier categoria soportada."""
    resultado = analytics.calcular_kpi_categoria(db, categoria)
    if resultado is None:
        raise HTTPException(status_code=404, detail=f"Sin datos para la categoria '{categoria}'")
    return resultado
