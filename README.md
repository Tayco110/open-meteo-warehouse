# open-meteo-warehouse

Pipeline completo de dados meteorológicos: ingestão da [Open-Meteo](https://open-meteo.com), modelagem dimensional em PostgreSQL e dashboard web para comparar regiões e períodos.

> Case técnico para vaga de Analista de Dados.

## Arquitetura

```
[Open-Meteo Historical API]
            │
            ▼
   [Ingestão Python]  ──►  [PostgreSQL (Supabase)]
                                    ▲
                                    │
                            [Backend FastAPI]
                                    ▲
                                    │  HTTP
                            [Frontend HTML + JS]
```

| Camada    | Tecnologia                          |
|-----------|-------------------------------------|
| Ingestão  | Python 3.11 + httpx + pydantic      |
| Banco     | PostgreSQL (Supabase)               |
| Backend   | FastAPI                             |
| Frontend  | HTML + JavaScript vanilla + Chart.js|
| Container | Docker Compose                      |

## Estrutura do repositório

```
open-meteo-warehouse/
├── ingestion/   # Coletor da Open-Meteo (Python)
├── db/          # DDL e seeds (SQL)
├── backend/     # API FastAPI
├── frontend/    # Dashboard estático
└── docker-compose.yml
```

## Como rodar

> Documentação detalhada será adicionada conforme o projeto evolui.

### 1. Variáveis de ambiente

```bash
cp .env.example .env
# edite .env conforme necessário
```

### 2. Configurar o banco no Supabase

Crie um projeto em [supabase.com](https://supabase.com), pegue a connection string em **Project Settings → Database → Connection string (Session pooler)** e cole em `DATABASE_URL` no `.env`.

### 3. Aplicar o schema

```bash
set -a; source .env; set +a
psql "$DATABASE_URL" -f db/001_schema.sql
psql "$DATABASE_URL" -f db/002_seed_dimensions.sql
psql "$DATABASE_URL" -f db/003_indexes.sql
```

## Validação

### Conexão com o Supabase

```bash
set -a; source .env; set +a
psql "$DATABASE_URL" -c "SELECT version();"
```

Esperado: retorna a versão do PostgreSQL do Supabase.

### Schema e seeds aplicados

```bash
psql "$DATABASE_URL" <<'EOF'
\dt
SELECT COUNT(*) AS variaveis FROM dim_variable;
SELECT COUNT(*) AS dias, MIN(date) AS de, MAX(date) AS ate FROM dim_date;
EOF
```

Esperado:
- 4 tabelas: `dim_date`, `dim_location`, `dim_variable`, `fact_weather_daily`
- `dim_variable` com 10 linhas
- `dim_date` com 5844 dias, de `2015-01-01` a `2030-12-31`

### Ingestão (Python)

```bash
cd ingestion
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

Esperado: 3/3 testes passando.

Smoke test contra a Open-Meteo (precisa do `.env` na raiz):

```bash
python -c "
from datetime import date
from src.client import OpenMeteoClient, load_locations
from src.config import Settings
from src.transform import to_long

settings = Settings()
locations = load_locations(settings.ingestion_locations_file)
sp = next(l for l in locations if l.city == 'São Paulo')

with OpenMeteoClient(settings.open_meteo_base_url) as client:
    response = client.fetch_daily(sp, date(2024, 1, 1), date(2024, 1, 7))

print(f'{len(to_long(sp, response))} medições coletadas')
"
```

Esperado: `70 medições coletadas` (7 dias × 10 variáveis).

### Carga inicial via CLI

Com o pacote instalado, o comando `openmeteo-ingest` fica disponível:

```bash
# Carga completa (5 anos × 10 cidades, ~3 min)
openmeteo-ingest --since 2020-01-01 --until 2024-12-31

# Janela arbitrária (subset de cidades)
openmeteo-ingest --since 2024-01-01 --until 2024-01-31 --locations "São Paulo" Reykjavik
```

A ingestão é **idempotente**: rodar o mesmo intervalo duas vezes atualiza as linhas existentes em vez de duplicar.

### Banco populado

```bash
psql "$DATABASE_URL" -c "
SELECT
  (SELECT COUNT(*) FROM dim_location)      AS localidades,
  (SELECT COUNT(*) FROM dim_variable)      AS variaveis,
  (SELECT COUNT(*) FROM fact_weather_daily) AS medicoes;
"
```

Esperado após a carga completa: `10 localidades, 10 variáveis, 182700 medições`.

## Uso de IA

Esta seção será preenchida ao final do projeto, documentando explicitamente onde a IA (Claude) foi utilizada e por quê.
