#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration variables
IMAGE_NAME="social-media-downloader"
CONTAINER_NAME="social-media-downloader"
PORT=5000
DOWNLOAD_DIR="./downloads"
LOGS_DIR="./logs"
CONFIG_DIR="./config"

# Function to print messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to build the Docker image
build_image() {
    log_message "Building Docker image: $IMAGE_NAME"
    
    if docker build -t $IMAGE_NAME .; then
        log_message "✓ Docker image built successfully"
    else
        log_message "ERROR: Failed to build Docker image"
        exit 1
    fi
}

# Function to check if container is running
is_container_running() {
    docker ps --filter "name=$CONTAINER_NAME" --filter "status=running" -q > /dev/null
}

# Function to check if container exists
container_exists() {
    docker ps -a --filter "name=$CONTAINER_NAME" -q > /dev/null
}

# Function to start the service
start_service() {
    log_message "Starting $CONTAINER_NAME service..."

    # Check if container is already running
    if is_container_running; then
        log_message "Container $CONTAINER_NAME is already running"
        return 0
    fi

    # If container exists but is stopped, start it
    if container_exists; then
        if docker start $CONTAINER_NAME; then
            log_message "✓ Container $CONTAINER_NAME started successfully"
        else
            log_message "ERROR: Failed to start container $CONTAINER_NAME"
            exit 1
        fi
        return 0
    fi

    # Create required directories
    mkdir -p $DOWNLOAD_DIR $LOGS_DIR $CONFIG_DIR

    # Run the container
    if docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:$PORT \
        -v $(pwd)/$DOWNLOAD_DIR:/mnt/video \
        -v $(pwd)/$LOGS_DIR:/app/logs \
        -v $(pwd)/$CONFIG_DIR:/app/config \
        -e SAVE_PATH=/mnt/video \
        -e LOG_PATH=./logs \
        --restart unless-stopped \
        $IMAGE_NAME; then
        
        log_message "✓ Container $CONTAINER_NAME started successfully"
        log_message "Service is running on http://localhost:$PORT"
    else
        log_message "ERROR: Failed to start container $CONTAINER_NAME"
        exit 1
    fi
}

# Function to stop the service
stop_service() {
    log_message "Stopping $CONTAINER_NAME service..."

    if container_exists; then
        if docker stop $CONTAINER_NAME; then
            log_message "✓ Container $CONTAINER_NAME stopped successfully"
        else
            log_message "ERROR: Failed to stop container $CONTAINER_NAME"
            exit 1
        fi
    else
        log_message "Container $CONTAINER_NAME does not exist"
    fi
}

# Function to remove the container
remove_container() {
    log_message "Removing $CONTAINER_NAME container..."

    if container_exists; then
        if docker rm $CONTAINER_NAME; then
            log_message "✓ Container $CONTAINER_NAME removed successfully"
        else
            log_message "ERROR: Failed to remove container $CONTAINER_NAME"
            exit 1
        fi
    else
        log_message "Container $CONTAINER_NAME does not exist"
    fi
}

# Function to remove the image
remove_image() {
    log_message "Removing $IMAGE_NAME image..."

    if docker images $IMAGE_NAME -q | grep -q .; then
        if docker rmi $IMAGE_NAME; then
            log_message "✓ Image $IMAGE_NAME removed successfully"
        else
            log_message "ERROR: Failed to remove image $IMAGE_NAME"
            exit 1
        fi
    else
        log_message "Image $IMAGE_NAME does not exist"
    fi
}

# Function to restart the service
restart_service() {
    stop_service
    sleep 2
    start_service
}

# Function to show service status
show_status() {
    if is_container_running; then
        log_message "Container $CONTAINER_NAME is running"
        docker ps --filter "name=$CONTAINER_NAME"
    elif container_exists; then
        log_message "Container $CONTAINER_NAME exists but is not running"
        docker ps -a --filter "name=$CONTAINER_NAME"
    else
        log_message "Container $CONTAINER_NAME does not exist"
    fi
}

# Function to show logs
show_logs() {
    if container_exists; then
        log_message "Displaying logs for $CONTAINER_NAME:"
        docker logs -f $CONTAINER_NAME
    else
        log_message "Container $CONTAINER_NAME does not exist"
    fi
}

# Main execution
main() {
    case "${1:-build-and-start}" in
        build)
            build_image
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        remove-container)
            stop_service
            remove_container
            ;;
        remove-image)
            remove_image
            ;;
        remove-all)
            stop_service
            remove_container
            remove_image
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        build-and-start)
            build_image
            start_service
            ;;
        *)
            echo "Usage: $0 {build|start|stop|restart|remove-container|remove-image|remove-all|status|logs|build-and-start}"
            echo ""
            echo "Commands:"
            echo "  build            Build the Docker image"
            echo "  start            Start the service container"
            echo "  stop             Stop the service container"
            echo "  restart          Restart the service container"
            echo "  remove-container Remove the container"
            echo "  remove-image     Remove the Docker image"
            echo "  remove-all       Stop and remove container and image"
            echo "  status           Show service status"
            echo "  logs             Show container logs"
            echo "  build-and-start  Build image and start service (default)"
            exit 1
            ;;
    esac
}

main "$@"