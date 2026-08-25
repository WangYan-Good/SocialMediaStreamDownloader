import os
import unittest
import uuid

from alembic import command
import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from backend.src.database.migration import make_alembic_config
from backend.src.database.orm.models import AppUserModel
from backend.src.database.schema_compare import compare_managed_schema
from backend.src.unit_test import no_network


DSN = os.environ.get("SMSD_TEST_MYSQL_DSN")
REQUIRED = os.environ.get("SMSD_REQUIRE_MYSQL_TESTS") == "1"

if REQUIRED and not DSN:
  raise RuntimeError(
    "SMSD_REQUIRE_MYSQL_TESTS=1 but SMSD_TEST_MYSQL_DSN is not set. "
    "The RBAC role migration must run against real MySQL."
  )


def _config_for(database_name: str) -> dict:
  url = sa.engine.make_url(DSN)
  return {
    "database": {
      "host": url.host,
      "port": url.port or 3306,
      "username": url.username,
      "password": url.password,
      "name": database_name,
    }
  }


@unittest.skipUnless(DSN, "set SMSD_TEST_MYSQL_DSN to run MySQL migration tests")
class RbacRoleMigrationTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    no_network.permit_real_connections()
    cls.database_name = "smsd_migration_test_{}".format(uuid.uuid4().hex[:12])
    cls.server = sa.create_engine(
      DSN, future=True, connect_args={"connect_timeout": 5}
    )
    with cls.server.connect() as connection:
      connection.execute(sa.text(
        "CREATE DATABASE `{}` CHARACTER SET utf8mb4 "
        "COLLATE utf8mb4_0900_ai_ci".format(cls.database_name)
      ))
      connection.commit()
    cls.engine = sa.create_engine(
      "{}/{}".format(DSN.rstrip("/"), cls.database_name),
      future=True,
      connect_args={"connect_timeout": 5},
    )

  @classmethod
  def tearDownClass(cls):
    try:
      cls.engine.dispose()
      with cls.server.connect() as connection:
        connection.execute(sa.text(
          "DROP DATABASE IF EXISTS `{}`".format(cls.database_name)
        ))
        connection.commit()
      cls.server.dispose()
    finally:
      no_network.restore_block()

  def _alembic(self):
    config = make_alembic_config(
      _config_for(self.database_name), self.database_name
    )
    config.attributes["engine"] = self.engine
    return config

  def upgrade(self, revision="head"):
    command.upgrade(self._alembic(), revision)

  def downgrade(self, revision):
    command.downgrade(self._alembic(), revision)

  def setUp(self):
    inspector = sa.inspect(self.engine)
    with self.engine.connect() as connection:
      connection.execute(sa.text("SET FOREIGN_KEY_CHECKS = 0"))
      try:
        for table in inspector.get_table_names():
          connection.execute(sa.text("DROP TABLE IF EXISTS `{}`".format(table)))
      finally:
        connection.execute(sa.text("SET FOREIGN_KEY_CHECKS = 1"))
      connection.commit()

  def test_0009_upgrade_0010_downgrade_and_reupgrade(self):
    self.upgrade("0009_recording_resource")
    with self.engine.connect() as connection:
      connection.execute(sa.text(
        "INSERT INTO app_user (username, password_hash) "
        "VALUES ('existing-alice', 'x'), ('existing-bob', 'x')"
      ))
      connection.commit()

    self.upgrade("0010_rbac_role_foundation")
    inspector = sa.inspect(self.engine)
    role = {column["name"]: column for column in inspector.get_columns("app_user")}["role"]
    self.assertFalse(role["nullable"])
    self.assertIn("user", str(role["default"]).lower())
    checks = {item["name"]: item["sqltext"] for item in inspector.get_check_constraints("app_user")}
    self.assertIn("ck_app_user_role", checks)
    self.assertIn("admin", checks["ck_app_user_role"])
    report = compare_managed_schema(self.engine)
    self.assertTrue(report.is_compatible, report.format_text())

    with self.engine.connect() as connection:
      migrated = connection.execute(sa.text(
        "SELECT username, role FROM app_user ORDER BY username"
      )).all()
    self.assertEqual(
      [("existing-alice", "user"), ("existing-bob", "user")],
      migrated,
    )

    self.downgrade("0009_recording_resource")
    inspector = sa.inspect(self.engine)
    self.assertNotIn("role", {column["name"] for column in inspector.get_columns("app_user")})
    for preserved in (
      "auth_session",
      "app_user_aweme_record",
      "recording_record",
    ):
      self.assertIn(preserved, inspector.get_table_names())

    self.upgrade("0010_rbac_role_foundation")
    self.assertIn(
      "role",
      {column["name"] for column in sa.inspect(self.engine).get_columns("app_user")},
    )

  def test_real_mysql_rejects_every_invalid_role_and_accepts_both_valid_roles(self):
    self.upgrade()
    insert = sa.text(
      "INSERT INTO app_user (username, password_hash, role) "
      "VALUES (:username, 'x', :role)"
    )
    with self.engine.connect() as connection:
      for index, role in enumerate(("root", "administrator", "superuser", "")):
        with self.subTest(role=role):
          with self.assertRaises(DBAPIError):
            connection.execute(
              insert,
              {"username": "invalid-{}".format(index), "role": role},
            )
            connection.commit()
          connection.rollback()

      connection.execute(insert, {"username": "ordinary", "role": "user"})
      connection.execute(insert, {"username": "operator", "role": "admin"})
      connection.execute(sa.text(
        "INSERT INTO app_user (username, password_hash) VALUES ('defaulted', 'x')"
      ))
      connection.commit()
      rows = dict(connection.execute(sa.text(
        "SELECT username, role FROM app_user"
      )).all())

    self.assertEqual("user", rows["ordinary"])
    self.assertEqual("admin", rows["operator"])
    self.assertEqual("user", rows["defaulted"])

  def test_role_survives_an_orm_roundtrip(self):
    self.upgrade()
    with Session(self.engine) as session:
      session.add(AppUserModel(
        username="orm-admin",
        password_hash="x",
        role="admin",
      ))
      session.commit()
      session.expire_all()
      stored = session.query(AppUserModel).filter_by(username="orm-admin").one()

    self.assertEqual("admin", stored.role)


if __name__ == "__main__":
  unittest.main()
