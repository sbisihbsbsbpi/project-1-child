# 📋 Priority Code Sync - Backend Logs Example

This document shows what you should see in your backend terminal when executing the Priority Code Sync tile.

---

## ✅ Successful Sync Example (With Deletions and Creations)

```
================================================================================
🎯 PRIORITY CODE SYNC - START
================================================================================
📋 Required codes: ['SPAC', 'STK', 'KEY', 'OVN', 'CSO']
📨 Received 31 total headers (including infrastructure)
✅ Validated 25 Tekion headers
🔑 Key headers: dealerid=7824, tenantname=f40llc, userid=e62fd11d...
🌐 Target API: https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code

────────────────────────────────────────────────────────────────────────────────
📥 STEP 1: FETCH EXISTING PRIORITY CODES
────────────────────────────────────────────────────────────────────────────────
🌐 GET https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code
📥 Response status: 200
📊 Response size: 1456 bytes
📊 Response type: <class 'dict'>
📄 Response preview: {'data': [{'id': '548999fd-78aa-4b86-b8cf-61f7c597ce1c', 'code': 'SPAC', ...
✅ Successfully fetched 7 existing priority codes
📋 Sample codes: ['SPAC', 'STK', 'OVN', 'CSO', 'CUSTOM1'] ...

────────────────────────────────────────────────────────────────────────────────
🔍 STEP 2: ANALYZE EXISTING CODES
────────────────────────────────────────────────────────────────────────────────
📋 Required codes: ['SPAC', 'STK', 'KEY', 'OVN', 'CSO']
✅ Keeping 4 required codes: ['SPAC', 'STK', 'OVN', 'CSO']
⚠️ Found 2 unwanted codes to delete: ['CUSTOM1', 'OLD_CODE']

────────────────────────────────────────────────────────────────────────────────
🗑️ STEP 3: DELETE UNWANTED CODES (SEQUENTIAL)
────────────────────────────────────────────────────────────────────────────────
🔄 Processing 2 deletions sequentially...
🗑️ [1/2] Deleting 'CUSTOM1' (ID: 548999fd...)
   🌐 PUT https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code/548999fd-78aa-4b86-b8cf-61f7c597ce1c
   📥 Response: 200
   ✅ Successfully deleted 'CUSTOM1'
🗑️ [2/2] Deleting 'OLD_CODE' (ID: a1b2c3d4...)
   🌐 PUT https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code/a1b2c3d4-e5f6-7890-abcd-1234567890ab
   📥 Response: 200
   ✅ Successfully deleted 'OLD_CODE'
📊 Delete summary: 2 succeeded, 0 failed

────────────────────────────────────────────────────────────────────────────────
🔍 STEP 4: IDENTIFY MISSING CODES
────────────────────────────────────────────────────────────────────────────────
📊 Existing active codes: ['SPAC', 'STK', 'OVN', 'CSO']
➕ Missing codes to create: ['KEY']

────────────────────────────────────────────────────────────────────────────────
➕ STEP 5: CREATE MISSING CODES (SEQUENTIAL)
────────────────────────────────────────────────────────────────────────────────
🔄 Processing 1 creations sequentially...
➕ [1/1] Creating 'KEY' (Key Order)
   🌐 POST https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code
   📥 Response: 201
   ✅ Successfully created 'KEY' (ID: 9f8e7d6c...)
📊 Create summary: 1 succeeded, 0 failed

────────────────────────────────────────────────────────────────────────────────
📊 STEP 6: FINAL SUMMARY
────────────────────────────────────────────────────────────────────────────────
📈 Operations Summary:
   • Total existing codes before: 7
   • Deleted: 2
   • Created: 1
   • Kept: 4
   • Total operations: 3
   • Failures: 0

🎯 Final state: 5 active codes
✅ Required codes: ['SPAC', 'STK', 'KEY', 'OVN', 'CSO']
🎉 SUCCESS: Sync complete: 2 deleted, 1 created, 4 kept
================================================================================
🎯 PRIORITY CODE SYNC - END
================================================================================
```

---

## ✅ Successful Sync (No Changes Needed)

```
================================================================================
🎯 PRIORITY CODE SYNC - START
================================================================================
📋 Required codes: ['SPAC', 'STK', 'KEY', 'OVN', 'CSO']
📨 Received 31 total headers (including infrastructure)
✅ Validated 25 Tekion headers
🔑 Key headers: dealerid=7824, tenantname=f40llc, userid=e62fd11d...
🌐 Target API: https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code

────────────────────────────────────────────────────────────────────────────────
📥 STEP 1: FETCH EXISTING PRIORITY CODES
────────────────────────────────────────────────────────────────────────────────
🌐 GET https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code
📥 Response status: 200
📊 Response size: 1024 bytes
📊 Response type: <class 'dict'>
📄 Response preview: {'data': [{'id': '...', 'code': 'SPAC', ...
✅ Successfully fetched 5 existing priority codes
📋 Sample codes: ['SPAC', 'STK', 'KEY', 'OVN', 'CSO']

────────────────────────────────────────────────────────────────────────────────
🔍 STEP 2: ANALYZE EXISTING CODES
────────────────────────────────────────────────────────────────────────────────
📋 Required codes: ['SPAC', 'STK', 'KEY', 'OVN', 'CSO']
✅ Keeping 5 required codes: ['SPAC', 'STK', 'KEY', 'OVN', 'CSO']
⚠️ Found 0 unwanted codes to delete: []

────────────────────────────────────────────────────────────────────────────────
🗑️ STEP 3: DELETE UNWANTED CODES (SEQUENTIAL)
────────────────────────────────────────────────────────────────────────────────
✅ No unwanted codes to delete

────────────────────────────────────────────────────────────────────────────────
🔍 STEP 4: IDENTIFY MISSING CODES
────────────────────────────────────────────────────────────────────────────────
📊 Existing active codes: ['SPAC', 'STK', 'KEY', 'OVN', 'CSO']
➕ Missing codes to create: []

────────────────────────────────────────────────────────────────────────────────
➕ STEP 5: CREATE MISSING CODES (SEQUENTIAL)
────────────────────────────────────────────────────────────────────────────────
✅ No missing codes to create - all required codes exist

────────────────────────────────────────────────────────────────────────────────
📊 STEP 6: FINAL SUMMARY
────────────────────────────────────────────────────────────────────────────────
📈 Operations Summary:
   • Total existing codes before: 5
   • Deleted: 0
   • Created: 0
   • Kept: 5
   • Total operations: 0
   • Failures: 0

🎯 Final state: 5 active codes
✅ Required codes: ['SPAC', 'STK', 'KEY', 'OVN', 'CSO']
🎉 SUCCESS: Sync complete: 0 deleted, 0 created, 5 kept
================================================================================
🎯 PRIORITY CODE SYNC - END
================================================================================
```

---

## ⚠️ Partial Success Example (Some Failures)

```
================================================================================
🎯 PRIORITY CODE SYNC - START
================================================================================
[... steps 1-3 ...]

────────────────────────────────────────────────────────────────────────────────
➕ STEP 5: CREATE MISSING CODES (SEQUENTIAL)
────────────────────────────────────────────────────────────────────────────────
🔄 Processing 2 creations sequentially...
➕ [1/2] Creating 'KEY' (Key Order)
   🌐 POST https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code
   📥 Response: 201
   ✅ Successfully created 'KEY' (ID: 9f8e7d6c...)
➕ [2/2] Creating 'OVN' (Over Night Order)
   🌐 POST https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code
   ❌ Timeout after 10s
📊 Create summary: 1 succeeded, 1 failed

────────────────────────────────────────────────────────────────────────────────
📊 STEP 6: FINAL SUMMARY
────────────────────────────────────────────────────────────────────────────────
📈 Operations Summary:
   • Total existing codes before: 4
   • Deleted: 0
   • Created: 1
   • Kept: 3
   • Total operations: 1
   • Failures: 1

🎯 Final state: 4 active codes
✅ Required codes: ['SPAC', 'STK', 'KEY', 'OVN', 'CSO']
⚠️ PARTIAL SUCCESS: Sync complete: 0 deleted, 1 created, 3 kept (1 failures)
   Failed creates: ['OVN']
================================================================================
🎯 PRIORITY CODE SYNC - END
================================================================================
```

---

## 📋 Log Features

### **Visual Structure:**
- ✅ Clear section separators with `═` and `─` lines
- ✅ Emoji indicators for different types of messages
- ✅ Indentation for sub-steps and details
- ✅ Progress counters like `[1/2]`, `[2/2]`

### **Detailed Information:**
- ✅ All HTTP endpoints and methods
- ✅ Response status codes
- ✅ Response sizes
- ✅ Sample data previews
- ✅ ID truncation for readability

### **Error Tracking:**
- ✅ Clear error messages with context
- ✅ Separate success/failure summaries
- ✅ Detailed operation counts

---

**Last Updated:** 2026-05-25
