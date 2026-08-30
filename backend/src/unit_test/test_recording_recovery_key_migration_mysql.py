##
## The recovery key against a real MySQL.
##
## Everything this file proves is a property of the database, not of Python:
## whether a unique index permits many NULLs, whether it refuses a second
## non-NULL duplicate, whether two independent connections racing the same
## insert can both win, and whether the column survives an upgrade and comes
## back cleanly after a downgrade.
##
## A fake cursor cannot disagree with invalid DDL, and SQLite enforces
## different rules - neither is evidence for the constraint this design rests
## on.  Skipped when no database is reachable so the ordinary suite stays
## offline, and required in CI so the skip cannot quietly become permanent.
##
import os
import threading
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
    "The recovery key unique constraint is the concurrency authority for "
    "replay idempotency, and only a real MySQL can prove it holds."
  )

RECOVERY_INDEX = "uq_recording_record_recovery_key"


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


##
## The schema fixture, shared by both suites below.
##
## A plain mixin rather than a base TestCase on purpose: inheriting from a
## TestCase would make every subclass re-run its parent's tests, and the
## migration tests assume a schema the idempotency tests have already moved.
##
class _RecoveryKeySchemaFixture:
  @classmethod
  def setUpClass(cls):
    no_network.permit_real_connections()
    cls.database_name = "smsd_recovery_{}".format(uuid.uuid4().hex[:12])
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

  def setUp(self):
    ##
    ## Each test starts from an empty schema so an upgrade/downgrade in one
    ## cannot decide the outcome of another.
    ##
    ## Driven from the server-level engine, and the schema engine is disposed
    ## afterwards: a pooled connection still bound to the dropped database
    ## would come back with nothing selected.
    ##
    with self.server.connect() as connection:
      connection.execute(sa.text(
        "DROP DATABASE IF EXISTS `{}`".format(self.database_name)
      ))
      connection.execute(sa.text(
        "CREATE DATABASE `{}` CHARACTER SET utf8mb4 "
        "COLLATE utf8mb4_0900_ai_ci".format(self.database_name)
      ))
      connection.commit()
    self.engine.dispose()

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

  def columns(self):
    inspector = sa.inspect(self.engine)
    return {c["name"]: c for c in inspector.get_columns("recording_record")}

  def indexes(self):
    inspector = sa.inspect(self.engine)
    return {i["name"]: i for i in inspector.get_indexes("recording_record")}

  def insert_recording(self, connection, recovery_key=None, output_path=None):
    connection.execute(
      sa.text(
        "INSERT INTO recording_record "
        "(app_user_id, platform, output_path, source, recovery_key) "
        "VALUES (NULL, 'douyin', :path, 'task_api', :key)"
      ),
      {
        "path": output_path or "/media/live/{}.ts".format(uuid.uuid4().hex[:8]),
        "key": recovery_key,
      },
    )


@unittest.skipUnless(DSN, "set SMSD_TEST_MYSQL_DSN to run MySQL migration tests")
class RecordingRecoveryKeyMigrationTest(_RecoveryKeySchemaFixture, unittest.TestCase):
  """The column, the constraint, and the upgrade/downgrade roundtrip."""

  ##
  ## >>================================ shape ================================>>
  ##
  def test_the_upgrade_adds_a_nullable_recovery_key(self):
    self.upgrade("0011_recording_recovery_key")

    column = self.columns()["recovery_key"]
    self.assertTrue(column["nullable"])
    ##
    ## Fixed width, so the stored value is exactly the identity and not a
    ## padded or truncated version of it.
    ##
    self.assertEqual(32, getattr(column["type"], "length", None))

  def test_the_recovery_key_index_is_unique(self):
    self.upgrade("0011_recording_recovery_key")

    index = self.indexes()[RECOVERY_INDEX]
    self.assertTrue(index["unique"])
    self.assertEqual(["recovery_key"], index["column_names"])

  def test_the_collation_is_case_sensitive(self):
    ##
    ## Load-bearing. Under a case-insensitive collation two keys differing only
    ## in case would collide, and the constraint would refuse a replay that is
    ## not one.
    ##
    self.upgrade("0011_recording_recovery_key")

    with self.engine.connect() as connection:
      collation = connection.execute(sa.text(
        "SELECT COLLATION_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = 'recording_record' "
        "AND COLUMN_NAME = 'recovery_key'"
      ), {"schema": self.database_name}).scalar()
    self.assertEqual("ascii_bin", collation)

  ##
  ## >>============================== history ==============================>>
  ##
  def test_rows_written_before_the_migration_survive_with_a_null_key(self):
    self.upgrade("0010_rbac_role_foundation")
    with self.engine.connect() as connection:
      connection.execute(sa.text(
        "INSERT INTO recording_record "
        "(app_user_id, platform, output_path, source) "
        "VALUES (NULL, 'douyin', '/media/live/legacy.ts', 'direct')"
      ))
      connection.commit()

    self.upgrade("0011_recording_recovery_key")

    with self.engine.connect() as connection:
      row = connection.execute(sa.text(
        "SELECT output_path, recovery_key FROM recording_record"
      )).one()
    self.assertEqual("/media/live/legacy.ts", row[0])
    ##
    ## Not backfilled. Nothing about an existing row can establish a recovery
    ## identity a later replay could be trusted to match.
    ##
    self.assertIsNone(row[1])

  def test_many_rows_may_have_no_recovery_key(self):
    ##
    ## MySQL permits repeated NULLs under a unique index, which is what keeps
    ## ordinary recordings - every one written today - legal.
    ##
    self.upgrade("0011_recording_recovery_key")

    with self.engine.connect() as connection:
      for _ in range(5):
        self.insert_recording(connection, recovery_key=None)
      connection.commit()
      total = connection.execute(sa.text(
        "SELECT COUNT(*) FROM recording_record WHERE recovery_key IS NULL"
      )).scalar()
    self.assertEqual(5, total)

  ##
  ## >>=============================== unique ===============================>>
  ##
  def test_a_duplicate_non_null_recovery_key_is_refused_by_the_database(self):
    self.upgrade("0011_recording_recovery_key")
    key = uuid.uuid4().hex

    with self.engine.connect() as connection:
      self.insert_recording(connection, recovery_key=key)
      connection.commit()

    with self.engine.connect() as connection:
      with self.assertRaises(IntegrityError):
        self.insert_recording(connection, recovery_key=key)
        connection.commit()

    with self.engine.connect() as connection:
      total = connection.execute(sa.text(
        "SELECT COUNT(*) FROM recording_record WHERE recovery_key = :key"
      ), {"key": key}).scalar()
    self.assertEqual(1, total)

  def test_two_different_recovery_keys_coexist(self):
    self.upgrade("0011_recording_recovery_key")

    with self.engine.connect() as connection:
      self.insert_recording(connection, recovery_key=uuid.uuid4().hex)
      self.insert_recording(connection, recovery_key=uuid.uuid4().hex)
      connection.commit()
      total = connection.execute(sa.text(
        "SELECT COUNT(*) FROM recording_record WHERE recovery_key IS NOT NULL"
      )).scalar()
    self.assertEqual(2, total)

  ##
  ## >>============================= roundtrip =============================>>
  ##
  def test_downgrade_removes_the_column_and_the_index(self):
    self.upgrade("0011_recording_recovery_key")
    with self.engine.connect() as connection:
      self.insert_recording(connection, recovery_key=uuid.uuid4().hex)
      connection.commit()

    self.downgrade("0010_rbac_role_foundation")

    self.assertNotIn("recovery_key", self.columns())
    self.assertNotIn(RECOVERY_INDEX, self.indexes())
    ##
    ## The recordings themselves are untouched by losing their recovery
    ## identity - they are still resources, just no longer replay-addressable.
    ##
    with self.engine.connect() as connection:
      total = connection.execute(sa.text(
        "SELECT COUNT(*) FROM recording_record"
      )).scalar()
    self.assertEqual(1, total)

  def test_a_full_roundtrip_ends_where_it_started(self):
    ##
    ## 0010 -> 0011 -> 0010 -> 0011, which is what an operator does when a
    ## deployment is rolled back and then rolled forward again.
    ##
    self.upgrade("0010_rbac_role_foundation")
    self.assertNotIn("recovery_key", self.columns())

    self.upgrade("0011_recording_recovery_key")
    self.assertIn("recovery_key", self.columns())

    self.downgrade("0010_rbac_role_foundation")
    self.assertNotIn("recovery_key", self.columns())

    self.upgrade("0011_recording_recovery_key")
    self.assertIn("recovery_key", self.columns())
    self.assertTrue(self.indexes()[RECOVERY_INDEX]["unique"])

  def test_the_migrated_schema_matches_the_canonical_model(self):
    ##
    ## The comparison the operator CLI runs. If the ORM model did not carry
    ## recovery_key, a deployed database would report drift against its own
    ## managed schema - and the fix for that must be to teach the model, never
    ## to exclude the column from the comparison.
    ##
    from backend.src.database.schema_compare import compare_managed_schema

    self.upgrade()

    report = compare_managed_schema(self.engine)
    recording = [
      d for d in report.errors if getattr(d, "table", None) == "recording_record"
    ]
    self.assertEqual([], recording)
    self.assertTrue(report.is_compatible)

  def test_the_head_is_the_recovery_key_revision(self):
    self.upgrade()
    with self.engine.connect() as connection:
      heads = connection.execute(
        sa.text("SELECT version_num FROM alembic_version")
      ).scalars().all()
    self.assertEqual(["0011_recording_recovery_key"], heads)


@unittest.skipUnless(DSN, "set SMSD_TEST_MYSQL_DSN to run MySQL migration tests")
class RecordingRecoveryIdempotencyTest(_RecoveryKeySchemaFixture, unittest.TestCase):
  """Replay through the real repository, against the real constraint.

  Inherits the schema fixture; every test here starts on 0011 with the
  repository pointed at it.
  """

  def setUp(self):
    super().setUp()
    self.upgrade("0011_recording_recovery_key")
    self.table = self.repository()

  def repository(self):
    from backend.src.database.table.recording_record import RecordingRecordTable

    url = sa.engine.make_url(DSN)
    table = object.__new__(RecordingRecordTable)
    table.require_write_ready = lambda: None

    class _Ctx:
      def __init__(self, connection):
        self.connection = connection

      def __enter__(self):
        return self.connection

      def __exit__(self, *args):
        self.connection.close()
        return False

    def get_connection():
      import pymysql

      return _Ctx(pymysql.connect(
        host=url.host,
        port=url.port or 3306,
        user=url.username,
        password=url.password,
        database=self.database_name,
        autocommit=False,
      ))

    table.get_connection = get_connection
    return table

  def record(self, **overrides):
    base = {
      "app_user_id": None,
      "platform": "douyin",
      "room_id": "room-x",
      "owner_user_id": "owner-x",
      "title": "Live title",
      "protocol": "hls",
      "output_path": "/media/live/room.mp4",
      "started_at": None,
      "finished_at": None,
      "source": "task_api",
    }
    base.update(overrides)
    return base

  def count(self, key):
    with self.engine.connect() as connection:
      return connection.execute(sa.text(
        "SELECT COUNT(*) FROM recording_record WHERE recovery_key = :key"
      ), {"key": key}).scalar()

  def test_replaying_a_key_returns_the_first_id_without_inserting(self):
    key = uuid.uuid4().hex

    first = self.table.create_recording(self.record(), recovery_key=key)
    second = self.table.create_recording(self.record(), recovery_key=key)

    self.assertEqual(first, second)
    self.assertEqual(1, self.count(key))

  def test_replaying_many_times_stays_one_resource(self):
    key = uuid.uuid4().hex
    ids = {
      self.table.create_recording(self.record(), recovery_key=key)
      for _ in range(5)
    }
    self.assertEqual(1, len(ids))
    self.assertEqual(1, self.count(key))

  def test_without_a_key_two_identical_recordings_stay_two_resources(self):
    ##
    ## One execution, one resource. Two broadcasts that happen to look alike
    ## are still two recordings, and deduplicating them would lose one.
    ##
    first = self.table.create_recording(self.record())
    second = self.table.create_recording(self.record())

    self.assertNotEqual(first, second)
    with self.engine.connect() as connection:
      total = connection.execute(sa.text(
        "SELECT COUNT(*) FROM recording_record WHERE recovery_key IS NULL"
      )).scalar()
    self.assertEqual(2, total)

  def test_a_key_naming_different_media_is_a_conflict(self):
    from backend.src.database.table.recording_record import (
      RecordingRecoveryConflict,
    )

    key = uuid.uuid4().hex
    self.table.create_recording(
      self.record(output_path="/media/live/a.mp4"), recovery_key=key
    )

    with self.assertRaises(RecordingRecoveryConflict):
      self.table.create_recording(
        self.record(output_path="/media/live/b.mp4"), recovery_key=key
      )

    ##
    ## Neither silently accepted nor silently inserted.
    ##
    self.assertEqual(1, self.count(key))
    with self.engine.connect() as connection:
      stored = connection.execute(sa.text(
        "SELECT output_path FROM recording_record WHERE recovery_key = :key"
      ), {"key": key}).scalar()
    self.assertEqual("/media/live/a.mp4", stored)

  def test_a_key_naming_a_different_owner_is_a_conflict(self):
    from backend.src.database.table.recording_record import (
      RecordingRecoveryConflict,
    )

    key = uuid.uuid4().hex
    self.table.create_recording(self.record(), recovery_key=key)

    with self.assertRaises(RecordingRecoveryConflict):
      self.table.create_recording(
        self.record(owner_user_id="somebody-else"), recovery_key=key
      )

  def test_an_invalid_owner_still_fails_the_foreign_key(self):
    ##
    ## The duplicate branch must not swallow unrelated integrity failures. A
    ## recording attributed to a user who does not exist has to fail, key or
    ## no key.
    ##
    key = uuid.uuid4().hex
    with self.assertRaises(Exception) as caught:
      self.table.create_recording(
        self.record(app_user_id=987654321), recovery_key=key
      )
    self.assertNotIn("RecordingRecoveryConflict", type(caught.exception).__name__)
    self.assertEqual(0, self.count(key))

  def make_app_users(self, *usernames):
    """Real ``app_user`` rows, because ``app_user_id`` carries a foreign key."""
    ids = {}
    with self.engine.connect() as connection:
      for username in usernames:
        connection.execute(
          sa.text(
            "INSERT INTO app_user (username, password_hash) "
            "VALUES (:username, 'x')"
          ),
          {"username": username},
        )
        ids[username] = connection.execute(
          sa.text("SELECT user_id FROM app_user WHERE username = :username"),
          {"username": username},
        ).scalar()
      connection.commit()
    return ids

  def stored(self, key, column):
    with self.engine.connect() as connection:
      return connection.execute(
        sa.text(
          "SELECT {} FROM recording_record WHERE recovery_key = :key".format(column)
        ),
        {"key": key},
      ).scalar()

  ##
  ## >>=================== ownership and identity isolation ===================>>
  ##
  ## ``app_user_id`` is application ownership; ``owner_user_id`` is the
  ## platform's broadcaster identity.  They are different facts, and only the
  ## first decides whose library a recording appears in - so a replay that
  ## crosses it is the one failure here that could hand one user's recording to
  ## another.  A corrupted journal, a reused key, or a bug upstream must never
  ## be resolved as "already recorded".
  ##
  def test_same_recovery_key_cannot_cross_app_user(self):
    from backend.src.database.table.recording_record import (
      RecordingRecoveryConflict,
    )

    users = self.make_app_users("recovery-alice", "recovery-bob")
    alice, bob = users["recovery-alice"], users["recovery-bob"]
    key = uuid.uuid4().hex

    first = self.table.create_recording(
      self.record(app_user_id=alice), recovery_key=key
    )

    with self.assertRaises(RecordingRecoveryConflict):
      self.table.create_recording(
        self.record(app_user_id=bob), recovery_key=key
      )

    ##
    ## Not resolved as an idempotent replay, and not inserted as a second row.
    ## The stored recording still belongs to whoever actually made it.
    ##
    self.assertEqual(1, self.count(key))
    self.assertEqual(alice, self.stored(key, "app_user_id"))
    self.assertEqual(
      first, self.stored(key, "recording_id")
    )

  def test_same_recovery_key_cannot_cross_platform(self):
    from backend.src.database.table.recording_record import (
      RecordingRecoveryConflict,
    )

    key = uuid.uuid4().hex
    self.table.create_recording(self.record(platform="douyin"), recovery_key=key)

    with self.assertRaises(RecordingRecoveryConflict):
      self.table.create_recording(
        self.record(platform="other"), recovery_key=key
      )

    self.assertEqual(1, self.count(key))
    self.assertEqual("douyin", self.stored(key, "platform"))

  def test_same_recovery_key_cannot_cross_source(self):
    from backend.src.database.table.recording_record import (
      RecordingRecoveryConflict,
    )

    key = uuid.uuid4().hex
    self.table.create_recording(
      self.record(source="task_api"), recovery_key=key
    )

    with self.assertRaises(RecordingRecoveryConflict):
      self.table.create_recording(
        self.record(source="direct"), recovery_key=key
      )

    self.assertEqual(1, self.count(key))
    self.assertEqual("task_api", self.stored(key, "source"))

  def test_an_owned_recording_still_replays_idempotently(self):
    ##
    ## The other side of the guard: the same owner replaying the same recording
    ## is still one resource, so the isolation check has not made ordinary
    ## replay stricter than it should be.
    ##
    users = self.make_app_users("recovery-carol")
    carol = users["recovery-carol"]
    key = uuid.uuid4().hex

    first = self.table.create_recording(
      self.record(app_user_id=carol), recovery_key=key
    )
    second = self.table.create_recording(
      self.record(app_user_id=carol), recovery_key=key
    )

    self.assertEqual(first, second)
    self.assertEqual(1, self.count(key))

  def test_two_connections_racing_the_same_key_resolve_to_one_resource(self):
    ##
    ## The point of putting uniqueness in the database. Both threads open their
    ## own connection and neither holds a process-local lock, so if the
    ## constraint were not the authority both inserts would land.
    ##
    key = uuid.uuid4().hex
    results = []
    errors = []
    start = threading.Barrier(2, timeout=15)

    def replay():
      table = self.repository()
      try:
        start.wait()
        results.append(table.create_recording(self.record(), recovery_key=key))
      except Exception as e:
        errors.append(e)

    threads = [threading.Thread(target=replay) for _ in range(2)]
    for t in threads:
      t.start()
    for t in threads:
      t.join(timeout=30)

    self.assertEqual([], errors)
    self.assertEqual(2, len(results))
    self.assertEqual(1, len(set(results)))
    self.assertEqual(1, self.count(key))


if __name__ == "__main__":
  unittest.main()
