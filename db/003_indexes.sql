-- ============================================================
-- Índices para os padrões de query do dashboard.
--
-- A PK do fato (location_id, date_id, variable_id) já cobre
-- queries que filtram por essas três colunas. Os índices abaixo
-- aceleram filtros parciais comuns no dashboard.
-- ============================================================

-- Filtro mais comum: variável + intervalo de datas (séries temporais)
CREATE INDEX IF NOT EXISTS idx_fact_weather_variable_date
    ON fact_weather_daily (variable_id, date_id);

-- Filtro por localidade (KPIs e comparativos por cidade)
CREATE INDEX IF NOT EXISTS idx_fact_weather_location_date
    ON fact_weather_daily (location_id, date_id);

-- dim_date: range queries por data e agregações por ano/mês
CREATE INDEX IF NOT EXISTS idx_dim_date_date  ON dim_date (date);
CREATE INDEX IF NOT EXISTS idx_dim_date_year  ON dim_date (year);
CREATE INDEX IF NOT EXISTS idx_dim_date_month ON dim_date (year, month);
