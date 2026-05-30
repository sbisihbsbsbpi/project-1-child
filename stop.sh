#!/bin/bash

# 🛑 Screenshot Tool - Stop Script
# ✅ MONOLITH: Stops Backend + Frontend (2 processes only)

echo "🛑 Stopping Screenshot Tool..."
echo "=========================================================="
echo ""

# Function to stop service
stop_service() {
    local name=$1
    local pattern=$2
    
    pids=$(pgrep -f "$pattern")
    
    if [ -n "$pids" ]; then
        echo "🛑 Stopping $name..."
        pkill -f "$pattern"
        sleep 1
        
        # Force kill if still running
        if pgrep -f "$pattern" > /dev/null; then
            pkill -9 -f "$pattern"
        fi
        
        echo "   ✅ $name stopped"
    else
        echo "   ℹ️  $name not running"
    fi
}

# Stop backend and frontend
stop_service "Backend" "backend/main.py"
stop_service "Frontend" "vite"

echo ""
echo "=========================================================="
echo "✅ Screenshot Tool stopped!"
echo "=========================================================="
echo ""
