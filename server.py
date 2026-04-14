##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import os

## <<Third-Part>>
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()

from backend.src.platform.platform_dispatcher import PlatformDispatcher

from flask import Flask, request, jsonify, render_template


platform_dispatcher = PlatformDispatcher()
app = Flask(__name__, static_folder='./frontend/src/static', template_folder='./frontend/src/templates')

##
## handle the request from the client
##
@app.route('/', methods=['POST'])
def process_request():
  try:
    ##
    ## get request from the client
    ##
    platform_dispatcher.dispatch(request.json)
  except Exception as e:
    print(f"ERROR: {e}")
    ##
    ## response to the client
    ##
    return jsonify({"message": f"request 处理失败"}), 500

  ##
  ## response to the client
  ##
  return jsonify({"message": f"request 已开始处理"}), 200

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == '__main__':
  ##
  ## register platform_dispatcher
  ##
  platform_dispatcher.register()

  ##
  ## 启动服务
  ## 从环境变量读取配置，默认: debug=False, port=5000
  ##
  debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() in ('true', '1', 'yes')
  server_port = int(os.getenv('SERVER_PORT', 5000))
  
  app.run(debug=debug_mode, host='0.0.0.0', port=server_port)
