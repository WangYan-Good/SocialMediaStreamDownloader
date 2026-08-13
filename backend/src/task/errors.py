"""Failures the task layer raises.

Separate types so callers can tell "you asked for something that does not exist"
from "you asked for something that is not allowed" without reading messages.
"""


class TaskError(Exception):
  """Base for everything the task layer refuses to do."""


class TaskNotFound(TaskError):
  """Raised when a task id is unknown, or has already been evicted."""


class TaskValidationError(TaskError, ValueError):
  """Raised when the caller's input cannot describe a task.

  Also a ``ValueError`` so the existing route handlers, which already translate
  ``ValueError`` into 400, keep working when they start creating tasks.
  """


class UnknownTaskType(TaskValidationError):
  """Raised when a task type is not one of the registered types."""


class InvalidTaskState(TaskValidationError):
  """Raised when a string is used as a task state but is not one."""


class InvalidTaskItemState(TaskValidationError):
  """Raised when a string is used as an item state but is not one."""


class InvalidProgress(TaskValidationError):
  """Raised when progress numbers cannot describe a position in a total."""


class TaskAlreadyFinished(TaskError):
  """Raised when a finished task is asked to change something it still owns.

  A task's final message is the reason it ended, and a worker still draining its
  own log lines must not be able to overwrite that with "downloading 18 / 42".
  """


class InvalidTaskTransition(TaskError):
  """Raised when a state change is not on the lifecycle's transition table.

  Not a ``ValueError``: the input was well formed, the task simply is not in a
  state where that change means anything.
  """
