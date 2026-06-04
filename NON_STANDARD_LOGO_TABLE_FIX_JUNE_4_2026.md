# Non-Standard Logo Table Detection Fix - June 4, 2026

## Critical Bug Fixed

### Problem:
The "non-standard template header addition" logic was adding headers to templates that **already had Logo 1/2 table structures**, just with non-matching container IDs. This resulted in templates having BOTH logo tables in the body AND a header with logos - creating duplicates.

### Example Templates Affected:
- **"Appointment Rescheduled - Concierge"** (ID: `667f0befd4964026ee7b6e96`) ⚠️ **User Reported**
- **"RO Payment Link"** (ID: `667f0befd4964026ee7b6ea4`)
- **"Service History Recap PDF"** (ID: `667f0befd4964026ee7b6ea2`)
- **13 other templates** (see analysis matrix below)

---

## Root Cause Analysis

### What Happened:

**Template Structure:**
```
Body:
  Logo 1 Table (3-cell, 4-cell, or 5-cell):
    - Position 1: empty
    - Position 2: empty  
    - Position 3: has logo
  
  Container IDs: NOT in hardcoded list (e.g., custom UUIDs)
```

**Script Processing (BUGGY):**

1. ✅ **JavaScript table-based detection FOUND logo tables**
   - Detected: 2 or 4 logo tables depending on template
   - Applied two-pass guardrail correctly
   - Skipped empty positions (row already has logo)

2. ✅ **JavaScript returned:** `logoTablesCount: 2` to Python

3. ❌ **Python hardcoded ID check FAILED**
   - Checked: Do container IDs match hardcoded list?
   - Result: NO match (templates use custom UUIDs)
   - Conclusion: "No Logo 1/2 containers detected"

4. ❌ **Python "non-standard template" logic triggered:**
   ```python
   if has_any_logos.get('found'):  # Resizable/sortable images detected
       if button_state.get('isActive'):  # #HEADER button active
           # Add header to template
   ```

5. ❌ **Header added despite logo tables existing!**
   - Result: Template now has BOTH logo tables AND header logos

**The Missing Check:**
```python
# Python SHOULD have checked:
if logo_tables_count > 0:
    # Don't add header - template already has logo structure!
    skip
```

---

## The Pattern

### Breakdown by Logo Table Count:

**Templates with 4 Logo Tables:**
- ✅ **13 templates** with NO extra resizable/sortable logos → SKIPPED (correct)
- ❌ **2 templates** with extra resizable logos detected → HEADER_ADDED (wrong!)

**Templates with 2 Logo Tables:**
- ✅ **1 template** (#2) with NO extra logos → SKIPPED (correct)
- ❌ **13 templates** with extra resizable logos detected → HEADER_ADDED (wrong!)

**Templates with 0 Logo Tables:**
- ✅ **9 CPRA templates** with header already (opacity=0.30) → SKIPPED (correct)
- ⚠️ **1 template** (#22) with no logo tables → HEADER_ADDED (maybe correct)

### Why the Inconsistency?

The "non-standard template" check uses `page.evaluate()` to find **any** resizable/sortable images:
```javascript
const resizableImages = document.querySelectorAll('[class*="resizable"] img');
const sortableItems = document.querySelectorAll('[class*="SortableItem"]');
```

**If these queries find images:**
- Python triggers: "Template has logos but needs header"
- **Even when those images are IN the logo tables!**

**If these queries DON'T find images:**
- Python skips (correctly assumes no action needed)

---

## The Fix - Two Changes

### Change 1: JavaScript Returns Logo Tables Count (Line 1853)

**Before:**
```javascript
return {
    logoTables: logoTables,
    logosToReplace: logosToReplace || [],
    // ...
};
```

**After:**
```javascript
return {
    logoTables: logoTables,
    logoTablesCount: logoTables.length,  // NEW: Pass count to Python
    logosToReplace: logosToReplace || [],
    // ...
};
```

**Effect:**
- ✅ Python now knows how many logo tables JavaScript found
- ✅ This information was already being calculated but not returned

---

### Change 2: Python Checks Logo Tables Count Before Adding Header (Lines 576-632)

**Before:**
```python
if has_any_logos.get('found'):
    logger.info("⚠️  Template has logos but IDs don't match hardcoded list")
    
    # Check #HEADER button status
    button_state = await page.evaluate(...)
    
    if button_state.get('found') and button_state.get('isActive'):
        # Add header structure
        header_added = await self._add_header_with_logo(...)
```

**After:**
```python
if has_any_logos.get('found'):
    logger.info("⚠️  Template has logos but IDs don't match hardcoded list")
    
    # FIX: Check if logo tables were already found
    logo_tables_count = detection_result.get('logoTablesCount', 0)
    
    if logo_tables_count > 0:
        # Template already has Logo 1/2 table structure - don't add header!
        logger.info(f"ℹ️  Template has {logo_tables_count} logo table(s)")
        logger.info(f"⏭️  Skipping header addition")
        return  # SKIP
    
    # Check #HEADER button status (only if no logo tables)
    button_state = await page.evaluate(...)
    
    if button_state.get('found') and button_state.get('isActive'):
        # Add header structure
        header_added = await self._add_header_with_logo(...)
```

**Effect:**
- ✅ If logo tables exist → Skip header addition
- ✅ Only add header if NO logo tables AND #HEADER button active
- ✅ Prevents duplicate logo structures

---

## Expected Behavior After Fix

### For "Appointment Rescheduled - Concierge" Template:

**Detection Phase:**
```
1. Table-based detection:
   ✅ Found 2 logo tables
   ✅ PASS 1: Logo 1 has logo
   ✅ PASS 2: Skip empty positions

2. Return to Python:
   ✅ logoTablesCount: 2

3. Python hardcoded check:
   ❌ IDs don't match hardcoded list

4. Python "non-standard" check:
   ✅ Found resizable images: 2
   ✅ Logo tables count: 2
   ✅ SKIP header addition (has logo tables)
```

**Final Result:**
```
✅ No header added
✅ Logo tables remain in body (correct!)
✅ No duplicate logos
```

---

## Impact

### Templates Fixed:
- ✅ **15 templates** will NO LONGER get incorrect headers added

### Templates Still Correctly Handled:
- ✅ **Templates with logo tables but no extra logos** → Still skipped
- ✅ **CPRA templates with existing headers** → Still skipped
- ✅ **Template #22 with no logo tables** → Still gets header (if needed)

### Before Fix:
- ❌ 15 templates incorrectly had headers added
- ❌ Created duplicate logo structures

### After Fix:
- ✅ All templates correctly handled
- ✅ Only templates with NO logo tables AND active #HEADER button get headers added

---

## Code Changes Summary

| Location | Lines | Change | Purpose |
|----------|-------|--------|---------|
| JavaScript return | 1853 | Added `logoTablesCount: logoTables.length` | Pass info to Python |
| Python non-standard check | 576-632 | Added logo tables count check before header addition | Prevent duplicates |

---

## Related Fixes

This fix builds on:
1. **Four-layer detection guardrails** (DETECTION_LOGIC_FIXES_JUNE_3_2026.md)
2. **Non-standard template header check** (NON_STANDARD_TEMPLATE_HEADER_FIX_JUNE_3_2026.md)
3. **Header misidentification prevention** (HEADER_MISIDENTIFICATION_FIX_JUNE_3_2026.md)

Together, these ensure:
- ✅ Logo tables are detected regardless of container IDs
- ✅ Two-pass guardrail prevents duplicates in Logo 1/2 rows
- ✅ Header detection doesn't interfere with logo table detection
- ✅ Headers are ONLY added when genuinely needed (no logo tables + no header)
