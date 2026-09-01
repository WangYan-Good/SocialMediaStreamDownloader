import unittest
from datetime import datetime, timedelta

from backend.src.service.live_probe import (
  STATE_ERROR,
  STATE_LIVING,
  STATE_OFFLINE,
  STATE_PENDING,
  STATE_RUNNING,
  LiveProbeService,
  ProbeBatchError,
  ProbeCapacityExceeded,
  ProbeBatchStore,
)


class FakeResult:
  def __init__(self, ok=True, room_status=2, error=None):
    self.ok = ok
    self.room_status = room_status
    self.error = error
    self.owner_user_id = "owner"
    self.room_id = "room-1"
    self.nickname = "Host"
    self.title = "Title"
    self.checked_at = datetime(2026, 8, 10, 12, 0, 0)

  @property
  def is_living(self):
    return self.room_status == 2


class FakeProber:
  def __init__(self, results=None, crash=False):
    self._results = results or {}
    self._crash = crash
    self.calls = []

  def probe(self, url):
    self.calls.append(url)
    if self._crash:
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


def build_service(prober, owners, **overrides):
  options = {
    "prober": prober,
    "owner_lookup": lambda ids: {k: v for k, v in owners.items() if k in ids},
    "executor": ImmediateExecutor(),
    "clock": lambda: datetime(2026, 8, 10, 12, 0, 0),
  }
  options.update(overrides)
  return LiveProbeService(**options)


class ProbeBatchStoreTest(unittest.TestCase):
  def test_active_batches_are_preserved_and_a_new_batch_is_rejected(self):
    store = ProbeBatchStore(max_entries=3, max_active_batches=2)
    first = store.create([{"owner_user_id": "1", "state": STATE_PENDING}])
    second = store.create([{"owner_user_id": "2", "state": STATE_RUNNING}])

    with self.assertRaises(ProbeCapacityExceeded):
      store.create([{"owner_user_id": "3", "state": STATE_PENDING}])

    self.assertIsNotNone(store.snapshot(first))
    self.assertIsNotNone(store.snapshot(second))

  def test_total_capacity_rejects_without_evicting_an_active_batch(self):
    store = ProbeBatchStore(max_entries=1, max_active_batches=2)
    active = store.create([{"owner_user_id": "1", "state": STATE_PENDING}])

    with self.assertRaises(ProbeCapacityExceeded):
      store.create([{"owner_user_id": "2", "state": STATE_PENDING}])

    self.assertIsNotNone(store.snapshot(active))

  def test_completed_batch_is_pressure_evicted_before_rejection(self):
    store = ProbeBatchStore(max_entries=2, max_active_batches=2)
    completed = store.create([{"owner_user_id": "1", "state": STATE_LIVING}])
    active = store.create([{"owner_user_id": "2", "state": STATE_PENDING}])

    admitted = store.create([{"owner_user_id": "3", "state": STATE_PENDING}])

    self.assertIsNone(store.snapshot(completed))
    self.assertIsNotNone(store.snapshot(active))
    self.assertIsNotNone(store.snapshot(admitted))

  def test_active_batch_is_not_ttl_evicted(self):
    current = [1000.0]
    store = ProbeBatchStore(
      retention_seconds=10.0,
      clock=lambda: current[0],
      max_entries=2,
      max_active_batches=1,
    )
    active = store.create([{"owner_user_id": "1", "state": STATE_PENDING}])
    current[0] += 100.0

    with self.assertRaises(ProbeCapacityExceeded):
      store.create([{"owner_user_id": "2", "state": STATE_PENDING}])

    self.assertIsNotNone(store.snapshot(active))

  def test_completed_batch_retention_starts_when_the_last_item_settles(self):
    current = [1000.0]
    store = ProbeBatchStore(
      retention_seconds=10.0,
      clock=lambda: current[0],
      max_entries=2,
      max_active_batches=1,
    )
    completed = store.create(
      [{"owner_user_id": "1", "state": STATE_PENDING}]
    )

    current[0] += 100.0
    store.update(completed, "1", state=STATE_LIVING)
    current[0] += 9.0
    self.assertIsNotNone(store.snapshot(completed))

    current[0] += 2.0
    self.assertIsNone(store.snapshot(completed))
    self.assertIsNotNone(
      store.snapshot(
        store.create([{"owner_user_id": "2", "state": STATE_PENDING}])
      )
    )

  def test_snapshot_reports_done_only_when_nothing_is_outstanding(self):
    store = ProbeBatchStore()
    batch_id = store.create(
      [
        {"owner_user_id": "1", "state": STATE_PENDING},
        {"owner_user_id": "2", "state": STATE_LIVING},
      ]
    )

    self.assertFalse(store.snapshot(batch_id)["done"])
    store.update(batch_id, "1", state=STATE_OFFLINE)
    self.assertTrue(store.snapshot(batch_id)["done"])

  def test_snapshot_returns_a_detached_copy(self):
    store = ProbeBatchStore()
    batch_id = store.create([{"owner_user_id": "1", "state": STATE_LIVING}])

    snapshot = store.snapshot(batch_id)
    snapshot["items"][0]["state"] = "tampered"

    self.assertEqual(STATE_LIVING, store.snapshot(batch_id)["items"][0]["state"])

  def test_batches_are_evicted_after_the_retention_window(self):
    current = [1000.0]
    store = ProbeBatchStore(retention_seconds=600.0, clock=lambda: current[0])
    batch_id = store.create([{"owner_user_id": "1", "state": STATE_LIVING}])

    current[0] += 599.0
    self.assertIsNotNone(store.snapshot(batch_id))
    current[0] += 2.0
    self.assertIsNone(store.snapshot(batch_id))

  def test_updating_an_unknown_batch_or_owner_is_ignored(self):
    store = ProbeBatchStore()
    batch_id = store.create([{"owner_user_id": "1", "state": STATE_PENDING}])

    store.update("missing-batch", "1", state=STATE_LIVING)
    store.update(batch_id, "missing-owner", state=STATE_LIVING)

    self.assertEqual(STATE_PENDING, store.snapshot(batch_id)["items"][0]["state"])


class LiveProbeSubmitTest(unittest.TestCase):
  def test_empty_and_oversized_batches_are_rejected(self):
    service = build_service(FakeProber(), {}, max_batch_size=10)

    with self.assertRaises(ProbeBatchError):
      service.submit([])
    with self.assertRaises(ProbeBatchError):
      service.submit([str(index) for index in range(11)])

  def test_absolute_safety_ceiling_cannot_be_disabled_by_configuration(self):
    looked_up = []
    service = LiveProbeService(
      prober=FakeProber(),
      owner_lookup=lambda ids: looked_up.append(ids) or {},
      max_batch_size=1000,
      executor=ImmediateExecutor(),
    )

    with self.assertRaises(ProbeBatchError):
      service.submit([str(index) for index in range(101)])

    self.assertEqual([], looked_up)

  def test_store_capacity_refusal_submits_no_probe_workers(self):
    executor = ImmediateExecutor()
    store = ProbeBatchStore(max_entries=1, max_active_batches=1)
    store.create([{"owner_user_id": "held", "state": STATE_PENDING}])
    service = build_service(
      FakeProber(),
      {"1": {"live_share_url": "https://u/1", "nickname": "A"}},
      store=store,
      executor=executor,
    )

    with self.assertRaises(ProbeCapacityExceeded):
      service.submit(["1"])

    self.assertEqual(0, executor.submitted)

  def test_duplicate_owner_ids_are_probed_once(self):
    prober = FakeProber()
    service = build_service(
      prober, {"1": {"live_share_url": "https://u/1", "nickname": "A"}}
    )

    batch_id = service.submit(["1", "1", " 1 "])

    self.assertEqual(1, len(prober.calls))
    self.assertEqual(1, len(service.snapshot(batch_id)["items"]))

  def test_unknown_owner_is_reported_without_touching_the_network(self):
    prober = FakeProber()
    service = build_service(prober, {})

    batch_id = service.submit(["missing"])

    item = service.snapshot(batch_id)["items"][0]
    self.assertEqual(STATE_ERROR, item["state"])
    self.assertEqual("历史记录中没有该主播", item["message"])
    self.assertEqual([], prober.calls)

  def test_owner_without_a_share_url_is_reported_without_probing(self):
    prober = FakeProber()
    service = build_service(prober, {"1": {"live_share_url": None, "nickname": "A"}})

    batch_id = service.submit(["1"])

    item = service.snapshot(batch_id)["items"][0]
    self.assertEqual(STATE_ERROR, item["state"])
    self.assertEqual([], prober.calls)

  def test_a_recent_cache_entry_is_served_without_probing(self):
    prober = FakeProber()
    service = build_service(
      prober,
      {
        "1": {
          "live_share_url": "https://u/1",
          "nickname": "A",
          "last_live_status": 2,
          "last_checked_at": datetime(2026, 8, 10, 11, 59, 30),
          "last_room_id": "room-cached",
        }
      },
      cache_ttl_seconds=60,
    )

    batch_id = service.submit(["1"])

    item = service.snapshot(batch_id)["items"][0]
    self.assertEqual(STATE_LIVING, item["state"])
    self.assertTrue(item["cached"])
    self.assertEqual("room-cached", item["room_id"])
    self.assertEqual([], prober.calls)

  def test_a_stale_cache_entry_is_probed_again(self):
    prober = FakeProber()
    service = build_service(
      prober,
      {
        "1": {
          "live_share_url": "https://u/1",
          "nickname": "A",
          "last_live_status": 2,
          "last_checked_at": datetime(2026, 8, 10, 11, 58, 0),
        }
      },
      cache_ttl_seconds=60,
    )

    batch_id = service.submit(["1"])

    self.assertEqual(["https://u/1"], prober.calls)
    self.assertFalse(service.snapshot(batch_id)["items"][0]["cached"])


class LiveProbeOutcomeTest(unittest.TestCase):
  def test_a_living_room_is_reported_and_cached(self):
    written = []
    service = build_service(
      FakeProber({"https://u/1": FakeResult(room_status=2)}),
      {"1": {"live_share_url": "https://u/1", "nickname": "A"}},
      status_writer=lambda *args: written.append(args),
    )

    batch_id = service.submit(["1"])

    item = service.snapshot(batch_id)["items"][0]
    self.assertEqual(STATE_LIVING, item["state"])
    self.assertEqual("room-1", item["room_id"])
    self.assertEqual([("1", 2, datetime(2026, 8, 10, 12, 0, 0), "room-1")], written)

  def test_a_finished_room_is_reported_as_offline(self):
    service = build_service(
      FakeProber({"https://u/1": FakeResult(room_status=4)}),
      {"1": {"live_share_url": "https://u/1", "nickname": "A"}},
    )

    batch_id = service.submit(["1"])

    self.assertEqual(STATE_OFFLINE, service.snapshot(batch_id)["items"][0]["state"])

  def test_an_unsuccessful_probe_carries_its_reason(self):
    service = build_service(
      FakeProber({"https://u/1": FakeResult(ok=False, error="请求超时")}),
      {"1": {"live_share_url": "https://u/1", "nickname": "A"}},
    )

    batch_id = service.submit(["1"])

    item = service.snapshot(batch_id)["items"][0]
    self.assertEqual(STATE_ERROR, item["state"])
    self.assertEqual("请求超时", item["message"])

  def test_a_crashing_probe_fails_only_its_own_entry(self):
    service = build_service(
      FakeProber(crash=True),
      {
        "1": {"live_share_url": "https://u/1", "nickname": "A"},
        "2": {"live_share_url": "https://u/2", "nickname": "B"},
      },
    )

    batch_id = service.submit(["1", "2"])

    snapshot = service.snapshot(batch_id)
    self.assertTrue(snapshot["done"])
    self.assertTrue(all(item["state"] == STATE_ERROR for item in snapshot["items"]))

  def test_a_failing_cache_write_does_not_fail_the_probe(self):
    def explode(*unused):
      raise RuntimeError("database gone")

    service = build_service(
      FakeProber({"https://u/1": FakeResult(room_status=2)}),
      {"1": {"live_share_url": "https://u/1", "nickname": "A"}},
      status_writer=explode,
    )

    batch_id = service.submit(["1"])

    self.assertEqual(STATE_LIVING, service.snapshot(batch_id)["items"][0]["state"])

  def test_construction_rejects_invalid_bounds(self):
    with self.assertRaises(ValueError):
      build_service(FakeProber(), {}, max_batch_size=0)
    with self.assertRaises(ValueError):
      LiveProbeService(prober=FakeProber(), owner_lookup=lambda ids: {}, concurrency=0)


if __name__ == "__main__":
  unittest.main()
