# Complete Flow Summary: Template List → Edit → Popup Detection

**Date**: 2026-05-30  
**Script**: `test_change_image_popup.py`  
**Branch**: `refactor/phase-1-quick-fixes`  
**Commit**: `c5a72ca`

---

## 🎯 Objective

Updated the script to execute the **complete user workflow** starting from the template list page, navigating to a template editor, and detecting the "Change Image" popup elements including radio buttons and Insert button state.

---

## 📋 Complete Flow

```
STEP 0: Template List Page
   ↓ (Navigate to /templates/list)
   
STEP 0b: Navigate to Specific Template
   ↓ (Navigate to /templates/edit/{template_id})
   ↓ (Wait 20 seconds for full load)
   
STEP 1: Find Logo with Warning
   ↓ (Detect .templates_Image_warningIcon__hCZHMuhEmb)
   
STEP 2: Hover Over Logo
   ↓ (Reveal toolbar with icons)
   
STEP 3: Click "Change Image" Icon
   ↓ (Open "Insert Files" popup)
   
STEP 4: Analyze Popup
   ↓ (Detect 11 media tiles, buttons, search box)
   
STEP 5: Hover Over Each Tile
   ↓ (Attempt to reveal radio buttons & delete icons)
   
STEP 6: Detect Insert Button
   ↓ (Check enabled/disabled state)
   
STEP 7: Change Selection (if possible)
   
STEP 8: Visual Highlighting
   ↓ (RED = selected, GREEN = available, ORANGE = broken)
```

---

## ✅ What Works

1. ✅ **Starts from template list** - No longer assumes you're already on edit page
2. ✅ **Navigates to specific template** - Uses template ID to open correct page
3. ✅ **Waits for full page load** - 20 second wait for template editor
4. ✅ **Finds logo with warning** - Detects warning icon on logos
5. ✅ **Hovers to reveal toolbar** - Shows change image icon
6. ✅ **Opens popup** - Clicks "Change Image" icon successfully
7. ✅ **Detects media tiles** - Found 11 tiles in popup
8. ✅ **Hovers over tiles** - Attempts to reveal hidden elements
9. ✅ **Detects Insert button** - Tracks enabled/disabled state
10. ✅ **Visual highlighting** - Color-codes elements for inspection

---

## ⚠️ Known Issues

1. **Radio buttons not detected on hover** - The script hovers but doesn't find radio buttons or delete icons
   - Possible causes:
     - Incorrect selectors for radio buttons
     - Radio buttons may require different hover target
     - Timing issue (hover duration too short)
     - Radio buttons may only exist on certain tile types

2. **Insert button already enabled** - Button is enabled even before selection change
   - This suggests a selection is already active (Logo #1 marked as SELECTED)

---

## 📊 Detection Results (Last Run)

```
Template ID: 667f0befd4964026ee7b6ea2 (Service History Recap PDF)

Popup Details:
- Title: Insert Files
- Radio Buttons Found: 0
- Image Count: 3 (visible)
- Media Tiles Count: 11 (total)
- Buttons: ['', '', 'Cancel', 'Insert']
- Insert Button State: 🟢 ENABLED

Logos Detected:
- Logo #1: ✅ SELECTED (80x73px, data:image/svg+xml)
- Logo #2: ⭕ Available (6a19132b6697f36de6236fb1, Tilton.png)
- Logo #3: ⭕ Available (6a0c6722864813539e4da7ae, _.png)

Hover Detection:
- Total tiles hovered: 11
- Tiles with radio buttons: 0
- Tiles with delete icons: 0
```

---

## 🔧 Next Steps

1. **Investigate radio button detection** - Why hover doesn't reveal them
2. **Try different selectors** - May need to target parent containers
3. **Increase hover duration** - May need longer hover time
4. **Test clicking tiles** - Try clicking instead of just hovering
5. **Check DOM structure** - Inspect actual HTML structure of tiles on hover

---

## 💡 Key Learnings

- Template editor requires **20+ seconds** to fully load
- Starting from template list provides **complete context** for debugging
- Visual highlighting is crucial for **manual verification**
- Radio buttons may not exist in DOM until specific interaction

---

## 📁 Related Files

- `test_change_image_popup.py` - Main script
- `logo_ignore_list.json` - List of known broken logos
- `important_elements_*.json` - Detected element snapshots
