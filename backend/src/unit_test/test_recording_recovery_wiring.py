##
## The production persistence protocol, in order.
##
## The crash this closes: media is durable on disk, and the process dies before
## ``recording_record`` has the row that makes it discoverable.  Publishing a
## journal note *before* the insert turns that into a recoverable state, and
## Phase 11B-0 guarantees replaying that note cannot create a duplicate.
##
## Order is the whole contract, so these assert sequences rather than call
## counts.  Three regions with different failure meanings:
##
##   prepare + key + publish   nothing has been catalogued; failing here must
##                             not reach the database at all
##   database insert           the journal stays, because that note is exactly
##                             what a later replay needs
##   acknowledge               the recording is already persisted; failing here
##                             must not undo a success
##
from datetime import datetime
import unittest

from backend.src.platform.douyin.douyin_live_downloader import LiveDownloadResult
from backend.src.service.live_recording_task import (
  PLATFORM_DOUYIN,
  SOURCE_TASK_API,
  LiveRecordingTaskService,
)
from backend.src.service.recording_resource import (
  RecordingPersistenceIntent,
  RecordingResourceService,
)
from backend.src.task.model import (
  TASK_STATE_PARTIAL,
  TASK_STATE_SUCCESS,
)
from backend.src.task.service import TaskService

KEY = "0123456789abcdef0123456789abcdef"
SOURCE_URL = "https://v.douyin.com/abc/"
RESOLVED_URL = "https://live.douyin.com/123456"


def recorded_result(**overrides):
  base = {
    "ok": True,
    "recorded": True,
    "room_status": 2,
    "room_id": "998877",
    "owner_user_id": "owner-1",
    "nickname": "Test Host",
    "title": "Launch title",
    "protocol": "hls",
    "output_path": "/media/douyin/live/A/live.mp4",
    "started_at": datetime(2026, 8, 30, 9, 0, 0),
    "finished_at": datetime(2026, 8, 30, 10, 0, 0),
  }
  base.update(overrides)
  return LiveDownloadResult(**base)


class _Log:
  def __init__(self):
    self.entries = []

  def note(self, entry):
    self.entries.append(entry)


class FakeDownloader:
  def __init__(self, result):
    self._result = result

  def run_with_result(self, token):
    return self._result


class FakeJournal:
  def __init__(self, log, *, publish_error=None, ack_error=None):
    self._log = log
    self._publish_error = publish_error
    self._ack_error = ack_error
    self.published = []
    self.acknowledged = []
    self.live = set()

  def publish(self, intent, recovery_key):
    self._log.note("journal-publish")
    self.published.append((intent, recovery_key))
    if self._publish_error is not None:
      raise self._publish_error
    self.live.add(recovery_key)
    return "/storage/.smsd-recording-recovery/{}.json".format(recovery_key)

  def acknowledge(self, recovery_key):
    self._log.note("journal-ack")
    self.acknowledged.append(recovery_key)
    if self._ack_error is not None:
      raise self._ack_error
    self.live.discard(recovery_key)


class SpyResourceService(RecordingResourceService):
  """The real prepare/record split, with the database stood in for."""

  def __init__(self, log, *, recording_id=73, db_error=None):
    super().__init__(repository_provider=lambda: None)
    self._log = log
    self._recording_id = recording_id
    self._db_error = db_error
    self.prepared = []
    self.persisted = []

  def prepare(self, result, **kwargs):
    self._log.note("prepare")
    intent = super().prepare(result, **kwargs)
    self.prepared.append(intent)
    return intent

  def record_prepared(self, intent, *, recovery_key=None):
    self._log.note("db-persist")
    self.persisted.append((intent, recovery_key))
    if self._db_error is not None:
      raise self._db_error
    return self._recording_id


class LoggingTaskService(TaskService):
  def __init__(self, log):
    super().__init__()
    self._log = log

  def finish_success(self, *args, **kwargs):
    self._log.note("task-finish-success")
    return super().finish_success(*args, **kwargs)

  def finish_partial(self, *args, **kwargs):
    self._log.note("task-finish-partial")
    return super().finish_partial(*args, **kwargs)


class InlineListenerItem:
  def __init__(self, func=None, args=None):
    self.func = func
    self.args = args

  def start_item(self):
    self.func(*self.args)


def run_persistence(
  *,
  result=None,
  app_user_id=41,
  publish_error=None,
  ack_error=None,
  db_error=None,
  keys=None,
):
  log = _Log()
  keys = list(keys if keys is not None else [KEY])
  generated = []

  def key_factory():
    log.note("key-generation")
    generated.append(keys[len(generated)])
    return generated[-1]

  tasks = LoggingTaskService(log)
  resource = SpyResourceService(log, db_error=db_error)
  journal = FakeJournal(log, publish_error=publish_error, ack_error=ack_error)
  downloader = FakeDownloader(
    result if result is not None else recorded_result()
  )
  service = LiveRecordingTaskService(
    task_service=tasks,
    downloader_factory=lambda: downloader,
    listener_factory=InlineListenerItem,
    recording_service=resource,
    recovery_journal=journal,
    recovery_key_factory=key_factory,
  )
  task_id = service.submit_tracked(
    resolved_url=RESOLVED_URL,
    source_url=SOURCE_URL,
    resolve_id="receipt-live-1",
    app_user_id=app_user_id,
  )
  return log, tasks, resource, journal, generated, task_id


class SuccessfulProtocolTest(unittest.TestCase):
  def test_the_persistence_protocol_runs_in_order(self):
    ##
    ## Every adjacent pair is load-bearing:
    ##   prepare -> key        : a key names an attempt to persist this intent
    ##   key -> publish        : the note carries the key it will be found by
    ##   publish -> db-persist : nothing is catalogued without a durable note
    ##   db-persist -> ack     : the note may only retire once the row exists
    ##   ack -> task-finish    : the task is not successful before all of it
    ##
    log, tasks, resource, journal, keys, task_id = run_persistence()

    self.assertEqual(
      [
        "prepare",
        "key-generation",
        "journal-publish",
        "db-persist",
        "journal-ack",
        "task-finish-success",
      ],
      log.entries,
    )

  def test_the_task_is_not_successful_before_the_protocol_completes(self):
    log, tasks, resource, journal, keys, task_id = run_persistence()

    for stage in ("journal-publish", "db-persist", "journal-ack"):
      self.assertLess(
        log.entries.index(stage),
        log.entries.index("task-finish-success"),
        "{} must precede success".format(stage),
      )

  def test_the_database_and_the_journal_receive_the_same_intent(self):
    ##
    ## One canonicalisation. If the wiring rebuilt the facts for the journal it
    ## would eventually disagree with the row, and a replay would restore a
    ## recording that differs from the one captured.
    ##
    log, tasks, resource, journal, keys, task_id = run_persistence()

    journalled_intent, journalled_key = journal.published[0]
    persisted_intent, persisted_key = resource.persisted[0]
    self.assertIs(journalled_intent, persisted_intent)
    self.assertIs(resource.prepared[0], journalled_intent)
    self.assertEqual(journalled_key, persisted_key)

  def test_the_generated_key_is_the_one_used_throughout(self):
    log, tasks, resource, journal, keys, task_id = run_persistence()

    self.assertEqual([KEY], keys)
    self.assertEqual(KEY, journal.published[0][1])
    self.assertEqual(KEY, resource.persisted[0][1])
    self.assertEqual([KEY], journal.acknowledged)

  def test_the_recording_is_reported_as_successful(self):
    log, tasks, resource, journal, keys, task_id = run_persistence()

    task = tasks.get_task(task_id)
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertEqual(73, task["metadata"]["result"]["recording_id"])

  def test_the_intent_carries_the_owner_and_the_platform(self):
    log, tasks, resource, journal, keys, task_id = run_persistence()

    intent = resource.prepared[0]
    self.assertIsInstance(intent, RecordingPersistenceIntent)
    self.assertEqual(41, intent.app_user_id)
    self.assertEqual(PLATFORM_DOUYIN, intent.platform)
    self.assertEqual(SOURCE_TASK_API, intent.source)
    self.assertEqual("/media/douyin/live/A/live.mp4", intent.output_path)


class JournalPublishFailureTest(unittest.TestCase):
  """Nothing may be catalogued without a durable note."""

  def run_failure(self, app_user_id=41):
    return run_persistence(
      app_user_id=app_user_id,
      publish_error=RuntimeError("journal storage unavailable"),
    )

  def test_the_database_is_never_reached(self):
    log, tasks, resource, journal, keys, task_id = self.run_failure()

    self.assertEqual(
      ["prepare", "key-generation", "journal-publish", "task-finish-partial"],
      log.entries,
    )
    self.assertEqual([], resource.persisted)
    self.assertEqual([], journal.acknowledged)

  def test_an_owned_recording_reports_persistence_failure(self):
    log, tasks, resource, journal, keys, task_id = self.run_failure()

    task = tasks.get_task(task_id)
    self.assertEqual(TASK_STATE_PARTIAL, task["state"])
    self.assertIsNone(task["metadata"]["result"].get("recording_id"))

  def test_an_unowned_recording_keeps_its_existing_best_effort_semantics(self):
    ##
    ## Nobody is waiting on a library entry for an anonymous recording, so it
    ## stays a successful recording with a warning - exactly as it behaved
    ## before a journal existed.
    ##
    log, tasks, resource, journal, keys, task_id = self.run_failure(
      app_user_id=None
    )

    task = tasks.get_task(task_id)
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertEqual([], resource.persisted)

  def test_the_media_result_is_still_reported(self):
    log, tasks, resource, journal, keys, task_id = self.run_failure()

    result = tasks.get_task(task_id)["metadata"]["result"]
    self.assertEqual("/media/douyin/live/A/live.mp4", result["output_path"])
    self.assertEqual("hls", result["protocol"])


class DatabaseFailureTest(unittest.TestCase):
  """The state Phase 11C exists to replay from."""

  def run_failure(self, app_user_id=41):
    return run_persistence(
      app_user_id=app_user_id,
      db_error=RuntimeError("mysql host unreachable"),
    )

  def test_the_journal_is_never_acknowledged(self):
    ##
    ## The note is the only remaining record that this media should be
    ## catalogued. Retiring it here would throw away the recovery input.
    ##
    log, tasks, resource, journal, keys, task_id = self.run_failure()

    self.assertEqual(
      [
        "prepare",
        "key-generation",
        "journal-publish",
        "db-persist",
        "task-finish-partial",
      ],
      log.entries,
    )
    self.assertEqual([], journal.acknowledged)

  def test_the_note_survives_under_its_original_key(self):
    log, tasks, resource, journal, keys, task_id = self.run_failure()

    self.assertEqual({KEY}, journal.live)
    self.assertEqual(KEY, journal.published[0][1])

  def test_an_owned_recording_reports_persistence_failure(self):
    log, tasks, resource, journal, keys, task_id = self.run_failure()

    self.assertEqual(TASK_STATE_PARTIAL, tasks.get_task(task_id)["state"])

  def test_an_unowned_recording_keeps_its_existing_semantics(self):
    log, tasks, resource, journal, keys, task_id = self.run_failure(
      app_user_id=None
    )

    self.assertEqual(TASK_STATE_SUCCESS, tasks.get_task(task_id)["state"])
    self.assertEqual({KEY}, journal.live)


class AcknowledgeFailureTest(unittest.TestCase):
  """A failure after the row exists must not undo the row.

  This is where Phase 11B-0 starts earning its keep: the note may survive, and
  replaying it later resolves to the recording that already exists rather than
  inserting a second one.
  """

  def run_failure(self):
    return run_persistence(
      ack_error=RuntimeError("journal directory unwritable")
    )

  def test_the_recording_is_still_successful(self):
    log, tasks, resource, journal, keys, task_id = self.run_failure()

    self.assertEqual(
      [
        "prepare",
        "key-generation",
        "journal-publish",
        "db-persist",
        "journal-ack",
        "task-finish-success",
      ],
      log.entries,
    )
    self.assertEqual(TASK_STATE_SUCCESS, tasks.get_task(task_id)["state"])

  def test_the_recording_id_is_still_reported(self):
    ##
    ## The row exists. Hiding its id because a cleanup step failed would make
    ## the recording unreachable for no reason.
    ##
    log, tasks, resource, journal, keys, task_id = self.run_failure()

    self.assertEqual(
      73, tasks.get_task(task_id)["metadata"]["result"]["recording_id"]
    )

  def test_the_database_row_is_not_rolled_back(self):
    log, tasks, resource, journal, keys, task_id = self.run_failure()

    self.assertEqual(1, len(resource.persisted))
    self.assertEqual(KEY, resource.persisted[0][1])

  def test_the_note_may_remain(self):
    ##
    ## Survivable rather than desirable: a later replay of this key resolves to
    ## the existing recording id.
    ##
    log, tasks, resource, journal, keys, task_id = self.run_failure()

    self.assertEqual({KEY}, journal.live)


class KeyGenerationTest(unittest.TestCase):
  def test_a_real_recording_generates_exactly_one_key(self):
    log, tasks, resource, journal, keys, task_id = run_persistence()

    self.assertEqual(1, len(keys))
    self.assertEqual(1, log.entries.count("key-generation"))

  def test_nothing_that_recorded_no_media_generates_a_key(self):
    ##
    ## A key names an attempt to persist a media resource. Generating one for a
    ## broadcast that was never captured would put a note in the journal for a
    ## recording that does not exist.
    ##
    for description, result in (
      ("test mode", LiveDownloadResult(
        ok=True, recorded=False, room_status=2, room_id="998877",
        nickname="Test Host", protocol="flv", test_mode=True,
      )),
      ("not recorded", LiveDownloadResult(
        ok=False, recorded=False, room_status=4, room_id="998877",
        nickname="Test Host", reason="当前未直播",
      )),
    ):
      with self.subTest(description=description):
        log, tasks, resource, journal, keys, task_id = run_persistence(
          result=result
        )

        self.assertEqual([], keys)
        self.assertEqual([], journal.published)
        self.assertEqual([], resource.persisted)
        self.assertNotIn("key-generation", log.entries)

  def test_the_key_is_generated_after_the_intent_is_known(self):
    ##
    ## Generated at the persistence boundary, not at the top of the run: a key
    ## produced before there is anything to persist would be spent on
    ## broadcasts that never recorded.
    ##
    log, tasks, resource, journal, keys, task_id = run_persistence()

    self.assertLess(
      log.entries.index("prepare"), log.entries.index("key-generation")
    )


class RecoveryKeyIsNotResultDataTest(unittest.TestCase):
  def test_the_key_never_reaches_the_download_result(self):
    log, tasks, resource, journal, keys, task_id = run_persistence()

    self.assertNotIn("recovery_key", LiveDownloadResult.__dataclass_fields__)

  def test_the_key_never_reaches_the_task_metadata(self):
    log, tasks, resource, journal, keys, task_id = run_persistence()

    metadata = tasks.get_task(task_id)["metadata"]
    self.assertNotIn("recovery_key", repr(metadata))
    self.assertNotIn(KEY, repr(metadata))


if __name__ == "__main__":
  unittest.main()
