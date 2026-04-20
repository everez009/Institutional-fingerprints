#!/bin/bash
# Complete system startup with web dashboard
# Ensures 24/7 operation with auto-restart

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID_FILE="$SCRIPT_DIR/server.pid"
DASHBOARD_PID_FILE="$SCRIPT_DIR/dashboard.pid"
LOG_DIR="$SCRIPT_DIR/logs"

# Create logs directory
mkdir -p "$LOG_DIR"

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
fi

start_backend() {
    echo "🔄 Starting backend server..."
    cd "$SCRIPT_DIR"
    
    if [ -f "$BACKEND_PID_FILE" ]; then
        PID=$(cat "$BACKEND_PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "✅ Backend already running (PID: $PID)"
            return 0
        fi
    fi
    
    # Start backend
    nohup python3 server.py > "$LOG_DIR/backend.log" 2> "$LOG_DIR/backend-error.log" &
    PID=$!
    echo $PID > "$BACKEND_PID_FILE"
    
    sleep 3
    if ps -p $PID > /dev/null; then
        echo "✅ Backend started successfully (PID: $PID)"
        return 0
    else
        echo "❌ Backend failed to start"
        return 1
    fi
}

start_dashboard() {
    echo "🔄 Starting web dashboard..."
    cd "$SCRIPT_DIR/web-dashboard"
    
    if [ -f "$DASHBOARD_PID_FILE" ]; then
        PID=$(cat "$DASHBOARD_PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "✅ Dashboard already running (PID: $PID)"
            return 0
        fi
    fi
    
    # Build and start Next.js
    echo "Building dashboard..."
    npm run build > "$LOG_DIR/dashboard-build.log" 2>&1
    
    # Start production server
    PORT=3001 nohup npm start > "$LOG_DIR/dashboard.log" 2> "$LOG_DIR/dashboard-error.log" &
    PID=$!
    echo $PID > "$DASHBOARD_PID_FILE"
    
    sleep 5
    if ps -p $PID > /dev/null; then
        echo "✅ Dashboard started successfully (PID: $PID)"
        echo "🌐 Dashboard available at: http://localhost:3001"
        return 0
    else
        echo "❌ Dashboard failed to start"
        return 1
    fi
}

stop_backend() {
    if [ ! -f "$BACKEND_PID_FILE" ]; then
        echo "Backend is not running"
        return 0
    fi
    
    PID=$(cat "$BACKEND_PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "⏹️  Stopping backend (PID: $PID)..."
        kill $PID
        
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null; then
                break
            fi
            sleep 1
        done
        
        if ps -p $PID > /dev/null; then
            kill -9 $PID
        fi
        echo "✅ Backend stopped"
    fi
    
    rm -f "$BACKEND_PID_FILE"
}

stop_dashboard() {
    if [ ! -f "$DASHBOARD_PID_FILE" ]; then
        echo "Dashboard is not running"
        return 0
    fi
    
    PID=$(cat "$DASHBOARD_PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "⏹️  Stopping dashboard (PID: $PID)..."
        kill $PID
        
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null; then
                break
            fi
            sleep 1
        done
        
        if ps -p $PID > /dev/null; then
            kill -9 $PID
        fi
        echo "✅ Dashboard stopped"
    fi
    
    rm -f "$DASHBOARD_PID_FILE"
}

status() {
    echo "=========================================="
    echo "Institutional Footprint System Status"
    echo "=========================================="
    echo ""
    
    # Backend status
    if [ -f "$BACKEND_PID_FILE" ]; then
        PID=$(cat "$BACKEND_PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "✅ Backend: RUNNING (PID: $PID, Port: 8000)"
        else
            echo "❌ Backend: STOPPED (stale PID file)"
        fi
    else
        echo "❌ Backend: NOT RUNNING"
    fi
    
    # Dashboard status
    if [ -f "$DASHBOARD_PID_FILE" ]; then
        PID=$(cat "$DASHBOARD_PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "✅ Dashboard: RUNNING (PID: $PID, Port: 3001)"
        else
            echo "❌ Dashboard: STOPPED (stale PID file)"
        fi
    else
        echo "❌ Dashboard: NOT RUNNING"
    fi
    
    echo ""
    echo "Access URLs:"
    echo "  Backend API: http://localhost:8000"
    echo "  Dashboard: http://localhost:3001"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
}

case "${1}" in
    start)
        echo "🚀 Starting Institutional Footprint System..."
        echo ""
        start_backend
        echo ""
        start_dashboard
        echo ""
        echo "=========================================="
        echo "✅ System Started Successfully!"
        echo "=========================================="
        echo ""
        echo "Backend API: http://localhost:8000"
        echo "Web Dashboard: http://localhost:3001"
        echo ""
        echo "To view logs:"
        echo "  tail -f $LOG_DIR/backend.log"
        echo "  tail -f $LOG_DIR/dashboard.log"
        ;;
    stop)
        echo "⏹️  Stopping Institutional Footprint System..."
        stop_dashboard
        stop_backend
        echo "✅ System stopped"
        ;;
    restart)
        echo "🔄 Restarting Institutional Footprint System..."
        stop_dashboard
        stop_backend
        sleep 2
        start_backend
        start_dashboard
        echo "✅ System restarted"
        ;;
    status)
        status
        ;;
    logs)
        echo "=== Backend Logs ==="
        tail -f "$LOG_DIR/backend.log"
        ;;
    dashboard-logs)
        echo "=== Dashboard Logs ==="
        tail -f "$LOG_DIR/dashboard.log"
        ;;
    errors)
        echo "=== Backend Errors ==="
        tail -f "$LOG_DIR/backend-error.log"
        echo ""
        echo "=== Dashboard Errors ==="
        tail -f "$LOG_DIR/dashboard-error.log"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|dashboard-logs|errors}"
        echo ""
        echo "Commands:"
        echo "  start          - Start backend and dashboard"
        echo "  stop           - Stop all services"
        echo "  restart        - Restart all services"
        echo "  status         - Check service status"
        echo "  logs           - View backend logs"
        echo "  dashboard-logs - View dashboard logs"
        echo "  errors         - View error logs"
        exit 1
        ;;
esac
