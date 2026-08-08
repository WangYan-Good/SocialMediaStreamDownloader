from contextlib import contextmanager
from pathlib import Path
import unittest

from backend.src.database.migration_service import MigrationStatus
from backend.src.database.schema_guard import (
  DatabaseSchemaGuard,
  DatabaseWriteBlocked,
  RuntimeSchemaMutationBlocked,
  install_schema_guard,
)
from backend.src.database.table.social_media_stream_db_table import SocialMediaStreamDataTable


def migration_status(compatible):
  return MigrationStatus(
    current="0001_initial_schema",
    heads=("0001_initial_schema",),
    relation="ready",
    schema_compatible=compatible,
  )


class FakeCursor:
  rowcount = 1
  lastrowid = 1

  def __enter__(self):
    return self

  def __exit__(self, *unused):
    return False

  def execute(self, *unused):
    return None

  def fetchone(self):
    return {"id": "1", "value": "stored"}


class FakeConnection:
  def cursor(self):
    return FakeCursor()

  def commit(self):
    return None


class FakeDatabase:
  def is_table_exist(self, unused):
    return True

  def is_table_registered(self, unused):
    return False

  def register_table(self, *unused):
    return None

  @contextmanager
  def get_connection(self):
    yield FakeConnection()


class SampleTable(SocialMediaStreamDataTable):
  def get_name(self):
    return "sample"

  def get_header(self):
    return ["id", "value"]

  def get_tuple(self):
    return {"id": None, "value": None}

  def get_pri_key(self):
    return ["id"]

  def get_auto_increment_field(self):
    return []

  def get_create_sql_cmd(self):
    return "CREATE TABLE sample (id VARCHAR(10) PRIMARY KEY)"

  def get_drop_sql_cmd(self):
    return "DROP TABLE sample"

  def verify_table_schema(self):
    return True


class DatabaseSchemaGuardTest(unittest.TestCase):
  def tearDown(self):
    install_schema_guard(None)

  def test_select_remains_available_but_insert_is_blocked(self):
    guard = DatabaseSchemaGuard(
      probe=lambda: migration_status(False), retry_seconds=30
    )
    install_schema_guard(guard)
    table = SampleTable(FakeDatabase())

    self.assertEqual([{"id": "1", "value": "stored"}], table.get_record({"id": "1"}))
    with self.assertRaises(DatabaseWriteBlocked):
      table.insert_record({"id": "1", "value": "new"})

  def test_production_guard_forbids_runtime_create_even_when_ready(self):
    guard = DatabaseSchemaGuard(
      probe=lambda: migration_status(True), retry_seconds=30
    )
    install_schema_guard(guard)
    table = SampleTable(FakeDatabase())

    with self.assertRaises(RuntimeSchemaMutationBlocked):
      table.create()

  def test_runtime_import_path_requires_migrated_tables_without_creating(self):
    from backend.src.database.table.table_import import require_managed_table

    class MissingDatabase:
      def is_table_exist(self, unused):
        return False

    with self.assertRaisesRegex(RuntimeError, "run the database migration command"):
      require_managed_table(MissingDatabase(), "room_base")

    source = (
      Path(__file__).resolve().parents[1]
      / "database"
      / "table"
      / "table_import.py"
    ).read_text(encoding="utf-8")
    self.assertNotIn(".create()", source)


if __name__ == "__main__":
  unittest.main()
