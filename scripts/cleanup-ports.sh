#!/bin/bash
# ✅ MONOLITH: Cleanup script for monolithic architecture
# Cleans up backend and frontend ports only

echo "🧹 Cleaning up ports for monolithic architecture..."
echo ""

# Define ports (only 2 now - microservices removed!)
BACKEND_PORT=8001
FRONTEND_PORT=5173

# Function to kill processes on a specific port
kill_port() {
    local port=$1
    local service_name=$2
    
    echo "Checking port $port ($service_name)..."
    
    # Find all PIDs listening on this port
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    if [ -z "$pids" ]; then
        echo "  ✅ Port $port is free"
    else
        echo "  ⚠️  Found processes on port $port:"
        for pid in $pids; do
            local process_name=$(ps -p $pid -o comm= 2>/dev/null)
            echo "    - PID $pid ($process_name)"
        done
        
        echo "  🔧 Killing processes..."
        kill -9 $pids 2>/dev/null
        sleep 0.5
        
        # Verify
        local remaining=$(lsof -ti :$port 2>/dev/null)
        if [ -z "$remaining" ]; then
            echo "  ✅ Port $port is now free"
        else
            echo "  ❌ Failed to free port $port"
        fi
    fi
    echo ""
}

# Clean up each port
kill_port $BACKEND_PORT "Backend (includes all services)"
kill_port $FRONTEND_PORT "Frontend"

echo "✅ Port cleanup complete!"
echo ""
echo "💡 All services integrated into backend - no microservices needed!"
echo ""
echo "You can now start the application:"
echo "  ./start.sh"
