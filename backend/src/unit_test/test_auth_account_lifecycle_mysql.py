import io
import os
from types import SimpleNamespace
import unittest
import uuid

from alembic import command
import pymysql
import sqlalchemy as sa

from backend.src.auth.cli import (
  build_cli_service_factory,
  disable_user_command,
  enable_user_command,
  revoke_sessions_command,
  set_password_command,
)
from backend.src.auth.errors import InvalidCredentials
from backend.src.auth.repository import AuthRepository
from backend.src.auth.service import AuthenticationService
from backend.src.database.migration import make_alembic_config
from backend.src.unit_test import no_network


DSN = os.environ.get("SMSD_TEST_MYSQL_DSN")
REQUIRED = os.environ.get("SMSD_REQUIRE_MYSQL_TESTS") == "1"
if REQUIRED and not DSN:
  raise RuntimeError(
    "SMSD_REQUIRE_MYSQL_TESTS=1 but SMSD_TEST_MYSQL_DSN is not set"
  )


class RealDatabaseAllowed:
  @classmethod
  def setUpClass(cls):
    no_network.permit_real_connections()
    super().setUpClass()

  @classmethod
  def tearDownClass(cls):
    try:
      super().tearDownClass()
    finally:
      no_network.restore_block()


class PortAwareTestDatabase:
  """Test adapter for the random host port; production Compose uses 3306."""

  def __init__(self, config):
    self.config = config["database"]

  def get_connection(self):
    return pymysql.connect(
      host=self.config["host"],
      port=self.config["port"],
      user=self.config["username"],
      password=self.config["password"],
      database=self.config["name"],
      charset="utf8mb4",
    )


@unittest.skipUnless(DSN, "set SMSD_TEST_MYSQL_DSN to run account lifecycle proof")
class AuthenticationAccountLifecycleMySQLTest(
  RealDatabaseAllowed, unittest.TestCase
):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.database_name = "smsd_auth_lifecycle_{}".format(uuid.uuid4().hex[:12])
    cls.server = sa.create_engine(DSN, future=True, connect_args={"connect_timeout": 5})
    with cls.server.connect() as connection:
      connection.execute(
        sa.text(
          "CREATE DATABASE `{}` CHARACTER SET utf8mb4 "
          "COLLATE utf8mb4_0900_ai_ci".format(cls.database_name)
        )
      )
      connection.commit()
    url = sa.engine.make_url(DSN)
    cls.config = {
      "database": {
        "enable": True,
        "host": url.host,
        "port": url.port or 3306,
        "username": url.username,
        "password": url.password,
        "name": cls.database_name,
      },
      "auth": {"session_ttl_seconds": 3600},
    }
    cls.engine = sa.create_engine(
      "{}/{}".format(DSN.rstrip("/"), cls.database_name),
      future=True,
      connect_args={"connect_timeout": 5},
    )
    alembic = make_alembic_config(cls.config, cls.database_name)
    alembic.attributes["engine"] = cls.engine
    command.upgrade(alembic, "head")

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

  def setUp(self):
    with self.engine.connect() as connection:
      connection.execute(sa.text("DELETE FROM auth_session"))
      connection.execute(sa.text("DELETE FROM app_user"))
      connection.commit()
    def runtime_builder(provider):
      settings = provider()
      database = PortAwareTestDatabase(settings)
      return SimpleNamespace(
        service=lambda: AuthenticationService(
          AuthRepository(database), session_ttl_seconds=3600
        )
      )

    self.factory = build_cli_service_factory(
      config_loader=lambda: self.config,
      runtime_builder=runtime_builder,
    )
    self.service = self.factory()
    self.user = self.service.create_user("alice", "old correct horse battery")

  def test_cli_lifecycle_is_atomic_and_invalidates_old_sessions(self):
    old_session = self.service.create_session(self.user.user_id)
    output = io.StringIO()
    self.assertEqual(
      0,
      set_password_command(
        "alice",
        service_factory=self.factory,
        prompt=lambda _label: "new correct horse battery",
        out=output,
      ),
    )
    with self.assertRaises(InvalidCredentials):
      self.factory().authenticate("alice", "old correct horse battery")
    self.factory().authenticate("alice", "new correct horse battery")
    self.assertIsNone(self.factory().resolve_session(old_session.token))

    before_disable = self.factory().create_session(self.user.user_id)
    self.assertEqual(
      0,
      disable_user_command(
        "alice", service_factory=self.factory, out=io.StringIO()
      ),
    )
    with self.assertRaises(InvalidCredentials):
      self.factory().authenticate("alice", "new correct horse battery")
    self.assertIsNone(self.factory().resolve_session(before_disable.token))

    self.assertEqual(
      0,
      enable_user_command(
        "alice", service_factory=self.factory, out=io.StringIO()
      ),
    )
    self.factory().authenticate("alice", "new correct horse battery")
    self.assertIsNone(self.factory().resolve_session(before_disable.token))

    current = self.factory().create_session(self.user.user_id)
    self.assertEqual(
      0,
      revoke_sessions_command(
        "alice", service_factory=self.factory, out=io.StringIO()
      ),
    )
    self.assertIsNone(self.factory().resolve_session(current.token))


if __name__ == "__main__":
  unittest.main()
