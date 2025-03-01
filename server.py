##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from urllib.parse import urlparse

## <<Third-Part>>
from backend.src.platform.platform_dispatcher import PlatformDispatcher

from flask import Flask, request, jsonify, render_template, g
import re


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
  for url in urls:
    try:
      ##
      ## trigger dispatch event
      ##
      platform_dispatcher.dispatch(url)
    except Exception as e:
      print(f"处理链接 {url} 时出错: {e}")

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
  app.run(debug=True, host='192.168.1.9', port=5000)