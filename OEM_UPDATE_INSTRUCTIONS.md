# OEM ID Update Demo - Instructions

## 🎯 Target User for Demo
- **Email:** MRodriguez@mbcoralgables.com
- **New OEM ID:** UMB1190745

---

## 📋 Prerequisites

### 1. **Get Fresh Authentication Headers**

The authentication token expires after ~2 hours. You need to get fresh headers from your browser:

#### Steps:
1. Open **Chrome DevTools** (F12)
2. Go to **Network** tab
3. Navigate to Tekion: `https://preprodapp.tekioncloud.com`
4. Log in to the **dreammotorgroupllc** tenant
5. Go to any user management page
6. Find a request to `/api/userservice/u/v2/userandroles` in Network tab
7. Right-click → **Copy → Copy as cURL**

#### Required Headers:
```
tekion-api-token: <YOUR_FRESH_TOKEN>
dealerid: 7616
tenantname: dreammotorgroupllc
roleid: 7616_ISM_Admin
userid: <YOUR_USER_ID>
```

---

## 🔄 Workflow Steps

### **Step 1: List All Users**
```bash
POST https://preprodapp.tekioncloud.com/api/userservice/u/v2/userandroles
Headers: <YOUR_FRESH_HEADERS>
Body: {}
```

**Expected Response:**
```json
{
  "data": {
    "userAndRoles": [
      {
        "id": "abc-123-def",
        "email": "MRodriguez@mbcoralgables.com",
        "firstName": "...",
        "lastName": "..."
      },
      ...
    ]
  }
}
```

**Extract:** User ID for "MRodriguez@mbcoralgables.com"

---

### **Step 2: Get User Details**
```bash
GET https://preprodapp.tekioncloud.com/api/userservice/u/user-access-settings/{userId}
Headers: <YOUR_FRESH_HEADERS>
```

**Expected Response:**
```json
{
  "data": {
    "user": {
      "id": "abc-123-def",
      "email": "MRodriguez@mbcoralgables.com",
      "oemMappings": [
        {
          "complexListId": "...",
          "dealerId": "7616",
          "oemDetails": [
            {
              "complexListId": "...",
              "oem": "benz",
              "oemId": "OLD_VALUE",  // ← Current value
              "oemName": "Mercedes-Benz",
              "makeOverrideDisabled": true,
              "makeOverrides": [...]
            }
          ]
        }
      ]
    }
  }
}
```

**Extract:** Current `oemId` value

---

### **Step 3: Update OEM ID**
```bash
PUT https://preprodapp.tekioncloud.com/api/userservice/u/user-access-settings/{userId}
Headers: <YOUR_FRESH_HEADERS>
Body:
{
  "saveUserRequest": {
    ...entire user object from Step 2...
    "oemMappings": [
      {
        "complexListId": "...",  // ← PRESERVE
        "dealerId": "7616",
        "oemDetails": [
          {
            "complexListId": "...",  // ← PRESERVE
            "oem": "benz",
            "oemId": "UMB1190745",  // ← UPDATED!
            "oemName": "Mercedes-Benz",
            "makeOverrideDisabled": true,  // ← PRESERVE
            "makeOverrides": [...]  // ← PRESERVE
          }
        ]
      }
    ]
  }
}
```

**Expected Response:**
```
Status: 200 OK
```

---

## 🐍 Run Demo Script

Once you have fresh headers, update the script and run:

```bash
# Edit the script with your fresh headers
nano demo_oem_update.py

# Update these lines:
# Line 42: 'tekion-api-token': '<YOUR_FRESH_TOKEN>',
# Line 46: 'userid': '<YOUR_USER_ID>',

# Run the demo
python3 demo_oem_update.py
```

---

## ✅ Success Indicators

1. **Step 1:** Returns 100+ users
2. **Step 2:** Shows current OEM ID
3. **Step 3:** Returns 200 OK
4. **Verification:** Get user details again → oemId = "UMB1190745"

---

## ❌ Common Issues

### **Issue 1: "Found 0 users"**
- **Cause:** Token expired or wrong tenant
- **Fix:** Get fresh headers from browser

### **Issue 2: "Email not found"**
- **Cause:** Wrong tenant (needs dreammotorgroupllc, not techmotors)
- **Fix:** Log in to correct tenant

### **Issue 3: "401 Unauthorized"**
- **Cause:** Token expired
- **Fix:** Get fresh token (tokens expire after ~2 hours)

### **Issue 4: "No OEM mapping structure"**
- **Cause:** User doesn't have oemMappings field
- **Fix:** This user can't be updated (needs OEM structure first)

---

## 📊 Next Steps After Demo Success

Once the demo works for 1 user:
1. ✅ Implement Core Tab UI
2. ✅ Add batch processing (loop through CSV)
3. ✅ Add progress tracking
4. ✅ Add status updates
5. ✅ Process all 192 users

---

## 🔗 Files

- **CSV Data:** `/Users/tlreddy/Documents/project-1-child/oemexcel.csv`
- **Demo Script:** `/Users/tlreddy/Documents/project-1-child/demo_oem_update.py`
- **This Guide:** `/Users/tlreddy/Documents/project-1-child/OEM_UPDATE_INSTRUCTIONS.md`
