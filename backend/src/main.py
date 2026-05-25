"""API FastAPI: endpoints para o dashboard meteorológico."""

import itertools
import logging
from collections.abc import Sequence
from contextlib import asynccontextmanager
from datetime import date
from typing import Any, Literal

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import Settings
from .db import DbDep
from .schemas import (
    HealthResponse,
    LocationOut,
    StatItem,
    VariableOut,
    WeatherResponse,
    WeatherSeries,
)

logger = logging.getLogger(__name__)

Aggregation = Literal["daily", "monthly"]


# ---------- helpers ----------

def _build_filters(
    locations: Sequence[str] | None,
    variables: Sequence[str] | None,
    start_date: date | None,
    end_date: date | None,
) -> tuple[str, list[Any]]:
    """Constrói a cláusula WHERE parametrizada para queries no fato."""
    clauses: list[str] = []
    params: list[Any] = []
    if locations:
        clauses.append("LOWER(l.city) = ANY(%s)")
        params.append([c.lower() for c in locations])
    if variables:
        clauses.append("v.code = ANY(%s)")
        params.append(list(variables))
    if start_date:
        clauses.append("d.date >= %s")
        params.append(start_date)
    if end_date:
        clauses.append("d.date <= %s")
        params.append(end_date)
    where = " AND ".join(clauses) if clauses else "TRUE"
    return where, params


# ---------- app factory ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    pool = ConnectionPool(
        settings.database_url,
        min_size=1,
        max_size=5,
        open=False,
    )
    pool.open()
    pool.wait()
    app.state.pool = pool
    logger.info("Pool de conexões aberto")
    try:
        yield
    finally:
        pool.close()
        logger.info("Pool de conexões fechado")


def create_app() -> FastAPI:
    settings = Settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = FastAPI(
        title="open-meteo-warehouse API",
        description="API para consulta de dados meteorológicos históricos.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    # ---------- endpoints ----------

    @app.get("/api/health", response_model=HealthResponse, tags=["health"])
    def health(conn: DbDep) -> dict:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"status": "ok", "database": "ok"}

    @app.get("/api/locations", response_model=list[LocationOut], tags=["catalog"])
    def list_locations(conn: DbDep) -> list[dict]:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT location_id, city, country,
                       latitude::float AS latitude,
                       longitude::float AS longitude,
                       timezone
                FROM dim_location
                ORDER BY city
                """
            )
            return cur.fetchall()

    @app.get("/api/variables", response_model=list[VariableOut], tags=["catalog"])
    def list_variables(conn: DbDep) -> list[dict]:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT code, name, unit, category, description
                FROM dim_variable
                ORDER BY category, code
                """
            )
            return cur.fetchall()

    @app.get("/api/weather", response_model=WeatherResponse, tags=["weather"])
    def get_weather(
        conn: DbDep,
        locations: list[str] | None = Query(None),
        variables: list[str] | None = Query(None),
        start_date: date | None = Query(None),
        end_date: date | None = Query(None),
        aggregation: Aggregation = Query("daily"),
    ) -> dict:
        where, params = _build_filters(locations, variables, start_date, end_date)

        if aggregation == "monthly":
            sql = f"""
                SELECT
                    l.city, l.country,
                    v.code AS variable, v.name AS variable_name, v.unit,
                    DATE_TRUNC('month', d.date)::DATE AS date,
                    AVG(f.value)::float AS value
                FROM fact_weather_daily f
                JOIN dim_location l USING (location_id)
                JOIN dim_date d     USING (date_id)
                JOIN dim_variable v USING (variable_id)
                WHERE {where}
                GROUP BY l.city, l.country, v.code, v.name, v.unit,
                         DATE_TRUNC('month', d.date)
                ORDER BY l.city, v.code, date
            """
        else:
            sql = f"""
                SELECT
                    l.city, l.country,
                    v.code AS variable, v.name AS variable_name, v.unit,
                    d.date AS date,
                    f.value::float AS value
                FROM fact_weather_daily f
                JOIN dim_location l USING (location_id)
                JOIN dim_date d     USING (date_id)
                JOIN dim_variable v USING (variable_id)
                WHERE {where}
                ORDER BY l.city, v.code, d.date
            """

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        series: list[WeatherSeries] = []
        keyfn = lambda r: (r["city"], r["variable"])  # noqa: E731
        for (_city, _var), group in itertools.groupby(rows, key=keyfn):
            group_list = list(group)
            first = group_list[0]
            series.append({
                "city": first["city"],
                "country": first["country"],
                "variable": first["variable"],
                "variable_name": first["variable_name"],
                "unit": first["unit"],
                "data": [{"date": r["date"], "value": r["value"]} for r in group_list],
            })
        return {"series": series}

    @app.get("/api/stats", response_model=list[StatItem], tags=["weather"])
    def get_stats(
        conn: DbDep,
        locations: list[str] | None = Query(None),
        variables: list[str] | None = Query(None),
        start_date: date | None = Query(None),
        end_date: date | None = Query(None),
    ) -> list[dict]:
        where, params = _build_filters(locations, variables, start_date, end_date)
        sql = f"""
            SELECT
                l.city,
                v.code AS variable,
                v.name AS variable_name,
                v.unit,
                MIN(f.value)::float AS min,
                MAX(f.value)::float AS max,
                AVG(f.value)::float AS avg,
                COUNT(*)             AS count
            FROM fact_weather_daily f
            JOIN dim_location l USING (location_id)
            JOIN dim_date d     USING (date_id)
            JOIN dim_variable v USING (variable_id)
            WHERE {where}
            GROUP BY l.city, v.code, v.name, v.unit
            ORDER BY l.city, v.code
        """
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    return app


app = create_app()


def run() -> None:
    settings = Settings()
    uvicorn.run(
        "src.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
    )
