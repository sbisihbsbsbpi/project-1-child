# ⚡ Priority Code Sync Feature

## Overview

The **Priority Code Sync** tile automatically manages priority codes for the Parts module, ensuring exactly 5 required codes exist:

1. **SPAC** - Back Order Part Order
2. **STK** - Stock Order
3. **KEY** - Key Order
4. **OVN** - Over Night Order
5. **CSO** - Customer Order (default)

---

## How It Works

### **Workflow:**

```
1. GET existing priority codes from Tekion API
2. Validate against required 5 codes
3. SEQUENTIALLY soft-delete unwanted codes (PUT with deleted=true)
4. SEQUENTIALLY create missing codes (POST)
5. Return detailed summary
```

### **Sequential Processing:**

- **DELETE operations:** One at a time for safety
- **CREATE operations:** One at a time to avoid race conditions
- **Total time:** ~1-2 seconds for typical sync

---

## Usage

### **Step 1: Configure Headers**

Ensure unified headers are configured in the Parts Tab with:
- `tekion-api-token` (authentication)
- `dealerid` (your dealer ID)
- `tenantname` (your tenant)
- All other 29 allowed headers

### **Step 2: Execute Sync**

1. Open **Business Apps → Parts**
2. Click **"Sync Priority Codes"** tile
3. Click **"▶ Execute"** button
4. View results in Response tab

---

## API Details

### **Backend Endpoint:**

```
POST http://localhost:8001/api/priority-code/sync
```

### **Request:**

Headers are automatically sent from unified headers state.

```json
{
  "headers": {
    "tekion-api-token": "eyJ...",
    "dealerid": "7824",
    "tenantname": "f40llc",
    ...
  }
}
```

### **Response:**

```json
{
  "success": true,
  "total_existing": 7,
  "required_codes": ["SPAC", "STK", "KEY", "OVN", "CSO"],
  "deleted_codes": [
    {
      "id": "uuid-1",
      "code": "CUSTOM1",
      "description": "Custom code"
    }
  ],
  "created_codes": [
    {
      "code": "KEY",
      "description": "Key Order",
      "id": "uuid-2"
    }
  ],
  "failed_deletes": [],
  "failed_creates": [],
  "kept_codes": ["SPAC", "STK", "OVN", "CSO"],
  "summary": "Sync complete: 2 deleted, 1 created, 4 kept"
}
```

---

## Tekion API Integration

### **GET Priority Codes:**

```
GET https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code
```

### **Soft Delete (PUT):**

```
PUT https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code/{id}

Body:
{
  "id": "uuid",
  "priorityCode": "UNWANTED",  // Note: different field name
  "description": "Description",
  "isDefault": false,           // Note: different field name
  "deleted": true
}
```

### **Create (POST):**

```
POST https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code

Body:
{
  "code": "OVN",               // Note: different field name
  "description": "Over Night Order"
}
```

---

## Error Handling

### **Partial Success:**

If some operations fail, the response includes:
- `failed_deletes`: Codes that couldn't be deleted
- `failed_creates`: Codes that couldn't be created
- `success: false` if any failures

### **Example with Failures:**

```json
{
  "success": false,
  "deleted_codes": [{"code": "CUSTOM1"}],
  "created_codes": [{"code": "KEY"}],
  "failed_creates": [
    {
      "code": "OVN",
      "status": 409,
      "error": "Code already exists"
    }
  ],
  "summary": "Sync complete: 1 deleted, 1 created, 3 kept (1 failures)"
}
```

---

## Field Name Mapping

⚠️ **IMPORTANT:** Tekion API uses different field names for GET vs PUT/POST:

| GET Response | PUT Request | POST Request |
|--------------|-------------|--------------|
| `code` | `priorityCode` | `code` |
| `default` | `isDefault` | N/A |
| `deleted` | `deleted` | N/A |

The backend handles this mapping automatically.

---

## Implementation Details

### **Backend:**
- **File:** `backend/main.py` (line 2180+)
- **Endpoint:** `/api/priority-code/sync`
- **Pattern:** Sequential async operations with httpx
- **Timeout:** 10s per operation, 30s overall

### **Frontend:**
- **File:** `frontend/src/components/BusinessApps/PartsTab.tsx` (line 237+)
- **Tile ID:** `priority-code-sync`
- **Method:** POST
- **Body:** Empty (headers in request)

---

## Benefits

✅ **Automated** - No manual validation needed  
✅ **Safe** - Sequential operations prevent race conditions  
✅ **Detailed** - Clear success/failure reporting  
✅ **Resilient** - Continues on partial failures  
✅ **Fast** - ~1-2 seconds typical execution  
✅ **Audited** - Full logging in backend

---

**Last Updated:** 2026-05-25
