from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
import re
from typing import Any, Literal

from alembic import command
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from backend.src.database.migration import make_alembic_config
from backend.src.database.orm.engine import create_schema_engine
from backend.src.database.orm.models import MANAGED_TABLE_NAMES
from backend.src.database.schema_compare import SchemaReport, compare_managed_schema
from backend.src.library.configlib import load_config


DISPOSABLE_DATABASE_PATTERN = re.compile(r"^smsd_migration_test_[0-9a-f]{12}$")


class MigrationError(RuntimeError):
  pass


class DatabaseUnavailable(MigrationError):
  def __init__(
    self,
    message: str = "database unavailable",
    *,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
  ):
    super().__init__(message)
    self.host = host
    self.port = port
    self.database = database

  def safe_location(self) -> str:
    values = (
      ("host", self.host),
      ("port", self.port),
      ("database", self.database),
    )
    return " ".join(f"{key}={value}" for key, value in values if value is not None)


class SchemaMismatchError(MigrationError):
  def __init__(self, report: SchemaReport):
    super().__init__("managed database schema is incompatible")
    self.report = report


class RevisionStateError(MigrationError):
  pass


class MigrationFailed(MigrationError):
  pass


@dataclass(frozen=True)
class MigrationStatus:
  current: str | None
  heads: tuple[str, ...]
  relation: Literal[
    "ready",
    "unversioned",
    "behind",
    "ahead_or_unknown",
    "diverged",
  ]
  schema_compatible: bool | None = None

  @property
  def classification(self) -> str:
    if len(self.heads) != 1:
      return "multiple_heads"
    if self.relation != "ready":
      return self.relation
    if self.schema_compatible is True:
      return "ready"
    return "schema_drift"


class MigrationService:
  def __init__(
    self,
    config: Mapping[str, Any] | None = None,
    *,
    database_name: str | None = None,
    engine_factory: Callable[..., Any] = create_schema_engine,
    compare_schema: Callable[..., SchemaReport] = compare_managed_schema,
    commands=command,
    current_revision_reader: Callable[[Any], str | tuple[str, ...] | None] | None = None,
  ):
    self.config                  = config
    self.database_name           = database_name
    self.engine_factory          = engine_factory
    self.compare_schema          = compare_schema
    self.commands                = commands
    self.current_revision_reader = current_revision_reader

  def _new_engine(self):
    return self.engine_factory(self.config, self.database_name)

  def _database_unavailable(self) -> DatabaseUnavailable:
    source = load_config() if self.config is None else self.config
    database = source.get("database", {})
    return DatabaseUnavailable(
      host=database.get("host"),
      port=database.get("port"),
      database=self.database_name or database.get("name"),
    )

  @contextmanager
  def _engine(self):
    try:
      engine = self._new_engine()
    except SQLAlchemyError as exc:
      raise self._database_unavailable() from exc
    try:
      yield engine
    except (SchemaMismatchError, RevisionStateError):
      raise
    except CommandError as exc:
      raise RevisionStateError("migration revision state is invalid") from exc
    except SQLAlchemyError as exc:
      raise self._database_unavailable() from exc
    finally:
      engine.dispose()

  def _alembic_config(self, engine=None):
    config = make_alembic_config(self.config, self.database_name)
    if engine is not None:
      config.attributes["engine"] = engine
    return config

  def _scripts(self):
    return ScriptDirectory.from_config(self._alembic_config())

  def _heads(self) -> tuple[str, ...]:
    return tuple(self._scripts().get_heads())

  def _current_revisions(self, engine) -> tuple[str, ...]:
    if self.current_revision_reader is not None:
      revisions = self.current_revision_reader(engine)
    else:
      with engine.connect() as connection:
        revisions = MigrationContext.configure(connection).get_current_heads()
    if revisions is None:
      return ()
    if isinstance(revisions, str):
      return (revisions,)
    return tuple(sorted(revisions))

  def _configured_database_name(self) -> str:
    if self.database_name is not None:
      return self.database_name
    source = load_config() if self.config is None else self.config
    return str(source["database"]["name"])

  @staticmethod
  def _relation(current: str | None, heads: tuple[str, ...], scripts) -> str:
    if len(heads) != 1:
      return "diverged"
    head = heads[0]
    if current is None:
      return "unversioned"
    if current == head:
      return "ready"
    try:
      current_revision = scripts.get_revision(current)
    except CommandError:
      return "ahead_or_unknown"
    if current_revision is None:
      return "ahead_or_unknown"
    pending = [scripts.get_revision(head)]
    seen = set()
    while pending:
      revision = pending.pop()
      if revision is None or revision.revision in seen:
        continue
      seen.add(revision.revision)
      if revision.revision == current:
        return "behind"
      pending.extend(scripts.get_revisions(revision.down_revision or ()))
    return "diverged"

  def check(self) -> SchemaReport:
    with self._engine() as engine:
      return self.compare_schema(engine)

  def status(self) -> MigrationStatus:
    with self._engine() as engine:
      scripts = self._scripts()
      heads = tuple(scripts.get_heads())
      current_revisions = self._current_revisions(engine)
      if len(current_revisions) > 1:
        current = ",".join(current_revisions)
        relation = "diverged"
      else:
        current = current_revisions[0] if current_revisions else None
        relation = self._relation(current, heads, scripts)
      report = self.compare_schema(engine)
      return MigrationStatus(
        current=current,
        heads=heads,
        relation=relation,
        schema_compatible=report.is_compatible,
      )

  def stamp(
    self,
    revision: str | None = None,
    *,
    confirm_database: str | None = None,
  ) -> None:
    """Record an existing database's revision without running any DDL.

    Stamping the head is validated: the managed schema must already match the ORM
    metadata, so the recorded revision cannot be a lie.

    Stamping an *older* revision cannot be validated that way, because the schema
    comparison only knows the current metadata.  A pre-baseline database that
    predates later migrations still needs a way in, so an explicit older target is
    accepted as an operator assertion and guarded exactly like ``downgrade``: the
    real database name must be repeated back.  The follow-up ``upgrade`` then
    applies the remaining revisions normally.
    """
    heads = self._heads()
    if len(heads) != 1:
      raise RevisionStateError("stamp requires exactly one migration head")
    target = heads[0] if revision is None or not revision.strip() else revision.strip()

    if target not in {item.revision for item in self._scripts().walk_revisions()}:
      raise RevisionStateError("stamp requires a known revision")

    if target != heads[0]:
      database_name = self._configured_database_name()
      if confirm_database != database_name:
        raise RevisionStateError(
          "stamping a non-head revision requires exact --confirm-database confirmation"
        )

    with self._engine() as engine:
      if target == heads[0]:
        report = self.compare_schema(engine)
        if not report.is_compatible:
          raise SchemaMismatchError(report)
      if self._current_revisions(engine):
        raise RevisionStateError("database is already versioned")
      try:
        self.commands.stamp(self._alembic_config(engine), target)
      except SQLAlchemyError:
        raise
      except Exception as exc:
        raise MigrationFailed("migration stamp failed") from exc

  def upgrade(self, target: str = "head") -> None:
    if not target or not target.strip():
      raise RevisionStateError("upgrade target must not be empty")
    heads = self._heads()
    if len(heads) != 1:
      raise RevisionStateError("upgrade requires exactly one migration head")
    with self._engine() as engine:
      current_revisions = self._current_revisions(engine)
      if len(current_revisions) > 1:
        raise RevisionStateError("upgrade refuses multiple database revisions")
      if not current_revisions:
        existing_managed_tables = (
          set(inspect(engine).get_table_names()) & set(MANAGED_TABLE_NAMES)
        )
        if existing_managed_tables:
          raise RevisionStateError(
            "unversioned database contains managed tables; run check then stamp"
          )
      try:
        self.commands.upgrade(self._alembic_config(engine), target)
      except SQLAlchemyError:
        raise
      except Exception as exc:
        raise MigrationFailed("migration upgrade failed") from exc

  def downgrade(self, target: str, *, confirm_database: str | None = None) -> None:
    if not target or not target.strip():
      raise RevisionStateError("downgrade requires an explicit revision")
    database_name = self._configured_database_name()
    is_disposable = (
      self.database_name is not None
      and DISPOSABLE_DATABASE_PATTERN.fullmatch(database_name) is not None
    )
    if target.strip() == "base" and not is_disposable:
      raise RevisionStateError(
        "baseline downgrade is restricted to disposable migration test databases"
      )
    if not is_disposable and confirm_database != database_name:
      raise RevisionStateError(
        "downgrade requires exact --confirm-database confirmation"
      )
    with self._engine() as engine:
      if not is_disposable:
        current_revisions = self._current_revisions(engine)
        if len(current_revisions) > 1:
          raise RevisionStateError("downgrade refuses multiple database revisions")
        current = current_revisions[0] if current_revisions else None
        steps = self._scripts()._downgrade_revs(target, current)
        if any(step.revision.down_revision is None for step in steps):
          raise RevisionStateError(
            "baseline downgrade is restricted to disposable migration test databases"
          )
      try:
        self.commands.downgrade(self._alembic_config(engine), target)
      except SQLAlchemyError:
        raise
      except Exception as exc:
        raise MigrationFailed("migration downgrade failed") from exc

  def revision(self, message: str) -> None:
    if not message or not message.strip():
      raise RevisionStateError("revision requires a non-empty message")
    with self._engine() as engine:
      try:
        self.commands.revision(
          self._alembic_config(engine),
          message=message.strip(),
          autogenerate=True,
        )
      except SQLAlchemyError:
        raise
      except Exception as exc:
        raise MigrationFailed("migration revision generation failed") from exc


__all__ = [
  "DatabaseUnavailable",
  "MigrationFailed",
  "MigrationService",
  "MigrationStatus",
  "RevisionStateError",
  "SchemaMismatchError",
]
