"""Persistência no PostgreSQL: upserts em dim_location e fact_weather_daily."""

import logging
from collections.abc import Iterable
from contextlib import contextmanager
from typing import Iterator

import psycopg

from .client import Location
from .transform import WeatherMeasurement

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


@contextmanager
def get_connection(database_url: str) -> Iterator[psycopg.Connection]:
    """Abre conexão com commit explícito (autocommit=False)."""
    with psycopg.connect(database_url, autocommit=False) as conn:
        yield conn


def upsert_locations(
    conn: psycopg.Connection,
    locations: Iterable[Location],
) -> dict[tuple[str, str], int]:
    """Upsert em dim_location; retorna mapping (city, country) → location_id."""
    mapping: dict[tuple[str, str], int] = {}
    with conn.cursor() as cur:
        for loc in locations:
            cur.execute(
                """
                INSERT INTO dim_location (city, country, latitude, longitude, timezone)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (city, country) DO UPDATE SET
                    latitude  = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    timezone  = EXCLUDED.timezone
                RETURNING location_id
                """,
                (loc.city, loc.country, loc.latitude, loc.longitude, loc.timezone),
            )
            row = cur.fetchone()
            assert row is not None
            mapping[(loc.city, loc.country)] = row[0]
    conn.commit()
    logger.info("Upserted %d localidades em dim_location", len(mapping))
    return mapping


def load_variable_map(conn: psycopg.Connection) -> dict[str, int]:
    """Carrega mapping code → variable_id a partir de dim_variable."""
    with conn.cursor() as cur:
        cur.execute("SELECT code, variable_id FROM dim_variable")
        return dict(cur.fetchall())


def upsert_measurements(
    conn: psycopg.Connection,
    measurements: Iterable[WeatherMeasurement],
    location_map: dict[tuple[str, str], int],
    variable_map: dict[str, int],
) -> int:
    """Upsert em fact_weather_daily em lotes. Pula medições com value=None."""
    rows: list[tuple[int, int, int, float]] = []
    for m in measurements:
        if m.value is None:
            continue
        rows.append((
            location_map[(m.city, m.country)],
            int(m.date.strftime("%Y%m%d")),
            variable_map[m.variable_code],
            m.value,
        ))

    if not rows:
        return 0

    sql = """
        INSERT INTO fact_weather_daily (location_id, date_id, variable_id, value)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (location_id, date_id, variable_id) DO UPDATE SET
            value     = EXCLUDED.value,
            loaded_at = NOW()
    """
    with conn.cursor() as cur:
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            cur.executemany(sql, batch)
            logger.debug("Upserted lote %d-%d", i, i + len(batch))
    conn.commit()
    logger.info("Upserted %d medições em fact_weather_daily", len(rows))
    return len(rows)
