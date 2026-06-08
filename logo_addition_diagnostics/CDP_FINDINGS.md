# CDP Browser Inspection Findings
## Date: 2026-06-08

## Summary
Used Chrome DevTools Protocol (CDP) to inspect 31 open browser tabs containing template editor pages. This investigation revealed critical information about why logo validation wasn't working as expected.

---

## Key Findings

### 1. ✅ Logo Detection IS Working
- **31 template tabs** inspected
- **Green borders** visible on detected dealer logos
- **Pink borders** visible on UI icons (correctly filtered out)
- **Detection count**: Most templates have 2 green-bordered logos

### 2. 🐛 The Filename Problem

#### Most Common Logo Detected:
```
Screenshot_2022-02-10_at_5.25.15_PM.png
```

This appears in **~24 out of 31 tabs** - indicating it's a **default/placeholder logo** being used across multiple templates!

#### Filename Extraction Issues:
Many image URLs have query parameters (AWS S3 signed URLs):
```
csm_HEADER_22de7ed3a8.jpeg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=...&X-Amz-Signature=...
```

The current filename extraction:
```javascript
imageFilename: img && img.src ? img.src.split('/').pop() : null
```

This returns the **entire filename WITH query parameters**, e.g.:
```
csm_HEADER_22de7ed3a8.jpeg?X-Amz-Algorithm=AWS4-HMAC-SHA256&...
```

Instead of the clean filename:
```
csm_HEADER_22de7ed3a8.jpeg
```

---

## Tab-by-Tab Breakdown

### Templates with `Screenshot_2022-02-10_at_5.25.15_PM.png` (24 tabs)
These templates all have the **same placeholder logo** - indicating they likely need logo updates!

**Sample tabs:**
- Tab 1: `6a0dc5fb62ae8d1a351df028`
- Tab 2: `6a0dc5fb62ae8d1a351df050`
- Tab 6: `6a0dc5fb62ae8d1a351df076`
- Tab 8: `6a0dc5fb62ae8d1a351df074`
- ... (20 more)

### Templates with Different Logos (7 tabs)

**Tab 4, 9:** `csm_HEADER_22de7ed3a8.jpeg` (with query params)
**Tab 5:** `cad27e6d-3a96-4bdb-94a9-29aa09bc6a60.jpeg` (with query params)
**Tab 7:** `order.png` (with query params)
**Tab 31:** `646466ff1283940007cfa58e_.png` (with query params)

### Templates with Only UI Icons (1 tab)

**Tab 14:** Only pink-bordered icons (no dealer logos)
- `icon-map.png`
- `icon-inbound-call-outlined.png`

---

## Why Validation Didn't Run

### Theory 1: ❌ Filename Mismatch Due to Query Parameters

**JavaScript returns:**
```javascript
imageFilename: "csm_HEADER_22de7ed3a8.jpeg?X-Amz-Algorithm=..."
```

**Media library has:**
```
csm_HEADER_22de7ed3a8.jpeg
```

**Validation check:**
```python
if logo_filename not in available_filenames:  # ❌ FAILS!
```

---

## Theory 2: ⚠️ Placeholder Logo Detection

The file `Screenshot_2022-02-10_at_5.25.15_PM.png` appears in **77% of templates** (24/31).

**Possible scenarios:**
1. This is a **default placeholder** logo that ships with templates
2. It **might be in the media library** (making validation pass)
3. Script **correctly detected** it exists, so no action needed

---

## Advantages of CDP Inspection

### ✅ What We Learned:
1. **Real-time state**: Can see exactly what's rendered in browser
2. **Visual confirmation**: Green/pink borders prove detection works
3. **Actual filenames**: Can extract the exact data JavaScript sees
4. **No re-runs needed**: Inspect existing tabs without re-executing script
5. **Multi-tab analysis**: Scanned 31 tabs in one run

### ✅ CDP Advantages Over Log Files:
| Capability | Log Files | CDP |
|------------|-----------|-----|
| See visual highlights | ❌ No | ✅ Yes |
| Extract current DOM state | ❌ No | ✅ Yes |
| Query live JavaScript | ❌ No | ✅ Yes |
| No re-run required | ❌ Need re-run | ✅ Instant |
| Inspect multiple tabs | ❌ Sequential | ✅ Parallel |

---

## Recommended Fixes

### Fix 1: Clean Query Parameters from Filenames

**Current code (line 1879):**
```javascript
imageFilename: img && img.src ? img.src.split('/').pop() : null,
```

**Proposed fix:**
```javascript
imageFilename: img && img.src ? img.src.split('/').pop().split('?')[0] : null,
```

This will strip `?X-Amz-Algorithm=...` from filenames.

---

### Fix 2: Add Debug Logging for Validation

**Add to line 802-814:**
```python
logo_filename = logo.get('imageFilename', '')
logger.debug(f"   Validating logo: '{logo_filename}'")

if logo_filename:
    # Check if filename has query params (shouldn't, but log if it does)
    if '?' in logo_filename:
        logger.warning(f"   ⚠️  Logo filename has query params: {logo_filename}")
        clean_filename = logo_filename.split('?')[0]
        logger.info(f"   Cleaned to: {clean_filename}")
        logo_filename = clean_filename
    
    if logo_filename not in available_filenames:
        logger.warning(f"   ⚠️  Logo '{logo_filename}' NOT in media library!")
```

---

## Next Steps

1. ✅ **Apply Fix 1** - Strip query parameters from filenames
2. ⏳ **Test on one template** - Verify validation runs correctly
3. ⏳ **Check if `Screenshot_2022-02-10_at_5.25.15_PM.png` is in media library**
4. ⏳ **Re-run script** - Should now validate all 24 templates with this logo
5. ⏳ **Monitor logs** - Confirm validation section runs and reports results

---

## Conclusion

✅ **Logo detection works perfectly** (green borders prove it)
⚠️ **Filename validation likely broken** due to query parameter issue
🔧 **Simple fix available** - strip query params before validation

The CDP inspection was invaluable for understanding the actual browser state!
