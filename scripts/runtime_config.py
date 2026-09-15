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


import re

CANONICAL_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yml"
CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "docs" / "design" / "config.yml.example"
CONFIG_ERROR = "config/config.yml is missing or invalid"
CONTAINER_INTERNAL_SERVER_HOST = "0.0.0.0"
MYSQL_ROOT_SECRET_PATH = PROJECT_ROOT / "config" / "mysql-root-password"

##
## The Compose service name, which is exactly what an external deployment must
## never be pointed at: inside Compose it is a service, and outside it is
## either nothing or somebody else's host entirely.
##
COMPOSE_DATABASE_HOST = "mysql"

##
## What may be used as a database address.
##
## Deliberately narrow, and enforced rather than trusted, because this value
## reaches the container as an environment string and is then written into a
## YAML document. A value carrying a newline would stop being an address and
## start being additional configuration.
##
_DATABASE_HOST = re.compile(r"[A-Za-z0-9]([A-Za-z0-9._-]{0,251}[A-Za-z0-9])?\Z")


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


def require_database_host(value) -> str:
  """Return ``value`` if it can be a database address, or refuse it.

  The address is not a secret and may travel as an environment value, which is
  precisely why it is checked here: an unchecked string is written verbatim
  into the staged YAML document, and a newline would make it a second setting
  rather than a hostname.
  """
  if not isinstance(value, str) or _DATABASE_HOST.fullmatch(value) is None:
    raise ValueError("$.database.host override must be a hostname or address")
  return value


##
## What may be used as a database name.
##
## Narrower than MySQL would accept, on purpose. This value is interpolated into
## a backquoted SQL identifier and into a ``mysqldump`` argument, and the
## release path has no use for a name that needs either of those to be careful.
##
_DATABASE_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_$-]{0,63}\Z")


def require_configured_database_name(config: dict, declared=None) -> str:
  """Return the database the canonical configuration names.

  The configuration is the authority, and this is the only place a release
  command may learn which database it is working on. Before this existed the
  backup asked the migration CLI about the configured database and then dumped
  whichever database an operator had typed on the command line - two different
  questions that looked like one answer. A bundle produced that way carries a
  schema status describing one database and rows from another, and nothing
  downstream can tell.

  ``declared`` is what an operator wrote, when they wrote anything. It is
  allowed to exist because naming the target out loud is worth something on a
  destructive path, but it is never allowed to *decide* anything: it either
  equals the configured name or the command refuses.
  """
  database = config.get("database")
  if not isinstance(database, dict):
    raise ValueError("$.database must be a mapping")
  name = _require_non_empty_string(database, "name", "$.database.name")
  if _DATABASE_NAME.fullmatch(name) is None:
    raise ValueError("$.database.name is not a plain database identifier")
  if declared is not None and declared != name:
    ##
    ## Deliberately without either value. This message reaches a terminal and a
    ## ticket, and a production database name is not something to scatter.
    ##
    raise ValueError(
      "the requested database is not the one the configuration names"
    )
  return name


def stage_container_config(
  source_path: Path,
  target_path: Path,
  owner_uid: int,
  owner_gid: int,
  database_host: str | None = None,
) -> None:
  config = yaml.safe_load(source_path.read_text(encoding="utf-8"))
  validate_runtime_config(config)
  # The mounted configuration keeps the safe loopback default. Inside the
  # isolated Compose network Waitress must listen on the container interface;
  # host exposure remains constrained by docker-compose.yml.
  config["server"]["host"] = CONTAINER_INTERNAL_SERVER_HOST
  ##
  ## External-host deployments only.
  ##
  ## Production's canonical file says ``localhost`` and must keep saying it -
  ## the bare-metal writer reads that same file until the moment it is stopped,
  ## so rewriting it would break the running production before its replacement
  ## was proven. Inside a container ``localhost`` is the container, so the
  ## address is corrected *here*, on the staged copy, and nowhere else.
  ##
  ## Only the address moves. The password stays in the mounted file, because an
  ## address in an environment variable is a fact about the network and a
  ## password in one is a credential in every ``inspect`` and every crash dump.
  ##
  if database_host is not None:
    config["database"]["host"] = require_database_host(database_host)
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


##
## The environment value an external-host deployment sets, and the only one it
## may set.
##
## A database *address* is a fact about the network: it appears in ``inspect``
## output, in a process listing and in a crash dump, and none of that is a
## disclosure. A database *password* in the same place would be, which is why
## there is no companion variable for one - the credential stays in the mounted
## file and is read only by the staging step below.
##
CONTAINER_DATABASE_HOST_VARIABLE = "SMSD_DB_HOST"


def run_container_entrypoint(
  source_path: Path,
  username: str,
  command: list[str],
) -> None:
  account = pwd.getpwnam(username)
  ##
  ## Absent for a Compose deployment, which wants the file exactly as mounted.
  ## Present for an external-host one, where the canonical ``localhost`` means
  ## the container itself and has to be corrected on the staged copy.
  ##
  database_host = os.environ.get(CONTAINER_DATABASE_HOST_VARIABLE)
  if database_host is not None:
    ##
    ## Checked before anything is written. A container that refused to start is
    ## a deployment that failed; a container that started against an address
    ## somebody injected is a deployment that succeeded at the wrong thing.
    ##
    require_database_host(database_host)
  stage_container_config(
    source_path,
    CANONICAL_CONFIG_PATH,
    account.pw_uid,
    account.pw_gid,
    database_host=database_host,
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


##
## The other topology, stated separately on purpose.
##
## ``compose_environment`` describes a stack that brings its own database and
## keeps media in a named volume. This describes the one this project actually
## runs in production: an application container against a MySQL that already
## exists on the host, and a media tree at a real path that is bind-mounted
## rather than copied.
##
## The two are not a flag apart. They disagree about where the database is,
## what may be created, and what a rollback means, and expressing that as
## conditionals inside one function is how one topology's guard quietly stops
## protecting the other. So each keeps its own refusal: Compose refuses any
## database host but ``mysql``, and this refuses exactly that one.
##
## Deliberately returns no password. Compose needs it because Compose *creates*
## the database user; an external deployment connects to a user somebody else
## already made, so the credential never has to leave the configuration file.
##
def external_environment(
  config: dict,
  config_path: Path = CANONICAL_CONFIG_PATH,
) -> dict:
  validate_runtime_config(config)
  database = config["database"]
  host = _require_non_empty_string(database, "host", "$.database.host")
  if host == COMPOSE_DATABASE_HOST:
    raise ValueError(
      "$.database.host must not be the Compose service name for an "
      "external-host deployment"
    )
  require_database_host(host)

  download = config.get("download")
  if not isinstance(download, dict):
    raise ValueError("$.download must be a mapping")
  media_root = _require_non_empty_string(
    download, "save_path", "$.download.save_path"
  )
  ##
  ## An absolute path, because it is about to become a bind-mount source and a
  ## relative one would be resolved against whatever directory the deployment
  ## happened to run from.
  ##
  if not media_root.startswith("/"):
    raise ValueError("$.download.save_path must be an absolute path")
  normalised = str(Path(media_root))
  if normalised == "/":
    raise ValueError("$.download.save_path must not be the filesystem root")

  return {
    "SMSD_SERVER_PORT": config["server"]["port"],
    "SMSD_DB_HOST": host,
    "SMSD_DB_NAME": _require_non_empty_string(
      database, "name", "$.database.name"
    ),
    "SMSD_MEDIA_ROOT": normalised,
    "SMSD_CONFIG_FILE": str(Path(config_path).resolve()),
  }


##
## Refuse a configuration file anybody but its owner can read.
##
## The file holds the database password. Production's copy is ``0644`` today,
## and a deployment tool that read it anyway would be treating "this mistake
## has already been made" as permission to keep making it.
##
## Not repaired here, deliberately. A deployment script that quietly widened or
## narrowed the permissions of an operator's file would be changing production
## state as a side effect of a check; fixing the mode is a decision an operator
## makes, and this only refuses to proceed until they have.
##
def _require_private_file(path: Path, description: str, max_bytes=None) -> Path:
  path = Path(path)
  ##
  ## ``lstat``: the mode of a link says nothing about the mode of its target,
  ## and a link at this name is somebody choosing which file gets read.
  ##
  info = path.lstat()
  if stat.S_ISLNK(info.st_mode):
    raise ValueError(f"the {description} must not be a symbolic link")
  if not stat.S_ISREG(info.st_mode):
    raise ValueError(f"the {description} must be a regular file")
  if stat.S_IMODE(info.st_mode) & 0o077:
    raise ValueError(
      f"the {description} holds the database password and must not be "
      "readable by group or other"
    )
  if max_bytes is not None and info.st_size > max_bytes:
    raise ValueError(f"the {description} is larger than one can be")
  return path


def require_private_config(path: Path) -> Path:
  return _require_private_file(path, "configuration file")


##
## An option file is a handful of lines. Anything larger is not one, and reading
## it unbounded is how a single planted file becomes an outage.
##
MYSQL_OPTION_FILE_MAX_BYTES = 8192


def require_private_option_file(path: Path) -> Path:
  return _require_private_file(
    path, "MySQL option file", MYSQL_OPTION_FILE_MAX_BYTES
  )


##
## >>================== the external client credential ==================>>
##
##
## Getting a password to ``mysqldump`` without leaving it anywhere it survives.
##
## The Compose backup never faces this: the credential is a Docker secret read
## inside the container by a shell that already has it mounted. An external
## backup runs against a MySQL on the host, and every obvious route is wrong.
## ``-pSECRET`` puts it in argv, which is world-readable in ``/proc`` for as long
## as the dump runs - and a dump of this database runs for a while. ``MYSQL_PWD``
## puts it in the environment, readable by anything that can read the process and
## inherited by every child. A heredoc puts it wherever the shell was traced.
##
## An option file is what is left: the *path* travels in argv and the secret
## stays in a 0600 file that the caller removes. The format has quoting rules,
## and a password containing ``#`` silently becomes a comment if they are
## ignored, so every value is quoted and escaped rather than interpolated.
##
_MYSQL_OPTION_ESCAPES = {
  "\\": "\\\\",
  '"': '\\"',
  "\t": "\\t",
  "\n": "\\n",
  "\r": "\\r",
  ##
  ## Spaces are escaped everywhere rather than only at the edges: the client
  ## strips unquoted trailing whitespace, and ``\s`` removes the question.
  ##
  " ": "\\s",
}


def _quote_mysql_option_value(value: str) -> str:
  escaped = "".join(_MYSQL_OPTION_ESCAPES.get(character, character)
                    for character in value)
  return '"' + escaped + '"'


##
## Written to every group a release client actually reads, so one file serves
## the dump and the restore without either having to know about the other.
##
_MYSQL_OPTION_GROUPS = ("client", "mysql", "mysqldump")


def write_mysql_option_file(config: dict, output_path: Path) -> Path:
  database = config["database"]
  values = {
    "user": _require_non_empty_string(database, "username", "$.database.username"),
    "password": _require_non_empty_string(
      database, "password", "$.database.password"
    ),
    "host": _require_non_empty_string(database, "host", "$.database.host"),
  }
  port = database.get("port")
  if type(port) is int:
    values["port"] = str(port)

  lines = []
  for group in _MYSQL_OPTION_GROUPS:
    lines.append("[{}]".format(group))
    for key, value in values.items():
      lines.append("{}={}".format(key, _quote_mysql_option_value(value)))
    lines.append("")
  document = "\n".join(lines)

  output_path = Path(output_path)
  ##
  ## Created through a private temporary and renamed into place, so the final
  ## name never exists with a wider mode - which is exactly the window a
  ## write-then-chmod would leave open.
  ##
  descriptor, temporary_name = tempfile.mkstemp(
    prefix=".my.cnf.", dir=output_path.parent
  )
  temporary_path = Path(temporary_name)
  try:
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
      descriptor = -1
      stream.write(document)
    os.replace(temporary_path, output_path)
  finally:
    if descriptor >= 0:
      os.close(descriptor)
    try:
      temporary_path.unlink()
    except FileNotFoundError:
      pass
  return output_path


##
## MySQL honours ``--defaults-extra-file`` only when it is the first argument.
## Anywhere else it is read as an unknown option and the client falls back to
## whatever other configuration it can find, which is how a backup silently
## connects as the wrong user. Returned as a list so a caller cannot reorder it
## by accident.
##
def mysql_credential_arguments(option_file: Path) -> list[str]:
  require_private_option_file(option_file)
  return ["--defaults-extra-file={}".format(Path(option_file))]


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
