"""
Generador de datos de MUESTRA (illustrativos, no reales) para poder usar
el tablero de punta a punta sin depender todavia del scraper.

Los precios "actuales" (el ultimo punto de cada serie) estan calibrados
para parecerse a valores reales publicados en prensa especializada sobre
el Mercado Agroganadero de Cañuelas en julio de 2026. Los 5 años hacia
atras se generan con una caminata aleatoria + estacionalidad + una curva
de crecimiento que aproxima (muy grosso modo) la inflacion en pesos
argentinos de este periodo. NO deben tomarse como precios historicos
reales: son un placeholder para que el tablero funcione y se vea bien
mientras se conecta una fuente real (scraper o importacion manual).

Uso:
    python -m app.seed.generate_sample_data
    python -m app.seed.generate_sample_data --years 5 --frecuencia semanal
"""
import argparse
import math
import random
from datetime import date, timedelta

from app.database import SessionLocal, Base, engine
from app.models import PriceRecord

random.seed(42)

# Precio actual "ancla" ($/kg vivo) aproximado a partir de precios
# publicados en prensa especializada para el MAG en julio de 2026, y peso
# promedio tipico de faena/venta para cada categoria.
CATEGORIAS_CONFIG = {
    "Terneros": {"anchor_price": 5800, "anchor_weight": 180, "cabezas_base": 1400},
    "Novillitos 300-390 kg": {"anchor_price": 5350, "anchor_weight": 350, "cabezas_base": 1100},
    "Novillitos 391-430 kg": {"anchor_price": 5000, "anchor_weight": 410, "cabezas_base": 900},
    "Novillos +430 kg": {"anchor_price": 4750, "anchor_weight": 460, "cabezas_base": 1600},
    "Vaquillonas": {"anchor_price": 5000, "anchor_weight": 330, "cabezas_base": 1900},
    "Vacas": {"anchor_price": 4150, "anchor_weight": 460, "cabezas_base": 2100},
}

# Factor de crecimiento acumulado aproximado, año calendario a año
# calendario (de mas viejo a mas nuevo). Es una aproximacion gruesa de la
# inflacion en pesos + ciclo ganadero, solo para que la serie "se sienta"
# realista.
CRECIMIENTO_ANUAL = [1.60, 2.00, 1.90, 1.40, 1.22]


def _fecha_lunes_on_or_before(d: date) -> date:
    return d - timedelta(days=d.weekday())


def generar_serie_semanal(categoria: str, cfg: dict, anios: int) -> list[dict]:
    hoy = date.today()
    ultimo_lunes = _fecha_lunes_on_or_before(hoy)
    primer_lunes = ultimo_lunes - timedelta(weeks=52 * anios)

    fechas = []
    f = primer_lunes
    while f <= ultimo_lunes:
        fechas.append(f)
        f += timedelta(weeks=1)

    n = len(fechas)
    factor_total = 1.0
    for f in CRECIMIENTO_ANUAL[:anios]:
        factor_total *= f

    precio_inicial = cfg["anchor_price"] / factor_total

    # 1) Tendencia determinista: se compone SOLO a partir del precio
    #    inicial + la estacionalidad, nunca sobre un valor ya "ruidoso".
    #    Esto evita que el ruido semanal se retroalimente semana a semana
    #    y termine generando una deriva descontrolada (un bug real que
    #    aparecia en una version anterior de este generador: el precio
    #    podia terminar multiplicado por 100x en la mitad de la serie).
    tendencia = []
    for i, f in enumerate(fechas):
        progreso = i / max(n - 1, 1)
        anio_idx = min(int(progreso * anios), anios - 1)
        crecimiento_interanual = CRECIMIENTO_ANUAL[anio_idx]
        drift_semanal = crecimiento_interanual ** (1 / 52) - 1

        base_previa = precio_inicial if i == 0 else tendencia[-1]
        valor_tendencial = base_previa * (1 + drift_semanal)

        semana_del_anio = f.timetuple().tm_yday // 7
        estacional = 1 + 0.05 * math.sin(2 * math.pi * semana_del_anio / 52 + 1.2)

        tendencia.append(valor_tendencial * estacional)

    # 2) Ruido: proceso de reversion a la media (Ornstein-Uhlenbeck simple
    #    en log-espacio) MULTIPLICADO sobre la tendencia, no acumulado
    #    sobre si mismo. Queda acotado en el tiempo (no se "escapa").
    phi = 0.85  # velocidad de reversion (mas cerca de 1 = mas persistente)
    sigma_innovacion = 0.02
    precios = []
    ou = 0.0
    for valor_tendencial in tendencia:
        ou = phi * ou + random.gauss(0, sigma_innovacion)
        ou = max(min(ou, 0.25), -0.25)  # cinturon de seguridad adicional
        precios.append(valor_tendencial * math.exp(ou))

    # Recalibrar para que el ultimo punto coincida con el precio ancla real
    factor_ajuste = cfg["anchor_price"] / precios[-1]
    precios = [p * factor_ajuste for p in precios]

    registros = []
    for f, precio in zip(fechas, precios):
        precio = round(precio, 1)
        peso = round(cfg["anchor_weight"] * (1 + random.gauss(0, 0.03)), 1)
        precio_max = round(precio * (1 + random.uniform(0.02, 0.06)), 1)
        precio_min = round(precio * (1 - random.uniform(0.02, 0.06)), 1)

        semana_del_anio = f.timetuple().tm_yday // 7
        estacionalidad_oferta = 1 + 0.25 * math.sin(2 * math.pi * semana_del_anio / 52 + 0.3)
        cabezas = max(50, int(cfg["cabezas_base"] * estacionalidad_oferta * random.uniform(0.8, 1.2)))
        kg_comercializados = round(cabezas * peso, 1)

        registros.append(
            {
                "fecha": f,
                "categoria": categoria,
                "peso_promedio": peso,
                "precio_promedio": precio,
                "precio_maximo": precio_max,
                "precio_minimo": precio_min,
                "cabezas": cabezas,
                "kg_comercializados": kg_comercializados,
                "fuente": "seed",
            }
        )
    return registros


def poblar_base(anios: int = 5) -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    total_insertados = 0
    try:
        for categoria, cfg in CATEGORIAS_CONFIG.items():
            registros = generar_serie_semanal(categoria, cfg, anios)
            for data in registros:
                existente = (
                    db.query(PriceRecord)
                    .filter(
                        PriceRecord.fecha == data["fecha"],
                        PriceRecord.categoria == data["categoria"],
                    )
                    .first()
                )
                if existente:
                    continue  # no pisar datos reales ya cargados
                db.add(PriceRecord(**data))
                total_insertados += 1
            db.commit()
    finally:
        db.close()
    return total_insertados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera datos de muestra para el tablero MAG")
    parser.add_argument("--years", type=int, default=5, dest="anios")
    args = parser.parse_args()

    n = poblar_base(anios=args.anios)
    print(f"Listo. Se insertaron {n} registros de muestra (fuente='seed').")
    print("IMPORTANTE: son datos ilustrativos, no precios historicos reales.")
    print("Corre el scraper o el importador manual para reemplazarlos por datos reales.")
