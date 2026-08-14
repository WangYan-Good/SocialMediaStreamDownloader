##<<Extension>>
from flask import Blueprint, current_app, jsonify, request

##<<Third-part>>
from backend.src.library.loglib import get_logger
from backend.src.platform.resource_resolution import ResourceResolveError
from backend.src.service.resource_resolve import ResourceResolveService


##
## Where the one ResourceResolveService lives for the life of the application.
## Namespaced like ``smsd_task_service`` so every extension this app owns reads
## the same way.
##
RESOLVE_SERVICE_KEY = "smsd_resolve_service"


def _error(message: str, code: int):
  return jsonify({"status": "error", "message": message, "code": code}), code


def _success(data: dict):
  return jsonify({"status": "success", "code": 200, "data": data}), 200


def install_resolve_service(app, service: ResourceResolveService = None):
  """Attach one ResourceResolveService to ``app`` and return it.

  Per application rather than per module, for the same reason the task service
  is: a receipt handed out by one application must mean nothing to another in
  the same interpreter - the lazy wsgi app and a test's app must not be able to
  redeem each other's resolutions.
  """
  service = service if service is not None else ResourceResolveService()
  app.extensions[RESOLVE_SERVICE_KEY] = service
  return service


def resolve_service() -> ResourceResolveService:
  """The ResourceResolveService of the application handling this request."""
  return current_app.extensions.get(RESOLVE_SERVICE_KEY)


def _serialize(record, expires_in_seconds: int) -> dict:
  resolution = record.resolution
  return {
    "resolve_id": record.resolve_id,
    "platform": resolution.platform,
    "resource_type": resolution.resource_type,
    "source_url": resolution.source_url,
    "resolved_url": resolution.resolved_url,
    ##
    ## Copied so the response cannot be a live handle on anything held server
    ## side, and plain so the json encoder has nothing to guess about.
    ##
    "identity": dict(resolution.identity),
    "expires_in_seconds": expires_in_seconds,
  }


def build_resolve_blueprint(service: ResourceResolveService = None) -> Blueprint:
  """The endpoint that answers what a pasted link is.

  Answering only.  Nothing here starts a download, a recording or a probe, and
  no task is created: what to *do* with a resolved resource is a decision the
  user has not made yet, and making it here would mean a mistyped link produced
  a task nobody asked for.

  The route does http and nothing else - reading the body, mapping a refusal to
  a status, serialising an answer.  Extracting the link, following it, deciding
  what it points at and remembering the result all belong to the service, where
  they can be tested without a request context.
  """
  blueprint = Blueprint("resolve", __name__, url_prefix="/api")

  @blueprint.route("/resolve", methods=["POST"])
  def resolve_resource():
    active = service if service is not None else resolve_service()
    if active is None:
      return _error("解析服务未初始化", 503)

    if not request.is_json:
      return _error("请求必须是 JSON 格式", 400)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
      return _error("请求体为空或格式错误", 400)

    try:
      record = active.resolve(payload.get("input"))
    except ResourceResolveError as e:
      ##
      ## The category, never the input.  A resolve failure has to be
      ## diagnosable from the log without the log holding what someone pasted -
      ## a share url can carry a signature, and the surrounding text can carry
      ## anything at all.
      ##
      get_logger().info("resolve refused: {}".format(e.kind))
      return _error(str(e), e.status_code)
    except Exception as e:
      ##
      ## Logged in full here, answered generically there: the message of an
      ## unexpected failure carries paths and internals that belong in the log
      ## and not in a browser.
      ##
      get_logger().error("resolve failed: {}: {}".format(type(e).__name__, e))
      return _error("服务器内部错误，请稍后重试", 500)

    get_logger().info(
      "resolved a {} link".format(record.resolution.resource_type)
    )
    return _success(_serialize(record, int(active.retention_seconds)))

  return blueprint
