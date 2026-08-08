from collections.abc import Mapping
from typing import Any

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

from backend.src.library.configlib import load_config


def build_database_url(
  config: Mapping[str, Any],
  database_name: str | None = None,
) -> URL:
  database = config["database"]
  return URL.create(
    "mysql+pymysql",
    username=database["username"],
    password=database["password"],
    host=database["host"],
    port=database["port"],
    database=database["name"] if database_name is None else database_name,
    query={"charset": "utf8mb4"},
  )


def create_schema_engine(
  config: Mapping[str, Any] | None = None,
  database_name: str | None = None,
) -> Engine:
  source = load_config() if config is None else config
  return create_engine(
    build_database_url(source, database_name),
    poolclass=NullPool,
    pool_pre_ping=True,
  )
