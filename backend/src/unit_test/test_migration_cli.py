from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import unittest
from unittest.mock import Mock, patch

from backend.src.database.schema_compare import SchemaReport


class MigrationCliTest(unittest.TestCase):
  def run_cli(self, argv, service):
    try:
      from backend.src.database import migration_cli
    except ImportError as exc:
      raise AssertionError("migration CLI is not implemented") from exc
    output = StringIO()
    errors = StringIO()
    with (
      patch.object(migration_cli, "MigrationService", return_value=service),
      redirect_stdout(output),
      redirect_stderr(errors),
    ):
      code = migration_cli.main(argv)
    return code, output.getvalue(), errors.getvalue()

  def test_check_returns_schema_mismatch_without_exposing_credentials(self):
    from backend.src.database.schema_compare import SchemaReport

    service = Mock()
    service.check.return_value = SchemaReport.with_error(
      "room_base", "column", "missing id"
    )
    code, output, errors = self.run_cli(["check"], service)

    self.assertEqual(4, code)
    self.assertIn("missing id", output)
    self.assertNotIn("credential-marker", output + errors)

  def test_upgrade_dispatches_to_service(self):
    service = Mock()
    code, output, errors = self.run_cli(["upgrade"], service)

    self.assertEqual(0, code)
    service.upgrade.assert_called_once_with("head")
    self.assertEqual("", errors)

  def test_downgrade_passes_explicit_database_confirmation(self):
    service = Mock()

    code, _, errors = self.run_cli(
      ["downgrade", "base", "--confirm-database", "smsd"],
      service,
    )

    self.assertEqual(0, code)
    self.assertEqual("", errors)
    service.downgrade.assert_called_once_with("base", confirm_database="smsd")

  def test_known_errors_map_to_stable_exit_codes(self):
    try:
      from backend.src.database.migration_service import (
        DatabaseUnavailable,
        RevisionStateError,
      )
    except ModuleNotFoundError as exc:
      raise AssertionError("migration service is not implemented") from exc

    service = Mock()
    service.status.side_effect = DatabaseUnavailable("credential-marker")
    code, output, errors = self.run_cli(["status"], service)
    self.assertEqual(3, code)
    self.assertNotIn("credential-marker", output + errors)

    service = Mock()
    service.stamp.side_effect = RevisionStateError("already versioned")
    code, _, errors = self.run_cli(["stamp"], service)
    self.assertEqual(5, code)
    self.assertIn("already versioned", errors)

  def test_database_unavailable_reports_only_nonsecret_location(self):
    from backend.src.database.migration_service import DatabaseUnavailable

    service = Mock()
    service.status.side_effect = DatabaseUnavailable(
      host="db.internal",
      port=3306,
      database="smsd",
    )

    code, output, errors = self.run_cli(["status"], service)

    self.assertEqual(3, code)
    self.assertEqual("", output)
    self.assertIn("host=db.internal", errors)
    self.assertIn("port=3306", errors)
    self.assertIn("database=smsd", errors)
    self.assertNotIn("password", errors.lower())


if __name__ == "__main__":
  unittest.main()
