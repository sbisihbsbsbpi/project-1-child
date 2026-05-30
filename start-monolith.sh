#!/bin/bash

# 🚀 Screenshot Tool - One-Click Startup Script
# This script starts both backend and frontend automatically

echo "🚀 Starting Screenshot Tool..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start backend in background
echo "📦 Starting Backend (Python FastAPI)..."
cd "$SCRIPT_DIR/backend"
python3 main.py &
BACKEND_PID=$!
echo "   ✅ Backend started (PID: $BACKEND_PID)"
echo "   📍 Running on: http://127.0.0.1:8001"
echo ""

# Wait a moment for backend to start
sleep 2

# Start frontend in background
echo "🎨 Starting Frontend (React + Vite)..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "   ✅ Frontend started (PID: $FRONTEND_PID)"
echo "   📍 Running on: http://localhost:5173"
echo ""

echo "✅ Both services are running!"
echo ""
echo "🌐 Open your browser to: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both services..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

# Wait for both processes
wait

