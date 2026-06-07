#!/bin/bash
# Monitor Phase 1 Data Collection Progress

LOG_FILE="logs/phase1_data_collection.log"

echo "==================================="
echo "Phase 1 Data Collection Monitor"
echo "==================================="
echo ""

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    exit 1
fi

# Get current template being processed
CURRENT=$(tail -200 "$LOG_FILE" | grep "TEMPLATE [0-9]" | tail -1)
echo "📍 Current: $CURRENT"
echo ""

# Show last 5 templates with their complexity
echo "📊 Recent Templates:"
tail -400 "$LOG_FILE" | grep -A 6 "TEMPLATE [0-9]" | grep -E "TEMPLATE|Sortable items:|🤖 AI:" | tail -15
echo ""

# Count completed templates
COMPLETED=$(grep -c "TEMPLATE [0-9]" "$LOG_FILE")
echo "✅ Templates processed: $COMPLETED"
echo ""

# Show any errors
ERRORS=$(grep -c "ERROR" "$LOG_FILE")
if [ $ERRORS -gt 0 ]; then
    echo "⚠️  Errors found: $ERRORS"
    tail -100 "$LOG_FILE" | grep "ERROR" | tail -3
fi

echo ""
echo "To see full log: tail -f logs/phase1_data_collection.log"
