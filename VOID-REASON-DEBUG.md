# 🔍 Void Reason Error - Debugging Guide

## Error Received

```json
{
  "status": "failed",
  "errorDetails": {
    "key": "unexpected.error"
  }
}
```

**HTTP Status:** 500 Internal Server Error  
**Tile:** Parts Void Reason (PUT request)  
**URL:** `https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/void-reason/23`

---

## 🎯 Root Cause Analysis

The Tekion API error `"unexpected.error"` is a generic error that can be caused by:

1. ❌ **Invalid ID** - The void reason ID `23` might not exist for your dealer
2. ❌ **Missing required fields** - The request body might be missing required fields
3. ❌ **Incorrect field values** - Field values might not match Tekion's validation rules
4. ❌ **Wrong structure** - The body structure might be incorrect

---

## ✅ Solution Steps

### **Step 1: Fetch Existing Void Reasons**

Before updating, you need to see what void reasons exist for your dealer.

1. **Find the new tile:** "Get Void Reasons" (🔍 icon)
2. **Execute it** to see all available void reasons
3. **Check the response** for:
   - Available IDs
   - Required fields
   - Current structure

**Expected Response:**
```json
{
  "data": [
    {
      "id": "abc-123",
      "active": true,
      "detail": {
        "reasonCode": "Customer Cancelled",
        "countInLostSale": true,
        "languages": {...}
      },
      "type": "SALES_ORDER"
    },
    ...
  ]
}
```

---

### **Step 2: Update the Tile with Correct ID**

Once you know the correct ID from Step 1:

1. **Note the ID** of the void reason you want to update
2. **Update the tile URL** in the code (if needed)
3. **Match the structure** from the GET response

---

### **Step 3: Check Backend Logs**

The backend now logs detailed request/response information:

**What to look for:**
```
🌐 Proxying PUT request to: https://preprodapp.tekioncloud.com/...
📋 Headers count: 25
📦 Body size: 123 bytes
📄 Body preview: {"active":true,"detail":{...
📥 Response: 500 (465ms)
📊 Response size: 87 bytes
❌ Error response JSON: {"status":"failed","errorDetails":{"key":"unexpected.error"}}
⚠️ Proxy request completed with error: 500 in 465.00ms
```

---

## 🛠️ Common Issues & Fixes

### **Issue 1: ID doesn't exist**

**Symptom:** `"unexpected.error"` with 500 status

**Fix:**
1. Run "Get Void Reasons" tile
2. Find the actual ID from the response
3. Update tile URL: `...void-reason/{ACTUAL_ID}`

---

### **Issue 2: Missing required fields**

**Symptom:** `"unexpected.error"` with field-specific error

**Fix:**
1. Compare your request body with the GET response structure
2. Add any missing required fields
3. Ensure all nested objects are complete

**Example - GET response shows:**
```json
{
  "id": "abc-123",
  "active": true,
  "detail": {
    "reasonCode": "Customer Cancelled",
    "countInLostSale": true,
    "languages": {
      "en_US": "Customer Cancelled"
    }
  },
  "type": "SALES_ORDER",
  "createdAt": "...",
  "updatedAt": "..."
}
```

**Your PUT body should match this structure** (excluding read-only fields like `createdAt`).

---

### **Issue 3: Incorrect field types**

**Symptom:** Type validation errors

**Fix:**
- `active`: Must be boolean (`true`/`false`, not string)
- `countInLostSale`: Must be boolean
- `type`: Must be exact string match (`"SALES_ORDER"` or `"PURCHASE_ORDER"`)
- `languages`: Can be `null` or object

---

### **Issue 4: You need to include the `id` field in PUT body**

Some Tekion APIs require the ID in both the URL AND the body.

**Fix:**
```json
{
  "id": "23",  // Add this
  "active": true,
  "detail": {
    "countInLostSale": true,
    "reasonCode": "Customer Cancelled - with Lost Sale",
    "languages": null
  },
  "type": "SALES_ORDER"
}
```

---

## 📋 Updated Tile Configuration

After running GET and finding the correct structure, update the tile:

```typescript
{
  id: 'void-reason',
  name: 'Update Void Reason',
  icon: '🚫',
  description: 'Configure void reason for sales orders',
  category: 'Parts Module',
  method: 'PUT',
  url: 'https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/void-reason/{ACTUAL_ID}',
  body: {
    id: "{ACTUAL_ID}",  // Add ID field
    active: true,
    detail: {
      countInLostSale: true,
      reasonCode: 'Customer Cancelled - with Lost Sale',
      languages: null  // Or actual language object from GET
    },
    type: 'SALES_ORDER'
  }
}
```

---

## 🧪 Testing Workflow

### **1. Diagnostic Phase:**
```
Execute "Get Void Reasons" tile
    ↓
Review response structure
    ↓
Note the ID and required fields
```

### **2. Update Phase:**
```
Update tile configuration with correct ID
    ↓
Match body structure to GET response
    ↓
Execute "Update Void Reason" tile
    ↓
Verify success (200 OK)
```

### **3. Verify Phase:**
```
Execute "Get Void Reasons" again
    ↓
Confirm your changes were applied
```

---

## 📊 What Changed

### **Frontend Changes:**
- ✅ Added "Get Void Reasons" tile for diagnostics
- ✅ Renamed "Parts Void Reason" to "Update Void Reason" for clarity

### **Backend Changes:**
- ✅ Enhanced proxy logging with request details
- ✅ Log body preview for debugging
- ✅ Log error responses with full detail
- ✅ Differentiate success vs error log levels

---

## 🎯 Next Steps

1. **Restart frontend** (should auto-reload)
2. **Restart backend** (if needed)
3. **Execute "Get Void Reasons"** tile first
4. **Review the response** to understand structure
5. **Update tile configuration** based on actual data
6. **Re-test "Update Void Reason"** tile

---

**Last Updated:** 2026-05-25
