-- ============================================================
-- Seed das dimensões "estáticas":
--   - dim_variable: catálogo de variáveis climáticas coletadas
--   - dim_date:     calendário 2015–2030 (cobre o escopo + folga)
--
-- dim_location é populada pela ingestão (a partir de locations.json).
-- Idempotente via ON CONFLICT.
-- ============================================================

INSERT INTO dim_variable (code, name, unit, category, description) VALUES
    ('temperature_2m_max',        'Temperatura máxima',         '°C',    'temperature',   'Temperatura máxima diária a 2m do solo'),
    ('temperature_2m_min',        'Temperatura mínima',         '°C',    'temperature',   'Temperatura mínima diária a 2m do solo'),
    ('temperature_2m_mean',       'Temperatura média',          '°C',    'temperature',   'Temperatura média diária a 2m do solo'),
    ('apparent_temperature_mean', 'Sensação térmica média',     '°C',    'temperature',   'Sensação térmica média diária (considera umidade e vento)'),
    ('precipitation_sum',         'Precipitação total',         'mm',    'precipitation', 'Precipitação acumulada diária (chuva + neve)'),
    ('rain_sum',                  'Chuva',                      'mm',    'precipitation', 'Chuva acumulada diária (exclui neve)'),
    ('snowfall_sum',              'Neve',                       'cm',    'precipitation', 'Neve acumulada diária'),
    ('windspeed_10m_max',         'Velocidade máx. do vento',   'km/h',  'wind',          'Velocidade máxima do vento a 10m do solo'),
    ('shortwave_radiation_sum',   'Radiação solar',             'MJ/m²', 'radiation',     'Radiação solar diária acumulada'),
    ('sunshine_duration',         'Duração de sol',             's',     'radiation',     'Duração diária de sol efetivo, em segundos')
ON CONFLICT (code) DO NOTHING;

INSERT INTO dim_date (date_id, date, year, quarter, month, month_name, day, day_of_week, day_name, is_weekend)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER         AS date_id,
    d::DATE                                  AS date,
    EXTRACT(YEAR    FROM d)::SMALLINT        AS year,
    EXTRACT(QUARTER FROM d)::SMALLINT        AS quarter,
    EXTRACT(MONTH   FROM d)::SMALLINT        AS month,
    TO_CHAR(d, 'FMMonth')                    AS month_name,
    EXTRACT(DAY     FROM d)::SMALLINT        AS day,
    EXTRACT(DOW     FROM d)::SMALLINT        AS day_of_week,
    TO_CHAR(d, 'FMDay')                      AS day_name,
    EXTRACT(DOW     FROM d) IN (0, 6)        AS is_weekend
FROM generate_series('2015-01-01'::DATE, '2030-12-31'::DATE, '1 day'::INTERVAL) d
ON CONFLICT (date_id) DO NOTHING;
