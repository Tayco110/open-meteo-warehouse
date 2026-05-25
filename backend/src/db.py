"""Pool de conexões PostgreSQL + dependency injection para FastAPI."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from psycopg import Connection
from psycopg_pool import ConnectionPool


def get_pool(request: Request) -> ConnectionPool:
    return request.app.state.pool


def get_db(
    pool: Annotated[ConnectionPool, Depends(get_pool)],
) -> Generator[Connection, None, None]:
    with pool.connection() as conn:
        yield conn


DbDep = Annotated[Connection, Depends(get_db)]
