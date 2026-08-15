##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import os
import signal
import traceback
import logging
import threading

## <<Extension>>
from flask import Flask, request, jsonify, render_template
from werkzeug.exceptions import BadRequest

## <<Third-Part>>
from backend.src.library.loglib    import get_logger
from backend.src.library.configlib import load_config
from backend.src.base.log import LoggerManager
from backend.src.database.schema_guard import initialize_schema_guard
from backend.src.platform.douyin.douyin_aweme_downloader import shutdown_aweme_downloads
from backend.src.platform.douyin.douyin_live_downloader import cancel_live_downloads
from backend.src.platform.platform_dispatcher import PlatformDispatcher
from backend.src.service.direct_post_download_task import DirectPostDownloadTaskService
from backend.src.service.live_recording_task import LiveRecordingTaskService
from backend.src.service.task_creation import TaskCreationService
from backend.src.web.history_routes import build_history_blueprint
from backend.src.web.owner_routes import (
  OWNER_RUNTIME_KEY,
  OwnerRuntime,
  build_owner_blueprint,
)
from backend.src.web.person_routes import build_person_blueprint
from backend.src.web.resolve_routes import (
  build_resolve_blueprint,
  install_resolve_service,
)
from backend.src.web.task_routes import (
  build_task_blueprint,
  install_task_creation_service,
  install_task_service,
)

def _server_options(config: dict) -> dict:
  server = config.get("server")
  if not isinstance(server, dict):
    raise ValueError("$.server must be a mapping")
  host = server.get("host")
  port = server.get("port")
  debug_mode = server.get("debug_mode")
  if not isinstance(host, str) or not host.strip():
    raise ValueError("$.server.host must be a non-empty string")
  if type(port) is not int or not 1 <= port <= 65535:
    raise ValueError("$.server.port must be an integer from 1 to 65535")
  if type(debug_mode) is not bool:
    raise ValueError("$.server.debug_mode must be a boolean")
  return {"host": host, "port": port, "debug": debug_mode}


def _new_flask_app(
  dispatcher=None,
  request_logger=None,
  lazy_config=False,
  schema_guard_factory=initialize_schema_guard,
  initial_schema_guard=None,
):
  configured_app = Flask(
    __name__,
    static_folder="./frontend/src/static",
    template_folder="./frontend/src/templates",
  )
  runtime = {
    "dispatcher": dispatcher,
    "logger": request_logger or logging.getLogger("bootstrap"),
    "initialized": not lazy_config,
  }
  if initial_schema_guard is not None:
    configured_app.extensions["smsd_schema_guard"] = initial_schema_guard
  initialization_lock = threading.Lock()

  def initialize_runtime():
    if runtime["initialized"]:
      return
    with initialization_lock:
      if runtime["initialized"]:
        return
      source = load_config()
      options = _server_options(source)
      LoggerManager(source["log"])
      schema_guard = schema_guard_factory(source)
      configured_dispatcher = PlatformDispatcher()
      configured_dispatcher.register()
      runtime["dispatcher"] = configured_dispatcher
      runtime["logger"] = get_logger()
      configured_app.debug = options["debug"]
      configured_app.extensions["smsd_schema_guard"] = schema_guard
      runtime["initialized"] = True

  @configured_app.before_request
  def ensure_runtime_initialized():
    initialize_runtime()

  ##
  ## handle the request from the client
  ##
  @configured_app.route('/', methods=['POST'])
  def process_request():
    try:
      ##
      ## 校验请求数据
      ##
      if not request.is_json:
        return jsonify({
          "status": "error",
          "message": "请求必须是 JSON 格式",
          "code": 400
        }), 400

      json_data = request.get_json(silent=True)
      if json_data is None:
        return jsonify({
          "status": "error",
          "message": "请求体为空或格式错误",
          "code": 400
        }), 400

      ##
      ## 校验必需字段
      ##
      urls = json_data.get('urls')
      if not urls or not isinstance(urls, list) or len(urls) == 0:
        return jsonify({
          "status": "error",
          "message": "缺少必需字段: urls（必须是非空数组）",
          "code": 400
        }), 400

      ##
      ## 校验 URL 格式（可选，根据业务需求调整）
      ##
      for idx, url in enumerate(urls):
        if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
          return jsonify({
            "status": "error",
            "message": f"第 {idx + 1} 个 URL 格式无效",
            "code": 400
          }), 400

      ##
      ## 处理请求
      ##
      ##
      ## The reply below is deliberately unchanged, and deliberately carries no
      ## task id.  Whether these links are posts or live rooms is not known yet -
      ## the share links have not been followed - so any id invented here would
      ## either be a guess or force this thread to wait on the network.  The
      ## tasks appear in the task centre as soon as the handler confirms what
      ## each link is.
      ##
      runtime["dispatcher"].dispatch(
        json_data,
        context={
          "direct_post_service": runtime.get("direct_post_service"),
          "live_record_service": runtime.get("live_record_service"),
        },
      )

    except BadRequest as e:
      ##
      ## 客户端请求格式错误（Flask 自动抛出）
      ##
      runtime["logger"].warning(f"无效的请求格式: {str(e)}")
      return jsonify({
        "status": "error",
        "message": "请求格式无效",
        "code": 400
      }), 400

    except ValueError as e:
      ##
      ## 业务逻辑校验错误
      ##
      runtime["logger"].warning(f"参数校验失败: {str(e)}")
      return jsonify({
        "status": "error",
        "message": f"参数错误: {str(e)}",
        "code": 400
      }), 400

    except Exception as e:
      ##
      ## 服务器内部错误
      ##
      error_traceback = traceback.format_exc()
      runtime["logger"].error(f"请求处理失败 - 异常: {str(e)}\n{error_traceback}")

      ##
      ## 生产环境返回通用错误，开发环境返回详细错误
      ##
      if configured_app.debug:
        return jsonify({
          "status": "error",
          "message": f"服务器内部错误: {str(e)}",
          "traceback": error_traceback.split('\n'),
          "code": 500
        }), 500
      else:
        return jsonify({
          "status": "error",
          "message": "服务器内部错误，请稍后重试",
          "code": 500
        }), 500

    ##
    ## 响应成功
    ##
    return jsonify({
      "status": "success",
      "message": "请求已开始处理",
      "code": 200
    }), 200

  @configured_app.route('/', methods=['GET'])
  def index():
      return render_template('index.html')

  ##
  ## the unified background task record.  Installed on the app rather than kept
  ## as a module global so every request of this process reads the one store,
  ## and two apps in one interpreter - the lazy wsgi app and a test's app - do
  ## not report each other's tasks.
  ##
  ## Installed before the blueprints that report into it, so the dependency
  ## travels down into the services rather than being reached up for.
  ##
  task_service = install_task_service(configured_app)

  ##
  ## The runner that turns a pasted post link into a task of this application.
  ##
  ## Held here, on the per-application runtime, and handed to the dispatcher one
  ## dispatch at a time.  The dispatcher is a process-wide singleton, so storing
  ## it there instead would let a second application overwrite the first one's
  ## task store and each would report the other's downloads.
  ##
  runtime["direct_post_service"] = DirectPostDownloadTaskService(
    task_service=task_service
  )
  runtime["live_record_service"] = LiveRecordingTaskService(
    task_service=task_service
  )

  ##
  ## download history browsing and live status probing
  ##
  configured_app.register_blueprint(
    build_history_blueprint(task_service=task_service)
  )

  ##
  ## owner profile browsing and post batch download
  ##
  ## Built here rather than inside the blueprint so the unified task api can be
  ## given the *same* runtime.  It owns the job store, the payload cache and the
  ## post locks; a second one would let the same post be walked by one and
  ## downloaded by the other, each unaware of the other's locks.
  ##
  owner_runtime = OwnerRuntime(task_service=task_service)
  configured_app.extensions[OWNER_RUNTIME_KEY] = owner_runtime
  configured_app.register_blueprint(build_owner_blueprint(runtime=owner_runtime))

  ##
  ## marking which accounts belong to the same person, and who works with whom
  ##
  configured_app.register_blueprint(build_person_blueprint())

  ##
  ## the read side of the task centre
  ##
  configured_app.register_blueprint(build_task_blueprint())

  ##
  ## Answering what a pasted link is, before anything is done about it.
  ##
  ## Installed on the application rather than kept as a module global for the
  ## same reason the task service is: a receipt is this server's own word that
  ## it resolved a resource, so two applications in one interpreter must not be
  ## able to redeem each other's.  Whatever creates tasks from a receipt reads
  ## this same instance rather than trusting the browser to hand the identity
  ## back.
  ##
  resolve_service = install_resolve_service(configured_app)
  configured_app.register_blueprint(build_resolve_blueprint())

  ##
  ## Turning a resolution into real work.
  ##
  ## Every collaborator is one already built above, never a fresh copy.  A
  ## creation service holding its own resolve store would answer "expired" to
  ## every receipt this application ever issued, and one holding its own task
  ## service would create tasks that ``GET /api/tasks`` could not see.
  ##
  ## The owner side arrives as a factory rather than an instance because the
  ## runtime builds its service lazily - a server that never downloads an owner
  ## never constructs a platform client.
  ##
  install_task_creation_service(
    configured_app,
    TaskCreationService(
      resolve_service=resolve_service,
      direct_post_service=runtime["direct_post_service"],
      live_record_service=runtime["live_record_service"],
      owner_service_factory=owner_runtime.service,
    ),
  )

  return configured_app


app = _new_flask_app(lazy_config=True)


def create_app(
  config: dict = None,
  dispatcher=None,
  schema_guard_factory=initialize_schema_guard,
):
  source = load_config() if config is None else config
  options = _server_options(source)
  LoggerManager(source["log"])
  schema_guard = schema_guard_factory(source)
  configured_dispatcher = (
    dispatcher if dispatcher is not None else PlatformDispatcher()
  )
  configured_dispatcher.register()
  configured_app = _new_flask_app(
    configured_dispatcher,
    get_logger(),
    initial_schema_guard=schema_guard,
  )
  configured_app.debug = options["debug"]
  return configured_app


def run_server(config: dict = None):
  source = load_config() if config is None else config
  options = _server_options(source)
  configured_app = create_app(source)
  cancellation_requested = False
  previous_handlers = {}
  installed_signals = []

  def cancel_once():
    nonlocal cancellation_requested
    if cancellation_requested:
      return
    cancellation_requested = True
    try:
      cancel_live_downloads()
    except BaseException:
      try:
        get_logger().error("live download cancellation failed during shutdown")
      except BaseException:
        pass
    ##
    ## Post downloads run on their own pool, so stopping recordings does not stop
    ## them.  Queued posts are dropped; a file mid-transfer is discarded rather
    ## than left truncated on disk.
    ##
    try:
      shutdown_aweme_downloads()
    except BaseException:
      try:
        get_logger().error("post download shutdown failed during shutdown")
      except BaseException:
        pass

  def handle_shutdown(signum, _frame):
    cancel_once()
    raise SystemExit(128 + signum)

  try:
    for signum in (signal.SIGINT, signal.SIGTERM):
      previous_handlers[signum] = signal.signal(signum, handle_shutdown)
      installed_signals.append(signum)
    configured_app.run(**options)
  finally:
    try:
      cancel_once()
    finally:
      for signum in reversed(installed_signals):
        signal.signal(signum, previous_handlers[signum])

if __name__ == '__main__':
  run_server()
