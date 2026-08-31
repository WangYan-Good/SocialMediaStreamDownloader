##
## Replaying the notes a crash left behind.
##
## Phase 11B made the handoff durable and stopped there: a note survives, and
## nothing ever reads it back.  This is what closes that gap - discover the
## notes that are present, prove the media they describe is still there, hand
## the *same* persistence intent to the same repository the ordinary path uses,
## and only then retire the note.
##
## Two things it is deliberately not.  It is not a scanner of media: the only
## trusted recovery input is a note this server published, never a file found
## by walking the download directory and guessing who owns it.  And it is not
## part of recording: ``LiveRecordingTaskService`` handles new recordings and
## this handles the handoff a dead process left, which is a different lifetime.
##
## Every failure below has the same shape - no database mutation, the note
## stays, the run continues.  A note is evidence, and this phase never destroys
## evidence it could not act on.
##
from datetime import datetime
from pathlib import Path
import json
import multiprocessing
import os
import tempfile
import unittest
from unittest import mock

from backend.src.database.table.recording_record import RecordingRecoveryConflict
from backend.src.service.recording_recovery import RecordingRecoveryReconciler
from backend.src.service import recording_recovery_journal as journal_module
from backend.src.service.recording_recovery_journal import (
  JOURNAL_SCHEMA_VERSION,
  payload_for,
  RecordingJournalScanOverflow,
  RecordingRecoveryJournal,
)
from backend.src.service.recording_resource import (
  RecordingPersistenceIntent,
  RecordingPersistenceUnavailable,
)

KEY = "0123456789abcdef0123456789abcdef"


def key_for(value):
  return "{:032x}".format(value)


class FakeRecordingService:
  """The repository side, reduced to what a replay is allowed to touch.

  ``prepare`` raises on purpose. A replay reads a journal, not a
  ``LiveDownloadResult``; anything that reached for ``prepare`` here would be
  fabricating a download result and re-deriving fields the note already holds.
  """

  def __init__(self, ids=None, error=None):
    self.calls = []
    self._ids = list(ids or [])
    self._error = error
    self._next = 900

  def prepare(self, *args, **kwargs):
    raise AssertionError("a replay must not call prepare()")

  def record(self, *args, **kwargs):
    raise AssertionError("a replay must not call record()")

  def record_prepared(self, intent, *, recovery_key=None):
    self.calls.append((intent, recovery_key))
    if self._error is not None:
      raise self._error
    if self._ids:
      return self._ids.pop(0)
    self._next += 1
    return self._next


def _reconcile_fifo_batch_in_child(root, connection):
  """Run the real FIFO isolation path behind a parent-enforced watchdog."""
  config = {"download": {"save_path": str(root)}}
  journal = RecordingRecoveryJournal(config_loader=lambda: config)
  service = FakeRecordingService(ids=[88])
  try:
    summary = RecordingRecoveryReconciler(
      journal=journal,
      recording_service=service,
      config_loader=lambda: config,
    ).reconcile_once()
    connection.send({
      "error": None,
      "calls": [call[1] for call in service.calls],
      "recovered": summary.recovered,
      "retained": summary.retained,
    })
  except BaseException as error:
    connection.send({"error": type(error).__name__})
  finally:
    connection.close()


class Fixture(unittest.TestCase):
  """A real journal on a real filesystem, beside real media."""

  def setUp(self):
    self.storage = tempfile.TemporaryDirectory()
    self.addCleanup(self.storage.cleanup)
    self.root = Path(self.storage.name)
    self.config = {"download": {"save_path": str(self.root)}}
    self.journal = RecordingRecoveryJournal(config_loader=lambda: self.config)

  def media(self, relative="douyin/live/live.mp4", content=b"recorded-bytes"):
    target = self.root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target

  def intent(self, **overrides):
    base = {
      "app_user_id": 41,
      "platform": "douyin",
      "room_id": "998877",
      "owner_user_id": "owner-1",
      "title": "Launch title",
      "protocol": "hls",
      "output_path": "douyin/live/live.mp4",
      "started_at": datetime(2026, 8, 30, 9, 0, 0, 123000),
      "finished_at": datetime(2026, 8, 30, 10, 0, 0, 456000),
      "source": "task_api",
    }
    base.update(overrides)
    return RecordingPersistenceIntent(**base)

  def publish(self, key=KEY, **overrides):
    intent = self.intent(**overrides)
    self.journal.publish(intent, key)
    return intent

  def write_note(self, key, payload=None, *, raw=None):
    """A note placed directly, for shapes ``publish`` would refuse to write."""
    directory = self.journal.ensure_root()
    target = directory / "{}.json".format(key)
    if raw is not None:
      target.write_bytes(raw)
    else:
      target.write_text(json.dumps(payload), encoding="utf-8")
    return target

  def reconciler(self, service):
    return RecordingRecoveryReconciler(
      journal=self.journal,
      recording_service=service,
      config_loader=lambda: self.config,
    )

  def notes(self):
    directory = self.root / ".smsd-recording-recovery"
    if not directory.exists():
      return []
    return sorted(p.name for p in directory.iterdir() if p.name.endswith(".json"))


class ReplayTest(Fixture):
  """The state Phase 11C exists to close: a durable note and no row."""

  def test_a_pending_note_with_valid_media_is_replayed(self):
    self.media()
    published = self.publish()
    service = FakeRecordingService(ids=[77])

    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(1, len(service.calls))
    self.assertEqual(1, summary.recovered)
    self.assertEqual(1, summary.discovered)
    self.assertEqual(1, summary.attempted)

  def test_the_journalled_intent_is_replayed_verbatim(self):
    ##
    ## The note *is* the canonical persistence intent. Nothing here re-trims,
    ## re-normalises or re-derives a field: the ordinary path and a replay must
    ## write the same row, and two copies of the normalisation rules eventually
    ## disagree.
    ##
    self.media()
    published = self.publish()
    service = FakeRecordingService()

    self.reconciler(service).reconcile_once()

    replayed, key = service.calls[0]
    self.assertEqual(published, replayed)
    self.assertEqual(KEY, key)

  def test_the_recovery_key_is_the_one_the_note_was_published_under(self):
    ##
    ## Without it the insert is an ordinary insert, and a second restart would
    ## create a second row for one broadcast.
    ##
    self.media()
    self.publish(key=key_for(5))
    service = FakeRecordingService()

    self.reconciler(service).reconcile_once()

    self.assertEqual(key_for(5), service.calls[0][1])

  def test_a_replayed_note_is_acknowledged(self):
    self.media()
    self.publish()
    service = FakeRecordingService()

    self.reconciler(service).reconcile_once()

    self.assertEqual([], self.notes())
    self.assertIsNone(self.journal.load(KEY))

  def test_an_existing_row_resolves_to_the_same_recording(self):
    ##
    ## Phase 11B-0's create-or-get, reached through the same call. No SELECT
    ## first and no second idempotency rule here: two workers replaying one
    ## note can both pass a lookup, and only the database constraint decides.
    ##
    self.media()
    self.publish()
    service = FakeRecordingService(ids=[404])

    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(1, len(service.calls))
    self.assertEqual(1, summary.recovered)
    self.assertEqual([], self.notes())

  def test_several_notes_are_replayed_in_key_order(self):
    ##
    ## Deterministic, so a failing restart is reproducible and a log can be
    ## read against a directory listing.
    ##
    for value in (3, 1, 2):
      self.media("douyin/live/{}.mp4".format(value))
      self.publish(
        key=key_for(value), output_path="douyin/live/{}.mp4".format(value)
      )
    service = FakeRecordingService()

    self.reconciler(service).reconcile_once()

    self.assertEqual(
      [key_for(1), key_for(2), key_for(3)],
      [call[1] for call in service.calls],
    )

  def test_nothing_pending_touches_the_database(self):
    service = FakeRecordingService()

    summary = self.reconciler(service).reconcile_once()

    self.assertEqual([], service.calls)
    self.assertEqual(0, summary.discovered)

  def test_reconciling_an_untouched_storage_root_creates_nothing(self):
    service = FakeRecordingService()

    self.reconciler(service).reconcile_once()

    self.assertEqual([], sorted(p.name for p in self.root.iterdir()))


class AcknowledgeIsLastTest(Fixture):
  """The order is load, then media, then the row, then the note."""

  def test_a_failed_insert_leaves_the_note_in_place(self):
    ##
    ## The note is the input a later restart replays from. Retiring it on a
    ## failure would turn a recoverable state into a permanently lost one.
    ##
    self.media()
    self.publish()
    service = FakeRecordingService(error=RuntimeError("insert exploded"))

    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(["{}.json".format(KEY)], self.notes())
    self.assertEqual(0, summary.recovered)
    self.assertEqual(1, summary.retained)

  def test_the_media_is_proved_before_the_database_is_told(self):
    ##
    ## The gate is load-bearing, not decoration: ``load`` proves what the note
    ## says, and only the filesystem can prove the recording still exists.
    ##
    self.publish()

    service = FakeRecordingService()
    summary = self.reconciler(service).reconcile_once()

    self.assertEqual([], service.calls)
    self.assertEqual(1, summary.missing)
    self.assertEqual(["{}.json".format(KEY)], self.notes())


class MissingNoteRaceTest(Fixture):
  """Another worker got there first."""

  def test_a_note_that_vanished_between_scan_and_load_is_skipped(self):
    ##
    ## Two processes starting together both scan, and one acknowledges before
    ## the other loads. That is the protocol working, not a fault.
    ##
    self.media()
    self.publish()
    service = FakeRecordingService()
    reconciler = self.reconciler(service)

    real_load = self.journal.load

    def load_after_removal(key):
      self.journal.acknowledge(key)
      return real_load(key)

    self.journal.load = load_after_removal
    summary = reconciler.reconcile_once()

    self.assertEqual([], service.calls)
    self.assertEqual(0, summary.recovered)
    self.assertEqual(0, summary.retained)


class MediaGateTest(Fixture):
  """A note describes a recording; the filesystem decides whether it still exists."""

  def test_missing_media_is_not_catalogued(self):
    self.publish()

    summary = self.reconciler(FakeRecordingService()).reconcile_once()

    self.assertEqual(1, summary.missing)
    self.assertEqual(1, summary.retained)
    self.assertEqual(["{}.json".format(KEY)], self.notes())

  def test_zero_byte_media_is_not_catalogued(self):
    ##
    ## The note says a recording completed. An empty file is a reservation, a
    ## truncated write or a placeholder - cataloguing it would advertise a
    ## playable resource that is not there.
    ##
    self.media(content=b"")
    self.publish()

    service = FakeRecordingService()
    summary = self.reconciler(service).reconcile_once()

    self.assertEqual([], service.calls)
    self.assertEqual(1, summary.missing)
    self.assertEqual(["{}.json".format(KEY)], self.notes())

  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_media_replaced_by_a_symlink_is_not_catalogued(self):
    ##
    ## The link points at a real, non-empty file inside the storage root, so
    ## following it would succeed. The recorder writes a regular file; a link
    ## where the recording should be means something else chose what is about
    ## to be catalogued.
    ##
    real = self.media("douyin/live/real.mp4")
    self.publish()
    (self.root / "douyin" / "live" / "live.mp4").symlink_to(real)

    service = FakeRecordingService()
    summary = self.reconciler(service).reconcile_once()

    self.assertEqual([], service.calls)
    self.assertEqual(1, summary.missing)
    self.assertEqual(["{}.json".format(KEY)], self.notes())

  def test_a_directory_where_the_media_should_be_is_not_catalogued(self):
    (self.root / "douyin" / "live" / "live.mp4").mkdir(parents=True)
    self.publish()

    service = FakeRecordingService()

    self.reconciler(service).reconcile_once()

    self.assertEqual([], service.calls)


class OneBadNoteIsolationTest(Fixture):
  """A note this build cannot read must not stop the ones after it."""

  def prepare_three(self, broken):
    for value in (1, 3):
      self.media("douyin/live/{}.mp4".format(value))
      self.publish(
        key=key_for(value), output_path="douyin/live/{}.mp4".format(value)
      )
    broken(key_for(2))

  def test_a_malformed_note_between_two_valid_ones_is_skipped(self):
    self.prepare_three(
      lambda key: self.write_note(key, raw=b"{not json at all")
    )
    service = FakeRecordingService()

    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(
      [key_for(1), key_for(3)], [call[1] for call in service.calls]
    )
    self.assertEqual(2, summary.recovered)
    self.assertEqual(1, summary.corrupt)
    self.assertEqual(["{}.json".format(key_for(2))], self.notes())

  def test_an_unsupported_version_between_two_valid_ones_is_skipped(self):
    ##
    ## A note written by a build this one does not understand. Refusing is the
    ## only safe answer - a field may have changed meaning - and refusing must
    ## not cost the notes that follow it.
    ##
    def unsupported(key):
      payload = payload_for(self.intent(), key)
      payload["schema_version"] = JOURNAL_SCHEMA_VERSION + 1
      self.write_note(key, payload)

    self.prepare_three(unsupported)
    service = FakeRecordingService()

    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(
      [key_for(1), key_for(3)], [call[1] for call in service.calls]
    )
    self.assertEqual(1, summary.corrupt)
    self.assertEqual(["{}.json".format(key_for(2))], self.notes())

  def test_a_note_whose_media_vanished_does_not_stop_the_others(self):
    for value in (1, 3):
      self.media("douyin/live/{}.mp4".format(value))
      self.publish(
        key=key_for(value), output_path="douyin/live/{}.mp4".format(value)
      )
    self.media("douyin/live/2.mp4")
    self.publish(key=key_for(2), output_path="douyin/live/2.mp4")
    (self.root / "douyin" / "live" / "2.mp4").unlink()

    service = FakeRecordingService()
    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(2, summary.recovered)
    self.assertEqual(1, summary.missing)
    self.assertEqual(["{}.json".format(key_for(2))], self.notes())


class ConflictTest(Fixture):
  """One recovery identity names one recording, or nothing happens."""

  def test_a_conflicting_note_is_neither_acknowledged_nor_reassigned(self):
    self.media()
    self.publish()
    service = FakeRecordingService(
      error=RecordingRecoveryConflict("key already names different media")
    )

    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(1, summary.conflicted)
    self.assertEqual(0, summary.recovered)
    self.assertEqual(["{}.json".format(KEY)], self.notes())

  def test_a_conflict_does_not_stop_the_run(self):
    self.media("douyin/live/1.mp4")
    self.publish(key=key_for(1), output_path="douyin/live/1.mp4")
    self.media("douyin/live/2.mp4")
    self.publish(key=key_for(2), output_path="douyin/live/2.mp4")

    class ConflictOnFirst(FakeRecordingService):
      def record_prepared(self, intent, *, recovery_key=None):
        self.calls.append((intent, recovery_key))
        if recovery_key == key_for(1):
          raise RecordingRecoveryConflict("differs")
        return 12

    service = ConflictOnFirst()
    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(
      [key_for(1), key_for(2)], [call[1] for call in service.calls]
    )
    self.assertEqual(1, summary.recovered)
    self.assertEqual(["{}.json".format(key_for(1))], self.notes())


class OwnershipTest(Fixture):
  """An owner that no longer exists is never downgraded to nobody."""

  def test_a_rejected_owner_is_not_replayed_as_anonymous(self):
    ##
    ## The database refuses the note's ``app_user_id`` - user deleted since the
    ## recording. Retrying without the owner would silently hand an owned
    ## recording to everybody, and ownership uncertainty is never repaired by
    ## downgrading the owner. The note stays; a human decides.
    ##
    self.media()
    self.publish(app_user_id=17)
    service = FakeRecordingService(
      error=RuntimeError("Cannot add or update a child row: foreign key")
    )

    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(1, len(service.calls))
    self.assertEqual(17, service.calls[0][0].app_user_id)
    self.assertEqual(0, summary.recovered)
    self.assertEqual(["{}.json".format(KEY)], self.notes())

  def test_a_rejected_owner_does_not_stop_the_run(self):
    self.media("douyin/live/1.mp4")
    self.publish(
      key=key_for(1), output_path="douyin/live/1.mp4", app_user_id=17
    )
    self.media("douyin/live/2.mp4")
    self.publish(key=key_for(2), output_path="douyin/live/2.mp4")

    class RefuseFirstOwner(FakeRecordingService):
      def record_prepared(self, intent, *, recovery_key=None):
        self.calls.append((intent, recovery_key))
        if intent.app_user_id == 17:
          raise RuntimeError("foreign key constraint fails")
        return 21

    service = RefuseFirstOwner()
    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(1, summary.recovered)
    self.assertEqual(["{}.json".format(key_for(1))], self.notes())


class DatabaseUnavailableTest(Fixture):
  """A repository that is down is not a per-note problem."""

  def test_an_unavailable_repository_defers_the_whole_run(self):
    ##
    ## Every remaining note would fail identically, so trying each one in turn
    ## only means a starting server hammers a database that is already down.
    ##
    for value in (1, 2, 3):
      self.media("douyin/live/{}.mp4".format(value))
      self.publish(
        key=key_for(value), output_path="douyin/live/{}.mp4".format(value)
      )
    service = FakeRecordingService(
      error=RecordingPersistenceUnavailable("repository is unavailable")
    )

    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(1, len(service.calls))
    self.assertEqual(3, summary.deferred)
    self.assertEqual(3, summary.retained)
    self.assertEqual(0, summary.recovered)

  def test_every_note_survives_an_unavailable_repository(self):
    for value in (1, 2, 3):
      self.media("douyin/live/{}.mp4".format(value))
      self.publish(
        key=key_for(value), output_path="douyin/live/{}.mp4".format(value)
      )
    service = FakeRecordingService(
      error=RecordingPersistenceUnavailable("repository is unavailable")
    )

    self.reconciler(service).reconcile_once()

    self.assertEqual(
      ["{}.json".format(key_for(value)) for value in (1, 2, 3)], self.notes()
    )

  def test_reconciliation_never_raises_into_its_caller(self):
    ##
    ## Whatever happens here, the application it runs inside must still come
    ## up. An exception escaping would take the SPA and every unrelated API
    ## down with it.
    ##
    self.media()
    self.publish()

    class Exploding(FakeRecordingService):
      def record_prepared(self, intent, *, recovery_key=None):
        raise MemoryError("something unexpected")

    self.reconciler(Exploding()).reconcile_once()

    self.assertEqual(["{}.json".format(KEY)], self.notes())


class AcknowledgeFailureTest(Fixture):
  """A row that exists stays; only the note is in doubt."""

  def test_a_failed_acknowledgement_does_not_undo_the_recording(self):
    ##
    ## The insert committed. Rolling it back or deleting the row would throw
    ## away the recovery this run just achieved, and a surviving note replayed
    ## under the same key resolves to this same recording anyway.
    ##
    self.media()
    self.publish()
    service = FakeRecordingService(ids=[55])

    def refuse(key):
      raise OSError("read-only filesystem")

    self.journal.acknowledge = refuse
    summary = self.reconciler(service).reconcile_once()

    self.assertEqual(1, summary.recovered)
    self.assertEqual(1, len(service.calls))
    self.assertEqual(["{}.json".format(KEY)], self.notes())


class UnreadableJournalDirectoryTest(Fixture):
  """Recovery can be unavailable without the server being unavailable."""

  @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
  def test_a_symlinked_journal_directory_yields_an_empty_run(self):
    elsewhere = self.root / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "{}.json".format(KEY)).write_text("{}")
    (self.root / ".smsd-recording-recovery").symlink_to(elsewhere)

    service = FakeRecordingService()
    summary = self.reconciler(service).reconcile_once()

    self.assertEqual([], service.calls)
    self.assertEqual(0, summary.discovered)

  def test_an_unconfigured_storage_root_yields_an_empty_run(self):
    self.config = {"download": {}}
    service = FakeRecordingService()

    summary = self.reconciler(service).reconcile_once()

    self.assertEqual([], service.calls)
    self.assertEqual(0, summary.discovered)


class LoggingTest(Fixture):
  """A log line names the note and the failure, never the recording."""

  def capture(self):
    from unittest import mock

    from backend.src.service import recording_recovery

    logger = mock.MagicMock()
    return mock.patch.object(
      recording_recovery, "get_logger", lambda: logger
    ), logger

  def test_a_refusal_does_not_log_the_payload(self):
    self.write_note(KEY, raw=b"{not json")
    patched, logger = self.capture()
    with patched:
      self.reconciler(FakeRecordingService()).reconcile_once()

    logged = " ".join(
      str(call) for call in logger.error.call_args_list + logger.info.call_args_list
    )
    self.assertIn(KEY[:8], logged)
    self.assertNotIn(KEY, logged)
    self.assertNotIn(str(self.root), logged)

  def test_a_missing_media_refusal_does_not_log_the_path(self):
    self.publish(title="a very secret stream title")
    patched, logger = self.capture()
    with patched:
      self.reconciler(FakeRecordingService()).reconcile_once()

    logged = " ".join(
      str(call) for call in logger.error.call_args_list + logger.info.call_args_list
    )
    self.assertNotIn("douyin/live/live.mp4", logged)
    self.assertNotIn("a very secret stream title", logged)


class ScanOverflowIsolationTest(unittest.TestCase):
  """An oversized directory is a safe degraded startup, never a partial replay."""

  def test_overflow_performs_no_load_database_or_ack_work(self):
    calls = []

    class OverflowJournal:
      def scan_pending_keys(self, *args, **kwargs):
        calls.append("scan")
        raise RecordingJournalScanOverflow("bounded scan overflow")

      def load(self, *args, **kwargs):
        calls.append("load")
        raise AssertionError("overflow must not return a partial batch")

      def acknowledge(self, *args, **kwargs):
        calls.append("ack")
        raise AssertionError("overflow must not acknowledge a note")

    service = FakeRecordingService()
    reconciler = RecordingRecoveryReconciler(
      journal=OverflowJournal(),
      recording_service=service,
      config_loader=lambda: {"download": {"save_path": "/unused"}},
    )

    summary = reconciler.reconcile_once()

    self.assertEqual(["scan"], calls)
    self.assertEqual([], service.calls)
    self.assertEqual(0, summary.discovered)
    self.assertEqual(0, summary.attempted)


class RealScanOverflowIsolationTest(Fixture):
  def test_overflow_cannot_turn_a_discovered_prefix_into_database_work(self):
    self.media()
    self.publish()
    service = FakeRecordingService()

    class Entries:
      def __init__(self):
        self.entries = iter((
          type("Entry", (), {"name": "{}.json".format(KEY)})(),
          type("Entry", (), {"name": "README"})(),
        ))

      def __enter__(self):
        return self

      def __exit__(self, *unused):
        return False

      def __iter__(self):
        return self.entries

    with mock.patch.object(journal_module, "MAX_RECOVERY_SCAN_ENTRIES", 1), \
         mock.patch.object(journal_module.os, "scandir", return_value=Entries()):
      summary = self.reconciler(service).reconcile_once()

    self.assertEqual([], service.calls)
    self.assertEqual(0, summary.attempted)
    self.assertEqual(["{}.json".format(KEY)], self.notes())


class FairBatchReconciliationTest(Fixture):
  """Scheduling rotates retained notes without changing recovery authority."""

  def test_retained_prefix_yields_to_later_valid_notes_on_the_next_start(self):
    keys = [key_for(value) for value in range(1, 5)]
    for index, key in enumerate(keys, start=1):
      relative = "douyin/live/{}.mp4".format(index)
      if index > 2:
        self.media(relative)
      self.publish(key=key, output_path=relative)
    service = FakeRecordingService()

    with mock.patch(
      "backend.src.service.recording_recovery.MAX_RECOVERY_JOURNALS_PER_RUN", 2
    ):
      first = self.reconciler(service).reconcile_once()
      second = self.reconciler(service).reconcile_once()

    self.assertEqual(2, first.missing)
    self.assertEqual(0, first.recovered)
    self.assertEqual(2, second.recovered)
    self.assertEqual(keys[2:4], [call[1] for call in service.calls])
    self.assertEqual(
      ["{}.json".format(keys[0]), "{}.json".format(keys[1])],
      self.notes(),
    )

  @unittest.skipUnless(hasattr(os, "mkfifo"), "requires named pipes")
  def test_canonical_fifo_is_retained_and_does_not_poison_a_later_note(self):
    fifo_key = key_for(1)
    valid_key = key_for(2)
    directory = self.journal.ensure_root()
    fifo = directory / "{}.json".format(fifo_key)
    os.mkfifo(fifo)
    self.media("douyin/live/valid.mp4")
    self.publish(key=valid_key, output_path="douyin/live/valid.mp4")
    context = multiprocessing.get_context("fork")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(
      target=_reconcile_fifo_batch_in_child,
      args=(self.root, child),
    )
    process.start()
    child.close()
    process.join(timeout=2.0)
    hung = process.is_alive()
    if hung:
      process.terminate()
      process.join(timeout=5.0)
    if process.is_alive():
      process.kill()
      process.join(timeout=5.0)

    self.assertFalse(hung, "a canonical FIFO blocked the reconciliation batch")
    self.assertTrue(parent.poll(0.5), "the reconciliation child returned no result")
    result = parent.recv()
    parent.close()
    self.assertIsNone(result["error"])
    self.assertEqual([valid_key], result["calls"])
    self.assertEqual(1, result["recovered"])
    self.assertEqual(1, result["retained"])
    self.assertTrue(fifo.exists())
    self.assertEqual(["{}.json".format(fifo_key)], self.notes())

  def test_database_unavailable_keeps_all_notes_despite_cursor_advance(self):
    keys = [key_for(value) for value in range(1, 4)]
    for index, key in enumerate(keys, start=1):
      relative = "douyin/live/{}.mp4".format(index)
      self.media(relative)
      self.publish(key=key, output_path=relative)

    unavailable = FakeRecordingService(
      error=RecordingPersistenceUnavailable("database unavailable")
    )
    with mock.patch(
      "backend.src.service.recording_recovery.MAX_RECOVERY_JOURNALS_PER_RUN", 2
    ):
      first = self.reconciler(unavailable).reconcile_once()
      notes_after_unavailable = self.notes()
      available = FakeRecordingService()
      second = self.reconciler(available).reconcile_once()

    self.assertEqual(2, first.deferred)
    self.assertEqual(3, len(notes_after_unavailable))
    self.assertEqual([keys[2], keys[0]], [call[1] for call in available.calls])
    self.assertEqual(2, second.recovered)
    self.assertEqual(["{}.json".format(keys[1])], self.notes())


if __name__ == "__main__":
  unittest.main()
