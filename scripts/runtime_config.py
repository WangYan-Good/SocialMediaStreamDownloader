#!/usr/bin/env python3
import os
from pathlib import Path
import pwd
import secrets
import stat
import sys
import tempfile

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.library.config_contract import (
  ConfigContractError,
  validate_config_contract,
)


CANONICAL_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yml"
CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "docs" / "design" / "config.yml.example"
CONFIG_ERROR = "config/config.yml is missing or invalid"
CONTAINER_INTERNAL_SERVER_HOST = "0.0.0.0"
MYSQL_ROOT_SECRET_PATH = PROJECT_ROOT / "config" / "mysql-root-password"


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
  config = yaml.safe_load(source_path.read_text(encoding="utf-8"))
  validate_runtime_config(config)
  # The mounted configuration keeps the safe loopback default. Inside the
  # isolated Compose network Waitress must listen on the container interface;
  # host exposure remains constrained by docker-compose.yml.
  config["server"]["host"] = CONTAINER_INTERNAL_SERVER_HOST
  staged_text = yaml.safe_dump(
    config, allow_unicode=True, sort_keys=False
  )

  descriptor, temporary_name = tempfile.mkstemp(
    prefix=".config.yml.", dir=target_path.parent
  )
  temporary_path = Path(temporary_name)
  try:
    os.fchmod(descriptor, 0o600)
    os.fchown(descriptor, owner_uid, owner_gid)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      descriptor = -1
      output.write(staged_text)
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
  reference = yaml.safe_load(CONFIG_EXAMPLE_PATH.read_text(encoding="utf-8"))
  validate_config_contract(reference, config)

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


def _read_mysql_root_secret(secret_path: Path) -> str:
  flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
  descriptor = os.open(str(secret_path), flags)
  try:
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode):
      raise ValueError("MySQL root secret must be a regular file")
    os.fchmod(descriptor, 0o600)
    content = os.read(descriptor, 4097)
    if len(content) > 4096:
      raise ValueError("MySQL root secret is invalid")
  finally:
    os.close(descriptor)
  try:
    value = content.decode("utf-8").rstrip("\n")
  except UnicodeDecodeError as error:
    raise ValueError("MySQL root secret is invalid") from error
  if not value or "\n" in value or "\r" in value or "\0" in value:
    raise ValueError("MySQL root secret is invalid")
  return value


def ensure_mysql_root_secret(
  secret_path: Path,
  application_password: str,
  token_factory=None,
) -> str:
  secret_path = Path(secret_path)
  token_factory = token_factory or (lambda: secrets.token_urlsafe(32))
  secret_path.parent.mkdir(parents=True, exist_ok=True)

  try:
    value = _read_mysql_root_secret(secret_path)
  except FileNotFoundError:
    for _ in range(8):
      value = token_factory()
      if value and value != application_password:
        break
    else:
      raise ValueError("MySQL root secret must be distinct")

    descriptor, temporary_name = tempfile.mkstemp(
      prefix=".mysql-root-password.", dir=secret_path.parent
    )
    temporary_path = Path(temporary_name)
    try:
      os.fchmod(descriptor, 0o600)
      with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        descriptor = -1
        output.write(value + "\n")
        output.flush()
        os.fsync(output.fileno())
      try:
        os.link(temporary_path, secret_path)
      except FileExistsError:
        value = _read_mysql_root_secret(secret_path)
      else:
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        directory_flags |= getattr(os, "O_CLOEXEC", 0)
        directory_descriptor = os.open(str(secret_path.parent), directory_flags)
        try:
          os.fsync(directory_descriptor)
        finally:
          os.close(directory_descriptor)
    finally:
      if descriptor >= 0:
        os.close(descriptor)
      try:
        temporary_path.unlink()
      except FileNotFoundError:
        pass

  if value == application_password:
    raise ValueError("MySQL root secret must be distinct from application password")
  return value


def compose_environment(
  config: dict,
  root_secret_path: Path = MYSQL_ROOT_SECRET_PATH,
  config_path: Path = CANONICAL_CONFIG_PATH,
) -> dict:
  validate_runtime_config(config)
  database = config["database"]
  if _require_non_empty_string(
    database, "host", "$.database.host"
  ) != "mysql":
    raise ValueError("$.database.host must be mysql for Docker Compose")
  return {
    "SMSD_SERVER_PORT": config["server"]["port"],
    "SMSD_DB_NAME": _require_non_empty_string(
      database, "name", "$.database.name"
    ),
    "SMSD_DB_USER": _require_non_empty_string(
      database, "username", "$.database.username"
    ),
    "SMSD_DB_PASSWORD": _require_non_empty_string(
      database, "password", "$.database.password"
    ),
    "SMSD_CONFIG_FILE": str(Path(config_path).resolve()),
    "SMSD_MYSQL_ROOT_SECRET_FILE": str(Path(root_secret_path).resolve()),
  }


def write_compose_environment(
  config: dict,
  output_path: Path,
  root_secret_path: Path = MYSQL_ROOT_SECRET_PATH,
  config_path: Path = CANONICAL_CONFIG_PATH,
) -> None:
  values = compose_environment(config, root_secret_path, config_path)
  lines = [
    f"SMSD_SERVER_PORT={values['SMSD_SERVER_PORT']}",
    f"SMSD_DB_NAME={_dotenv_quote(values['SMSD_DB_NAME'])}",
    f"SMSD_DB_USER={_dotenv_quote(values['SMSD_DB_USER'])}",
    f"SMSD_DB_PASSWORD={_dotenv_quote(values['SMSD_DB_PASSWORD'])}",
    f"SMSD_CONFIG_FILE={_dotenv_quote(values['SMSD_CONFIG_FILE'])}",
    "SMSD_MYSQL_ROOT_SECRET_FILE="
    f"{_dotenv_quote(values['SMSD_MYSQL_ROOT_SECRET_FILE'])}",
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
  elif len(arguments) == 2 and arguments[0] == "ensure-root-secret":
    command = "ensure-root-secret"
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
      "ensure-root-secret PATH | "
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
      write_compose_environment(
        config,
        output_path,
        MYSQL_ROOT_SECRET_PATH,
        config_path,
      )
    elif command == "ensure-root-secret":
      application_password = _require_non_empty_string(
        config["database"], "password", "$.database.password"
      )
      ensure_mysql_root_secret(output_path, application_password)
    elif command == "server-port":
      print(config["server"]["port"])
  except ConfigContractError as error:
    print(f"{CONFIG_ERROR}: {', '.join(error.issues)}", file=sys.stderr)
    return 1
  except Exception:
    print(CONFIG_ERROR, file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
