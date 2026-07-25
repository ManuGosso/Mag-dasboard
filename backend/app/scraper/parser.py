"""
Parser generico de las tablas de precios del MAG.

IMPORTANTE (leer antes de tocar el scraper):
Este entorno de desarrollo tiene la salida de red restringida a una lista
blanca de dominios y NO pudo acceder en vivo a mercadoagroganadero.com.ar
para inspeccionar el HTML real de la tabla (las herramientas de busqueda
web si devolvieron una descripcion de la pagina, pero no el HTML crudo).
Por eso el parser esta escrito para ser TOLERANTE a variaciones de
estructura (busca por texto de encabezado en vez de por posicion fija de
columna), pero de todas formas conviene:

  1) Correr `python -m app.scraper.requests_scraper --debug-save` una vez
     desde una maquina con acceso normal a internet.
  2) Revisar el archivo HTML guardado en backend/data/debug/ para
     confirmar que los nombres de columnas coinciden con
     ENCABEZADOS_ESPERADOS de abajo.
  3) Si el sitio cambio de estructura, ajustar ENCABEZADOS_ESPERADOS y/o
     MAPA_CATEGORIAS.

La estructura conocida (segun la version publica de la pagina al momento
de escribir esto) es una tabla "Precios por categoria" con columnas:
Categoria | Minimo | Maximo | Promedio | Mediana | Cabezas | Importe | Kgs
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from typing import Optional

from bs4 import BeautifulSoup

ENCABEZADOS_ESPERADOS = {
    "categoria": ["categoria"],
    "precio_minimo": ["minimo", "min"],
    "precio_maximo": ["maximo", "max"],
    "precio_promedio": ["promedio", "prom"],
    "mediana": ["mediana"],
    "cabezas": ["cabezas", "cab"],
    "importe": ["importe", "monto"],
    "kg_comercializados": ["kgs", "kg", "kilos"],
}

# Variantes de nombres de categoria que puede publicar el MAG -> categoria
# canonica que usa el tablero (ver app/models.py::CATEGORIAS).
# Completar/ajustar esta tabla despues de ver datos reales (ver docstring).
MAPA_CATEGORIAS = {
    "ternero": "Terneros",
    "terneros": "Terneros",
    "ternera": "Terneros",
    "terneras": "Terneros",
    "novillito 300/390": "Novillitos 300-390 kg",
    "novillito 300-390": "Novillitos 300-390 kg",
    "novillitos 300/390": "Novillitos 300-390 kg",
    "novillito liviano": "Novillitos 300-390 kg",
    "novillito 391/430": "Novillitos 391-430 kg",
    "novillito 391-430": "Novillitos 391-430 kg",
    "novillitos 391/430": "Novillitos 391-430 kg",
    "novillito pesado": "Novillitos 391-430 kg",
    "novillo": "Novillos +430 kg",
    "novillos": "Novillos +430 kg",
    "novillo +430": "Novillos +430 kg",
    "novillo pesado": "Novillos +430 kg",
    "vaquillona": "Vaquillonas",
    "vaquillonas": "Vaquillonas",
    "vaca": "Vacas",
    "vacas": "Vacas",
}


def _normalizar(texto: str) -> str:
    texto = texto.strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", texto)


def mapear_categoria(nombre_crudo: str) -> Optional[str]:
    """Traduce el nombre de categoria tal cual viene del sitio a la categoria
    canonica del tablero.

    Primero intenta un match exacto/por substring contra MAPA_CATEGORIAS
    (rapido y explicito para los casos ya conocidos). Si no encuentra nada,
    cae a una heuristica por palabra clave + rango de peso (mas robusta
    ante variantes de texto no anticipadas, ej. "Novillito pesado 391/430
    kg" o "Novillitos entre 391 y 430 kgs").

    Devuelve None si no se pudo mapear (se loguea aparte para que el
    usuario la agregue a MAPA_CATEGORIAS).
    """
    clave = _normalizar(nombre_crudo)

    if clave in MAPA_CATEGORIAS:
        return MAPA_CATEGORIAS[clave]
    for variante, canonica in MAPA_CATEGORIAS.items():
        if variante in clave or clave in variante:
            return canonica

    return _mapear_categoria_por_heuristica(clave)


def _mapear_categoria_por_heuristica(clave_normalizada: str) -> Optional[str]:
    """Heuristica de respaldo: busca una palabra clave de categoria y, si
    hace falta desambiguar por peso (novillitos), toma el primer numero de
    3 digitos que aparezca en el texto como referencia de peso en kg."""
    pesos = [int(n) for n in re.findall(r"\b(\d{3})\b", clave_normalizada)]
    peso_ref = pesos[0] if pesos else None

    if "ternero" in clave_normalizada or "ternera" in clave_normalizada:
        return "Terneros"
    if "vaquillona" in clave_normalizada:
        return "Vaquillonas"
    if "vaca" in clave_normalizada:
        return "Vacas"
    if "novillito" in clave_normalizada:
        if peso_ref is not None and peso_ref <= 390:
            return "Novillitos 300-390 kg"
        if peso_ref is not None and peso_ref <= 430:
            return "Novillitos 391-430 kg"
        return "Novillitos 300-390 kg" if peso_ref is None else "Novillitos 391-430 kg"
    if "novillo" in clave_normalizada:
        return "Novillos +430 kg"

    return None


def _parsear_numero(texto: str) -> Optional[float]:
    """Convierte numeros con formato argentino ("$ 4.750,50", "1.400",
    "5.800") a float.

    Convencion argentina: "," es separador decimal, "." es separador de
    miles. El caso ambiguo es un numero con UN SOLO punto y sin coma
    (ej. "1.400" o "5.8"): si tiene exactamente 3 digitos despues del
    punto se interpreta como separador de miles (1.400 -> 1400); si tiene
    1 o 2 digitos se interpreta como separador decimal (5.8 -> 5.8).
    """
    if texto is None:
        return None
    limpio = re.sub(r"[^\d,.\-]", "", texto)
    if not limpio:
        return None

    if "," in limpio and "." in limpio:
        limpio = limpio.replace(".", "").replace(",", ".")
    elif "," in limpio:
        limpio = limpio.replace(",", ".")
    elif "." in limpio:
        partes = limpio.split(".")
        if len(partes[-1]) == 3:
            limpio = "".join(partes)
        # si no, se asume que el punto ya es separador decimal (dejar como esta)

    try:
        return float(limpio)
    except ValueError:
        return None


def extraer_fecha_periodo(html: str) -> Optional[date]:
    """Busca un patron tipo 'DESDE EL ... AL 19/07/2026' y devuelve la
    fecha final del periodo (la mas representativa del dia de la rueda)."""
    match = re.search(r"AL\s+\w+\s+(\d{1,2}/\d{1,2}/\d{4})", html, re.IGNORECASE)
    if not match:
        match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", html)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%d/%m/%Y").date()
    except ValueError:
        return None


def parsear_tabla_precios(html: str) -> list[dict]:
    """
    Devuelve una lista de dicts con las columnas crudas encontradas
    (categoria_original, categoria, precio_minimo, precio_maximo,
    precio_promedio, cabezas, kg_comercializados) para cada fila de datos
    de la tabla de precios por categoria.

    Categorias que no se pudieron mapear a MAPA_CATEGORIAS se devuelven
    igual (con categoria=None) para que el llamador decida (loguear /
    descartar / guardar como categoria libre).
    """
    soup = BeautifulSoup(html, "lxml")
    resultados = []

    for tabla in soup.find_all("table"):
        filas = tabla.find_all("tr")
        if len(filas) < 2:
            continue

        encabezado_celdas = [c.get_text(" ", strip=True) for c in filas[0].find_all(["th", "td"])]
        encabezado_normalizado = [_normalizar(c) for c in encabezado_celdas]

        columnas_idx: dict[str, int] = {}
        for campo, alias in ENCABEZADOS_ESPERADOS.items():
            for i, celda in enumerate(encabezado_normalizado):
                if any(a in celda for a in alias):
                    columnas_idx[campo] = i
                    break

        if "categoria" not in columnas_idx or "precio_promedio" not in columnas_idx:
            continue  # esta tabla no es la de precios por categoria

        for fila in filas[1:]:
            celdas = [c.get_text(" ", strip=True) for c in fila.find_all(["td", "th"])]
            if len(celdas) <= columnas_idx["categoria"]:
                continue
            categoria_original = celdas[columnas_idx["categoria"]]
            if not categoria_original:
                continue

            def _get(campo):
                idx = columnas_idx.get(campo)
                if idx is None or idx >= len(celdas):
                    return None
                return celdas[idx]

            precio_promedio = _parsear_numero(_get("precio_promedio"))
            if precio_promedio is None:
                continue  # fila sin precio util (ej. subtotales)

            resultados.append(
                {
                    "categoria_original": categoria_original,
                    "categoria": mapear_categoria(categoria_original),
                    "precio_minimo": _parsear_numero(_get("precio_minimo")),
                    "precio_maximo": _parsear_numero(_get("precio_maximo")),
                    "precio_promedio": precio_promedio,
                    "cabezas": (
                        int(_parsear_numero(_get("cabezas")))
                        if _parsear_numero(_get("cabezas")) is not None
                        else None
                    ),
                    "kg_comercializados": _parsear_numero(_get("kg_comercializados")),
                }
            )

    return resultados
