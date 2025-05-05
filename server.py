##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>

## <<Third-Part>>
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
  ##
  app.run(debug=True, host='localhost', port=5000)
