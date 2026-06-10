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
from backend.src.library.configlib import init_config
from backend.src.platform.platform_dispatcher import PlatformDispatcher
from backend.src.library.loglib import get_logger


def _is_truthy(value: str) -> bool:
  return str(value).lower() in ('true', '1', 'yes', 'on')

def _is_placeholder_token(value: str) -> bool:
  return value in ('replace_with_a_random_local_token', 'replace_with_a_random_deployment_token')

def _require_api_token():
  expected_token = os.getenv('SMSD_API_TOKEN', '').strip()
  if not expected_token or _is_placeholder_token(expected_token):
    return None

  supplied_token = request.headers.get('X-SMSD-Token', '').strip()
  auth_header = request.headers.get('Authorization', '').strip()
  if auth_header.startswith('Bearer '):
    supplied_token = auth_header.removeprefix('Bearer ').strip()

  if supplied_token != expected_token:
    return jsonify({
      "status": "error",
      "message": "未授权请求",
      "code": 401
    }), 401
  return None

def _allowed_domains() -> tuple:
  raw_domains = os.getenv(
    'SMSD_ALLOWED_DOMAINS',
    'douyin.com,iesdouyin.com,v.douyin.com,live.douyin.com,www.douyin.com'
  )
  return tuple(domain.strip().lower() for domain in raw_domains.split(',') if domain.strip())

def _is_allowed_domain(hostname: str) -> bool:
  hostname = (hostname or '').lower().rstrip('.')
  return any(hostname == domain or hostname.endswith('.' + domain) for domain in _allowed_domains())

def _validate_url(url: str, index: int) -> str:
  max_url_length = int(os.getenv('SMSD_MAX_URL_LENGTH', 2048))
  if not isinstance(url, str) or len(url) == 0 or len(url) > max_url_length:
    raise ValueError(f"第 {index + 1} 个 URL 长度无效")

  parsed_url = urlparse(url)
  if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
    raise ValueError(f"第 {index + 1} 个 URL 格式无效")

  if not _is_allowed_domain(parsed_url.hostname):
    raise ValueError(f"第 {index + 1} 个 URL 域名不在允许列表中")

  return url

##
## handle the request from the client
##
@app.route('/', methods=['POST'])
def process_request():
  try:
    auth_error = _require_api_token()
    if auth_error is not None:
      return auth_error

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
    max_urls = int(os.getenv('SMSD_MAX_URLS_PER_REQUEST', 20))
    if len(urls) > max_urls:
      return jsonify({
        "status": "error",
        "message": f"URL 数量超过限制: {max_urls}",
        "code": 400
      }), 400

    ##
    ## 校验 URL 格式（可选，根据业务需求调整）
    ##
    for idx, url in enumerate(urls):
      urls[idx] = _validate_url(url, idx)

    score = json_data.get('score')
    if score is not None:
      try:
        score = int(score)
      except (TypeError, ValueError):
        raise ValueError("score 必须是 0-100 的整数")
      if score < 0 or score > 100:
        raise ValueError("score 必须是 0-100 的整数")
      json_data['score'] = score

    favorite = json_data.get('favorite')
    if favorite is not None and not isinstance(favorite, bool):
      raise ValueError("favorite 必须是布尔值")

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
    debug_mode = _is_truthy(os.getenv('FLASK_DEBUG', 'false'))
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
  ## 加载 .env 文件（如果存在）
  ##
  load_dotenv()
  
  ##
  ## 初始化配置
  ##
  try:
    init_config()
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
  ## 从环境变量读取配置，默认: debug=False, port=5000
  ##
  debug_mode = _is_truthy(os.getenv('FLASK_DEBUG', 'false'))
  server_host = os.getenv('SERVER_HOST', '0.0.0.0')
  server_port = int(os.getenv('SERVER_PORT', 5000))
  
  app.run(debug=debug_mode, host=server_host, port=server_port)
