"""Schemas Pydantic para os responses da API."""

from datetime import date

from pydantic import BaseModel


class LocationOut(BaseModel):
    location_id: int
    city: str
    country: str
    latitude: float
    longitude: float
    timezone: str


class VariableOut(BaseModel):
    code: str
    name: str
    unit: str
    category: str
    description: str | None = None


class TimeSeriesPoint(BaseModel):
    date: date
    value: float


class WeatherSeries(BaseModel):
    city: str
    country: str
    variable: str
    variable_name: str
    unit: str
    data: list[TimeSeriesPoint]


class WeatherResponse(BaseModel):
    series: list[WeatherSeries]


class StatItem(BaseModel):
    city: str
    variable: str
    variable_name: str
    unit: str
    min: float
    max: float
    avg: float
    count: int


class HealthResponse(BaseModel):
    status: str
    database: str
