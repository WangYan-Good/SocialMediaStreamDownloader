from contextlib import contextmanager
from copy import deepcopy
import re
import secrets
import unittest

from alembic import command
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from backend.src.database.migration_service import (
  MigrationService,
  RevisionStateError,
  SchemaMismatchError,
)
from backend.src.database.migration import make_alembic_config
from backend.src.database.orm.engine import create_schema_engine
from backend.src.database.orm.models import MANAGED_TABLE_NAMES
from backend.src.library.configlib import load_config


TEST_DATABASE_PATTERN = re.compile(r"^smsd_migration_test_[0-9a-f]{12}$")


def validate_test_database_name(name):
  if not isinstance(name, str) or not TEST_DATABASE_PATTERN.fullmatch(name):
    raise ValueError("unsafe migration test database name")
  return name


@contextmanager
def disposable_database(config):
  database_name = validate_test_database_name(
    "smsd_migration_test_{}".format(secrets.token_hex(6))
  )
  administration_engine = create_schema_engine(config, database_name="mysql")
  created = False
  try:
    with administration_engine.connect().execution_options(
      isolation_level="AUTOCOMMIT"
    ) as connection:
      validated = validate_test_database_name(database_name)
      connection.exec_driver_sql(
        "CREATE DATABASE `{}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci".format(
          validated
        )
      )
    created = True
    print("created disposable database {}".format(database_name))
    yield database_name
  finally:
    try:
      if created:
        with administration_engine.connect().execution_options(
          isolation_level="AUTOCOMMIT"
        ) as connection:
          validated = validate_test_database_name(database_name)
          connection.exec_driver_sql(
            "DROP DATABASE IF EXISTS `{}`".format(validated)
          )
        print("removed disposable database {}".format(database_name))
    finally:
      administration_engine.dispose()


def current_revision(engine):
  with engine.connect() as connection:
    return MigrationContext.configure(connection).get_current_revision()


class OrmMigrationIntegrationTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.config = load_config()

  def test_empty_database_round_trip_and_unmanaged_table_survival(self):
    with disposable_database(self.config) as database_name:
      service = MigrationService(self.config, database_name=database_name)
      engine = create_schema_engine(self.config, database_name)
      try:
        with engine.begin() as connection:
          connection.exec_driver_sql(
            "CREATE TABLE legacy_v1_probe (id INT PRIMARY KEY) ENGINE=InnoDB"
          )
        service.upgrade("head")
        self.assertEqual("0001_initial_schema", current_revision(engine))
        report = service.check()
        self.assertTrue(report.is_compatible, report.format_text())
        self.assertEqual(
          ["legacy_v1_probe"],
          [item.table for item in report.warnings],
        )

        service.downgrade("base")
        tables = set(inspect(engine).get_table_names())
        self.assertTrue(MANAGED_TABLE_NAMES.isdisjoint(tables))
        self.assertIn("legacy_v1_probe", tables)

        service.upgrade("head")
        self.assertTrue(service.check().is_compatible)
        self.assertIn("legacy_v1_probe", inspect(engine).get_table_names())

        alembic_config = make_alembic_config(self.config, database_name)
        alembic_config.attributes["engine"] = engine
        command.check(alembic_config)
      finally:
        engine.dispose()

  def test_upgrade_refuses_existing_unversioned_managed_table_without_mutation(self):
    with disposable_database(self.config) as database_name:
      service = MigrationService(self.config, database_name=database_name)
      engine = create_schema_engine(self.config, database_name)
      try:
        with engine.begin() as connection:
          connection.exec_driver_sql(
            "CREATE TABLE share_url (owner_user_id VARCHAR(200) PRIMARY KEY) ENGINE=InnoDB"
          )

        with self.assertRaisesRegex(RevisionStateError, "check.*stamp"):
          service.upgrade("head")

        self.assertEqual({"share_url"}, set(inspect(engine).get_table_names()))
      finally:
        engine.dispose()

  def test_configured_database_cannot_downgrade_baseline_through_relative_target(self):
    with disposable_database(self.config) as database_name:
      configured = deepcopy(self.config)
      configured["database"]["name"] = database_name
      service = MigrationService(configured)
      engine = create_schema_engine(configured)
      try:
        service.upgrade("head")

        with self.assertRaisesRegex(RevisionStateError, "disposable"):
          service.downgrade("-1", confirm_database=database_name)

        self.assertEqual("0001_initial_schema", current_revision(engine))
        self.assertTrue(MANAGED_TABLE_NAMES.issubset(inspect(engine).get_table_names()))
      finally:
        engine.dispose()

  def test_status_handles_unknown_and_multiple_database_revisions(self):
    with disposable_database(self.config) as database_name:
      service = MigrationService(self.config, database_name=database_name)
      engine = create_schema_engine(self.config, database_name)
      try:
        service.upgrade("head")
        with engine.begin() as connection:
          connection.exec_driver_sql(
            "UPDATE alembic_version SET version_num=%s",
            ("revision_from_newer_code",),
          )
        self.assertEqual("ahead_or_unknown", service.status().classification)

        with engine.begin() as connection:
          connection.exec_driver_sql(
            "UPDATE alembic_version SET version_num=%s",
            ("0001_initial_schema",),
          )
          connection.exec_driver_sql(
            "INSERT INTO alembic_version (version_num) VALUES (%s)",
            ("second_database_head",),
          )
        status = service.status()
        self.assertEqual("diverged", status.classification)
        self.assertEqual(
          "0001_initial_schema,second_database_head",
          status.current,
        )
      finally:
        engine.dispose()

  def test_existing_schema_can_be_checked_and_stamped_without_data_loss(self):
    with disposable_database(self.config) as database_name:
      service = MigrationService(self.config, database_name=database_name)
      engine = create_schema_engine(self.config, database_name)
      try:
        service.upgrade("head")
        with engine.begin() as connection:
          connection.exec_driver_sql(
            "INSERT INTO share_url (owner_user_id, nickname) VALUES (%s, %s)",
            ("adoption-owner", "Adoption Test"),
          )
          connection.exec_driver_sql("DROP TABLE alembic_version")
        before_tables = set(inspect(engine).get_table_names())

        report = service.check()
        self.assertTrue(report.is_compatible, report.format_text())
        service.stamp()

        self.assertEqual("0001_initial_schema", current_revision(engine))
        after_tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
        self.assertEqual(before_tables, after_tables)
        with engine.connect() as connection:
          row = connection.exec_driver_sql(
            "SELECT owner_user_id, nickname FROM share_url WHERE owner_user_id=%s",
            ("adoption-owner",),
          ).mappings().one()
        self.assertEqual("Adoption Test", row["nickname"])
      finally:
        engine.dispose()

  def test_every_managed_drift_category_blocks_stamp(self):
    drift_cases = (
      ("missing column", "ALTER TABLE share_url DROP COLUMN sec_user_id", "column"),
      ("extra column", "ALTER TABLE share_url ADD COLUMN unexpected INT NULL", "column"),
      ("changed length", "ALTER TABLE share_url MODIFY sec_user_id VARCHAR(199) NULL", "column"),
      ("unsigned", "ALTER TABLE share_url MODIFY actived_count INT NOT NULL DEFAULT 0", "column"),
      ("nullable", "ALTER TABLE share_url MODIFY actived_count INT UNSIGNED NULL DEFAULT 0", "column"),
      ("default", "ALTER TABLE share_url ALTER COLUMN actived_count SET DEFAULT 7", "column"),
      (
        "primary key",
        "ALTER TABLE favorite_owner DROP PRIMARY KEY, ADD PRIMARY KEY (platform, owner_user_id)",
        "primary_key",
      ),
      ("index", "ALTER TABLE share_url DROP INDEX idx_nickname", "index"),
      (
        "unique constraint",
        "ALTER TABLE room_admin_user_id DROP INDEX unique_record",
        "unique_constraint",
      ),
      ("engine", "ALTER TABLE room_stats ENGINE=MyISAM", "engine"),
      (
        "charset",
        "ALTER TABLE room_stats CONVERT TO CHARACTER SET latin1 COLLATE latin1_swedish_ci",
        "charset",
      ),
      (
        "collation",
        "ALTER TABLE room_stats CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci",
        "collation",
      ),
      (
        "autoincrement",
        "ALTER TABLE room_admin_user_id MODIFY `index` BIGINT NOT NULL",
        "column",
      ),
      (
        "column collation",
        "ALTER TABLE share_url MODIFY live_share_url VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL",
        "column",
      ),
    )
    with disposable_database(self.config) as database_name:
      service = MigrationService(self.config, database_name=database_name)
      engine = create_schema_engine(self.config, database_name)
      try:
        service.upgrade("head")
        for label, statement, expected_object in drift_cases:
          with self.subTest(drift=label):
            with engine.begin() as connection:
              connection.exec_driver_sql(statement)
            with self.assertRaises(SchemaMismatchError) as raised:
              service.stamp()
            self.assertIn(
              expected_object,
              {item.object_type for item in raised.exception.report.errors},
            )
            service.downgrade("base")
            service.upgrade("head")
      finally:
        engine.dispose()


if __name__ == "__main__":
  unittest.main()
