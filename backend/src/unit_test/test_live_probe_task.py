import unittest
from datetime import datetime

from backend.src.service.live_probe import (
  STATE_ERROR,
  STATE_LIVING,
  STATE_OFFLINE,
  STATE_PENDING,
  LiveProbeService,
)
from backend.src.service.live_probe_task_mirror import (
  LIVE_STATUS_LIVING,
  LIVE_STATUS_OFFLINE,
  PLATFORM_DOUYIN,
)
from backend.src.task.model import (
  ITEM_STATE_FAILED,
  ITEM_STATE_PENDING,
  ITEM_STATE_SUCCESS,
  TASK_STATE_FAILED,
  TASK_STATE_PARTIAL,
  TASK_STATE_RUNNING,
  TASK_STATE_SUCCESS,
  TASK_TYPE_LIVE_PROBE,
  to_payload,
)
from backend.src.task.service import TaskService

NOW = datetime(2026, 8, 13, 20, 30, 0)


class FakeResult:
  def __init__(self, ok=True, room_status=2, error=None, room_id="room-1"):
    self.ok = ok
    self.room_status = room_status
    self.error = error
    self.owner_user_id = "owner"
    self.room_id = room_id
    self.nickname = "Host"
    self.title = "Title"
    self.checked_at = NOW

  @property
  def is_living(self):
    return self.room_status == 2


class FakeProber:
  def __init__(self, results=None, crash_on=None):
    self._results = results or {}
    self._crash_on = crash_on or ()
    self.calls = []

  def probe(self, url):
    self.calls.append(url)
    if url in self._crash_on:
      raise RuntimeError("boom")
    return self._results.get(url, FakeResult())


class ImmediateExecutor:
  """Runs submitted work inline so batches finish deterministically."""

  def __init__(self):
    self.submitted = 0

  def submit(self, fn, *args, **kwargs):
    self.submitted += 1
    fn(*args, **kwargs)

  def shutdown(self, wait=False):
    return None


class DeferredExecutor:
  """Holds submitted work until asked, so mid-flight state can be observed."""

  def __init__(self):
    self.queued = []

  def submit(self, fn, *args, **kwargs):
    self.queued.append((fn, args, kwargs))

  def drain(self):
    pending, self.queued = self.queued, []
    for fn, args, kwargs in pending:
      fn(*args, **kwargs)

  def shutdown(self, wait=False):
    return None


def build_service(prober, owners, task_service=None, **overrides):
  options = {
    "prober": prober,
    "owner_lookup": lambda ids: {k: v for k, v in owners.items() if k in ids},
    "executor": ImmediateExecutor(),
    "clock": lambda: NOW,
    "task_service": task_service,
  }
  options.update(overrides)
  return LiveProbeService(**options)


def owner(share_url="https://u/1", nickname="A", **extra):
  row = {"live_share_url": share_url, "nickname": nickname}
  row.update(extra)
  return row


def cached_owner(status, room_id="room-cached", **extra):
  return owner(
    last_live_status=status,
    last_checked_at=NOW,
    last_room_id=room_id,
    **extra
  )


def item_of(task: dict, key: str) -> dict:
  return next(item for item in task["items"] if item["key"] == key)


def legacy_item(service, batch_id: str, owner_user_id: str) -> dict:
  snapshot = service.snapshot(batch_id)
  return next(
    item for item in snapshot["items"] if item["owner_user_id"] == owner_user_id
  )


class ProbeTaskCreationTest(unittest.TestCase):
  def test_a_probe_creates_a_live_probe_task_beside_its_batch(self):
    tasks = TaskService()
    service = build_service(FakeProber(), {"1": owner()}, task_service=tasks)

    batch_id = service.submit(["1"])

    task = tasks.get_task(service.task_id_for(batch_id))
    self.assertEqual(TASK_TYPE_LIVE_PROBE, task["task_type"])

  def test_the_task_and_the_batch_are_separate_identifiers(self):
    tasks = TaskService()
    service = build_service(FakeProber(), {"1": owner()}, task_service=tasks)

    batch_id = service.submit(["1"])

    task_id = service.task_id_for(batch_id)
    self.assertNotEqual(batch_id, task_id)
    self.assertEqual(batch_id, tasks.get_task(task_id)["metadata"]["legacy_batch_id"])

  def test_the_task_records_the_platform_and_how_many_were_asked_for(self):
    tasks = TaskService()
    service = build_service(
      FakeProber(), {"1": owner(), "2": owner("https://u/2")}, task_service=tasks
    )

    batch_id = service.submit(["1", "2"])

    metadata = tasks.get_task(service.task_id_for(batch_id))["metadata"]
    self.assertEqual(PLATFORM_DOUYIN, metadata["platform"])
    self.assertEqual(2, metadata["requested_count"])

  def test_the_task_is_titled_for_the_people_being_checked(self):
    tasks = TaskService()
    service = build_service(
      FakeProber(), {"1": owner(), "2": owner("https://u/2")}, task_service=tasks
    )

    batch_id = service.submit(["1", "2"])

    self.assertEqual(
      "检查 2 个主播直播状态", tasks.get_task(service.task_id_for(batch_id))["title"]
    )

  def test_a_single_owner_gets_a_singular_title(self):
    tasks = TaskService()
    service = build_service(FakeProber(), {"1": owner()}, task_service=tasks)

    batch_id = service.submit(["1"])

    self.assertEqual(
      "检查主播直播状态", tasks.get_task(service.task_id_for(batch_id))["title"]
    )

  def test_a_repeated_owner_is_one_unit_of_work(self):
    tasks = TaskService()
    prober = FakeProber()
    service = build_service(prober, {"1": owner()}, task_service=tasks)

    batch_id = service.submit(["1", "1", " 1 "])

    task = tasks.get_task(service.task_id_for(batch_id))
    self.assertEqual(["1"], [item["key"] for item in task["items"]])
    self.assertEqual(1, task["progress"]["total"])
    self.assertEqual(1, len(prober.calls))
    self.assertEqual(1, len(service.snapshot(batch_id)["items"]))

  def test_a_service_without_a_task_service_still_probes(self):
    prober = FakeProber()
    service = build_service(prober, {"1": owner()})

    batch_id = service.submit(["1"])

    self.assertEqual(STATE_LIVING, legacy_item(service, batch_id, "1")["state"])
    self.assertIsNone(service.task_id_for(batch_id))


class ProbeTaskSynchronousOutcomeTest(unittest.TestCase):
  def probe_one(self, owners, prober=None, task_service=None):
    tasks = task_service if task_service is not None else TaskService()
    prober = prober if prober is not None else FakeProber()
    service = build_service(prober, owners, task_service=tasks)
    batch_id = service.submit(list(owners.keys()) or ["missing"])
    return service, tasks, prober, batch_id

  def test_an_unknown_owner_fails_its_item_without_touching_the_network(self):
    service, tasks, prober, batch_id = self.probe_one({})

    task = tasks.get_task(service.task_id_for(batch_id))
    item = item_of(task, "missing")
    self.assertEqual(ITEM_STATE_FAILED, item["state"])
    self.assertEqual("历史记录中没有该主播", item["message"])
    self.assertEqual([], prober.calls)
    self.assertEqual(STATE_ERROR, legacy_item(service, batch_id, "missing")["state"])

  def test_an_owner_without_a_share_link_fails_its_item_without_probing(self):
    service, tasks, prober, batch_id = self.probe_one({"1": owner(share_url=None)})

    item = item_of(tasks.get_task(service.task_id_for(batch_id)), "1")
    self.assertEqual(ITEM_STATE_FAILED, item["state"])
    self.assertEqual("该主播没有可用的直播分享链接", item["message"])
    self.assertEqual([], prober.calls)

  def test_a_cached_living_owner_succeeds_without_probing(self):
    service, tasks, prober, batch_id = self.probe_one({"1": cached_owner(2)})

    item = item_of(tasks.get_task(service.task_id_for(batch_id)), "1")
    self.assertEqual(ITEM_STATE_SUCCESS, item["state"])
    self.assertEqual(LIVE_STATUS_LIVING, item["metadata"]["live_status"])
    self.assertIs(True, item["metadata"]["cached"])
    self.assertEqual("room-cached", item["metadata"]["room_id"])
    self.assertEqual([], prober.calls)
    self.assertEqual(STATE_LIVING, legacy_item(service, batch_id, "1")["state"])

  def test_a_cached_offline_owner_succeeds_without_probing(self):
    service, tasks, prober, batch_id = self.probe_one({"1": cached_owner(4)})

    item = item_of(tasks.get_task(service.task_id_for(batch_id)), "1")
    self.assertEqual(ITEM_STATE_SUCCESS, item["state"])
    self.assertEqual(LIVE_STATUS_OFFLINE, item["metadata"]["live_status"])
    self.assertIs(True, item["metadata"]["cached"])
    self.assertEqual([], prober.calls)
    self.assertEqual(STATE_OFFLINE, legacy_item(service, batch_id, "1")["state"])

  def test_a_fully_cached_batch_is_already_finished_when_submit_returns(self):
    tasks = TaskService()
    service = build_service(
      FakeProber(),
      {"1": cached_owner(2), "2": cached_owner(4, share_url="https://u/2")},
      task_service=tasks,
      executor=DeferredExecutor(),
    )

    batch_id = service.submit(["1", "2"])

    task = tasks.get_task(service.task_id_for(batch_id))
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertEqual({"current": 2, "total": 2}, task["progress"])

  def test_a_batch_of_only_synchronous_errors_fails_when_submit_returns(self):
    tasks = TaskService()
    service = build_service(
      FakeProber(),
      {"2": owner(share_url=None, nickname="B")},
      task_service=tasks,
      executor=DeferredExecutor(),
    )

    batch_id = service.submit(["missing", "2"])

    task = tasks.get_task(service.task_id_for(batch_id))
    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertEqual({"current": 2, "total": 2}, task["progress"])

  def test_a_mixed_batch_waits_for_the_owners_it_still_has_to_probe(self):
    tasks = TaskService()
    executor = DeferredExecutor()
    service = build_service(
      FakeProber(),
      {
        "A": cached_owner(2),
        "C": owner("https://u/C", nickname="C"),
      },
      task_service=tasks,
      executor=executor,
    )

    batch_id = service.submit(["A", "B", "C"])

    task_id = service.task_id_for(batch_id)
    task = tasks.get_task(task_id)
    self.assertEqual(TASK_STATE_RUNNING, task["state"])
    self.assertEqual({"current": 2, "total": 3}, task["progress"])
    self.assertEqual(ITEM_STATE_SUCCESS, item_of(task, "A")["state"])
    self.assertEqual(ITEM_STATE_FAILED, item_of(task, "B")["state"])
    self.assertEqual(ITEM_STATE_PENDING, item_of(task, "C")["state"])

    executor.drain()

    finished = tasks.get_task(task_id)
    self.assertEqual(TASK_STATE_PARTIAL, finished["state"])
    self.assertEqual({"current": 3, "total": 3}, finished["progress"])
    self.assertEqual(ITEM_STATE_SUCCESS, item_of(finished, "C")["state"])


class ProbeTaskNetworkOutcomeTest(unittest.TestCase):
  def test_a_living_room_becomes_a_successful_item(self):
    tasks = TaskService()
    service = build_service(
      FakeProber({"https://u/1": FakeResult(room_status=2)}),
      {"1": owner()},
      task_service=tasks,
    )

    batch_id = service.submit(["1"])

    item = item_of(tasks.get_task(service.task_id_for(batch_id)), "1")
    self.assertEqual(ITEM_STATE_SUCCESS, item["state"])
    self.assertEqual(LIVE_STATUS_LIVING, item["metadata"]["live_status"])
    self.assertIs(False, item["metadata"]["cached"])
    self.assertEqual("room-1", item["metadata"]["room_id"])
    self.assertEqual("Title", item["metadata"]["title"])
    self.assertEqual("Host", item["metadata"]["nickname"])
    self.assertEqual("https://u/1", item["metadata"]["live_share_url"])

  def test_a_finished_room_becomes_a_successful_item_too(self):
    tasks = TaskService()
    service = build_service(
      FakeProber({"https://u/1": FakeResult(room_status=4)}),
      {"1": owner()},
      task_service=tasks,
    )

    batch_id = service.submit(["1"])

    task = tasks.get_task(service.task_id_for(batch_id))
    item = item_of(task, "1")
    self.assertEqual(ITEM_STATE_SUCCESS, item["state"])
    self.assertEqual(LIVE_STATUS_OFFLINE, item["metadata"]["live_status"])
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])

  def test_an_owner_is_reported_as_running_while_being_probed(self):
    tasks = TaskService()
    seen = []
    service = build_service(FakeProber(), {"1": owner()}, task_service=tasks)
    original = tasks.update_item

    def watch(task_id, key, **kwargs):
      seen.append(kwargs.get("state"))
      return original(task_id, key, **kwargs)

    tasks.update_item = watch
    service.submit(["1"])

    self.assertEqual(["running", ITEM_STATE_SUCCESS], seen)

  def test_a_probe_that_answered_with_an_error_fails_its_item(self):
    tasks = TaskService()
    service = build_service(
      FakeProber({"https://u/1": FakeResult(ok=False, error="请求超时")}),
      {"1": owner()},
      task_service=tasks,
    )

    batch_id = service.submit(["1"])

    task = tasks.get_task(service.task_id_for(batch_id))
    item = item_of(task, "1")
    self.assertEqual(ITEM_STATE_FAILED, item["state"])
    self.assertEqual("请求超时", item["message"])
    self.assertEqual(TASK_STATE_FAILED, task["state"])
    self.assertEqual(STATE_ERROR, legacy_item(service, batch_id, "1")["state"])

  def test_a_crashing_probe_fails_only_its_own_owner(self):
    tasks = TaskService()
    service = build_service(
      FakeProber(crash_on=("https://u/1",)),
      {"1": owner(), "2": owner("https://u/2", nickname="B")},
      task_service=tasks,
    )

    batch_id = service.submit(["1", "2"])

    task = tasks.get_task(service.task_id_for(batch_id))
    self.assertEqual(ITEM_STATE_FAILED, item_of(task, "1")["state"])
    self.assertEqual("探测失败", item_of(task, "1")["message"])
    self.assertEqual(ITEM_STATE_SUCCESS, item_of(task, "2")["state"])
    self.assertEqual(TASK_STATE_PARTIAL, task["state"])
    self.assertTrue(service.snapshot(batch_id)["done"])

  def test_a_failing_cache_write_leaves_the_probe_successful(self):
    def explode(*unused):
      raise RuntimeError("database gone")

    tasks = TaskService()
    service = build_service(
      FakeProber({"https://u/1": FakeResult(room_status=2)}),
      {"1": owner()},
      task_service=tasks,
      status_writer=explode,
    )

    batch_id = service.submit(["1"])

    task = tasks.get_task(service.task_id_for(batch_id))
    self.assertEqual(ITEM_STATE_SUCCESS, item_of(task, "1")["state"])
    self.assertEqual(LIVE_STATUS_LIVING, item_of(task, "1")["metadata"]["live_status"])
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertEqual(STATE_LIVING, legacy_item(service, batch_id, "1")["state"])


class ProbeTaskSerialisationTest(unittest.TestCase):
  def test_a_checked_at_survives_as_a_string_on_the_wire(self):
    tasks = TaskService()
    service = build_service(FakeProber(), {"1": owner()}, task_service=tasks)

    batch_id = service.submit(["1"])

    payload = to_payload(tasks.get_task(service.task_id_for(batch_id)))
    checked_at = payload["items"][0]["metadata"]["checked_at"]
    self.assertIsInstance(checked_at, str)
    self.assertEqual("2026-08-13T20:30:00.000", checked_at)

  def test_a_cached_checked_at_survives_as_a_string_too(self):
    tasks = TaskService()
    service = build_service(FakeProber(), {"1": cached_owner(2)}, task_service=tasks)

    batch_id = service.submit(["1"])

    payload = to_payload(tasks.get_task(service.task_id_for(batch_id)))
    self.assertIsInstance(payload["items"][0]["metadata"]["checked_at"], str)

  def test_the_whole_task_payload_is_json_serialisable(self):
    import json

    tasks = TaskService()
    service = build_service(
      FakeProber(),
      {"1": owner(), "2": cached_owner(4, share_url="https://u/2")},
      task_service=tasks,
    )

    batch_id = service.submit(["1", "2", "missing"])

    json.dumps(to_payload(tasks.get_task(service.task_id_for(batch_id))))


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

  def update_message(self, *args, **kwargs):
    self._fail("update_message")

  def update_item(self, *args, **kwargs):
    self._fail("update_item")

  def update_progress(self, *args, **kwargs):
    self._fail("update_progress")

  def get_task(self, *args, **kwargs):
    self._fail("get_task")

  def finish_success(self, *args, **kwargs):
    self._fail("finish_success")

  def finish_partial(self, *args, **kwargs):
    self._fail("finish_partial")

  def finish_failed(self, *args, **kwargs):
    self._fail("finish_failed")


class ProbeTaskTelemetryFailureTest(unittest.TestCase):
  """Reporting is telemetry: a broken task layer must not change any probe."""

  def build(self, task_service, prober=None, **overrides):
    prober = prober if prober is not None else FakeProber()
    owners = {
      "1": owner(),
      "2": owner("https://u/2", nickname="B"),
      "3": cached_owner(4, share_url="https://u/3", nickname="C"),
      "4": owner(share_url=None, nickname="D"),
    }
    return prober, build_service(
      prober, owners, task_service=task_service, **overrides
    )

  def assert_legacy_batch_is_intact(self, service, prober, batch_id):
    snapshot = service.snapshot(batch_id)
    self.assertTrue(snapshot["done"])
    self.assertEqual(STATE_LIVING, legacy_item(service, batch_id, "1")["state"])
    self.assertEqual(STATE_LIVING, legacy_item(service, batch_id, "2")["state"])
    self.assertEqual(STATE_OFFLINE, legacy_item(service, batch_id, "3")["state"])
    self.assertEqual(STATE_ERROR, legacy_item(service, batch_id, "4")["state"])
    self.assertEqual(STATE_ERROR, legacy_item(service, batch_id, "missing")["state"])
    ##
    ## Both owners that needed the network were probed, and the cached one was
    ## not: a broken task layer costs no probe and provokes no extra one.
    ##
    self.assertEqual(["https://u/1", "https://u/2"], sorted(prober.calls))

  def test_a_task_layer_that_fails_everywhere_leaves_the_probe_untouched(self):
    prober, service = self.build(BrokenTaskService())

    batch_id = service.submit(["1", "2", "3", "4", "missing"])

    self.assert_legacy_batch_is_intact(service, prober, batch_id)

  def test_a_refused_task_leaves_the_response_without_a_task_id(self):
    prober, service = self.build(BrokenTaskService())

    batch_id = service.submit(["1", "2", "3", "4", "missing"])

    self.assertIsNone(service.task_id_for(batch_id))

  def test_nothing_further_is_attempted_once_creation_was_refused(self):
    broken = BrokenTaskService()
    prober, service = self.build(broken)

    service.submit(["1", "2", "3", "4", "missing"])

    self.assertEqual(["create_task"], broken.calls)

  def test_a_task_layer_that_fails_only_mid_batch_leaves_the_probe_untouched(self):
    class RefusesUpdates(TaskService):
      def update_item(self, *args, **kwargs):
        raise RuntimeError("item reporting unavailable")

    prober, service = self.build(RefusesUpdates())

    batch_id = service.submit(["1", "2", "3", "4", "missing"])

    self.assert_legacy_batch_is_intact(service, prober, batch_id)

  def test_a_task_that_cannot_be_ended_leaves_the_probe_untouched(self):
    class RefusesFinish(TaskService):
      def finish_success(self, *args, **kwargs):
        raise RuntimeError("finishing unavailable")

      def finish_partial(self, *args, **kwargs):
        raise RuntimeError("finishing unavailable")

      def finish_failed(self, *args, **kwargs):
        raise RuntimeError("finishing unavailable")

    tasks = RefusesFinish()
    prober, service = self.build(tasks)

    batch_id = service.submit(["1", "2", "3", "4", "missing"])

    self.assert_legacy_batch_is_intact(service, prober, batch_id)
    ##
    ## Stranded in ``running`` rather than mislabelled: the mirror could not end
    ## it, and saying so is better than inventing an outcome.
    ##
    self.assertEqual(
      TASK_STATE_RUNNING, tasks.get_task(service.task_id_for(batch_id))["state"]
    )

  def test_a_task_layer_that_fails_never_breaks_a_worker(self):
    from concurrent.futures import ThreadPoolExecutor

    class CountingExecutor:
      def __init__(self, pool):
        self._pool = pool
        self.futures = []

      def submit(self, fn, *args, **kwargs):
        future = self._pool.submit(fn, *args, **kwargs)
        self.futures.append(future)
        return future

      def shutdown(self, wait=False):
        self._pool.shutdown(wait=wait)

    pool = ThreadPoolExecutor(max_workers=2)
    executor = CountingExecutor(pool)
    prober, service = self.build(BrokenTaskService(), executor=executor)

    service.submit(["1", "2", "3", "4", "missing"])
    pool.shutdown(wait=True)

    ##
    ## Every worker returned normally.  ``result()`` re-raises whatever a worker
    ## raised, so a mirror failure escaping into the future would fail here.
    ##
    for future in executor.futures:
      self.assertIsNone(future.result())


class ProbeTaskConcurrentCompletionTest(unittest.TestCase):
  def test_owners_finishing_together_end_the_task_exactly_once(self):
    from concurrent.futures import ThreadPoolExecutor

    class CountingTaskService(TaskService):
      def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.finishes = []

      def finish_success(self, task_id, message=None):
        self.finishes.append("success")
        return super().finish_success(task_id, message=message)

      def finish_partial(self, task_id, message=None):
        self.finishes.append("partial")
        return super().finish_partial(task_id, message=message)

      def finish_failed(self, task_id, message=None):
        self.finishes.append("failed")
        return super().finish_failed(task_id, message=message)

    tasks = CountingTaskService()
    pool = ThreadPoolExecutor(max_workers=4)
    prober = FakeProber(crash_on=("https://u/4",))
    service = build_service(
      prober,
      {
        "1": owner(),
        "2": owner("https://u/2", nickname="B"),
        "3": owner("https://u/3", nickname="C"),
        "4": owner("https://u/4", nickname="D"),
      },
      task_service=tasks,
      executor=pool,
    )

    batch_id = service.submit(["1", "2", "3", "4"])
    pool.shutdown(wait=True)

    task = tasks.get_task(service.task_id_for(batch_id))
    self.assertEqual(["partial"], tasks.finishes)
    self.assertEqual(TASK_STATE_PARTIAL, task["state"])
    self.assertEqual({"current": 4, "total": 4}, task["progress"])
    self.assertTrue(service.snapshot(batch_id)["done"])


class RecordingLogger:
  """Captures what the mirror logged, so silence can be asserted."""

  def __init__(self):
    self.errors = []
    self.warnings = []

  def error(self, message):
    self.errors.append(message)

  def warning(self, message):
    self.warnings.append(message)

  def info(self, message):
    return None

  def debug(self, message):
    return None


class ProbeTaskFinishRaceTest(unittest.TestCase):
  """The last two workers landing together must not race the completion check.

  ``finish_if_complete`` reads the task, decides the batch is over and ends it.
  Left unserialised those three steps are a time-of-check/time-of-use window:
  two workers whose items both settled would each read "running, everything
  terminal" and each try to end the same task, and the transition table would
  reject the loser - a rejection that is a real error and would be logged as
  one, on a batch where nothing actually went wrong.
  """

  def run_race(self, outcomes):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from unittest.mock import patch

    from backend.src.service import live_probe_task_mirror

    ##
    ## Trips once both workers have written their terminal item, which puts them
    ## into the completion check together.  This is the window itself, forced to
    ## happen rather than waited for.
    ##
    gate = threading.Barrier(len(outcomes), timeout=5)
    ##
    ## Trips only if two workers are inside the completion check's read at the
    ## same moment - that is, only if "read, decide, finish" is not mutually
    ## exclusive.  A short timeout is what makes non-arrival the normal answer:
    ## when the section really is exclusive nobody has company and every waiter
    ## simply gives up.
    ##
    ##
    ## The wait only has to outlast the hand-off between two workers that were
    ## released together, which is a matter of microseconds; it is a race
    ## detector, not a wait for asynchronous work.
    ##
    detector = threading.Barrier(2, timeout=0.05)
    armed = [True]
    concurrent = []
    observed = []

    class GatedTaskService(TaskService):
      def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.finishes = []

      def get_task(self, task_id):
        result = super().get_task(task_id)
        if armed[0]:
          try:
            detector.wait()
            concurrent.append(True)
          except threading.BrokenBarrierError:
            ##
            ## Nobody else showed up: exclusion held for this pass.
            ##
            detector.reset()
        return result

      def update_item(self, task_id, key, state=None, **kwargs):
        recorded = super().update_item(task_id, key, state=state, **kwargs)
        if state in (ITEM_STATE_SUCCESS, ITEM_STATE_FAILED):
          ##
          ## Released only once every worker has settled.  What each worker sees
          ## is read after that release - the state it will carry into the
          ## completion check - not the snapshot of its own write, which for the
          ## first writer necessarily still has work outstanding.
          ##
          gate.wait()
          ##
          ## Straight to the base read: this observation is bookkeeping and must
          ## not register as a visitor to the section being watched.
          ##
          current = super().get_task(task_id)
          observed.append(
            current["state"]
            + ":"
            + str(
              all(
                item["state"] in (ITEM_STATE_SUCCESS, ITEM_STATE_FAILED)
                for item in current["items"]
              )
            )
          )
        return recorded

      def finish_success(self, task_id, message=None):
        self.finishes.append("success")
        return super().finish_success(task_id, message=message)

      def finish_partial(self, task_id, message=None):
        self.finishes.append("partial")
        return super().finish_partial(task_id, message=message)

      def finish_failed(self, task_id, message=None):
        self.finishes.append("failed")
        return super().finish_failed(task_id, message=message)

    tasks = GatedTaskService()
    pool = ThreadPoolExecutor(max_workers=len(outcomes))
    owners = {}
    results = {}
    crashing = []
    for index, outcome in enumerate(outcomes):
      key = str(index)
      url = "https://u/{}".format(index)
      owners[key] = owner(url, nickname=key)
      if outcome == "living":
        results[url] = FakeResult(room_status=2)
      elif outcome == "offline":
        results[url] = FakeResult(room_status=4)
      else:
        crashing.append(url)

    prober = FakeProber(results, crash_on=tuple(crashing))
    recorder = RecordingLogger()

    class TrackingExecutor:
      def __init__(self):
        self.futures = []

      def submit(self, fn, *args, **kwargs):
        future = pool.submit(fn, *args, **kwargs)
        self.futures.append(future)
        return future

      def shutdown(self, wait=False):
        pool.shutdown(wait=wait)

    executor = TrackingExecutor()
    service = build_service(
      prober, owners, task_service=tasks, executor=executor
    )

    with patch.object(
      live_probe_task_mirror, "get_logger", lambda *args, **kwargs: recorder
    ):
      batch_id = service.submit(list(owners.keys()))
      pool.shutdown(wait=True)

    ##
    ## The probing is over; the assertions below read the task normally.
    ##
    armed[0] = False
    return {
      "tasks": tasks,
      "task": tasks.get_task(service.task_id_for(batch_id)),
      "snapshot": service.snapshot(batch_id),
      "futures": executor.futures,
      "recorder": recorder,
      "observed": observed,
      "concurrent": concurrent,
    }

  def test_the_race_is_actually_provoked(self):
    outcome = self.run_race(["living", "living"])

    observed = outcome["observed"]

    ##
    ## Every worker reached the completion check, and by then the batch was over
    ## as far as its items were concerned - so each of them had grounds to end
    ## the task.  Without this the rest of this class would be asserting against
    ## a race that never happened.
    ##
    self.assertEqual(2, len(observed))
    self.assertTrue(all(entry.endswith(":True") for entry in observed))

    ##
    ## The first one through found the task complete but still running: the
    ## window is real.  What the second one finds is genuinely up to the
    ## scheduler - ``running`` when both stand in the window together,
    ## ``success`` when the winner got all the way through first - and asserting
    ## either would be asserting a thread interleaving rather than behaviour.
    ##
    self.assertEqual(TASK_STATE_RUNNING + ":True", observed[0])

  def test_no_two_workers_are_ever_inside_the_completion_check(self):
    outcome = self.run_race(["living", "living"])

    ##
    ## The guarantee itself, rather than one of its consequences: reading the
    ## task, judging the batch and ending it is one critical section, so a second
    ## worker can only look once the first has finished looking - and by then it
    ## sees a task that is already over.
    ##
    self.assertEqual([], outcome["concurrent"])

  def test_the_task_ends_exactly_once(self):
    outcome = self.run_race(["living", "living"])

    self.assertEqual(["success"], outcome["tasks"].finishes)
    self.assertEqual(TASK_STATE_SUCCESS, outcome["task"]["state"])

  def test_progress_is_complete_and_not_lost(self):
    outcome = self.run_race(["living", "offline"])

    self.assertEqual({"current": 2, "total": 2}, outcome["task"]["progress"])
    self.assertEqual(TASK_STATE_SUCCESS, outcome["task"]["state"])

  def test_a_mixed_race_still_lands_on_the_right_verdict(self):
    outcome = self.run_race(["living", "crash"])

    self.assertEqual(["partial"], outcome["tasks"].finishes)
    self.assertEqual(TASK_STATE_PARTIAL, outcome["task"]["state"])
    self.assertEqual({"current": 2, "total": 2}, outcome["task"]["progress"])

  def test_a_racing_finish_logs_nothing(self):
    outcome = self.run_race(["living", "living"])

    ##
    ## A rejected transition would arrive here as an error.  Losing the race is
    ## an ordinary outcome and must be silent; a genuine fault must not be.
    ##
    self.assertEqual([], outcome["recorder"].errors)
    self.assertEqual([], outcome["recorder"].warnings)

  def test_the_legacy_batch_is_unaffected_by_the_race(self):
    outcome = self.run_race(["living", "offline"])

    snapshot = outcome["snapshot"]
    self.assertTrue(snapshot["done"])
    self.assertEqual(
      {STATE_LIVING, STATE_OFFLINE}, {item["state"] for item in snapshot["items"]}
    )

  def test_no_worker_future_raises(self):
    outcome = self.run_race(["living", "crash"])

    for future in outcome["futures"]:
      self.assertIsNone(future.result())

  def test_three_workers_landing_together_still_end_the_task_once(self):
    outcome = self.run_race(["living", "offline", "crash"])

    self.assertEqual(["partial"], outcome["tasks"].finishes)
    self.assertEqual({"current": 3, "total": 3}, outcome["task"]["progress"])
    self.assertEqual([], outcome["recorder"].errors)


class ProbeTaskApiTest(unittest.TestCase):
  """The two surfaces side by side: the legacy batch and the unified task."""

  def build_app(self, owners=None, executor=None):
    from flask import Flask

    from backend.src.web.history_routes import build_history_blueprint
    from backend.src.web.task_routes import build_task_blueprint, install_task_service

    app = Flask(__name__)
    tasks = install_task_service(app)
    probe = build_service(
      FakeProber(),
      owners
      if owners is not None
      else {"1": owner(), "2": cached_owner(4, share_url="https://u/2", nickname="B")},
      task_service=tasks,
      **({"executor": executor} if executor is not None else {})
    )

    class Runtime:
      def page_size_limit(self):
        return 10

      def query(self):
        raise AssertionError("probing must not need the history query")

      def probe_service(self):
        return probe

    app.register_blueprint(build_history_blueprint(Runtime()))
    app.register_blueprint(build_task_blueprint())
    return app.test_client(), tasks, probe

  def test_an_accepted_probe_hands_back_both_identifiers(self):
    client, tasks, probe = self.build_app()

    response = client.post("/api/live/probe", json={"owner_user_ids": ["1", "2"]})
    body = response.get_json()

    self.assertEqual(202, response.status_code)
    self.assertEqual({"batch_id", "task_id", "done", "items"}, set(body["data"]))
    self.assertIsNotNone(body["data"]["task_id"])
    self.assertNotEqual(body["data"]["batch_id"], body["data"]["task_id"])

  def test_the_task_can_be_read_from_the_task_centre(self):
    client, tasks, probe = self.build_app()

    task_id = client.post(
      "/api/live/probe", json={"owner_user_ids": ["1", "2"]}
    ).get_json()["data"]["task_id"]
    response = client.get("/api/tasks/{}".format(task_id))
    task = response.get_json()["data"]

    self.assertEqual(200, response.status_code)
    self.assertEqual(TASK_TYPE_LIVE_PROBE, task["task_type"])
    self.assertEqual(PLATFORM_DOUYIN, task["metadata"]["platform"])
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])
    self.assertEqual({"current": 2, "total": 2}, task["progress"])

  def test_the_task_tells_living_and_offline_apart_by_metadata(self):
    client, tasks, probe = self.build_app()

    task_id = client.post(
      "/api/live/probe", json={"owner_user_ids": ["1", "2"]}
    ).get_json()["data"]["task_id"]
    task = client.get("/api/tasks/{}".format(task_id)).get_json()["data"]

    living = item_of(task, "1")
    offline = item_of(task, "2")
    self.assertEqual(ITEM_STATE_SUCCESS, living["state"])
    self.assertEqual(LIVE_STATUS_LIVING, living["metadata"]["live_status"])
    self.assertEqual(ITEM_STATE_SUCCESS, offline["state"])
    self.assertEqual(LIVE_STATUS_OFFLINE, offline["metadata"]["live_status"])
    self.assertIsInstance(living["metadata"]["checked_at"], str)

  def test_a_failed_owner_reaches_the_task_centre_as_a_failure(self):
    client, tasks, probe = self.build_app()

    task_id = client.post(
      "/api/live/probe", json={"owner_user_ids": ["1", "missing"]}
    ).get_json()["data"]["task_id"]
    task = client.get("/api/tasks/{}".format(task_id)).get_json()["data"]

    failed = item_of(task, "missing")
    self.assertEqual(ITEM_STATE_FAILED, failed["state"])
    self.assertEqual("历史记录中没有该主播", failed["message"])
    self.assertEqual(TASK_STATE_PARTIAL, task["state"])

  def test_polling_the_legacy_batch_is_unchanged(self):
    client, tasks, probe = self.build_app()

    batch_id = client.post(
      "/api/live/probe", json={"owner_user_ids": ["1", "2"]}
    ).get_json()["data"]["batch_id"]
    response = client.get("/api/live/probe/{}".format(batch_id))
    data = response.get_json()["data"]

    self.assertEqual(200, response.status_code)
    self.assertEqual({"batch_id", "done", "items"}, set(data))
    self.assertTrue(data["done"])
    self.assertEqual(
      {STATE_LIVING, STATE_OFFLINE}, {item["state"] for item in data["items"]}
    )

  def test_a_probe_and_a_download_share_one_task_store(self):
    from backend.src.task.model import TASK_TYPE_OWNER_BATCH_DOWNLOAD

    client, tasks, probe = self.build_app()
    ##
    ## Written straight onto the app's service, the way the owner mirror does.
    ##
    tasks.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, title="下载主播作品")

    probe_task_id = client.post(
      "/api/live/probe", json={"owner_user_ids": ["1"]}
    ).get_json()["data"]["task_id"]
    listing = client.get("/api/tasks").get_json()["data"]

    self.assertEqual(2, listing["total"])
    self.assertEqual(
      {TASK_TYPE_LIVE_PROBE, TASK_TYPE_OWNER_BATCH_DOWNLOAD},
      {task["task_type"] for task in listing["items"]},
    )
    self.assertIn(probe_task_id, {task["task_id"] for task in listing["items"]})

  def test_a_probe_still_running_is_visible_as_a_running_task(self):
    executor = DeferredExecutor()
    client, tasks, probe = self.build_app(
      owners={"1": owner(), "2": cached_owner(2, share_url="https://u/2", nickname="B")},
      executor=executor,
    )

    body = client.post(
      "/api/live/probe", json={"owner_user_ids": ["1", "2"]}
    ).get_json()["data"]
    task = client.get("/api/tasks/{}".format(body["task_id"])).get_json()["data"]

    self.assertIs(False, body["done"])
    self.assertEqual(TASK_STATE_RUNNING, task["state"])
    self.assertEqual({"current": 1, "total": 2}, task["progress"])

    executor.drain()

    finished = client.get("/api/tasks/{}".format(body["task_id"])).get_json()["data"]
    self.assertEqual(TASK_STATE_SUCCESS, finished["state"])
    self.assertTrue(client.get("/api/live/probe/{}".format(body["batch_id"])).get_json()["data"]["done"])

  def test_the_batch_association_survives_the_request_that_made_it(self):
    client, tasks, probe = self.build_app()

    body = client.post(
      "/api/live/probe", json={"owner_user_ids": ["1"]}
    ).get_json()["data"]

    ##
    ## Looked up again in a later request: the mirror holds the association for
    ## the life of the process, not for the life of a request context.
    ##
    self.assertEqual(body["task_id"], probe.task_id_for(body["batch_id"]))
    self.assertEqual(
      200, client.get("/api/tasks/{}".format(body["task_id"])).status_code
    )


if __name__ == "__main__":
  unittest.main()
