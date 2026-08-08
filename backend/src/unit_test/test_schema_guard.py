import unittest

from backend.src.database.migration_service import DatabaseUnavailable, MigrationStatus


class FakeClock:
  def __init__(self):
    self.now = 0.0

  def __call__(self):
    return self.now

  def advance(self, seconds):
    self.now += seconds


class SequencedProbe:
  def __init__(self, values):
    self.values = list(values)
    self.calls = 0

  def __call__(self):
    self.calls += 1
    value = self.values.pop(0)
    if isinstance(value, Exception):
      raise value
    return value


def status(*, relation="ready", compatible=True):
  return MigrationStatus(
    current="0001_initial_schema",
    heads=("0001_initial_schema",),
    relation=relation,
    schema_compatible=compatible,
  )


class SchemaGuardTest(unittest.TestCase):
  def load_api(self):
    try:
      from backend.src.database.schema_guard import (
        DatabaseSchemaGuard,
        DatabaseWriteBlocked,
        SchemaState,
      )
    except ModuleNotFoundError as exc:
      raise AssertionError("schema guard is not implemented") from exc
    return DatabaseSchemaGuard, DatabaseWriteBlocked, SchemaState

  def test_unavailable_database_retries_then_becomes_ready(self):
    DatabaseSchemaGuard, _, SchemaState = self.load_api()
    clock = FakeClock()
    probe = SequencedProbe([
      DatabaseUnavailable("credential-marker"),
      status(),
    ])
    guard = DatabaseSchemaGuard(probe=probe, clock=clock, retry_seconds=5)

    self.assertEqual(SchemaState.UNAVAILABLE, guard.refresh().state)
    self.assertEqual(SchemaState.UNAVAILABLE, guard.refresh().state)
    self.assertEqual(1, probe.calls)
    clock.advance(5)
    self.assertEqual(SchemaState.READY, guard.refresh().state)
    self.assertEqual(2, probe.calls)

  def test_schema_drift_blocks_writes(self):
    DatabaseSchemaGuard, DatabaseWriteBlocked, SchemaState = self.load_api()
    guard = DatabaseSchemaGuard(
      probe=lambda: status(compatible=False),
      clock=FakeClock(),
      retry_seconds=5,
    )

    self.assertEqual(SchemaState.BLOCKED, guard.refresh().state)
    with self.assertRaises(DatabaseWriteBlocked):
      guard.require_write_ready()

  def test_ready_and_disabled_states_have_explicit_write_behavior(self):
    DatabaseSchemaGuard, DatabaseWriteBlocked, SchemaState = self.load_api()
    ready = DatabaseSchemaGuard(
      probe=lambda: status(), clock=FakeClock(), retry_seconds=5
    )
    self.assertEqual(SchemaState.READY, ready.refresh().state)
    ready.require_write_ready()

    disabled = DatabaseSchemaGuard.disabled(clock=FakeClock())
    self.assertEqual(SchemaState.DISABLED, disabled.refresh().state)
    with self.assertRaises(DatabaseWriteBlocked):
      disabled.require_write_ready()

  def test_process_guard_installation_is_replaceable_for_tests(self):
    DatabaseSchemaGuard, _, _ = self.load_api()
    from backend.src.database.schema_guard import get_schema_guard, install_schema_guard

    guard = DatabaseSchemaGuard.disabled(clock=FakeClock())
    install_schema_guard(guard)
    self.assertIs(guard, get_schema_guard())
    install_schema_guard(None)
    self.assertIsNone(get_schema_guard())


if __name__ == "__main__":
  unittest.main()
