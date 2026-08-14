##<<Base>>
from datetime import datetime
from threading import Lock

##<<Third-part>>
from backend.src.library.loglib import get_logger
from backend.src.task.model import (
  ITEM_STATE_FAILED,
  ITEM_STATE_RUNNING,
  ITEM_STATE_SUCCESS,
  TASK_TYPE_LIVE_PROBE,
  TERMINAL_ITEM_STATES,
  is_terminal,
)


##
## Which platform was asked.  It lives in task metadata rather than in the task
## type, so a second platform reuses ``live_probe`` instead of minting
## ``douyin_live_probe`` beside it.
##
PLATFORM_DOUYIN = "douyin"

##
## What the probe found, recorded as item metadata rather than as an item state.
##
## This is the whole point of the mapping.  The user asked "is this host live?"
## and "no, they are not" is a complete, correct answer - the probe did its job -
## so both outcomes are ``success`` and only ``live_status`` tells them apart.
## Modelling ``offline`` as a failure would make a task centre count a perfectly
## healthy check as something that went wrong, and modelling it as its own item
## state would put the probe's private vocabulary back into the shared lifecycle
## the task package exists to replace.
##
LIVE_STATUS_LIVING = "living"
LIVE_STATUS_OFFLINE = "offline"


def _isoformat(value):
  ##
  ## Task metadata is arbitrary business data that the API hands to
  ## ``jsonify`` as it is - only the task's own timestamps are converted on the
  ## way out.  A ``datetime`` left in here would therefore travel all the way to
  ## the response and fail to serialise, so the adapter that knows the probe
  ## produces one is the layer that flattens it.  Done here rather than by
  ## teaching the task serialiser to walk metadata recursively, which would make
  ## every business pay for one business's field.
  ##
  if isinstance(value, datetime):
    return value.isoformat(timespec="milliseconds")
  return value


def _live_metadata(
  live_status: str,
  nickname=None,
  room_id=None,
  title=None,
  live_share_url=None,
  checked_at=None,
  cached: bool = False,
) -> dict:
  """What one answered probe knows, as JSON-safe metadata.

  Facts the platform did not give are left out rather than written as ``None``:
  an offline room has no title, and ``"title": null`` reads as "the title is
  missing" when the truth is that the question does not apply.
  """
  facts = {
    "live_status": live_status,
    "nickname": nickname,
    "room_id": room_id,
    "title": title,
    "live_share_url": live_share_url,
    "checked_at": _isoformat(checked_at),
  }
  known = {key: value for key, value in facts.items() if value is not None}
  ##
  ## Always stated, because "was this answer served from the cache?" has a
  ## meaningful ``False`` and dropping it would lose that.
  ##
  known["cached"] = bool(cached)
  return known


class LiveProbeTaskMirror:
  """Reports a live status probe onto the unified TaskService.

  Live probing is temporarily dual-written: ``ProbeBatchStore`` remains the
  legacy compatibility surface the current history page polls, and
  ``TaskService`` is the unified contract the next frontend will read.  This
  class is the whole of the second write, so ``LiveProbeService`` gains report
  calls rather than task-layer branching, and removing the mirror later is one
  file plus its call sites.

  Three rules hold everywhere here:

  * **Telemetry, never workflow.**  A probe must not fail because reporting
    did.  Every call into the task layer is guarded and a failure is logged at
    error level, never raised and never silently dropped.
  * **The association is recorded, not derived.**  A batch id and a task id are
    independent identifiers; this class holds the map between them, and nothing
    parses one out of the other.
  * **Nothing is remembered per owner.**  ``LiveProbeService`` deduplicates
    before it opens a batch, so each owner settles exactly once and there is no
    repeated-unit problem of the kind ``OwnerTaskMirror`` has to arbitrate.  The
    only state here is one entry per batch.
  """

##
## >>============================= private method =============================>>
##
  def __init__(self, task_service=None) -> None:
    ##
    ## ``None`` is a supported wiring, not a defect: a service built without a
    ## task service - an old test, a script - still probes, it just reports
    ## nothing.  Every method below is then a no-op.
    ##
    self._task_service = task_service
    self._guard = Lock()
    self._task_ids = dict()

  @property
  def enabled(self) -> bool:
    return self._task_service is not None

  def _safe(self, action: str, batch_id: str, call):
    """Run one task-layer call, turning any failure into a logged no-op."""
    try:
      return call()
    except Exception as e:
      ##
      ## Deliberately broad, deliberately loud.  Anything the task layer can
      ## raise - an unknown task, a rejected transition, a bug in the store - is
      ## a reporting problem, and the probe it describes is still valid work
      ## whose legacy answer must reach the page unchanged.  It is logged rather
      ## than swallowed so the failure is visible without being fatal.
      ##
      get_logger().error(
        "live probe task mirror: {} failed for batch {}: {}".format(
          action, batch_id, e
        )
      )
      return None

  def _resolve(self, batch_id: str):
    with self._guard:
      return self._task_ids.get(batch_id)

  def _prune(self) -> None:
    ##
    ## Caller must hold the guard.  Associations must not outlive the tasks they
    ## point at: the task store evicts finished tasks on its own schedule, and a
    ## map that kept every batch id ever seen would be the one thing in this
    ## process that grows without bound.
    ##
    ## Lazy, at the one moment a new entry is added, so a long-running server
    ## needs no background sweeper to stay bounded.
    ##
    stale = [
      batch_id
      for batch_id, task_id in self._task_ids.items()
      if self._task_service.get_task(task_id) is None
    ]
    for batch_id in stale:
      del self._task_ids[batch_id]

  def _settle(self, action: str, batch_id: str, owner_user_id, state, message, metadata):
    """Record one owner's outcome, which is what moves the task's progress."""
    task_id = self._resolve(batch_id)
    if task_id is None:
      return
    self._safe(
      action,
      batch_id,
      lambda: self._task_service.update_item(
        task_id,
        owner_user_id,
        state=state,
        message=message,
        metadata=metadata,
      ),
    )

##
## >>============================= sub class method =============================>>
##
  def task_id(self, batch_id: str):
    """The task mirroring ``batch_id``, or ``None`` when there is not one."""
    return self._resolve(batch_id)

  def tracked(self) -> int:
    """How many batch associations are held.  For tests and diagnostics."""
    with self._guard:
      return len(self._task_ids)

  def open(self, batch_id: str, title: str, metadata: dict, items):
    """Create the task for a batch that has just been registered.

    ``items`` are the deduplicated owner ids, which are known in full before any
    probing starts - a probe never discovers work while it runs - so the task has
    its complete item list and a real total from the moment it exists.

    Returns the task id, or ``None`` when mirroring is off or the task layer
    refused, in which case every later call for this batch is a no-op.
    """
    if not self.enabled:
      return None

    task = self._safe(
      "create",
      batch_id,
      lambda: self._task_service.create_task(
        TASK_TYPE_LIVE_PROBE,
        title=title,
        metadata=metadata,
        items=items,
      ),
    )
    if task is None:
      return None

    with self._guard:
      self._prune()
      self._task_ids[batch_id] = task["task_id"]
    return task["task_id"]

  def start(self, batch_id: str, message: str = None) -> None:
    """Report that the batch has been accepted and is being worked on."""
    task_id = self._resolve(batch_id)
    if task_id is None:
      return
    self._safe(
      "start",
      batch_id,
      lambda: self._task_service.start_task(task_id, message=message),
    )

  def item_running(self, batch_id: str, owner_user_id) -> None:
    """Report that one owner is being probed right now."""
    task_id = self._resolve(batch_id)
    if task_id is None:
      return
    self._safe(
      "item running",
      batch_id,
      lambda: self._task_service.update_item(
        task_id, owner_user_id, state=ITEM_STATE_RUNNING
      ),
    )

  def item_living(self, batch_id: str, owner_user_id, **facts) -> None:
    """Report that one owner was found broadcasting."""
    self._settle(
      "item living",
      batch_id,
      owner_user_id,
      ITEM_STATE_SUCCESS,
      None,
      _live_metadata(LIVE_STATUS_LIVING, **facts),
    )

  def item_offline(self, batch_id: str, owner_user_id, **facts) -> None:
    """Report that one owner was found not broadcasting.

    A success: the question was answered.  See ``LIVE_STATUS_OFFLINE``.
    """
    self._settle(
      "item offline",
      batch_id,
      owner_user_id,
      ITEM_STATE_SUCCESS,
      None,
      _live_metadata(LIVE_STATUS_OFFLINE, **facts),
    )

  def item_failed(self, batch_id: str, owner_user_id, message: str) -> None:
    """Report that one owner's live status could not be determined at all.

    This is the *no answer* case - an unknown owner, a missing share link, a
    timeout, a rejected request, a malformed response - and never the case where
    the platform answered "not broadcasting".
    """
    self._settle(
      "item failed", batch_id, owner_user_id, ITEM_STATE_FAILED, message, None
    )

  def finish_if_complete(self, batch_id: str, message: str = None) -> None:
    """End the task once every owner has an outcome, and not before.

    Called after each owner settles, including the ones resolved before any
    worker starts, so an all-cached batch is already finished by the time its
    HTTP response is written and a mixed batch waits for its last worker.

    The read, the decision and the transition are one critical section.  Two
    workers finishing at the same moment would otherwise both see a complete
    batch and both try to end the task, and the second would be rejected by the
    transition table; serialising them here means exactly one ends it and the
    loser simply finds the work already done.
    """
    task_id = self._resolve(batch_id)
    if task_id is None:
      return

    with self._guard:
      task = self._safe(
        "read for finish", batch_id, lambda: self._task_service.get_task(task_id)
      )
      if task is None:
        return
      if is_terminal(task["state"]):
        ##
        ## Not a warning, unlike the same check in ``OwnerTaskMirror``.  There a
        ## second finish means two owners believed they ended one job; here this
        ## method is a question - "is it over yet?" - asked after every owner, so
        ## losing the race to another worker is the expected answer and not a
        ## fault worth logging.  A transition that is genuinely rejected still
        ## reaches the log through ``_safe``.
        ##
        return

      states = [item["state"] for item in task["items"]]
      if not states or not all(state in TERMINAL_ITEM_STATES for state in states):
        return

      answered = sum(1 for state in states if state == ITEM_STATE_SUCCESS)
      failed = sum(1 for state in states if state == ITEM_STATE_FAILED)

      ##
      ## Judged on whether the question was answered, never on what the answer
      ## was: a batch that found every host offline did everything it was asked
      ## to do.
      ##
      if failed and answered:
        outcome = "partial"
        final_message = message or "{} 个主播中有 {} 个检查失败".format(
          len(states), failed
        )
      elif failed:
        outcome = "failed"
        final_message = message or "{} 个主播全部检查失败".format(failed)
      else:
        outcome = "success"
        final_message = message

      finishers = {
        "success": self._task_service.finish_success,
        "partial": self._task_service.finish_partial,
        "failed": self._task_service.finish_failed,
      }
      self._safe(
        "finish {}".format(outcome),
        batch_id,
        lambda: finishers[outcome](task_id, message=final_message),
      )
