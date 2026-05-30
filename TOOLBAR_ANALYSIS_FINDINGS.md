# 🔍 Toolbar Analysis - Change Image Icon Investigation

**Date:** 2026-05-30  
**Finding:** ❌ **No "Change Image" icon exists in the toolbar**

---

## 🎯 **What We Discovered:**

### **Toolbar Contains Only 3 Icons:**

When hovering over a logo with warning in Service History Recap PDF template:

1. **`icon-cross`** (X button)
   - Class: `.templates_SortableItem_removeBtn__osvYZsTyqJ`
   - Aria-Label: `icon-cross`
   - Purpose: **Remove logo**

2. **`icon-resize`** (Resize button)
   - Title: "Resize Image"  
   - Aria-Label: `icon-resize`
   - Class: `.templates_Image_resizeIcon__9h37gGhXwx`
   - Purpose: Resize the image

3. **`icon-alert1`** (Warning icon)
   - Aria-Label: `icon-alert1`
   - Class: `.templates_Image_warningIcon__hCZHMuhEmb`
   - Purpose: Display warning indicator

---

## ❌ **What Does NOT Exist:**

- ❌ No "Change Image" button
- ❌ No "Replace" button
- ❌ No `icon-switch` button
- ❌ No arrow icon for changing images
- ❌ No direct replacement option

---

## ✅ **Conclusion:**

**The ONLY way to replace a broken logo is:**

1. Click **X icon** (`.templates_SortableItem_removeBtn__osvYZsTyqJ`) to remove the logo
2. Check button state after removal
3. If button grayed → Template has container structure (stop, success!)
4. If button active → Add new header/logo

---

## 🔄 **Previous Assumption (WRONG):**

We thought there might be a "Change Image" icon that would:
- Open media library popup
- Allow direct replacement without removal
- Be simpler than remove + re-add workflow

**Reality:** No such icon exists. The toolbar is simple:
- Remove (X)
- Resize
- Warning indicator

---

## 📝 **Code References:**

The Change Image approach was found in older scripts:
- `logo_replacement_automation.py` (lines 223-240)
- `auto_logo_replacement_service.py` (lines 250-267)

These might be for **different contexts** (e.g., INSERT_IMAGE components in template body, not SortableItem logos in header).

---

## ✅ **Correct Approach for SortableItem Logos:**

```python
# Step 1: Find logo with warning
warningIcon = document.querySelector('.templates_Image_warningIcon__hCZHMuhEmb')
sortableItem = warningIcon.closest('[class*="SortableItem"]')

# Step 2: Hover to reveal toolbar
await sortableItem.hover(force=True)

# Step 3: Click X (remove) button
removeBtn = sortableItem.querySelector('.templates_SortableItem_removeBtn__osvYZsTyqJ')
removeBtn.click()

# Step 4: Check button state
button_opacity = check_header_button_opacity()

if button_opacity < 1.0:
    # Grayed = Container structure exists
    return SUCCESS
else:
    # Active = Can add new header
    add_header_with_logo()
```

---

## 🎓 **Key Learning:**

**For logos in SortableItem containers (header/body zones):**
- ✅ Use X icon (remove) - this is the ONLY option
- ✅ Check button state after removal
- ✅ Respect container structure

**"Change Image" approach may apply to:**
- INSERT_IMAGE components (different structure)
- Different template types
- Body content images (not header logos)

---

**Status:** ✅ **Investigation complete - Use X icon removal approach**
