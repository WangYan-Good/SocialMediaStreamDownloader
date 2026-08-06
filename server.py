##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import os
import traceback
import logging
from dotenv import load_dotenv

## <<Extension>>
from flask import Flask, request, jsonify, render_template
from werkzeug.exceptions import BadRequest

## <<Third-Part>>
from backend.src.library.loglib    import get_logger
from backend.src.library.configlib import load_config
from backend.src.platform.platform_dispatcher import PlatformDispatcher

##
## handle the request from the client
##
@app.route('/', methods=['POST'])
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
    platform_dispatcher.dispatch(json_data)

  except BadRequest as e:
    ##
    ## 客户端请求格式错误（Flask 自动抛出）
    ##
    logger.warning(f"无效的请求格式: {str(e)}")
    return jsonify({
      "status": "error",
      "message": "请求格式无效",
      "code": 400
    }), 400

  except ValueError as e:
    ##
    ## 业务逻辑校验错误
    ##
    logger.warning(f"参数校验失败: {str(e)}")
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
    logger.error(f"请求处理失败 - 异常: {str(e)}\n{error_traceback}")

    ##
    ## 生产环境返回通用错误，开发环境返回详细错误
    ##
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() in ('true', '1', 'yes')
    if debug_mode:
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

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == '__main__': 
  ##
  ## 加载配置
  ##
  try:
    load_config()
  except Exception as e:
    raise RuntimeError(f"配置初始化失败: {str(e)}")

  ##
  ## 创建平台分发器实例和 Flask 应用实例
  ##
  platform_dispatcher = PlatformDispatcher()
  app = Flask(__name__, static_folder='./frontend/src/static', template_folder='./frontend/src/templates')

  ##
  ## 配置日志记录器
  ##
  logger = get_logger() if callable(get_logger) else logging.getLogger(__name__)

  ##
  ## register platform_dispatcher
  ##
  platform_dispatcher.register()

  ##
  ## 启动服务
  ## 从环境变量读取配置，默认: debug=False, host=0.0.0.0, port=5000
  ##
  debug_mode  = os.getenv('FLASK_DEBUG', 'false').lower() in ('true', '1', 'yes')
  server_host = os.getenv('SERVER_HOST', '0.0.0.0')
  server_port = int(os.getenv('SERVER_PORT', 5000))
  
  app.run(debug=debug_mode, host=server_host, port=server_port)
