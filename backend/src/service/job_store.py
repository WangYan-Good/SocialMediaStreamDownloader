##<<Base>>
from threading import Lock
from time import monotonic
from uuid import uuid4


##
## Progress storage for user-triggered background work.
##
## Deliberately separate from ``live_probe.ProbeBatchStore``: that one is shaped
## around probing a batch of owners and is covered by its own tests.  This one
## holds an ordered item list with per-item state, which the post download job
## needs.  Two small stores beat one store trying to be both.
##

STATE_PENDING = "pending"
STATE_RUNNING = "running"
STATE_DONE = "done"
STATE_ERROR = "error"
STATE_SKIPPED = "skipped"

##
## A job is finished when nothing is still waiting or in flight.
##
_TERMINAL_STATES = (STATE_DONE, STATE_ERROR, STATE_SKIPPED)

JOB_RUNNING = "running"
JOB_DONE = "done"
JOB_ERROR = "error"


class JobStore:
  """Holds job progress in memory, dropping jobs once they are stale.

  Entries expire on their own so a long-running server does not accumulate one
  record per download the user ever started.
  """

  def __init__(self, retention_seconds: float = 600.0, clock=monotonic) -> None:
    self._retention_seconds = retention_seconds
    self._clock = clock
    self._guard = Lock()
    self._jobs = {}

  def _evict_expired(self) -> None:
    now = self._clock()
    expired = [
      job_id
      for job_id, job in self._jobs.items()
      if now - job["touched_at"] >= self._retention_seconds
    ]
    for job_id in expired:
      del self._jobs[job_id]

  def create(self, keys, payload: dict = None) -> str:
    """Register a job over ``keys`` and return its id.

    ``keys`` are whatever identifies each unit of work - aweme ids here.  Order is
    preserved so the UI can show progress against the list the user submitted.
    """
    job_id = uuid4().hex
    now = self._clock()
    with self._guard:
      self._evict_expired()
      self._jobs[job_id] = {
        "state": JOB_RUNNING,
        "message": None,
        "created_at": now,
        "touched_at": now,
        "order": [str(key) for key in keys],
        "items": {
          str(key): {"key": str(key), "state": STATE_PENDING, "message": None}
          for key in keys
        },
        "payload": dict(payload or {}),
      }
    return job_id

  def update_item(self, job_id: str, key, **fields) -> None:
    with self._guard:
      job = self._jobs.get(job_id)
      if job is None:
        return
      item = job["items"].get(str(key))
      if item is None:
        ##
        ## A job that grows while it runs - "download everything" discovers items
        ## page by page - appends rather than dropping the update.
        ##
        item = {"key": str(key), "state": STATE_PENDING, "message": None}
        job["items"][str(key)] = item
        job["order"].append(str(key))
      item.update(fields)
      job["touched_at"] = self._clock()

  def finish(self, job_id: str, state: str = JOB_DONE, message=None) -> None:
    with self._guard:
      job = self._jobs.get(job_id)
      if job is None:
        return
      job["state"] = state
      job["message"] = message
      job["touched_at"] = self._clock()

  def snapshot(self, job_id: str):
    """Return a copy of one job, or ``None`` if it is unknown or expired."""
    with self._guard:
      self._evict_expired()
      job = self._jobs.get(job_id)
      if job is None:
        return None
      items = [dict(job["items"][key]) for key in job["order"]]
      finished = sum(
        1 for item in items if item["state"] in _TERMINAL_STATES
      )
      return {
        "job_id": job_id,
        "state": job["state"],
        "message": job["message"],
        "total": len(items),
        "finished": finished,
        "items": items,
      }

  def tracked(self) -> int:
    """How many jobs are currently held.  For tests."""
    with self._guard:
      self._evict_expired()
      return len(self._jobs)
