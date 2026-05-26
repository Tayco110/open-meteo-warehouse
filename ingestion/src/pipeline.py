"""Orquestração da ingestão: API → transform → upsert."""

import logging
import time
from dataclasses import dataclass
from datetime import date

from .client import OpenMeteoClient, load_locations
from .config import Settings
from .loader import (
    get_connection,
    load_variable_map,
    upsert_locations,
    upsert_measurements,
)
from .transform import to_long

logger = logging.getLogger(__name__)

# Intervalo entre cidades para respeitar rate limit da Open-Meteo (~uma req/s suficiente).
INTER_REQUEST_DELAY_SECONDS = 1.0


@dataclass(frozen=True, slots=True)
class IngestionStats:
    locations: int
    measurements_collected: int
    measurements_upserted: int
    failed_locations: list[str]


def run_ingestion(
    start_date: date,
    end_date: date,
    settings: Settings,
    location_filter: list[str] | None = None,
) -> IngestionStats:
    """Coleta da Open-Meteo e persiste no Postgres, cidade-a-cidade.

    Persistência incremental: cada cidade é coletada, transformada e gravada
    antes da próxima. Falhas em uma cidade são logadas e a coleta continua
    com as próximas; o upsert garante que re-rodar não duplica.
    """
    all_locations = load_locations(settings.ingestion_locations_file)
    if location_filter:
        wanted = {c.lower() for c in location_filter}
        all_locations = [loc for loc in all_locations if loc.city.lower() in wanted]
        if not all_locations:
            raise ValueError(f"Nenhuma localidade casa com {location_filter}")

    logger.info(
        "Iniciando ingestão de %d localidade(s), %s a %s",
        len(all_locations), start_date, end_date,
    )

    total_collected = 0
    total_upserted = 0
    failed: list[str] = []

    with (
        get_connection(settings.database_url) as conn,
        OpenMeteoClient(
            settings.open_meteo_base_url, settings.open_meteo_timeout_seconds
        ) as client,
    ):
        location_map = upsert_locations(conn, all_locations)
        variable_map = load_variable_map(conn)

        for i, loc in enumerate(all_locations):
            try:
                response = client.fetch_daily(loc, start_date, end_date)
                measurements = to_long(loc, response)
                upserted = upsert_measurements(
                    conn, measurements, location_map, variable_map
                )
                total_collected += len(measurements)
                total_upserted += upserted
            except Exception:
                label = f"{loc.city}, {loc.country}"
                logger.exception("Falha ao coletar %s; continuando", label)
                failed.append(label)

            if i < len(all_locations) - 1:
                time.sleep(INTER_REQUEST_DELAY_SECONDS)

    if failed:
        logger.warning(
            "Ingestão concluiu com %d falha(s): %s", len(failed), ", ".join(failed)
        )

    return IngestionStats(
        locations=len(all_locations),
        measurements_collected=total_collected,
        measurements_upserted=total_upserted,
        failed_locations=failed,
    )
