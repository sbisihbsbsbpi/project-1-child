#!/bin/bash

# 🚀 Screenshot Tool - Monolithic Architecture Startup Script
# ✅ MONOLITH: Starts Backend + Frontend (2 processes only)
# No microservices needed - all services integrated into backend!

echo "🚀 Starting Screenshot Tool - Monolithic Architecture"
echo "=========================================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# ✅ STEP 0: Clean up ports before starting
echo "🧹 Cleaning up ports 8001 and 5173..."
for port in 8001 5173; do
    pids=$(lsof -ti :$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo "  Killing processes on port $port"
        kill -9 $pids 2>/dev/null || true
    fi
done
echo "   ✅ Ports cleaned"
echo ""

# Array to store PIDs
declare -a PIDS

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    
    # Kill all background processes
    for pid in "${PIDS[@]}"; do
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null
        fi
    done
    
    # Also kill any remaining processes
    pkill -f "backend/main.py" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    
    echo "✅ All services stopped"
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

echo "📦 Step 1/2: Starting Backend (Port 8001)..."
cd "$SCRIPT_DIR/backend"
python3 main.py > /tmp/backend.log 2>&1 &
PIDS+=($!)
echo "   ✅ Backend started (PID: ${PIDS[-1]})"
echo "   📍 API: http://127.0.0.1:8001"
echo "   📄 Logs: tail -f /tmp/backend.log"
echo ""

# Give backend time to start
sleep 2

echo "🎨 Step 2/2: Starting Frontend (Port 5173)..."
cd "$SCRIPT_DIR/frontend"
npm run dev > /tmp/frontend.log 2>&1 &
PIDS+=($!)
echo "   ✅ Frontend started (PID: ${PIDS[-1]})"
echo "   📍 UI: http://localhost:5173"
echo "   📄 Logs: tail -f /tmp/frontend.log"
echo ""

# Give frontend time to start
sleep 2

echo "=========================================================="
echo "🎉 Screenshot Tool is ready!"
echo "=========================================================="
echo ""
echo "📊 Running Services:"
echo "   • Backend:  http://127.0.0.1:8001 ✅"
echo "   • Frontend: http://localhost:5173 ✅"
echo ""
echo "💡 All services (Quality, Document, API, Screenshot) are"
echo "   integrated into the backend - no microservices needed!"
echo ""
echo "🔍 Health Check:"
echo "   curl http://127.0.0.1:8001/health"
echo ""
echo "🛑 To stop: Press Ctrl+C or run: ./stop.sh"
echo "=========================================================="
echo ""
echo "Waiting for services... (Press Ctrl+C to stop)"
echo ""

# Wait for all background processes
wait
