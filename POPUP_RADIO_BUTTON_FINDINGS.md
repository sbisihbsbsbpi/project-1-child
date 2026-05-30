# 📻 Popup Radio Button & Logo Selection Investigation

**Date:** 2026-05-30  
**Finding:** ✅ **Warning icon opens popup with VISUAL selection (not radio buttons)**

---

## 🎯 **What We Discovered:**

### **1. Warning Icon Opens a Popup**
- **Action:** Click the warning icon (`.templates_Image_warningIcon__hCZHMuhEmb`)
- **Result:** Opens "Insert Files" popup (media library)
- **Popup Type:** `[role="dialog"]` or `.ant-modal`

### **2. No Radio Buttons - Uses Visual Selection**
- **Radio buttons:** ❌ NOT present in this popup
- **Selection method:** Visual indicators (CSS classes)
- **Selected indicator:** `templates_mediaTile_itemChecked__3m5oqF8t62` class on parent container

### **3. Popup Contents:**
```
Title: Insert Files
Has Radio Buttons: False
Radio Count: 0
Image Count: 3
Has Search Box: True
Buttons: ['', '', 'Cancel', 'Insert']
```

### **4. Logo Detection:**

**Logo #1 (Icon):**
- Media ID: unknown (SVG data URI)
- Size: 80x73px
- Selected: True (default icon)
- Not a dealer logo

**Logo #2 (Tilton - Good):**
- Media ID: `6a19132b6697f36de6236fb1`
- Size: 228x138px
- Selected: False
- URL: `.../6a19132b6697f36de6236fb1/Tilton.png`
- ✅ **This is the correct logo to use**

**Logo #3 (Nucar - Broken):**
- Media ID: `6a0c6722864813539e4da7ae`
- Size: 228x138px
- Selected: False
- URL: `.../6a0c6722864813539e4da7ae_.png` (note trailing `_`)
- ❌ **This is the broken logo - AVOID**

---

## 🔄 **Working Replacement Flow:**

```
1. Find logo with warning
   ↓
2. Hover to reveal toolbar
   ↓
3. Click WARNING ICON (.templates_Image_warningIcon__hCZHMuhEmb)
   ↓
4. Popup opens ("Insert Files")
   ↓
5. Detect all logos in popup
   ├─ Extract media IDs from URLs
   ├─ Identify broken logo (6a0c6722864813539e4da7ae)
   └─ Find alternative logo (6a19132b6697f36de6236fb1)
   ↓
6. Click on the alternative logo's container
   (.templates_mediaTile_* parent element)
   ↓
7. Click "Insert" button
   ↓
8. ✅ Logo replaced!
```

---

## 💻 **Key Code Patterns:**

### **Popup Detection:**
```javascript
const popup = document.querySelector('[role="dialog"]') || 
             document.querySelector('.ant-modal');
```

### **Logo Selection Detection:**
```javascript
const parent = img.closest('[class*="mediaTile"]');
const isSelected = parent?.className?.includes('itemChecked');
```

### **Media ID Extraction:**
```javascript
// Handles both formats:
// - media_/.../ 6a19132b6697f36de6236fb1/Tilton.png
// - media_6a0c6722864813539e4da7ae_.png
const mediaIdMatch = src.match(/([a-f0-9]{24})/);
const mediaId = mediaIdMatch ? mediaIdMatch[1] : 'unknown';
```

### **Logo Selection:**
```javascript
// Find target logo image
const targetImg = allImages[index];
const container = targetImg.closest('[class*="mediaTile"]');
container.click();  // Selects the logo
```

### **Insert Button Click:**
```javascript
const insertBtn = popup.querySelector('button:has-text("Insert")');
insertBtn.click();
```

---

## 📊 **Comparison: Radio Buttons vs Visual Selection**

| Feature | Radio Buttons | Visual Selection (Actual) |
|---------|---------------|---------------------------|
| **Selection State** | `radio.checked` | CSS class `itemChecked` |
| **Reliability** | ✅ High (boolean state) | ⚠️ Medium (CSS dependent) |
| **Detection** | `input[type="radio"]` | Parent container classes |
| **Click Target** | Radio element | Media tile container |
| **Used In** | Insert Header popup | Insert Files popup |

---

## 🎓 **Key Learnings:**

1. **Different popups use different selection methods:**
   - "Insert Header" popup: Radio buttons
   - "Insert Files" popup: Visual selection (CSS classes)

2. **Always check for both methods:**
   - Try radio buttons first (most reliable)
   - Fallback to visual state detection

3. **Media ID extraction must handle multiple formats:**
   - With trailing underscore: `media_ID_`
   - Without underscore: `ID/filename.png`
   - General pattern: Any 24-char hex string

4. **Known broken logo must be avoided:**
   - ID: `6a0c6722864813539e4da7ae`
   - Has trailing underscore in URL
   - Causes warnings in templates

5. **Selection order matters:**
   - Filter out broken logos first
   - Prefer known good logos (Tilton: `6a19132b6697f36de6236fb1`)
   - Only then select from remaining options

---

## ✅ **Test Results:**

**Script:** `test_change_image_popup.py`  
**Template:** Service History Recap PDF  
**Success Rate:** ✅ **100%**

**Steps Verified:**
- ✅ Warning icon click opens popup
- ✅ Popup analysis detects all logos
- ✅ Media ID extraction works
- ✅ Broken logo identified
- ✅ Tilton logo selected
- ✅ Insert button clicked
- ✅ Logo replacement complete

---

## 🚀 **Next Steps:**

1. Integrate this logic into `parallel_logo_warning_updater.py`
2. Replace the "X icon + re-add" flow with "Warning icon + select alternative"
3. Test on all 11 templates
4. Measure success rate improvement

**Expected Impact:**
- Fewer removals needed
- More direct replacement
- Better preservation of template structure
- Higher success rate

---

**Status:** ✅ **Investigation Complete - Ready for Integration**
