import unittest
from unittest.mock import Mock, patch

from backend.src.database.schema_compare import SchemaReport


def unified_config():
  return {
    "database": {
      "host": "db.internal",
      "port": 3306,
      "username": "smsd",
      "password": "credential-marker",
      "name": "smsd",
    }
  }


class FakeEngine:
  def __init__(self):
    self.disposed = False

  def dispose(self):
    self.disposed = True


class MigrationServiceTest(unittest.TestCase):
  def load_api(self):
    try:
      from backend.src.database.migration_service import (
        MigrationService,
        MigrationStatus,
        RevisionStateError,
        SchemaMismatchError,
      )
    except ModuleNotFoundError as exc:
      raise AssertionError("migration service is not implemented") from exc
    return MigrationService, MigrationStatus, RevisionStateError, SchemaMismatchError

  def test_status_classification_covers_safe_states(self):
    _, MigrationStatus, _, _ = self.load_api()

    self.assertEqual(
      "unversioned",
      MigrationStatus(None, ("0001_initial_schema",), "unversioned").classification,
    )
    self.assertEqual(
      "ready",
      MigrationStatus(
        "0001_initial_schema",
        ("0001_initial_schema",),
        "ready",
        schema_compatible=True,
      ).classification,
    )
    self.assertEqual(
      "schema_drift",
      MigrationStatus(
        "0001_initial_schema",
        ("0001_initial_schema",),
        "ready",
        schema_compatible=False,
      ).classification,
    )
    self.assertEqual(
      "multiple_heads",
      MigrationStatus(None, ("a", "b"), "diverged").classification,
    )
    self.assertEqual(
      "behind",
      MigrationStatus("0000", ("0001",), "behind").classification,
    )
    self.assertEqual(
      "ahead_or_unknown",
      MigrationStatus("future", ("0001",), "ahead_or_unknown").classification,
    )

  def test_stamp_refuses_incompatible_schema_and_disposes_engine(self):
    MigrationService, _, _, SchemaMismatchError = self.load_api()
    engine = FakeEngine()
    commands = Mock()
    service = MigrationService(
      config=unified_config(),
      engine_factory=lambda *args, **kwargs: engine,
      compare_schema=lambda unused: SchemaReport.with_error(
        "room_base", "column", "missing id"
      ),
      commands=commands,
      current_revision_reader=lambda unused: None,
    )

    with self.assertRaises(SchemaMismatchError):
      service.stamp()

    commands.stamp.assert_not_called()
    self.assertTrue(engine.disposed)

  def test_stamp_requires_unversioned_database_and_invokes_head(self):
    MigrationService, _, RevisionStateError, _ = self.load_api()
    commands = Mock()
    versioned = MigrationService(
      config=unified_config(),
      engine_factory=lambda *args, **kwargs: FakeEngine(),
      compare_schema=lambda unused: SchemaReport(),
      commands=commands,
      current_revision_reader=lambda unused: "0001_initial_schema",
    )
    with self.assertRaises(RevisionStateError):
      versioned.stamp()

    engine = FakeEngine()
    unversioned = MigrationService(
      config=unified_config(),
      engine_factory=lambda *args, **kwargs: engine,
      compare_schema=lambda unused: SchemaReport(),
      commands=commands,
      current_revision_reader=lambda unused: None,
    )
    unversioned.stamp()

    alembic_config, target = commands.stamp.call_args.args
    ##
    ## stamp records the single head, whatever it currently is; hardcoding a
    ## revision here would break on every new migration.
    ##
    self.assertEqual(unversioned._heads()[0], target)
    self.assertIs(engine, alembic_config.attributes["engine"])
    self.assertTrue(engine.disposed)

  def test_downgrade_and_revision_require_explicit_nonempty_values(self):
    MigrationService, _, RevisionStateError, _ = self.load_api()
    service = MigrationService(
      config=unified_config(),
      engine_factory=lambda *args, **kwargs: FakeEngine(),
      commands=Mock(),
    )

    with self.assertRaises(RevisionStateError):
      service.downgrade("")
    with self.assertRaises(RevisionStateError):
      service.revision("  ")

  def test_unknown_current_revision_is_classified_without_crashing(self):
    MigrationService, _, _, _ = self.load_api()
    service = MigrationService(config=unified_config())

    self.assertEqual(
      "ahead_or_unknown",
      service._relation(
        "revision-from-newer-code",
        ("0001_initial_schema",),
        service._scripts(),
      ),
    )

  def test_stamp_wraps_alembic_failure_and_disposes_engine(self):
    from backend.src.database.migration_service import MigrationFailed

    MigrationService, _, _, _ = self.load_api()
    engine = FakeEngine()
    commands = Mock()
    commands.stamp.side_effect = RuntimeError("alembic failed")
    service = MigrationService(
      config=unified_config(),
      engine_factory=lambda *args, **kwargs: engine,
      compare_schema=lambda unused: SchemaReport(),
      commands=commands,
      current_revision_reader=lambda unused: None,
    )

    with self.assertRaises(MigrationFailed):
      service.stamp()
    self.assertTrue(engine.disposed)

  def test_status_classifies_multiple_database_heads_as_diverged(self):
    MigrationService, _, _, _ = self.load_api()
    service = MigrationService(
      config=unified_config(),
      engine_factory=lambda *args, **kwargs: FakeEngine(),
      compare_schema=lambda unused: SchemaReport(),
      current_revision_reader=lambda unused: ("branch_a", "branch_b"),
    )

    status = service.status()

    self.assertEqual("branch_a,branch_b", status.current)
    self.assertEqual("diverged", status.relation)
    self.assertEqual("diverged", status.classification)

  def test_upgrade_refuses_unversioned_database_with_managed_tables(self):
    MigrationService, _, RevisionStateError, _ = self.load_api()
    commands = Mock()
    inspector = Mock()
    inspector.get_table_names.return_value = ["share_url", "legacy_probe"]
    service = MigrationService(
      config=unified_config(),
      engine_factory=lambda *args, **kwargs: FakeEngine(),
      commands=commands,
      current_revision_reader=lambda unused: None,
    )

    with (
      patch("backend.src.database.migration_service.inspect", return_value=inspector),
      self.assertRaisesRegex(RevisionStateError, "check.*stamp"),
    ):
      service.upgrade("head")

    commands.upgrade.assert_not_called()

  def test_upgrade_allows_unversioned_database_with_only_unmanaged_tables(self):
    MigrationService, _, _, _ = self.load_api()
    commands = Mock()
    inspector = Mock()
    inspector.get_table_names.return_value = ["legacy_probe"]
    service = MigrationService(
      config=unified_config(),
      engine_factory=lambda *args, **kwargs: FakeEngine(),
      commands=commands,
      current_revision_reader=lambda unused: None,
    )

    with patch("backend.src.database.migration_service.inspect", return_value=inspector):
      service.upgrade("head")

    commands.upgrade.assert_called_once()

  def test_production_downgrade_protects_baseline_and_requires_confirmation(self):
    MigrationService, _, RevisionStateError, _ = self.load_api()
    commands = Mock()
    engine_factory = Mock(return_value=FakeEngine())
    service = MigrationService(
      config=unified_config(),
      engine_factory=engine_factory,
      commands=commands,
      current_revision_reader=lambda unused: "0001_initial_schema",
    )

    with self.assertRaisesRegex(RevisionStateError, "confirmation"):
      service.downgrade("0001_initial_schema")
    with self.assertRaises(RevisionStateError):
      service.downgrade("0001_initial_schema", confirm_database="another_database")
    with self.assertRaisesRegex(RevisionStateError, "disposable"):
      service.downgrade("base", confirm_database="smsd")
    with self.assertRaisesRegex(RevisionStateError, "disposable"):
      service.downgrade("-1", confirm_database="smsd")
    with self.assertRaisesRegex(RevisionStateError, "disposable"):
      service.downgrade(
        "0001_initial_schema@base",
        confirm_database="smsd",
      )

    commands.downgrade.assert_not_called()

    service.downgrade("0001_initial_schema", confirm_database="smsd")
    commands.downgrade.assert_called_once()

  def test_disposable_database_downgrade_does_not_require_confirmation(self):
    MigrationService, _, _, _ = self.load_api()
    commands = Mock()
    service = MigrationService(
      config=unified_config(),
      database_name="smsd_migration_test_0123456789ab",
      engine_factory=lambda *args, **kwargs: FakeEngine(),
      commands=commands,
    )

    service.downgrade("base")

    commands.downgrade.assert_called_once()

  def test_configured_database_name_cannot_impersonate_disposable_override(self):
    MigrationService, _, RevisionStateError, _ = self.load_api()
    config = unified_config()
    config["database"]["name"] = "smsd_migration_test_0123456789ab"
    commands = Mock()
    service = MigrationService(
      config=config,
      engine_factory=lambda *args, **kwargs: FakeEngine(),
      commands=commands,
    )

    with self.assertRaisesRegex(RevisionStateError, "disposable"):
      service.downgrade("base")

    commands.downgrade.assert_not_called()


if __name__ == "__main__":
  unittest.main()
