# Smart Header Filtering - Implementation Guide

## Overview

The Business Apps section now includes **smart header filtering** that automatically extracts and validates headers when users paste API data from browser DevTools, Postman, or curl commands.

## Features

### ✅ 1. **29-Header Whitelist**
Only these headers are allowed (all others are automatically filtered out):
```
accept, accept-language, applicationid, clientid, content-type, dealerid, dnt,
flattenedaecprogramsmap, locale, origin, original-tenantid, original-userid,
priority, productids, program, roleid, sec-ch-ua, sec-ch-ua-mobile,
sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site,
subapplicationid, tek-siteid, tekion-api-token, tenantname, user-agent, userid
```

**Removed headers:**
- `referer` - Not required for API calls
- `tracestate` - Optional tracking header
- `x-observe-rum-id` - Optional monitoring header
- `Cookie` - Not needed (token-based auth)

### ✅ 2. **Smart Parsing**
Automatically handles multiple input formats:

#### Browser DevTools Format:
```
General
Request URL: https://preprodapp.tekioncloud.com/api/parts/...
Request Method: PUT

Request Headers
accept: application/json
tekion-api-token: eyJhbGci...
dealerid: 7824
referer: https://example.com    ← Filtered out
x-custom: test                   ← Filtered out
```

#### curl Command Format:
```
curl 'https://api.example.com' \
  -H 'accept: application/json' \
  -H 'tekion-api-token: eyJhbGci...' \
  --data-raw '{"key":"value"}'
```

#### Clean Headers Format:
```
accept: application/json
dealerid: 7824
tekion-api-token: eyJhbGci...
```

### ✅ 3. **Replace Strategy**
When pasting new headers:
- **OLD headers are COMPLETELY REPLACED** (not merged)
- Only the newly pasted headers are kept (after filtering)
- Ensures no stale data remains

### ✅ 4. **localStorage Persistence**
- Headers are automatically saved to localStorage
- Persists across browser sessions
- Survives page reloads
- Synced with all operations (add, update, delete, bulk edit)

### ✅ 5. **Validation on Manual Add**
When manually adding a header:
- System checks if it's in the allowed list
- Shows friendly error with the full list of allowed headers
- Prevents invalid headers from being added

### ✅ 6. **Shared Across All Tiles**
- All Parts tiles use the same unified headers
- Update once, applies to all API calls
- Consistent authentication across all requests

## How to Use

### Method 1: Bulk Edit (Recommended)
1. Open **Business Apps** → **Parts**
2. Click on any tile
3. Click **Headers** tab
4. Click **📝 Bulk Edit** button
5. Paste entire DevTools Request Headers section (including noise)
6. Click **💾 Save**
7. ✅ System automatically filters to keep only the 29 allowed headers

### Method 2: Manual Edit
1. Click **Headers** tab
2. Edit values directly in the table
3. Changes auto-save to localStorage

### Method 3: Manual Add
1. Click **+ Add Header**
2. Enter header key (must be from allowed list)
3. Enter header value
4. ✅ Validated and saved

## User Experience

### Success Message Example:
```
✅ Applied 29 headers

📊 Parsed: 45 headers
✅ Kept: 29 allowed headers
❌ Filtered out: 16 non-allowed/duplicate headers
```

### Error Message Example (Invalid Add):
```
❌ Header "referer" is not in the allowed list.

Only these 29 headers are allowed:
accept, accept-language, applicationid, ...

Tip: Use the "📝 Bulk Edit" mode to paste all headers at once.
```

## Technical Implementation

### Files Modified:
1. **`frontend/src/components/BusinessApps/PartsTab.tsx`**
   - Added `ALLOWED_HEADERS` constant (29 headers)
   - Added `isAllowedHeader()` helper function
   - Added `parseAndFilterHeaders()` smart parser
   - Updated `handleSaveBulkEdit()` with filtering
   - Updated `handleAddHeader()` with validation
   - Updated `handleUpdateHeaderKey()` with validation
   - Added localStorage persistence to all header operations
   - Removed `referer` from default headers

2. **`frontend/src/components/BusinessApps/APITestingTab.tsx`**
   - Added same whitelist and validation logic
   - Updated bulk edit parser with filtering
   - Added header key validation

### Storage Key:
- `parts-unified-headers` - localStorage key for Parts Tab headers

## Testing Checklist

- [ ] Paste DevTools headers with noise (General, Request URL, etc.)
- [ ] Verify only 29 allowed headers are kept
- [ ] Check localStorage persistence (reload page)
- [ ] Try adding invalid header manually (should show error)
- [ ] Update header value (should persist)
- [ ] Delete header (should persist)
- [ ] Reset to defaults (should work)
- [ ] Execute API call with filtered headers (should work)
- [ ] Test API Testing Tab with same logic

## Benefits

✅ **User-Friendly:** Paste entire DevTools section without cleanup  
✅ **Clean Data:** Only essential headers stored  
✅ **Secure:** Prevents unwanted headers from being sent  
✅ **Efficient:** Reduces payload size  
✅ **Persistent:** Headers survive page reloads  
✅ **Consistent:** Same headers across all tiles  
✅ **Future-Proof:** Easy to update whitelist if requirements change
