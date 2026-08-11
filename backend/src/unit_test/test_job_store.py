import unittest

from backend.src.service.job_store import (
  JOB_DONE,
  JOB_ERROR,
  JOB_RUNNING,
  STATE_DONE,
  STATE_ERROR,
  STATE_PENDING,
  STATE_RUNNING,
  STATE_SKIPPED,
  JobStore,
)


class FakeClock:
  def __init__(self, now=0.0):
    self.now = now

  def __call__(self):
    return self.now

  def advance(self, seconds):
    self.now += seconds


class JobLifecycleTest(unittest.TestCase):
  def test_a_new_job_lists_every_key_as_pending(self):
    store = JobStore()

    job_id = store.create(["a", "b", "c"])
    snapshot = store.snapshot(job_id)

    self.assertEqual(snapshot["state"], JOB_RUNNING)
    self.assertEqual(snapshot["total"], 3)
    self.assertEqual(snapshot["finished"], 0)
    self.assertEqual(
      [item["state"] for item in snapshot["items"]],
      [STATE_PENDING] * 3,
    )

  def test_submitted_order_is_preserved(self):
    """The UI shows progress against the list the user submitted."""
    store = JobStore()

    job_id = store.create(["c", "a", "b"])

    self.assertEqual(
      [item["key"] for item in store.snapshot(job_id)["items"]],
      ["c", "a", "b"],
    )

  def test_keys_are_normalised_to_text(self):
    store = JobStore()

    job_id = store.create([1, 2])

    self.assertEqual(
      [item["key"] for item in store.snapshot(job_id)["items"]],
      ["1", "2"],
    )
    store.update_item(job_id, 1, state=STATE_DONE)
    self.assertEqual(store.snapshot(job_id)["items"][0]["state"], STATE_DONE)

  def test_finished_counts_every_terminal_state(self):
    store = JobStore()
    job_id = store.create(["a", "b", "c", "d"])

    store.update_item(job_id, "a", state=STATE_DONE)
    store.update_item(job_id, "b", state=STATE_ERROR)
    store.update_item(job_id, "c", state=STATE_SKIPPED)
    store.update_item(job_id, "d", state=STATE_RUNNING)

    self.assertEqual(store.snapshot(job_id)["finished"], 3)

  def test_extra_fields_are_carried_on_the_item(self):
    store = JobStore()
    job_id = store.create(["a"])

    store.update_item(job_id, "a", state=STATE_DONE, saved=3, planned=3)
    item = store.snapshot(job_id)["items"][0]

    self.assertEqual(item["saved"], 3)
    self.assertEqual(item["planned"], 3)

  def test_a_job_can_grow_while_it_runs(self):
    """"Download everything" discovers its items page by page."""
    store = JobStore()
    job_id = store.create([])

    store.update_item(job_id, "a", state=STATE_DONE)
    store.update_item(job_id, "b", state=STATE_DONE)
    snapshot = store.snapshot(job_id)

    self.assertEqual(snapshot["total"], 2)
    self.assertEqual([item["key"] for item in snapshot["items"]], ["a", "b"])

  def test_finishing_records_the_state_and_message(self):
    store = JobStore()
    job_id = store.create(["a"])

    store.finish(job_id, state=JOB_ERROR, message="停在第 1 个作品")
    snapshot = store.snapshot(job_id)

    self.assertEqual(snapshot["state"], JOB_ERROR)
    self.assertEqual(snapshot["message"], "停在第 1 个作品")

  def test_an_unknown_job_has_no_snapshot(self):
    self.assertIsNone(JobStore().snapshot("nope"))

  def test_updating_an_unknown_job_is_ignored(self):
    store = JobStore()

    store.update_item("nope", "a", state=STATE_DONE)
    store.finish("nope")

    self.assertEqual(store.tracked(), 0)

  def test_a_snapshot_is_a_copy(self):
    """A caller must not be able to mutate stored state through a snapshot."""
    store = JobStore()
    job_id = store.create(["a"])

    snapshot = store.snapshot(job_id)
    snapshot["items"][0]["state"] = "tampered"

    self.assertEqual(store.snapshot(job_id)["items"][0]["state"], STATE_PENDING)


class JobRetentionTest(unittest.TestCase):
  """Jobs expire so a long-running server does not accumulate them."""

  def test_a_job_is_dropped_once_it_is_stale(self):
    clock = FakeClock()
    store = JobStore(retention_seconds=100.0, clock=clock)
    job_id = store.create(["a"])

    clock.advance(99)
    self.assertIsNotNone(store.snapshot(job_id))

    clock.advance(2)
    self.assertIsNone(store.snapshot(job_id))

  def test_activity_keeps_a_job_alive(self):
    clock = FakeClock()
    store = JobStore(retention_seconds=100.0, clock=clock)
    job_id = store.create(["a"])

    clock.advance(90)
    store.update_item(job_id, "a", state=STATE_RUNNING)
    clock.advance(90)

    self.assertIsNotNone(store.snapshot(job_id))

  def test_creating_a_job_evicts_stale_ones(self):
    clock = FakeClock()
    store = JobStore(retention_seconds=10.0, clock=clock)
    store.create(["a"])

    clock.advance(11)
    store.create(["b"])

    self.assertEqual(store.tracked(), 1)

  def test_many_jobs_do_not_accumulate(self):
    """Only the job created since the last expiry window is still held."""
    clock = FakeClock()
    store = JobStore(retention_seconds=5.0, clock=clock)

    for index in range(50):
      clock.advance(6)
      store.create(["item-{}".format(index)])

    self.assertEqual(store.tracked(), 1)


if __name__ == "__main__":
  unittest.main()
