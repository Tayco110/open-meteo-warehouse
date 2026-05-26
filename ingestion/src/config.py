"""Configuração da ingestão — lê variáveis do `.env` na raiz do projeto."""

from datetime import date
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INGESTION_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = INGESTION_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str
    open_meteo_base_url: str = "https://archive-api.open-meteo.com/v1/archive"
    open_meteo_timeout_seconds: int = 30
    ingestion_start_date: date = date(2020, 1, 1)
    ingestion_locations_file: Path = INGESTION_DIR / "locations.json"
    log_level: str = "INFO"

    # Scheduler (modo --daemon)
    scheduler_cron_hour: int = 3
    scheduler_cron_minute: int = 0
    scheduler_lookback_days: int = 7

    @field_validator("ingestion_locations_file", mode="after")
    @classmethod
    def _resolve_locations(cls, v: Path) -> Path:
        return v if v.is_absolute() else INGESTION_DIR / v
