"""Container proof for the process-local work admission boundaries."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Lock
import sys


PROJECT_ROOT = Path("/app")
if not (PROJECT_ROOT / "backend").is_dir():
  PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.platform.resource_resolution import (
  RESOURCE_TYPE_POST,
  ResolveCapacityExceeded,
  ResourceResolution,
)
from backend.src.service.job_store import JobCapacityExceeded, JobStore
from backend.src.service.live_probe import (
  STATE_PENDING,
  ProbeBatchStore,
  ProbeCapacityExceeded,
)
from backend.src.service.post_download_job import PayloadCache
from backend.src.service.resource_resolve import ResolveStore
from backend.src.task.errors import TaskCapacityExceeded
from backend.src.task.model import TASK_TYPE_POST_DOWNLOAD
from backend.src.task.store import TaskStore


MARKER = "ok   runtime bounded work admission"


def _resolution(identifier: str) -> ResourceResolution:
  return ResourceResolution(
    platform="douyin",
    resource_type=RESOURCE_TYPE_POST,
    source_url="https://example.invalid/source/{}".format(identifier),
    resolved_url="https://example.invalid/post/{}".format(identifier),
    identity={"aweme_id": identifier},
  )


def _prove_task_concurrency() -> None:
  store = TaskStore(
    max_entries=4,
    max_active_global=4,
    max_active_per_user=4,
    max_active_by_type={TASK_TYPE_POST_DOWNLOAD: 4},
  )
  barrier = Barrier(20)
  outcomes = []
  guard = Lock()

  def create_one(index):
    barrier.wait()
    try:
      store.create(TASK_TYPE_POST_DOWNLOAD, app_user_id=index + 1)
      result = "accepted"
    except TaskCapacityExceeded:
      result = "refused"
    with guard:
      outcomes.append(result)

  with ThreadPoolExecutor(max_workers=20) as pool:
    list(pool.map(create_one, range(20)))

  if outcomes.count("accepted") != 4 or store.tracked() != 4:
    raise SystemExit("FAIL: TaskStore concurrent admission exceeded its cap")


def _prove_resolve_atomicity() -> None:
  store = ResolveStore(max_entries=2, max_entries_per_user=2)
  existing = store.put(_resolution("existing"), app_user_id=1)
  try:
    store.put_many(
      (_resolution("first"), _resolution("second")), app_user_id=2
    )
  except ResolveCapacityExceeded:
    pass
  else:
    raise SystemExit("FAIL: ResolveStore accepted an overflowing batch")
  if store.tracked() != 1 or store.get_for_user(existing, 1) is None:
    raise SystemExit("FAIL: ResolveStore left partial batch receipts")


def _prove_owner_job_capacity() -> None:
  store = JobStore(max_entries=1, max_active_jobs=1, max_items=2)
  active = store.create([])
  try:
    store.create([])
  except JobCapacityExceeded:
    pass
  else:
    raise SystemExit("FAIL: JobStore accepted work above its active cap")
  if store.snapshot(active) is None or store.tracked() != 1:
    raise SystemExit("FAIL: JobStore evicted active work under pressure")


def _prove_payload_lru() -> None:
  cache = PayloadCache(max_entries=2)
  cache.remember(({"aweme_id": "a"}, {"aweme_id": "b"}))
  cache.take(("a",))
  cache.remember(({"aweme_id": "c"},))
  payloads, missing = cache.take(("a", "b", "c"))
  if (
    [payload["aweme_id"] for payload in payloads] != ["a", "c"]
    or missing != ["b"]
    or cache.tracked() != 2
  ):
    raise SystemExit("FAIL: PayloadCache did not enforce bounded LRU eviction")


def _prove_probe_capacity() -> None:
  store = ProbeBatchStore(max_entries=1, max_active_batches=1)
  active = store.create([{"owner_user_id": "1", "state": STATE_PENDING}])
  try:
    store.create([{"owner_user_id": "2", "state": STATE_PENDING}])
  except ProbeCapacityExceeded:
    pass
  else:
    raise SystemExit("FAIL: ProbeBatchStore accepted work above its active cap")
  if store.snapshot(active) is None:
    raise SystemExit("FAIL: ProbeBatchStore evicted an active batch")


def main() -> None:
  _prove_task_concurrency()
  _prove_resolve_atomicity()
  _prove_owner_job_capacity()
  _prove_payload_lru()
  _prove_probe_capacity()
  print(MARKER)


if __name__ == "__main__":
  main()
