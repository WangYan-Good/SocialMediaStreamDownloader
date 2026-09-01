from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Lock
import unittest

from backend.src.platform import resource_resolution as resolution_errors
from backend.src.platform.resource_resolution import (
  RESOURCE_TYPE_POST,
  ResourceResolution,
)
from backend.src.service.resource_resolve import ResolveStore
from backend.src.service import job_store as job_store_module
from backend.src.service.job_store import JOB_DONE, JobStore
from backend.src.service.post_download_job import PayloadCache
from backend.src.task import errors as task_errors
from backend.src.task.model import (
  TASK_STATE_RUNNING,
  TASK_STATE_SUCCESS,
  TASK_TYPE_LIVE_RECORD,
  TASK_TYPE_POST_DOWNLOAD,
)
from backend.src.task.store import TaskStore


TaskCapacityExceeded = getattr(
  task_errors, "TaskCapacityExceeded", type("MissingTaskCapacityExceeded", (Exception,), {})
)
TaskItemCapacityExceeded = getattr(
  task_errors,
  "TaskItemCapacityExceeded",
  type("MissingTaskItemCapacityExceeded", (Exception,), {}),
)
ResolveCapacityExceeded = getattr(
  resolution_errors,
  "ResolveCapacityExceeded",
  type("MissingResolveCapacityExceeded", (Exception,), {}),
)
JobCapacityExceeded = getattr(
  job_store_module,
  "JobCapacityExceeded",
  type("MissingJobCapacityExceeded", (Exception,), {}),
)
JobItemCapacityExceeded = getattr(
  job_store_module,
  "JobItemCapacityExceeded",
  type("MissingJobItemCapacityExceeded", (Exception,), {}),
)


def resolution(identifier="1"):
  return ResourceResolution(
    platform="douyin",
    resource_type=RESOURCE_TYPE_POST,
    source_url="https://example.invalid/source/{}".format(identifier),
    resolved_url="https://example.invalid/post/{}".format(identifier),
    identity={"aweme_id": str(identifier)},
  )


class TaskStoreAdmissionTest(unittest.TestCase):
  def build_store(self, **overrides):
    options = {
      "max_entries": 8,
      "max_active_global": 8,
      "max_active_per_user": 8,
      "max_active_by_type": {
        TASK_TYPE_POST_DOWNLOAD: 8,
        TASK_TYPE_LIVE_RECORD: 8,
      },
      "max_items_per_task": 8,
    }
    options.update(overrides)
    return TaskStore(**options)

  def test_terminal_task_is_pressure_evicted_before_new_work_is_refused(self):
    store = self.build_store(max_entries=2)
    finished = store.create(TASK_TYPE_POST_DOWNLOAD)
    store.set_state(finished, TASK_STATE_RUNNING)
    store.set_state(finished, TASK_STATE_SUCCESS)
    active = store.create(TASK_TYPE_POST_DOWNLOAD)

    admitted = store.create(TASK_TYPE_POST_DOWNLOAD)

    self.assertIsNone(store.get(finished))
    self.assertIsNotNone(store.get(active))
    self.assertIsNotNone(store.get(admitted))
    self.assertEqual(2, store.tracked())

  def test_total_capacity_never_pressure_evicts_active_tasks(self):
    store = self.build_store(max_entries=2)
    first = store.create(TASK_TYPE_POST_DOWNLOAD)
    second = store.create(TASK_TYPE_POST_DOWNLOAD)

    with self.assertRaises(TaskCapacityExceeded):
      store.create(TASK_TYPE_POST_DOWNLOAD)

    self.assertIsNotNone(store.get(first))
    self.assertIsNotNone(store.get(second))
    self.assertEqual(2, store.tracked())

  def test_global_active_capacity_refuses_the_next_task(self):
    store = self.build_store(max_active_global=2)
    store.create(TASK_TYPE_POST_DOWNLOAD)
    store.create(TASK_TYPE_POST_DOWNLOAD)

    with self.assertRaises(TaskCapacityExceeded):
      store.create(TASK_TYPE_POST_DOWNLOAD)

    self.assertEqual(2, store.tracked())

  def test_per_user_capacity_preserves_capacity_for_another_user(self):
    store = self.build_store(max_active_per_user=1)
    first = store.create(TASK_TYPE_POST_DOWNLOAD, app_user_id=11)

    with self.assertRaises(TaskCapacityExceeded):
      store.create(TASK_TYPE_POST_DOWNLOAD, app_user_id=11)
    other = store.create(TASK_TYPE_POST_DOWNLOAD, app_user_id=12)

    self.assertIsNotNone(store.get(first))
    self.assertIsNotNone(store.get(other))

  def test_task_type_capacity_refuses_only_that_resource_class(self):
    store = self.build_store(
      max_active_by_type={
        TASK_TYPE_POST_DOWNLOAD: 8,
        TASK_TYPE_LIVE_RECORD: 1,
      }
    )
    live = store.create(TASK_TYPE_LIVE_RECORD)

    with self.assertRaises(TaskCapacityExceeded):
      store.create(TASK_TYPE_LIVE_RECORD)
    post = store.create(TASK_TYPE_POST_DOWNLOAD)

    self.assertIsNotNone(store.get(live))
    self.assertIsNotNone(store.get(post))

  def test_concurrent_creation_never_exceeds_the_active_cap(self):
    for round_number in range(5):
      store = self.build_store(max_entries=4, max_active_global=4)
      barrier = Barrier(20)
      outcomes = []
      guard = Lock()

      def create_one(index):
        barrier.wait()
        try:
          store.create(TASK_TYPE_POST_DOWNLOAD, app_user_id=index + 1)
          outcome = "accepted"
        except TaskCapacityExceeded:
          outcome = "refused"
        with guard:
          outcomes.append(outcome)

      with ThreadPoolExecutor(max_workers=20) as pool:
        list(pool.map(create_one, range(20)))

      with self.subTest(round_number=round_number):
        self.assertEqual(4, outcomes.count("accepted"))
        self.assertEqual(16, outcomes.count("refused"))
        self.assertEqual(4, store.tracked())


class TaskItemAdmissionTest(unittest.TestCase):
  def build_store(self):
    return TaskStore(
      max_entries=8,
      max_active_global=8,
      max_active_per_user=8,
      max_items_per_task=2,
    )

  def test_create_refuses_more_than_the_item_ceiling(self):
    store = self.build_store()

    with self.assertRaises(TaskItemCapacityExceeded):
      store.create(TASK_TYPE_POST_DOWNLOAD, items=["1", "2", "3"])

    self.assertEqual(0, store.tracked())

  def test_create_stops_consuming_an_unbounded_duplicate_iterable(self):
    store = self.build_store()
    consumed = []

    def repeated():
      while True:
        consumed.append("one")
        yield "one"

    with self.assertRaises(TaskItemCapacityExceeded):
      store.create(TASK_TYPE_POST_DOWNLOAD, items=repeated())

    self.assertEqual(3, len(consumed))
    self.assertEqual(0, store.tracked())

  def test_duplicate_add_at_the_ceiling_is_a_no_op_but_new_item_is_refused(self):
    store = self.build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD, items=["1", "2"])

    unchanged = store.add_item(task_id, "2")
    with self.assertRaises(TaskItemCapacityExceeded):
      store.add_item(task_id, "3")

    self.assertEqual(["1", "2"], [item["key"] for item in unchanged["items"]])
    self.assertEqual(2, len(store.get(task_id)["items"]))

  def test_update_item_cannot_bypass_the_item_ceiling(self):
    store = self.build_store()
    task_id = store.create(TASK_TYPE_POST_DOWNLOAD, items=["1", "2"])

    with self.assertRaises(TaskItemCapacityExceeded):
      store.update_item(task_id, "3")

    self.assertEqual(2, len(store.get(task_id)["items"]))


class ResolveClock:
  def __init__(self):
    self.value = 0.0

  def __call__(self):
    return self.value

  def advance(self, seconds):
    self.value += seconds


class ResolveStoreAdmissionTest(unittest.TestCase):
  def build_store(self, **overrides):
    options = {
      "max_entries": 4,
      "max_entries_per_user": 3,
    }
    options.update(overrides)
    return ResolveStore(**options)

  def test_global_capacity_refuses_without_evicting_unexpired_receipts(self):
    store = self.build_store(max_entries=2)
    first = store.put(resolution("1"), 11)
    second = store.put(resolution("2"), 12)

    with self.assertRaises(ResolveCapacityExceeded):
      store.put(resolution("3"), 13)

    self.assertIsNotNone(store.get_for_user(first, 11))
    self.assertIsNotNone(store.get_for_user(second, 12))
    self.assertEqual(2, store.tracked())

  def test_per_user_capacity_preserves_slots_for_another_user(self):
    store = self.build_store(max_entries_per_user=1)
    store.put(resolution("1"), 11)

    with self.assertRaises(ResolveCapacityExceeded):
      store.put(resolution("2"), 11)
    other = store.put(resolution("3"), 12)

    self.assertIsNotNone(store.get_for_user(other, 12))
    self.assertEqual(2, store.tracked())

  def test_expired_receipt_releases_capacity(self):
    clock = ResolveClock()
    store = self.build_store(
      max_entries=1, retention_seconds=5.0, clock=clock
    )
    expired = store.put(resolution("1"), 11)
    clock.advance(5.0)

    current = store.put(resolution("2"), 11)

    self.assertIsNone(store.get(expired))
    self.assertIsNotNone(store.get_for_user(current, 11))

  def test_put_many_commits_all_receipts_in_input_order(self):
    store = self.build_store()

    receipt_ids = store.put_many(
      [resolution("1"), resolution("2")], app_user_id=11
    )

    self.assertEqual(2, len(receipt_ids))
    self.assertEqual("1", store.get_for_user(receipt_ids[0], 11).identity["aweme_id"])
    self.assertEqual("2", store.get_for_user(receipt_ids[1], 11).identity["aweme_id"])

  def test_insufficient_batch_capacity_leaves_zero_partial_receipts(self):
    store = self.build_store(max_entries=2)
    existing = store.put(resolution("0"), 11)

    with self.assertRaises(ResolveCapacityExceeded):
      store.put_many([resolution("1"), resolution("2")], app_user_id=12)

    self.assertEqual(1, store.tracked())
    self.assertIsNotNone(store.get_for_user(existing, 11))

  def test_concurrent_batches_never_exceed_global_capacity(self):
    store = self.build_store(max_entries=4, max_entries_per_user=4)
    barrier = Barrier(10)
    outcomes = []
    guard = Lock()

    def put_batch(index):
      barrier.wait()
      try:
        store.put_many(
          [resolution("{}a".format(index)), resolution("{}b".format(index))],
          app_user_id=index + 1,
        )
        outcome = "accepted"
      except ResolveCapacityExceeded:
        outcome = "refused"
      with guard:
        outcomes.append(outcome)

    with ThreadPoolExecutor(max_workers=10) as pool:
      list(pool.map(put_batch, range(10)))

    self.assertEqual(2, outcomes.count("accepted"))
    self.assertEqual(8, outcomes.count("refused"))
    self.assertEqual(4, store.tracked())


class JobStoreAdmissionTest(unittest.TestCase):
  def build_store(self, **overrides):
    options = {
      "max_entries": 4,
      "max_active_jobs": 3,
      "max_items": 3,
    }
    options.update(overrides)
    return JobStore(**options)

  def test_terminal_job_is_pressure_evicted_before_new_work_is_refused(self):
    store = self.build_store(max_entries=2)
    finished = store.create([])
    store.finish(finished, state=JOB_DONE)
    active = store.create([])

    admitted = store.create([])

    self.assertIsNone(store.snapshot(finished))
    self.assertIsNotNone(store.snapshot(active))
    self.assertIsNotNone(store.snapshot(admitted))

  def test_total_capacity_never_pressure_evicts_active_jobs(self):
    store = self.build_store(max_entries=2)
    first = store.create([])
    second = store.create([])

    with self.assertRaises(JobCapacityExceeded):
      store.create([])

    self.assertIsNotNone(store.snapshot(first))
    self.assertIsNotNone(store.snapshot(second))

  def test_active_job_capacity_refuses_the_next_job(self):
    store = self.build_store(max_active_jobs=1)
    store.create([])

    with self.assertRaises(JobCapacityExceeded):
      store.create([])

    self.assertEqual(1, store.tracked())

  def test_create_stops_at_the_request_sequence_item_ceiling(self):
    store = self.build_store(max_items=2)
    consumed = []

    def repeated():
      while True:
        consumed.append("1")
        yield "1"

    with self.assertRaises(JobItemCapacityExceeded):
      store.create(repeated())

    self.assertEqual(3, len(consumed))
    self.assertEqual(0, store.tracked())

  def test_growing_job_cannot_bypass_the_item_ceiling(self):
    store = self.build_store(max_items=2)
    job_id = store.create([])
    store.update_item(job_id, "1")
    store.update_item(job_id, "2")

    with self.assertRaises(JobItemCapacityExceeded):
      store.update_item(job_id, "3")

    self.assertEqual(2, store.snapshot(job_id)["total"])


def post_payload(identifier):
  return {"aweme_id": str(identifier)}


class PayloadCacheAdmissionTest(unittest.TestCase):
  def test_cache_evicts_the_least_recently_used_entry(self):
    cache = PayloadCache(max_entries=2)
    cache.remember([post_payload("a"), post_payload("b")])
    cache.take(["a"])

    cache.remember([post_payload("c")])

    payloads, missing = cache.take(["a", "b", "c"])
    self.assertEqual(["a", "c"], [item["aweme_id"] for item in payloads])
    self.assertEqual(["b"], missing)
    self.assertEqual(2, cache.tracked())

  def test_remembering_an_existing_entry_refreshes_without_growth(self):
    cache = PayloadCache(max_entries=2)
    cache.remember([post_payload("a"), post_payload("b")])

    cache.remember([post_payload("a")])
    cache.remember([post_payload("c")])

    unused, missing = cache.take(["a", "b", "c"])
    self.assertEqual(["b"], missing)
    self.assertEqual(2, cache.tracked())

  def test_concurrent_remember_never_exceeds_the_hard_cap(self):
    cache = PayloadCache(max_entries=4)
    barrier = Barrier(20)

    def remember_one(index):
      barrier.wait()
      cache.remember([post_payload(index)])

    with ThreadPoolExecutor(max_workers=20) as pool:
      list(pool.map(remember_one, range(20)))

    self.assertEqual(4, cache.tracked())


class RuntimeWorkAdmissionContractTest(unittest.TestCase):
  def test_ci_executes_the_tracked_probe_with_an_exact_independent_guard(self):
    root = Path(__file__).resolve().parents[3]
    workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    probe = (
      root / "scripts/runtime_work_admission_probe.py"
    ).read_text(encoding="utf-8")
    marker = "ok   runtime bounded work admission"

    self.assertEqual(1, probe.count(marker))
    self.assertIn(
      "docker cp scripts/runtime_work_admission_probe.py", workflow
    )
    self.assertIn(
      "python /tmp/runtime_work_admission_probe.py", workflow
    )
    self.assertIn("grep -Fxq '{}'".format(marker), workflow)
    self.assertNotIn(
      "docker exec smsd-ci-smoke python -", workflow
    )

if __name__ == "__main__":
  unittest.main()
