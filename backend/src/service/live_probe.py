##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from time import monotonic
from uuid import uuid4

## <<Third-Part>>
from backend.src.library.loglib import get_logger
from backend.src.service.live_probe_task_mirror import (
  PLATFORM_DOUYIN,
  LiveProbeTaskMirror,
)


##
## Per-owner probe states reported to the UI.
##
STATE_PENDING = "pending"
STATE_RUNNING = "running"
STATE_LIVING = "living"
STATE_OFFLINE = "offline"
STATE_ERROR = "error"

##
## room.status 2 means the room is broadcasting.
##
ROOM_STATUS_LIVING = 2

MAX_PROBE_BATCH_STORE_ENTRIES = 32
MAX_ACTIVE_PROBE_BATCHES = 16
MAX_SAFE_PROBE_ITEMS_PER_BATCH = 100


class ProbeBatchError(ValueError):
  """Raised when a probe batch cannot be accepted as requested."""


class ProbeCapacityExceeded(Exception):
  """Raised when this process cannot admit another live-probe batch."""


class ProbeBatchStore:
  """In-memory store of probe batches, evicted after a retention window.

  Batches live in this process only.  That is sufficient for the single-process
  server this project ships, and the interface is deliberately narrow so a shared
  backend can replace it without touching callers.
  """

  def __init__(
    self,
    retention_seconds: float = 600.0,
    clock=monotonic,
    max_entries: int = MAX_PROBE_BATCH_STORE_ENTRIES,
    max_active_batches: int = MAX_ACTIVE_PROBE_BATCHES,
  ) -> None:
    self._retention_seconds = retention_seconds
    self._clock = clock
    self._max_entries = self._positive_limit(max_entries, "max_entries")
    self._max_active_batches = self._positive_limit(
      max_active_batches, "max_active_batches"
    )
    self._lock = threading.Lock()
    self._batches = dict()

  @staticmethod
  def _positive_limit(value, label: str) -> int:
    if type(value) is not int or value < 1:
      raise ValueError("{} must be a positive integer".format(label))
    return value

  @staticmethod
  def _is_active(batch: dict) -> bool:
    return any(
      item["state"] in (STATE_PENDING, STATE_RUNNING)
      for item in batch["items"].values()
    )

  def _evict_expired(self) -> None:
    ##
    ## Caller must hold the lock.
    ##
    deadline = self._clock() - self._retention_seconds
    expired = [
      batch_id
      for batch_id, batch in self._batches.items()
      if batch["completed_at"] is not None
      and batch["completed_at"] <= deadline
    ]
    for batch_id in expired:
      del self._batches[batch_id]

  def _pressure_evict_completed(self) -> None:
    completed = [
      batch_id
      for batch_id, batch in self._batches.items()
      if not self._is_active(batch)
    ]
    while len(self._batches) >= self._max_entries and completed:
      del self._batches[completed.pop(0)]

  def create(self, items: list) -> str:
    batch_id = uuid4().hex
    item_map = {item["owner_user_id"]: item for item in items}
    created_at = self._clock()
    new_batch = {
      "created_at": created_at,
      "completed_at": None,
      "items": item_map,
    }
    if not self._is_active(new_batch):
      new_batch["completed_at"] = created_at
    with self._lock:
      self._evict_expired()
      self._pressure_evict_completed()
      if self._is_active(new_batch):
        active = sum(
          1 for batch in self._batches.values() if self._is_active(batch)
        )
        if active >= self._max_active_batches:
          raise ProbeCapacityExceeded("probe batch active capacity is full")
      if len(self._batches) >= self._max_entries:
        raise ProbeCapacityExceeded("probe batch store capacity is full")
      self._batches[batch_id] = new_batch
    return batch_id

  def update(self, batch_id: str, owner_user_id: str, **fields) -> None:
    with self._lock:
      batch = self._batches.get(batch_id)
      if batch is None:
        return
      item = batch["items"].get(owner_user_id)
      if item is None:
        return
      was_active = self._is_active(batch)
      item.update(fields)
      if self._is_active(batch):
        batch["completed_at"] = None
      elif was_active:
        batch["completed_at"] = self._clock()

  def snapshot(self, batch_id: str):
    """Return a detached copy of one batch, or None when it is unknown."""
    with self._lock:
      self._evict_expired()
      batch = self._batches.get(batch_id)
      if batch is None:
        return None
      items = [dict(item) for item in batch["items"].values()]
    return {
      "batch_id": batch_id,
      "done": all(
        item["state"] not in (STATE_PENDING, STATE_RUNNING) for item in items
      ),
      "items": items,
    }


class LiveProbeService:
  """Probes a small set of owners for their current live status.

  One probe is two platform requests separated by deliberate delays, so a batch is
  bounded on both sides: ``max_batch_size`` caps how many owners one action may
  touch, and ``concurrency`` caps how many run at once.  The pool is private on
  purpose - the download executor has a single worker and sharing it would let a
  probe burst stall an in-flight recording.
  """

##
## >>============================= private method =============================>>
##
  def __init__(
    self,
    prober,
    owner_lookup,
    status_writer=None,
    max_batch_size: int = 10,
    concurrency: int = 3,
    cache_ttl_seconds: float = 60.0,
    store=None,
    executor=None,
    clock=datetime.now,
    task_service=None,
  ) -> None:
    if prober is None:
      raise ValueError("prober is required")
    if owner_lookup is None:
      raise ValueError("owner_lookup is required")
    if max_batch_size < 1:
      raise ValueError("max_batch_size must be at least 1")
    if concurrency < 1:
      raise ValueError("concurrency must be at least 1")

    self._prober = prober
    self._owner_lookup = owner_lookup
    self._status_writer = status_writer
    self._max_batch_size = max_batch_size
    self._effective_max_batch_size = min(
      max_batch_size, MAX_SAFE_PROBE_ITEMS_PER_BATCH
    )
    self._cache_ttl = timedelta(seconds=cache_ttl_seconds)
    self._clock = clock
    self._store = store if store is not None else ProbeBatchStore()
    self._executor = executor if executor is not None else ThreadPoolExecutor(
      max_workers=concurrency,
      thread_name_prefix="live-probe",
    )
    ##
    ## Live probing is temporarily dual-written: ``store`` is the legacy
    ## compatibility surface the current history page polls, and the mirror
    ## reports the same probe onto the unified TaskService the next frontend
    ## will read.
    ##
    ## The task service is injected rather than constructed here.  One process
    ## must have exactly one task store, and a service that built its own would
    ## report into a store no request could ever read.  Passing ``None`` is a
    ## supported wiring that simply reports nothing.
    ##
    self.task_service = task_service
    self._tasks = LiveProbeTaskMirror(task_service)

  def _batch_title(self, count: int) -> str:
    if count == 1:
      return "检查主播直播状态"
    return "检查 {} 个主播直播状态".format(count)

  def _cached_state(self, row: dict):
    """Return a cached state for ``row`` when it was probed recently enough."""
    checked_at = row.get("last_checked_at")
    if checked_at is None:
      return None
    if self._clock() - checked_at > self._cache_ttl:
      return None
    status = row.get("last_live_status")
    return {
      "state": STATE_LIVING if status == ROOM_STATUS_LIVING else STATE_OFFLINE,
      "room_id": row.get("last_room_id"),
      "checked_at": checked_at,
      "cached": True,
    }

  def _record(self, owner_user_id: str, result) -> None:
    if self._status_writer is None:
      return
    try:
      self._status_writer(
        owner_user_id,
        result.room_status,
        result.checked_at,
        result.room_id,
      )
    except Exception as e:
      ##
      ## Persisting the cache is a convenience; a failure here must not turn a
      ## successful probe into a failed one.
      ##
      get_logger().warning("live status cache write failed: {}".format(e))

  def _run_one(self, batch_id: str, owner_user_id: str, share_url: str) -> None:
    self._store.update(batch_id, owner_user_id, state=STATE_RUNNING)
    self._tasks.item_running(batch_id, owner_user_id)
    try:
      self._probe_one(batch_id, owner_user_id, share_url)
    finally:
      ##
      ## In a ``finally`` so that every way out of a probe - answered, refused,
      ## crashed - is followed by the completion check.  The last worker to
      ## settle is the one that ends the task, and which worker that is cannot be
      ## known in advance.
      ##
      self._tasks.finish_if_complete(batch_id)

  def _probe_one(self, batch_id: str, owner_user_id: str, share_url: str) -> None:
    try:
      result = self._prober.probe(share_url)
    except Exception as e:
      get_logger().error("live probe crashed for {}: {}".format(owner_user_id, e))
      self._store.update(
        batch_id, owner_user_id, state=STATE_ERROR, message="探测失败"
      )
      self._tasks.item_failed(batch_id, owner_user_id, "探测失败")
      return

    if result.ok is not True:
      message = result.error or "探测失败"
      self._store.update(
        batch_id,
        owner_user_id,
        state=STATE_ERROR,
        message=message,
      )
      self._tasks.item_failed(batch_id, owner_user_id, message)
      return

    self._record(owner_user_id, result)
    self._store.update(
      batch_id,
      owner_user_id,
      state=STATE_LIVING if result.is_living else STATE_OFFLINE,
      room_id=result.room_id,
      title=result.title,
      nickname=result.nickname or None,
      checked_at=result.checked_at,
      cached=False,
      message=None,
    )
    ##
    ## The room was reached and it answered, so the probe succeeded whichever
    ## answer it gave; only ``live_status`` differs between the two.
    ##
    report = self._tasks.item_living if result.is_living else self._tasks.item_offline
    report(
      batch_id,
      owner_user_id,
      nickname=result.nickname or None,
      room_id=result.room_id,
      title=result.title,
      live_share_url=share_url,
      checked_at=result.checked_at,
      cached=False,
    )

##
## >>============================= sub class method =============================>>
##
  def submit(self, owner_user_ids) -> str:
    """Accept a batch of owners to probe and return its identifier.

    Owners already probed inside the cache window are resolved immediately and
    never reach the network.
    """
    identifiers = list()
    seen = set()
    for candidate in owner_user_ids or ():
      text = str(candidate).strip()
      if text and text not in seen:
        seen.add(text)
        identifiers.append(text)
        if len(identifiers) > self._effective_max_batch_size:
          raise ProbeBatchError(
            "a probe batch accepts at most {} owners".format(
              self._effective_max_batch_size
            )
          )

    if not identifiers:
      raise ProbeBatchError("owner_user_ids must not be empty")
    owners = self._owner_lookup(identifiers)

    items = list()
    scheduled = list()
    ##
    ## Owners whose answer is known before any worker starts: unknown to history,
    ## no share link, or a cache entry still inside the window.  They are held
    ## rather than reported straight away because the task does not exist yet -
    ## it is created from ``items`` below - and replayed onto it once it does.
    ##
    settled = list()
    for owner_user_id in identifiers:
      row = owners.get(owner_user_id)
      if row is None:
        items.append(
          {
            "owner_user_id": owner_user_id,
            "state": STATE_ERROR,
            "message": "历史记录中没有该主播",
          }
        )
        settled.append((STATE_ERROR, owner_user_id, "历史记录中没有该主播"))
        continue

      share_url = row.get("live_share_url")
      if not share_url:
        items.append(
          {
            "owner_user_id": owner_user_id,
            "state": STATE_ERROR,
            "nickname": row.get("nickname"),
            "message": "该主播没有可用的直播分享链接",
          }
        )
        settled.append(
          (STATE_ERROR, owner_user_id, "该主播没有可用的直播分享链接")
        )
        continue

      cached = self._cached_state(row)
      if cached is not None:
        items.append(
          {
            "owner_user_id": owner_user_id,
            "nickname": row.get("nickname"),
            "live_share_url": share_url,
            **cached,
          }
        )
        settled.append(
          (
            cached["state"],
            owner_user_id,
            {
              "nickname": row.get("nickname"),
              "room_id": cached["room_id"],
              "live_share_url": share_url,
              "checked_at": cached["checked_at"],
              "cached": True,
            },
          )
        )
        continue

      items.append(
        {
          "owner_user_id": owner_user_id,
          "state": STATE_PENDING,
          "nickname": row.get("nickname"),
          "live_share_url": share_url,
          "cached": False,
        }
      )
      scheduled.append((owner_user_id, share_url))

    batch_id = self._store.create(items)
    self._open_task(batch_id, identifiers, settled)
    for owner_user_id, share_url in scheduled:
      self._executor.submit(self._run_one, batch_id, owner_user_id, share_url)
    return batch_id

  def _open_task(self, batch_id: str, identifiers: list, settled: list) -> None:
    """Mirror the batch onto the unified task record.

    Every owner is known here - a probe never discovers work while it runs - so
    the task is created with its full item list and a real total, and the
    outcomes already decided are replayed onto it immediately.

    The completion check that follows is what lets a batch answered entirely
    from the cache, or rejected entirely before any network call, be a finished
    task by the time the HTTP response is written.  A batch with work left is
    simply not complete yet and the check does nothing.
    """
    self._tasks.open(
      batch_id,
      title=self._batch_title(len(identifiers)),
      metadata={
        "platform": PLATFORM_DOUYIN,
        "legacy_batch_id": batch_id,
        "requested_count": len(identifiers),
      },
      items=identifiers,
    )
    self._tasks.start(batch_id)
    for state, owner_user_id, detail in settled:
      if state == STATE_ERROR:
        self._tasks.item_failed(batch_id, owner_user_id, detail)
      elif state == STATE_LIVING:
        self._tasks.item_living(batch_id, owner_user_id, **detail)
      else:
        self._tasks.item_offline(batch_id, owner_user_id, **detail)
    self._tasks.finish_if_complete(batch_id)

  def task_id_for(self, batch_id: str):
    """The unified task mirroring ``batch_id``, or ``None`` when there is not one.

    The association is held by the mirror; neither id is ever derived from the
    other.
    """
    return self._tasks.task_id(batch_id)

  def snapshot(self, batch_id: str):
    return self._store.snapshot(batch_id)

  def shutdown(self, wait: bool = False) -> None:
    self._executor.shutdown(wait=wait)
