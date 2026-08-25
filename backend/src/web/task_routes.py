##<<Extension>>
from flask import Blueprint, current_app, jsonify, request

##<<Third-part>>
from backend.src.auth.roles import ROLE_ADMIN
from backend.src.library.loglib import get_logger
from backend.src.service.task_creation import TaskCreateError
from backend.src.task.errors import TaskValidationError
from backend.src.task.model import (
  TASK_STATE_CANCELLED,
  TASK_STATE_FAILED,
  TASK_STATE_PARTIAL,
  TASK_STATE_PENDING,
  TASK_STATE_RUNNING,
  TASK_STATE_SUCCESS,
  to_payload,
)
from backend.src.task.service import TaskService
from backend.src.web.auth_routes import (
  require_authenticated,
  require_authenticated_csrf,
  request_auth_context,
)


##
## Where the one TaskService lives for the life of the process.  Namespaced like
## ``smsd_schema_guard`` so every extension this app owns reads the same way.
##
TASK_SERVICE_KEY = "smsd_task_service"

##
## And where the one thing allowed to *start* work lives.  Separate from the
## service above because reading tasks and creating them are different
## authorities: the read side works with nothing wired behind it, the write side
## must refuse rather than pretend.
##
TASK_CREATION_SERVICE_KEY = "smsd_task_creation_service"

##
## The whole of what a creation request may say.  Anything else is refused
## rather than ignored: a client sending ``aweme_id`` is describing the resource,
## which is exactly the thing this endpoint declines to take its word for, and
## silently dropping the field would leave the caller believing it was used.
##
_CREATE_FIELDS = ("resolve_id", "task_type", "options")

_USER_RESULT_COUNT_FIELDS = ("saved_count", "media_count", "recording_id")
_USER_RESULT_FLAG_FIELDS = ("skipped", "partial", "recorded")

_USER_TASK_MESSAGES = {
  TASK_STATE_PENDING: "等待处理",
  TASK_STATE_RUNNING: "正在处理",
  TASK_STATE_SUCCESS: "任务已完成",
  TASK_STATE_PARTIAL: "任务部分完成",
  TASK_STATE_FAILED: "任务未完成",
  TASK_STATE_CANCELLED: "任务已取消",
}


def _error(message: str, code: int):
  return jsonify({"status": "error", "message": message, "code": code}), code


def _success(data: dict):
  return jsonify({"status": "success", "code": 200, "data": data}), 200


def _accepted(data: dict):
  ##
  ## 202, not 200: the request has been taken on, and what it started is
  ## observable through the read side rather than finished by the time this
  ## answers.
  ##
  return jsonify({"status": "success", "code": 202, "data": data}), 202


def _safe_user_result(metadata: dict) -> dict:
  source = metadata.get("result")
  if not isinstance(source, dict):
    return {}
  result = {}
  for key in _USER_RESULT_COUNT_FIELDS:
    value = source.get(key)
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
      result[key] = value
  for key in _USER_RESULT_FLAG_FIELDS:
    value = source.get(key)
    if isinstance(value, bool):
      result[key] = value
  return result


def _to_user_payload(snapshot: dict) -> dict:
  """Explicit user wire: useful status, never execution internals."""
  full = to_payload(snapshot)
  metadata = snapshot.get("metadata") or {}
  safe_metadata = {}
  source_url = metadata.get("source_url")
  if isinstance(source_url, str) and source_url.strip():
    safe_metadata["source_url"] = source_url.strip()
  result = _safe_user_result(metadata)
  if result:
    safe_metadata["result"] = result

  # Runner messages and result reasons are operational text, even when they
  # contain Chinese prose: either may interpolate a path, URL, driver error or
  # credential.  The user wire therefore derives its wording from the closed
  # lifecycle vocabulary rather than attempting to classify arbitrary text.
  full["message"] = _USER_TASK_MESSAGES.get(snapshot.get("state"))
  full["metadata"] = safe_metadata
  full["items"] = [
    {
      "key": "item-{}".format(index),
      "state": item["state"],
      "message": None,
      "metadata": {},
    }
    for index, item in enumerate(snapshot.get("items") or (), start=1)
  ]
  return full


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


def install_task_creation_service(app, service=None):
  """Attach the one thing allowed to start work to ``app`` and return it.

  Per application for the same reason everything else here is: a receipt issued
  by one application must not be redeemable in another, and the tasks it creates
  belong to that application's store.
  """
  app.extensions[TASK_CREATION_SERVICE_KEY] = service
  return service


def task_creation_service():
  """The TaskCreationService of the application handling this request."""
  return current_app.extensions.get(TASK_CREATION_SERVICE_KEY)


def _required_text(payload: dict, field: str):
  value = payload.get(field)
  if not isinstance(value, str) or not value.strip():
    raise TaskValidationError("缺少必需字段: {}".format(field))
  return value.strip()


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
  """The unified task centre: what is running, and how to start something.

  Both verbs live on one resource rather than in two blueprints sharing a url.
  Creating arrived only once there was a trustworthy way to say *what* to run:
  a request names a server-side resolution by its receipt and the work it wants
  done, and never describes the resource itself.
  """
  blueprint = Blueprint("task", __name__, url_prefix="/api")

  @blueprint.route("/tasks", methods=["POST"])
  @require_authenticated_csrf
  def create_task():
    auth_context = request_auth_context()
    app_user_id = auth_context.user.user_id
    service = task_creation_service()
    if service is None:
      return _error("任务创建服务未初始化", 503)

    if not request.is_json:
      return _error("请求必须是 JSON 格式", 400)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
      return _error("请求体为空或格式错误", 400)

    unknown = sorted(set(payload) - set(_CREATE_FIELDS))
    if unknown:
      ##
      ## Named in the message, because the fields a client is most likely to
      ## send here are the ones it wants the server to trust - an aweme id, a
      ## url - and "unknown field" alone would read as pedantry rather than as
      ## the refusal it is.
      ##
      return _error("不支持的字段: {}".format(", ".join(unknown)), 400)

    try:
      resolve_id = _required_text(payload, "resolve_id")
      task_type = _required_text(payload, "task_type")
    except TaskValidationError as e:
      return _error(str(e), 400)

    options = payload.get("options")
    if options is not None and not isinstance(options, dict):
      return _error("options 必须是对象", 400)

    try:
      result = service.create(
        resolve_id,
        task_type,
        options,
        app_user_id=app_user_id,
      )
    except TaskCreateError as e:
      ##
      ## The category, never the request.  A refusal has to be diagnosable from
      ## the log without the log holding what a client sent.
      ##
      get_logger().info("task creation refused: {}".format(e.kind))
      return _error(str(e), e.status_code)
    except Exception as e:
      get_logger().error(
        "task creation failed: {}: {}".format(type(e).__name__, e)
      )
      return _error("服务器内部错误，请稍后重试", 500)

    get_logger().info(
      "created a {} task from a resolution".format(result.task_type)
    )
    return _accepted(
      {
        "task_id": result.task_id,
        "task_type": result.task_type,
        "resolve_id": result.resolve_id,
      }
    )

  @blueprint.route("/tasks", methods=["GET"])
  @require_authenticated
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
      context = request_auth_context()
      filters = {
        "state": _optional_filter("state"),
        "task_type": _optional_filter("type"),
      }
      if context.user.role == ROLE_ADMIN:
        tasks = service.list_tasks(**filters)
      else:
        tasks = service.list_tasks_for_user(context.user.user_id, **filters)
    except TaskValidationError as e:
      return _error(str(e), 400)
    except Exception as e:
      get_logger().error("task listing failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    selected = tasks if limit is None else tasks[:limit]
    return _success(
      {
        "items": [
          to_payload(task) if context.user.role == ROLE_ADMIN
          else _to_user_payload(task)
          for task in selected
        ],
        "total": len(tasks),
      }
    )

  @blueprint.route("/tasks/<task_id>", methods=["GET"])
  @require_authenticated
  def read_task(task_id):
    service = task_service()
    if service is None:
      return _error("任务服务未初始化", 503)

    try:
      context = request_auth_context()
      task = (
        service.get_task(task_id)
        if context.user.role == ROLE_ADMIN
        else service.get_task_for_user(task_id, context.user.user_id)
      )
    except Exception as e:
      get_logger().error("task lookup failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    if task is None:
      return _error("任务不存在或已过期", 404)

    return _success(
      to_payload(task)
      if context.user.role == ROLE_ADMIN
      else _to_user_payload(task)
    )

  return blueprint
