import unittest
from datetime import datetime, timedelta

from backend.src.task.errors import (
  InvalidProgress,
  InvalidTaskItemState,
  InvalidTaskState,
  InvalidTaskTransition,
  TaskAlreadyFinished,
  TaskNotFound,
  UnknownTaskType,
)
from backend.src.task.model import (
  ITEM_STATE_FAILED,
  ITEM_STATE_PENDING,
  ITEM_STATE_RUNNING,
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
from backend.src.task.store import TaskStore


class FakeClock:
  """One handle over both clocks the store needs.

  Wall time is what the user reads; monotonic time is what expiry counts.  Tests
  move them together so a scenario reads as one timeline.
  """

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


def build_store(clock=None, retention_seconds=600.0, **overrides):
  clock = clock if clock is not None else FakeClock()
  return TaskStore(
    retention_seconds=retention_seconds,
    clock=clock.now,
    monotonic_clock=clock.monotonic,
    **overrides,
  )


class TaskCreationTest(unittest.TestCase):
  def test_an_owned_task_keeps_its_application_user(self):
    store = build_store()

    task_id = store.create(TASK_TYPE_POST_DOWNLOAD, app_user_id=17)

    self.assertEqual(store.get(task_id)["app_user_id"], 17)

  def test_task_ownership_has_no_transfer_mutator(self):
    store = build_store()

    self.assertFalse(hasattr(store, "set_owner"))
    self.assertFalse(hasattr(store, "transfer_owner"))

  def test_an_anonymous_task_is_explicitly_unowned(self):
    store = build_store()

    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)

    self.assertIsNone(store.get(task_id)["app_user_id"])

  def test_a_new_task_starts_pending_with_its_creation_time(self):
    clock = FakeClock()
    store = build_store(clock)

    task_id = store.create(TASK_TYPE_POST_DOWNLOAD, title="下载作品")
    task = store.get(task_id)

    self.assertEqual(task["task_id"], task_id)
    self.assertEqual(task["task_type"], TASK_TYPE_POST_DOWNLOAD)
    self.assertEqual(task["state"], TASK_STATE_PENDING)
    self.assertEqual(task["title"], "下载作品")
    self.assertIsNone(task["message"])
    self.assertEqual(task["created_at"], clock.wall)
    self.assertIsNone(task["started_at"])
    self.assertIsNone(task["finished_at"])
    self.assertEqual(task["metadata"], {})
    self.assertEqual(task["items"], [])

  def test_a_task_without_items_has_no_known_total(self):
    """A live recording runs until it stops; there is nothing to divide by."""
    store = build_store()

    task_id = store.create(TASK_TYPE_LIVE_RECORD)

    self.assertEqual(store.get(task_id)["progress"], {"current": 0, "total": None})

  def test_ids_are_unique(self):
    store = build_store(
      max_active_global=256,
      max_active_by_type={TASK_TYPE_LIVE_PROBE: 256},
    )

    ids = {store.create(TASK_TYPE_LIVE_PROBE) for _ in range(200)}

    self.assertEqual(len(ids), 200)

  def test_items_are_registered_pending_in_submission_order(self):
    store = build_store()

    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["c", "a", "b"])
    items = store.get(task_id)["items"]

    self.assertEqual([item["key"] for item in items], ["c", "a", "b"])
    self.assertEqual([item["state"] for item in items], [ITEM_STATE_PENDING] * 3)
    self.assertEqual(items[0]["message"], None)
    self.assertEqual(items[0]["metadata"], {})

  def test_item_keys_are_normalised_to_text(self):
    store = build_store()

    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=[7657271784144009946])

    self.assertEqual(store.get(task_id)["items"][0]["key"], "7657271784144009946")

  def test_a_known_item_count_becomes_the_total(self):
    store = build_store()

    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a", "b", "c"])

    self.assertEqual(store.get(task_id)["progress"], {"current": 0, "total": 3})

  def test_a_key_listed_twice_is_one_item(self):
    store = build_store()

    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["1", "2", "1"])

    self.assertEqual(
      [item["key"] for item in store.get(task_id)["items"]], ["1", "2"]
    )

  def test_a_derived_total_counts_the_items_that_exist(self):
    """A total no item list can ever reach would strand the bar at 2 / 3."""
    store = build_store()

    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["1", "2", "1"])

    self.assertEqual(store.get(task_id)["progress"], {"current": 0, "total": 2})

  def test_an_explicit_total_wins_over_the_item_count(self):
    """"Download everything" knows the count before it has the items."""
    store = build_store()

    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"], total=238)

    self.assertEqual(store.get(task_id)["progress"]["total"], 238)

  def test_an_explicit_unknown_total_is_kept(self):
    store = build_store()

    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"], total=None)

    self.assertIsNone(store.get(task_id)["progress"]["total"])

  def test_metadata_is_detached_from_the_caller(self):
    store = build_store()
    metadata = {"sec_user_id": "MS4w"}

    task_id = store.create(TASK_TYPE_POST_DOWNLOAD, metadata=metadata)
    metadata["sec_user_id"] = "tampered"

    self.assertEqual(store.get(task_id)["metadata"], {"sec_user_id": "MS4w"})

  def test_an_unregistered_type_cannot_create_a_task(self):
    store = build_store()

    with self.assertRaises(UnknownTaskType):
      store.create("post_dowload")

    self.assertEqual(store.tracked(), 0)

  def test_an_unknown_task_has_no_snapshot(self):
    self.assertIsNone(build_store().get("nope"))


class TaskOwnershipQueryTest(unittest.TestCase):
  def setUp(self):
    self.store = build_store()
    self.a = self.store.create(TASK_TYPE_POST_DOWNLOAD, app_user_id=1)
    self.b = self.store.create(TASK_TYPE_LIVE_RECORD, app_user_id=2)
    self.unowned = self.store.create(TASK_TYPE_POST_DOWNLOAD)

  def test_scoped_list_only_returns_the_requested_users_tasks(self):
    self.assertEqual(
      [task["task_id"] for task in self.store.list_for_user(1)],
      [self.a],
    )

  def test_scoped_get_hides_another_users_task_as_missing(self):
    self.assertIsNone(self.store.get_for_user(self.b, 1))
    self.assertEqual(self.store.get_for_user(self.a, 1)["task_id"], self.a)

  def test_global_list_still_contains_owned_and_unowned_tasks(self):
    self.assertEqual(
      {task["task_id"] for task in self.store.list()},
      {self.a, self.b, self.unowned},
    )

  def test_owner_scope_composes_with_type_and_state_filters(self):
    self.store.set_state(self.a, TASK_STATE_RUNNING)

    self.assertEqual(
      [task["task_id"] for task in self.store.list_for_user(
        1,
        state=TASK_STATE_RUNNING,
        task_type=TASK_TYPE_POST_DOWNLOAD,
      )],
      [self.a],
    )
    self.assertEqual(
      self.store.list_for_user(1, state=TASK_STATE_PENDING),
      [],
    )

  def test_owner_scope_does_not_change_terminal_task_retention(self):
    clock = FakeClock()
    store = build_store(clock, retention_seconds=5)
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD, app_user_id=1)
    store.set_state(task_id, TASK_STATE_RUNNING)
    store.set_state(task_id, TASK_STATE_SUCCESS)

    clock.advance(6)

    self.assertIsNone(store.get_for_user(task_id, 1))


class TaskStateTest(unittest.TestCase):
  def test_starting_a_task_records_when_it_started(self):
    clock = FakeClock()
    store = build_store(clock)
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)

    clock.advance(5)
    store.set_state(task_id, TASK_STATE_RUNNING)
    task = store.get(task_id)

    self.assertEqual(task["state"], TASK_STATE_RUNNING)
    self.assertEqual(task["started_at"], clock.wall)
    self.assertIsNone(task["finished_at"])

  def test_a_successful_task_records_when_it_finished(self):
    clock = FakeClock()
    store = build_store(clock)
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.set_state(task_id, TASK_STATE_RUNNING)

    clock.advance(30)
    store.set_state(task_id, TASK_STATE_SUCCESS, message="全部完成")
    task = store.get(task_id)

    self.assertEqual(task["state"], TASK_STATE_SUCCESS)
    self.assertEqual(task["message"], "全部完成")
    self.assertEqual(task["finished_at"], clock.wall)

  def test_a_failed_task_keeps_its_reason(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.set_state(task_id, TASK_STATE_RUNNING)

    store.set_state(task_id, TASK_STATE_FAILED, message="停在第 1 个作品")

    self.assertEqual(store.get(task_id)["message"], "停在第 1 个作品")

  def test_a_partly_successful_task_ends_partial(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a", "b"])
    store.set_state(task_id, TASK_STATE_RUNNING)

    store.set_state(task_id, TASK_STATE_PARTIAL, message="2 个中有 1 个失败")

    self.assertEqual(store.get(task_id)["state"], TASK_STATE_PARTIAL)

  def test_a_queued_task_can_be_cancelled_before_it_runs(self):
    clock = FakeClock()
    store = build_store(clock)
    task_id = store.create(TASK_TYPE_LIVE_RECORD)

    clock.advance(2)
    store.set_state(task_id, TASK_STATE_CANCELLED)
    task = store.get(task_id)

    self.assertEqual(task["state"], TASK_STATE_CANCELLED)
    self.assertIsNone(task["started_at"])
    self.assertEqual(task["finished_at"], clock.wall)

  def test_an_illegal_transition_raises_and_changes_nothing(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.set_state(task_id, TASK_STATE_RUNNING)
    store.set_state(task_id, TASK_STATE_SUCCESS)

    with self.assertRaises(InvalidTaskTransition):
      store.set_state(task_id, TASK_STATE_FAILED, message="迟到的失败")

    task = store.get(task_id)
    self.assertEqual(task["state"], TASK_STATE_SUCCESS)
    self.assertIsNone(task["message"])

  def test_an_unknown_state_is_refused(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)

    with self.assertRaises(InvalidTaskState):
      store.set_state(task_id, "done")

  def test_changing_an_unknown_task_is_an_error_not_a_silent_no_op(self):
    with self.assertRaises(TaskNotFound):
      build_store().set_state("nope", TASK_STATE_RUNNING)

  def test_setting_a_state_returns_the_new_snapshot(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)

    task = store.set_state(task_id, TASK_STATE_RUNNING)

    self.assertEqual(task["state"], TASK_STATE_RUNNING)


class TaskMessageTest(unittest.TestCase):
  """A running task narrates itself without changing state each time."""

  def test_a_running_task_can_report_what_it_is_doing(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)
    store.set_state(task_id, TASK_STATE_RUNNING)

    for narration in ("正在解析主播", "正在读取第 3 页", "正在下载 18 / 42"):
      task = store.update_message(task_id, narration)
      self.assertEqual(task["message"], narration)
      self.assertEqual(task["state"], TASK_STATE_RUNNING)

  def test_narrating_is_not_a_state_transition(self):
    """running -> running is illegal; saying what running means is not."""
    clock = FakeClock()
    store = build_store(clock)
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)
    store.set_state(task_id, TASK_STATE_RUNNING)
    started_at = store.get(task_id)["started_at"]

    clock.advance(60)
    store.update_message(task_id, "正在读取第 3 页")
    task = store.get(task_id)

    self.assertEqual(task["started_at"], started_at)
    self.assertIsNone(task["finished_at"])

  def test_a_queued_task_can_report_its_position(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)

    task = store.update_message(task_id, "排队中，前面还有 2 个")

    self.assertEqual(task["state"], TASK_STATE_PENDING)
    self.assertEqual(task["message"], "排队中，前面还有 2 个")

  def test_a_message_can_be_cleared(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.update_message(task_id, "排队中")

    self.assertIsNone(store.update_message(task_id, None)["message"])

  def test_a_finished_task_keeps_the_reason_it_finished_with(self):
    """A late log line must not overwrite why the task ended."""
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.set_state(task_id, TASK_STATE_RUNNING)
    store.set_state(task_id, TASK_STATE_FAILED, message="登录已失效")

    with self.assertRaises(TaskAlreadyFinished):
      store.update_message(task_id, "正在下载 18 / 42")

    self.assertEqual(store.get(task_id)["message"], "登录已失效")

  def test_narrating_an_unknown_task_is_an_error(self):
    with self.assertRaises(TaskNotFound):
      build_store().update_message("nope", "正在解析主播")


class TaskProgressTest(unittest.TestCase):
  def test_progress_moves_forward(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a", "b"])

    store.update_progress(task_id, current=1)

    self.assertEqual(store.get(task_id)["progress"], {"current": 1, "total": 2})

  def test_a_total_discovered_later_can_be_set(self):
    """The owner walk learns its size only once the first page comes back."""
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    store.update_progress(task_id, total=42)

    self.assertEqual(store.get(task_id)["progress"], {"current": 0, "total": 42})

  def test_updating_only_the_current_leaves_the_total_alone(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, total=42)

    store.update_progress(task_id, current=18)

    self.assertEqual(store.get(task_id)["progress"], {"current": 18, "total": 42})

  def test_a_total_can_be_set_back_to_unknown(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, total=42)

    store.update_progress(task_id, total=None)

    self.assertIsNone(store.get(task_id)["progress"]["total"])

  def test_negative_progress_is_refused(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    with self.assertRaises(InvalidProgress):
      store.update_progress(task_id, current=-1)

  def test_progress_on_an_unknown_task_is_an_error(self):
    with self.assertRaises(TaskNotFound):
      build_store().update_progress("nope", current=1)


class TaskItemTest(unittest.TestCase):
  def test_an_item_carries_its_state_message_and_metadata(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"])

    store.update_item(
      task_id,
      "a",
      state=ITEM_STATE_FAILED,
      message="下载超时",
      metadata={"saved": 0, "planned": 3},
    )
    item = store.get(task_id)["items"][0]

    self.assertEqual(item["state"], ITEM_STATE_FAILED)
    self.assertEqual(item["message"], "下载超时")
    self.assertEqual(item["metadata"], {"saved": 0, "planned": 3})

  def test_an_item_key_may_be_addressed_as_a_number(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=[123])

    store.update_item(task_id, 123, state=ITEM_STATE_SUCCESS)

    self.assertEqual(store.get(task_id)["items"][0]["state"], ITEM_STATE_SUCCESS)

  def test_a_task_may_grow_items_while_it_runs(self):
    """The owner walk discovers its posts page by page."""
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    store.update_item(task_id, "a", state=ITEM_STATE_SUCCESS)
    store.update_item(task_id, "b", state=ITEM_STATE_RUNNING)
    items = store.get(task_id)["items"]

    self.assertEqual([item["key"] for item in items], ["a", "b"])
    self.assertEqual(items[0]["state"], ITEM_STATE_SUCCESS)

  def test_an_omitted_field_keeps_its_previous_value(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"])
    store.update_item(task_id, "a", state=ITEM_STATE_RUNNING, message="开始")

    store.update_item(task_id, "a", state=ITEM_STATE_SUCCESS)
    item = store.get(task_id)["items"][0]

    self.assertEqual(item["state"], ITEM_STATE_SUCCESS)
    self.assertEqual(item["message"], "开始")

  def test_a_message_can_be_cleared(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"])
    store.update_item(task_id, "a", state=ITEM_STATE_FAILED, message="下载超时")

    store.update_item(task_id, "a", state=ITEM_STATE_SUCCESS, message=None)

    self.assertIsNone(store.get(task_id)["items"][0]["message"])

  def test_a_task_state_is_not_accepted_as_an_item_state(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"])

    with self.assertRaises(InvalidTaskItemState):
      store.update_item(task_id, "a", state=TASK_STATE_PARTIAL)

  def test_updating_an_item_of_an_unknown_task_is_an_error(self):
    with self.assertRaises(TaskNotFound):
      build_store().update_item("nope", "a", state=ITEM_STATE_SUCCESS)

  def test_an_item_update_leaves_progress_alone_by_default(self):
    """The store records; deciding what progress means is the service's job."""
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a", "b"])

    store.update_item(task_id, "a", state=ITEM_STATE_SUCCESS)

    self.assertEqual(store.get(task_id)["progress"]["current"], 0)

  def test_progress_can_follow_the_finished_items_atomically(self):
    """Counting outside the lock would let two workers write a stale total."""
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a", "b", "c"])

    store.update_item(
      task_id, "a", state=ITEM_STATE_SUCCESS, advance_progress=True
    )
    task = store.update_item(
      task_id, "b", state=ITEM_STATE_FAILED, advance_progress=True
    )

    self.assertEqual(task["progress"], {"current": 2, "total": 3})

  def test_advancing_progress_counts_only_finished_items(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a", "b"])

    task = store.update_item(
      task_id, "a", state=ITEM_STATE_RUNNING, advance_progress=True
    )

    self.assertEqual(task["progress"]["current"], 0)

  def test_parallel_item_updates_leave_progress_consistent(self):
    store = build_store()
    keys = ["key-{}".format(index) for index in range(200)]
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=keys)
    import threading

    ready = threading.Barrier(8)

    def run(index):
      ready.wait()
      for key in keys[index * 25:(index + 1) * 25]:
        store.update_item(
          task_id, key, state=ITEM_STATE_SUCCESS, advance_progress=True
        )

    threads = [threading.Thread(target=run, args=(index,)) for index in range(8)]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join()

    self.assertEqual(store.get(task_id)["progress"], {"current": 200, "total": 200})


class TaskItemRegistrationTest(unittest.TestCase):
  """Registering work discovered while the task runs, without losing any."""

  def test_a_new_key_is_registered_pending(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    task = store.add_item(task_id, "a")

    self.assertEqual([item["key"] for item in task["items"]], ["a"])
    self.assertEqual(task["items"][0]["state"], ITEM_STATE_PENDING)

  def test_discovery_order_is_preserved(self):
    """Pages arrive in order and the list the user watches must match."""
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    for key in ("c", "a", "b"):
      store.add_item(task_id, key)

    self.assertEqual(
      [item["key"] for item in store.get(task_id)["items"]], ["c", "a", "b"]
    )

  def test_registering_a_known_key_changes_nothing(self):
    """A post seen twice while paging must not be reset to pending."""
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)
    store.add_item(task_id, "a")
    store.update_item(task_id, "a", state=ITEM_STATE_SUCCESS, message="已保存 3 个")

    task = store.add_item(task_id, "a")

    self.assertEqual(len(task["items"]), 1)
    self.assertEqual(task["items"][0]["state"], ITEM_STATE_SUCCESS)
    self.assertEqual(task["items"][0]["message"], "已保存 3 个")

  def test_registering_a_known_key_does_not_disturb_progress(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)
    store.add_item(task_id, "a")
    store.update_item(task_id, "a", state=ITEM_STATE_SUCCESS, advance_progress=True)

    task = store.add_item(task_id, "a")

    self.assertEqual(task["progress"]["current"], 1)

  def test_registering_a_new_key_does_not_count_as_progress(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    task = store.add_item(task_id, "a")

    self.assertEqual(task["progress"], {"current": 0, "total": None})

  def test_registering_does_not_invent_a_total(self):
    """A walk still in progress has no total; only its end knows one."""
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, total=None)

    store.add_item(task_id, "a")
    store.add_item(task_id, "b")

    self.assertIsNone(store.get(task_id)["progress"]["total"])

  def test_a_key_is_normalised_to_text(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    store.add_item(task_id, 7657271784144009946)
    store.add_item(task_id, "7657271784144009946")

    self.assertEqual(len(store.get(task_id)["items"]), 1)

  def test_a_first_registration_may_carry_its_own_details(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    store.add_item(task_id, "a", message="第 2 页", metadata={"page": 2})
    item = store.get(task_id)["items"][0]

    self.assertEqual(item["message"], "第 2 页")
    self.assertEqual(item["metadata"], {"page": 2})

  def test_registering_on_an_unknown_task_is_an_error(self):
    with self.assertRaises(TaskNotFound):
      build_store().add_item("nope", "a")

  def test_parallel_discovery_registers_each_key_once(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)
    import threading

    ready = threading.Barrier(8)

    def run(index):
      ready.wait()
      for key in ("key-{}".format(step) for step in range(50)):
        store.add_item(task_id, key)

    threads = [threading.Thread(target=run, args=(index,)) for index in range(8)]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join()

    self.assertEqual(len(store.get(task_id)["items"]), 50)


class SnapshotIsolationTest(unittest.TestCase):
  """A caller must never be able to reach into the store through a snapshot."""

  def test_mutating_a_snapshot_does_not_change_the_store(self):
    store = build_store()
    task_id = store.create(
      TASK_TYPE_OWNER_BATCH_DOWNLOAD,
      title="批量下载",
      metadata={"sec_user_id": "MS4w"},
      items=["a"],
    )

    snapshot = store.get(task_id)
    snapshot["state"] = "tampered"
    snapshot["metadata"]["sec_user_id"] = "tampered"
    snapshot["progress"]["current"] = 999
    snapshot["items"][0]["state"] = "tampered"
    snapshot["items"].append({"key": "injected"})

    fresh = store.get(task_id)
    self.assertEqual(fresh["state"], TASK_STATE_PENDING)
    self.assertEqual(fresh["metadata"], {"sec_user_id": "MS4w"})
    self.assertEqual(fresh["progress"]["current"], 0)
    self.assertEqual([item["key"] for item in fresh["items"]], ["a"])
    self.assertEqual(fresh["items"][0]["state"], ITEM_STATE_PENDING)

  def test_item_metadata_is_detached_from_the_caller(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"])
    metadata = {"saved": 1}

    store.update_item(task_id, "a", metadata=metadata)
    metadata["saved"] = 999

    self.assertEqual(store.get(task_id)["items"][0]["metadata"], {"saved": 1})

  def test_nested_metadata_survives_a_tampered_snapshot(self):
    """Metadata is arbitrary business data, so it nests; copying one level deep
    would hand the caller a live reference to everything below it."""
    store = build_store()
    task_id = store.create(
      TASK_TYPE_OWNER_BATCH_DOWNLOAD,
      metadata={"filters": {"types": ["video"], "since": None}, "pages": [1, 2]},
    )

    snapshot = store.get(task_id)
    snapshot["metadata"]["filters"]["types"].append("tampered")
    snapshot["metadata"]["filters"]["since"] = "tampered"
    snapshot["metadata"]["pages"].append(999)

    fresh = store.get(task_id)
    self.assertEqual(fresh["metadata"]["filters"], {"types": ["video"], "since": None})
    self.assertEqual(fresh["metadata"]["pages"], [1, 2])

  def test_nested_metadata_is_detached_from_the_caller_at_creation(self):
    store = build_store()
    metadata = {"filters": {"types": ["video"]}}

    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, metadata=metadata)
    metadata["filters"]["types"].append("tampered")

    self.assertEqual(store.get(task_id)["metadata"], {"filters": {"types": ["video"]}})

  def test_nested_item_metadata_survives_a_tampered_snapshot(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"])
    store.update_item(task_id, "a", metadata={"saved": {"urls": ["u1"]}})

    snapshot = store.get(task_id)
    snapshot["items"][0]["metadata"]["saved"]["urls"].append("tampered")

    self.assertEqual(
      store.get(task_id)["items"][0]["metadata"], {"saved": {"urls": ["u1"]}}
    )

  def test_nested_item_metadata_is_detached_from_the_caller_at_update(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"])
    metadata = {"saved": {"urls": ["u1"]}}

    store.update_item(task_id, "a", metadata=metadata)
    metadata["saved"]["urls"].append("tampered")

    self.assertEqual(
      store.get(task_id)["items"][0]["metadata"], {"saved": {"urls": ["u1"]}}
    )

  def test_a_listing_hands_out_detached_nested_metadata(self):
    store = build_store()
    task_id = store.create(
      TASK_TYPE_OWNER_BATCH_DOWNLOAD, metadata={"filters": {"types": ["video"]}}
    )

    store.list()[0]["metadata"]["filters"]["types"].append("tampered")

    self.assertEqual(
      store.get(task_id)["metadata"], {"filters": {"types": ["video"]}}
    )

  def test_two_snapshots_do_not_share_nested_objects(self):
    store = build_store()
    task_id = store.create(
      TASK_TYPE_OWNER_BATCH_DOWNLOAD, metadata={"filters": {"types": ["video"]}}
    )

    first = store.get(task_id)
    second = store.get(task_id)

    self.assertIsNot(first["metadata"]["filters"], second["metadata"]["filters"])

  def test_two_snapshots_do_not_share_objects(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"])

    first = store.get(task_id)
    second = store.get(task_id)

    self.assertIsNot(first["items"][0], second["items"][0])
    self.assertIsNot(first["progress"], second["progress"])
    self.assertIsNot(first["metadata"], second["metadata"])


class TaskListingTest(unittest.TestCase):
  def build_three(self, store):
    probe = store.create(TASK_TYPE_LIVE_PROBE, title="探测")
    download = store.create(TASK_TYPE_POST_DOWNLOAD, title="下载")
    store.set_state(download, TASK_STATE_RUNNING)
    batch = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, title="批量")
    store.set_state(batch, TASK_STATE_RUNNING)
    store.set_state(batch, TASK_STATE_SUCCESS)
    return probe, download, batch

  def test_an_empty_store_lists_nothing(self):
    self.assertEqual(build_store().list(), [])

  def test_the_newest_task_comes_first(self):
    """A task centre opens on what the user just submitted."""
    store = build_store()
    probe, download, batch = self.build_three(store)

    listed = [task["task_id"] for task in store.list()]

    self.assertEqual(listed, [batch, download, probe])

  def test_tasks_can_be_filtered_by_state(self):
    store = build_store()
    probe, download, batch = self.build_three(store)

    listed = store.list(state=TASK_STATE_RUNNING)

    self.assertEqual([task["task_id"] for task in listed], [download])

  def test_tasks_can_be_filtered_by_type(self):
    store = build_store()
    probe, download, batch = self.build_three(store)

    listed = store.list(task_type=TASK_TYPE_LIVE_PROBE)

    self.assertEqual([task["task_id"] for task in listed], [probe])

  def test_both_filters_apply_together(self):
    store = build_store()
    probe, download, batch = self.build_three(store)

    listed = store.list(state=TASK_STATE_RUNNING, task_type=TASK_TYPE_LIVE_PROBE)

    self.assertEqual(listed, [])

  def test_a_limit_keeps_the_newest(self):
    store = build_store()
    probe, download, batch = self.build_three(store)

    listed = store.list(limit=2)

    self.assertEqual([task["task_id"] for task in listed], [batch, download])

  def test_a_limit_larger_than_the_store_is_harmless(self):
    store = build_store()
    self.build_three(store)

    self.assertEqual(len(store.list(limit=100)), 3)

  def test_an_unknown_state_filter_is_refused(self):
    store = build_store()

    with self.assertRaises(InvalidTaskState):
      store.list(state="done")

  def test_an_unknown_type_filter_is_refused(self):
    store = build_store()

    with self.assertRaises(UnknownTaskType):
      store.list(task_type="post_dowload")

  def test_a_limit_below_one_is_refused(self):
    store = build_store()

    for limit in (0, -1):
      with self.assertRaises(ValueError):
        store.list(limit=limit)

  def test_a_non_integer_limit_is_refused(self):
    store = build_store()

    with self.assertRaises(ValueError):
      store.list(limit="2")

  def test_listed_tasks_are_copies(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD, items=["a"])

    store.list()[0]["items"][0]["state"] = "tampered"

    self.assertEqual(store.get(task_id)["items"][0]["state"], ITEM_STATE_PENDING)


class TaskRetentionTest(unittest.TestCase):
  """Finished tasks expire; work still in flight does not."""

  def finished_task(self, store):
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.set_state(task_id, TASK_STATE_RUNNING)
    store.set_state(task_id, TASK_STATE_SUCCESS)
    return task_id

  def test_a_finished_task_survives_its_retention_window(self):
    clock = FakeClock()
    store = build_store(clock, retention_seconds=100.0)
    task_id = self.finished_task(store)

    clock.advance(99)

    self.assertIsNotNone(store.get(task_id))

  def test_a_finished_task_is_dropped_once_it_is_stale(self):
    clock = FakeClock()
    store = build_store(clock, retention_seconds=100.0)
    task_id = self.finished_task(store)

    clock.advance(101)

    self.assertIsNone(store.get(task_id))
    self.assertEqual(store.tracked(), 0)

  def test_retention_counts_from_the_end_not_from_the_start(self):
    clock = FakeClock()
    store = build_store(clock, retention_seconds=100.0)
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.set_state(task_id, TASK_STATE_RUNNING)

    clock.advance(500)
    store.set_state(task_id, TASK_STATE_SUCCESS)
    clock.advance(50)

    self.assertIsNotNone(store.get(task_id))

  def test_a_running_task_is_never_evicted(self):
    """A live recording runs for hours and must not vanish while it does."""
    clock = FakeClock()
    store = build_store(clock, retention_seconds=100.0)
    task_id = store.create(TASK_TYPE_LIVE_RECORD)
    store.set_state(task_id, TASK_STATE_RUNNING)

    clock.advance(100000)

    self.assertIsNotNone(store.get(task_id))

  def test_a_pending_task_is_never_evicted(self):
    clock = FakeClock()
    store = build_store(clock, retention_seconds=100.0)
    task_id = store.create(TASK_TYPE_LIVE_RECORD)

    clock.advance(100000)

    self.assertIsNotNone(store.get(task_id))

  def test_every_end_state_expires(self):
    for terminal in (TASK_STATE_FAILED, TASK_STATE_PARTIAL, TASK_STATE_CANCELLED):
      clock = FakeClock()
      store = build_store(clock, retention_seconds=10.0)
      task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
      store.set_state(task_id, TASK_STATE_RUNNING)
      store.set_state(task_id, terminal)

      clock.advance(11)

      self.assertIsNone(store.get(task_id), terminal)

  def test_creating_a_task_evicts_stale_ones(self):
    clock = FakeClock()
    store = build_store(clock, retention_seconds=10.0)
    self.finished_task(store)

    clock.advance(11)
    store.create(TASK_TYPE_POST_DOWNLOAD)

    self.assertEqual(store.tracked(), 1)

  def test_listing_does_not_return_stale_tasks(self):
    clock = FakeClock()
    store = build_store(clock, retention_seconds=10.0)
    self.finished_task(store)

    clock.advance(11)

    self.assertEqual(store.list(), [])

  def test_finished_tasks_do_not_accumulate(self):
    clock = FakeClock()
    store = build_store(clock, retention_seconds=5.0)

    for _ in range(50):
      clock.advance(6)
      self.finished_task(store)

    self.assertEqual(store.tracked(), 1)


class TaskConcurrencyTest(unittest.TestCase):
  """The store is written from download threads and read from request threads."""

  def run_together(self, worker, count):
    import threading

    ready = threading.Barrier(count)
    failures = []

    def run(index):
      ready.wait()
      try:
        worker(index)
      except Exception as e:
        failures.append(e)

    threads = [threading.Thread(target=run, args=(index,)) for index in range(count)]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join()
    return failures

  def test_parallel_item_updates_are_all_recorded(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD)

    def worker(index):
      for step in range(25):
        store.update_item(
          task_id,
          "{}-{}".format(index, step),
          state=ITEM_STATE_SUCCESS,
        )

    failures = self.run_together(worker, 8)
    items = store.get(task_id)["items"]

    self.assertEqual(failures, [])
    self.assertEqual(len(items), 200)
    self.assertEqual({item["state"] for item in items}, {ITEM_STATE_SUCCESS})

  def test_parallel_creation_never_reuses_an_id(self):
    store = build_store(
      max_active_global=256,
      max_active_by_type={TASK_TYPE_LIVE_PROBE: 256},
    )
    created = []

    def worker(index):
      for _ in range(25):
        created.append(store.create(TASK_TYPE_LIVE_PROBE))

    failures = self.run_together(worker, 8)

    self.assertEqual(failures, [])
    self.assertEqual(len(set(created)), 200)
    self.assertEqual(store.tracked(), 200)

  def test_only_one_thread_can_finish_a_task(self):
    """Two workers believing they finished the same task is a real defect."""
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.set_state(task_id, TASK_STATE_RUNNING)

    def worker(index):
      store.set_state(task_id, TASK_STATE_SUCCESS)

    failures = self.run_together(worker, 10)

    self.assertEqual(len(failures), 9)
    self.assertTrue(
      all(isinstance(failure, InvalidTaskTransition) for failure in failures)
    )
    self.assertEqual(store.get(task_id)["state"], TASK_STATE_SUCCESS)

  def test_reading_while_writing_never_sees_a_half_written_task(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_OWNER_BATCH_DOWNLOAD, items=["a"])
    seen = []

    def worker(index):
      if index == 0:
        for step in range(200):
          store.update_progress(task_id, current=step)
        return
      for _ in range(200):
        seen.append(store.get(task_id))

    failures = self.run_together(worker, 4)

    self.assertEqual(failures, [])
    for task in seen:
      self.assertEqual(task["progress"]["total"], 1)
      self.assertEqual(len(task["items"]), 1)


class TaskMetadataUpdateTest(unittest.TestCase):
  """Facts a task only learns while it runs.

  A task that is its own unit of work - one post download - has results that do
  not exist when it is created: where the files landed, how many were saved, why
  it could not finish.  Those belong to the task itself rather than to an item,
  so there has to be a way to write them after creation.
  """

  def test_a_field_can_be_added_after_creation(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD, metadata={"platform": "douyin"})

    store.update_metadata(task_id, {"result": {"ok": True}})

    metadata = store.get(task_id)["metadata"]
    self.assertEqual({"ok": True}, metadata["result"])

  def test_what_was_already_there_is_kept(self):
    store = build_store()
    task_id = store.create(
      TASK_TYPE_POST_DOWNLOAD,
      metadata={"platform": "douyin", "aweme_id": "123"},
    )

    store.update_metadata(task_id, {"result": {"ok": True}})

    metadata = store.get(task_id)["metadata"]
    self.assertEqual("douyin", metadata["platform"])
    self.assertEqual("123", metadata["aweme_id"])

  def test_a_stated_field_replaces_the_one_it_names(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD, metadata={"stage": "resolving"})

    store.update_metadata(task_id, {"stage": "downloading"})

    self.assertEqual("downloading", store.get(task_id)["metadata"]["stage"])

  def test_the_merge_is_one_level_deep(self):
    store = build_store()
    task_id = store.create(
      TASK_TYPE_POST_DOWNLOAD, metadata={"result": {"ok": False, "reason": "gone"}}
    )

    store.update_metadata(task_id, {"result": {"ok": True}})

    ##
    ## The whole value is replaced rather than merged into.  A result is one
    ## coherent record of one attempt, and half of an old attempt beside half of
    ## a new one would describe something that never happened.
    ##
    self.assertEqual({"ok": True}, store.get(task_id)["metadata"]["result"])

  def test_updating_nothing_leaves_the_metadata_alone(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD, metadata={"platform": "douyin"})

    store.update_metadata(task_id, {})
    store.update_metadata(task_id, None)

    self.assertEqual({"platform": "douyin"}, store.get(task_id)["metadata"])

  def test_the_updated_task_is_returned(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)

    returned = store.update_metadata(task_id, {"aweme_id": "123"})

    self.assertEqual("123", returned["metadata"]["aweme_id"])

  def test_an_unknown_task_is_refused(self):
    store = build_store()

    with self.assertRaises(TaskNotFound):
      store.update_metadata("nope", {"aweme_id": "123"})

  def test_a_finished_task_keeps_the_record_it_ended_with(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.set_state(task_id, TASK_STATE_RUNNING)
    store.set_state(task_id, TASK_STATE_SUCCESS)

    ##
    ## Refused for the same reason a finished task keeps its final message: once
    ## a task is over its record is what happened, and a late writer would be
    ## editing history.  Callers must write their results before they finish.
    ##
    with self.assertRaises(TaskAlreadyFinished):
      store.update_metadata(task_id, {"result": {"ok": True}})

  def test_a_running_task_accepts_updates(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.set_state(task_id, TASK_STATE_RUNNING)

    store.update_metadata(task_id, {"result": {"ok": True}})

    self.assertEqual({"ok": True}, store.get(task_id)["metadata"]["result"])

  def test_the_caller_cannot_reach_in_afterwards(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    supplied = {"result": {"saved": [1, 2]}}

    store.update_metadata(task_id, supplied)
    supplied["result"]["saved"].append(3)
    supplied["result"]["ok"] = True

    stored = store.get(task_id)["metadata"]["result"]
    self.assertEqual([1, 2], stored["saved"])
    self.assertNotIn("ok", stored)

  def test_a_snapshot_cannot_be_written_back_through(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.update_metadata(task_id, {"result": {"saved": [1]}})

    snapshot = store.update_metadata(task_id, {"stage": "done"})
    snapshot["metadata"]["result"]["saved"].append(2)

    self.assertEqual([1], store.get(task_id)["metadata"]["result"]["saved"])

  def test_progress_and_state_are_untouched(self):
    store = build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD, total=1)
    store.set_state(task_id, TASK_STATE_RUNNING, message="下载中")

    store.update_metadata(task_id, {"result": {"ok": True}})

    task = store.get(task_id)
    self.assertEqual(TASK_STATE_RUNNING, task["state"])
    self.assertEqual("下载中", task["message"])
    self.assertEqual({"current": 0, "total": 1}, task["progress"])


if __name__ == "__main__":
  unittest.main()
