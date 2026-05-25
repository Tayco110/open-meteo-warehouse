"""Testes integration: tocam o banco real (Supabase) via TestClient."""

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}


def test_list_locations(client):
    r = client.get("/api/locations")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert {"location_id", "city", "country"} <= set(data[0])


def test_list_variables(client):
    r = client.get("/api/variables")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert {"code", "name", "unit", "category"} <= set(data[0])


def test_weather_with_filters(client):
    r = client.get(
        "/api/weather",
        params={
            "locations": ["São Paulo"],
            "variables": ["temperature_2m_max"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["series"]) == 1
    series = body["series"][0]
    assert series["city"] == "São Paulo"
    assert series["variable"] == "temperature_2m_max"
    assert len(series["data"]) == 7


def test_weather_monthly_aggregation(client):
    r = client.get(
        "/api/weather",
        params={
            "locations": ["São Paulo"],
            "variables": ["temperature_2m_max"],
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "aggregation": "monthly",
        },
    )
    assert r.status_code == 200
    series = r.json()["series"][0]
    # 3 meses = 3 pontos
    assert len(series["data"]) == 3


def test_stats(client):
    r = client.get(
        "/api/stats",
        params={
            "locations": ["São Paulo"],
            "variables": ["temperature_2m_max"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    stat = data[0]
    assert stat["count"] == 31
    assert stat["min"] <= stat["avg"] <= stat["max"]
