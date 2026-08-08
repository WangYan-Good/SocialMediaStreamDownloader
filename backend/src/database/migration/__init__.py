from collections.abc import Mapping
from pathlib import Path
from typing import Any

from alembic.config import Config

from backend.src.library.configlib import load_config


def make_alembic_config(
  config: Mapping[str, Any] | None = None,
  database_name: str | None = None,
) -> Config:
  source = load_config() if config is None else config
  alembic_config = Config()
  alembic_config.set_main_option(
    "script_location",
    str(Path(__file__).resolve().parent),
  )
  alembic_config.attributes["smsd_config"] = source
  alembic_config.attributes["database_name"] = database_name
  return alembic_config


__all__ = ["make_alembic_config"]
