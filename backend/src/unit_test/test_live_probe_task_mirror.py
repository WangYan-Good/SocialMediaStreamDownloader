import unittest
from datetime import datetime, timedelta

from backend.src.service.live_probe_task_mirror import (
  LIVE_STATUS_LIVING,
  LIVE_STATUS_OFFLINE,
  PLATFORM_DOUYIN,
  LiveProbeTaskMirror,
)
from backend.src.task.model import (
  ITEM_STATE_FAILED,
  ITEM_STATE_PENDING,
  ITEM_STATE_RUNNING,
  ITEM_STATE_SUCCESS,
  TASK_STATE_FAILED,
  TASK_STATE_PARTIAL,
  TASK_STATE_RUNNING,
  TASK_STATE_SUCCESS,
  TASK_TYPE_LIVE_PROBE,
)
from backend.src.task.service import TaskService


def build_mirror(task_service=None):
  service = task_service if task_service is not None else TaskService()
  return LiveProbeTaskMirror(service), service


def open_batch(mirror, batch_id="batch-1", items=("1", "2"), requested=None):
  """Open a batch the way LiveProbeService will, returning the task id."""
  owners = list(items)
  return mirror.open(
    batch_id,
    title="检查 {} 个主播直播状态".format(len(owners)),
    metadata={
      "platform": PLATFORM_DOUYIN,
      "legacy_batch_id": batch_id,
      "requested_count": len(owners) if requested is None else requested,
    },
    items=owners,
  )


def item_of(task: dict, key: str) -> dict:
  return next(item for item in task["items"] if item["key"] == key)


class MirrorCreationTest(unittest.TestCase):
  def test_opening_a_batch_creates_a_live_probe_task(self):
    mirror, service = build_mirror()

    task_id = open_batch(mirror, items=("1", "2"))

    task = service.get_task(task_id)
    self.assertEqual(TASK_TYPE_LIVE_PROBE, task["task_type"])
    self.assertEqual("检查 2 个主播直播状态", task["title"])

  def test_the_task_records_the_platform_and_the_legacy_batch(self):
    mirror, service = build_mirror()

    task_id = open_batch(mirror, batch_id="batch-9", items=("1", "2", "3"))

    metadata = service.get_task(task_id)["metadata"]
    self.assertEqual(PLATFORM_DOUYIN, metadata["platform"])
    self.assertEqual("batch-9", metadata["legacy_batch_id"])
    self.assertEqual(3, metadata["requested_count"])

  def test_every_owner_starts_as_a_pending_item(self):
    mirror, service = build_mirror()

    task_id = open_batch(mirror, items=("1", "2"))

    task = service.get_task(task_id)
    self.assertEqual(["1", "2"], [item["key"] for item in task["items"]])
    self.assertTrue(
      all(item["state"] == ITEM_STATE_PENDING for item in task["items"])
    )

  def test_the_total_is_the_number_of_owners(self):
    mirror, service = build_mirror()

    task_id = open_batch(mirror, items=("1", "2", "3"))

    self.assertEqual({"current": 0, "total": 3}, service.get_task(task_id)["progress"])

  def test_the_task_id_can_be_looked_up_by_batch_id(self):
    mirror, unused = build_mirror()

    task_id = open_batch(mirror, batch_id="batch-7")

    self.assertEqual(task_id, mirror.task_id("batch-7"))

  def test_an_unknown_batch_has_no_task(self):
    mirror, unused = build_mirror()

    self.assertIsNone(mirror.task_id("never-opened"))

  def test_a_mirror_without_a_task_service_reports_nothing(self):
    mirror = LiveProbeTaskMirror(None)

    self.assertFalse(mirror.enabled)
    self.assertIsNone(open_batch(mirror))
    self.assertIsNone(mirror.task_id("batch-1"))

  def test_a_mirror_without_a_task_service_never_raises(self):
    mirror = LiveProbeTaskMirror(None)
    open_batch(mirror)

    mirror.start("batch-1")
    mirror.item_running("batch-1", "1")
    mirror.item_living("batch-1", "1")
    mirror.item_offline("batch-1", "2")
    mirror.item_failed("batch-1", "3", "探测失败")
    mirror.finish_if_complete("batch-1")

    self.assertEqual(0, mirror.tracked())


class MirrorItemStateTest(unittest.TestCase):
  def setUp(self):
    self.mirror, self.service = build_mirror()
    self.task_id = open_batch(self.mirror, items=("1", "2"))
    self.mirror.start("batch-1")

  def test_starting_moves_the_task_to_running(self):
    self.assertEqual(TASK_STATE_RUNNING, self.service.get_task(self.task_id)["state"])

  def test_an_owner_being_probed_is_running(self):
    self.mirror.item_running("batch-1", "1")

    task = self.service.get_task(self.task_id)
    self.assertEqual(ITEM_STATE_RUNNING, item_of(task, "1")["state"])
    self.assertEqual(0, task["progress"]["current"])

  def test_a_living_owner_is_a_successful_item(self):
    self.mirror.item_living(
      "batch-1",
      "1",
      nickname="张三",
      room_id="123456",
      title="直播标题",
      live_share_url="https://u/1",
      checked_at=datetime(2026, 8, 13, 20, 30, 0),
      cached=False,
    )

    item = item_of(self.service.get_task(self.task_id), "1")
    self.assertEqual(ITEM_STATE_SUCCESS, item["state"])
    self.assertEqual(LIVE_STATUS_LIVING, item["metadata"]["live_status"])
    self.assertEqual("张三", item["metadata"]["nickname"])
    self.assertEqual("123456", item["metadata"]["room_id"])
    self.assertEqual("直播标题", item["metadata"]["title"])
    self.assertEqual("https://u/1", item["metadata"]["live_share_url"])
    self.assertIs(False, item["metadata"]["cached"])

  def test_an_offline_owner_is_a_successful_item_too(self):
    self.mirror.item_offline("batch-1", "2", nickname="李四", cached=True)

    item = item_of(self.service.get_task(self.task_id), "2")
    self.assertEqual(ITEM_STATE_SUCCESS, item["state"])
    self.assertEqual(LIVE_STATUS_OFFLINE, item["metadata"]["live_status"])
    self.assertIs(True, item["metadata"]["cached"])

  def test_offline_is_never_recorded_as_a_task_item_state(self):
    self.mirror.item_offline("batch-1", "2")

    item = item_of(self.service.get_task(self.task_id), "2")
    self.assertNotEqual("offline", item["state"])
    self.assertNotEqual(ITEM_STATE_FAILED, item["state"])

  def test_a_probe_that_could_not_answer_is_a_failed_item(self):
    self.mirror.item_failed("batch-1", "1", "请求超时")

    item = item_of(self.service.get_task(self.task_id), "1")
    self.assertEqual(ITEM_STATE_FAILED, item["state"])
    self.assertEqual("请求超时", item["message"])

  def test_a_checked_at_datetime_is_stored_as_a_string(self):
    self.mirror.item_living(
      "batch-1", "1", checked_at=datetime(2026, 8, 13, 20, 30, 0)
    )

    metadata = item_of(self.service.get_task(self.task_id), "1")["metadata"]
    self.assertIsInstance(metadata["checked_at"], str)
    self.assertEqual("2026-08-13T20:30:00.000", metadata["checked_at"])

  def test_a_checked_at_string_is_kept_as_it_is(self):
    self.mirror.item_living("batch-1", "1", checked_at="2026-08-13T20:30:00.000")

    metadata = item_of(self.service.get_task(self.task_id), "1")["metadata"]
    self.assertEqual("2026-08-13T20:30:00.000", metadata["checked_at"])

  def test_facts_the_platform_did_not_give_are_left_out(self):
    self.mirror.item_offline("batch-1", "2", nickname="李四")

    metadata = item_of(self.service.get_task(self.task_id), "2")["metadata"]
    self.assertNotIn("title", metadata)
    self.assertNotIn("room_id", metadata)
    self.assertNotIn("checked_at", metadata)

  def test_a_failed_item_carries_no_live_status(self):
    self.mirror.item_failed("batch-1", "1", "历史记录中没有该主播")

    metadata = item_of(self.service.get_task(self.task_id), "1")["metadata"]
    self.assertNotIn("live_status", metadata)

  def test_settling_an_owner_advances_progress(self):
    self.mirror.item_living("batch-1", "1")
    self.assertEqual(1, self.service.get_task(self.task_id)["progress"]["current"])

    self.mirror.item_failed("batch-1", "2", "探测失败")
    self.assertEqual(2, self.service.get_task(self.task_id)["progress"]["current"])


class MirrorTerminalStateTest(unittest.TestCase):
  def settle(self, outcomes):
    """Open a batch, settle each owner as told, and return the finished task."""
    mirror, service = build_mirror()
    keys = [str(index) for index in range(len(outcomes))]
    task_id = open_batch(mirror, items=keys)
    mirror.start("batch-1")
    for key, outcome in zip(keys, outcomes):
      if outcome == "living":
        mirror.item_living("batch-1", key)
      elif outcome == "cached_living":
        mirror.item_living("batch-1", key, cached=True)
      elif outcome == "offline":
        mirror.item_offline("batch-1", key)
      elif outcome == "cached_offline":
        mirror.item_offline("batch-1", key, cached=True)
      else:
        mirror.item_failed("batch-1", key, "探测失败")
      mirror.finish_if_complete("batch-1")
    return service.get_task(task_id)

  def test_a_batch_that_answered_for_everyone_is_a_success(self):
    self.assertEqual(
      TASK_STATE_SUCCESS, self.settle(["living", "offline", "cached_living"])["state"]
    )

  def test_offline_alone_is_still_a_success(self):
    self.assertEqual(TASK_STATE_SUCCESS, self.settle(["offline", "offline"])["state"])

  def test_a_fully_cached_batch_is_a_success(self):
    self.assertEqual(
      TASK_STATE_SUCCESS, self.settle(["cached_living", "cached_offline"])["state"]
    )

  def test_living_beside_a_failure_is_partial(self):
    self.assertEqual(TASK_STATE_PARTIAL, self.settle(["living", "failed"])["state"])

  def test_offline_beside_a_failure_is_partial(self):
    self.assertEqual(TASK_STATE_PARTIAL, self.settle(["offline", "failed"])["state"])

  def test_a_batch_that_answered_for_nobody_is_a_failure(self):
    self.assertEqual(TASK_STATE_FAILED, self.settle(["failed", "failed"])["state"])

  def test_a_finished_batch_reports_full_progress(self):
    task = self.settle(["living", "failed"])

    self.assertEqual({"current": 2, "total": 2}, task["progress"])

  def test_an_unfinished_batch_is_left_running(self):
    mirror, service = build_mirror()
    task_id = open_batch(mirror, items=("1", "2"))
    mirror.start("batch-1")

    mirror.item_living("batch-1", "1")
    mirror.finish_if_complete("batch-1")

    task = service.get_task(task_id)
    self.assertEqual(TASK_STATE_RUNNING, task["state"])
    self.assertEqual({"current": 1, "total": 2}, task["progress"])

  def test_a_second_completion_check_keeps_the_first_answer(self):
    mirror, service = build_mirror()
    task_id = open_batch(mirror, items=("1",))
    mirror.start("batch-1")
    mirror.item_living("batch-1", "1")

    mirror.finish_if_complete("batch-1")
    mirror.finish_if_complete("batch-1")

    self.assertEqual(TASK_STATE_SUCCESS, service.get_task(task_id)["state"])


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


class RefusingUpdates(TaskService):
  """Creates tasks, then refuses every per-owner report."""

  def update_item(self, *args, **kwargs):
    raise RuntimeError("item reporting unavailable")


class RefusingFinish(TaskService):
  """Runs normally until the task is asked to end."""

  def finish_success(self, *args, **kwargs):
    raise RuntimeError("finishing unavailable")

  def finish_partial(self, *args, **kwargs):
    raise RuntimeError("finishing unavailable")

  def finish_failed(self, *args, **kwargs):
    raise RuntimeError("finishing unavailable")


class MirrorTelemetryFailureTest(unittest.TestCase):
  def test_a_refused_creation_leaves_the_batch_unmirrored(self):
    broken = BrokenTaskService()
    mirror = LiveProbeTaskMirror(broken)

    self.assertIsNone(open_batch(mirror))
    self.assertIsNone(mirror.task_id("batch-1"))
    self.assertEqual(0, mirror.tracked())

  def test_every_later_report_is_a_no_op_once_creation_was_refused(self):
    broken = BrokenTaskService()
    mirror = LiveProbeTaskMirror(broken)
    open_batch(mirror)

    mirror.start("batch-1")
    mirror.item_running("batch-1", "1")
    mirror.item_living("batch-1", "1")
    mirror.item_offline("batch-1", "2")
    mirror.item_failed("batch-1", "3", "探测失败")
    mirror.finish_if_complete("batch-1")

    ##
    ## Only the refused creation reached the task layer; nothing else even tried,
    ## because a batch with no task has nothing to report against.
    ##
    self.assertEqual(["create_task"], broken.calls)

  def test_a_task_layer_that_fails_mid_batch_never_raises(self):
    mirror = LiveProbeTaskMirror(RefusingUpdates())
    open_batch(mirror, items=("1", "2"))
    mirror.start("batch-1")

    mirror.item_running("batch-1", "1")
    mirror.item_living("batch-1", "1")
    mirror.item_failed("batch-1", "2", "探测失败")
    mirror.finish_if_complete("batch-1")

  def test_a_refused_finish_never_raises(self):
    service = RefusingFinish()
    mirror = LiveProbeTaskMirror(service)
    task_id = open_batch(mirror, items=("1",))
    mirror.start("batch-1")
    mirror.item_living("batch-1", "1")

    mirror.finish_if_complete("batch-1")

    ##
    ## The task is stranded in ``running`` - which is honest, the mirror could
    ## not end it - and nothing was raised at the caller.
    ##
    self.assertEqual(TASK_STATE_RUNNING, service.get_task(task_id)["state"])

  def test_a_failure_to_report_one_owner_does_not_strand_the_others(self):
    class RefusesOwnerTwo(TaskService):
      def update_item(self, task_id, key, *args, **kwargs):
        if str(key) == "2":
          raise RuntimeError("item reporting unavailable")
        return super().update_item(task_id, key, *args, **kwargs)

    service = RefusesOwnerTwo()
    mirror = LiveProbeTaskMirror(service)
    task_id = open_batch(mirror, items=("1", "2"))
    mirror.start("batch-1")

    mirror.item_living("batch-1", "1")
    mirror.item_living("batch-1", "2")
    mirror.finish_if_complete("batch-1")

    task = service.get_task(task_id)
    self.assertEqual(ITEM_STATE_SUCCESS, item_of(task, "1")["state"])
    self.assertEqual(ITEM_STATE_PENDING, item_of(task, "2")["state"])
    self.assertEqual(TASK_STATE_RUNNING, task["state"])


class FakeClock:
  def __init__(self, start=datetime(2026, 8, 13, 9, 0, 0)):
    self.wall = start
    self.mono = 0.0

  def now(self):
    return self.wall

  def monotonic(self):
    return self.mono

  def advance(self, seconds):
    self.wall = self.wall + timedelta(seconds=seconds)
    self.mono += seconds


def build_expiring_mirror(retention_seconds=600.0):
  from backend.src.task.store import TaskStore

  clock = FakeClock()
  service = TaskService(
    TaskStore(
      retention_seconds=retention_seconds,
      clock=clock.now,
      monotonic_clock=clock.monotonic,
    )
  )
  return LiveProbeTaskMirror(service), service, clock


def finish_batch(mirror, batch_id, items=("1",)):
  open_batch(mirror, batch_id=batch_id, items=items)
  mirror.start(batch_id)
  for key in items:
    mirror.item_living(batch_id, key)
  mirror.finish_if_complete(batch_id)


class MirrorAssociationLifetimeTest(unittest.TestCase):
  def test_the_task_id_still_answers_after_the_batch_ends(self):
    mirror, service, unused = build_expiring_mirror()
    finish_batch(mirror, "batch-1")

    task_id = mirror.task_id("batch-1")
    self.assertIsNotNone(task_id)
    self.assertEqual(TASK_STATE_SUCCESS, service.get_task(task_id)["state"])

  def test_an_association_does_not_outlive_the_task_it_points_at(self):
    mirror, service, clock = build_expiring_mirror(retention_seconds=600.0)
    finish_batch(mirror, "batch-1")

    clock.advance(601.0)
    ##
    ## Pruning is lazy: opening the next batch is what clears the last one.
    ##
    finish_batch(mirror, "batch-2")

    self.assertIsNone(mirror.task_id("batch-1"))
    self.assertEqual(1, mirror.tracked())

  def test_associations_stay_bounded_over_many_batches(self):
    mirror, service, clock = build_expiring_mirror(retention_seconds=600.0)

    for index in range(50):
      finish_batch(mirror, "batch-{}".format(index))
      clock.advance(601.0)

    ##
    ## Every batch but the newest has been evicted from the task store, so the
    ## map holds one entry rather than fifty.
    ##
    self.assertEqual(1, mirror.tracked())

  def test_a_batch_still_running_is_never_pruned(self):
    mirror, service, clock = build_expiring_mirror(retention_seconds=600.0)
    open_batch(mirror, batch_id="slow", items=("1",))
    mirror.start("slow")

    clock.advance(10000.0)
    finish_batch(mirror, "batch-2")

    self.assertIsNotNone(mirror.task_id("slow"))
    self.assertEqual(2, mirror.tracked())


class CountingTaskService(TaskService):
  """Counts how many times a task was asked to end."""

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


class MirrorConcurrentCompletionTest(unittest.TestCase):
  def race(self, outcomes):
    """Settle every owner from its own thread, all finishing at once."""
    import threading

    service = CountingTaskService()
    mirror = LiveProbeTaskMirror(service)
    keys = [str(index) for index in range(len(outcomes))]
    task_id = open_batch(mirror, items=keys)
    mirror.start("batch-1")

    gate = threading.Barrier(len(keys))
    raised = []

    def settle(key, outcome):
      try:
        if outcome == "living":
          mirror.item_living("batch-1", key)
        else:
          mirror.item_failed("batch-1", key, "探测失败")
        ##
        ## Every worker arrives at the completion check together, which is the
        ## moment two of them could both believe they ended the batch.
        ##
        gate.wait()
        mirror.finish_if_complete("batch-1")
      except Exception as e:
        raised.append(e)

    threads = [
      threading.Thread(target=settle, args=(key, outcome))
      for key, outcome in zip(keys, outcomes)
    ]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join()

    return service, service.get_task(task_id), raised

  def test_two_owners_finishing_together_end_the_task_once(self):
    service, task, raised = self.race(["living", "living"])

    self.assertEqual([], raised)
    self.assertEqual(["success"], service.finishes)
    self.assertEqual(TASK_STATE_SUCCESS, task["state"])

  def test_a_racing_finish_does_not_lose_progress(self):
    service, task, raised = self.race(["living", "living", "living"])

    self.assertEqual({"current": 3, "total": 3}, task["progress"])
    self.assertEqual(["success"], service.finishes)

  def test_a_racing_finish_still_judges_the_batch_correctly(self):
    service, task, raised = self.race(["living", "failed"])

    self.assertEqual([], raised)
    self.assertEqual(["partial"], service.finishes)
    self.assertEqual(TASK_STATE_PARTIAL, task["state"])


if __name__ == "__main__":
  unittest.main()
