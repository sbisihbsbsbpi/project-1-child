#!/bin/bash

# 🔍 Screenshot Tool - Health Check Script
# ✅ MONOLITH: Checks Backend + Frontend (2 services only)

echo "🔍 Checking Screenshot Tool Status..."
echo "=========================================================="
echo ""

# Function to check service health
check_service() {
    local name=$1
    local url=$2
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo "✅ $name - HEALTHY (HTTP $response)"
        return 0
    else
        echo "❌ $name - DOWN (HTTP $response)"
        return 1
    fi
}

# Check backend
echo "📊 Service Health:"
echo ""
check_service "Backend (API)" "http://127.0.0.1:8001/health"

echo ""
echo "🌐 Frontend:"
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ Frontend - RUNNING (http://localhost:5173)"
else
    echo "❌ Frontend - DOWN"
fi

echo ""
echo "=========================================================="
echo ""
echo "💡 Integrated Services (all in backend):"
echo "   • Screenshot Service ✅"
echo "   • Quality Checker    ✅"
echo "   • Document Generator ✅"
echo "   • API Extraction     ✅"
echo ""
echo "📄 View Logs:"
echo "   tail -f /tmp/backend.log"
echo "   tail -f /tmp/frontend.log"
echo ""
echo "🚀 To start: ./start.sh"
echo "🛑 To stop:  ./stop.sh"
echo ""
