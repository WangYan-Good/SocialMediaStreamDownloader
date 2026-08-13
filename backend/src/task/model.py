##<<Base>>
from copy import deepcopy
from datetime import datetime

##<<Third-part>>
from backend.src.task.errors import (
  InvalidProgress,
  InvalidTaskItemState,
  InvalidTaskState,
  InvalidTaskTransition,
  UnknownTaskType,
)


##
## Distinguishes "the caller did not mention this field" from "the caller asked
## for None".  Both are meaningful: a total may legitimately be unknown, so a
## plain None default could not tell "leave it" from "it is unknowable".
##
UNSET = object()


##
## The one lifecycle every background action reports against.  Deliberately
## small: the old vocabularies - ``done``/``error``/``skipped`` from JobStore and
## ``living``/``offline`` from the probe store - describe what happened to one
## unit of work, not whether the user's action is over.  They stay available as
## item states and metadata; they never appear as a task state.
##
TASK_STATE_PENDING = "pending"
TASK_STATE_RUNNING = "running"
TASK_STATE_SUCCESS = "success"
TASK_STATE_PARTIAL = "partial"
TASK_STATE_FAILED = "failed"
TASK_STATE_CANCELLED = "cancelled"

TASK_STATES = (
  TASK_STATE_PENDING,
  TASK_STATE_RUNNING,
  TASK_STATE_SUCCESS,
  TASK_STATE_PARTIAL,
  TASK_STATE_FAILED,
  TASK_STATE_CANCELLED,
)

##
## Per-item outcomes.  A task is ``partial`` when its items disagree; an item is
## never ``partial`` because an item is one indivisible piece of work.
##
ITEM_STATE_PENDING = "pending"
ITEM_STATE_RUNNING = "running"
ITEM_STATE_SUCCESS = "success"
ITEM_STATE_FAILED = "failed"
ITEM_STATE_SKIPPED = "skipped"

TASK_ITEM_STATES = (
  ITEM_STATE_PENDING,
  ITEM_STATE_RUNNING,
  ITEM_STATE_SUCCESS,
  ITEM_STATE_FAILED,
  ITEM_STATE_SKIPPED,
)

##
## Stable wire identifiers for what a task is doing.  These are strings on
## purpose and are never derived from a Python class name: the frontend filters
## on them and they must survive any refactor of the services behind them.
##
## They name the *kind of work*, never the platform it runs against.  A second
## platform records itself in ``metadata["platform"]`` - "douyin", "bilibili" -
## and reuses ``post_download``.  Minting ``douyin_post_download`` and
## ``bilibili_post_download`` instead would multiply this list by every platform
## added and force the task centre to special-case each one to answer "show me
## the downloads".  Adding a genuinely new *kind* of work is what adds a constant
## here.
##
TASK_TYPE_LIVE_RECORD = "live_record"
TASK_TYPE_POST_DOWNLOAD = "post_download"
TASK_TYPE_OWNER_BATCH_DOWNLOAD = "owner_batch_download"
TASK_TYPE_LIVE_PROBE = "live_probe"

TASK_TYPES = (
  TASK_TYPE_LIVE_RECORD,
  TASK_TYPE_POST_DOWNLOAD,
  TASK_TYPE_OWNER_BATCH_DOWNLOAD,
  TASK_TYPE_LIVE_PROBE,
)

##
## An item in one of these will not run again, whatever the outcome was.
## ``skipped`` belongs here: a post that was already downloaded is finished work,
## and leaving it out would stall a progress bar on nothing.
##
TERMINAL_ITEM_STATES = (
  ITEM_STATE_SUCCESS,
  ITEM_STATE_FAILED,
  ITEM_STATE_SKIPPED,
)

##
## Once a task reaches one of these it is over and never moves again.
##
TERMINAL_TASK_STATES = (
  TASK_STATE_SUCCESS,
  TASK_STATE_PARTIAL,
  TASK_STATE_FAILED,
  TASK_STATE_CANCELLED,
)

##
## The whole state machine, in one place.  Nothing outside this module decides
## whether a change is legal, which is what keeps "who set this to failed?" a
## question with an answer.
##
## Known trade-off, recorded rather than resolved here: the table has no self
## edges, so finishing an already finished task raises.  That is the right
## invariant for the store - it catches two owners each believing they finished
## the same work.  It is not necessarily the right ergonomics for business code
## with several exit paths, where a "finish unless it is already over" helper may
## read better.  Such a helper belongs in the service layer and can be added
## without touching this table; nothing here should be read as promising that
## every future ``finish_*`` on the service raises.
##
_TRANSITIONS = {
  TASK_STATE_PENDING: (
    TASK_STATE_RUNNING,
    ##
    ## A submission may be rejected, or the user may drop it, before any worker
    ## picks it up.  Both must be expressible without a fake running phase.
    ##
    TASK_STATE_FAILED,
    TASK_STATE_CANCELLED,
  ),
  TASK_STATE_RUNNING: (
    TASK_STATE_SUCCESS,
    TASK_STATE_PARTIAL,
    TASK_STATE_FAILED,
    TASK_STATE_CANCELLED,
  ),
  TASK_STATE_SUCCESS: (),
  TASK_STATE_PARTIAL: (),
  TASK_STATE_FAILED: (),
  TASK_STATE_CANCELLED: (),
}


def is_terminal(state: str) -> bool:
  """Whether ``state`` is an end state.  Unknown strings are not terminal."""
  return state in TERMINAL_TASK_STATES


def validate_task_type(task_type) -> str:
  """Return ``task_type`` when it is registered, else raise."""
  if task_type not in TASK_TYPES:
    raise UnknownTaskType(
      "unknown task type: {!r} (expected one of {})".format(
        task_type, ", ".join(TASK_TYPES)
      )
    )
  return task_type


def validate_task_state(state) -> str:
  """Return ``state`` when it is part of the task lifecycle, else raise."""
  if state not in TASK_STATES:
    raise InvalidTaskState(
      "unknown task state: {!r} (expected one of {})".format(
        state, ", ".join(TASK_STATES)
      )
    )
  return state


def validate_item_state(state) -> str:
  """Return ``state`` when it is a legal item state, else raise."""
  if state not in TASK_ITEM_STATES:
    raise InvalidTaskItemState(
      "unknown task item state: {!r} (expected one of {})".format(
        state, ", ".join(TASK_ITEM_STATES)
      )
    )
  return state


def validate_transition(current, target) -> str:
  """Return ``target`` when moving there from ``current`` is legal, else raise.

  Restating the current state raises too: a second ``finish_success`` on the same
  task means two owners think they finished it, and silently accepting that hides
  the real bug.
  """
  validate_task_state(current)
  validate_task_state(target)
  if target not in _TRANSITIONS[current]:
    raise InvalidTaskTransition(
      "a task in state {!r} cannot move to {!r}".format(current, target)
    )
  return target


def _validate_count(value, label: str, allow_none: bool = False):
  if value is None and allow_none:
    return None
  ##
  ## ``bool`` is an ``int`` in Python, and ``True`` as a progress count is always
  ## a mistake rather than the number one.
  ##
  if type(value) is not int:
    raise InvalidProgress("{} must be an integer, got {!r}".format(label, value))
  if value < 0:
    raise InvalidProgress("{} must not be negative, got {}".format(label, value))
  return value


def normalize_progress(current, total) -> dict:
  """Build the progress pair the API promises.

  ``total`` may be ``None`` - a live recording runs until it stops and has no
  final count.  Percentages are the frontend's business: storing one here would
  make ``current``/``total`` and the percentage two sources of the same truth.
  """
  return {
    "current": _validate_count(current, "progress current"),
    "total": _validate_count(total, "progress total", allow_none=True),
  }


def _isoformat(value):
  if isinstance(value, datetime):
    return value.isoformat(timespec="milliseconds")
  return value


def to_payload(snapshot: dict) -> dict:
  """Turn a store snapshot into the JSON body the API returns.

  The snapshot keeps real ``datetime`` objects so services can compare them; only
  the wire needs ISO 8601, so the conversion lives here rather than in the store.
  """
  return {
    "task_id": snapshot["task_id"],
    "task_type": snapshot["task_type"],
    "state": snapshot["state"],
    "title": snapshot["title"],
    "message": snapshot["message"],
    "created_at": _isoformat(snapshot["created_at"]),
    "started_at": _isoformat(snapshot["started_at"]),
    "finished_at": _isoformat(snapshot["finished_at"]),
    "progress": dict(snapshot["progress"]),
    "metadata": deepcopy(snapshot["metadata"]),
    "items": [
      {
        "key": item["key"],
        "state": item["state"],
        "message": item["message"],
        "metadata": deepcopy(item["metadata"]),
      }
      for item in snapshot["items"]
    ],
  }
