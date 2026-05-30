#!/bin/bash
# Kill the stock market server that keeps respawning on port 8001

echo "🔫 Killing port 8001 intruder (stock market server)..."

while true; do
    # Find node processes on port 8001 running delete_stocks_server.js
    NODE_PIDS=$(lsof -i :8001 | grep node | grep delete_stocks | awk '{print $2}')
    
    if [ ! -z "$NODE_PIDS" ]; then
        echo "⚠️  Found intruder on port 8001 (PIDs: $NODE_PIDS)"
        kill -9 $NODE_PIDS 2>/dev/null
        echo "✅ Killed intruder"
    fi
    
    sleep 2
done
