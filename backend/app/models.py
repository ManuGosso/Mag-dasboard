"""
Modelo de datos principal: registros historicos de precios de hacienda.

Cada fila representa el precio de UNA categoria en UNA fecha (rueda de
comercializacion) del Mercado Agroganadero de Cañuelas (MAG).
El historico nunca se borra: las cargas nuevas hacen upsert por
(fecha, categoria, peso_promedio) y las corridas viejas quedan intactas.
"""
from datetime import datetime, date

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Date,
    DateTime,
    UniqueConstraint,
    Index,
)

from app.database import Base

# Categorias oficiales que soporta el tablero. Se mantienen como lista
# centralizada para validar filtros y para el seed de datos.
CATEGORIAS = [
    "Terneros",
    "Novillitos 300-390 kg",
    "Novillitos 391-430 kg",
    "Novillos +430 kg",
    "Vaquillonas",
    "Vacas",
]


class PriceRecord(Base):
    """Registro historico de precios por fecha y categoria."""

    __tablename__ = "price_records"

    id = Column(Integer, primary_key=True, index=True)

    fecha = Column(Date, nullable=False, index=True)
    categoria = Column(String(64), nullable=False, index=True)

    peso_promedio = Column(Float, nullable=True)  # kg
    precio_promedio = Column(Float, nullable=False)  # $/kg vivo
    precio_maximo = Column(Float, nullable=True)  # $/kg vivo
    precio_minimo = Column(Float, nullable=True)  # $/kg vivo

    cabezas = Column(Integer, nullable=True)  # cantidad de animales
    kg_comercializados = Column(Float, nullable=True)  # kg totales

    fuente = Column(String(32), nullable=False, default="seed")  # seed | scraper | manual
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("fecha", "categoria", name="uq_fecha_categoria"),
        Index("ix_categoria_fecha", "categoria", "fecha"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PriceRecord {self.fecha} {self.categoria} ${self.precio_promedio}>"
