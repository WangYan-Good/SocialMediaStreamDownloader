import unittest
from datetime import datetime, timedelta

from backend.src.task.errors import (
  InvalidTaskTransition,
  TaskAlreadyFinished,
  TaskNotFound,
  UnknownTaskType,
)
from backend.src.task.model import (
  ITEM_STATE_FAILED,
  ITEM_STATE_PENDING,
  ITEM_STATE_RUNNING,
  ITEM_STATE_SKIPPED,
  ITEM_STATE_SUCCESS,
  TASK_STATE_CANCELLED,
  TASK_STATE_FAILED,
  TASK_STATE_PARTIAL,
  TASK_STATE_PENDING,
  TASK_STATE_RUNNING,
  TASK_STATE_SUCCESS,
  TASK_TYPE_LIVE_PROBE,
  TASK_TYPE_LIVE_RECORD,
  TASK_TYPE_OWNER_BATCH_DOWNLOAD,
  TASK_TYPE_POST_DOWNLOAD,
)
from backend.src.task.service import TaskService
from backend.src.task.store import TaskStore


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


def build_service(clock=None, retention_seconds=600.0):
  clock = clock if clock is not None else FakeClock()
  return TaskService(
    store=TaskStore(
      retention_seconds=retention_seconds,
      clock=clock.now,
      monotonic_clock=clock.monotonic,
    )
  )


class TaskCreationTest(unittest.TestCase):
  def test_a_created_task_comes_back_pending_with_its_id(self):
    service = build_service()

    task = service.create_task(TASK_TYPE_POST_DOWNLOAD, title="下载作品")

    self.assertTrue(task["task_id"])
    self.assertEqual(task["state"], TASK_STATE_PENDING)
    self.assertEqual(task["title"], "下载作品")

  def test_creation_carries_items_metadata_and_total(self):
    service = build_service()

    task = service.create_task(
      TASK_TYPE_OWNER_BATCH_DOWNLOAD,
      title="批量下载",
      metadata={"sec_user_id": "MS4w"},
      items=["a", "b"],
    )

    self.assertEqual([item["key"] for item in task["items"]], ["a", "b"])
    self.assertEqual(task["metadata"], {"sec_user_id": "MS4w"})
    self.assertEqual(task["progress"], {"current": 0, "total": 2})

  def test_an_unregistered_type_is_refused(self):
    service = build_service()

    with self.assertRaises(UnknownTaskType):
      service.create_task("live_recording")

  def test_a_created_task_is_immediately_visible(self):
    service = build_service()

    task = service.create_task(TASK_TYPE_LIVE_PROBE)

    self.assertEqual(service.get_task(task["task_id"])["task_id"], task["task_id"])


class TaskLifecycleTest(unittest.TestCase):
  """The service names the lifecycle so no caller writes a state string."""

  def running_task(self, service, task_type=TASK_TYPE_POST_DOWNLOAD, **kwargs):
    task = service.create_task(task_type, **kwargs)
    service.start_task(task["task_id"])
    return task["task_id"]

  def test_starting_a_task_makes_it_running(self):
    clock = FakeClock()
    service = build_service(clock)
    task = service.create_task(TASK_TYPE_POST_DOWNLOAD)

    clock.advance(3)
    started = service.start_task(task["task_id"])

    self.assertEqual(started["state"], TASK_STATE_RUNNING)
    self.assertEqual(started["started_at"], clock.wall)

  def test_a_task_cannot_be_started_twice(self):
    service = build_service()
    task_id = self.running_task(service)

    with self.assertRaises(InvalidTaskTransition):
      service.start_task(task_id)

  def test_finishing_successfully_records_the_end_state(self):
    service = build_service()
    task_id = self.running_task(service)

    finished = service.finish_success(task_id, message="3 个作品全部下载完成")

    self.assertEqual(finished["state"], TASK_STATE_SUCCESS)
    self.assertEqual(finished["message"], "3 个作品全部下载完成")
    self.assertIsNotNone(finished["finished_at"])

  def test_finishing_partially_records_the_end_state(self):
    service = build_service()
    task_id = self.running_task(service, items=["a", "b"])

    finished = service.finish_partial(task_id, message="2 个中有 1 个失败")

    self.assertEqual(finished["state"], TASK_STATE_PARTIAL)

  def test_failing_records_the_end_state(self):
    service = build_service()
    task_id = self.running_task(service)

    finished = service.finish_failed(task_id, message="登录已失效")

    self.assertEqual(finished["state"], TASK_STATE_FAILED)
    self.assertEqual(finished["message"], "登录已失效")

  def test_a_queued_task_may_fail_before_it_starts(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_POST_DOWNLOAD)

    finished = service.finish_failed(task["task_id"], message="链接无法解析")

    self.assertEqual(finished["state"], TASK_STATE_FAILED)
    self.assertIsNone(finished["started_at"])

  def test_cancelling_marks_the_task_cancelled(self):
    service = build_service()
    task_id = self.running_task(service, task_type=TASK_TYPE_LIVE_RECORD)

    cancelled = service.cancel_task(task_id, message="用户取消")

    self.assertEqual(cancelled["state"], TASK_STATE_CANCELLED)
    self.assertEqual(cancelled["message"], "用户取消")

  def test_a_queued_task_may_be_cancelled_before_it_starts(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_LIVE_RECORD)

    cancelled = service.cancel_task(task["task_id"])

    self.assertEqual(cancelled["state"], TASK_STATE_CANCELLED)

  def test_a_finished_task_cannot_be_cancelled(self):
    service = build_service()
    task_id = self.running_task(service)
    service.finish_success(task_id)

    with self.assertRaises(InvalidTaskTransition):
      service.cancel_task(task_id)

  def test_every_lifecycle_call_rejects_an_unknown_task(self):
    service = build_service()

    for call in (
      service.start_task,
      service.finish_success,
      service.finish_partial,
      service.finish_failed,
      service.cancel_task,
    ):
      with self.assertRaises(TaskNotFound):
        call("nope")


class TaskProgressTest(unittest.TestCase):
  def test_progress_can_be_reported_directly(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, total=42)

    updated = service.update_progress(task["task_id"], current=18)

    self.assertEqual(updated["progress"], {"current": 18, "total": 42})

  def test_a_total_learned_later_can_be_reported_on_its_own(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    updated = service.update_progress(task["task_id"], total=238)

    self.assertEqual(updated["progress"], {"current": 0, "total": 238})

  def test_progress_on_an_unknown_task_is_refused(self):
    with self.assertRaises(TaskNotFound):
      build_service().update_progress("nope", current=1)


class TaskItemTest(unittest.TestCase):
  def test_an_item_update_is_recorded(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"])

    updated = service.update_item(
      task["task_id"], "a", state=ITEM_STATE_FAILED, message="下载超时"
    )

    self.assertEqual(updated["items"][0]["state"], ITEM_STATE_FAILED)
    self.assertEqual(updated["items"][0]["message"], "下载超时")

  def test_finished_items_move_the_task_progress(self):
    """Every batch migration would otherwise count its own items by hand."""
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a", "b", "c"])

    service.update_item(task["task_id"], "a", state=ITEM_STATE_SUCCESS)
    updated = service.update_item(task["task_id"], "b", state=ITEM_STATE_FAILED)

    self.assertEqual(updated["progress"], {"current": 2, "total": 3})

  def test_an_item_still_running_does_not_count_as_progress(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a", "b"])

    updated = service.update_item(task["task_id"], "a", state=ITEM_STATE_RUNNING)

    self.assertEqual(updated["progress"]["current"], 0)

  def test_a_skipped_item_counts_as_finished(self):
    """Already downloaded is not pending; the bar must not stall on it."""
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a", "b"])

    updated = service.update_item(task["task_id"], "a", state=ITEM_STATE_SKIPPED)

    self.assertEqual(updated["progress"]["current"], 1)

  def test_a_growing_task_grows_its_total_with_its_items(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    service.update_item(task["task_id"], "a", state=ITEM_STATE_SUCCESS)
    updated = service.update_item(task["task_id"], "b", state=ITEM_STATE_RUNNING)

    self.assertEqual(updated["progress"]["current"], 1)

  def test_a_caller_owning_its_own_progress_can_opt_out(self):
    """A recording counts segments, not items, and must keep its own number."""
    service = build_service()
    task = service.create_task(TASK_TYPE_LIVE_RECORD, items=["a", "b"])
    service.update_progress(task["task_id"], current=97, total=None)

    updated = service.update_item(
      task["task_id"], "a", state=ITEM_STATE_SUCCESS, advance_progress=False
    )

    self.assertEqual(updated["progress"], {"current": 97, "total": None})

  def test_an_item_of_an_unknown_task_is_refused(self):
    with self.assertRaises(TaskNotFound):
      build_service().update_item("nope", "a", state=ITEM_STATE_SUCCESS)


class TaskMessageTest(unittest.TestCase):
  """The service is what business code narrates a long task through."""

  def test_a_long_task_can_narrate_its_stages(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, title="下载张三的作品")
    service.start_task(task["task_id"])

    stages = ["正在解析主播", "正在读取第 3 页", "正在下载 18 / 42"]
    seen = [
      service.update_message(task["task_id"], stage)["message"] for stage in stages
    ]

    self.assertEqual(seen, stages)
    self.assertEqual(service.get_task(task["task_id"])["state"], TASK_STATE_RUNNING)

  def test_narrating_does_not_disturb_progress_or_items(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a", "b"])
    service.start_task(task["task_id"])
    service.update_item(task["task_id"], "a", state=ITEM_STATE_SUCCESS)

    narrated = service.update_message(task["task_id"], "正在下载 2 / 2")

    self.assertEqual(narrated["progress"], {"current": 1, "total": 2})
    self.assertEqual(len(narrated["items"]), 2)

  def test_a_finished_task_cannot_be_narrated(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_POST_DOWNLOAD)
    service.start_task(task["task_id"])
    service.finish_success(task["task_id"], message="全部完成")

    with self.assertRaises(TaskAlreadyFinished):
      service.update_message(task["task_id"], "迟到的日志")

    self.assertEqual(service.get_task(task["task_id"])["message"], "全部完成")

  def test_narrating_an_unknown_task_is_refused(self):
    with self.assertRaises(TaskNotFound):
      build_service().update_message("nope", "正在解析主播")


class TaskItemRegistrationTest(unittest.TestCase):
  """A task that discovers its work registers it as it goes."""

  def test_discovered_work_is_registered_pending(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    updated = service.add_item(task["task_id"], "7657271784144009946")

    self.assertEqual(updated["items"][0]["key"], "7657271784144009946")
    self.assertEqual(updated["items"][0]["state"], ITEM_STATE_PENDING)

  def test_seeing_the_same_work_twice_registers_it_once(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    service.add_item(task["task_id"], "a")
    updated = service.add_item(task["task_id"], "a")

    self.assertEqual(len(updated["items"]), 1)

  def test_re_registering_never_undoes_finished_work(self):
    service = build_service()
    task = service.create_task(TASK_TYPE_OWNER_BATCH_DOWNLOAD)
    service.add_item(task["task_id"], "a")
    service.update_item(task["task_id"], "a", state=ITEM_STATE_SUCCESS)

    updated = service.add_item(task["task_id"], "a")

    self.assertEqual(updated["items"][0]["state"], ITEM_STATE_SUCCESS)
    self.assertEqual(updated["progress"]["current"], 1)

  def test_registering_on_an_unknown_task_is_refused(self):
    with self.assertRaises(TaskNotFound):
      build_service().add_item("nope", "a")


class TaskReadTest(unittest.TestCase):
  def test_an_unknown_task_reads_as_nothing(self):
    """A browser polling a task the store has dropped is expected, not an error."""
    self.assertIsNone(build_service().get_task("nope"))

  def test_tasks_list_newest_first(self):
    service = build_service()
    first = service.create_task(TASK_TYPE_LIVE_PROBE)
    second = service.create_task(TASK_TYPE_POST_DOWNLOAD)

    listed = service.list_tasks()

    self.assertEqual(
      [task["task_id"] for task in listed], [second["task_id"], first["task_id"]]
    )

  def test_tasks_can_be_listed_by_state_and_type(self):
    service = build_service()
    probe = service.create_task(TASK_TYPE_LIVE_PROBE)
    download = service.create_task(TASK_TYPE_POST_DOWNLOAD)
    service.start_task(download["task_id"])

    by_state = service.list_tasks(state=TASK_STATE_RUNNING)
    by_type = service.list_tasks(task_type=TASK_TYPE_LIVE_PROBE)

    self.assertEqual([task["task_id"] for task in by_state], [download["task_id"]])
    self.assertEqual([task["task_id"] for task in by_type], [probe["task_id"]])

  def test_a_limit_keeps_the_newest(self):
    service = build_service()
    service.create_task(TASK_TYPE_LIVE_PROBE)
    newest = service.create_task(TASK_TYPE_LIVE_PROBE)

    listed = service.list_tasks(limit=1)

    self.assertEqual([task["task_id"] for task in listed], [newest["task_id"]])

  def test_a_service_without_a_store_still_holds_its_tasks(self):
    """The default store is real, so a bare TaskService() is usable."""
    service = TaskService()

    task = service.create_task(TASK_TYPE_LIVE_PROBE)

    self.assertEqual(len(service.list_tasks()), 1)
    self.assertIsNotNone(service.get_task(task["task_id"]))

  def test_finished_tasks_stop_being_listed_once_stale(self):
    clock = FakeClock()
    service = build_service(clock, retention_seconds=10.0)
    task = service.create_task(TASK_TYPE_POST_DOWNLOAD)
    service.start_task(task["task_id"])
    service.finish_success(task["task_id"])

    clock.advance(11)

    self.assertEqual(service.list_tasks(), [])


class ServiceMetadataUpdateTest(unittest.TestCase):
  """Results learned while a task runs reach the record through the service."""

  def test_results_can_be_recorded_before_the_task_ends(self):
    service = TaskService()
    task = service.create_task(
      TASK_TYPE_POST_DOWNLOAD, metadata={"platform": "douyin"}, total=1
    )
    service.start_task(task["task_id"])

    service.update_metadata(task["task_id"], {"result": {"ok": True, "saved": 3}})

    metadata = service.get_task(task["task_id"])["metadata"]
    self.assertEqual("douyin", metadata["platform"])
    self.assertEqual({"ok": True, "saved": 3}, metadata["result"])

  def test_the_updated_task_is_returned(self):
    service = TaskService()
    task = service.create_task(TASK_TYPE_POST_DOWNLOAD)

    returned = service.update_metadata(task["task_id"], {"aweme_id": "123"})

    self.assertEqual("123", returned["metadata"]["aweme_id"])

  def test_an_unknown_task_is_refused(self):
    service = TaskService()

    with self.assertRaises(TaskNotFound):
      service.update_metadata("nope", {"aweme_id": "123"})

  def test_a_finished_task_is_refused(self):
    service = TaskService()
    task = service.create_task(TASK_TYPE_POST_DOWNLOAD)
    service.start_task(task["task_id"])
    service.finish_success(task["task_id"])

    with self.assertRaises(TaskAlreadyFinished):
      service.update_metadata(task["task_id"], {"result": {"ok": True}})


if __name__ == "__main__":
  unittest.main()
