##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import os
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
from backend.src.platform.platform_dispatcher import PlatformDispatcher

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


def _new_flask_app(dispatcher=None, request_logger=None, lazy_config=False):
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
      configured_dispatcher = PlatformDispatcher()
      configured_dispatcher.register()
      runtime["dispatcher"] = configured_dispatcher
      runtime["logger"] = get_logger()
      configured_app.debug = options["debug"]
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
      runtime["dispatcher"].dispatch(json_data)

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

  return configured_app


app = _new_flask_app(lazy_config=True)


def create_app(config: dict = None, dispatcher=None):
  source = load_config() if config is None else config
  options = _server_options(source)
  LoggerManager(source["log"])
  configured_dispatcher = (
    dispatcher if dispatcher is not None else PlatformDispatcher()
  )
  configured_dispatcher.register()
  configured_app = _new_flask_app(configured_dispatcher, get_logger())
  configured_app.debug = options["debug"]
  return configured_app


def run_server(config: dict = None):
  source = load_config() if config is None else config
  options = _server_options(source)
  configured_app = create_app(source)
  configured_app.run(**options)

if __name__ == '__main__':
  run_server()
