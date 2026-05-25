from datetime import date

import pytest

from src.client import DAILY_VARIABLES, DailyWeather, Location, WeatherResponse
from src.transform import to_long


def _location() -> Location:
    return Location(
        city="Test City",
        country="Test Country",
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
    )


def _response(time: list[date], values: dict[str, list[float | None]]) -> WeatherResponse:
    return WeatherResponse(
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
        daily=DailyWeather(time=time, **values),
    )


def test_to_long_expands_to_one_row_per_date_and_variable():
    days = [date(2024, 1, 1), date(2024, 1, 2)]
    response = _response(
        time=days,
        values={code: [1.0, 2.0] for code in DAILY_VARIABLES},
    )

    result = to_long(_location(), response)

    assert len(result) == len(days) * len(DAILY_VARIABLES)
    assert {m.variable_code for m in result} == set(DAILY_VARIABLES)
    assert {m.date for m in result} == set(days)


def test_to_long_preserves_none_values():
    response = _response(
        time=[date(2024, 1, 1)],
        values={code: [None] for code in DAILY_VARIABLES},
    )

    result = to_long(_location(), response)

    assert all(m.value is None for m in result)


def test_response_rejects_mismatched_array_lengths():
    bad_values = {code: [1.0, 2.0] for code in DAILY_VARIABLES}
    bad_values["temperature_2m_max"] = [1.0]  # tamanho errado

    with pytest.raises(ValueError, match="Inconsistência na resposta"):
        _response(time=[date(2024, 1, 1), date(2024, 1, 2)], values=bad_values)
