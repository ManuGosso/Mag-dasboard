from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CATEGORIAS
from app.services import analytics

router = APIRouter(prefix="/api/situacion-actual", tags=["situacion-actual"])


@router.get("")
def situacion_actual(db: Session = Depends(get_db)):
    """
    Seccion "Situacion actual": para cada categoria compara el precio de
    hoy contra el promedio de los ultimos 12 y 24 meses, y contra el
    maximo/minimo historico, devolviendo tambien el semaforo.
    """
    resultados = []
    for categoria in CATEGORIAS:
        situacion = analytics.calcular_situacion_categoria(db, categoria)
        if situacion is not None:
            resultados.append(situacion)
    return resultados


@router.get("/{categoria}")
def situacion_categoria(categoria: str, db: Session = Depends(get_db)):
    situacion = analytics.calcular_situacion_categoria(db, categoria)
    return situacion
