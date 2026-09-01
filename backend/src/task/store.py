##<<Base>>
from copy import deepcopy
from datetime import datetime
from threading import Lock
from time import monotonic
from uuid import uuid4

##<<Third-part>>
from backend.src.task.errors import (
  TaskAlreadyFinished,
  TaskCapacityExceeded,
  TaskItemCapacityExceeded,
  TaskNotFound,
  TaskValidationError,
)
from backend.src.task.model import (
  ITEM_STATE_PENDING,
  TASK_STATE_PENDING,
  TASK_STATE_RUNNING,
  TERMINAL_ITEM_STATES,
  UNSET,
  is_terminal,
  normalize_progress,
  validate_item_state,
  validate_task_state,
  validate_task_type,
  validate_transition,
)


MAX_TASK_STORE_ENTRIES = 256
MAX_ACTIVE_TASKS_GLOBAL = 32
MAX_ACTIVE_TASKS_PER_USER = 8
MAX_ACTIVE_TASKS_BY_TYPE = {
  "post_download": 24,
  "live_record": 8,
  "owner_batch_download": 8,
  "live_probe": 8,
}
MAX_TASK_ITEMS_PER_TASK = 5000


class TaskStore:
  """The process-wide record of every background task, held in memory.

  Deliberately not persisted: a task describes work owned by *this* process, and
  a restart cannot resume a half-finished recording anyway, so a row surviving in
  a table would only ever describe a task nobody is running.

  Every method that mutates a task raises rather than ignoring an unknown id.  A
  worker updating a task it created should never find it missing, so silence
  there would hide a real defect.

  One item key is one logical unit of work, unique within a task; see ``create``
  for what that guarantees and why.
  """

##
## >>============================= private method =============================>>
##
  def __init__(
    self,
    retention_seconds: float = 600.0,
    clock=datetime.now,
    monotonic_clock=monotonic,
    max_entries: int = MAX_TASK_STORE_ENTRIES,
    max_active_global: int = MAX_ACTIVE_TASKS_GLOBAL,
    max_active_per_user: int = MAX_ACTIVE_TASKS_PER_USER,
    max_active_by_type: dict = None,
    max_items_per_task: int = MAX_TASK_ITEMS_PER_TASK,
  ) -> None:
    ##
    ## Two clocks on purpose: the wall clock is what the user reads, and it may
    ## jump; expiry counts on the monotonic one, which may not.
    ##
    self._retention_seconds = retention_seconds
    self._clock = clock
    self._monotonic = monotonic_clock
    self._max_entries = self._positive_limit(max_entries, "max_entries")
    self._max_active_global = self._positive_limit(
      max_active_global, "max_active_global"
    )
    self._max_active_per_user = self._positive_limit(
      max_active_per_user, "max_active_per_user"
    )
    active_by_type = (
      MAX_ACTIVE_TASKS_BY_TYPE
      if max_active_by_type is None
      else max_active_by_type
    )
    self._max_active_by_type = {
      validate_task_type(task_type): self._positive_limit(limit, task_type)
      for task_type, limit in dict(active_by_type).items()
    }
    self._max_items_per_task = self._positive_limit(
      max_items_per_task, "max_items_per_task"
    )
    self._guard = Lock()
    self._tasks = dict()
    self._sequence = 0

  @staticmethod
  def _positive_limit(value, label: str) -> int:
    if type(value) is not int or value < 1:
      raise ValueError("{} must be a positive integer".format(label))
    return value

  def _evict_expired(self) -> None:
    ##
    ## Caller must hold the guard.
    ##
    ## Only finished tasks expire.  Age is the wrong test for work still in
    ## flight: a live recording legitimately runs for hours, and dropping it
    ## because it is old would erase the one task the user most wants to watch.
    ## So expiry counts from the moment a task ended, and a task that has not
    ## ended is bounded by the work itself rather than by a timer.
    ##
    ## The consequence, stated so it is a decision and not an oversight: a
    ## ``pending`` or ``running`` task whose worker died never leaves the store.
    ## Reaping those needs a liveness signal the store does not have - it cannot
    ## tell a stalled download from a slow one - so it is deliberately out of
    ## scope here and belongs with the cancellation adapters, where something
    ## does own the threads.
    ##
    deadline = self._monotonic() - self._retention_seconds
    expired = [
      task_id
      for task_id, task in self._tasks.items()
      if task["expires_from"] is not None and task["expires_from"] <= deadline
    ]
    for task_id in expired:
      del self._tasks[task_id]

  def _pressure_evict_terminal(self) -> None:
    """Make one total-store slot using only the oldest finished records."""
    if len(self._tasks) < self._max_entries:
      return
    terminal = sorted(
      (
        task
        for task in self._tasks.values()
        if is_terminal(task["state"])
      ),
      key=lambda task: task["sequence"],
    )
    while len(self._tasks) >= self._max_entries and terminal:
      del self._tasks[terminal.pop(0)["task_id"]]

  def _check_active_capacity(self, task_type: str, app_user_id) -> None:
    active = [
      task
      for task in self._tasks.values()
      if task["state"] in (TASK_STATE_PENDING, TASK_STATE_RUNNING)
    ]
    if len(active) >= self._max_active_global:
      raise TaskCapacityExceeded("task active capacity is full")
    if app_user_id is not None and sum(
      1 for task in active if task["app_user_id"] == app_user_id
    ) >= self._max_active_per_user:
      raise TaskCapacityExceeded("task user capacity is full")
    type_limit = self._max_active_by_type.get(task_type)
    if type_limit is not None and sum(
      1 for task in active if task["task_type"] == task_type
    ) >= type_limit:
      raise TaskCapacityExceeded("task type capacity is full")

  def _bounded_item_keys(self, items) -> list:
    keys = []
    known = set()
    for observed, key in enumerate(items or (), start=1):
      if observed > self._max_items_per_task:
        raise TaskItemCapacityExceeded(
          "task accepts at most {} item inputs".format(
            self._max_items_per_task
          )
        )
      text = str(key)
      if text not in known:
        known.add(text)
        keys.append(text)
    return keys

  def _locked_task(self, task_id: str) -> dict:
    ##
    ## Caller must hold the guard.
    ##
    task = self._tasks.get(task_id)
    if task is None:
      raise TaskNotFound("unknown task: {!r}".format(task_id))
    return task

  def _snapshot(self, task: dict) -> dict:
    ##
    ## Caller must hold the guard.  Nothing mutable is shared with the caller:
    ## a snapshot handed out today must still read the same tomorrow.
    ##
    ## Deep rather than one level: metadata is arbitrary business data and does
    ## nest - a filter holding a list, a saved-file record holding urls - and a
    ## one-level copy would hand back a live reference to everything below it.
    ## Deep copying costs nothing at this size and removes a whole class of
    ## "who changed my task?" bugs.
    ##
    return {
      "task_id": task["task_id"],
      "app_user_id": task["app_user_id"],
      "task_type": task["task_type"],
      "state": task["state"],
      "title": task["title"],
      "message": task["message"],
      "created_at": task["created_at"],
      "started_at": task["started_at"],
      "finished_at": task["finished_at"],
      "progress": dict(task["progress"]),
      "metadata": deepcopy(task["metadata"]),
      "items": [
        {
          "key": item["key"],
          "state": item["state"],
          "message": item["message"],
          "metadata": deepcopy(item["metadata"]),
        }
        for item in task["items"].values()
      ],
    }

  @staticmethod
  def _app_user_id(value) -> int:
    if type(value) is not int or value < 1:
      raise TaskValidationError(
        "app_user_id must be a positive integer, got {!r}".format(value)
      )
    return value

  def _selected(
    self,
    *,
    state: str = None,
    task_type: str = None,
    limit: int = None,
    app_user_id=UNSET,
  ):
    if state is not None:
      validate_task_state(state)
    if task_type is not None:
      validate_task_type(task_type)
    if limit is not None and (type(limit) is not int or limit < 1):
      raise TaskValidationError(
        "limit must be an integer of at least 1, got {!r}".format(limit)
      )
    if app_user_id is not UNSET:
      app_user_id = self._app_user_id(app_user_id)

    with self._guard:
      self._evict_expired()
      ordered = sorted(
        self._tasks.values(), key=lambda task: task["sequence"], reverse=True
      )
      selected = []
      for task in ordered:
        if app_user_id is not UNSET and task["app_user_id"] != app_user_id:
          continue
        if state is not None and task["state"] != state:
          continue
        if task_type is not None and task["task_type"] != task_type:
          continue
        selected.append(self._snapshot(task))
        if limit is not None and len(selected) >= limit:
          break
      return selected

##
## >>============================= sub class method =============================>>
##
  def create(
    self,
    task_type: str,
    title: str = None,
    metadata: dict = None,
    items=None,
    total=UNSET,
    app_user_id=None,
  ) -> str:
    """Register a pending task and return its id.

    ``items`` are the units of work the caller already knows about; a task that
    discovers its work as it runs may start with none and grow.  When ``total``
    is not stated it follows the item count, and stays unknown when there are no
    items - a live recording has no final number to divide by.

    **Item key contract.**  A ``TaskItem.key`` identifies one logical unit of
    work and is unique within a task.  Duplicate keys are deduplicated, keeping
    first-seen order.  This is a decision, not an accident of the dict used to
    hold them, and callers may rely on it:

    * one key, one item, whatever a caller's list happens to repeat;
    * ``len(items)`` is therefore the number of units, which is what makes a
      derived ``total`` reachable and progress monotonic;
    * a legacy list that names the same unit twice - a browser sending an
      untidied selection - describes two passes over one unit, and the task
      counts units, not passes.

    Callers whose ids are not unit identities must key on something that is.
    """
    validate_task_type(task_type)
    if app_user_id is not None:
      app_user_id = self._app_user_id(app_user_id)
    ##
    ## Deduplicated while keeping submission order.  A caller may hand the same
    ## id twice - a browser sending a selection it did not tidy up - and one item
    ## per unit of work is the invariant everything else rests on: a total taken
    ## from a list with repeats would exceed the number of items that can ever
    ## finish, stranding the progress bar one short forever.
    ##
    keys = self._bounded_item_keys(items)
    resolved_total = len(keys) if total is UNSET else total
    if not keys and total is UNSET:
      resolved_total = None

    task_id = uuid4().hex
    now = self._clock()
    with self._guard:
      self._evict_expired()
      self._pressure_evict_terminal()
      self._check_active_capacity(task_type, app_user_id)
      if len(self._tasks) >= self._max_entries:
        raise TaskCapacityExceeded("task store capacity is full")
      self._sequence += 1
      self._tasks[task_id] = {
        "task_id": task_id,
        ##
        ## Ownership is fixed at creation.  There is deliberately no mutator:
        ## transferring a process-local task would rewrite who initiated work
        ## that has already begun.
        ##
        "app_user_id": app_user_id,
        "task_type": task_type,
        "state": TASK_STATE_PENDING,
        "title": title,
        "message": None,
        "created_at": now,
        "started_at": None,
        "finished_at": None,
        "progress": normalize_progress(0, resolved_total),
        "metadata": deepcopy(dict(metadata or {})),
        "items": {
          key: {
            "key": key,
            "state": ITEM_STATE_PENDING,
            "message": None,
            "metadata": {},
          }
          for key in keys
        },
        ##
        ## Ordering key for listing, and the moment expiry counts from.
        ##
        "sequence": self._sequence,
        "expires_from": None,
      }
    return task_id

  def get(self, task_id: str):
    """Return a detached copy of one task, or ``None`` when it is unknown.

    Reading tolerates a missing id because a browser may poll a task the store
    has since dropped; that is expected, not a defect.
    """
    with self._guard:
      self._evict_expired()
      task = self._tasks.get(task_id)
      if task is None:
        return None
      return self._snapshot(task)

  def get_for_user(self, task_id: str, app_user_id: int):
    """Return an owned task, hiding every other task as missing."""
    app_user_id = self._app_user_id(app_user_id)
    with self._guard:
      self._evict_expired()
      task = self._tasks.get(task_id)
      if task is None or task["app_user_id"] != app_user_id:
        return None
      return self._snapshot(task)

  def list(self, state: str = None, task_type: str = None, limit: int = None):
    """Return snapshots of the tasks matching every filter, newest first.

    Newest first because a task centre opens on what the user just submitted; a
    filter left as ``None`` means "do not narrow on this", while a filter with a
    value the lifecycle does not know is a caller bug and says so.
    """
    return self._selected(state=state, task_type=task_type, limit=limit)

  def list_for_user(
    self,
    app_user_id: int,
    state: str = None,
    task_type: str = None,
    limit: int = None,
  ):
    """Return only tasks created for one application user."""
    return self._selected(
      app_user_id=app_user_id,
      state=state,
      task_type=task_type,
      limit=limit,
    )

  def set_state(self, task_id: str, state: str, message=None) -> dict:
    """Move a task to ``state``, refusing anything off the transition table.

    ``message`` always describes the state just entered, so it is replaced on
    every change rather than accumulated.
    """
    now = self._clock()
    with self._guard:
      task = self._locked_task(task_id)
      validate_transition(task["state"], state)
      task["state"] = state
      task["message"] = message
      if state == TASK_STATE_RUNNING:
        task["started_at"] = now
      if is_terminal(state):
        task["finished_at"] = now
        task["expires_from"] = self._monotonic()
      return self._snapshot(task)

  def update_message(self, task_id: str, message) -> dict:
    """Replace what a task says it is doing, without moving its state.

    A long task narrates itself - "正在解析主播", then "正在读取第 3 页", then
    "正在下载 18 / 42" - and all of that happens inside one ``running`` state.
    Routing those through ``set_state`` would mean running -> running, which the
    transition table rejects for good reason, so narration gets its own door.

    Refused once the task has finished: at that point ``message`` is the reason
    it ended, not a status line.
    """
    with self._guard:
      task = self._locked_task(task_id)
      if is_terminal(task["state"]):
        raise TaskAlreadyFinished(
          "task {!r} finished as {!r} and keeps its final message".format(
            task_id, task["state"]
          )
        )
      task["message"] = message
      return self._snapshot(task)

  def update_metadata(self, task_id: str, fields: dict) -> dict:
    """Merge ``fields`` into the task's metadata, one level deep.

    A task whose work is one indivisible unit - a single post download - learns
    most of its record while it runs: where the files went, how many were saved,
    why it stopped.  Those facts describe the *task*, not an item of it, and
    ``create`` is too early to know them, so they need a door of their own.

    **Top level only.**  A stated key replaces whatever it named.  Nested merging
    is deliberately not offered: a ``result`` is one coherent account of one
    attempt, and blending a new one into an old one would produce a record of
    something that never happened.

    Refused once the task has finished, matching ``update_message``: after the
    end the record is what happened, and a late writer would be editing history.
    Callers therefore write their results *before* they finish the task.
    """
    ##
    ## Copied on the way in, so a caller that keeps and later mutates the dict it
    ## handed over cannot reach into the store through it.
    ##
    incoming = deepcopy(dict(fields or {}))
    with self._guard:
      task = self._locked_task(task_id)
      if is_terminal(task["state"]):
        raise TaskAlreadyFinished(
          "task {!r} finished as {!r} and keeps the record it ended with".format(
            task_id, task["state"]
          )
        )
      task["metadata"].update(incoming)
      return self._snapshot(task)

  def update_progress(self, task_id: str, current=UNSET, total=UNSET) -> dict:
    """Set either end of the progress pair, leaving anything unstated alone."""
    with self._guard:
      task = self._locked_task(task_id)
      progress = task["progress"]
      task["progress"] = normalize_progress(
        progress["current"] if current is UNSET else current,
        progress["total"] if total is UNSET else total,
      )
      return self._snapshot(task)

  def add_item(self, task_id: str, key, message=None, metadata=None) -> dict:
    """Register one unit of work, doing nothing when it is already known.

    A task that discovers its work while running - the owner walk pages through
    posts - meets the same id twice when a page overlaps or is retried.  Doing
    that through ``update_item`` would reset a post already downloaded back to
    pending, so registering has its own door and is deliberately a no-op on a
    key that exists, whatever state that key has reached.

    Registering does not touch progress: a pending item is not finished work, and
    the total belongs to whoever knows how much work there is.
    """
    key = str(key)
    with self._guard:
      task = self._locked_task(task_id)
      if key not in task["items"]:
        if len(task["items"]) >= self._max_items_per_task:
          raise TaskItemCapacityExceeded("task item capacity is full")
        task["items"][key] = {
          "key": key,
          "state": ITEM_STATE_PENDING,
          "message": message,
          "metadata": deepcopy(dict(metadata or {})),
        }
      return self._snapshot(task)

  def update_item(
    self,
    task_id: str,
    key,
    state=UNSET,
    message=UNSET,
    metadata=UNSET,
    advance_progress: bool = False,
  ) -> dict:
    """Record what happened to one unit of work.

    An unknown key is appended rather than rejected: a task that discovers its
    work while running - the owner walk pages through posts - has no complete
    list to declare up front.

    ``advance_progress`` recounts the finished items and writes the result as the
    progress position, inside the same lock as the item change.  Counting from a
    snapshot afterwards would let two workers finishing at once each write the
    number they saw, and the later write could be the smaller one.  Off by
    default: the store records, it does not decide what progress means.
    """
    key = str(key)
    if state is not UNSET:
      validate_item_state(state)
    with self._guard:
      task = self._locked_task(task_id)
      item = task["items"].get(key)
      if item is None:
        if len(task["items"]) >= self._max_items_per_task:
          raise TaskItemCapacityExceeded("task item capacity is full")
        item = {
          "key": key,
          "state": ITEM_STATE_PENDING,
          "message": None,
          "metadata": {},
        }
        task["items"][key] = item
      if state is not UNSET:
        item["state"] = state
      if message is not UNSET:
        item["message"] = message
      if metadata is not UNSET:
        item["metadata"] = deepcopy(dict(metadata or {}))
      if advance_progress:
        finished = sum(
          1
          for candidate in task["items"].values()
          if candidate["state"] in TERMINAL_ITEM_STATES
        )
        task["progress"] = normalize_progress(finished, task["progress"]["total"])
      return self._snapshot(task)

  def tracked(self) -> int:
    """How many tasks are currently held.  For tests and diagnostics."""
    with self._guard:
      self._evict_expired()
      return len(self._tasks)
