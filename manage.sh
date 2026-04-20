#!/bin/bash
# Process Manager for Institutional Entry Detection System
# Ensures 24/7 operation with auto-restart on failure

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/server.pid"
LOG_FILE="$SCRIPT_DIR/server.log"
ERROR_LOG="$SCRIPT_DIR/server_error.log"

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
fi

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "Server is already running (PID: $PID)"
            return 1
        else
            echo "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi

    echo "Starting Institutional Entry Detection Server..."
    cd "$SCRIPT_DIR"
    
    # Start server in background with logging
    nohup python3 server.py > "$LOG_FILE" 2> "$ERROR_LOG" &
    PID=$!
    echo $PID > "$PID_FILE"
    
    echo "Server started (PID: $PID)"
    echo "Logs: $LOG_FILE"
    echo "Errors: $ERROR_LOG"
    
    # Wait a moment and check if it's still running
    sleep 2
    if ps -p $PID > /dev/null; then
        echo "✅ Server is running successfully"
    else
        echo "❌ Server failed to start. Check $ERROR_LOG"
        return 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Server is not running (no PID file)"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "Stopping server (PID: $PID)..."
        kill $PID
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null; then
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if ps -p $PID > /dev/null; then
            echo "Force killing server..."
            kill -9 $PID
        fi
        
        echo "✅ Server stopped"
    else
        echo "Server is not running (stale PID file)"
    fi
    
    rm -f "$PID_FILE"
}

restart() {
    echo "Restarting server..."
    stop
    sleep 2
    start
}

status() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ Server is not running"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "✅ Server is running (PID: $PID)"
        echo ""
        echo "Recent logs:"
        tail -n 10 "$LOG_FILE" 2>/dev/null || echo "No logs available"
    else
        echo "❌ Server is not running (stale PID file)"
        rm -f "$PID_FILE"
        return 1
    fi
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "No log file found"
    fi
}

errors() {
    if [ -f "$ERROR_LOG" ]; then
        tail -f "$ERROR_LOG"
    else
        echo "No error log found"
    fi
}

case "${1}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    errors)
        errors
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|errors}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the server"
        echo "  stop    - Stop the server"
        echo "  restart - Restart the server"
        echo "  status  - Check server status"
        echo "  logs    - View server logs"
        echo "  errors  - View error logs"
        exit 1
        ;;
esac
