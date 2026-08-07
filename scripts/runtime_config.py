#!/usr/bin/env python3
import os
from pathlib import Path
import pwd
import sys
import tempfile

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yml"
CONFIG_ERROR = "config/config.yml is missing or invalid"
REQUIRED_TOP_LEVEL_MAPPINGS = (
  "database", "download", "log", "server", "migrate", "platform",
)
REQUIRED_DOUYIN_MAPPINGS = (
  "download", "api", "headers", "login", "post", "live",
)


def _require_mapping(source: dict, key: str, path: str) -> dict:
  value = source.get(key)
  if not isinstance(value, dict):
    raise ValueError(f"{path} must be a mapping")
  return value


def _require_non_empty_string(source: dict, key: str, path: str) -> str:
  value = source.get(key)
  if not isinstance(value, str) or not value.strip():
    raise ValueError(f"{path} must be a non-empty string")
  return value


def _require_port(source: dict, key: str, path: str) -> int:
  value = source.get(key)
  if type(value) is not int or not 1 <= value <= 65535:
    raise ValueError(f"{path} must be an integer from 1 to 65535")
  return value


def load_runtime_config(config_path: Path = CANONICAL_CONFIG_PATH) -> dict:
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("Config root must be a mapping")
  return config


def stage_container_config(
  source_path: Path,
  target_path: Path,
  owner_uid: int,
  owner_gid: int,
) -> None:
  config_text = source_path.read_text(encoding="utf-8")
  config = yaml.safe_load(config_text)
  validate_runtime_config(config)

  descriptor, temporary_name = tempfile.mkstemp(
    prefix=".config.yml.", dir=target_path.parent
  )
  temporary_path = Path(temporary_name)
  try:
    os.fchmod(descriptor, 0o600)
    os.fchown(descriptor, owner_uid, owner_gid)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      descriptor = -1
      output.write(config_text)
    os.replace(temporary_path, target_path)
  finally:
    if descriptor >= 0:
      os.close(descriptor)
    try:
      temporary_path.unlink()
    except FileNotFoundError:
      pass


def drop_privileges_and_exec(username: str, command: list[str]) -> None:
  if not command:
    raise ValueError("Container command is required")
  account = pwd.getpwnam(username)
  os.initgroups(account.pw_name, account.pw_gid)
  os.setgid(account.pw_gid)
  os.setuid(account.pw_uid)
  os.execvp(command[0], command)


def run_container_entrypoint(
  source_path: Path,
  username: str,
  command: list[str],
) -> None:
  account = pwd.getpwnam(username)
  stage_container_config(
    source_path,
    CANONICAL_CONFIG_PATH,
    account.pw_uid,
    account.pw_gid,
  )
  drop_privileges_and_exec(username, command)


def validate_runtime_config(config: dict) -> dict:
  if not isinstance(config, dict):
    raise ValueError("Config root must be a mapping")
  for section in REQUIRED_TOP_LEVEL_MAPPINGS:
    _require_mapping(config, section, f"$.{section}")
  platform = _require_mapping(config, "platform", "$.platform")
  douyin = _require_mapping(platform, "douyin", "$.platform.douyin")
  for section in REQUIRED_DOUYIN_MAPPINGS:
    _require_mapping(douyin, section, f"$.platform.douyin.{section}")

  server = config["server"]
  _require_non_empty_string(server, "host", "$.server.host")
  _require_port(server, "port", "$.server.port")
  if type(server.get("debug_mode")) is not bool:
    raise ValueError("$.server.debug_mode must be a boolean")
  return config


def _dotenv_quote(value: str) -> str:
  if any(character in value for character in ("\0", "\n", "\r")):
    raise ValueError("Compose string values must fit on one line")
  escaped = value.replace("\\", "\\\\").replace("'", "\\'")
  return f"'{escaped}'"


def compose_environment(config: dict) -> dict:
  validate_runtime_config(config)
  database = config["database"]
  return {
    "SMSD_SERVER_PORT": config["server"]["port"],
    "SMSD_DB_PORT": _require_port(database, "port", "$.database.port"),
    "SMSD_DB_NAME": _require_non_empty_string(
      database, "name", "$.database.name"
    ),
    "SMSD_DB_USER": _require_non_empty_string(
      database, "username", "$.database.username"
    ),
    "SMSD_DB_PASSWORD": _require_non_empty_string(
      database, "password", "$.database.password"
    ),
  }


def write_compose_environment(config: dict, output_path: Path) -> None:
  values = compose_environment(config)
  lines = [
    f"SMSD_SERVER_PORT={values['SMSD_SERVER_PORT']}",
    f"SMSD_DB_PORT={values['SMSD_DB_PORT']}",
    f"SMSD_DB_NAME={_dotenv_quote(values['SMSD_DB_NAME'])}",
    f"SMSD_DB_USER={_dotenv_quote(values['SMSD_DB_USER'])}",
    f"SMSD_DB_PASSWORD={_dotenv_quote(values['SMSD_DB_PASSWORD'])}",
  ]
  flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
  descriptor = os.open(str(output_path), flags, 0o600)
  try:
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      descriptor = -1
      output.write("\n".join(lines) + "\n")
  finally:
    if descriptor >= 0:
      os.close(descriptor)


def main(argv=None, config_path: Path = CANONICAL_CONFIG_PATH) -> int:
  arguments = list(sys.argv[1:] if argv is None else argv)
  if arguments == ["validate"]:
    command = "validate"
    output_path = None
  elif arguments == ["server-port"]:
    command = "server-port"
    output_path = None
  elif len(arguments) == 2 and arguments[0] == "compose-env":
    command = "compose-env"
    output_path = Path(arguments[1])
  elif len(arguments) >= 4 and arguments[0] == "container-entrypoint":
    command = "container-entrypoint"
    source_path = Path(arguments[1])
    username = arguments[2]
    container_command = arguments[3:]
    output_path = None
  else:
    print(
      "usage: runtime_config.py validate | server-port | compose-env OUTPUT | "
      "container-entrypoint SOURCE USER COMMAND [ARG ...]",
      file=sys.stderr,
    )
    return 2

  try:
    if command == "container-entrypoint":
      run_container_entrypoint(source_path, username, container_command)
    else:
      config = validate_runtime_config(load_runtime_config(config_path))
    if command == "compose-env":
      write_compose_environment(config, output_path)
    elif command == "server-port":
      print(config["server"]["port"])
  except Exception:
    print(CONFIG_ERROR, file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
