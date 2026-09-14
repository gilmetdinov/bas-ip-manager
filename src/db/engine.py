from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from src.config.env_keys import (
    PG_HOST,
    PG_PORT,
    PG_DB,
    PG_USER,
    PG_PASSWORD,
    SQLITE_PATH,
)


def build_postgres_url() -> str:
    host = os.getenv(PG_HOST, 'localhost')
    port = int(os.getenv(PG_PORT, 5432))
    db = os.getenv(PG_DB, 'bas_manager')
    user = os.getenv(PG_USER, 'bas_manager')
    password = os.getenv(PG_PASSWORD, '123456')
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def get_postgres_engine(echo: bool = False):
    url = build_postgres_url()
    return create_engine(url, echo=echo, pool_pre_ping=True)


def get_sqlite_engine(echo: bool = False):
    path = os.getenv(SQLITE_PATH, './agent.db')
    url = f"sqlite+pysqlite:///{path}"
    return create_engine(url, echo=echo)


def get_session_factory(engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False)


