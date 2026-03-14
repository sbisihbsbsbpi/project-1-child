# 🤖 Agent Mode Context - Backend Refactoring

**Date**: 2024
**Branch**: `refactor/phase-1-quick-fixes`
**Current Status**: Phase 1 Complete ✅, Ready for Phase 2

---

## 📍 Where We Are

### ✅ Phase 1: COMPLETE (Commits: 765f2b4, 3c49a89)

**What was done:**
1. **Fixed critical bug** - Moved `/api/tabs/cleanup` and `/api/tabs/status` endpoints before `if __name__ == "__main__"` (they were unreachable)
2. **Extracted hardcoded URLs** - Added `document_service_url`, `quality_service_url`, `api_service_url` to `backend/config.py`
3. **Added type hints** - Added return types to `startup_event()`, `shutdown_event()`, `root()`, `health()`, `system_usage()`

**Verification**: All checks passing (`./verify_phase1.sh`)

---

## 🎯 What You Need to Do Next

### **Phase 2: Code Organization (1-2 days)**

**Goal**: Split `backend/main.py` (2,357 lines) into modular router files

**Target Structure**:
```
backend/
├── main.py                    # Core app + startup (keep ~200 lines)
├── config.py                  # ✅ Already exists
├── routers/
│   ├── __init__.py
│   ├── screenshot.py          # Screenshot endpoints (~400 lines)
│   ├── document.py            # Document generation (~300 lines)
│   ├── quality.py             # Quality check (~200 lines)
│   ├── api_service.py         # API service proxy (~150 lines)
│   ├── network.py             # Network/API interception (~250 lines)
│   └── tabs.py                # Tab management (~100 lines)
└── services/
    ├── __init__.py
    └── screenshot_service.py  # ✅ Already exists
```

---

## 📋 Phase 2 Tasks (In Order)

### Task 2.1: Create Router Structure
- [ ] Create `backend/routers/` directory
- [ ] Create `backend/routers/__init__.py`
- [ ] Create empty router files (screenshot.py, document.py, quality.py, api_service.py, network.py, tabs.py)

### Task 2.2: Extract Screenshot Router
- [ ] Move screenshot endpoints to `routers/screenshot.py`
- [ ] Import `screenshot_service` from `services.screenshot_service`
- [ ] Register router in `main.py` with `app.include_router(screenshot_router)`
- [ ] Test: `curl http://localhost:8001/api/screenshot`

### Task 2.3: Extract Document Router
- [ ] Move document endpoints to `routers/document.py`
- [ ] Move `generate_document()` helper function
- [ ] Register router in `main.py`
- [ ] Test: Document generation endpoint

### Task 2.4: Extract Quality Router
- [ ] Move quality endpoints to `routers/quality.py`
- [ ] Move `check_quality_via_service()` helper
- [ ] Register router in `main.py`

### Task 2.5: Extract API Service Router
- [ ] Move API service endpoints to `routers/api_service.py`
- [ ] Move `_call_api_service()` helper
- [ ] Register router in `main.py`

### Task 2.6: Extract Network Router
- [ ] Move network/API interception endpoints to `routers/network.py`
- [ ] Register router in `main.py`

### Task 2.7: Extract Tabs Router
- [ ] Move tab cleanup endpoints to `routers/tabs.py`
- [ ] Register router in `main.py`

### Task 2.8: Clean Up main.py
- [ ] Keep only: app initialization, startup/shutdown, health, root
- [ ] Verify all routers registered
- [ ] Test all endpoints still work

---

## 📚 Key Files to Read

1. **MAIN_PY_REFACTORING_PHASES.md** - Complete refactoring plan (all 5 phases)
2. **REFACTORING_SUMMARY.md** - Executive summary
3. **PHASE_1_COMPLETE.md** - What was done in Phase 1
4. **backend/main.py** - Current monolithic file (2,357 lines)
5. **backend/config.py** - Configuration (227 lines)

---

## 🔍 Important Context

### Current File Stats
- `backend/main.py`: 2,357 lines
- `backend/config.py`: 227 lines
- `backend/services/screenshot_service.py`: Exists (screenshot logic)

### Endpoint Groups (from main.py)
```python
# Screenshot endpoints (~400 lines)
@app.post("/api/screenshot")
@app.post("/api/screenshot/batch")
@app.post("/api/screenshot/real-browser")
# ... etc

# Document endpoints (~300 lines)
@app.post("/api/document/generate")
@app.get("/api/document/download/{filename}")
# ... etc

# Quality endpoints (~200 lines)
@app.post("/api/quality/check")
@app.post("/api/quality/batch")
# ... etc

# API Service endpoints (~150 lines)
@app.post("/api/api-service/extract")
@app.post("/api/api-service/batch")
# ... etc

# Network endpoints (~250 lines)
@app.get("/api/network/intercepted-apis")
@app.delete("/api/network/intercepted-apis")
# ... etc

# Tab endpoints (~100 lines)
@app.post("/api/tabs/cleanup")
@app.get("/api/tabs/status")
```

---

## ⚠️ Critical Rules

1. **Don't break existing functionality** - All endpoints must work exactly as before
2. **Use FastAPI APIRouter** - Each router file uses `APIRouter(prefix="/api", tags=[...])`
3. **Import dependencies correctly** - `from backend.services.screenshot_service import screenshot_service`
4. **Test after each router** - Verify endpoints still work
5. **Keep commits atomic** - One router per commit

---

## 🧪 Testing Commands

```bash
# Start backend
cd backend && python main.py

# Test health
curl http://localhost:8001/health

# Test screenshot
curl -X POST http://localhost:8001/api/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Test tabs
curl -X POST http://localhost:8001/api/tabs/cleanup
curl http://localhost:8001/api/tabs/status
```

---

## 📊 Success Criteria for Phase 2

- [ ] `backend/main.py` reduced from 2,357 to ~200 lines
- [ ] 6 router files created in `backend/routers/`
- [ ] All endpoints still work (test with curl)
- [ ] No breaking changes
- [ ] Clean imports, no circular dependencies
- [ ] All tests passing

---

## 🚀 After Phase 2

**Phase 3**: Error handling standardization
**Phase 4**: Service layer extraction  
**Phase 5**: Testing & documentation

See `MAIN_PY_REFACTORING_PHASES.md` for details.

---

## 💡 Tips for Agent Mode

- Use `gitnexus_context()` to understand function dependencies
- Use `gitnexus_impact()` before moving functions
- Use `gitnexus_detect_changes()` before committing
- Read `backend/main.py` to see current structure
- Follow the task order above for best results

---

## 🎯 Your Mission

**Start with Task 2.1**: Create the router directory structure and empty files.

Then proceed through tasks 2.2-2.8 systematically, testing after each router extraction.

**Good luck! 🚀**

