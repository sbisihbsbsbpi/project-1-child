# Detection Logic Fixes - June 3, 2026

## Problem Summary

The "RO Created" template (`667f0befd4964026ee7b6e76`) showed incorrect logo placements:
- ❌ Two small logos at the top (should NOT be there)
- ✅ One large logo at the bottom (correct)

### Root Causes Identified

1. **State Synchronization Issue**: Hardcoded Logo 1/2 detection ran BEFORE table-based detection, so it didn't know that Logo 1 CENTER already had a logo
2. **Sequential Processing Issue**: Loop processed LEFT→CENTER→RIGHT, adding empty LEFT before seeing that RIGHT had a logo
3. **Too Broad Detection Criteria**: Any 4-column table with empty containers was treated as a logo table (caught content/layout tables)
4. **No Guardrail Limits**: Script processed ALL 4-column tables (found 4 when only 2 were actual logo tables)

## Fixes Applied

### Fix #1: State Synchronization
**File:** `logo_addition_diagnostics/temp_logo_adding_FINAL.py`
**Lines:** 1278-1290, 1398-1419, 1494-1576

**Changes:**
- Created `globalLogoRowsWithContent` (shared state between detection systems)
- Moved table-based detection to run FIRST
- Table detection populates `globalLogoRowsWithContent` in PASS 1
- Hardcoded Logo 1/2 detection now runs AFTER and checks `globalLogoRowsWithContent` before adding containers

**Effect:** Logo 1/2 hardcoded detection now skips rows that table detection already found have logos

### Fix #2: Two-Pass Processing
**File:** `logo_addition_diagnostics/temp_logo_adding_FINAL.py`
**Lines:** 1398-1493

**Changes:**
- **PASS 1:** Scan ALL positions in ALL logo rows to find which rows have logos (any position)
- **PASS 2:** Process logos and empties (empty positions correctly skipped if row already has logo)

**Effect:** Logo 4 LEFT is now correctly skipped because Logo 4 RIGHT has a logo

### Fix #3: Stricter Logo Table Identification
**File:** `logo_addition_diagnostics/temp_logo_adding_FINAL.py`
**Lines:** 1350-1387

**Changes:**
Added validation criteria to distinguish logo tables from content tables:
- Must have at least one image OR
- Must have logo markers (`.templates_Image_imageComponent__tqwK7j9G7t` or `[class*="Image_resizable"]`) AND
- All relevant cells have `.TEXT_TEMPLATE` AND
- Table is in logo region (top 800px or bottom of page)

**Effect:** Logo Table 2 & 3 (content tables) are now correctly rejected

### Fix #4: Maximum Logo Tables Limit
**File:** `logo_addition_diagnostics/temp_logo_adding_FINAL.py`
**Lines:** 1299, 1301-1303

**Changes:**
- Added `MAX_LOGO_TABLES = 2` constant
- Table scan stops after finding 2 logo tables

**Effect:** Script won't process more than 2 logo rows (prevents excessive table processing)

## Expected Behavior After Fixes

### For "RO Created" Template:

| Table | Position | Before Fix | After Fix |
|-------|----------|------------|-----------|
| Logo Table #1 (top) | CENTER | ✅ Has logo (correct) | ✅ Has logo (correct) |
| Logo Table #1 (top) | LEFT | ❌ Script added logo | ✅ Skipped (row has logo in CENTER) |
| Logo Table #2 (content) | LEFT | ❌ Script added logo | ✅ Rejected (not a logo table) |
| Logo Table #3 (content) | LEFT | ❌ Script added logo | ✅ Rejected (not a logo table) |
| Logo Table #4 (bottom) | RIGHT | ✅ Has logo (correct) | ✅ Has logo (correct) |
| Logo Table #4 (bottom) | LEFT | ❌ Script tried to add | ✅ Skipped (row has logo in RIGHT) |

**Final Result:** Only 2 logos (top CENTER + bottom RIGHT), both already present, no additions needed ✅

## Technical Details

### Detection Flow (After Fixes):

```
1. Initialize globalLogoRowsWithContent = Set()
2. Run TABLE-BASED DETECTION (Primary)
   a. PASS 1: Scan all tables for existing logos
      - Mark logo rows with logos in globalLogoRowsWithContent
   b. PASS 2: Process logos and empties
      - Skip empty positions if row already has logo
3. Run HARDCODED Logo 1/2 DETECTION (Fallback)
   - Check globalLogoRowsWithContent first
   - Skip rows that table detection already processed
4. Run HEADER DETECTION
5. Compile all results
```

### Key JavaScript Variables:

- `globalLogoRowsWithContent`: Set of logo rows with existing logos (shared across all detection systems)
- `tableLogoRowsProcessed`: Local to table-based detection
- `hardcodedLogoRowsProcessed`: Local to hardcoded detection
- `MAX_LOGO_TABLES`: Limit on how many logo tables to process (2)

## Testing Recommendations

1. Re-run the script on "RO Created" template
2. Verify only 2 logos appear (both already correct)
3. Check that Logo Table 2 & 3 are rejected as "not logo tables"
4. Verify detection logs show proper two-pass processing
5. Test on other templates with multiple logo rows

## Files Modified

- `logo_addition_diagnostics/temp_logo_adding_FINAL.py` (Lines 1278-1576)

## Git Commits

- **Before fix:** `05fcb79` - "chore: capture detection logic before guardrail fixes (RO Created template bug analysis)"
- **After fix:** (Next commit) - "fix: implement four-layer detection guardrails to prevent incorrect logo placements"
