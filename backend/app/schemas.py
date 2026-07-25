"""Schemas Pydantic usados por la API (request/response)."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PriceRecordBase(BaseModel):
    fecha: date
    categoria: str
    peso_promedio: Optional[float] = None
    precio_promedio: float
    precio_maximo: Optional[float] = None
    precio_minimo: Optional[float] = None
    cabezas: Optional[int] = None
    kg_comercializados: Optional[float] = None


class PriceRecordCreate(PriceRecordBase):
    fuente: Optional[str] = "manual"


class PriceRecordOut(PriceRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fuente: str


class KPI(BaseModel):
    categoria: str
    precio_actual: float
    fecha_actual: date
    variacion_semanal_pct: Optional[float]
    variacion_mensual_pct: Optional[float]
    variacion_anual_pct: Optional[float]


class DashboardResponse(BaseModel):
    ternero: KPI
    novillo: KPI
    relacion_compra_venta: Optional[float]
    actualizado_en: date


class SituacionCategoria(BaseModel):
    categoria: str
    precio_actual: float
    promedio_12m: Optional[float]
    promedio_24m: Optional[float]
    maximo_historico: Optional[float]
    minimo_historico: Optional[float]
    variacion_vs_promedio_12m_pct: Optional[float]
    semaforo: str  # "verde" | "amarillo" | "rojo"


class ImportSummary(BaseModel):
    filas_recibidas: int
    filas_insertadas: int
    filas_actualizadas: int
    filas_con_error: int
    errores: list[str] = []
