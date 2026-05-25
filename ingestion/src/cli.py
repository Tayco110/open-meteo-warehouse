"""CLI da ingestão.

Exemplos:
    openmeteo-ingest --since 2024-01-01 --until 2024-01-31
    openmeteo-ingest --since 2020-01-01 --locations "São Paulo" Reykjavik
"""

import argparse
import logging
import sys
from datetime import date

from .config import Settings
from .pipeline import run_ingestion

logger = logging.getLogger("openmeteo-ingest")


def _parse_date(s: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Data inválida: {s!r} (use YYYY-MM-DD)") from e


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openmeteo-ingest",
        description="Coleta dados meteorológicos da Open-Meteo e persiste no Postgres.",
    )
    parser.add_argument(
        "--since", type=_parse_date,
        help="Data inicial (YYYY-MM-DD). Default: INGESTION_START_DATE do .env",
    )
    parser.add_argument(
        "--until", type=_parse_date, default=date.today(),
        help="Data final (YYYY-MM-DD). Default: hoje",
    )
    parser.add_argument(
        "--locations", nargs="+",
        help="Cidades para coletar (case-insensitive). Default: todas em locations.json",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings = Settings()

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    since = args.since or settings.ingestion_start_date
    if since > args.until:
        logger.error("--since (%s) é posterior a --until (%s)", since, args.until)
        return 2

    try:
        stats = run_ingestion(
            start_date=since,
            end_date=args.until,
            settings=settings,
            location_filter=args.locations,
        )
    except Exception:
        logger.exception("Falha durante a ingestão")
        return 1

    print()
    print("Ingestão concluída:")
    print(f"  localidades processadas : {stats.locations}")
    print(f"  medições coletadas      : {stats.measurements_collected}")
    print(f"  medições upserted       : {stats.measurements_upserted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
