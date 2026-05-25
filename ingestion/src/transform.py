"""Transformação wide → long: explode arrays paralelos em uma linha por medição."""

from dataclasses import dataclass
from datetime import date

from .client import Location, WeatherResponse


@dataclass(frozen=True, slots=True)
class WeatherMeasurement:
    """Uma medição diária (chave: city × country × date × variable_code)."""

    city: str
    country: str
    date: date
    variable_code: str
    value: float | None


def to_long(location: Location, response: WeatherResponse) -> list[WeatherMeasurement]:
    """Converte a resposta wide da Open-Meteo em medições long.

    Preserva valores `None` (a API ocasionalmente retorna gaps); o loader
    decide se descarta ou insere como NULL no fato.
    """
    daily = response.daily
    variable_codes = [f for f in daily.__class__.model_fields if f != "time"]

    measurements: list[WeatherMeasurement] = []
    for i, day in enumerate(daily.time):
        for code in variable_codes:
            measurements.append(
                WeatherMeasurement(
                    city=location.city,
                    country=location.country,
                    date=day,
                    variable_code=code,
                    value=getattr(daily, code)[i],
                )
            )
    return measurements
