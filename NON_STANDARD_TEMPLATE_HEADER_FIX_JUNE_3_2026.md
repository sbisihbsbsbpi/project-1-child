# Non-Standard Template Header Fix - June 3, 2026

## Problem Identified

### Issue:
Templates with **non-standard logo structures** (e.g., sortable item images, resizable images) were being **skipped entirely** without checking if they needed a header structure added.

### Example Template:
**"Standard Appointment"** (ID: `STANDARD_APPOINTMENT_EMAIL`)
- **URL:** https://preprodapp.tekioncloud.com/templates/edit/STANDARD_APPOINTMENT_EMAIL
- **Department:** SALES
- **Structure:** Has 1 sortable item logo in body, but NO Logo 1/2 containers
- **Problem:** Script detected logo and skipped without checking #HEADER button status

---

## Root Cause Analysis

### Old Logic Flow (BROKEN):

```
Template with non-standard logos detected
    ↓
has_any_logos.get('found') = True
    ↓
Log: "Template has logos but IDs don't match hardcoded list"
Log: "Skipping to avoid duplicate header"
    ↓
Mark as "skipped" and RETURN (exit early)
    ↓
❌ NEVER checks #HEADER button status
```

### The Problem:

The script **assumed**:
> "If template has ANY logos (even in different structure), it must have a header already"

But this is **WRONG** because:
- ✅ Template can have logos in the **body/content area**
- ❌ Template may have **NO header structure** (Logo 1/2 containers don't exist)
- ❓ #HEADER button may be **ACTIVE** (not grayed), indicating header CAN be added

---

## The Fix

### New Logic Flow (FIXED):

```
Template with non-standard logos detected
    ↓
has_any_logos.get('found') = True
    ↓
Log: "Template has logos but IDs don't match hardcoded list"
Log: "Checking if template still needs a header structure..."
    ↓
Check #HEADER button opacity
    ↓
    ├─ If opacity = 1.0 (ACTIVE):
    │    ✅ Template has logos BUT no header structure
    │    ✅ ADD header with logo
    │    ✅ Mark as "success" with action "header_added_to_non_standard"
    │    ✅ Result: Template now has both body logo + header logo
    │
    └─ If opacity < 1.0 (GRAYED):
         ✅ Template already has header structure
         ✅ Skip (already correct)
         ✅ Mark as "skipped" with detailed reason
         ✅ Result: No changes needed
```

---

## Code Changes

### Location:
`logo_addition_diagnostics/temp_logo_adding_FINAL.py` lines 578-678

### Before (14 lines):
```python
if has_any_logos.get('found'):
    logger.info(f"   ⚠️  Template has logos ({has_any_logos['reason']}: {has_any_logos['count']}) but IDs don't match hardcoded list")
    logger.info(f"   ℹ️  This template uses a different structure - skipping to avoid duplicate header")
    self.results.append({
        'template': template_name,
        'id': template_id,
        'status': 'skipped',
        'reason': f"Has logos but different structure ({has_any_logos['reason']})",
        'logos_processed': 0,
        'published': False
    })
    logger.info(f"   📑 Tab kept open for verification")
    return  # ❌ Early exit without checking #HEADER button
```

### After (101 lines):
```python
if has_any_logos.get('found'):
    logger.info(f"   ⚠️  Template has logos ({has_any_logos['reason']}: {has_any_logos['count']}) but IDs don't match hardcoded list")
    logger.info(f"   📋 Checking if template still needs a header structure...")
    
    # ✅ NEW: Check #HEADER button status even for non-standard templates
    button_state = await page.evaluate("""
        () => {
            const headerBtn = document.querySelector('#HEADER');
            if (!headerBtn) return { found: false };
            
            const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
            return {
                found: true,
                opacity: opacity,
                isActive: opacity === 1.0,
                isGrayed: opacity < 1.0
            };
        }
    """)
    
    logger.debug(f"   Header button state (non-standard template): {button_state}")
    
    if button_state.get('found') and button_state.get('isActive'):
        # ✅ Header button is active - add header!
        logger.info(f"   🎯 #HEADER button is active (opacity={button_state['opacity']}) - template needs header despite having logos")
        logger.info(f"   ℹ️  Template has {has_any_logos['count']} logo(s) in body but no header structure")
        logger.info("   ➕ Adding header structure with logo...")
        
        header_added = await self._add_header_with_logo(page, logo_media_id)
        
        if header_added:
            # ... success handling
            self.results.append({
                'action': 'header_added_to_non_standard',
                'reason': f"Had {has_any_logos['count']} logo(s) but no header structure",
                # ...
            })
        else:
            # ... failure handling
    else:
        # ✅ Header button is grayed or not found - skip appropriately
        if button_state.get('found') and button_state.get('isGrayed'):
            logger.info(f"   ℹ️  #HEADER button is grayed (opacity={button_state['opacity']}) - template already has header structure")
        
        logger.info(f"   ℹ️  This template uses a different structure - skipping to avoid duplicate header")
        self.results.append({
            'status': 'skipped',
            'reason': f"Has logos but different structure ({has_any_logos['reason']}) and header already exists or cannot be added",
            # ...
        })
        return
```

---

## Impact

### Templates Affected:

All templates with **non-standard logo structures** that don't use the hardcoded Logo 1/2 container IDs:

1. **"Standard Appointment"** (STANDARD_APPOINTMENT_EMAIL)
2. **"Consumer Scheduling OTP"** (667f0befd4964026ee7b6e6e)
3. **"RO Payment Link"** (667f0befd4964026ee7b6ea4)
4. **"Service History Recap PDF"** (667f0befd4964026ee7b6ea2)
5. **"Collection Slip"** (667f0befd4964026ee7b6e9a)
6. **All CPRA templates** (Request Acknowledgement, Decline, Completion, etc.)
7. Any other templates using:
   - `sortable item images`
   - `resizable images`
   - Custom logo structures

### Before Fix:
- ❌ ALL skipped without header check
- ❌ Missed templates that needed headers

### After Fix:
- ✅ #HEADER button checked for ALL templates
- ✅ Headers added when needed
- ✅ Properly skipped when header already exists
- ✅ Detailed logging of button status

---

## New Result Types

### Success Case:
```json
{
  "status": "success",
  "action": "header_added_to_non_standard",
  "reason": "Had 1 logo(s) but no header structure"
}
```

### Skip Case:
```json
{
  "status": "skipped",
  "reason": "Has logos but different structure (sortable item images) and header already exists or cannot be added"
}
```

---

## Testing Recommendation

Re-run the script on all 40 templates to verify:

```bash
python3 logo_addition_diagnostics/temp_logo_adding_FINAL.py \
  --departments Service Parts \
  --no-publish
```

**Watch for:**
- Templates previously skipped now having headers added
- Log messages: `"🎯 #HEADER button is active - template needs header despite having logos"`
- New action type: `"header_added_to_non_standard"`

---

## Related Files

- **Script:** `logo_addition_diagnostics/temp_logo_adding_FINAL.py`
- **Detection Fixes:** `DETECTION_LOGIC_FIXES_JUNE_3_2026.md`
- **Session Summary:** `SESSION_SUMMARY_JUNE_3_2026.md`
