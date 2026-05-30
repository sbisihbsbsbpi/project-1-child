# 🔄 Change Image Icon - Final Findings

**Date:** 2026-05-30  
**Status:** ✅ **COMPLETE - Ready for Production Integration**

---

## 🎯 **The Correct Icon:**

### **Icon Details:**
```javascript
{
  ariaLabel: "icon-switch",
  title: "Change Image",
  className: "d-flex justify-content-center templates_Image_actionButton__6mcWjcuKxF",
  location: "Appears on hover over logo with warning"
}
```

### **Selector:**
```javascript
// Primary selector (most reliable)
container.querySelector('[aria-label="icon-switch"]')

// Fallback selector
container.querySelector('[title="Change Image"]')
```

---

## 🚫 **Icons That DON'T Work:**

1. ❌ **Warning Icon** (`icon-alert1`) - Just an indicator, not clickable
2. ❌ **Remove Icon** (`icon-cross`) - Deletes logo, doesn't open selection
3. ❌ **Resize Icon** (`icon-resize`) - Only for resizing
4. ❌ **Image element** itself - No popup

---

## ✅ **Complete Working Flow:**

### **Step-by-Step:**

```python
# 1. Find logo with warning
warning_icon = page.query_selector('.templates_Image_warningIcon__hCZHMuhEmb')
sortable = warning_icon.closest('[class*="SortableItem"]')

# 2. Hover to reveal toolbar
await sortable.hover(force=True)
await asyncio.sleep(2)

# 3. Click Change Image icon (icon-switch)
change_icon = sortable.querySelector('[aria-label="icon-switch"]')
await change_icon.click()
await asyncio.sleep(3)

# 4. Popup opens: "Insert Files"
popup = page.query_selector('[role="dialog"]')

# 5. Analyze available logos
images = popup.query_selector_all('img')
for img in images:
    media_id = extract_media_id(img.src)  # regex: /([a-f0-9]{24})/
    parent = img.closest('[class*="mediaTile"]')
    is_selected = 'itemChecked' in parent.className

# 6. Select alternative logo (NOT the broken one)
BROKEN_ID = '6a0c6722864813539e4da7ae'
GOOD_ID = '6a19132b6697f36de6236fb1'  # Tilton

target_img = find_logo_by_media_id(images, GOOD_ID)
container = target_img.closest('[class*="mediaTile"]')
await container.click()

# 7. Click Insert button
insert_btn = popup.query_selector('button:has-text("Insert")')
await insert_btn.click()

# 8. ✅ Logo replaced!
```

---

## 📊 **Popup Structure:**

```
[role="dialog"] - "Insert Files"
├── Search box (input)
├── Media tiles (grid)
│   ├── Logo 1: SVG icon (default, selected)
│   ├── Logo 2: Tilton (6a19132b6697f36de6236fb1) ✅ GOOD
│   └── Logo 3: Nucar (6a0c6722864813539e4da7ae) ❌ BROKEN
└── Buttons
    ├── Cancel
    └── Insert
```

---

## 🔍 **Detection Logic:**

### **Radio Buttons:**
```javascript
// Check for radio buttons first
const radios = popup.querySelectorAll('input[type="radio"]');
if (radios.length > 0) {
    // Use radio button approach
    const checked = Array.from(radios).find(r => r.checked);
    const unchecked = Array.from(radios).filter(r => !r.checked);
    // Click unchecked[0]
}
```

### **Visual Selection (Fallback):**
```javascript
// If no radio buttons, use visual selection
const images = popup.querySelectorAll('img');
images.forEach(img => {
    const container = img.closest('[class*="mediaTile"]');
    const isSelected = container?.className.includes('itemChecked');
});
```

---

## 💡 **Key Insights:**

### **1. Media ID Extraction:**
```javascript
// Handles both formats:
// - .../media_6a0c6722864813539e4da7ae_.png (broken, has trailing _)
// - .../6a19132b6697f36de6236fb1/Tilton.png (good)

const mediaId = src.match(/([a-f0-9]{24})/)?.[1];
```

### **2. Broken Logo Identification:**
- Media ID: `6a0c6722864813539e4da7ae`
- URL has trailing underscore: `media_..._`
- Causes warning icons in templates
- **MUST AVOID** when selecting alternative

### **3. Selection State:**
```javascript
// Visual selection indicator
const isSelected = parent.className.includes('itemChecked') ||
                   parent.className.includes('selected') ||
                   parent.getAttribute('aria-selected') === 'true';
```

---

## 🎓 **Toolbar Icon Reference:**

When hovering over a logo, these icons appear:

| Icon | aria-label | title | Purpose |
|------|-----------|-------|---------|
| ❌ | `icon-cross` | - | Delete/Remove logo |
| 🔄 | `icon-switch` | **"Change Image"** | ✅ Opens media selection |
| 📏 | `icon-resize` | "Resize Image" | Resize logo |
| ⬅️ | `icon-left-align` | - | Align left |
| ↔️ | `icon-center-align` | - | Align center |
| ➡️ | `icon-right-align` | - | Align right |
| 🔗 | `icon-insert-link` | - | Add hyperlink |
| ⚠️ | `icon-alert1` | - | Warning indicator |

---

## 📝 **Integration Checklist:**

For `parallel_logo_warning_updater.py`:

- [ ] Update `detect_warnings_and_logo()` to mark logos for inspection
- [ ] Add hover step before clicking Change Image
- [ ] Replace warning icon click with `icon-switch` click
- [ ] Add popup detection and waiting logic
- [ ] Implement logo analysis (detect broken vs good)
- [ ] Add selection logic (avoid broken IDs)
- [ ] Click Insert button
- [ ] Verify logo replaced (check for warning disappearance)

---

## 🚀 **Expected Benefits:**

**vs. Remove + Re-add approach:**
- ✅ Direct replacement (no removal)
- ✅ Preserves template structure
- ✅ Access to full media library
- ✅ Can intelligently avoid broken logos
- ✅ No button state checking needed
- ✅ Fewer steps, more reliable

**Success Rate Improvement:**
- Current: ~90% (10/11 templates)
- Expected: ~100% (11/11 templates)

---

## ✅ **Test Results:**

**Script:** `test_change_image_popup.py` (temporary)  
**Template:** Service History Recap PDF  
**Success Rate:** 100% (1/1)

**Verified:**
- ✅ Change Image icon detection
- ✅ Popup opening
- ✅ Logo analysis
- ✅ Media ID extraction
- ✅ Broken logo avoidance
- ✅ Alternative selection
- ✅ Insert button click
- ✅ Replacement completion

---

**Status:** ✅ **Ready for production integration**  
**Next Step:** Update `parallel_logo_warning_updater.py` with this approach
