# Tablero Ganadero — Mercado Agroganadero de Cañuelas (MAG)

Tablero profesional (estilo Bloomberg/TradingView) para analizar la evolución de
precios de hacienda del **Mercado Agroganadero de Cañuelas (MAG)**, ex Mercado
de Liniers. Es exclusivamente una herramienta de análisis de mercado: **no
incluye ni requiere datos de ninguna empresa privada**, solo precios de
referencia publicados por el mercado concentrador.

---

## 1. Qué incluye este proyecto

```
mag-dashboard/
├── backend/                  API en FastAPI (Python)
│   ├── app/
│   │   ├── main.py           punto de entrada de la API
│   │   ├── config.py         configuracion (.env)
│   │   ├── database.py       conexion SQLite/Postgres
│   │   ├── models.py         modelo PriceRecord + categorias oficiales
│   │   ├── schemas.py        schemas Pydantic
│   │   ├── crud.py           acceso a datos (upsert, filtros)
│   │   ├── routers/          endpoints (dashboard, historico, situacion, import, categorias)
│   │   ├── services/
│   │   │   └── analytics.py  variaciones %, promedios 12/24m, semaforo
│   │   ├── scraper/
│   │   │   ├── parser.py             parser HTML tolerante a cambios de estructura
│   │   │   ├── requests_scraper.py   scraper liviano (uso diario)
│   │   │   ├── playwright_scraper.py scraper robusto (navegador real, backfill historico)
│   │   │   └── run_daily_update.py   orquestador con fallback, pensado para cron
│   │   ├── seed/
│   │   │   └── generate_sample_data.py  datos de muestra (5 años, ilustrativos)
│   │   └── scheduler.py      alternativa a cron (proceso long-running)
│   ├── data/
│   │   └── mag_dashboard.db  base SQLite YA POBLADA con datos de muestra
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 Next.js 14 + TypeScript + Tailwind + Recharts
│   ├── app/
│   │   ├── page.tsx           Dashboard principal
│   │   ├── historico/         Histórico de precios (gráficos + filtros)
│   │   └── situacion/         Situación actual (semáforo)
│   ├── components/
│   ├── lib/
│   └── Dockerfile
├── .github/workflows/daily-update.yml   actualizacion diaria automatica (GitHub Actions)
├── docker-compose.yml
└── README.md                  (este archivo)
```

---

## 2. Arquitectura y por qué se eligió

| Capa | Tecnología | Motivo |
|---|---|---|
| Frontend | **Next.js 14 (App Router) + TypeScript + Tailwind + Recharts** | Server-side rendering para carga rápida, tipado fuerte, diseño responsive con Tailwind, gráficos interactivos livianos con Recharts. |
| Backend | **Python + FastAPI** | Excelente para scraping (BeautifulSoup/Playwright/pandas) y para servir una API tipada y documentada automáticamente (`/docs`). |
| Base de datos | **SQLite por defecto, Postgres opcional** | SQLite no requiere instalar nada para arrancar; basta con cambiar `DATABASE_URL` para pasar a Postgres en producción sin tocar código (SQLAlchemy abstrae ambos). |
| Actualización de datos | **Scraper propio + importación manual de respaldo** | El MAG no publica una API pública ni Excel histórico descargable (ver sección 5), así que se construyó un scraper adaptable más una vía manual de carga para cuando el scraper necesite ajustes. |

El historico **nunca se borra**: toda carga (scraper, importación manual o
seed) hace *upsert* por `(fecha, categoria)` — si el dato ya existe se
actualiza, si no existe se agrega. Nada se elimina automáticamente.

---

## 3. Instalación

### Requisitos
- Python 3.11+
- Node.js 18+
- (Opcional) Docker + Docker Compose, si preferís levantar todo con un comando

### Opción A — Manual (recomendada para desarrollo)

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # ajustar si hace falta

# La base ya viene con datos de muestra en data/mag_dashboard.db.
# Si querés regenerarla desde cero:
#   python -m app.seed.generate_sample_data

uvicorn app.main:app --reload --port 8000
```
La API queda en `http://localhost:8000` y la documentación interactiva
(Swagger) en `http://localhost:8000/docs`.

**Frontend** (en otra terminal):
```bash
cd frontend
npm install
cp .env.local.example .env.local   # ajustar NEXT_PUBLIC_API_URL si hace falta
npm run dev
```
El tablero queda en `http://localhost:3000`.

### Opción B — Docker Compose
```bash
docker compose up --build
```
Backend en `:8000`, frontend en `:3000`. Los datos de SQLite quedan
persistidos en `backend/data/` gracias al volumen configurado.

---

## 4. Base de datos inicial

El archivo `backend/data/mag_dashboard.db` **ya viene poblado** con ~1.560
registros: 5 años de historico semanal para las 6 categorías, calibrados
para que el precio más reciente se parezca a valores reales publicados en
prensa especializada sobre el MAG en julio de 2026.

**Importante:** el recorrido de los 5 años hacia atrás es una
**aproximación ilustrativa** (una caminata aleatoria con reversión a la
media + una curva de crecimiento que intenta imitar, muy a grandes
rasgos, la inflación en pesos argentinos de este período), no precios
históricos reales — el MAG no publica un Excel histórico público para
reconstruirlos automáticamente (ver sección 5). Sirve para que el tablero
funcione y se vea bien de entrada, mientras cargás datos reales con el
scraper o la importación manual.

Cada fila indica su origen en la columna `fuente`: `seed` (dato de
muestra), `scraper` (cargado automáticamente) o `manual` (importado a
mano). Podés auditar en cualquier momento qué es real y qué es ilustrativo
con una consulta SQL simple:
```sql
SELECT fuente, COUNT(*) FROM price_records GROUP BY fuente;
```

Para reemplazar los datos de muestra por reales, corré el scraper (sección
5) o importá un CSV/Excel propio desde `POST /api/import/archivo`.

---

## 5. Actualización de datos: cómo se investigó y cómo funciona

### Lo que se investigó
El MAG publica sus precios en `mercadoagroganadero.com.ar`, en una página
tipo "Precios por categoría" con columnas Categoría / Mínimo / Máximo /
Promedio / Mediana / Cabezas / Importe / Kgs, con un filtro de fecha
inicial/final. **No tiene API pública ni un Excel histórico descargable.**
El sitio es un sistema legacy (`.dll`, tipo ISAPI) y, al probarlo desde
este entorno de desarrollo, devolvió `403 Forbidden` — pero eso fue el
firewall de salida del propio sandbox de desarrollo (tiene una lista
blanca de dominios que no incluye ese sitio), no necesariamente una
protección anti-bot del sitio real. **Este scraper no se pudo probar en
vivo durante el desarrollo** por esa restricción de red del entorno; hace
falta correrlo una vez desde tu computadora o servidor (que sí tienen
salida normal a internet) y ajustar selectores si el sitio cambió de
estructura. El código está escrito para que ese ajuste sea rápido (ver
`app/scraper/parser.py`, que parsea por texto de encabezado en vez de
posición fija de columna, y trae un modo `--debug-save` que guarda el
HTML/capturas para inspeccionar).

Como fuente alternativa se evaluó IPCVA (Instituto de Promoción de la
Carne Vacuna Argentina), que publica informes mensuales de precios, pero
en formato PDF (no series descargables) — quedó documentado como opción
de referencia cruzada, no como fuente primaria automatizada.

### Cómo actualizar los datos

**a) Automático — scraper diario**
```bash
cd backend
python -m app.scraper.run_daily_update
```
Intenta primero un scraper liviano (`requests`); si falla (por ejemplo,
por protección anti-bot), reintenta con un navegador real vía Playwright
(`playwright install chromium` una sola vez). Si ambos fallan, **no
modifica la base** y termina con código de error, para que un cron/CI
pueda avisar del fallo sin arriesgar el histórico.

**b) Backfill histórico** (una sola vez, para cargar años previos)
```bash
python -m app.scraper.playwright_scraper --desde 2021-07-01 --hasta 2026-07-19 --debug-save
```

**c) Programar la actualización diaria** — tres formas, elegí la que te
quede más cómoda:

1. **Cron (Linux/Mac)** — agregar a `crontab -e`:
   ```
   0 20 * * 1-5 cd /ruta/al/proyecto/backend && .venv/bin/python -m app.scraper.run_daily_update >> logs/update.log 2>&1
   ```
2. **Task Scheduler (Windows)** — crear una tarea diaria que ejecute
   `python -m app.scraper.run_daily_update` con directorio de trabajo en
   `backend/`.
3. **GitHub Actions** (sin necesitar un servidor propio) — ya incluido en
   `.github/workflows/daily-update.yml`: corre de lunes a viernes a las
   20:00 (hora Argentina), y comitea la base SQLite actualizada al repo
   (o usa un secret `DATABASE_URL` para apuntar a Postgres en lugar de
   tocar el archivo).
4. **Proceso propio** — `python -m app.scheduler` deja un proceso vivo
   (APScheduler) que dispara la actualización todos los días a las 20:00;
   útil si corrés el backend en un VPS con systemd/pm2.

**d) Importación manual (respaldo)** — si el sitio cambia de estructura y
el scraper deja de funcionar, se puede cargar un día (o un histórico
entero) a mano:
```bash
curl -F "archivo=@precios_del_dia.csv" http://localhost:8000/api/import/archivo
```
Columnas esperadas: `fecha, categoria, precio_promedio` (obligatorias) +
`peso_promedio, precio_maximo, precio_minimo, cabezas,
kg_comercializados` (opcionales). Ver `GET /api/import/plantilla` para el
detalle exacto y las categorías válidas.

---

## 6. Cómo funciona el tablero

- **Dashboard principal** (`/`): tarjetas KPI de ternero (compra) y
  novillo (venta) con variación semanal/mensual/anual, indicador de
  relación compra/venta (ternero ÷ novillo, ambos en $/kg vivo), gráficos
  de evolución de cada uno a 5 años, y un resumen rápido de semáforo por
  categoría.
- **Histórico de precios** (`/historico`): gráficos interactivos con
  filtros por categoría, año, rango de fechas y peso; incluye vista de
  tabla (accesible) además del gráfico.
- **Situación actual** (`/situacion`): compara el precio de hoy contra el
  promedio de 12 y 24 meses y contra el máximo/mínimo histórico, con
  semáforo (verde = precio bajo respecto al histórico, amarillo = normal,
  rojo = elevado). El umbral del semáforo es configurable vía
  `SEMAFORO_UMBRAL_BAJO` / `SEMAFORO_UMBRAL_ALTO` en `.env` (por defecto
  ±8% respecto al promedio de 12 meses).

### Categorías soportadas
Terneros · Novillitos 300-390 kg · Novillitos 391-430 kg · Novillos +430 kg
· Vaquillonas · Vacas — definidas en `backend/app/models.py::CATEGORIAS`.

### Qué categoría representa "ternero de compra" y "novillo de venta"
Por defecto: `Terneros` y `Novillos +430 kg` respectivamente (configurable
en `.env` vía `KPI_CATEGORIA_TERNERO` / `KPI_CATEGORIA_NOVILLO`, por si
preferís usar otro corte de peso para el novillo de venta).

---

## 7. Pasar de SQLite a Postgres

1. Levantar un Postgres (podés descomentar el servicio `db` en
   `docker-compose.yml`).
2. Cambiar `DATABASE_URL` en `backend/.env`, por ejemplo:
   ```
   DATABASE_URL=postgresql+psycopg2://mag:mag@localhost:5432/mag_dashboard
   ```
3. Reiniciar el backend: al arrancar crea las tablas automáticamente si
   no existen (`Base.metadata.create_all`). Para migrar los datos de
   SQLite a Postgres podés exportar `price_records` a CSV y usar el
   importador manual (`/api/import/archivo`).

---

## 8. API — endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/dashboard` | KPIs de ternero/novillo + relación compra/venta |
| GET | `/api/dashboard/kpi/{categoria}` | KPI de cualquier categoría |
| GET | `/api/precios/historico` | Serie histórica filtrable (`categoria`, `anio`, `fecha_desde`, `fecha_hasta`, `peso_min`, `peso_max`) |
| GET | `/api/precios/ultimo` | Último precio de una categoría |
| GET | `/api/situacion-actual` | Semáforo + comparación vs promedios/máx/mín para todas las categorías |
| GET | `/api/categorias` | Categorías oficiales y con datos cargados |
| POST | `/api/import/archivo` | Importar CSV/Excel manual |
| GET | `/api/import/plantilla` | Columnas esperadas para importar |

Documentación completa e interactiva en `/docs` (Swagger UI) una vez que
el backend está corriendo.

---

## 9. Limitaciones conocidas y próximos pasos sugeridos

- El scraper **no se probó contra el sitio real** durante este desarrollo
  por la restricción de red del entorno usado para construirlo (ver
  sección 5). Antes de depender de él en producción, corré
  `python -m app.scraper.requests_scraper --debug-save` una vez y
  confirmá que `parsear_tabla_precios` reconoce bien las columnas; si no,
  ajustá `ENCABEZADOS_ESPERADOS` / `MAPA_CATEGORIAS` en
  `app/scraper/parser.py` mirando el HTML guardado en `data/debug/`.
- Los 5 años de histórico que trae la base son **ilustrativos**, no reales
  (ver sección 4). Reemplazarlos con el scraper/importador es el primer
  paso recomendado antes de usar el tablero para decisiones reales.
- El semáforo usa un umbral simple (±8% vs promedio 12 meses); si
  preferís algo más sofisticado (percentiles, bandas de desvío estándar,
  ajuste estacional) es un cambio acotado en
  `app/services/analytics.py::clasificar_semaforo`.
- No se implementó autenticación: la API queda abierta en `localhost`. Si
  se despliega en un servidor público, agregar al menos un API key en el
  endpoint de importación (`/api/import/archivo`) para que no cualquiera
  pueda escribir en la base.

---

## 10. Despliegue recomendado en Render (versión corregida)

Esta versión evita el error 502 que podía aparecer cuando el backend gratuito
estaba dormido o cuando `NEXT_PUBLIC_API_URL` no quedaba incorporada durante el
build del frontend.

### Servicios ya creados manualmente

En el servicio del **frontend**, configurá estas variables:

```text
API_URL=https://TU-BACKEND.onrender.com
NEXT_PUBLIC_API_URL=https://TU-BACKEND.onrender.com
```

La primera se lee en tiempo de ejecución y es la recomendada. La segunda se
mantiene por compatibilidad.

Configuración del backend:

```text
Root Directory: backend
Dockerfile Path: Dockerfile
Docker Build Context: .
Docker Command: vacío
Pre-Deploy Command: vacío
Health Check Path: /api/health
```

Configuración del frontend:

```text
Root Directory: frontend
Dockerfile Path: Dockerfile
Docker Build Context: .
Docker Command: vacío
Pre-Deploy Command: vacío
```

Luego usá **Manual Deploy → Clear build cache & deploy** en el frontend para
asegurar que la URL anterior no quede guardada en caché.

### Blueprint opcional

El archivo `render.yaml` permite crear ambos servicios desde un Blueprint. Antes
de sincronizarlo, reemplazá las dos URL de ejemplo por la URL real de tu backend
si fuera distinta.
