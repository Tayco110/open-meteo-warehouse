"""Scheduler diário da ingestão (APScheduler)."""

import logging
from datetime import date, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import Settings
from .pipeline import run_ingestion

logger = logging.getLogger(__name__)


def _run_daily_job(settings: Settings) -> None:
    """Coleta os últimos N dias e persiste. Erros são logados, não derrubam o scheduler."""
    end_date = date.today()
    start_date = end_date - timedelta(days=settings.scheduler_lookback_days)
    logger.info("Job diário iniciado (%s → %s)", start_date, end_date)
    try:
        stats = run_ingestion(start_date, end_date, settings)
        logger.info(
            "Job diário concluído: %d cidade(s), %d medições upserted",
            stats.locations, stats.measurements_upserted,
        )
    except Exception:
        logger.exception("Falha no job diário; a próxima execução tentará de novo.")


def start_scheduler(settings: Settings, run_on_startup: bool = True) -> None:
    scheduler = BlockingScheduler()
    scheduler.add_job(
        _run_daily_job,
        args=[settings],
        trigger=CronTrigger(
            hour=settings.scheduler_cron_hour,
            minute=settings.scheduler_cron_minute,
        ),
        id="daily_ingestion",
        name="Ingestão diária Open-Meteo",
    )

    logger.info(
        "Scheduler iniciado: cron diário às %02d:%02d, lookback %d dia(s)",
        settings.scheduler_cron_hour,
        settings.scheduler_cron_minute,
        settings.scheduler_lookback_days,
    )

    if run_on_startup:
        logger.info("Executando job de startup antes de aguardar o cron...")
        _run_daily_job(settings)

    scheduler.start()
