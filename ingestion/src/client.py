"""Cliente HTTP da Open-Meteo Historical API + modelos de domínio."""

import json
import logging
from datetime import date
from pathlib import Path

import httpx
from pydantic import BaseModel, model_validator
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Variáveis solicitadas à Open-Meteo. Os códigos devem casar com `dim_variable.code`.
DAILY_VARIABLES: tuple[str, ...] = (
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_mean",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "windspeed_10m_max",
    "shortwave_radiation_sum",
    "sunshine_duration",
)


class Location(BaseModel):
    city: str
    country: str
    latitude: float
    longitude: float
    timezone: str


class DailyWeather(BaseModel):
    """Resposta diária no formato wide: arrays paralelos indexados por `time`."""

    time: list[date]
    temperature_2m_max: list[float | None]
    temperature_2m_min: list[float | None]
    temperature_2m_mean: list[float | None]
    apparent_temperature_mean: list[float | None]
    precipitation_sum: list[float | None]
    rain_sum: list[float | None]
    snowfall_sum: list[float | None]
    windspeed_10m_max: list[float | None]
    shortwave_radiation_sum: list[float | None]
    sunshine_duration: list[float | None]

    @model_validator(mode="after")
    def _check_array_lengths(self) -> "DailyWeather":
        n = len(self.time)
        for name in type(self).model_fields:
            if name == "time":
                continue
            arr = getattr(self, name)
            if len(arr) != n:
                raise ValueError(
                    f"Inconsistência na resposta: {name} tem {len(arr)} valores, esperado {n}"
                )
        return self


class WeatherResponse(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    daily: DailyWeather


def load_locations(path: Path) -> list[Location]:
    """Lê e valida a lista de localidades a partir de um arquivo JSON."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Location.model_validate(item) for item in raw]


class OpenMeteoClient:
    """Cliente síncrono da Open-Meteo Historical API."""

    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self._base_url = base_url
        self._client = httpx.Client(timeout=timeout)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    def fetch_daily(
        self,
        location: Location,
        start_date: date,
        end_date: date,
    ) -> WeatherResponse:
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": ",".join(DAILY_VARIABLES),
            "timezone": location.timezone,
        }
        logger.info(
            "Coletando %s, %s (%s a %s)",
            location.city, location.country, start_date, end_date,
        )
        response = self._client.get(self._base_url, params=params)
        response.raise_for_status()
        return WeatherResponse.model_validate(response.json())

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "OpenMeteoClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
