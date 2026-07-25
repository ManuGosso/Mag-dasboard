"""Operaciones de acceso a datos (CRUD) sobre PriceRecord."""
from datetime import date
from typing import Optional, Sequence

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import PriceRecord


def upsert_price_record(db: Session, data: dict) -> tuple[PriceRecord, bool]:
    """
    Inserta o actualiza un registro identificado por (fecha, categoria).
    Nunca borra historico: si ya existe, actualiza sus valores; si no
    existe, lo crea. Devuelve (registro, fue_creado).
    """
    existente = (
        db.query(PriceRecord)
        .filter(
            PriceRecord.fecha == data["fecha"],
            PriceRecord.categoria == data["categoria"],
        )
        .first()
    )
    if existente:
        for key, value in data.items():
            setattr(existente, key, value)
        db.commit()
        db.refresh(existente)
        return existente, False

    registro = PriceRecord(**data)
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro, True


def get_price_records(
    db: Session,
    categoria: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    peso_min: Optional[float] = None,
    peso_max: Optional[float] = None,
    limit: int = 5000,
) -> Sequence[PriceRecord]:
    query = db.query(PriceRecord)
    filtros = []
    if categoria:
        filtros.append(PriceRecord.categoria == categoria)
    if fecha_desde:
        filtros.append(PriceRecord.fecha >= fecha_desde)
    if fecha_hasta:
        filtros.append(PriceRecord.fecha <= fecha_hasta)
    if peso_min is not None:
        filtros.append(PriceRecord.peso_promedio >= peso_min)
    if peso_max is not None:
        filtros.append(PriceRecord.peso_promedio <= peso_max)
    if filtros:
        query = query.filter(and_(*filtros))
    return query.order_by(PriceRecord.fecha.asc()).limit(limit).all()


def get_ultimo_precio(db: Session, categoria: str) -> Optional[PriceRecord]:
    return (
        db.query(PriceRecord)
        .filter(PriceRecord.categoria == categoria)
        .order_by(PriceRecord.fecha.desc())
        .first()
    )


def get_categorias_disponibles(db: Session) -> list[str]:
    filas = db.query(PriceRecord.categoria).distinct().all()
    return sorted({f[0] for f in filas})
