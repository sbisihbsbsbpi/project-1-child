# 🚀 curl Command Parsing Feature

## Overview

The Business Apps (Parts Tab & API Testing Tab) now support **smart header parsing** from multiple formats, including full `curl` commands copied from browser DevTools or terminal.

---

## ✨ Supported Formats

### 1. **Browser DevTools Format** (Original)

Copy headers directly from Chrome/Firefox DevTools Network tab:

```
accept: application/json
dealerid: 7824
tekion-api-token: eyJhbGci...
tenantname: f40llc
```

### 2. **curl Command Format** (NEW!)

Copy entire `curl` commands with line continuations:

```bash
curl 'https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/void-reason/23' \
  -X 'PUT' \
  -H 'accept: application/json, text/plain, */*' \
  -H 'dealerid: 7824' \
  -H 'tekion-api-token: eyJhbGci...' \
  -b 'cookie=value' \
  --data-raw '{"active":true}'
```

### 3. **Postman Format**

```
accept: application/json
dealerid: 7824
```

### 4. **Mixed Format**

Paste headers from anywhere - the parser will extract valid headers and filter noise:

```
General
Request URL: https://example.com
accept: application/json
dealerid: 7824
```

---

## 🧠 Smart Features

### **Automatic Detection**

The parser automatically detects the input format:
- **curl command**: Uses regex-based extraction
- **DevTools/Postman**: Uses line-by-line parsing
- **Mixed**: Skips noise and extracts headers

### **Line Continuation Handling**

Handles multi-line curl commands with backslashes:

```bash
curl 'https://example.com' \
  -H 'header1: value1' \
  -H 'header2: value2'
```

### **Quote Removal**

Automatically removes quotes from curl -H flags:

```bash
-H 'accept: application/json'    → accept: application/json
-H "dealerid: 7824"              → dealerid: 7824
```

### **Noise Filtering**

Skips non-header curl flags and DevTools noise:
- HTTP method: `-X PUT`, `--request POST`
- Cookies: `-b 'cookie=value'`, `--cookie`
- Request body: `--data-raw`, `-d`, `--data-binary`
- Form upload: `-F`, `--form`
- Output: `-o`, `--output`, `-O`
- Other flags: `-v`, `--verbose`, `--compressed`, `-L`, `-i`, `-s`

---

## 🎯 Header Filtering (Whitelist)

Only **29 essential Tekion API headers** are kept. All others are filtered out:

### **Allowed Headers:**

| Category | Headers |
|----------|---------|
| **Accept** | `accept`, `accept-language` |
| **Application** | `applicationid`, `clientid`, `subapplicationid` |
| **Content** | `content-type` |
| **Dealer** | `dealerid`, `original-tenantid`, `original-userid`, `tenantname`, `userid` |
| **DNT** | `dnt` |
| **Locale** | `locale` |
| **Origin** | `origin` |
| **Priority** | `priority` |
| **Product** | `productids`, `program`, `roleid` |
| **Programs** | `flattenedaecprogramsmap` |
| **Security** | `sec-ch-ua`, `sec-ch-ua-mobile`, `sec-ch-ua-platform`, `sec-fetch-dest`, `sec-fetch-mode`, `sec-fetch-site` |
| **Site** | `tek-siteid` |
| **Token** | `tekion-api-token` |
| **User-Agent** | `user-agent` |

### **Filtered Out (Examples):**
- `referer` - Not needed for API calls
- `cookie` - Handled separately
- `tracestate`, `traceparent` - Tracking noise
- `cache-control`, `pragma` - Caching headers
- Custom tracking headers

---

## 📊 Usage Statistics

After pasting headers, you'll see detailed statistics:

```
✅ Applied 27 headers

📊 Parsed: 28 headers
✅ Kept: 27 allowed headers
❌ Filtered out: 1 non-allowed/duplicate headers
```

---

## 🔧 How to Use

### **In Parts Tab:**

1. Navigate to **Business Apps** → **Parts**
2. Click the **"📝 Bulk Edit"** button in the Headers section
3. Paste your curl command or DevTools headers
4. Click **"💾 Save"**
5. See statistics and confirmation
6. Headers are now applied to **ALL tiles** automatically

### **In API Testing Tab:**

1. Navigate to **Business Apps** → **API Testing**
2. Click **"Bulk Edit"** in the Headers section
3. Paste your curl command or headers
4. Click **"Save"** or close the dialog
5. Headers are populated in the table

---

## 🧪 Technical Implementation

### **Parsing Logic:**

```typescript
// Step 1: Detect curl command
const joinedInput = rawInput.replace(/\\\s*\n\s*/g, ' ');

if (joinedInput.trim().startsWith('curl ')) {
  // Step 2: Extract -H flags with regex
  const headerPattern = /(?:-H|--header)\s+(['"])((?:(?!\1).)*)\1/g;
  
  // Step 3: Parse each match
  while ((match = headerPattern.exec(joinedInput)) !== null) {
    const headerLine = match[2];
    // Parse key: value
    // Filter by whitelist
  }
} else {
  // Fall back to line-by-line parsing (DevTools format)
}
```

### **Files Modified:**

- `frontend/src/components/BusinessApps/PartsTab.tsx` (Line 949-1075)
- `frontend/src/components/BusinessApps/APITestingTab.tsx` (Line 129-232)

---

## ✅ Test Results

**Test Input:** Full curl command with 28 headers

**Results:**
- ✅ **Total parsed:** 28 headers
- ✅ **Kept (allowed):** 27 headers  
- ✅ **Filtered out:** 1 header (`referer`)
- ✅ **Skipped:** `-X PUT`, `-b 'cookie'`, `--data-raw '{...}'`

---

## 🎯 Benefits

1. **Faster Setup** - Copy curl directly from DevTools "Copy as cURL"
2. **No Manual Cleaning** - Automatic noise filtering
3. **Universal** - Works for all tiles (Parts & API Testing)
4. **Persistent** - Saved to localStorage
5. **Secure** - Only allows essential headers (prevents header bloat)

---

## 📚 Related Documentation

- `SMART-HEADER-FILTERING.md` - Header filtering system
- `PARTS-VOID-REASON-IMPLEMENTATION.md` - Parts tile implementation
- `DOUBLE-PERSISTENCE.md` - Data persistence strategy

---

**Last Updated:** 2026-05-25  
**Feature Status:** ✅ Production Ready
