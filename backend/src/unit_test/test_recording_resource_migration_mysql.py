import os
import unittest
import uuid

from alembic import command
import pymysql
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from backend.src.database.migration import make_alembic_config
from backend.src.database.query.library import (
  LibraryQuery,
  LibraryRecordingFilter,
)
from backend.src.unit_test import no_network


DSN = os.environ.get("SMSD_TEST_MYSQL_DSN")
REQUIRED = os.environ.get("SMSD_REQUIRE_MYSQL_TESTS") == "1"

if REQUIRED and not DSN:
  raise RuntimeError(
    "SMSD_REQUIRE_MYSQL_TESTS=1 but SMSD_TEST_MYSQL_DSN is not set. "
    "The recording resource migration must run against real MySQL."
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
class RecordingResourceMigrationTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    no_network.permit_real_connections()
    cls.database_name = "smsd_recording_{}".format(uuid.uuid4().hex[:12])
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

  def _users(self):
    with self.engine.connect() as connection:
      connection.execute(sa.text(
        "INSERT INTO app_user (username, password_hash) "
        "VALUES ('alice', 'x'), ('bob', 'x')"
      ))
      users = dict(connection.execute(sa.text(
        "SELECT username, user_id FROM app_user"
      )).all())
      connection.commit()
    return users

  def _library(self):
    url = sa.engine.make_url(DSN)
    class QueryDatabase:
      def get_connection(inner_self):
        return pymysql.connect(
          host=url.host,
          port=url.port or 3306,
          user=url.username,
          password=url.password,
          database=self.database_name,
          charset="utf8mb4",
          cursorclass=pymysql.cursors.DictCursor,
        )

    database = QueryDatabase()
    return LibraryQuery(database)

  def test_upgrade_shape_downgrade_reupgrade_and_no_historical_backfill(self):
    self.upgrade("0008_app_user_aweme_ownership")
    with self.engine.connect() as connection:
      connection.execute(sa.text(
        "INSERT INTO live_record "
        "(`now`, platform, room_id, owner_user_id, user_id, status_code) "
        "VALUES (CURRENT_TIMESTAMP(3), 'douyin', 'legacy-room', "
        "'platform-owner', 'platform-viewer', 0)"
      ))
      connection.commit()

    self.assertNotIn("recording_record", sa.inspect(self.engine).get_table_names())
    self.upgrade("0009_recording_resource")

    inspector = sa.inspect(self.engine)
    self.assertEqual(
      ["recording_id"],
      inspector.get_pk_constraint("recording_record")["constrained_columns"],
    )
    columns = {column["name"]: column for column in inspector.get_columns("recording_record")}
    self.assertTrue(columns["app_user_id"]["nullable"])
    self.assertFalse(columns["output_path"]["nullable"])
    self.assertEqual(
      {
        "ix_recording_record_app_user_finished": ["app_user_id", "finished_at"],
        "ix_recording_record_owner_user_id": ["owner_user_id"],
        "ix_recording_record_finished_at": ["finished_at"],
      },
      {
        index["name"]: index["column_names"]
        for index in inspector.get_indexes("recording_record")
        if index["name"].startswith("ix_recording_record_")
      },
    )
    foreign_keys = inspector.get_foreign_keys("recording_record")
    self.assertEqual(1, len(foreign_keys))
    self.assertEqual(["app_user_id"], foreign_keys[0]["constrained_columns"])
    self.assertEqual("app_user", foreign_keys[0]["referred_table"])
    self.assertEqual(["user_id"], foreign_keys[0]["referred_columns"])
    self.assertEqual("SET NULL", foreign_keys[0]["options"].get("ondelete"))

    with self.engine.connect() as connection:
      self.assertEqual(
        0,
        connection.execute(sa.text("SELECT COUNT(*) FROM recording_record")).scalar(),
      )
      self.assertEqual(
        1,
        connection.execute(sa.text("SELECT COUNT(*) FROM live_record")).scalar(),
      )

    self.downgrade("0008_app_user_aweme_ownership")
    self.assertNotIn("recording_record", sa.inspect(self.engine).get_table_names())
    self.upgrade("0009_recording_resource")
    self.assertIn("recording_record", sa.inspect(self.engine).get_table_names())

  def test_same_room_creates_independent_owned_and_anonymous_resources(self):
    self.upgrade()
    users = self._users()
    insert = sa.text(
      "INSERT INTO recording_record "
      "(app_user_id, platform, room_id, owner_user_id, title, protocol, "
      "output_path, started_at, finished_at, source) VALUES "
      "(:app_user_id, 'douyin', 'room-x', 'platform-owner', '晚间直播', "
      "'hls', :output_path, CURRENT_TIMESTAMP(3), CURRENT_TIMESTAMP(3), :source)"
    )
    with self.engine.connect() as connection:
      connection.execute(insert, {
        "app_user_id": users["alice"],
        "output_path": "/media/alice/room-x.ts",
        "source": "task_api",
      })
      connection.execute(insert, {
        "app_user_id": users["bob"],
        "output_path": "/media/bob/room-x.ts",
        "source": "task_api",
      })
      connection.execute(insert, {
        "app_user_id": None,
        "output_path": "/media/legacy/room-x.ts",
        "source": "direct",
      })
      connection.commit()

      rows = connection.execute(sa.text(
        "SELECT recording_id, app_user_id, room_id, output_path "
        "FROM recording_record ORDER BY recording_id"
      )).mappings().all()

    self.assertEqual(3, len(rows))
    self.assertEqual(3, len({row["recording_id"] for row in rows}))
    self.assertEqual({"room-x"}, {row["room_id"] for row in rows})
    self.assertEqual(
      {users["alice"], users["bob"], None},
      {row["app_user_id"] for row in rows},
    )
    self.assertEqual(3, len({row["output_path"] for row in rows}))

  def test_foreign_key_rejects_unknown_owner_and_delete_sets_null(self):
    self.upgrade()
    users = self._users()
    insert = sa.text(
      "INSERT INTO recording_record "
      "(app_user_id, platform, room_id, output_path, source) "
      "VALUES (:app_user_id, 'douyin', 'room-x', '/media/room-x.flv', 'task_api')"
    )
    with self.engine.connect() as connection:
      with self.assertRaises(IntegrityError):
        connection.execute(insert, {"app_user_id": 999999})
        connection.commit()
      connection.rollback()

      connection.execute(insert, {"app_user_id": users["alice"]})
      recording_id = connection.execute(sa.text(
        "SELECT recording_id FROM recording_record"
      )).scalar_one()
      connection.execute(sa.text(
        "DELETE FROM app_user WHERE user_id = :user_id"
      ), {"user_id": users["alice"]})
      connection.commit()

      row = connection.execute(sa.text(
        "SELECT recording_id, app_user_id FROM recording_record "
        "WHERE recording_id = :recording_id"
      ), {"recording_id": recording_id}).mappings().one()

    self.assertEqual(recording_id, row["recording_id"])
    self.assertIsNone(row["app_user_id"])

  def test_global_and_scoped_queries_keep_owners_totals_filters_and_pages(self):
    self.upgrade()
    users = self._users()
    insert = sa.text(
      "INSERT INTO recording_record "
      "(app_user_id, platform, room_id, owner_user_id, title, protocol, "
      "output_path, started_at, finished_at, source) VALUES "
      "(:app_user_id, 'douyin', 'room-x', :owner_user_id, :title, :protocol, "
      ":output_path, :started_at, :finished_at, 'task_api')"
    )
    rows = (
      (users["alice"], "owner-a", "Alpha evening", "hls", "/media/a.ts", 1),
      (users["alice"], "owner-b", "Beta morning", "flv", "/media/b.flv", 2),
      (users["bob"], "owner-c", "Gamma evening", "hls", "/media/c.ts", 3),
      (None, "owner-d", "Legacy evening", "hls", "/media/d.ts", 4),
    )
    with self.engine.connect() as connection:
      for app_user_id, owner_user_id, title, protocol, output_path, hour in rows:
        connection.execute(insert, {
          "app_user_id": app_user_id,
          "owner_user_id": owner_user_id,
          "title": title,
          "protocol": protocol,
          "output_path": output_path,
          "started_at": "2026-08-25 {:02d}:00:00.000".format(hour),
          "finished_at": "2026-08-25 {:02d}:30:00.000".format(hour),
        })
      connection.commit()

    query = self._library()
    global_first = query.recordings(LibraryRecordingFilter.from_mapping({
      "sort": "finished_at", "order": "asc", "page_size": "2",
    }))
    global_second = query.recordings(LibraryRecordingFilter.from_mapping({
      "sort": "finished_at", "order": "asc", "page": "2", "page_size": "2",
    }))
    alice = query.recordings_for_user(
      users["alice"], LibraryRecordingFilter.from_mapping({}),
    )
    bob = query.recordings_for_user(
      users["bob"], LibraryRecordingFilter.from_mapping({}),
    )
    filtered = query.recordings_for_user(
      users["alice"],
      LibraryRecordingFilter.from_mapping({
        "q": "evening",
        "owner_user_id": "owner-a",
        "protocol": "hls",
      }),
    )

    self.assertEqual(4, global_first.total)
    self.assertEqual(4, global_second.total)
    self.assertEqual(
      ["/media/a.ts", "/media/b.flv", "/media/c.ts", "/media/d.ts"],
      [item["output_path"] for item in global_first.items + global_second.items],
    )
    self.assertEqual(2, alice.total)
    self.assertEqual({"/media/a.ts", "/media/b.flv"}, {
      item["output_path"] for item in alice.items
    })
    self.assertEqual(1, bob.total)
    self.assertEqual(["/media/c.ts"], [item["output_path"] for item in bob.items])
    self.assertEqual(1, filtered.total)
    self.assertEqual(["/media/a.ts"], [
      item["output_path"] for item in filtered.items
    ])


if __name__ == "__main__":
  unittest.main()
