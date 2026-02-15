##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import re
import threading
import psutil
import time
## <<Third-Part>>
from backend.src.platform.platform_dispatcher import PlatformDispatcher
from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from backend.src.base.config import BaseConfig
from backend.src.base.log import get_logger


platform_dispatcher = PlatformDispatcher()
app = Flask(__name__, static_folder='./frontend/src/static', template_folder='./frontend/src/templates')

# Initialize logger
logger = get_logger()

# System load monitoring constants
LOAD_MONITORING_INTERVAL = 5  # seconds
HIGH_CPU_THRESHOLD = 80.0     # percentage
HIGH_MEMORY_THRESHOLD = 85.0  # percentage
HIGH_DISK_THRESHOLD = 90.0    # percentage
HIGH_NETWORK_THRESHOLD = 100.0  # MB/s (example threshold)

# Global variables for load monitoring
last_network_io = psutil.net_io_counters()
last_network_time = time.time()
high_load_alert_active = False

def get_system_load():
    """Get current system load metrics"""
    global last_network_io, last_network_time
    
    # CPU usage percentage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Memory usage percentage
    memory_percent = psutil.virtual_memory().percent
    
    # Disk usage percentage (for root partition)
    disk_percent = psutil.disk_usage('/').percent
    
    # Network I/O (calculate speed since last check)
    current_network_io = psutil.net_io_counters()
    current_time = time.time()
    
    time_diff = current_time - last_network_time
    if time_diff > 0:
        bytes_sent_per_sec = (current_network_io.bytes_sent - last_network_io.bytes_sent) / time_diff
        bytes_recv_per_sec = (current_network_io.bytes_recv - last_network_io.bytes_recv) / time_diff
        network_speed_mb_s = (bytes_sent_per_sec + bytes_recv_per_sec) / (1024 * 1024)  # Convert to MB/s
    else:
        network_speed_mb_s = 0.0
    
    # Update for next calculation
    last_network_io = current_network_io
    last_network_time = current_time
    
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'disk_percent': disk_percent,
        'network_speed_mb_s': network_speed_mb_s
    }

def check_system_load_thresholds(load_metrics):
    """Check if any system load metric exceeds thresholds"""
    alerts = []
    
    if load_metrics['cpu_percent'] > HIGH_CPU_THRESHOLD:
        alerts.append(f"High CPU usage: {load_metrics['cpu_percent']:.1f}% (threshold: {HIGH_CPU_THRESHOLD}%)")
    
    if load_metrics['memory_percent'] > HIGH_MEMORY_THRESHOLD:
        alerts.append(f"High memory usage: {load_metrics['memory_percent']:.1f}% (threshold: {HIGH_MEMORY_THRESHOLD}%)")
    
    if load_metrics['disk_percent'] > HIGH_DISK_THRESHOLD:
        alerts.append(f"High disk usage: {load_metrics['disk_percent']:.1f}% (threshold: {HIGH_DISK_THRESHOLD}%)")
    
    if load_metrics['network_speed_mb_s'] > HIGH_NETWORK_THRESHOLD:
        alerts.append(f"High network activity: {load_metrics['network_speed_mb_s']:.2f} MB/s (threshold: {HIGH_NETWORK_THRESHOLD} MB/s)")
    
    return alerts

def is_system_overloaded():
    """Check if system is currently overloaded"""
    load_metrics = get_system_load()
    alerts = check_system_load_thresholds(load_metrics)
    return len(alerts) > 0, alerts, load_metrics

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
## decrement active download count and log
##
def decrement_download_count_and_log(client_ip=None):
    global active_downloads
    with download_lock:
        previous_count = active_downloads
        if active_downloads > 0:
            active_downloads -= 1
        new_count = active_downloads
        
    if client_ip:
        logger.info(f"Download completed for IP: {client_ip}. Active downloads decreased from {previous_count} to {new_count}")
    else:
        logger.info(f"Download completed. Active downloads decreased from {previous_count} to {new_count}")
    return new_count

##
## handle the request from the client
##
@app.route('/', methods=['POST'])
@limiter.limit("10 per minute")  # Limit to 10 requests per minute per IP for POST endpoint
def process_request():
    client_ip = request.remote_addr
    logger.info(f"Received download request from IP: {client_ip}")
    
    # Check system load before processing request
    is_overloaded, overload_alerts, load_metrics = is_system_overloaded()
    if is_overloaded:
        logger.warning(f"System overloaded, rejecting request from IP: {client_ip}. Alerts: {overload_alerts}")
        return jsonify({
            "message": f"System is currently overloaded. Please try again later.",
            "alerts": overload_alerts,
            "load_metrics": load_metrics
        }), 503  # Service Unavailable
    
    try:
        # Validate request data
        json_data = request.json

        if not json_data:
            logger.warning(f"Invalid JSON data received from IP: {client_ip}")
            return jsonify({"message": "Invalid JSON data"}), 400

        # Validate required fields
        if 'urls' not in json_data or not isinstance(json_data['urls'], list) or len(json_data['urls']) == 0:
            logger.warning(f"Missing or invalid 'urls' field in request from IP: {client_ip}")
            return jsonify({"message": "Missing or invalid 'urls' field in request"}), 400

        # Log the number of URLs in the request
        logger.info(f"Processing request with {len(json_data['urls'])} URLs from IP: {client_ip}")

        # Check if download limit is exceeded (only if there is a limit)
        current_count = get_active_download_count()
        if MAX_DOWNLOAD_COUNT != float('inf') and current_count >= MAX_DOWNLOAD_COUNT:
            logger.warning(f"Download limit exceeded for IP: {client_ip}. Current: {current_count}, Max: {int(MAX_DOWNLOAD_COUNT)}")
            return jsonify({
                "message": f"Download limit exceeded. Maximum {int(MAX_DOWNLOAD_COUNT)} downloads allowed. Current: {current_count}"
            }), 429  # Too Many Requests

        # Validate URLs
        for url in json_data['urls']:
            if not isinstance(url, str):
                logger.warning(f"Invalid URL format in request from IP: {client_ip}, URL: {url}")
                return jsonify({"message": f"Invalid URL format: {url}"}), 400
            if not is_valid_url(url):
                logger.warning(f"Invalid URL format from IP: {client_ip}, URL: {url}")
                return jsonify({"message": f"Invalid URL format: {url}"}), 400

        ##
        ## get request from the client
        ##
        # Increment download counter before dispatching
        new_count = increment_download_count()
        logger.info(f"Incremented download count. Current active downloads: {new_count}, from IP: {client_ip}")

        # Pass a callback to decrement counter when download completes
        platform_dispatcher.dispatch(json_data, lambda: decrement_download_count_and_log(client_ip))

    except ValueError as ve:
        logger.error(f"ValueError processing request from IP {client_ip}: {ve}")
        return jsonify({"message": f"Invalid request data: {str(ve)}"}), 400
    except Exception as e:
        logger.error(f"Error processing request from IP {client_ip}: {e}")
        ##
        ## response to the client
        ##
        return jsonify({"message": f"Request processing failed: {str(e)}"}), 500

    ##
    ## response to the client
    ##
    final_count = get_active_download_count()
    logger.info(f"Request processing started successfully. Active downloads: {final_count}, from IP: {client_ip}")
    return jsonify({"message": f"Request started processing", "current_downloads": final_count}), 200

##
## get current download count
##
@app.route('/api/download-status', methods=['GET'])
def get_download_status():
    client_ip = request.remote_addr
    logger.info(f"Download status requested from IP: {client_ip}")
    
    current_count = get_active_download_count()
    # Handle infinite limit case
    if MAX_DOWNLOAD_COUNT == float('inf'):
        max_downloads_display = 0  # Represent unlimited as 0
        available_slots = 0  # Unlimited slots
    else:
        max_downloads_display = int(MAX_DOWNLOAD_COUNT)
        available_slots = int(MAX_DOWNLOAD_COUNT - current_count)

    logger.info(f"Returning download status to IP: {client_ip}. Current: {current_count}, Max: {max_downloads_display}, Available: {available_slots}")
    
    return jsonify({
        "current_downloads": current_count,
        "max_downloads": max_downloads_display,
        "available_slots": available_slots,
        "is_limited": MAX_DOWNLOAD_COUNT != float('inf')
    }), 200

##
## get recent logs
##
@app.route('/api/logs', methods=['GET'])
def get_recent_logs():
    import os
    from datetime import datetime
    client_ip = request.remote_addr
    logger.info(f"Recent logs requested from IP: {client_ip}")
    
    # Get query parameters for filtering
    log_level = request.args.get('level', 'INFO')
    limit = int(request.args.get('limit', 50))  # Default to last 50 logs
    
    # Find the most recent log file
    log_dir = os.path.dirname(logger.handlers[1].baseFilename)
    log_files = [f for f in os.listdir(log_dir) if f.startswith("social_media_stream_downloader")]
    log_files.sort(reverse=True)  # Sort by name to get most recent first
    
    recent_logs = []
    if log_files:
        latest_log_file = os.path.join(log_dir, log_files[0])
        try:
            with open(latest_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Get the last 'limit' lines
                recent_lines = lines[-limit:] if len(lines) >= limit else lines
                
                for line in recent_lines:
                    # Filter by log level if specified
                    if log_level == 'ALL' or f'-[{log_level}]-' in line:
                        recent_logs.append(line.strip())
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            recent_logs = [f"Error reading log file: {e}"]
    else:
        recent_logs = ["No log files found"]
    
    logger.info(f"Sent {len(recent_logs)} log entries to IP: {client_ip}")
    return jsonify({
        "log_entries": recent_logs,
        "log_file": log_files[0] if log_files else "N/A",
        "total_entries_returned": len(recent_logs),
        "recent_activity": {
            "active_downloads": get_active_download_count(),
            "max_allowed": MAX_DOWNLOAD_COUNT if MAX_DOWNLOAD_COUNT != float('inf') else 'unlimited',
            "request_from": client_ip
        }
    }), 200

##
## get system load status
##
@app.route('/api/system-load', methods=['GET'])
def get_system_load_status():
    client_ip = request.remote_addr
    logger.info(f"System load status requested from IP: {client_ip}")
    
    load_metrics = get_system_load()
    is_overloaded, alerts, _ = is_system_overloaded()
    
    logger.info(f"Sending system load status to IP: {client_ip}. Overloaded: {is_overloaded}, Metrics: {load_metrics}")
    
    return jsonify({
        "is_overloaded": is_overloaded,
        "alerts": alerts,
        "load_metrics": load_metrics,
        "thresholds": {
            "cpu_percent": HIGH_CPU_THRESHOLD,
            "memory_percent": HIGH_MEMORY_THRESHOLD,
            "disk_percent": HIGH_DISK_THRESHOLD,
            "network_speed_mb_s": HIGH_NETWORK_THRESHOLD
        }
    }), 200

@app.route('/', methods=['GET'])
def index():
    client_ip = request.remote_addr
    logger.info(f"Homepage accessed from IP: {client_ip}")
    return render_template('index.html')

@app.teardown_appcontext
def shutdown_dispatchers(exception=None):
    """Clean up resources when the application shuts down"""
    try:
        logger.info("Application shutdown initiated")
        platform_dispatcher.shutdown()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == '__main__':
  ##
  ## register platform_dispatcher
  ##
  logger.info("Starting server initialization")
  platform_dispatcher.register()
  logger.info("Platform dispatcher registered successfully")

  ##
  ## 启动服务
  ##
  try:
    logger.info("Starting server on http://0.0.0.0:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
  finally:
    # Ensure cleanup happens when the script exits
    logger.info("Server shutting down, cleaning up resources")
    platform_dispatcher.shutdown()
    logger.info("Server shutdown completed")
