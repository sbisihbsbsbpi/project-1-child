# 🚀 Quick Start for Agent Mode

**TL;DR**: Phase 1 done ✅. Now split `backend/main.py` into 6 router files.

---

## 📍 Current State

- **Branch**: `refactor/phase-1-quick-fixes`
- **Phase 1**: Complete (bug fixes, config extraction, type hints)
- **Phase 2**: Ready to start (code organization)

---

## 🎯 Your Task

**Split `backend/main.py` (2,357 lines) into modular routers**

### Step 1: Create Structure
```bash
mkdir -p backend/routers
touch backend/routers/__init__.py
touch backend/routers/{screenshot,document,quality,api_service,network,tabs}.py
```

### Step 2: Extract Routers (One at a Time)

**Template for each router file:**
```python
from fastapi import APIRouter, HTTPException
from backend.services.screenshot_service import screenshot_service
from backend.config import settings

router = APIRouter(prefix="/api", tags=["screenshot"])

@router.post("/screenshot")
async def capture_screenshot(request_data: dict):
    # Move endpoint logic here
    pass
```

**Register in main.py:**
```python
from backend.routers import screenshot, document, quality, api_service, network, tabs

app.include_router(screenshot.router)
app.include_router(document.router)
# ... etc
```

### Step 3: Test Each Router
```bash
# After each router extraction, test it works
curl http://localhost:8001/api/screenshot
```

---

## 📋 Router Breakdown

| Router | Endpoints | Lines | Priority |
|--------|-----------|-------|----------|
| `screenshot.py` | `/api/screenshot/*` | ~400 | 1️⃣ Start here |
| `document.py` | `/api/document/*` | ~300 | 2️⃣ |
| `quality.py` | `/api/quality/*` | ~200 | 3️⃣ |
| `api_service.py` | `/api/api-service/*` | ~150 | 4️⃣ |
| `network.py` | `/api/network/*` | ~250 | 5️⃣ |
| `tabs.py` | `/api/tabs/*` | ~100 | 6️⃣ |

---

## 📚 Read These First

1. **AGENT_CONTEXT.md** ← Full context and detailed tasks
2. **MAIN_PY_REFACTORING_PHASES.md** ← Complete plan
3. **backend/main.py** ← Current code to refactor

---

## ⚠️ Critical Rules

1. ✅ **Test after each router** - Don't break existing functionality
2. ✅ **One router per commit** - Keep changes atomic
3. ✅ **Use GitNexus tools** - `gitnexus_impact()` before moving functions
4. ✅ **Follow the order** - Start with screenshot.py, end with tabs.py

---

## 🧪 Quick Test

```bash
# Start backend
cd backend && python main.py

# Test health (should always work)
curl http://localhost:8001/health

# Test after each router extraction
curl -X POST http://localhost:8001/api/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## ✅ Success = Phase 2 Complete

- [ ] 6 router files created
- [ ] `main.py` reduced to ~200 lines
- [ ] All endpoints still work
- [ ] Clean commits with good messages

---

**Start with AGENT_CONTEXT.md for full details!**

