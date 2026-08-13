##<<Third-part>>
from backend.src.task.model import (
  TASK_STATE_CANCELLED,
  TASK_STATE_FAILED,
  TASK_STATE_PARTIAL,
  TASK_STATE_RUNNING,
  TASK_STATE_SUCCESS,
  UNSET,
)
from backend.src.task.store import TaskStore


class TaskService:
  """The one way business code touches the task record.

  Every lifecycle step has a name here, so no downloader, prober or route ever
  writes a state string of its own.  That is what keeps the vocabulary from
  drifting back into the four dialects this package replaces, and it means the
  legal transitions are enforced in exactly one place - the store's table.
  """

##
## >>============================= private method =============================>>
##
  def __init__(self, store: TaskStore = None) -> None:
    self._store = store if store is not None else TaskStore()

  @property
  def store(self) -> TaskStore:
    """The backing store.  Exposed for wiring and diagnostics, not for writes."""
    return self._store

##
## >>============================= sub class method =============================>>
##
  def create_task(
    self,
    task_type: str,
    title: str = None,
    metadata: dict = None,
    items=None,
    total=UNSET,
  ) -> dict:
    """Register a pending task and return its first snapshot.

    The snapshot rather than the bare id, because the caller almost always wants
    to hand the whole task back to the browser that asked for it.
    """
    task_id = self._store.create(
      task_type,
      title=title,
      metadata=metadata,
      items=items,
      total=total,
    )
    return self._store.get(task_id)

  def start_task(self, task_id: str, message: str = None) -> dict:
    """Mark a task as running.  Raises if it has already started or ended."""
    return self._store.set_state(task_id, TASK_STATE_RUNNING, message=message)

  def update_message(self, task_id: str, message) -> dict:
    """Say what the task is doing now, without changing what state it is in.

    The stage a long task is at - parsing the owner, reading page 3, downloading
    18 of 42 - is all one ``running`` state, so narrating it must not look like a
    transition.  Raises once the task has finished, where ``message`` has become
    the reason it ended.
    """
    return self._store.update_message(task_id, message)

  def update_progress(self, task_id: str, current=UNSET, total=UNSET) -> dict:
    """Report how far along a task is, leaving anything unstated alone."""
    return self._store.update_progress(task_id, current=current, total=total)

  def update_item(
    self,
    task_id: str,
    key,
    state=UNSET,
    message=UNSET,
    metadata=UNSET,
    advance_progress: bool = True,
  ) -> dict:
    """Report what happened to one unit of work.

    Progress follows the finished items by default, so an item-shaped task never
    has to count itself.  A task whose progress means something else - a
    recording counting segments, not items - passes ``advance_progress=False``
    and keeps the number it reported.
    """
    return self._store.update_item(
      task_id,
      key,
      state=state,
      message=message,
      metadata=metadata,
      advance_progress=advance_progress,
    )

##
## The three ``finish_*`` calls below currently pass straight through to the
## store, so finishing a task twice raises.  That is the store's invariant and it
## stays.  Whether *business* code should see an exception is a separate
## question: a downloader with several exit paths may prefer "end it unless it
## has already ended".  If that turns out to be the common shape during the
## migrations, an idempotent variant is added here - the service is the layer
## allowed to soften it - and the transition table is left alone.  Callers should
## therefore not assume that raising is a permanent part of this contract.
##
  def finish_success(self, task_id: str, message: str = None) -> dict:
    """End a task that did everything it was asked to do."""
    return self._store.set_state(task_id, TASK_STATE_SUCCESS, message=message)

  def finish_partial(self, task_id: str, message: str = None) -> dict:
    """End a task that did some of its work and could not do the rest."""
    return self._store.set_state(task_id, TASK_STATE_PARTIAL, message=message)

  def finish_failed(self, task_id: str, message: str = None) -> dict:
    """End a task that achieved nothing the user asked for."""
    return self._store.set_state(task_id, TASK_STATE_FAILED, message=message)

  def cancel_task(self, task_id: str, message: str = None) -> dict:
    """Mark a task cancelled.

    This changes the record only.  It does not stop a recording, interrupt a
    download or drop a queued item - nothing in this stage owns the threads doing
    that work.  Stopping real work needs a cancellation adapter per task type
    (the live recorder already has ``cancel_live_downloads``, the aweme
    downloader has ``shutdown_aweme_downloads``), and those are wired up when
    each business migrates onto this service.  Until then a cancelled task means
    "the user asked to stop", not "it has stopped".
    """
    return self._store.set_state(task_id, TASK_STATE_CANCELLED, message=message)

  def get_task(self, task_id: str):
    """Return one task, or ``None`` when it is unknown or has expired."""
    return self._store.get(task_id)

  def list_tasks(self, state: str = None, task_type: str = None, limit: int = None):
    """Return the tasks matching every filter, newest first."""
    return self._store.list(state=state, task_type=task_type, limit=limit)
