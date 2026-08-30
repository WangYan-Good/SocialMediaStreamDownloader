##
## The handoff, end to end, against a real database and a real filesystem.
##
## Everything else in Phase 11B proves one half at a time: the journal writes
## durably, or the wiring calls things in the right order against stand-ins.
## This proves the two halves fit - a note published on disk, a keyed row in
## MySQL, and the note retired only once the row exists.
##
## It also demonstrates the state Phase 11C will replay from, without building
## the scanner: a row that already exists and a note that survived because the
## process died before acknowledgement.  Replaying that note has to answer with
## the recording that is already there rather than creating a second one, and
## only a real unique constraint can show it.
##
import os
import tempfile
import unittest
import uuid

from alembic import command
import sqlalchemy as sa

from backend.src.database.migration import make_alembic_config
from backend.src.service.recording_recovery_journal import (
  RecordingRecoveryJournal,
)
from backend.src.service.recording_resource import RecordingResourceService
from backend.src.unit_test import no_network


DSN = os.environ.get("SMSD_TEST_MYSQL_DSN")
REQUIRED = os.environ.get("SMSD_REQUIRE_MYSQL_TESTS") == "1"

if REQUIRED and not DSN:
  raise RuntimeError(
    "SMSD_REQUIRE_MYSQL_TESTS=1 but SMSD_TEST_MYSQL_DSN is not set. "
    "The recovery handoff is only meaningful against a real unique "
    "constraint, which nothing else in the suite can stand in for."
  )


class FakeResult:
  """A finished recording, as the downloader would report it.

  ``output_path`` is root-relative: a journal note may only describe media
  inside the configured storage root, and this suite runs against a temporary
  one.
  """

  def __init__(self, output_path, app_user_id=None):
    self.ok = True
    self.recorded = True
    self.test_mode = False
    self.room_id = "998877"
    self.owner_user_id = "owner-1"
    self.title = "Launch title"
    self.protocol = "hls"
    self.output_path = output_path
    self.started_at = None
    self.finished_at = None
    self.app_user_id = app_user_id


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


@unittest.skipUnless(DSN, "set SMSD_TEST_MYSQL_DSN to run MySQL handoff tests")
class RecordingRecoveryHandoffTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    no_network.permit_real_connections()
    cls.database_name = "smsd_handoff_{}".format(uuid.uuid4().hex[:12])
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
    config = make_alembic_config(
      _config_for(cls.database_name), cls.database_name
    )
    config.attributes["engine"] = cls.engine
    command.upgrade(config, "head")

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
    with self.engine.connect() as connection:
      connection.execute(sa.text("DELETE FROM recording_record"))
      connection.commit()
    self.storage = tempfile.TemporaryDirectory()
    self.addCleanup(self.storage.cleanup)

  def journal(self):
    return RecordingRecoveryJournal(
      config_loader=lambda: {"download": {"save_path": self.storage.name}}
    )

  def resource(self):
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
    return RecordingResourceService(repository_provider=lambda: table)

  def rows_for(self, key):
    with self.engine.connect() as connection:
      return connection.execute(sa.text(
        "SELECT recording_id, output_path, app_user_id FROM recording_record "
        "WHERE recovery_key = :key"
      ), {"key": key}).all()

  ##
  ## >>=============================== handoff ===============================>>
  ##
  def test_the_full_handoff_publishes_persists_and_retires(self):
    journal = self.journal()
    resource = self.resource()
    key = uuid.uuid4().hex
    intent = resource.prepare(
      FakeResult("douyin/live/A/live.mp4"),
      app_user_id=None,
      platform="douyin",
      source="task_api",
    )

    published = journal.publish(intent, key)
    self.assertTrue(published.is_file())

    recording_id = resource.record_prepared(intent, recovery_key=key)
    self.assertIsInstance(recording_id, int)

    journal.acknowledge(key)

    ##
    ## One row, and no note left describing work that is already done.
    ##
    rows = self.rows_for(key)
    self.assertEqual(1, len(rows))
    self.assertEqual(recording_id, rows[0][0])
    self.assertEqual("douyin/live/A/live.mp4", rows[0][1])
    self.assertFalse(published.exists())
    self.assertIsNone(journal.load(key))

  def test_the_row_carries_the_key_the_note_was_published_under(self):
    journal = self.journal()
    resource = self.resource()
    key = uuid.uuid4().hex
    intent = resource.prepare(
      FakeResult("douyin/live/A/live.mp4"),
      app_user_id=None, platform="douyin", source="task_api",
    )

    journal.publish(intent, key)
    resource.record_prepared(intent, recovery_key=key)

    with self.engine.connect() as connection:
      stored = connection.execute(sa.text(
        "SELECT recovery_key FROM recording_record"
      )).scalar()
    self.assertEqual(key, stored)

  ##
  ## >>========================= crash after commit =========================>>
  ##
  def test_a_note_that_outlived_its_insert_replays_to_the_same_recording(self):
    ##
    ## The exact state a crash between the insert and the acknowledgement
    ## leaves behind: the row exists and the note is still on disk. This is
    ## what Phase 11C will find, and replaying it must resolve to the recording
    ## that is already there.
    ##
    ## Not a scanner - the key is addressed directly. What is being shown is
    ## that the replay primitive works end to end.
    ##
    journal = self.journal()
    resource = self.resource()
    key = uuid.uuid4().hex
    intent = resource.prepare(
      FakeResult("douyin/live/A/live.mp4"),
      app_user_id=None, platform="douyin", source="task_api",
    )

    published = journal.publish(intent, key)
    first_id = resource.record_prepared(intent, recovery_key=key)
    ##
    ## ... and here the process dies, before acknowledge.
    ##

    self.assertTrue(published.is_file())

    ##
    ## Restart: a fresh service reads the surviving note and replays it.
    ##
    restarted_journal = self.journal()
    restarted_resource = self.resource()
    replayed_intent = restarted_journal.load(key)
    self.assertEqual(intent, replayed_intent)

    replayed_id = restarted_resource.record_prepared(
      replayed_intent, recovery_key=key
    )

    self.assertEqual(first_id, replayed_id)
    self.assertEqual(1, len(self.rows_for(key)))

    ##
    ## Only now is the note retired, and the state is identical to the one a
    ## clean run would have produced.
    ##
    restarted_journal.acknowledge(key)
    self.assertIsNone(restarted_journal.load(key))
    self.assertEqual(1, len(self.rows_for(key)))

  def test_replaying_many_times_still_yields_one_recording(self):
    journal = self.journal()
    resource = self.resource()
    key = uuid.uuid4().hex
    intent = resource.prepare(
      FakeResult("douyin/live/A/live.mp4"),
      app_user_id=None, platform="douyin", source="task_api",
    )
    journal.publish(intent, key)

    ids = {
      resource.record_prepared(journal.load(key), recovery_key=key)
      for _ in range(4)
    }

    self.assertEqual(1, len(ids))
    self.assertEqual(1, len(self.rows_for(key)))

  def test_a_note_for_a_different_recording_is_refused_not_merged(self):
    ##
    ## Ownership and identity still hold across the handoff: a note whose facts
    ## disagree with the stored row is a conflict, not an idempotent replay.
    ##
    from backend.src.database.table.recording_record import (
      RecordingRecoveryConflict,
    )

    journal = self.journal()
    resource = self.resource()
    key = uuid.uuid4().hex
    first = resource.prepare(
      FakeResult("douyin/live/A/first.mp4"),
      app_user_id=None, platform="douyin", source="task_api",
    )
    journal.publish(first, key)
    resource.record_prepared(first, recovery_key=key)

    second = resource.prepare(
      FakeResult("douyin/live/A/second.mp4"),
      app_user_id=None, platform="douyin", source="task_api",
    )
    with self.assertRaises(RecordingRecoveryConflict):
      resource.record_prepared(second, recovery_key=key)

    rows = self.rows_for(key)
    self.assertEqual(1, len(rows))
    self.assertEqual("douyin/live/A/first.mp4", rows[0][1])


if __name__ == "__main__":
  unittest.main()
