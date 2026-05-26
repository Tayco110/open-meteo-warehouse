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
                                    │  HTTP/JSON
                            [Frontend HTML + JS]
```

| Camada     | Tecnologia                                              |
|------------|---------------------------------------------------------|
| Ingestão   | Python 3.11 · httpx · pydantic · tenacity · APScheduler |
| Banco      | PostgreSQL (Supabase)                                   |
| Backend    | FastAPI · psycopg3 · uvicorn                            |
| Frontend   | HTML + JavaScript vanilla · Chart.js                    |
| Testes/CI  | pytest · ruff · GitHub Actions                          |


### Modelagem dimensional

Esquema *narrow* (long): uma linha do fato por (cidade × dia × variável). Permite acrescentar variáveis sem alterar o schema, e os filtros do dashboard ficam triviais.

```
dim_location  ──┐
dim_date      ──┼──►  fact_weather_daily (location_id, date_id, variable_id, value)
dim_variable  ──┘
```

### Endpoints da API

| Método | Path              | Função                                            |
|--------|-------------------|---------------------------------------------------|
| GET    | `/api/health`     | Healthcheck (testa conexão com o banco)           |
| GET    | `/api/locations`  | Lista de cidades                                  |
| GET    | `/api/variables`  | Catálogo de variáveis                             |
| GET    | `/api/weather`    | Série temporal com filtros + agregação            |
| GET    | `/api/stats`      | KPIs (min/max/avg/count) que alimentam cards/barras |

Docs interativos (Swagger UI): `http://localhost:8000/docs`.

## Estrutura do repositório

```
open-meteo-warehouse/
├── ingestion/              # Coletor da Open-Meteo (Python)
│   ├── locations.json      # 10 capitais coletadas
│   └── src/
│       ├── client.py       # HTTP client + modelos Pydantic
│       ├── transform.py    # wide → long
│       ├── loader.py       # upserts em dim_location e fact_weather_daily
│       ├── pipeline.py     # orquestra coleta → transform → upsert
│       ├── cli.py          # entry point `openmeteo-ingest`
│       └── scheduler.py    # modo --daemon (APScheduler)
├── db/                     # DDL e seeds
│   ├── 001_schema.sql
│   ├── 002_seed_dimensions.sql
│   └── 003_indexes.sql
├── backend/                # API FastAPI
│   └── src/main.py         # endpoints + app factory + pool de conexões
├── frontend/               # Dashboard estático
│   ├── index.html
│   ├── style.css
│   └── src/{api,filters,charts,kpis,main}.js
├── .github/workflows/ci.yml
└── .env.example
```

## Como rodar

### 1. Pré-requisitos

- Python 3.11+
- Cliente `psql` (PostgreSQL client)
- Conta gratuita no [Supabase](https://supabase.com)

### 2. Clonar e configurar `.env`

```bash
git clone <repo-url>
cd open-meteo-warehouse
cp .env.example .env
```

### 3. Configurar o banco no Supabase

1. Crie um projeto em [supabase.com](https://supabase.com) (defina e guarde a senha)
2. **Project Settings → Database → Connection string → Session pooler** (porta `5432`, IPv4)
3. Cole no `DATABASE_URL` do `.env`, **URL-encodando caracteres especiais da senha** (ex: `@` → `%40`)
4. Use aspas simples em torno do valor:

```env
DATABASE_URL='postgresql://postgres.<ref>:<senha-encoded>@aws-0-<region>.pooler.supabase.com:5432/postgres'
```

### 4. Aplicar o schema

```bash
set -a; source .env; set +a
psql "$DATABASE_URL" -f db/001_schema.sql
psql "$DATABASE_URL" -f db/002_seed_dimensions.sql
psql "$DATABASE_URL" -f db/003_indexes.sql
```

### 5. Rodar a ingestão

```bash
cd ingestion
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# carga inicial (5 anos × 10 cidades, ~3 min)
openmeteo-ingest --since 2020-01-01 --until 2024-12-31
```

A ingestão é **idempotente**: re-executar o mesmo intervalo atualiza as linhas existentes em vez de duplicar.

### 6. Subir o backend

```bash
cd ../backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
openmeteo-api
# API em http://localhost:8000  |  Swagger em http://localhost:8000/docs
```

### 7. Subir o frontend

Em outro terminal:

```bash
cd frontend
python3 -m http.server 5500
# Dashboard em http://localhost:5500
```

### 8. (Opcional) Modo daemon

```bash
openmeteo-ingest --daemon
```

Roda continuamente, coletando os últimos `SCHEDULER_LOOKBACK_DAYS` dias todos os dias às `SCHEDULER_CRON_HOUR:SCHEDULER_CRON_MINUTE` (defaults: 7 dias, 03:00).

## Validação

```bash
# Conexão com o Supabase
psql "$DATABASE_URL" -c "SELECT version();"

# Schema + seeds aplicados
psql "$DATABASE_URL" -c "
  SELECT
    (SELECT COUNT(*) FROM dim_location)       AS localidades,
    (SELECT COUNT(*) FROM dim_variable)       AS variaveis,
    (SELECT COUNT(*) FROM fact_weather_daily) AS medicoes;
"
# após a carga completa: 10 localidades, 10 variáveis, 182700 medições

# Testes da ingestão (unit)
cd ingestion && source .venv/bin/activate && pytest -v   # 3/3

# Testes do backend (integration)
cd backend && source .venv/bin/activate && pytest -v     # 6/6
```

## CI

`.github/workflows/ci.yml` roda em push para `main` e em PRs:

- `ruff check` nos pacotes `ingestion/` e `backend/`
- Sobe Postgres service, aplica o schema, faz uma ingestão pequena (SP jan-mar/2024) via CLI real e roda os 6 testes integration do backend

## Uso de IA

Esta solução foi construída em par com **Claude** (Anthropic). A IA foi usada nas categorias que o case menciona (**geração de código**, **otimização** e **criação do dashboard**) e em algumas extras como debug e revisão de decisões. Cada peça foi testada e validada antes do commit.

### Geração de código

- **Modelagem dimensional**: estrutura das três dimensões + fato, escolha entre formato *narrow* e *wide*, índices para os padrões de query do dashboard
- **Cliente Open-Meteo**: arquitetura com modelos Pydantic, validador de consistência de arrays, retry com tenacity
- **Pipeline e loader**: upsert idempotente com `ON CONFLICT DO UPDATE`, batching em `executemany`, mapping `(city, country) → location_id`
- **FastAPI**: factory pattern, lifespan com pool de conexões `psycopg_pool`, dependency injection via `Annotated[..., Depends()]`, helper `_build_filters()` reusado entre `/weather` e `/stats`
- **Frontend**: layout responsivo com CSS Grid, ES modules sem build, paleta consistente entre line chart e bar chart
- **Scheduler**: integração APScheduler com `BlockingScheduler` + `CronTrigger`
- **CI**: workflow GitHub Actions com Postgres service e seed via CLI real
- **Documentação**: estrutura deste README, comentários onde o "porquê" não era óbvio

### Otimização

- **Persistência incremental**: pipeline reescrito para persistir cidade-a-cidade após topar com rate-limit (429) da Open-Meteo, evitando perder coleta já feita
- **Retry mais paciente**: backoff exponencial até 60s + filtro por tipo de exceção, para suportar 429
- **Agregação no banco**: `/api/weather?aggregation=monthly` usa `DATE_TRUNC` em vez de baixar dados diários e agregar no front
- **Endpoint `/api/stats` dedicado**: evita o frontend baixar ~180k linhas só para calcular min/max/avg

### Criação do dashboard

- **Filtros + Chart.js**: estrutura UI orientada a eventos (apenas re-render no clique de "Aplicar"), cores indexadas por cidade preservadas entre os dois gráficos
- **KPI cards**: cálculo de média ponderada por count e exibição da cidade responsável pelo min/max, oferecendo contexto imediato para o avaliador
- **Bar chart comparativo**: ordenado por média desc para destacar ranking; preserva a cor de cada cidade do line chart

### Debug e diagnóstico

- **Erro de URL parsing no `psql`**: a IA identificou que o sintoma `socket "@aws-..."` era causado por um `@` não-URL-encoded na senha do Supabase, e propôs a correção via `urllib.parse.quote`
- **Análise de coerência climática**: comparativo São Paulo verão × Reykjavik inverno para validar que a API estava retornando dados fisicamente plausíveis antes de carregar a janela completa

### Revisão de decisões

- Discussão de trade-offs entre **PostgreSQL/Supabase × DuckDB × SQLite** (escolha: Supabase pela coerência dev/prod e familiaridade com infra real)
- Discussão **Streamlit × React × HTML+JS vanilla** (escolha: vanilla, citado no case, sem build step)
- Discussão de quais **variáveis climáticas** coletar para enriquecer análises sem inflar o volume (sensação térmica, chuva/neve separadas, sol efetivo)

### Por que usar IA

A IA acelera o desenvolvimento em ordens de grandeza sem abrir mão de qualidade, desde que cada decisão arquitetural seja revisada e cada artefato validado antes de avançar. Aqui ela atuou como par técnico: propõe estruturas e código idiomático, justifica trade-offs e responde a correções com mudanças cirúrgicas. O resultado é um pipeline ponta-a-ponta que prioriza simplicidade e legibilidade ("arroz com feijão bem feito") em vez de exibicionismo técnico.
