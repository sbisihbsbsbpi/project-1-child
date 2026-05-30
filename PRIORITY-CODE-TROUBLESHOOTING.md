# 🔧 Priority Code Sync - Troubleshooting Guide

## Common Issues & Solutions

---

### ❌ Error: "No headers provided"

**Symptom:**
```json
{
  "detail": "Sync failed: 400: No Tekion headers provided. Please ensure unified headers are configured in Parts Tab."
}
```

**Cause:** Unified headers are not configured in the Parts Tab.

**Solution:**

1. **Check Headers Tab:**
   - Click the **"Headers"** section in Parts Tab
   - Verify you see headers like:
     - `tekion-api-token`
     - `dealerid`
     - `tenantname`
     - `userid`
     - etc.

2. **Add Headers if Missing:**
   - Click **"📝 Bulk Edit"** in Headers section
   - Paste your curl command with headers, OR
   - Paste headers from DevTools Network tab
   - Click **"💾 Save"**

3. **Verify Header Count:**
   - Should see "X headers • Shared across all tiles" where X ≥ 25

**Example: Adding headers via curl:**
```bash
# Paste this entire curl command in Bulk Edit:
curl 'https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code' \
  -H 'tekion-api-token: eyJ...' \
  -H 'dealerid: 7824' \
  -H 'tenantname: f40llc' \
  ...
```

The parser will automatically extract the 29 allowed headers.

---

### ❌ Error: 401 Unauthorized

**Symptom:**
```json
{
  "detail": "Tekion API error: 401 Unauthorized"
}
```

**Cause:** Invalid or expired `tekion-api-token`.

**Solution:**

1. **Get New Token:**
   - Login to Tekion preprod: https://preprodapp.tekioncloud.com
   - Open DevTools → Network tab
   - Make any API request
   - Copy new `tekion-api-token` from request headers

2. **Update Header:**
   - In Parts Tab, click individual header edit
   - Find `tekion-api-token`
   - Paste new token
   - Click save

---

### ❌ Error: "Failed to fetch priority codes"

**Symptom:**
```json
{
  "detail": "Failed to fetch priority codes: 404 Not Found"
}
```

**Cause:** Wrong dealer or tenant.

**Solution:**

1. **Verify Headers:**
   - Check `dealerid` matches your dealer
   - Check `tenantname` matches your tenant
   - Check `original-tenantid` if needed

2. **Test GET First:**
   - Try executing the GET manually:
     ```bash
     curl 'https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code' \
       -H 'tekion-api-token: YOUR_TOKEN' \
       -H 'dealerid: YOUR_DEALER_ID' \
       -H 'tenantname: YOUR_TENANT'
     ```

---

### ❌ Error: Backend not running

**Symptom:**
```
Failed to fetch
ERR_CONNECTION_REFUSED
```

**Cause:** Backend server is not running.

**Solution:**

1. **Start Backend:**
   ```bash
   cd /Users/tlreddy/Documents/project-1-child/backend
   uvicorn main:app --reload --port 8001
   ```

2. **Verify Backend:**
   ```bash
   curl http://localhost:8001/health
   ```

   Should return: `{"status":"healthy"}`

---

### ⚠️ Warning: Partial Success

**Symptom:**
```json
{
  "success": false,
  "failed_creates": [
    {"code": "OVN", "error": "Timeout after 10s"}
  ],
  "summary": "Sync complete: 2 deleted, 1 created, 4 kept (1 failures)"
}
```

**Cause:** Some operations failed (network, API errors, etc.).

**Solution:**

1. **Check Specific Errors:**
   - Look at `failed_deletes` and `failed_creates` arrays
   - Each entry shows the specific error

2. **Retry:**
   - Click Execute again
   - The sync is idempotent (safe to retry)

3. **Manual Fix:**
   - If a code keeps failing, check Tekion API directly
   - Verify the code doesn't have special constraints

---

### 🔍 Debugging Tips

#### **1. Check Backend Logs:**

When you execute the tile, watch the backend terminal for detailed logs:

```
🎯 Starting priority code synchronization...
📋 Received 28 headers from frontend
📥 Step 1: Fetching existing priority codes...
✅ Found 7 existing priority codes
⚠️ Found 2 unwanted codes to delete: ['CUSTOM1', 'OLD_CODE']
🗑️ Deleting code 'CUSTOM1' (ID: uuid-1)...
✅ Deleted 'CUSTOM1' successfully
➕ Found 1 missing codes to create: ['KEY']
➕ Creating code 'KEY'...
✅ Created 'KEY' successfully
🎉 Sync complete: 2 deleted, 1 created, 4 kept
```

#### **2. Check Frontend Logs:**

Open browser DevTools → Console tab:

```
🚀 Parts Tab: Executing Sync Priority Codes (uuid)
🌐 Parts Tab: Sending POST request to Sync Priority Codes
✅ Parts Tab: Sync Priority Codes - 200 OK (1234ms)
📥 Parts Tab: Response JSON keys: success, total_existing, deleted_codes, ...
```

#### **3. Check Network Tab:**

DevTools → Network tab → Find request to `/api/proxy-request`:

- **Request Payload:** Should show headers object with 29 headers
- **Response:** Should show sync results

---

### 📊 Expected Behavior

#### **First Run (No codes exist):**
```json
{
  "success": true,
  "deleted_codes": [],
  "created_codes": [
    {"code": "SPAC", ...},
    {"code": "STK", ...},
    {"code": "KEY", ...},
    {"code": "OVN", ...},
    {"code": "CSO", ...}
  ],
  "summary": "Sync complete: 0 deleted, 5 created, 0 kept"
}
```

#### **Subsequent Runs (All correct):**
```json
{
  "success": true,
  "deleted_codes": [],
  "created_codes": [],
  "kept_codes": ["SPAC", "STK", "KEY", "OVN", "CSO"],
  "summary": "Sync complete: 0 deleted, 0 created, 5 kept"
}
```

#### **With Unwanted Codes:**
```json
{
  "success": true,
  "deleted_codes": [
    {"code": "CUSTOM1", ...},
    {"code": "CUSTOM2", ...}
  ],
  "created_codes": [],
  "kept_codes": ["SPAC", "STK", "KEY", "OVN", "CSO"],
  "summary": "Sync complete: 2 deleted, 0 created, 5 kept"
}
```

---

### 🆘 Still Having Issues?

1. **Verify All Requirements:**
   - [ ] Backend running on port 8001
   - [ ] Frontend running on port 5173
   - [ ] Valid tekion-api-token
   - [ ] Correct dealerid and tenantname
   - [ ] At least 25 headers configured

2. **Test Components Individually:**
   - Test backend health: `curl http://localhost:8001/health`
   - Test headers: Click other tiles (void-reason, manufacturer)
   - Test Tekion API: Use curl directly

3. **Check Documentation:**
   - `PRIORITY-CODE-SYNC.md` - Feature documentation
   - `PRIORITY-CODE-IMPLEMENTATION.md` - Implementation details

---

**Last Updated:** 2026-05-25
