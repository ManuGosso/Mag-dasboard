"""
Alternativa a cron/Task Scheduler: un proceso Python de larga duracion
que se queda corriendo y dispara la actualizacion diaria solo, usando
APScheduler. Util si vas a correr el backend en un servidor/VPS propio
(por ejemplo, dentro de un contenedor Docker separado, o con systemd/pm2
manteniendolo vivo).

Si preferis usar el cron del sistema operativo o GitHub Actions en su
lugar, no hace falta este archivo: alcanza con ejecutar
`python -m app.scraper.run_daily_update` desde ahi (ver README.md).

Uso:
    python -m app.scheduler
"""
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.scraper.run_daily_update import main as actualizar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler")

# Corre todos los dias a las 20:00 (hora Argentina), despues del cierre
# habitual de ruedas del mercado. Ajustar la hora si hace falta.
HORA_ACTUALIZACION = {"hour": 20, "minute": 0}
ZONA_HORARIA = "America/Argentina/Buenos_Aires"


def job():
    logger.info("Disparando actualizacion diaria programada...")
    codigo = actualizar()
    if codigo == 0:
        logger.info("Actualizacion diaria OK.")
    else:
        logger.error("Actualizacion diaria termino con errores (codigo %s).", codigo)


def main():
    scheduler = BlockingScheduler(timezone=ZONA_HORARIA)
    scheduler.add_job(job, CronTrigger(**HORA_ACTUALIZACION, timezone=ZONA_HORARIA))
    logger.info(
        "Scheduler iniciado. Actualizara la base todos los dias a las %02d:%02d (%s).",
        HORA_ACTUALIZACION["hour"],
        HORA_ACTUALIZACION["minute"],
        ZONA_HORARIA,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler detenido.")


if __name__ == "__main__":
    main()
