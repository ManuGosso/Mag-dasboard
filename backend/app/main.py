"""
Punto de entrada de la API del Tablero de Mercado Ganadero (MAG Cañuelas).

Correr en desarrollo:
    uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.routers import prices, kpis, market_analysis, categories, import_data
from app.models import PriceRecord

settings = get_settings()

# Crea las tablas si no existen (para Postgres en produccion se recomienda
# usar una migracion real, pero esto alcanza para arrancar rapido).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MAG Cañuelas - Tablero de Mercado Ganadero",
    description=(
        "API de analisis de precios historicos y actuales del Mercado "
        "Agroganadero de Cañuelas (ex Mercado de Liniers). Uso "
        "exclusivamente informativo/analitico, sin datos de empresas "
        "privadas."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prices.router)
app.include_router(kpis.router)
app.include_router(market_analysis.router)
app.include_router(categories.router)
app.include_router(import_data.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/api/health")
def health():
    with SessionLocal() as db:
        registros = db.query(PriceRecord).count()
    return {"status": "ok", "registros": registros, "version": app.version}
