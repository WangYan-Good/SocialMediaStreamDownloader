##
## Two workers, one crash, one note.
##
## A deployment runs more than one process against the same storage.  They all
## start at once after a restart, they all scan the same journal directory, and
## they all find the same pending note.  Nothing coordinates them - there is no
## lock file, no lease and no leader - because the coordination already exists
## in the one place it can be trusted: the database's unique constraint on
## ``recovery_key``.
##
## So the property under test is not "only one worker replays".  Both replay.
## The property is that two replays of one note produce one recording, and that
## whichever worker gets there second is not harmed by having lost.
##
## The barrier is load-bearing.  Without it one worker would finish and retire
## the note before the other had even read it, the second would find nothing,
## and the test would pass while proving only that sequential replay works.
##
from datetime import datetime
from pathlib import Path
import tempfile
import threading
import unittest

from backend.src.service.recording_recovery import RecordingRecoveryReconciler
from backend.src.service.recording_recovery_journal import (
  RecordingRecoveryJournal,
)
from backend.src.service.recording_resource import RecordingPersistenceIntent

KEY = "0123456789abcdef0123456789abcdef"


class UniqueKeyRepository:
  """A repository whose ``recovery_key`` is unique, as the real one's is.

  Stands in for the constraint, not for the database: the point of the real
  ``create_recording`` is that it inserts and lets the index decide, and what
  a caller observes either way is one id per key.
  """

  def __init__(self, barrier=None):
    self._lock = threading.Lock()
    self._barrier = barrier
    self.rows = {}
    self.inserts = 0
    self.next_id = 700

  def create_recording(self, record, recovery_key=None):
    ##
    ## Outside the lock, so both workers are genuinely inside this call at the
    ## same moment rather than queued behind one another.
    ##
    if self._barrier is not None:
      self._barrier.wait(timeout=10)
    with self._lock:
      self.inserts += 1
      if recovery_key in self.rows:
        return self.rows[recovery_key][0]
      self.next_id += 1
      self.rows[recovery_key] = (self.next_id, record)
      return self.next_id


class Worker:
  """One process's view of the shared storage: its own journal, its own reconciler."""

  def __init__(self, storage, repository):
    self.config = {"download": {"save_path": str(storage)}}
    self.journal = RecordingRecoveryJournal(config_loader=lambda: self.config)

    class Service:
      def record_prepared(self, intent, *, recovery_key=None):
        return repository.create_recording(
          intent.as_record(), recovery_key=recovery_key
        )

    self.service = Service()
    self.reconciler = RecordingRecoveryReconciler(
      journal=self.journal,
      recording_service=self.service,
      config_loader=lambda: self.config,
    )
    self.summary = None
    self.error = None

  def run(self):
    try:
      self.summary = self.reconciler.reconcile_once()
    except BaseException as e:  # pragma: no cover - a failure to report
      self.error = e


class ConcurrentReplayTest(unittest.TestCase):
  def setUp(self):
    self.storage = tempfile.TemporaryDirectory()
    self.addCleanup(self.storage.cleanup)
    self.root = Path(self.storage.name)
    media = self.root / "douyin" / "live" / "live.mp4"
    media.parent.mkdir(parents=True)
    media.write_bytes(b"recorded-bytes")

    self.intent = RecordingPersistenceIntent(
      app_user_id=41,
      platform="douyin",
      room_id="998877",
      owner_user_id="owner-1",
      title="Launch title",
      protocol="hls",
      output_path="douyin/live/live.mp4",
      started_at=datetime(2026, 8, 30, 9, 0, 0, 123000),
      finished_at=datetime(2026, 8, 30, 10, 0, 0, 456000),
      source="task_api",
    )
    RecordingRecoveryJournal(
      config_loader=lambda: {"download": {"save_path": str(self.root)}}
    ).publish(self.intent, KEY)

  def notes(self):
    directory = self.root / ".smsd-recording-recovery"
    if not directory.exists():
      return []
    return sorted(p.name for p in directory.iterdir() if p.name.endswith(".json"))

  def race(self):
    ##
    ## Two, because two is what proves it. The barrier admits exactly two
    ## workers, so neither can finish before the other has loaded the note.
    ##
    repository = UniqueKeyRepository(barrier=threading.Barrier(2))
    workers = [Worker(self.root, repository) for _ in range(2)]
    threads = [threading.Thread(target=worker.run) for worker in workers]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join(timeout=30)
    for worker in workers:
      if worker.error is not None:
        raise worker.error
    return repository, workers

  def test_both_workers_replay_the_same_note(self):
    ##
    ## The premise. If this fails the rest of the file is proving nothing,
    ## because only one worker ever reached the repository.
    ##
    repository, workers = self.race()

    self.assertEqual(2, repository.inserts)

  def test_two_concurrent_replays_produce_one_recording(self):
    repository, workers = self.race()

    self.assertEqual(1, len(repository.rows))

  def test_both_workers_are_told_the_same_recording_id(self):
    ##
    ## The loser is not given an error and not given a second id. It is given
    ## the recording that already exists, which is the honest answer: the note
    ## it replayed is now in the database.
    ##
    repository, workers = self.race()

    self.assertEqual([1, 1], [worker.summary.recovered for worker in workers])
    self.assertEqual(1, len(set(row[0] for row in repository.rows.values())))

  def test_the_note_ends_up_retired_exactly_once(self):
    ##
    ## Both acknowledge. One removes the file and the other finds it already
    ## gone, which is success rather than an error - nothing is owed to a
    ## caller who asked twice.
    ##
    repository, workers = self.race()

    self.assertEqual([], self.notes())

  def test_neither_worker_reports_a_failure(self):
    repository, workers = self.race()

    for worker in workers:
      self.assertEqual(0, worker.summary.retained)
      self.assertEqual(0, worker.summary.conflicted)
      self.assertEqual(0, worker.summary.corrupt)


class LateWorkerTest(unittest.TestCase):
  """A worker that arrives after the note is already gone."""

  def setUp(self):
    self.storage = tempfile.TemporaryDirectory()
    self.addCleanup(self.storage.cleanup)
    self.root = Path(self.storage.name)
    media = self.root / "douyin" / "live" / "live.mp4"
    media.parent.mkdir(parents=True)
    media.write_bytes(b"recorded-bytes")
    self.config = {"download": {"save_path": str(self.root)}}

  def test_a_worker_that_scans_a_note_another_already_retired_does_nothing(self):
    journal = RecordingRecoveryJournal(config_loader=lambda: self.config)
    journal.publish(
      RecordingPersistenceIntent(
        app_user_id=None,
        platform="douyin",
        room_id="1",
        owner_user_id=None,
        title=None,
        protocol="hls",
        output_path="douyin/live/live.mp4",
        started_at=None,
        finished_at=None,
        source="task_api",
      ),
      KEY,
    )
    repository = UniqueKeyRepository()

    class Service:
      def record_prepared(self, intent, *, recovery_key=None):
        return repository.create_recording(
          intent.as_record(), recovery_key=recovery_key
        )

    reconciler = RecordingRecoveryReconciler(
      journal=journal, recording_service=Service(), config_loader=lambda: self.config
    )
    ##
    ## The note is retired between the scan and the load - the exact window a
    ## second worker races through.
    ##
    real_scan = journal.scan_pending_keys

    def scan_then_lose_the_note(*args, **kwargs):
      pending = real_scan(*args, **kwargs)
      journal.acknowledge(KEY)
      return pending

    journal.scan_pending_keys = scan_then_lose_the_note
    summary = reconciler.reconcile_once()

    self.assertEqual(1, summary.discovered)
    self.assertEqual(0, summary.recovered)
    self.assertEqual(0, summary.retained)
    self.assertEqual(0, repository.inserts)


if __name__ == "__main__":
  unittest.main()
