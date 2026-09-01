##<<Base>>
from threading import Lock

##<<Third-part>>
from backend.src.library.loglib import get_logger
from backend.src.service.task_creation import (
  CAPACITY_MESSAGE,
  TaskCreationCapacityExceeded,
  TaskCreationUnavailable,
)
from backend.src.task.model import (
  ITEM_STATE_FAILED,
  ITEM_STATE_RUNNING,
  ITEM_STATE_SKIPPED,
  ITEM_STATE_SUCCESS,
  TASK_TYPE_OWNER_BATCH_DOWNLOAD,
  UNSET,
  is_terminal,
)
from backend.src.task.errors import TaskCapacityExceeded


##
## Which platform the work ran against.  It lives in task metadata rather than in
## the task type so that a second platform reuses ``owner_batch_download``
## instead of minting a type per platform.
##
PLATFORM_DOUYIN = "douyin"

##
## How the user asked.  Absent from a legacy job's metadata, so a task carrying
## it was created through ``POST /api/tasks`` against a server-side resolution.
##
SOURCE_TASK_API = "task_api"

##
## What an owner walk that found nothing should say.  Stated once because both
## the empty-owner case and its test need the same words.
##
NO_POSTS_MESSAGE = "该主播没有可下载的作品"

##
## What a strict creation says when it could not produce a task.
##
NOT_CREATED_MESSAGE = "任务创建失败，请稍后重试"

##
## How good an outcome is for one post, for this business.  A repeated pass over
## the same unit may improve on what was recorded but never undo it, so the
## ranking is what decides which pass the task keeps.
##
## ``skipped`` outranks ``failed`` because here it means the file is already on
## disk - the user's goal is met - and a later pass that fails must not erase a
## post that is sitting there.  Local to this mirror on purpose: another business
## may rank its own outcomes differently, and the task layer stays neutral.
##
_OUTCOME_RANK = {
  ITEM_STATE_FAILED: 1,
  ITEM_STATE_SKIPPED: 2,
  ITEM_STATE_SUCCESS: 3,
}


class OwnerTaskMirror:
  """Reports an owner batch download onto the unified TaskService.

  Owner batch download is temporarily dual-written: ``JobStore`` remains the
  legacy compatibility surface that the current page polls, and ``TaskService``
  is the unified contract the next frontend will read.  This class is the whole
  of the second write, so ``PostDownloadJobService`` gains report calls rather
  than branching logic, and removing the mirror later is one file plus its call
  sites.

  Two rules hold everywhere here:

  * **Telemetry, never workflow.**  Downloading must not fail because reporting
    did.  Every call into the task layer is guarded and a failure is logged at
    error level, never raised and never silently dropped.
  * **The association is recorded, not derived.**  A job id and a task id are
    independent identifiers; this class holds the map between them, and nothing
    parses one out of the other.
  """

##
## >>============================= private method =============================>>
##
  def __init__(self, task_service=None) -> None:
    ##
    ## ``None`` is a supported wiring, not a defect: a runtime built without a
    ## task service - an old test, a script - still downloads, it just reports
    ## nothing.  Every method below is then a no-op.
    ##
    self._task_service = task_service
    self._guard = Lock()
    self._task_ids = dict()
    ##
    ## What each job has recorded for each unit so far, as ``key -> rank``.  A
    ## legacy selection may carry the same id twice - the browser does not tidy
    ## it up - and the legacy loop faithfully downloads it twice.  The task
    ## counts units of work, not passes over a list, so a second pass may only
    ## improve what is recorded.
    ##
    ## Released as soon as a job ends: it holds one entry per post, which for a
    ## walk of several hundred is the bulk of what this class remembers, and
    ## after the end no further pass is expected.
    ##
    self._settled = dict()

  @property
  def enabled(self) -> bool:
    return self._task_service is not None

  def _safe(self, action: str, job_id: str, call):
    """Run one task-layer call, turning any failure into a logged no-op."""
    try:
      return call()
    except Exception as e:
      ##
      ## Deliberately broad, deliberately loud.  Anything the task layer can
      ## raise - an unknown task, a rejected transition, a bug in the store - is
      ## a reporting problem, and the download it describes is still valid work
      ## that must continue.  It is logged rather than swallowed so the failure
      ## is visible without being fatal.
      ##
      get_logger().error(
        "owner task mirror: {} failed for job {}: {}".format(action, job_id, e)
      )
      return None

  def _resolve(self, job_id: str):
    with self._guard:
      return self._task_ids.get(job_id)

  def _prune(self) -> None:
    ##
    ## Caller must hold the guard.  Associations must not outlive the tasks they
    ## point at: the task store evicts finished tasks on its own schedule, and a
    ## map that kept every job id ever seen would be the one thing in this
    ## process that grows without bound.
    ##
    stale = [
      job_id
      for job_id, task_id in self._task_ids.items()
      if self._task_service.get_task(task_id) is None
    ]
    for job_id in stale:
      del self._task_ids[job_id]
      self._settled.pop(job_id, None)

##
## >>============================= sub class method =============================>>
##
  def task_id(self, job_id: str):
    """The task mirroring ``job_id``, or ``None`` when there is not one."""
    return self._resolve(job_id)

  def open(self, job_id: str, title: str, metadata: dict, items=None, total=UNSET,
           app_user_id=None):
    """Create the task for a job that has just been registered.

    Returns the task id, or ``None`` when mirroring is off or the task layer
    refused - in which case every later call for this job is a no-op.
    """
    if not self.enabled:
      return None

    task = self._safe(
      "create",
      job_id,
      lambda: self._task_service.create_task(
        TASK_TYPE_OWNER_BATCH_DOWNLOAD,
        title=title,
        metadata=metadata,
        items=items,
        total=total,
        app_user_id=app_user_id,
      ),
    )
    if task is None:
      return None

    with self._guard:
      self._prune()
      self._task_ids[job_id] = task["task_id"]
      self._settled[job_id] = dict()
    return task["task_id"]

  def open_strict(self, job_id: str, title: str, metadata: dict, items=None,
                  total=UNSET, app_user_id=None) -> str:
    """Create and associate the task for a job that was promised one.

    The strict twin of ``open``.  ``open`` is telemetry over work that runs
    regardless, so it swallows a refusal and returns ``None``; this one is
    called where the caller has been told a task exists, so a refusal has to
    travel and stop the work rather than be logged and forgotten.
    """
    if not self.enabled:
      raise TaskCreationUnavailable(NOT_CREATED_MESSAGE)

    try:
      task = self._task_service.create_task(
        TASK_TYPE_OWNER_BATCH_DOWNLOAD,
        title=title,
        metadata=metadata,
        items=items,
        total=total,
        app_user_id=app_user_id,
      )
    except TaskCapacityExceeded:
      get_logger().warning(
        "owner task mirror: strict create rejected for job {}: capacity".format(
          job_id
        )
      )
      raise TaskCreationCapacityExceeded(CAPACITY_MESSAGE)
    except Exception as e:
      get_logger().error(
        "owner task mirror: strict create failed for job {}: {}".format(job_id, e)
      )
      raise TaskCreationUnavailable(NOT_CREATED_MESSAGE)

    if task is None:
      raise TaskCreationUnavailable(NOT_CREATED_MESSAGE)

    with self._guard:
      self._prune()
      self._task_ids[job_id] = task["task_id"]
      self._settled[job_id] = dict()
    return task["task_id"]

  def start(self, job_id: str, message: str = None) -> None:
    """Report that a worker has picked the job up."""
    task_id = self._resolve(job_id)
    if task_id is None:
      return
    self._safe(
      "start",
      job_id,
      lambda: self._task_service.start_task(task_id, message=message),
    )

  def narrate(self, job_id: str, message: str) -> None:
    """Report what stage the job is at, without moving its state."""
    task_id = self._resolve(job_id)
    if task_id is None:
      return
    self._safe(
      "narrate",
      job_id,
      lambda: self._task_service.update_message(task_id, message),
    )

  def add_item(self, job_id: str, key) -> None:
    """Register a post discovered while walking, once per id."""
    task_id = self._resolve(job_id)
    if task_id is None:
      return
    self._safe(
      "add item",
      job_id,
      lambda: self._task_service.add_item(task_id, key),
    )

  def item_running(self, job_id: str, key) -> None:
    """Report that work on one unit has begun.

    Ignored for a unit this job has already recorded an outcome for: the legacy
    list may name the same post twice, and moving a finished item back to running
    would walk the progress bar backwards - 2 / 2, then 1 / 2, then 2 / 2 again -
    which reads as a fault rather than as a duplicate.

    The guard is by outcome recorded, not by lock over the download: two passes
    over the same id genuinely running at once would both be reported, which is
    an honest picture of what is happening.
    """
    task_id = self._resolve(job_id)
    if task_id is None:
      return
    with self._guard:
      if str(key) in self._settled.get(job_id, {}):
        return
    self._safe(
      "item running",
      job_id,
      lambda: self._task_service.update_item(task_id, key, state=ITEM_STATE_RUNNING),
    )

  def item_finished(
    self,
    job_id: str,
    key,
    state: str,
    message: str = None,
    metadata: dict = None,
  ) -> None:
    """Record one post's outcome, which is what moves the task's progress."""
    task_id = self._resolve(job_id)
    if task_id is None:
      return
    text = str(key)
    rank = _OUTCOME_RANK.get(state, 0)
    ##
    ## Decided and written under one lock, so two workers reporting the same unit
    ## at once cannot interleave into "the worse one landed last".  The store's
    ## own lock is taken inside this one and nothing takes them the other way
    ## round, so the nesting has no cycle.
    ##
    with self._guard:
      recorded_rank = self._settled.get(job_id, {}).get(text)
      if recorded_rank is not None and rank <= recorded_rank:
        ##
        ## A repeated pass that is no better than what is already recorded.  The
        ## whole update is dropped rather than merged: the message and the
        ## metadata belong to the pass whose state was adopted, and mixing them
        ## would describe an outcome that never happened.
        ##
        return
      recorded = self._safe(
        "item finished",
        job_id,
        lambda: self._task_service.update_item(
          task_id,
          key,
          state=state,
          message=message,
          metadata=metadata if metadata is not None else UNSET,
        ),
      )
      if recorded is None:
        ##
        ## The outcome never landed, so the unit is not settled and a later pass
        ## over it is still worth reporting.
        ##
        return
      self._settled.setdefault(job_id, {})[text] = rank

  def settle_total(self, job_id: str) -> None:
    """Fix the total once every post is known.

    Only the end of a walk knows how many posts there were.  The count comes
    from the items actually registered rather than from the platform's
    ``aweme_count``, which is a profile statistic that can disagree with what
    the pages hand over.
    """
    task_id = self._resolve(job_id)
    if task_id is None:
      return

    task = self._safe(
      "read for total", job_id, lambda: self._task_service.get_task(task_id)
    )
    if task is None:
      return
    self._settle_total(job_id, task_id, task)

  def _settle_total(self, job_id: str, task_id: str, task: dict) -> None:
    self._safe(
      "settle total",
      job_id,
      lambda: self._task_service.update_progress(task_id, total=len(task["items"])),
    )

  def finish(self, job_id: str, message: str = None, stopped_early: bool = False):
    """End the task, choosing the end state from what its items achieved.

    ``stopped_early`` marks the path where the job itself raised - an expired
    session part way through a walk, most often.  Work already downloaded still
    counts, so such a job ends ``partial`` rather than throwing away the record
    of what it did manage.
    """
    task_id = self._resolve(job_id)
    if task_id is None:
      return

    task = self._safe(
      "read for finish", job_id, lambda: self._task_service.get_task(task_id)
    )
    if task is None:
      return
    if is_terminal(task["state"]):
      ##
      ## Checked rather than discovered through an exception: a second finish
      ## means two owners believe they ended one job, which is worth saying out
      ## loud even though the first answer stands.
      ##
      get_logger().warning(
        "owner task mirror: job {} finished again, task {} is already {}".format(
          job_id, task_id, task["state"]
        )
      )
      self._release_units(job_id)
      return

    ##
    ## Settled here as well as at the end of a walk, so that a caller which never
    ## called ``settle_total`` cannot leave a finished task claiming an unknown
    ## total.  For a selected download this writes back the number it already
    ## had; for a walk it is the count actually discovered.
    ##
    self._settle_total(job_id, task_id, task)

    states = [item["state"] for item in task["items"]]
    achieved = sum(
      1 for state in states if state in (ITEM_STATE_SUCCESS, ITEM_STATE_SKIPPED)
    )
    failed = sum(1 for state in states if state == ITEM_STATE_FAILED)

    if stopped_early:
      ##
      ## The legacy message already says how far it got; it is carried through
      ## unchanged so both surfaces tell the user the same story.
      ##
      outcome = "partial" if achieved else "failed"
      final_message = message
    elif not states:
      ##
      ## An owner with nothing downloadable.  Reported as success with a reason
      ## rather than as a failure, and never as a made-up "0 / 0 done".
      ##
      outcome = "success"
      final_message = message or NO_POSTS_MESSAGE
    elif failed and achieved:
      outcome = "partial"
      final_message = message or "{} 个作品中有 {} 个失败".format(len(states), failed)
    elif failed:
      outcome = "failed"
      final_message = message or "{} 个作品全部失败".format(failed)
    else:
      outcome = "success"
      final_message = message

    self._finish_as(outcome, job_id, task_id, final_message)
    ##
    ## The per-unit notes have done their job.  The association itself stays, so
    ## a browser holding the task id can still read the finished task; it is
    ## dropped by ``_prune`` once the task store has forgotten the task.
    ##
    self._release_units(job_id)

  def _release_units(self, job_id: str) -> None:
    with self._guard:
      self._settled.pop(job_id, None)

  def tracked(self) -> int:
    """How many job associations are held.  For tests and diagnostics."""
    with self._guard:
      return len(self._task_ids)

  def tracked_units(self, job_id: str) -> int:
    """How many per-unit notes are held for one job.  For tests."""
    with self._guard:
      return len(self._settled.get(job_id, {}))

  def _finish_as(self, outcome: str, job_id: str, task_id: str, message) -> None:
    finishers = {
      "success": self._task_service.finish_success,
      "partial": self._task_service.finish_partial,
      "failed": self._task_service.finish_failed,
    }
    self._safe(
      "finish {}".format(outcome),
      job_id,
      lambda: finishers[outcome](task_id, message=message),
    )
