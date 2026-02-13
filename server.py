##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import re
## <<Third-Part>>
from backend.src.platform.platform_dispatcher import PlatformDispatcher
from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


platform_dispatcher = PlatformDispatcher()
app = Flask(__name__, static_folder='./frontend/src/static', template_folder='./frontend/src/templates')

# Initialize rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]  # Default global rate limit
)

##
## validate URL format
##
def is_valid_url(url):
    # Basic URL validation regex
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url) is not None

##
## handle the request from the client
##
@app.route('/', methods=['POST'])
@limiter.limit("10 per minute")  # Limit to 10 requests per minute per IP for POST endpoint
def process_request():
    try:
        # Validate request data
        json_data = request.json
        
        if not json_data:
            return jsonify({"message": "Invalid JSON data"}), 400
            
        # Validate required fields
        if 'urls' not in json_data or not isinstance(json_data['urls'], list) or len(json_data['urls']) == 0:
            return jsonify({"message": "Missing or invalid 'urls' field in request"}), 400
            
        # Validate URLs
        for url in json_data['urls']:
            if not isinstance(url, str):
                return jsonify({"message": f"Invalid URL format: {url}"}), 400
            if not is_valid_url(url):
                return jsonify({"message": f"Invalid URL format: {url}"}), 400
                
        ##
        ## get request from the client
        ##
        platform_dispatcher.dispatch(json_data)
        
    except ValueError as ve:
        print(f"ValueError: {ve}")
        return jsonify({"message": f"Invalid request data: {str(ve)}"}), 400
    except Exception as e:
        print(f"ERROR: {e}")
        ##
        ## response to the client
        ##
        return jsonify({"message": f"Request processing failed: {str(e)}"}), 500

  ##
  ## response to the client
  ##
  return jsonify({"message": f"Request started processing"}), 200

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.teardown_appcontext
def shutdown_dispatchers(exception=None):
    """Clean up resources when the application shuts down"""
    try:
        platform_dispatcher.shutdown()
    except Exception as e:
        print(f"Error during shutdown: {e}")

if __name__ == '__main__':
  ##
  ## register platform_dispatcher
  ##
  platform_dispatcher.register()

  ##
  ## 启动服务
  ##
  try:
    app.run(debug=True, host='0.0.0.0', port=5000)
  finally:
    # Ensure cleanup happens when the script exits
    platform_dispatcher.shutdown()
