##
## Reconciliation against a real database, a real unique constraint and a real
## foreign key.
##
## Everything about this replay that matters is enforced by MySQL and not by
## Python.  "Two workers replaying one note produce one recording" is the
## behaviour of ``uq_recording_record_recovery_key``; "an owner that no longer
## exists is refused rather than downgraded" is the behaviour of the foreign
## key on ``app_user_id``.  A fake cursor agrees with whatever it is told and
## SQLite enforces different rules, so neither is evidence for either claim.
##
## Disposable databases only.  Each run creates its own, migrates it to head,
## and drops it - nothing here ever addresses a real deployment.
##
from pathlib import Path
import os
import tempfile
import threading
import unittest
import uuid

from alembic import command
import sqlalchemy as sa

from backend.src.database.migration import make_alembic_config
from backend.src.service.recording_recovery import RecordingRecoveryReconciler
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
    "Automatic reconciliation is only meaningful against a real unique "
    "constraint and a real foreign key, which nothing else in the suite can "
    "stand in for."
  )


class FakeResult:
  """A finished recording, as the downloader would report it."""

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


@unittest.skipUnless(DSN, "set SMSD_TEST_MYSQL_DSN to run MySQL recovery tests")
class RecordingRecoveryReconciliationTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    no_network.permit_real_connections()
    cls.database_name = "smsd_reconcile_{}".format(uuid.uuid4().hex[:12])
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
    self.root = Path(self.storage.name)
    self.config = {"download": {"save_path": str(self.root)}}

  ##
  ## >>------------------------------ fixtures ------------------------------<<
  ##
  def media(self, relative="douyin/live/A/live.mp4", content=b"recorded-bytes"):
    target = self.root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target

  def journal(self):
    return RecordingRecoveryJournal(config_loader=lambda: self.config)

  def table(self):
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

    database_name = self.database_name

    def get_connection():
      import pymysql

      return _Ctx(pymysql.connect(
        host=url.host,
        port=url.port or 3306,
        user=url.username,
        password=url.password,
        database=database_name,
        autocommit=False,
      ))

    table.get_connection = get_connection
    return table

  def resource(self):
    table = self.table()
    return RecordingResourceService(repository_provider=lambda: table)

  def reconciler(self, journal=None, resource=None):
    return RecordingRecoveryReconciler(
      journal=journal if journal is not None else self.journal(),
      recording_service=resource if resource is not None else self.resource(),
      config_loader=lambda: self.config,
    )

  def intent_for(self, path="douyin/live/A/live.mp4", app_user_id=None):
    return self.resource().prepare(
      FakeResult(path),
      app_user_id=app_user_id,
      platform="douyin",
      source="task_api",
    )

  def rows_for(self, key):
    with self.engine.connect() as connection:
      return connection.execute(sa.text(
        "SELECT recording_id, output_path, app_user_id FROM recording_record "
        "WHERE recovery_key = :key"
      ), {"key": key}).all()

  def total_rows(self):
    with self.engine.connect() as connection:
      return connection.execute(
        sa.text("SELECT COUNT(*) FROM recording_record")
      ).scalar()

  def notes(self):
    directory = self.root / ".smsd-recording-recovery"
    if not directory.exists():
      return []
    return sorted(p.name for p in directory.iterdir() if p.name.endswith(".json"))

  ##
  ## >>=========================== A. journal only ===========================>>
  ##
  def test_a_pending_note_becomes_a_recording(self):
    ##
    ## The crash this whole line of work exists for: media on disk, a durable
    ## note, and no row. After one reconciliation the library can see it.
    ##
    self.media()
    key = uuid.uuid4().hex
    self.journal().publish(self.intent_for(), key)

    summary = self.reconciler().reconcile_once()

    self.assertEqual(1, summary.recovered)
    rows = self.rows_for(key)
    self.assertEqual(1, len(rows))
    self.assertEqual("douyin/live/A/live.mp4", rows[0][1])
    self.assertEqual([], self.notes())

  def test_reconciling_twice_does_not_produce_a_second_recording(self):
    ##
    ## The note is gone after the first run, so the second finds nothing. This
    ## is the ordinary restart, and it must be free.
    ##
    self.media()
    self.journal().publish(self.intent_for(), uuid.uuid4().hex)

    self.reconciler().reconcile_once()
    second = self.reconciler().reconcile_once()

    self.assertEqual(0, second.discovered)
    self.assertEqual(1, self.total_rows())

  ##
  ## >>=========================== B. row + journal ==========================>>
  ##
  def test_a_note_that_outlived_its_insert_resolves_to_the_same_recording(self):
    ##
    ## The process died between the commit and the acknowledgement. Replaying
    ## the surviving note must answer with the recording that is already there
    ## - the unique constraint decides, not a lookup this code performs.
    ##
    self.media()
    key = uuid.uuid4().hex
    intent = self.intent_for()
    self.journal().publish(intent, key)
    first_id = self.resource().record_prepared(intent, recovery_key=key)

    summary = self.reconciler().reconcile_once()

    self.assertEqual(1, summary.recovered)
    rows = self.rows_for(key)
    self.assertEqual(1, len(rows))
    self.assertEqual(first_id, rows[0][0])
    self.assertEqual(1, self.total_rows())
    self.assertEqual([], self.notes())

  ##
  ## >>============================= C. conflict =============================>>
  ##
  def test_a_note_naming_different_media_is_refused_and_retained(self):
    ##
    ## One recovery identity names one recording. The stored row is left
    ## exactly as it was, nothing is reassigned, and the note stays as the
    ## evidence an operator needs.
    ##
    self.media("douyin/live/A/first.mp4")
    self.media("douyin/live/A/second.mp4")
    key = uuid.uuid4().hex
    stored = self.intent_for("douyin/live/A/first.mp4")
    stored_id = self.resource().record_prepared(stored, recovery_key=key)
    ##
    ## A note under the same key describing different media - a reused key or
    ## a corrupted note, either way not a replay of the stored recording.
    ##
    self.journal().publish(self.intent_for("douyin/live/A/second.mp4"), key)

    summary = self.reconciler().reconcile_once()

    self.assertEqual(1, summary.conflicted)
    self.assertEqual(0, summary.recovered)
    rows = self.rows_for(key)
    self.assertEqual(1, len(rows))
    self.assertEqual(stored_id, rows[0][0])
    self.assertEqual("douyin/live/A/first.mp4", rows[0][1])
    self.assertEqual(["{}.json".format(key)], self.notes())

  ##
  ## >>=========================== D. two workers ============================>>
  ##
  def test_two_workers_replaying_one_note_produce_one_recording(self):
    ##
    ## Both processes start after the restart, both scan, both find the note,
    ## and both insert. The barrier makes that simultaneous rather than
    ## sequential - without it one would finish and retire the note before the
    ## other read it, and this would prove nothing.
    ##
    self.media()
    key = uuid.uuid4().hex
    self.journal().publish(self.intent_for(), key)

    barrier = threading.Barrier(2, timeout=30)
    results = []
    errors = []

    def worker():
      try:
        resource = self.resource()
        real = resource.record_prepared

        def synchronised(intent, *, recovery_key=None):
          barrier.wait()
          return real(intent, recovery_key=recovery_key)

        resource.record_prepared = synchronised
        results.append(self.reconciler(resource=resource).reconcile_once())
      except BaseException as e:  # pragma: no cover - reported below
        errors.append(e)
        try:
          barrier.abort()
        except BaseException:
          pass

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join(timeout=60)

    self.assertEqual([], [type(e).__name__ for e in errors])
    self.assertEqual(2, len(results))
    self.assertEqual([1, 1], [one.recovered for one in results])
    ##
    ## One row, one id, and no note - whichever worker lost the insert was
    ## handed the winner's recording rather than an error.
    ##
    self.assertEqual(1, len(self.rows_for(key)))
    self.assertEqual(1, self.total_rows())
    self.assertEqual([], self.notes())

  ##
  ## >>========================== E. deleted owner ===========================>>
  ##
  def test_a_note_for_an_owner_that_does_not_exist_is_retained(self):
    ##
    ## The foreign key refuses the insert. The one repair that must never be
    ## attempted is retrying without the owner: that would silently turn an
    ## owned recording into one anybody can see, and ownership uncertainty is
    ## not fixable by downgrading the owner.
    ##
    ## The note stays, unaltered, for a human to resolve.
    ##
    self.media()
    key = uuid.uuid4().hex
    missing_owner = 987654321
    self.journal().publish(self.intent_for(app_user_id=missing_owner), key)

    summary = self.reconciler().reconcile_once()

    self.assertEqual(0, summary.recovered)
    self.assertEqual(1, summary.retained)
    self.assertEqual(0, self.total_rows())
    self.assertEqual(["{}.json".format(key)], self.notes())

  def test_a_rejected_owner_is_never_stored_as_anonymous(self):
    self.media()
    self.journal().publish(self.intent_for(app_user_id=987654321), uuid.uuid4().hex)

    self.reconciler().reconcile_once()

    with self.engine.connect() as connection:
      anonymous = connection.execute(sa.text(
        "SELECT COUNT(*) FROM recording_record WHERE app_user_id IS NULL"
      )).scalar()
    self.assertEqual(0, anonymous)

  def test_a_rejected_owner_does_not_stop_the_other_notes(self):
    self.media("douyin/live/A/good.mp4")
    self.media("douyin/live/A/bad.mp4")
    good_key = uuid.uuid4().hex
    bad_key = uuid.uuid4().hex
    self.journal().publish(
      self.intent_for("douyin/live/A/bad.mp4", app_user_id=987654321), bad_key
    )
    self.journal().publish(self.intent_for("douyin/live/A/good.mp4"), good_key)

    summary = self.reconciler().reconcile_once()

    self.assertEqual(2, summary.discovered)
    self.assertEqual(1, summary.recovered)
    self.assertEqual(1, len(self.rows_for(good_key)))
    self.assertEqual(["{}.json".format(bad_key)], self.notes())

  ##
  ## >>=========================== the media gate ============================>>
  ##
  def test_a_note_whose_media_is_gone_never_reaches_the_database(self):
    ##
    ## Proved here as well as offline, because this is the assertion that the
    ## gate runs *before* the insert rather than merely existing.
    ##
    key = uuid.uuid4().hex
    self.media()
    self.journal().publish(self.intent_for(), key)
    (self.root / "douyin" / "live" / "A" / "live.mp4").unlink()

    summary = self.reconciler().reconcile_once()

    self.assertEqual(1, summary.missing)
    self.assertEqual(0, self.total_rows())
    self.assertEqual(["{}.json".format(key)], self.notes())


if __name__ == "__main__":
  unittest.main()
