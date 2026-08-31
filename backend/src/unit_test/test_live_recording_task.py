import contextlib
import io
import logging
import unittest
from datetime import datetime
from unittest.mock import patch

from backend.src.platform.douyin.douyin_live_downloader import LiveDownloadResult
from backend.src.platform.douyin.hls_recorder import HlsCancelled
from backend.src.platform.douyin.douyin_listener import ListenerItem
from backend.src.service import live_recording_task as task_module
from backend.src.service.live_recording_task import (
  PLATFORM_DOUYIN,
  SOURCE_DIRECT,
  SOURCE_TASK_API,
  LiveRecordingTaskService,
)
from backend.src.service.recording_resource import RecordingResourceService
from backend.src.task.model import (
  TASK_STATE_CANCELLED,
  TASK_STATE_FAILED,
  TASK_STATE_PENDING,
  TASK_STATE_PARTIAL,
  TASK_STATE_RUNNING,
  TASK_STATE_SUCCESS,
  TASK_TYPE_LIVE_RECORD,
)
from backend.src.task.service import TaskService

SOURCE_URL = "https://v.douyin.com/abc/"
RESOLVED_URL = "https://live.douyin.com/123456"


def token(url=SOURCE_URL, resolved_url=RESOLVED_URL, **extra):
  built = {"url": url, "resolved_url": resolved_url}
  built.update(extra)
  return built


def recorded_result(protocol="flv", output_path="/media/douyin/live/A/live.flv"):
  return LiveDownloadResult(
    ok=True,
    recorded=True,
    room_status=2,
    room_id="998877",
    owner_user_id="owner-1",
    nickname="Test Host",
    title="Launch title",
    protocol=protocol,
    output_path=output_path,
    started_at=datetime(2026, 8, 25, 9, 0, 0),
    finished_at=datetime(2026, 8, 25, 10, 0, 0),
  )


def make_test_mode_result():
  return LiveDownloadResult(
    ok=True,
    recorded=False,
    room_status=2,
    room_id="998877",
    nickname="Test Host",
    protocol="flv",
    test_mode=True,
  )


def offline_result():
  return LiveDownloadResult(
    ok=False,
    recorded=False,
    room_status=4,
    room_id="998877",
    nickname="Test Host",
    reason="当前未直播",
  )


def probe_failed_result():
  return LiveDownloadResult(ok=False, recorded=False, reason="直播状态获取失败")


class FakeLiveDownloader:
  def __init__(self, result=None, crash=None):
    self._result = result
    self._crash = crash
    self.calls = []

  def run_with_result(self, token):
    self.calls.append(token)
    if self._crash is not None:
      raise self._crash
    return self._result if self._result is not None else recorded_result()


class FakeRecordingService:
  """Stands in for the resource service across the prepare/record split.

  ``calls`` keeps the same ``(result-ish, arguments)`` shape the tests already
  assert on, so what is recorded is still readable as the facts that reached
  persistence - now carried by the prepared intent rather than by the raw
  download result.
  """

  def __init__(self, failure=None, recording_id=73):
    self.failure = failure
    self.recording_id = recording_id
    self.calls = []
    self.prepared = []

  def prepare(self, result, **kwargs):
    intent = _REAL_RESOURCE.prepare(result, **kwargs)
    self.prepared.append((intent, dict(kwargs)))
    return intent

  def record_prepared(self, intent, *, recovery_key=None):
    arguments = next(
      (a for i, a in self.prepared if i is intent), {}
    )
    self.calls.append((intent, dict(arguments)))
    if self.failure is not None:
      raise self.failure
    return self.recording_id

  def record(self, result, **kwargs):
    return self.record_prepared(
      self.prepare(result, **kwargs),
      recovery_key=kwargs.get("recovery_key"),
    )


##
## The real canonicalisation, so the fake cannot drift from what production
## actually persists.
##
_REAL_RESOURCE = RecordingResourceService(repository_provider=lambda: None)


class InMemoryJournal:
  """A journal that records the protocol without touching a filesystem."""

  def __init__(self, publish_error=None, ack_error=None):
    self.publish_error = publish_error
    self.ack_error = ack_error
    self.published = []
    self.acknowledged = []

  def publish(self, intent, recovery_key):
    self.published.append((intent, recovery_key))
    if self.publish_error is not None:
      raise self.publish_error
    return "/storage/.smsd-recording-recovery/{}.json".format(recovery_key)

  def acknowledge(self, recovery_key):
    self.acknowledged.append(recovery_key)
    if self.ack_error is not None:
      raise self.ack_error


class InlineListenerItem:
  """A listener whose thread runs inline, so a submit finishes deterministically."""

  created = []

  def __init__(self, func=None, args=None):
    if not isinstance(args, tuple):
      raise ValueError("args must be a tuple")
    self.func = func
    self.args = args
    self.started = False
    InlineListenerItem.created.append(self)

  def start_item(self):
    self.started = True
    self.func(*self.args)


class DeferredListenerItem:
  """A listener that does not run until told, so queued state can be observed."""

  def __init__(self, func=None, args=None):
    self.func = func
    self.args = args
    self.started = False

  def start_item(self):
    self.started = True

  def run_now(self):
    self.func(*self.args)


class RefusingListenerItem:
  """A listener whose thread cannot be started."""

  def __init__(self, func=None, args=None):
    self.func = func
    self.args = args

  def start_item(self):
    raise RuntimeError("can't start new thread")


def build_service(
  downloader=None,
  task_service=None,
  listener=InlineListenerItem,
  recording_service=None,
  recovery_journal=None,
):
  ##
  ## A journal is part of production wiring wherever a recording service is,
  ## so the default harness provides one. Persisting without a durable recovery
  ## handoff is not a configuration this service supports.
  ##
  downloader = downloader if downloader is not None else FakeLiveDownloader()
  if recovery_journal is None:
    recovery_journal = InMemoryJournal()
  return (
    LiveRecordingTaskService(
      task_service=task_service,
      downloader_factory=lambda: downloader,
      listener_factory=listener,
      recording_service=recording_service,
      recovery_journal=recovery_journal,
    ),
    downloader,
  )


def only_task(tasks: TaskService) -> dict:
  listed = tasks.list_tasks()
  assert len(listed) == 1, listed
  return listed[0]


def submit_tracked(service, app_user_id=None):
  return service.submit_tracked(
    resolved_url=RESOLVED_URL,
    source_url=SOURCE_URL,
    resolve_id="receipt-live-1",
    app_user_id=app_user_id,
  )


class LiveTaskCreationTest(unittest.TestCase):
  def test_a_confirmed_room_becomes_a_live_record_task(self):
    tasks = TaskService()
    service, downloader = build_service(
      task_service=tasks, listener=DeferredListenerItem
    )

    service.submit(token())

    self.assertEqual(TASK_TYPE_LIVE_RECORD, only_task(tasks)["task_type"])

  def test_the_task_waits_as_pending_until_its_thread_runs(self):
    tasks = TaskService()
    service, downloader = build_service(
      task_service=tasks, listener=DeferredListenerItem
    )

    service.submit(token())

    task = only_task(tasks)
    self.assertEqual(TASK_STATE_PENDING, task["state"])
    self.assertEqual([], downloader.calls)

  def test_a_recording_has_no_final_count_to_measure_against(self):
    tasks = TaskService()
    service, downloader = build_service(
      task_service=tasks, listener=DeferredListenerItem
    )

    service.submit(token())

    ##
    ## A recording runs until the broadcast ends.  There is no total to divide
    ## by, and inventing "1" would make an hours-long stream render as a
    ## progress bar frozen at nothing.
    ##
    self.assertEqual({"current": 0, "total": None}, only_task(tasks)["progress"])

  def test_the_task_records_what_the_handler_resolved(self):
    tasks = TaskService()
    service, downloader = build_service(
      task_service=tasks, listener=DeferredListenerItem
    )

    service.submit(token())

    metadata = only_task(tasks)["metadata"]
    self.assertEqual(PLATFORM_DOUYIN, metadata["platform"])
    self.assertEqual(SOURCE_DIRECT, metadata["source"])
    self.assertEqual(SOURCE_URL, metadata["source_url"])
    self.assertEqual(RESOLVED_URL, metadata["resolved_url"])

  def test_the_task_is_titled_without_asking_the_platform(self):
    tasks = TaskService()
    service, downloader = build_service(
      task_service=tasks, listener=DeferredListenerItem
    )

    service.submit(token())

    self.assertEqual("录制抖音直播", only_task(tasks)["title"])

  def test_a_recording_carries_no_items(self):
    tasks = TaskService()
    service, downloader = build_service(
      task_service=tasks, listener=DeferredListenerItem
    )

    service.submit(token())

    self.assertEqual([], only_task(tasks)["items"])

  def test_the_token_is_not_polluted(self):
    tasks = TaskService()
    service, downloader = build_service(task_service=tasks)
    supplied = token(score=5)

    service.submit(supplied)

    self.assertEqual({"url", "resolved_url", "score"}, set(supplied))


class LiveTaskWorkerTest(unittest.TestCase):
  def test_the_task_runs_only_once_its_thread_does(self):
    tasks = TaskService()
    service, downloader = build_service(
      task_service=tasks, listener=DeferredListenerItem
    )
    item = service.submit(token())
    self.assertEqual(TASK_STATE_PENDING, only_task(tasks)["state"])

    item.run_now()

    self.assertEqual(1, len(downloader.calls))
    self.assertEqual(TASK_STATE_SUCCESS, only_task(tasks)["state"])

  def test_the_downloader_is_handed_the_token(self):
    tasks = TaskService()
    service, downloader = build_service(task_service=tasks)

    service.submit(token(score=5))

    self.assertEqual(RESOLVED_URL, downloader.calls[0]["resolved_url"])
    self.assertEqual(5, downloader.calls[0]["score"])

  def test_an_inline_thread_never_skips_the_running_state(self):
    tasks = TaskService()
    service, downloader = build_service(task_service=tasks)

    service.submit(token())

    ##
    ## pending -> success is not a legal move, so a finished task proves running
    ## was passed through even when the thread runs inside submit.
    ##
    task = only_task(tasks)
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertIsNotNone(task["started_at"])


class LiveResultMappingTest(unittest.TestCase):
  def run_with(self, result=None, crash=None):
    tasks = TaskService()
    downloader = FakeLiveDownloader(result=result, crash=crash)
    service, unused = build_service(downloader=downloader, task_service=tasks)
    try:
      service.submit(token())
    except Exception:
      ##
      ## Some endings deliberately re-raise on the recording thread; the task is
      ## what this test is about.
      ##
      pass
    return tasks, only_task(tasks)

  def test_a_finished_recording_is_a_success(self):
    tasks, task = self.run_with(recorded_result())

    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertIs(True, task["metadata"]["result"]["recorded"])

  def test_a_finished_recording_reports_where_it_wrote(self):
    tasks, task = self.run_with(recorded_result(output_path="/media/re_1_live.flv"))

    result = task["metadata"]["result"]
    self.assertEqual("/media/re_1_live.flv", result["output_path"])
    self.assertEqual("flv", result["protocol"])
    self.assertEqual("998877", result["room_id"])
    self.assertEqual("Test Host", result["nickname"])
    self.assertEqual("Launch title", result["title"])
    self.assertEqual("2026-08-25T09:00:00.000", result["started_at"])


  def test_test_mode_succeeds_without_claiming_a_file(self):
    tasks, task = self.run_with(make_test_mode_result())

    result = task["metadata"]["result"]
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertIs(True, result["test_mode"])
    self.assertIs(False, result["recorded"])
    self.assertIsNone(result["output_path"])

  def test_a_room_that_is_not_live_is_a_failed_recording(self):
    tasks, task = self.run_with(offline_result())

    ##
    ## The opposite of a probe task, and deliberately so: here the user asked to
    ## *record*, and there is no recording.  A probe asking "are they live?" is
    ## answered successfully by "no"; this was not.
    ##
    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertEqual("当前未直播", task["message"])
    self.assertEqual("offline", task["metadata"]["result"]["live_status"])
    self.assertIs(False, task["metadata"]["result"]["recorded"])

  def test_a_probe_failure_is_a_failed_recording(self):
    tasks, task = self.run_with(probe_failed_result())

    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertEqual("直播状态获取失败", task["message"])
    ##
    ## Unlike the offline case, nothing is claimed about whether they are live.
    ##
    self.assertIsNone(task["metadata"]["result"]["live_status"])

  def test_a_missing_stream_is_a_failed_recording(self):
    tasks, task = self.run_with(
      LiveDownloadResult(
        ok=False, recorded=False, room_status=2, reason="直播流地址不可用"
      )
    )

    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertEqual("直播流地址不可用", task["message"])

  def test_a_crashing_recording_is_a_failed_task(self):
    tasks, task = self.run_with(crash=RuntimeError("stream reset"))

    self.assertEqual(TASK_STATE_FAILED, task["state"])

  def test_a_crash_never_publishes_a_traceback(self):
    tasks, task = self.run_with(crash=RuntimeError("stream reset"))

    rendered = repr(task["metadata"]) + repr(task["message"])
    self.assertNotIn("Traceback", rendered)
    self.assertNotIn("File \"", rendered)

  def test_a_cancelled_recording_is_recorded_as_cancelled(self):
    tasks, task = self.run_with(crash=HlsCancelled("shutting down"))

    ##
    ## The one cancellation this stage can describe honestly: the HLS recorder
    ## was stopped deliberately, most often by the server shutting down.
    ##
    self.assertEqual(TASK_STATE_CANCELLED, task["state"])

  def test_every_ending_leaves_the_total_unknown(self):
    for label, arguments in {
      "recorded": {"result": recorded_result()},
      "test mode": {"result": make_test_mode_result()},
      "offline": {"result": offline_result()},
      "probe failed": {"result": probe_failed_result()},
      "crashed": {"crash": RuntimeError("stream reset")},
      "cancelled": {"crash": HlsCancelled("shutting down")},
    }.items():
      with self.subTest(ending=label):
        tasks, task = self.run_with(**arguments)
        self.assertIsNone(task["progress"]["total"])

  def test_every_ending_reaches_a_terminal_state(self):
    from backend.src.task.model import TERMINAL_TASK_STATES

    for label, arguments in {
      "recorded": {"result": recorded_result()},
      "test mode": {"result": make_test_mode_result()},
      "offline": {"result": offline_result()},
      "probe failed": {"result": probe_failed_result()},
      "crashed": {"crash": RuntimeError("stream reset")},
      "cancelled": {"crash": HlsCancelled("shutting down")},
    }.items():
      with self.subTest(ending=label):
        tasks, task = self.run_with(**arguments)
        self.assertIn(task["state"], TERMINAL_TASK_STATES)
        self.assertIsNotNone(task["finished_at"])


class LiveRecordingResourceIntegrationTest(unittest.TestCase):
  def test_owned_recording_is_persisted_before_success_and_exposes_recording_id(self):
    events = []

    class OrderedTaskService(TaskService):
      def update_metadata(self, *args, **kwargs):
        events.append("metadata")
        return super().update_metadata(*args, **kwargs)

      def finish_success(self, *args, **kwargs):
        events.append("finish_success")
        return super().finish_success(*args, **kwargs)

    class OrderedRecordingService(FakeRecordingService):
      ##
      ## ``record_prepared`` is what writes now; ``record`` is the convenience
      ## wrapper around it. Spying on the wrapper would observe nothing.
      ##
      def record_prepared(self, intent, **arguments):
        events.append("record")
        return super().record_prepared(intent, **arguments)

    tasks = OrderedTaskService()
    resources = OrderedRecordingService(recording_id=73)
    service, downloader = build_service(
      task_service=tasks,
      recording_service=resources,
    )

    task_id = submit_tracked(service, app_user_id=41)

    task = tasks.get_task(task_id)
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertEqual(73, task["metadata"]["result"]["recording_id"])
    _, arguments = resources.calls[0]
    self.assertEqual(41, arguments["app_user_id"])
    self.assertEqual(PLATFORM_DOUYIN, arguments["platform"])
    self.assertEqual(SOURCE_TASK_API, arguments["source"])
    self.assertEqual(["record", "metadata", "finish_success"], events)

  def test_a_normalized_hls_recording_is_persisted_as_the_mp4(self):
    ##
    ## Normalization happens inside the recording pipeline, before the result
    ## exists, so the path arriving here is already final.  There is no second
    ## write that corrects a ``.ts`` row into an ``.mp4`` one afterwards - the
    ## row is right the first time it is inserted.
    ##
    tasks = TaskService()
    resources = FakeRecordingService(recording_id=91)
    downloader = FakeLiveDownloader(
      recorded_result(
        protocol="hls",
        output_path="/media/douyin/live/A/live.mp4",
      )
    )
    service, _ = build_service(
      downloader=downloader,
      task_service=tasks,
      recording_service=resources,
    )

    task_id = submit_tracked(service, app_user_id=41)

    persisted, _ = resources.calls[0]
    self.assertEqual("/media/douyin/live/A/live.mp4", persisted.output_path)
    ##
    ## Still an HLS recording: the protocol names how it was captured, not the
    ## container it ended up in.
    ##
    self.assertEqual("hls", persisted.protocol)
    task = tasks.get_task(task_id)
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertEqual(91, task["metadata"]["result"]["recording_id"])
    self.assertEqual(
      "/media/douyin/live/A/live.mp4",
      task["metadata"]["result"]["output_path"],
    )

  def test_an_unnormalized_hls_recording_is_persisted_as_the_ts(self):
    ##
    ## The remux did not run, or could not.  The broadcast was still captured
    ## in full, so this is a successful recording that happens to be a ``.ts``:
    ## downloadable, not previewable in place, and definitely not a failure.
    ##
    tasks = TaskService()
    resources = FakeRecordingService(recording_id=92)
    downloader = FakeLiveDownloader(
      recorded_result(
        protocol="hls",
        output_path="/media/douyin/live/A/live.ts",
      )
    )
    service, _ = build_service(
      downloader=downloader,
      task_service=tasks,
      recording_service=resources,
    )

    task_id = submit_tracked(service, app_user_id=41)

    persisted, _ = resources.calls[0]
    self.assertEqual("/media/douyin/live/A/live.ts", persisted.output_path)
    self.assertEqual("hls", persisted.protocol)
    task = tasks.get_task(task_id)
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertNotEqual(TASK_STATE_PARTIAL, task["state"])
    self.assertEqual(92, task["metadata"]["result"]["recording_id"])
    self.assertEqual(
      "/media/douyin/live/A/live.ts",
      task["metadata"]["result"]["output_path"],
    )

  def test_the_recording_is_persisted_exactly_once_whatever_the_container(self):
    for output_path in (
      "/media/douyin/live/A/live.mp4",
      "/media/douyin/live/A/live.ts",
    ):
      with self.subTest(output_path=output_path):
        tasks = TaskService()
        resources = FakeRecordingService()
        downloader = FakeLiveDownloader(
          recorded_result(protocol="hls", output_path=output_path)
        )
        service, _ = build_service(
          downloader=downloader,
          task_service=tasks,
          recording_service=resources,
        )

        submit_tracked(service, app_user_id=41)

        self.assertEqual(1, len(resources.calls))

  def test_anonymous_legacy_recording_is_persisted_with_null_owner(self):
    tasks = TaskService()
    resources = FakeRecordingService()
    service, downloader = build_service(
      task_service=tasks,
      recording_service=resources,
    )

    service.submit(token())

    _, arguments = resources.calls[0]
    self.assertIsNone(arguments["app_user_id"])
    self.assertEqual(SOURCE_DIRECT, arguments["source"])
    self.assertEqual(TASK_STATE_SUCCESS, only_task(tasks)["state"])

  def test_owned_persistence_failure_keeps_media_but_prevents_full_success(self):
    tasks = TaskService()
    resources = FakeRecordingService(
      failure=RuntimeError("mysql host and driver detail")
    )
    service, downloader = build_service(
      task_service=tasks,
      recording_service=resources,
    )

    task_id = submit_tracked(service, app_user_id=41)

    task = tasks.get_task(task_id)
    self.assertEqual(TASK_STATE_PARTIAL, task["state"])
    self.assertNotIn("mysql", task["message"].lower())
    self.assertNotIn("driver", task["message"].lower())

  def test_owned_result_without_output_path_is_partial_and_not_inserted(self):
    tasks = TaskService()
    repository = FakeRecordingService()
    validator = RecordingResourceService(repository_provider=lambda: repository)
    service, downloader = build_service(
      downloader=FakeLiveDownloader(result=recorded_result(output_path=None)),
      task_service=tasks,
      recording_service=validator,
    )

    task_id = submit_tracked(service, app_user_id=41)

    self.assertEqual(TASK_STATE_PARTIAL, tasks.get_task(task_id)["state"])
    self.assertEqual([], repository.calls)

  def test_anonymous_persistence_failure_preserves_recording_success(self):
    tasks = TaskService()
    resources = FakeRecordingService(failure=RuntimeError("database unavailable"))
    service, downloader = build_service(
      task_service=tasks,
      recording_service=resources,
    )

    service.submit(token())

    self.assertEqual(TASK_STATE_SUCCESS, only_task(tasks)["state"])

  def test_non_recording_endings_never_reach_the_resource_service(self):
    endings = (
      (make_test_mode_result(), None),
      (offline_result(), None),
      (probe_failed_result(), None),
      (None, RuntimeError("stream reset")),
      (None, HlsCancelled("shutting down")),
    )
    for result, crash in endings:
      with self.subTest(result=result, crash=crash):
        tasks = TaskService()
        resources = FakeRecordingService()
        service, downloader = build_service(
          downloader=FakeLiveDownloader(result=result, crash=crash),
          task_service=tasks,
          recording_service=resources,
        )
        try:
          service.submit(token())
        except Exception:
          pass
        self.assertEqual([], resources.calls)


class LiveTaskSecrecyTest(unittest.TestCase):
  def test_a_signed_stream_url_cannot_reach_the_task(self):
    tasks = TaskService()
    downloader = FakeLiveDownloader(result=recorded_result())
    service, unused = build_service(downloader=downloader, task_service=tasks)

    service.submit(
      token(stream_url="https://stream.test/live.flv?sign=SECRET&token=SECRET")
    )

    ##
    ## Even when a caller puts one in the token, nothing copies it across: the
    ## task is built from named fields, never from the token wholesale.
    ##
    rendered = repr(only_task(tasks))
    self.assertNotIn("sign=", rendered)
    self.assertNotIn("token=SECRET", rendered)
    self.assertNotIn("stream_url", rendered)


class BrokenTaskService:
  """Every call fails, standing in for a task layer that has gone wrong."""

  def __init__(self):
    self.calls = []

  def _fail(self, name):
    self.calls.append(name)
    raise RuntimeError("task layer unavailable")

  def create_task(self, *args, **kwargs):
    self._fail("create_task")

  def start_task(self, *args, **kwargs):
    self._fail("start_task")

  def update_metadata(self, *args, **kwargs):
    self._fail("update_metadata")

  def update_progress(self, *args, **kwargs):
    self._fail("update_progress")

  def update_message(self, *args, **kwargs):
    self._fail("update_message")

  def get_task(self, *args, **kwargs):
    self._fail("get_task")

  def finish_success(self, *args, **kwargs):
    self._fail("finish_success")

  def finish_failed(self, *args, **kwargs):
    self._fail("finish_failed")

  def cancel_task(self, *args, **kwargs):
    self._fail("cancel_task")


class LiveTaskTelemetryFailureTest(unittest.TestCase):
  """Reporting can never decide whether a broadcast gets recorded."""

  def test_a_recording_runs_with_no_task_service_at_all(self):
    service, downloader = build_service()

    service.submit(token())

    self.assertEqual(1, len(downloader.calls))
    self.assertFalse(service.enabled)

  def test_a_recording_runs_when_the_whole_task_layer_is_broken(self):
    broken = BrokenTaskService()
    service, downloader = build_service(task_service=broken)

    service.submit(token())

    self.assertEqual(1, len(downloader.calls))

  def test_nothing_further_is_attempted_once_creation_was_refused(self):
    broken = BrokenTaskService()
    service, downloader = build_service(task_service=broken)

    service.submit(token())

    self.assertEqual(["create_task"], broken.calls)

  def test_a_refused_start_does_not_stop_the_recording(self):
    class RefusesStart(TaskService):
      def start_task(self, *args, **kwargs):
        raise RuntimeError("start unavailable")

    service, downloader = build_service(task_service=RefusesStart())

    service.submit(token())

    self.assertEqual(1, len(downloader.calls))

  def test_a_refused_metadata_write_still_ends_the_task(self):
    class RefusesMetadata(TaskService):
      def update_metadata(self, *args, **kwargs):
        raise RuntimeError("metadata unavailable")

    tasks = RefusesMetadata()
    service, downloader = build_service(task_service=tasks)

    service.submit(token())

    self.assertEqual(1, len(downloader.calls))
    self.assertEqual(TASK_STATE_SUCCESS, only_task(tasks)["state"])

  def test_a_refused_finish_does_not_undo_the_recording(self):
    class RefusesFinish(TaskService):
      def finish_success(self, *args, **kwargs):
        raise RuntimeError("finish unavailable")

    tasks = RefusesFinish()
    service, downloader = build_service(task_service=tasks)

    service.submit(token())

    self.assertEqual(1, len(downloader.calls))
    self.assertEqual(TASK_STATE_RUNNING, only_task(tasks)["state"])

  def test_a_refused_cancel_still_lets_the_cancellation_propagate(self):
    class RefusesCancel(TaskService):
      def cancel_task(self, *args, **kwargs):
        raise RuntimeError("cancel unavailable")

    tasks = RefusesCancel()
    downloader = FakeLiveDownloader(crash=HlsCancelled("shutting down"))
    service, unused = build_service(downloader=downloader, task_service=tasks)

    with self.assertRaises(HlsCancelled):
      service.submit(token())


class LiveTaskThreadFailureTest(unittest.TestCase):
  def test_a_recording_that_never_starts_does_not_stay_pending(self):
    tasks = TaskService()
    service, downloader = build_service(
      task_service=tasks, listener=RefusingListenerItem
    )

    returned = service.submit(token())

    task = only_task(tasks)
    self.assertIsNone(returned)
    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertEqual("直播录制没有进入执行线程", task["message"])
    self.assertEqual([], downloader.calls)

  def test_a_recording_that_never_starts_is_eventually_reclaimed(self):
    from datetime import datetime, timedelta

    from backend.src.task.store import TaskStore

    class Clock:
      def __init__(self):
        self.wall = datetime(2026, 8, 14, 9, 0, 0)
        self.mono = 0.0

      def now(self):
        return self.wall

      def monotonic(self):
        return self.mono

      def advance(self, seconds):
        self.wall = self.wall + timedelta(seconds=seconds)
        self.mono += seconds

    clock = Clock()
    tasks = TaskService(
      TaskStore(
        retention_seconds=600.0, clock=clock.now, monotonic_clock=clock.monotonic
      )
    )
    service, downloader = build_service(
      task_service=tasks, listener=RefusingListenerItem
    )
    service.submit(token())

    clock.advance(601.0)

    ##
    ## Only ended tasks are ever expired, so this passing is proof the ending was
    ## really recorded.  One left pending would stay for the life of the process.
    ##
    self.assertEqual([], tasks.list_tasks())

  def test_a_failure_to_start_survives_having_no_task(self):
    service, downloader = build_service(listener=RefusingListenerItem)

    self.assertIsNone(service.submit(token()))

  def test_a_recording_that_failed_is_not_reported_as_never_started(self):
    ##
    ## The two are told apart by whether the worker began, not by where the
    ## exception surfaced.  A listener that runs its target inline raises the
    ## worker's own exception out of ``start_item``, and calling that "never
    ## started" would overwrite the ending the worker already recorded.
    ##
    tasks = TaskService()
    downloader = FakeLiveDownloader(crash=RuntimeError("stream reset"))
    service, unused = build_service(downloader=downloader, task_service=tasks)

    with self.assertRaises(RuntimeError):
      service.submit(token())

    task = only_task(tasks)
    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertEqual("直播录制失败", task["message"])
    self.assertEqual(1, len(downloader.calls))

  def test_a_cancelled_recording_is_not_reported_as_never_started(self):
    tasks = TaskService()
    downloader = FakeLiveDownloader(crash=HlsCancelled("shutting down"))
    service, unused = build_service(downloader=downloader, task_service=tasks)

    with self.assertRaises(HlsCancelled):
      service.submit(token())

    self.assertEqual(TASK_STATE_CANCELLED, only_task(tasks)["state"])


class LiveTaskIndependenceTest(unittest.TestCase):
  def test_each_room_becomes_its_own_task(self):
    tasks = TaskService()
    service, downloader = build_service(task_service=tasks)

    service.submit(token(url="https://v.douyin.com/a/"))
    service.submit(token(url="https://v.douyin.com/b/"))
    service.submit(token(url="https://v.douyin.com/c/"))

    listed = tasks.list_tasks()
    self.assertEqual(3, len(listed))
    self.assertEqual(
      {"https://v.douyin.com/a/", "https://v.douyin.com/b/", "https://v.douyin.com/c/"},
      {task["metadata"]["source_url"] for task in listed},
    )

  def test_one_failed_recording_does_not_disturb_another(self):
    tasks = TaskService()
    results = {
      "https://v.douyin.com/a/": recorded_result(),
      "https://v.douyin.com/b/": offline_result(),
    }

    class PerUrlDownloader:
      def __init__(self):
        self.calls = []

      def run_with_result(self, token):
        self.calls.append(token)
        return results[token["url"]]

    service, unused = build_service(
      downloader=PerUrlDownloader(), task_service=tasks
    )

    service.submit(token(url="https://v.douyin.com/a/"))
    service.submit(token(url="https://v.douyin.com/b/"))

    listed = {task["metadata"]["source_url"]: task for task in tasks.list_tasks()}
    self.assertEqual(
      TASK_STATE_SUCCESS, listed["https://v.douyin.com/a/"]["state"]
    )
    self.assertEqual(TASK_STATE_FAILED, listed["https://v.douyin.com/b/"]["state"])

  def test_the_same_room_submitted_twice_stays_two_recordings(self):
    tasks = TaskService()
    service, downloader = build_service(task_service=tasks)

    service.submit(token())
    service.submit(token())

    ##
    ## Legacy submission semantics are not this stage's to change.
    ##
    self.assertEqual(2, len(downloader.calls))
    self.assertEqual(2, len(tasks.list_tasks()))


class LiveTaskDiagnosticSafetyTest(unittest.TestCase):
  def test_a_downloader_exception_cannot_log_its_signed_url_or_message(self):
    secret = "SECRET_QUERY_TOKEN_13A"
    messages = []

    class Logger:
      def error(self, message):
        messages.append(str(message))

    service, unused = build_service(
      downloader=FakeLiveDownloader(
        crash=RuntimeError("request failed at signed=" + secret)
      )
    )

    with patch.object(task_module, "get_logger", return_value=Logger()):
      with self.assertRaises(RuntimeError):
        service._run(
          None,
          token(url="https://live.example.test/room?token=" + secret),
        )

    visible = "\n".join(messages)
    self.assertNotIn(secret, visible)
    self.assertIn("live diagnostic event=live_recording_failed", visible)

  def test_real_logger_and_thread_boundary_never_render_exception_secrets(self):
    secret = "SECRET_THREAD_EXCEPTION_13A"
    output = io.StringIO()
    logger = logging.Logger("phase13a-live-thread")
    logger.addHandler(logging.StreamHandler(output))
    service, unused = build_service(
      downloader=FakeLiveDownloader(
        crash=RuntimeError("signed-url-token=" + secret)
      )
    )

    stderr = io.StringIO()
    with patch.object(task_module, "get_logger", return_value=logger), patch(
      "backend.src.platform.douyin.douyin_listener.get_logger",
      return_value=logger,
    ), contextlib.redirect_stderr(stderr):
      item = ListenerItem(
        func=lambda: service._run(
          None,
          token(url="https://live.example.test/room?token=" + secret),
        ),
        args=(),
      )
      item.start_item()
      item._thread.join(timeout=2)

    visible = output.getvalue() + stderr.getvalue()
    self.assertFalse(item._thread.is_alive())
    self.assertNotIn(secret, visible)
    self.assertIn("live diagnostic event=live_recording_failed", visible)

  def test_persistence_failure_regions_log_only_closed_diagnostics(self):
    secret = "SECRET_PERSISTENCE_EXCEPTION_13A"

    cases = (
      (
        FakeRecordingService(),
        InMemoryJournal(publish_error=RuntimeError(secret + "-publish")),
        "live_recovery_handoff_failed",
      ),
      (
        FakeRecordingService(failure=RuntimeError(secret + "-database")),
        InMemoryJournal(),
        "live_recording_persistence_failed",
      ),
      (
        FakeRecordingService(),
        InMemoryJournal(ack_error=RuntimeError(secret + "-ack")),
        "live_recovery_ack_failed",
      ),
    )

    for recording_service, journal, event in cases:
      with self.subTest(event=event):
        output = io.StringIO()
        logger = logging.Logger("phase13a-" + event)
        logger.addHandler(logging.StreamHandler(output))
        service, unused = build_service(
          recording_service=recording_service,
          recovery_journal=journal,
        )

        with patch.object(task_module, "get_logger", return_value=logger):
          service._run(None, token())

        visible = output.getvalue()
        self.assertNotIn(secret, visible)
        self.assertIn("live diagnostic event=" + event, visible)


if __name__ == "__main__":
  unittest.main()
