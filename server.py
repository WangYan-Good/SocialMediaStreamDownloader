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
## process all links those are posted to the server
## TODO response to the client
##
@app.route('/', methods=['POST'])
def process_urls():
  urls = request.json.get('urls')
  print(f"接收到的数据: {urls}")
  if urls is None or len(urls) == 0:
    return jsonify({"error": "No valid URLs found in input"}), 400
  
  ##
  ## handle all urls
  ##
  try:
    ##
    ## trigger dispatch event
    ##
    platform_dispatcher.dispatch(urls)
  except Exception as e:
    print("处理出错: {}".format(e))

  ##
  ## response to the client
  ##
  return jsonify({"message": f"共接收 {len(urls)} 条链接，已开始处理"}), 200

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
  app.run(debug=True, host='192.168.1.9', port=5001)