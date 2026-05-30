# 🚀 Quick Start Guide: OEM ID Update Feature

## 📍 **How to Access**

1. **Start the app:**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Navigate to feature:**
   - Open: http://localhost:5173
   - Click: **Business Apps** (in main menu)
   - Click: **Core** tab
   - You'll see: **🔑 OEM ID Update** interface

---

## 📝 **Step-by-Step Usage**

### **STEP 1: Get Your Headers**

**Option A: From Browser DevTools (Recommended)**

1. Open Tekion in Chrome/Edge
2. Open DevTools (F12)
3. Go to **Network** tab
4. Make any request to Tekion
5. Right-click the request → **Copy** → **Copy as cURL**
6. Paste the entire cURL command into Step 1

**Option B: Paste Headers Directly**

Extract these from your browser session:
```
dealerid:7619
tekion-api-token:eyJhbGciOiJIUzI1NiJ9...
tenantname:dreammotorgroupllc
userid:4f41b4ee-ff61-4826-8532-6fd91998b7de
```

**Click:** 🔍 Detect Headers

**Expected Result:** Green box shows detected headers ✅

---

### **STEP 2: Prepare Your CSV File**

**CSV Format:**
```csv
oemId,email
UMB1191975,Maria.Caso@mbcutlerbay.com
UMB1196056,Marc.Barratteau@mbcutlerbay.com
UMB1200478,Sarahi.Batista@mbcutlerbay.com
```

**Requirements:**
- Must have header row
- Must have columns for email and oemId (names can vary)
- Supported formats: `.csv`, `.xlsx`, `.xls`

**Upload Methods:**
- **Drag & Drop:** Drop file onto upload zone
- **Click to Browse:** Click the zone → select file

**Expected Result:** Green box shows detected columns ✅

---

### **STEP 3: Start Batch Update**

**Click:** 🚀 Start Batch Update

**Confirmation Dialog:**
```
🚀 Start batch update for 154 users?

Dealer ID: 7619
This will update OEM IDs in Tekion.

Continue?
```

**Click:** OK

---

### **STEP 4: Monitor Progress**

**You'll see:**

1. **Progress Bar:** Visual indicator (0% → 100%)
2. **Statistics:**
   - Total: 154
   - Success: 138 (Created: 106, Updated: 32)
   - Failed: 16
3. **Live Logs:**
   ```
   [1/154] Maria.Caso@mbcutlerbay.com
      ✅ Updated (EXISTING): UMB1191975 → UMB1191975

   [2/154] Marc.Barratteau@mbcutlerbay.com
      ✅ Created: [NONE] → UMB1196056

   [17/154] Yuclant.Cabrera@mbcutlerbay.com
      ❌ Not found
   ```

---

## 🎯 **Sample Test (Using Real Data)**

**You already have the test data ready!**

### **Test File: `oemexcel_7619.csv`**
Location: `/Users/tlreddy/Documents/project-1-child/oemexcel`

**Sample Headers (Store 7619):**
```
dealerid:7619
tekion-api-token:eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI0ZjQxYjRlZS1mZjYxLTQ4MjYtODUzMi02ZmQ5MTk5OGI3ZGUiLCJpYXQiOjE3Nzk4Njk0NjksInN1YiI6IjRmNDFiNGVlLWZmNjEtNDgyNi04NTMyLTZmZDkxOTk4YjdkZSIsImlzcyI6IkxvZ2luU2VydmljZSIsInVubG9ja0FjY291bnQiOmZhbHNlLCJub3VuY2UiOiI0NGE3MGZhNS1mMTEyLTRlYWUtYWVhNC03ZDA0OTNhMmUzM2YiLCJvcmlnaW5hbFVzZXJJZCI6ImZlM2EzMzMzLWM5YWQtNDlmZC1iZWY3LTc5ZWFjYWRkYzFkNSIsIm9yaWdpbmFsVGVuYW50SWQiOiJ0ZWNobW90b3JzIiwidXNlcklkIjoiNGY0MWI0ZWUtZmY2MS00ODI2LTg1MzItNmZkOTE5OThiN2RlIiwiZW1haWwiOiJpc21AZHJlYW1tb3Rvcmdyb3VwbGxjLmNvbSIsImV4cCI6MTc3OTg3NzI0NX0.puUiH2lZF0x8dOboqzaLNphXgaigeaBp-Dwi02rrSao
tenantname:dreammotorgroupllc
userid:4f41b4ee-ff61-4826-8532-6fd91998b7de
applicationid:ARC_NA
clientid:web
```

**Expected Results:**
- Total: 154 users
- Success: 138 (89.6%)
- Failed: 16 (emails not found)

---

## ⚠️ **Important Notes**

### **Token Expiry**
- Tekion tokens expire after ~2 hours
- If you get 401/403 errors, get fresh headers from browser

### **Dealer ID Verification**
- The system ONLY updates the dealer specified in headers
- Multi-dealer users are handled correctly
- Other dealers' data is preserved

### **Rate Limiting**
- 100ms delay between each user update
- For 154 users: ~15 seconds + API time (~3 minutes total)

### **Error Handling**
- Failed updates don't stop the batch
- Each error is logged with reason
- Common errors:
  - "Email not found" - User doesn't exist in Tekion
  - "GET failed: 401" - Token expired
  - "PUT failed: 403" - Insufficient permissions

---

## 🐛 **Troubleshooting**

### **"Headers validation failed"**
- Check that `dealerid` and `tekion-api-token` are present
- Ensure dealer ID is numeric
- Verify token starts with "eyJ"

### **"Could not detect email column"**
- CSV must have a column named "email" (case-insensitive)
- Or contains "mail", "user", "username"

### **"Could not detect OEM ID column"**
- CSV must have a column named "oemId" or "oemid"
- Or named "id", "oem_id", "oem-id"

### **"CSV has too many rows"**
- Maximum: 1000 rows per batch
- Split large files into smaller batches

### **API Errors During Batch**
- Check browser console for details
- Verify token is still valid
- Check network connectivity

---

## 📞 **Need Help?**

Check the detailed documentation:
- **Implementation Guide:** `OEM_ID_UPDATE_UI_IMPLEMENTATION.md`
- **Python Script (Reference):** `batch_oem_update_7619.py`
- **Previous Batch Report:** `BATCH_7619_FINAL_REPORT.md`

---

## ✅ **Success Checklist**

Before starting your batch:

- [ ] Headers detected and validated (green box in Step 1)
- [ ] CSV uploaded and parsed (green box in Step 2)
- [ ] Token is fresh (< 2 hours old)
- [ ] CSV has correct columns (email and oemId)
- [ ] Dealer ID matches your target store
- [ ] You've reviewed the confirmation dialog

**Then click 🚀 Start Batch Update and watch the magic happen!** 🎉
