##<<Extension>>
from flask import Blueprint, current_app, jsonify, request

##<<Third-part>>
from backend.src.library.loglib import get_logger
from backend.src.task.errors import TaskValidationError
from backend.src.task.model import to_payload
from backend.src.task.service import TaskService


##
## Where the one TaskService lives for the life of the process.  Namespaced like
## ``smsd_schema_guard`` so every extension this app owns reads the same way.
##
TASK_SERVICE_KEY = "smsd_task_service"


def _error(message: str, code: int):
  return jsonify({"status": "error", "message": message, "code": code}), code


def _success(data: dict):
  return jsonify({"status": "success", "code": 200, "data": data}), 200


def install_task_service(app, service: TaskService = None) -> TaskService:
  """Attach one TaskService to ``app`` and return it.

  Built once per application rather than per request: the store is the process's
  memory of what is running, and a service rebuilt per request would report an
  empty task list to the browser polling the download it just started.
  """
  service = service if service is not None else TaskService()
  app.extensions[TASK_SERVICE_KEY] = service
  return service


def task_service() -> TaskService:
  """The TaskService of the application handling this request."""
  return current_app.extensions.get(TASK_SERVICE_KEY)


def _optional_filter(name: str):
  ##
  ## A UI that always sends its filter fields sends empty ones when nothing is
  ## selected; that means "no filter", not "match the empty string".
  ##
  value = (request.args.get(name) or "").strip()
  return value or None


def _optional_limit():
  raw = (request.args.get("limit") or "").strip()
  if not raw:
    return None
  try:
    limit = int(raw)
  except ValueError:
    raise TaskValidationError("limit must be an integer")
  if limit < 1:
    raise TaskValidationError("limit must be at least 1")
  return limit


def build_task_blueprint() -> Blueprint:
  """The read side of the unified task centre.

  Creating tasks is deliberately absent: a task is only worth showing once some
  business actually runs it, so ``POST /api/tasks`` arrives with the first
  migration rather than as an endpoint that starts nothing.
  """
  blueprint = Blueprint("task", __name__, url_prefix="/api")

  @blueprint.route("/tasks", methods=["GET"])
  def list_tasks():
    service = task_service()
    if service is None:
      return _error("任务服务未初始化", 503)

    try:
      limit = _optional_limit()
      ##
      ## Listed without the limit so ``total`` can answer "how many are there",
      ## not "how many did you ask for" - the difference is what lets the page
      ## say it is showing part of a longer list.
      ##
      tasks = service.list_tasks(
        state=_optional_filter("state"),
        task_type=_optional_filter("type"),
      )
    except TaskValidationError as e:
      return _error(str(e), 400)
    except Exception as e:
      get_logger().error("task listing failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    selected = tasks if limit is None else tasks[:limit]
    return _success(
      {
        "items": [to_payload(task) for task in selected],
        "total": len(tasks),
      }
    )

  @blueprint.route("/tasks/<task_id>", methods=["GET"])
  def read_task(task_id):
    service = task_service()
    if service is None:
      return _error("任务服务未初始化", 503)

    try:
      task = service.get_task(task_id)
    except Exception as e:
      get_logger().error("task lookup failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    if task is None:
      return _error("任务不存在或已过期", 404)

    return _success(to_payload(task))

  return blueprint
