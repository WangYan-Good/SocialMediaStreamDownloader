from dataclasses import dataclass
from enum import Enum
from threading import Lock
import time

from backend.src.database.migration_service import (
  DatabaseUnavailable,
  MigrationService,
  MigrationStatus,
)


class SchemaState(str, Enum):
  READY = "ready"
  UNAVAILABLE = "unavailable"
  BLOCKED = "blocked"
  DISABLED = "disabled"


@dataclass(frozen=True)
class GuardSnapshot:
  state: SchemaState
  reason: str
  checked_at: float


class DatabaseWriteBlocked(RuntimeError):
  pass


class RuntimeSchemaMutationBlocked(DatabaseWriteBlocked):
  pass


class DatabaseSchemaGuard:
  def __init__(
    self,
    probe,
    *,
    clock=time.monotonic,
    retry_seconds: float = 30.0,
    disabled: bool = False,
  ):
    self.probe = probe
    self.clock = clock
    self.retry_seconds = retry_seconds
    self._disabled = disabled
    self._snapshot: GuardSnapshot | None = None
    self._lock = Lock()

  @classmethod
  def disabled(cls, *, clock=time.monotonic):
    return cls(None, clock=clock, retry_seconds=float("inf"), disabled=True)

  def refresh(self, force: bool = False) -> GuardSnapshot:
    now = self.clock()
    with self._lock:
      if self._disabled:
        if self._snapshot is None:
          self._snapshot = GuardSnapshot(
            SchemaState.DISABLED,
            "database persistence is disabled",
            now,
          )
        return self._snapshot
      if (
        not force
        and self._snapshot is not None
        and now - self._snapshot.checked_at < self.retry_seconds
      ):
        return self._snapshot
      try:
        status: MigrationStatus = self.probe()
        if status.classification == "ready":
          snapshot = GuardSnapshot(SchemaState.READY, "schema is ready", now)
        else:
          snapshot = GuardSnapshot(
            SchemaState.BLOCKED,
            f"schema state is {status.classification}",
            now,
          )
      except DatabaseUnavailable:
        snapshot = GuardSnapshot(
          SchemaState.UNAVAILABLE,
          "database unavailable",
          now,
        )
      except Exception:
        snapshot = GuardSnapshot(
          SchemaState.UNAVAILABLE,
          "schema status check failed",
          now,
        )
      self._snapshot = snapshot
      return snapshot

  @property
  def snapshot(self) -> GuardSnapshot | None:
    with self._lock:
      return self._snapshot

  def require_write_ready(self) -> None:
    snapshot = self.refresh()
    if snapshot.state is not SchemaState.READY:
      raise DatabaseWriteBlocked(snapshot.reason)


_installed_guard: DatabaseSchemaGuard | None = None
_installed_guard_lock = Lock()


def install_schema_guard(guard: DatabaseSchemaGuard | None) -> None:
  global _installed_guard
  with _installed_guard_lock:
    _installed_guard = guard


def get_schema_guard() -> DatabaseSchemaGuard | None:
  with _installed_guard_lock:
    return _installed_guard


def require_database_write_ready() -> None:
  guard = get_schema_guard()
  if guard is not None:
    guard.require_write_ready()


def require_runtime_schema_mutation_allowed() -> None:
  if get_schema_guard() is not None:
    raise RuntimeSchemaMutationBlocked(
      "runtime schema creation and deletion must use Alembic"
    )


def initialize_schema_guard(config: dict) -> DatabaseSchemaGuard:
  database = config.get("database")
  if not isinstance(database, dict):
    guard = DatabaseSchemaGuard.disabled()
  elif database.get("enable") is not True:
    guard = DatabaseSchemaGuard.disabled()
  else:
    service = MigrationService(config=config)
    guard = DatabaseSchemaGuard(probe=service.status)
  install_schema_guard(guard)
  guard.refresh(force=True)
  return guard


__all__ = [
  "DatabaseSchemaGuard",
  "DatabaseUnavailable",
  "DatabaseWriteBlocked",
  "GuardSnapshot",
  "RuntimeSchemaMutationBlocked",
  "SchemaState",
  "get_schema_guard",
  "initialize_schema_guard",
  "install_schema_guard",
  "require_database_write_ready",
  "require_runtime_schema_mutation_allowed",
]
