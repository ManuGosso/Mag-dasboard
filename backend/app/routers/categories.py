from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CATEGORIAS
from app import crud

router = APIRouter(prefix="/api/categorias", tags=["categorias"])


@router.get("")
def listar_categorias(db: Session = Depends(get_db)):
    """
    Devuelve las categorias oficiales soportadas por el tablero y, aparte,
    las que efectivamente tienen datos cargados (por si hay alguna extra
    importada manualmente).
    """
    return {
        "categorias_oficiales": CATEGORIAS,
        "categorias_con_datos": crud.get_categorias_disponibles(db),
    }
