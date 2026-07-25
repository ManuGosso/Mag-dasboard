# Cómo publicar esta versión

## Plataforma recomendada: Render

Este proyecto no es un sitio estático: incluye un frontend Next.js, una API FastAPI y una base SQLite. Por eso no debe cargarse completo en Netlify.

1. Subí el contenido de esta carpeta a la raíz de un repositorio de GitHub.
2. Verificá que GitHub muestre `backend/data/mag_dashboard.db`.
3. En Render elegí **New > Blueprint**.
4. Conectá el repositorio y dejá que Render lea `render.yaml`.
5. Render creará dos servicios: `mag-dashboard-api` y `mag-dashboard-web`.
6. Primero comprobá la API entrando a `/api/health`; debe indicar `status: ok` y aproximadamente 1566 registros.
7. Luego abrí el servicio web.

## Nota sobre los datos

La base SQLite incluida permite que el tablero abra con datos de muestra. Render usa un sistema de archivos efímero en servicios gratuitos: las actualizaciones hechas dentro del servidor pueden perderse al reiniciar o redesplegar. Para actualización permanente conviene migrar luego a PostgreSQL.

## Si el frontend no encuentra la API

En el servicio `mag-dashboard-web`, configurá estas variables con la URL pública exacta del backend:

- `API_URL=https://TU-BACKEND.onrender.com`
- `NEXT_PUBLIC_API_URL=https://TU-BACKEND.onrender.com`

Después ejecutá **Manual Deploy > Clear build cache & deploy**.
