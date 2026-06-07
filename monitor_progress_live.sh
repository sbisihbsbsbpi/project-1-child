#!/bin/bash
echo "📊 Live Progress Monitor"
echo "=" | tr '=' '='
echo ""

while true; do
    clear
    echo "📊 Service + Parts Full Run - Live Progress"
    echo "==========================================="
    echo ""
    
    # Get current template
    CURRENT=$(tail -100 logs/full_service_parts_run.log | grep "TEMPLATE" | tail -1)
    echo "Current: $CURRENT"
    echo ""
    
    # Count processed
    PROCESSED=$(grep -c "Template loaded successfully" logs/full_service_parts_run.log 2>/dev/null || echo "0")
    echo "Templates processed: $PROCESSED"
    echo ""
    
    # Show last few actions
    echo "Recent activity:"
    tail -10 logs/full_service_parts_run.log | grep -E "INFO|✅|📊" | tail -5
    echo ""
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    sleep 5
done
