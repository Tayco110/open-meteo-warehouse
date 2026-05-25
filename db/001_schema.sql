-- ============================================================
-- open-meteo-warehouse — schema dimensional
--
-- Modelo: 1 fato (medições diárias) + 3 dimensões (localidade,
-- data, variável). Fato em formato "narrow" (long), com uma
-- linha por (localidade × data × variável).
--
-- Idempotente: usa CREATE TABLE IF NOT EXISTS.
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_location (
    location_id  SERIAL PRIMARY KEY,
    city         TEXT          NOT NULL,
    country      TEXT          NOT NULL,
    latitude     NUMERIC(8, 5) NOT NULL,
    longitude    NUMERIC(8, 5) NOT NULL,
    timezone     TEXT          NOT NULL,
    created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dim_location_city_country UNIQUE (city, country)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id      INTEGER  PRIMARY KEY,   -- YYYYMMDD
    date         DATE     NOT NULL UNIQUE,
    year         SMALLINT NOT NULL,
    quarter      SMALLINT NOT NULL,
    month        SMALLINT NOT NULL,
    month_name   TEXT     NOT NULL,
    day          SMALLINT NOT NULL,
    day_of_week  SMALLINT NOT NULL,      -- 0=domingo, 6=sábado
    day_name     TEXT     NOT NULL,
    is_weekend   BOOLEAN  NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_variable (
    variable_id  SERIAL PRIMARY KEY,
    code         TEXT NOT NULL UNIQUE,   -- código da Open-Meteo
    name         TEXT NOT NULL,
    unit         TEXT NOT NULL,
    category     TEXT NOT NULL,          -- temperature | precipitation | wind | radiation
    description  TEXT
);

CREATE TABLE IF NOT EXISTS fact_weather_daily (
    location_id  INTEGER          NOT NULL REFERENCES dim_location(location_id),
    date_id      INTEGER          NOT NULL REFERENCES dim_date(date_id),
    variable_id  INTEGER          NOT NULL REFERENCES dim_variable(variable_id),
    value        DOUBLE PRECISION,
    loaded_at    TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    PRIMARY KEY (location_id, date_id, variable_id)
);
