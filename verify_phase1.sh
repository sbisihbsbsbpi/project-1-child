#!/bin/bash
# Phase 1 Verification Script
# Tests that all Phase 1 changes work correctly

set -e  # Exit on error

echo "🧪 Phase 1 Verification Script"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Verify endpoints are before if __name__
echo "📋 Check 1: Endpoint placement..."
if grep -n "if __name__" backend/main.py | head -1 | cut -d: -f1 | {
    read main_line
    cleanup_line=$(grep -n "@app.post(\"/api/tabs/cleanup\")" backend/main.py | cut -d: -f1)
    status_line=$(grep -n "@app.get(\"/api/tabs/status\")" backend/main.py | cut -d: -f1)
    
    if [ "$cleanup_line" -lt "$main_line" ] && [ "$status_line" -lt "$main_line" ]; then
        echo -e "${GREEN}✅ PASS${NC}: Tab endpoints are before if __name__ (cleanup: $cleanup_line, status: $status_line, main: $main_line)"
        exit 0
    else
        echo -e "${RED}❌ FAIL${NC}: Tab endpoints are after if __name__"
        exit 1
    fi
}; then
    :
else
    exit 1
fi

# Check 2: Verify config has microservice URLs
echo "📋 Check 2: Config has microservice URLs..."
if grep -q "document_service_url" backend/config.py && \
   grep -q "quality_service_url" backend/config.py && \
   grep -q "api_service_url" backend/config.py; then
    echo -e "${GREEN}✅ PASS${NC}: All microservice URLs in config.py"
else
    echo -e "${RED}❌ FAIL${NC}: Missing microservice URLs in config.py"
    exit 1
fi

# Check 3: Verify no hardcoded URLs in main.py
echo "📋 Check 3: No hardcoded microservice URLs..."
hardcoded_count=$(grep -c "http://localhost:800[234]" backend/main.py || true)
if [ "$hardcoded_count" -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC}: No hardcoded microservice URLs found"
else
    echo -e "${RED}❌ FAIL${NC}: Found $hardcoded_count hardcoded URLs"
    grep -n "http://localhost:800[234]" backend/main.py
    exit 1
fi

# Check 4: Verify settings usage
echo "📋 Check 4: Using settings for microservice URLs..."
if grep -q "settings.document_service_url" backend/main.py && \
   grep -q "settings.quality_service_url" backend/main.py && \
   grep -q "settings.api_service_url" backend/main.py; then
    echo -e "${GREEN}✅ PASS${NC}: All microservice URLs use settings"
else
    echo -e "${RED}❌ FAIL${NC}: Not all URLs use settings"
    exit 1
fi

# Check 5: Verify type hints
echo "📋 Check 5: Type hints added..."
if grep -q "async def startup_event() -> None:" backend/main.py && \
   grep -q "async def shutdown_event() -> None:" backend/main.py && \
   grep -q "async def root() -> Dict\[str, str\]:" backend/main.py && \
   grep -q "async def health() -> Dict\[str, str\]:" backend/main.py; then
    echo -e "${GREEN}✅ PASS${NC}: Type hints added to core functions"
else
    echo -e "${RED}❌ FAIL${NC}: Missing type hints"
    exit 1
fi

# Check 6: Verify file structure
echo "📋 Check 6: File structure..."
if [ -f "backend/main.py" ] && [ -f "backend/config.py" ]; then
    main_lines=$(wc -l < backend/main.py)
    config_lines=$(wc -l < backend/config.py)
    echo -e "${GREEN}✅ PASS${NC}: Files exist (main.py: $main_lines lines, config.py: $config_lines lines)"
else
    echo -e "${RED}❌ FAIL${NC}: Missing files"
    exit 1
fi

# Summary
echo ""
echo "=============================="
echo -e "${GREEN}🎉 All Phase 1 checks passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Test manually: cd backend && python main.py"
echo "  2. Test endpoints: curl http://localhost:8001/health"
echo "  3. Continue to Phase 2: See MAIN_PY_REFACTORING_PHASES.md"
echo ""

