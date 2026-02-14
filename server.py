##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import re
import threading
## <<Third-Part>>
from backend.src.platform.platform_dispatcher import PlatformDispatcher
from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from backend.src.base.config import BaseConfig


platform_dispatcher = PlatformDispatcher()
app = Flask(__name__, static_folder='./frontend/src/static', template_folder='./frontend/src/templates')

# Initialize rate limiter
limiter = Limiter(
    app,
    default_limits=["100 per hour"],  # Default global rate limit
    storage_uri="memory://",
    strategy="fixed-window"
)

# Global counter for active downloads
active_downloads = 0
download_lock = threading.Lock()

# Load max download count from config using max_thread setting
base_config = BaseConfig()
MAX_DOWNLOAD_COUNT = getattr(base_config, 'max_thread', 5)
if MAX_DOWNLOAD_COUNT == 0:
    MAX_DOWNLOAD_COUNT = float('inf')  # No limit when max_thread is 0

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
## get current active download count
##
def get_active_download_count():
    global active_downloads
    with download_lock:
        return active_downloads

##
## increment active download count
##
def increment_download_count():
    global active_downloads
    with download_lock:
        active_downloads += 1
        return active_downloads

##
## decrement active download count
##
def decrement_download_count():
    global active_downloads
    with download_lock:
        if active_downloads > 0:
            active_downloads -= 1
        return active_downloads

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

        # Check if download limit is exceeded (only if there is a limit)
        current_count = get_active_download_count()
        if MAX_DOWNLOAD_COUNT != float('inf') and current_count >= MAX_DOWNLOAD_COUNT:
            return jsonify({
                "message": f"Download limit exceeded. Maximum {int(MAX_DOWNLOAD_COUNT)} downloads allowed. Current: {current_count}"
            }), 429  # Too Many Requests

        # Validate URLs
        for url in json_data['urls']:
            if not isinstance(url, str):
                return jsonify({"message": f"Invalid URL format: {url}"}), 400
            if not is_valid_url(url):
                return jsonify({"message": f"Invalid URL format: {url}"}), 400

        ##
        ## get request from the client
        ##
        # Increment download counter before dispatching
        increment_download_count()
        
        # Pass a callback to decrement counter when download completes
        platform_dispatcher.dispatch(json_data, lambda: decrement_download_count())

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
    return jsonify({"message": f"Request started processing", "current_downloads": get_active_download_count()}), 200

##
## get current download count
##
@app.route('/api/download-status', methods=['GET'])
def get_download_status():
    current_count = get_active_download_count()
    # Handle infinite limit case
    if MAX_DOWNLOAD_COUNT == float('inf'):
        max_downloads_display = 0  # Represent unlimited as 0
        available_slots = 0  # Unlimited slots
    else:
        max_downloads_display = int(MAX_DOWNLOAD_COUNT)
        available_slots = int(MAX_DOWNLOAD_COUNT - current_count)
    
    return jsonify({
        "current_downloads": current_count,
        "max_downloads": max_downloads_display,
        "available_slots": available_slots,
        "is_limited": MAX_DOWNLOAD_COUNT != float('inf')
    }), 200

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
