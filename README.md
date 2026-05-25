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

## Uso de IA

Esta seção será preenchida ao final do projeto, documentando explicitamente onde a IA (Claude) foi utilizada e por quê.
