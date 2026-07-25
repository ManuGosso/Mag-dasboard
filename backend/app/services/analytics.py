"""
Logica de analisis de mercado: variaciones porcentuales, promedios moviles,
maximos/minimos historicos y el semaforo de "situacion actual".

Se mantiene separada de los routers para poder testearla de forma aislada
y para que el codigo del scraper / notebooks pueda reutilizarla.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, Sequence

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import PriceRecord

settings = get_settings()


@dataclass
class SerieRecord:
    fecha: date
    precio_promedio: float


def _get_ultima_fecha(db: Session, categoria: str) -> Optional[date]:
    return (
        db.query(func.max(PriceRecord.fecha))
        .filter(PriceRecord.categoria == categoria)
        .scalar()
    )


def _get_precio_en_o_antes(db: Session, categoria: str, fecha_limite: date) -> Optional[float]:
    """Devuelve el precio_promedio del registro mas cercano (hacia atras) a fecha_limite."""
    registro = (
        db.query(PriceRecord)
        .filter(PriceRecord.categoria == categoria, PriceRecord.fecha <= fecha_limite)
        .order_by(PriceRecord.fecha.desc())
        .first()
    )
    return registro.precio_promedio if registro else None


def calcular_variacion_pct(actual: Optional[float], referencia: Optional[float]) -> Optional[float]:
    if actual is None or referencia is None or referencia == 0:
        return None
    return round((actual - referencia) / referencia * 100, 2)


def calcular_kpi_categoria(db: Session, categoria: str) -> Optional[dict]:
    """Calcula precio actual + variaciones semanal/mensual/anual para una categoria."""
    ultima_fecha = _get_ultima_fecha(db, categoria)
    if ultima_fecha is None:
        return None

    ultimo = (
        db.query(PriceRecord)
        .filter(PriceRecord.categoria == categoria, PriceRecord.fecha == ultima_fecha)
        .first()
    )
    precio_actual = ultimo.precio_promedio

    precio_hace_7d = _get_precio_en_o_antes(db, categoria, ultima_fecha - timedelta(days=7))
    precio_hace_30d = _get_precio_en_o_antes(db, categoria, ultima_fecha - timedelta(days=30))
    precio_hace_365d = _get_precio_en_o_antes(db, categoria, ultima_fecha - timedelta(days=365))

    return {
        "categoria": categoria,
        "precio_actual": precio_actual,
        "fecha_actual": ultima_fecha,
        "variacion_semanal_pct": calcular_variacion_pct(precio_actual, precio_hace_7d),
        "variacion_mensual_pct": calcular_variacion_pct(precio_actual, precio_hace_30d),
        "variacion_anual_pct": calcular_variacion_pct(precio_actual, precio_hace_365d),
    }


def calcular_situacion_categoria(db: Session, categoria: str) -> Optional[dict]:
    """Compara el precio actual contra promedios 12/24 meses y maximo/minimo historico."""
    ultima_fecha = _get_ultima_fecha(db, categoria)
    if ultima_fecha is None:
        return None

    ultimo = (
        db.query(PriceRecord)
        .filter(PriceRecord.categoria == categoria, PriceRecord.fecha == ultima_fecha)
        .first()
    )
    precio_actual = ultimo.precio_promedio

    desde_12m = ultima_fecha - timedelta(days=365)
    desde_24m = ultima_fecha - timedelta(days=730)

    promedio_12m = (
        db.query(func.avg(PriceRecord.precio_promedio))
        .filter(PriceRecord.categoria == categoria, PriceRecord.fecha >= desde_12m)
        .scalar()
    )
    promedio_24m = (
        db.query(func.avg(PriceRecord.precio_promedio))
        .filter(PriceRecord.categoria == categoria, PriceRecord.fecha >= desde_24m)
        .scalar()
    )
    maximo_historico = (
        db.query(func.max(PriceRecord.precio_promedio))
        .filter(PriceRecord.categoria == categoria)
        .scalar()
    )
    minimo_historico = (
        db.query(func.min(PriceRecord.precio_promedio))
        .filter(PriceRecord.categoria == categoria)
        .scalar()
    )

    promedio_12m = round(promedio_12m, 2) if promedio_12m is not None else None
    promedio_24m = round(promedio_24m, 2) if promedio_24m is not None else None

    variacion_vs_12m = calcular_variacion_pct(precio_actual, promedio_12m)
    semaforo = clasificar_semaforo(variacion_vs_12m)

    return {
        "categoria": categoria,
        "precio_actual": precio_actual,
        "promedio_12m": promedio_12m,
        "promedio_24m": promedio_24m,
        "maximo_historico": maximo_historico,
        "minimo_historico": minimo_historico,
        "variacion_vs_promedio_12m_pct": variacion_vs_12m,
        "semaforo": semaforo,
    }


def clasificar_semaforo(variacion_vs_12m_pct: Optional[float]) -> str:
    """
    VERDE: precio bajo respecto al historico (barato para comprar)
    AMARILLO: precio normal
    ROJO: precio elevado respecto al historico
    """
    if variacion_vs_12m_pct is None:
        return "amarillo"
    if variacion_vs_12m_pct <= settings.semaforo_umbral_bajo:
        return "verde"
    if variacion_vs_12m_pct >= settings.semaforo_umbral_alto:
        return "rojo"
    return "amarillo"
