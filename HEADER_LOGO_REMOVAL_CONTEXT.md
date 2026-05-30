# 🎯 Header Logo Removal - X Icon Detection Context

**Last Updated:** 2026-05-30  
**Status:** In Progress - Debugging X icon detection on outer container  
**Branch:** refactor/phase-1-quick-fixes

---

## 📋 **Project Summary**

Building an automated system to **remove header logos** from Tekion email templates by detecting and clicking the X/delete icon that appears when hovering over the logo's **outer container**.

---

## 🔍 **The Challenge**

Header logos behave differently than body/footer logos:

| Logo Type | Hover Target | Delete Button Location |
|-----------|--------------|------------------------|
| Body/Footer | Logo image itself | Appears on logo image |
| **Header** | **Outer container (parent element)** | **Appears near container's top-right** |

**Key Issue:** Must hover on the **outer container** (not the logo) to reveal the X icon.

---

## 🏗️ **Current Architecture**

### **Detection Strategy:**

```
1. Find logo image (S3 + media_ + top < 600px)
2. Find outer container (closest TD, DIV, or parent)
3. Hover over OUTER container using Playwright
4. Wait 1.5 seconds for X icon to appear
5. Get all visible elements after hover
6. Calculate distance from container's top-right corner
7. Sort by distance, take closest 20
8. Filter by keywords: close, cross, delete, remove, times, ×
9. Click the matched X icon
```

### **Key Files:**

#### **1. `batch_header_logo_detector.py` (444 lines)**
- **Purpose:** Batch detection of header logos across templates
- **Features:**
  - Detects logos by position (top < 600px = header)
  - Checks if HEADER button is grayed out
  - Filters by SERVICE + PARTS departments
  - Generates CSV/JSON reports
- **Output:** Analysis reports showing which templates have header logos

#### **2. `find_x_icon_global.py` (217 lines)**
- **Purpose:** Find X icon by hovering and detecting new elements
- **Strategy:**
  - Get all buttons/icons BEFORE hover
  - Hover on outer container
  - Get all buttons/icons AFTER hover
  - Compare to find newly appeared elements
- **Container Detection:**
  ```javascript
  let container = logoImg.closest('td') ||       // Try table cell
                 logoImg.closest('div') ||        // Try div
                 logoImg.parentElement;           // Fallback
  ```

#### **3. `click_x_icon_template_1.py` (459 lines)**
- **Purpose:** Full workflow to click X icon
- **Features:**
  - Distance calculation from container's top-right corner
  - Keyword matching for delete patterns
  - Fallback to smallest icon near container
  - Screenshot on failure for debugging
- **Keywords Detected:**
  ```python
  ['close', 'cross', 'delete', 'remove', 'times', '×']
  ```

#### **4. `debug_x_icon_detection.py`**
- **Purpose:** Debug tool to inspect DOM ancestors
- **Features:**
  - Traverses up 5 parent levels
  - Lists all buttons/SVGs/icons in each level
  - Shows element properties (className, id, aria-label)

---

## 🎨 **Container Detection Logic**

### **Current Approach (Lines 96-100 in find_x_icon_global.py):**

```javascript
// Find outer container - go up several levels
let container = logoImg.closest('td') ||       // Try table cell
               logoImg.closest('div') ||        // Try div
               logoImg.parentElement;           // Fallback to parent
```

### **Potential Improvements Needed:**

1. **Go up more levels** - May need to go 2-3 parents up
2. **Try more selectors** - `closest('tr')`, `closest('table')`
3. **Check for specific attributes** - `[data-type]`, `[class*="element"]`

---

## 🖱️ **Hover & Detection Workflow**

### **Step 1: Mark Container**
```javascript
container.setAttribute('data-logo-container-temp', 'true');
```

### **Step 2: Playwright Hover**
```python
container = await page.query_selector('[data-logo-container-temp="true"]')
await container.hover()
await asyncio.sleep(1.5)  # Wait for X to appear
```

### **Step 3: Find X Icon**
```python
# Get all visible elements after hover
all_elements = document.querySelectorAll(
    'svg, button, i, [role="button"], [class*="icon"], [data-action]'
)

# Calculate distance from container's top-right corner
distance = sqrt(
    (rect.top - containerRect.top)^2 + 
    (rect.left - containerRect.right)^2
)

# Sort by distance, take closest 20
candidates = sorted_by_distance[:20]
```

---

## 🎯 **X Icon Detection Patterns**

### **Attributes to Check:**

```python
# Check in order of priority:
1. className     # e.g., "icon-close", "delete-btn"
2. ariaLabel     # e.g., aria-label="Delete"
3. title         # e.g., title="Remove"
4. innerHTML     # e.g., <svg>×</svg>
5. dataAction    # e.g., data-action="delete"
```

### **Keywords:**
```python
keywords = ['close', 'cross', 'delete', 'remove', 'times', '×', 'trash']
```

### **Size Heuristics:**
```python
# X icons are typically small
if width <= 32 and height <= 32 and distance < 200:
    # Likely the X icon
```

---

## 📊 **Current Status**

### **What's Working:**
✅ Logo detection (S3 images with media_ in header)  
✅ Container detection (TD/DIV/parent)  
✅ Playwright hover on container  
✅ Keyword matching for X icon  
✅ Distance calculation from top-right corner  

### **What's Being Debugged:**
🔍 Which parent level is the correct container?  
🔍 Is 1.5s wait time sufficient?  
🔍 Should we check other corner positions?  
🔍 Are there additional keyword patterns needed?  
🔍 Visibility checks (opacity, display, z-index)?  

---

## 🗂️ **Generated Reports**

Located in project root:

```
header_logo_analysis_YYYYMMDD_HHMMSS.csv
header_logo_analysis_YYYYMMDD_HHMMSS.json
```

**Contains:**
- Template ID & name
- Departments
- Header grayed out status
- Logo count (header, top, bottom)
- Logo URLs

---

## 🚀 **Next Steps**

1. **Test on specific template** to see X icon in DOM inspector
2. **Adjust container detection** if needed (go up more levels)
3. **Verify X icon selectors** match actual DOM structure
4. **Add more keyword patterns** if current ones miss the X icon
5. **Implement visibility filters** (check computed opacity/display)
6. **Add retry logic** with different wait times

---

## 💡 **Usage Commands**

```bash
# Batch analyze all SERVICE + PARTS templates
python3 batch_header_logo_detector.py

# Find X icon globally after hover
python3 find_x_icon_global.py

# Full workflow: detect + click X icon
python3 click_x_icon_template_1.py

# Debug DOM structure
python3 debug_x_icon_detection.py
```

---

## 📝 **Important Notes**

- Header logos are at `top < 600px`
- X icon appears ONLY on hover (not always visible)
- Container hover is KEY (not logo hover)
- Distance from top-right corner is primary filter
- Keyword matching is secondary filter
- Small size (≤32px) is tertiary filter

---

**End of Context Document**
