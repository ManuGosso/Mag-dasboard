from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas import PriceRecordOut

router = APIRouter(prefix="/api/precios", tags=["precios"])


@router.get("/historico", response_model=list[PriceRecordOut])
def historico(
    categoria: Optional[str] = Query(None, description="Filtrar por categoria exacta"),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    anio: Optional[int] = Query(None, description="Atajo: filtra todo el año calendario"),
    peso_min: Optional[float] = Query(None),
    peso_max: Optional[float] = Query(None),
    limit: int = Query(5000, le=20000),
    db: Session = Depends(get_db),
):
    """Serie historica de precios, con filtros opcionales por fecha/año/categoria/peso."""
    if anio is not None:
        fecha_desde = date(anio, 1, 1)
        fecha_hasta = date(anio, 12, 31)

    registros = crud.get_price_records(
        db,
        categoria=categoria,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        peso_min=peso_min,
        peso_max=peso_max,
        limit=limit,
    )
    return registros


@router.get("/ultimo", response_model=Optional[PriceRecordOut])
def ultimo_precio(categoria: str, db: Session = Depends(get_db)):
    """Ultimo precio registrado para una categoria."""
    return crud.get_ultimo_precio(db, categoria=categoria)
