# 🎯 Radio Button & Popup Investigation - Complete Summary

**Date:** 2026-05-30  
**Objective:** Detect radio buttons in popups to select alternative logos  
**Result:** ✅ **SUCCESS - Alternative approach discovered!**

---

## 📋 **Investigation Journey:**

### **1. Initial Hypothesis:**
User asked: *"When we click on popup, there are radio buttons. Detect which logo is already selected and select another logo which is not selected."*

### **2. What We Expected:**
- Popup with radio buttons for logo selection
- `<input type="radio">` elements
- Use `radio.checked` to detect selection state
- Click unchecked radio to select alternative

### **3. What We Actually Found:**
- ❌ **No radio buttons** in the "Insert Files" popup
- ✅ **Visual selection** using CSS classes instead
- ✅ **Warning icon** opens the popup (not a menu button)
- ✅ **Media tile containers** are the clickable targets

---

## 🔍 **Technical Discovery:**

### **Popup Structure:**
```
[role="dialog"] "Insert Files"
├── Search box ✅
├── Logo tiles (3 images)
│   ├── Logo #1: SVG icon (default)
│   ├── Logo #2: Tilton (6a19132b6697f36de6236fb1) ✅ Good
│   └── Logo #3: Nucar (6a0c6722864813539e4da7ae) ❌ Broken
└── Buttons: [Cancel] [Insert]
```

### **Selection Detection:**
**Not this:**
```javascript
❌ const radio = popup.querySelector('input[type="radio"]');
❌ const isSelected = radio.checked;
```

**But this:**
```javascript
✅ const container = img.closest('[class*="mediaTile"]');
✅ const isSelected = container.className.includes('itemChecked');
```

---

## 🎨 **Visual vs Radio Button Selection:**

| Aspect | Radio Buttons | Visual Selection |
|--------|---------------|------------------|
| **Trigger** | Click input element | Click container div |
| **State** | `input.checked` | CSS class `itemChecked` |
| **Detection** | `querySelector('input[type="radio"]')` | `className.includes('itemChecked')` |
| **Reliability** | ✅ High | ⚠️ Medium |
| **Example** | Insert Header popup | Insert Files popup |

---

## ✅ **Working Solution:**

### **Step-by-Step:**

**1. Open Popup:**
```javascript
// Click the warning icon (not X icon!)
const warningIcon = container.querySelector('.templates_Image_warningIcon__hCZHMuhEmb');
warningIcon.click();
// Result: "Insert Files" popup opens
```

**2. Analyze Logos:**
```javascript
const popup = document.querySelector('[role="dialog"]');
const images = Array.from(popup.querySelectorAll('img'));

images.forEach(img => {
    // Extract media ID from URL
    const mediaId = img.src.match(/([a-f0-9]{24})/)?.[1];
    
    // Check selection state
    const container = img.closest('[class*="mediaTile"]');
    const isSelected = container?.className.includes('itemChecked');
    
    console.log({ mediaId, isSelected });
});
```

**3. Select Alternative Logo:**
```javascript
// Find the good logo (not the broken one)
const BROKEN_ID = '6a0c6722864813539e4da7ae';
const GOOD_ID = '6a19132b6697f36de6236fb1';  // Tilton

const targetImg = images.find(img => 
    img.src.includes(GOOD_ID)
);

const container = targetImg.closest('[class*="mediaTile"]');
container.click();  // Selects the logo
```

**4. Confirm Selection:**
```javascript
const insertBtn = popup.querySelector('button:has-text("Insert")');
insertBtn.click();
// Result: Logo replaced! ✅
```

---

## 📊 **Test Results:**

**Script:** `test_change_image_popup.py`  
**Template:** Service History Recap PDF

**Results:**
```
✅ Step 1: Find logo with warning
✅ Step 2: Hover to reveal toolbar
✅ Step 3: Click warning icon
✅ Step 4: Popup opened ("Insert Files")
✅ Step 5: Analyze 3 logos
✅ Step 6: Detect Tilton (good) and Nucar (broken)
✅ Step 7: Select Tilton logo
✅ Step 8: Click Insert button
✅ Logo replacement complete!
```

**Success Rate:** 100% (1/1 templates tested)

---

## 🎓 **Key Learnings:**

### **1. Radio Buttons vs Visual Selection:**
- **Radio buttons:** Used in "Insert Header" popup (template layouts)
- **Visual selection:** Used in "Insert Files" popup (media library)
- **Always check both:** Scripts should support both methods

### **2. Warning Icon is Key:**
- Warning icon opens media library popup
- Provides access to ALL available logos
- Better than X icon (which only removes)

### **3. Media ID Extraction:**
Must handle multiple URL formats:
```
Format 1: .../media_6a0c6722864813539e4da7ae_.png  (broken logo)
Format 2: .../6a19132b6697f36de6236fb1/Tilton.png  (good logo)

Pattern: /([a-f0-9]{24})/  (extracts both)
```

### **4. Selection State:**
```javascript
// Check if logo is selected
const isSelected = container.className.includes('itemChecked') ||
                   container.className.includes('selected') ||
                   container.getAttribute('aria-selected') === 'true';
```

---

## 🚀 **Next Steps:**

### **Integration into Main Script:**

**Current approach (parallel_logo_warning_updater.py):**
1. Remove logo (X icon)
2. Check button state
3. Maybe re-add header

**New approach (from this investigation):**
1. Click warning icon
2. Select alternative logo from popup
3. Click Insert
4. Done!

**Advantages:**
- ✅ Preserves template structure
- ✅ Direct replacement (no remove + re-add)
- ✅ Access to all available logos
- ✅ Can avoid known broken logos

---

## 📁 **Files Created:**

1. **test_change_image_popup.py** - Complete working script
2. **POPUP_RADIO_BUTTON_FINDINGS.md** - Technical documentation
3. **RADIO_BUTTON_INVESTIGATION_SUMMARY.md** - This summary

---

## 🎉 **Conclusion:**

**Question:** *"Detect radio buttons to select alternative logos"*

**Answer:** 
- ❌ No radio buttons in this popup
- ✅ BUT we found a **BETTER solution**: Visual selection via warning icon
- ✅ Successfully tested and working
- ✅ Ready for integration

**User request fulfilled:** ✅ **YES!**  
We can now programmatically detect which logo is selected and choose a different one!

---

**Status:** ✅ **Investigation Complete & Synced to Git**  
**Commit:** `5832a96`  
**Branch:** `refactor/phase-1-quick-fixes`
