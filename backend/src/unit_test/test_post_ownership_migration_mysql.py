import os
import unittest
import uuid

from alembic import command
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from backend.src.database.migration import make_alembic_config
from backend.src.unit_test import no_network


DSN = os.environ.get("SMSD_TEST_MYSQL_DSN")
REQUIRED = os.environ.get("SMSD_REQUIRE_MYSQL_TESTS") == "1"

if REQUIRED and not DSN:
  raise RuntimeError(
    "SMSD_REQUIRE_MYSQL_TESTS=1 but SMSD_TEST_MYSQL_DSN is not set. "
    "The ownership migration must run against real MySQL."
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
class PostOwnershipMigrationTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    no_network.permit_real_connections()
    cls.database_name = "smsd_owner_{}".format(uuid.uuid4().hex[:12])
    cls.server = sa.create_engine(DSN, future=True, connect_args={"connect_timeout": 5})
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
    config = make_alembic_config(_config_for(self.database_name), self.database_name)
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

  def seed(self):
    with self.engine.connect() as connection:
      connection.execute(sa.text(
        "INSERT INTO app_user (username, password_hash) "
        "VALUES ('alice', 'x'), ('bob', 'x')"
      ))
      connection.execute(sa.text(
        "INSERT INTO aweme_record "
        "(platform, aweme_id, downloaded_at, media_count, saved_count) "
        "VALUES ('douyin', 'post-x', CURRENT_TIMESTAMP(3), 1, 1)"
      ))
      users = dict(connection.execute(sa.text(
        "SELECT username, user_id FROM app_user"
      )).all())
      connection.commit()
    return users

  def test_upgrade_shape_downgrade_and_reupgrade(self):
    self.upgrade("0007_authentication_foundation")
    self.assertNotIn("app_user_aweme_record", sa.inspect(self.engine).get_table_names())

    self.upgrade("0008_app_user_aweme_ownership")
    inspector = sa.inspect(self.engine)
    self.assertEqual(
      ["app_user_id", "platform", "aweme_id"],
      inspector.get_pk_constraint("app_user_aweme_record")["constrained_columns"],
    )
    self.assertEqual(
      {"ix_app_user_aweme_record_aweme": ["platform", "aweme_id"]},
      {
        index["name"]: index["column_names"]
        for index in inspector.get_indexes("app_user_aweme_record")
        if index["name"] == "ix_app_user_aweme_record_aweme"
      },
    )
    foreign_keys = {
      tuple(item["constrained_columns"]): (
        item["referred_table"],
        tuple(item["referred_columns"]),
        item["options"].get("ondelete"),
      )
      for item in inspector.get_foreign_keys("app_user_aweme_record")
    }
    self.assertEqual(
      ("app_user", ("user_id",), "CASCADE"),
      foreign_keys[("app_user_id",)],
    )
    self.assertEqual(
      ("aweme_record", ("platform", "aweme_id"), "CASCADE"),
      foreign_keys[("platform", "aweme_id")],
    )

    self.downgrade("0007_authentication_foundation")
    self.assertNotIn("app_user_aweme_record", sa.inspect(self.engine).get_table_names())
    self.upgrade("0008_app_user_aweme_ownership")
    self.assertIn("app_user_aweme_record", sa.inspect(self.engine).get_table_names())

  def test_many_to_many_idempotence_foreign_keys_and_cascade_directions(self):
    self.upgrade()
    users = self.seed()
    link = sa.text(
      "INSERT INTO app_user_aweme_record (app_user_id, platform, aweme_id) "
      "VALUES (:user_id, 'douyin', 'post-x') "
      "ON DUPLICATE KEY UPDATE app_user_id = VALUES(app_user_id)"
    )
    with self.engine.connect() as connection:
      connection.execute(link, {"user_id": users["alice"]})
      connection.execute(link, {"user_id": users["alice"]})
      connection.execute(link, {"user_id": users["bob"]})
      connection.commit()
      self.assertEqual(
        2,
        connection.execute(sa.text(
          "SELECT COUNT(*) FROM app_user_aweme_record"
        )).scalar(),
      )

      with self.assertRaises(IntegrityError):
        connection.execute(link, {"user_id": 999999})
        connection.commit()
      connection.rollback()
      with self.assertRaises(IntegrityError):
        connection.execute(sa.text(
          "INSERT INTO app_user_aweme_record "
          "(app_user_id, platform, aweme_id) "
          "VALUES (:user_id, 'douyin', 'missing')"
        ), {"user_id": users["alice"]})
        connection.commit()
      connection.rollback()

      connection.execute(sa.text(
        "DELETE FROM app_user WHERE user_id = :user_id"
      ), {"user_id": users["alice"]})
      connection.commit()
      self.assertEqual(
        1,
        connection.execute(sa.text(
          "SELECT COUNT(*) FROM app_user_aweme_record"
        )).scalar(),
      )
      self.assertEqual(
        1,
        connection.execute(sa.text(
          "SELECT COUNT(*) FROM aweme_record WHERE aweme_id = 'post-x'"
        )).scalar(),
      )

      connection.execute(sa.text(
        "DELETE FROM aweme_record WHERE platform = 'douyin' AND aweme_id = 'post-x'"
      ))
      connection.commit()
      self.assertEqual(
        0,
        connection.execute(sa.text(
          "SELECT COUNT(*) FROM app_user_aweme_record"
        )).scalar(),
      )
      self.assertEqual(
        1,
        connection.execute(sa.text(
          "SELECT COUNT(*) FROM app_user WHERE username = 'bob'"
        )).scalar(),
      )

  def test_scoped_rows_exclude_other_users_and_unowned_history(self):
    self.upgrade()
    with self.engine.connect() as connection:
      connection.execute(sa.text(
        "INSERT INTO app_user (username, password_hash) "
        "VALUES ('alice', 'x'), ('bob', 'x')"
      ))
      users = dict(connection.execute(sa.text(
        "SELECT username, user_id FROM app_user"
      )).all())
      connection.execute(sa.text(
        "INSERT INTO aweme_record "
        "(platform, aweme_id, downloaded_at, media_count, saved_count) VALUES "
        "('douyin', 'x', CURRENT_TIMESTAMP(3), 1, 1), "
        "('douyin', 'y', CURRENT_TIMESTAMP(3), 1, 1), "
        "('douyin', 'z', CURRENT_TIMESTAMP(3), 1, 1)"
      ))
      connection.execute(sa.text(
        "INSERT INTO app_user_aweme_record "
        "(app_user_id, platform, aweme_id) VALUES "
        "(:alice, 'douyin', 'x'), (:bob, 'douyin', 'x'), "
        "(:alice, 'douyin', 'y')"
      ), users)
      connection.commit()

      def scoped(user_id):
        return set(connection.execute(sa.text(
          "SELECT a.aweme_id FROM aweme_record a "
          "JOIN app_user_aweme_record uar "
          "ON uar.platform = a.platform AND uar.aweme_id = a.aweme_id "
          "WHERE uar.app_user_id = :user_id"
        ), {"user_id": user_id}).scalars())

      self.assertEqual({"x", "y"}, scoped(users["alice"]))
      self.assertEqual({"x"}, scoped(users["bob"]))
      self.assertEqual(
        {"x", "y", "z"},
        set(connection.execute(sa.text(
          "SELECT aweme_id FROM aweme_record"
        )).scalars()),
      )


if __name__ == "__main__":
  unittest.main()
