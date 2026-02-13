#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration variables
REQUIREMENTS_FILE="./requirements.txt"
CACHE_DIR="./.deps_cache"
CACHE_FILE="$CACHE_DIR/last_install.md5"
PYPI_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple/"
TRUSTED_HOST="pypi.tuna.tsinghua.edu.cn"
LOG_DIR="./logs"
PID_FILE="./server.pid"

# Function to print messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to activate virtual environment
activate_venv() {
    if test -n "$VIRTUAL_ENV"; then
        log_message "Already in Python virtual environment: $VIRTUAL_ENV"
    else
        if [ -d "venv" ]; then
            log_message "Activating Python virtual environment"
            if . venv/bin/activate; then
                log_message "Virtual environment activated successfully"
            else
                log_message "ERROR: Failed to activate virtual environment"
                exit 1
            fi
        else
            log_message "ERROR: Virtual environment 'venv' not found. Please create it first."
            exit 1
        fi
    fi
}

# Function to update pip
update_pip() {
    local pip3_version=$(pip3 --version 2>/dev/null | awk '{print $2}')
    
    if [[ -z "$pip3_version" ]]; then
        log_message "ERROR: pip3 not installed or not in PATH"
        exit 1
    fi
    
    log_message "Current pip3 version: $pip3_version"
    
    # Attempt to get latest pip version
    local latest_version=$(pip3 install --dry-run --upgrade pip 2>&1 | grep -o 'would install.*pip-[0-9.]*' | grep -o '[0-9.]*' | head -n1)
    
    if [[ -z "$latest_version" ]]; then
        # Alternative method to get latest version
        latest_version=$(python3 -c "import urllib.request, json; response = urllib.request.urlopen('https://pypi.org/pypi/pip/json'); data = json.loads(response.read()); print(data['info']['version'])" 2>/dev/null)
    fi
    
    if [[ -n "$latest_version" && "$pip3_version" != "$latest_version" ]]; then
        log_message "Updating pip from $pip3_version to $latest_version..."
        pip3 install --upgrade pip -i "$PYPI_MIRROR" --trusted-host "$TRUSTED_HOST"
        log_message "pip updated to version: $latest_version"
    else
        log_message "pip is already up to date"
    fi
}

# Function to check if all dependencies are satisfied
check_all_deps() {
    while IFS= read -r line || [[ -n "$line" ]]; do
        line_clean=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        [[ -z "$line_clean" || "$line_clean" =~ ^# ]] && continue

        # Extract package name (remove version specifiers)
        package=$(echo "$line_clean" | sed 's/[><!=].*//;s/[[:space:]]*$//')

        if ! pip3 show "$package" > /dev/null 2>&1; then
            return 1  # Package not installed
        fi
    done < "$REQUIREMENTS_FILE"
    return 0  # All packages installed
}

# Function to install dependencies with caching
install_dependencies() {
    # Create cache directory
    mkdir -p "$CACHE_DIR"
    mkdir -p "$LOG_DIR"
    
    # Generate MD5 hash of requirements file
    local current_md5=$(md5sum "$REQUIREMENTS_FILE" 2>/dev/null | awk '{print $1}')
    if [[ -z "$current_md5" ]]; then
        # Fallback for systems without md5sum
        current_md5=$(cat "$REQUIREMENTS_FILE" | cksum | awk '{print $1}')
    fi

    # Check cache
    local need_install=true
    if [[ -f "$CACHE_FILE" ]]; then
        local cached_md5=$(cat "$CACHE_FILE")
        
        if [[ "$current_md5" == "$cached_md5" ]]; then
            log_message "Checking installed dependencies..."
            if check_all_deps; then
                log_message "✓ Dependencies already installed and up to date"
                need_install=false
            else
                log_message "⚠ Requirements unchanged but some dependencies missing"
            fi
        fi
    fi

    if [[ "$need_install" == true ]]; then
        log_message "🚀 Installing/updating Python dependencies..."
        
        if pip3 install -r "$REQUIREMENTS_FILE" -i "$PYPI_MIRROR" --trusted-host "$TRUSTED_HOST"; then
            # Update cache
            echo "$current_md5" > "$CACHE_FILE"
            log_message "✓ Dependencies installed successfully"
            
            # Save installed versions
            pip3 freeze > "$CACHE_DIR/installed_versions.txt"
        else
            log_message "ERROR: Dependency installation failed"
            exit 1
        fi
    fi
}

# Function to start the server
start_server() {
    log_message "Starting server..."
    
    # Check if server is already running
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_message "Server is already running with PID: $pid"
            exit 1
        else
            log_message "Stale PID file found, removing it"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    # Start server in background and save PID
    nohup python3 ./server.py > "$LOG_DIR/server.log" 2>&1 &
    local server_pid=$!
    echo $server_pid > "$PID_FILE"
    
    log_message "Server started with PID: $server_pid"
    log_message "Check logs at: $LOG_DIR/server.log"
    log_message "Server is running on http://localhost:5000"
}

# Main execution
main() {
    log_message "Starting SocialMediaStreamDownloader setup..."
    
    activate_venv
    update_pip
    install_dependencies
    start_server
    
    log_message "Setup completed successfully!"
}

# Handle command-line arguments
case "${1:-start}" in
    start)
        main
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            local pid=$(cat "$PID_FILE")
            if ps -p "$pid" > /dev/null 2>&1; then
                kill "$pid"
                rm -f "$PID_FILE"
                log_message "Server stopped (PID: $pid)"
            else
                log_message "No server process found with PID: $pid"
                rm -f "$PID_FILE"
            fi
        else
            log_message "Server is not running (no PID file found)"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac