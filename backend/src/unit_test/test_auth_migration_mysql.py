##<<Base>>
import os
import unittest
import uuid

##<<Extension>>
import sqlalchemy as sa
from alembic import command
from sqlalchemy.exc import IntegrityError

##<<Third-part>>
from backend.src.database.migration import make_alembic_config
from backend.src.unit_test import no_network


##
## >>============================= why a real database =============================>>
##
##
## What is being proved here is that migration 0007 actually runs, on MySQL,
## against a database that already holds every earlier revision - and that it
## leaves the platform tables alone while doing it.
##
## None of that can be checked by reading the file.  A UNIQUE that MySQL refuses
## to create, a foreign key whose column types do not match, a CASCADE that
## silently is not one: each of these is a source file that looks correct and a
## database that disagrees.  The source-level tests in
## ``test_alembic_environment`` hold the shape; only this holds the behaviour.
##
## Skipped when no database is reachable so the ordinary run stays offline and
## fast, and required in CI so the skip cannot quietly become permanent.
##

DSN = os.environ.get("SMSD_TEST_MYSQL_DSN")

REQUIRED = os.environ.get("SMSD_REQUIRE_MYSQL_TESTS") == "1"

if REQUIRED and not DSN:
  raise RuntimeError(
    "SMSD_REQUIRE_MYSQL_TESTS=1 but SMSD_TEST_MYSQL_DSN is not set. "
    "These tests prove that the authentication migration runs on a real "
    "MySQL and leaves the platform tables untouched, which nothing else in "
    "the suite can stand in for."
  )

CONNECT_ARGS = {"connect_timeout": 5}


class RealDatabaseAllowed:
  """Lets this file - and only this file - reach a database."""

  @classmethod
  def setUpClass(cls):
    no_network.permit_real_connections()
    super(RealDatabaseAllowed, cls).setUpClass()

  @classmethod
  def tearDownClass(cls):
    try:
      super(RealDatabaseAllowed, cls).tearDownClass()
    finally:
      no_network.restore_block()


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


@unittest.skipUnless(DSN, "set SMSD_TEST_MYSQL_DSN to run the MySQL migration tests")
class AuthenticationMigrationTest(RealDatabaseAllowed, unittest.TestCase):
  """Migration 0007, run for real."""

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.database_name = "smsd_auth_{}".format(uuid.uuid4().hex[:12])
    cls.server = sa.create_engine(DSN, future=True, connect_args=CONNECT_ARGS)
    with cls.server.connect() as connection:
      connection.execute(
        sa.text(
          "CREATE DATABASE `{}` CHARACTER SET utf8mb4 "
          "COLLATE utf8mb4_0900_ai_ci".format(cls.database_name)
        )
      )
      connection.commit()
    cls.engine = sa.create_engine(
      "{}/{}".format(DSN.rstrip("/"), cls.database_name),
      future=True,
      connect_args=CONNECT_ARGS,
    )

  @classmethod
  def tearDownClass(cls):
    try:
      cls.engine.dispose()
      with cls.server.connect() as connection:
        connection.execute(
          sa.text("DROP DATABASE IF EXISTS `{}`".format(cls.database_name))
        )
        connection.commit()
      cls.server.dispose()
    finally:
      super().tearDownClass()

  ##
  ## >>--------------------------- helpers ---------------------------<<
  ##
  def _alembic(self):
    config = make_alembic_config(_config_for(self.database_name), self.database_name)
    config.attributes["engine"] = self.engine
    return config

  def upgrade(self, revision: str = "head"):
    command.upgrade(self._alembic(), revision)

  def downgrade(self, revision: str):
    command.downgrade(self._alembic(), revision)

  def tables(self):
    return set(sa.inspect(self.engine).get_table_names())

  def setUp(self):
    with self.engine.connect() as connection:
      for table in sorted(self.tables()):
        connection.execute(sa.text("DROP TABLE IF EXISTS `{}`".format(table)))
      connection.commit()

  ##
  ## >>--------------------------- the migration ---------------------------<<
  ##
  def test_upgrading_from_the_previous_revision_creates_both_tables(self):
    self.upgrade("0006_person_main_unique")
    self.assertNotIn("app_user", self.tables())

    self.upgrade("0007_authentication_foundation")

    self.assertIn("app_user", self.tables())
    self.assertIn("auth_session", self.tables())

  def test_the_platform_user_table_survives_untouched(self):
    ##
    ## The rule this whole phase is built around: ``user`` is a Douyin profile
    ## and authentication must not go near it.
    ##
    self.upgrade("0006_person_main_unique")
    with self.engine.connect() as connection:
      before = connection.execute(sa.text("SHOW CREATE TABLE `user`")).fetchone()[1]

    self.upgrade("0007_authentication_foundation")

    with self.engine.connect() as connection:
      after = connection.execute(sa.text("SHOW CREATE TABLE `user`")).fetchone()[1]
    self.assertEqual(before, after)

  def test_a_username_cannot_be_taken_twice(self):
    self.upgrade()

    with self.engine.connect() as connection:
      connection.execute(
        sa.text(
          "INSERT INTO app_user (username, password_hash) VALUES ('alice', 'x')"
        )
      )
      connection.commit()

      with self.assertRaises(IntegrityError):
        connection.execute(
          sa.text(
            "INSERT INTO app_user (username, password_hash) VALUES ('alice', 'y')"
          )
        )
        connection.commit()

  def test_a_session_cannot_point_at_a_user_who_does_not_exist(self):
    self.upgrade()

    with self.engine.connect() as connection:
      with self.assertRaises(IntegrityError):
        connection.execute(
          sa.text(
            "INSERT INTO auth_session (token_hash, user_id, expires_at)"
            " VALUES ('deadbeef', 999999, '2030-01-01 00:00:00')"
          )
        )
        connection.commit()

  def test_deleting_a_user_takes_their_sessions_with_them(self):
    ##
    ## The CASCADE, proved rather than asserted from the source. A foreign key
    ## declared without it looks identical in Python and behaves differently
    ## here.
    ##
    self.upgrade()

    with self.engine.connect() as connection:
      connection.execute(
        sa.text(
          "INSERT INTO app_user (username, password_hash) VALUES ('alice', 'x')"
        )
      )
      user_id = connection.execute(
        sa.text("SELECT user_id FROM app_user WHERE username = 'alice'")
      ).scalar()
      connection.execute(
        sa.text(
          "INSERT INTO auth_session (token_hash, user_id, expires_at)"
          " VALUES ('deadbeef', :user_id, '2030-01-01 00:00:00')"
        ),
        {"user_id": user_id},
      )
      connection.commit()

      connection.execute(
        sa.text("DELETE FROM app_user WHERE user_id = :user_id"), {"user_id": user_id}
      )
      connection.commit()

      remaining = connection.execute(
        sa.text("SELECT COUNT(*) FROM auth_session")
      ).scalar()
    self.assertEqual(0, remaining)

  def test_a_password_hash_column_holds_a_full_scrypt_string(self):
    ##
    ## A column too narrow for the hash truncates it silently, and a truncated
    ## hash never matches again - which presents as "the password stopped
    ## working" long after the migration that caused it.
    ##
    self.upgrade()
    from backend.src.auth.credentials import hash_password

    stored = hash_password("correct horse battery staple")

    with self.engine.connect() as connection:
      connection.execute(
        sa.text(
          "INSERT INTO app_user (username, password_hash) VALUES ('alice', :hash)"
        ),
        {"hash": stored},
      )
      connection.commit()
      read_back = connection.execute(
        sa.text("SELECT password_hash FROM app_user WHERE username = 'alice'")
      ).scalar()

    self.assertEqual(stored, read_back)

  ##
  ## >>--------------------------- the downgrade ---------------------------<<
  ##
  def test_downgrading_removes_both_tables(self):
    self.upgrade()

    self.downgrade("0006_person_main_unique")

    tables = self.tables()
    self.assertNotIn("app_user", tables)
    self.assertNotIn("auth_session", tables)

  def test_downgrading_leaves_the_platform_tables_alone(self):
    self.upgrade()

    self.downgrade("0006_person_main_unique")

    tables = self.tables()
    for platform_table in ("user", "share_url", "aweme_record", "live_record", "person"):
      self.assertIn(platform_table, tables)


if __name__ == "__main__":
  unittest.main()
