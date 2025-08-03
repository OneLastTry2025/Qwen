#!/bin/bash

# Qwen Clone Application - Server Management Script

echo "🚀 Qwen Clone Application Server Manager"
echo "========================================"

# Function to check if server is running
check_server() {
    if pgrep -f "api_server.py" > /dev/null; then
        echo "✅ Server is running (PID: $(pgrep -f api_server.py))"
        return 0
    else
        echo "❌ Server is not running"
        return 1
    fi
}

# Function to start server
start_server() {
    echo "🔄 Starting Qwen Clone server..."
    cd /app
    python api_server.py > server.log 2>&1 &
    sleep 5
    
    if check_server; then
        echo "🎉 Server started successfully!"
        echo "📡 Access the application at: http://127.0.0.1:5000"
        echo "📋 View logs with: tail -f /app/server.log"
    else
        echo "❌ Failed to start server. Check logs:"
        tail -20 /app/server.log
    fi
}

# Function to stop server
stop_server() {
    echo "🛑 Stopping Qwen Clone server..."
    pkill -f "api_server.py"
    sleep 2
    
    if ! check_server; then
        echo "✅ Server stopped successfully"
    else
        echo "⚠️  Force killing server..."
        pkill -9 -f "api_server.py"
        sleep 1
        if ! check_server; then
            echo "✅ Server force stopped"
        else
            echo "❌ Failed to stop server"
        fi
    fi
}

# Function to restart server
restart_server() {
    echo "🔄 Restarting Qwen Clone server..."
    stop_server
    sleep 2
    start_server
}

# Function to show server status
show_status() {
    echo "📊 Server Status:"
    echo "---------------"
    check_server
    
    if pgrep -f "api_server.py" > /dev/null; then
        echo "📡 Server URL: http://0.0.0.0:8010 (External access enabled)"
        echo "🌐 Local access: http://127.0.0.1:8010"
        echo "🔗 Preview domain should now work!"
        echo "🔍 Test connection:"
        status_code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8010/ 2>/dev/null)
        if [ "$status_code" = "200" ]; then
            echo "   ✅ Frontend accessible (HTTP $status_code)"
        else
            echo "   ❌ Frontend not accessible (HTTP $status_code)"
        fi
        
        # Test API endpoint
        api_status=$(curl -s -X GET http://127.0.0.1:8010/model 2>/dev/null | grep -o '"status":"success"')
        if [ -n "$api_status" ]; then
            echo "   ✅ API endpoints working"
        else
            echo "   ❌ API endpoints not responding"
        fi
    fi
}

# Function to show logs
show_logs() {
    echo "📋 Recent Server Logs:"
    echo "--------------------"
    if [ -f "/app/server.log" ]; then
        tail -20 /app/server.log
    else
        echo "❌ No log file found"
    fi
}

# Main menu
case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the Qwen Clone server"
        echo "  stop    - Stop the Qwen Clone server"
        echo "  restart - Restart the Qwen Clone server"
        echo "  status  - Show server status and connectivity"
        echo "  logs    - Show recent server logs"
        echo ""
        echo "Quick Commands:"
        echo "  ./start_server.sh start    # Start server"
        echo "  ./start_server.sh status   # Check if running"
        echo "  ./start_server.sh logs     # View logs"
        echo ""
        echo "🌐 Application URL: http://127.0.0.1:8010"
        exit 1
        ;;
esac