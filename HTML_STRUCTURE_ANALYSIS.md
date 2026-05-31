# 🔍 Template HTML Structure Analysis

## Document Purpose
Analysis of the raw HTML structure from `scroll template.txt` to identify patterns for dynamic logo container detection.

---

## 📋 Key Findings

### **1. Logo 1/2 Container Structure**

#### **Container Wrapper Class:**
```css
.templates_SortableItem_elementContainer__mqxpcPKqc1
```

This class wraps ALL sortable elements in the template, including:
- Logo containers (LEFT/CENTER/RIGHT positions)
- Text blocks
- Buttons
- Headers
- Layouts

#### **Logo 1 Container (Found in First Table):**

**Structure Pattern:**
```html
<table width="100%" border="0" cellspacing="0" cellpadding="0">
  <tbody>
    <tr>
      <!-- Logo 1 LEFT -->
      <td>
        <div class="templates_SortableItem_elementContainer__mqxpcPKqc1">
          <div id="6f0b8570-c4dc-45bd-b746-40e3af9af3bb">
            <div class="TEXT_TEMPLATE" contenteditable="true">
              <!-- Empty or has content -->
            </div>
          </div>
        </div>
      </td>
      
      <!-- Logo 1 CENTER -->
      <td>
        <div class="templates_SortableItem_elementContainer__mqxpcPKqc1">
          <div class="templates_SortableItem_elementSelected__7BJ2ftVwa4">
            <!-- Has image -->
            <div class="templates_Image_imageComponent__tqwK7j9G7t">
              <div class="templates_Image_resizable__ke4cWfggP1">
                <img src="Tilton.png" />
              </div>
            </div>
          </div>
        </div>
      </td>
      
      <!-- Logo 1 RIGHT -->
      <td>
        <div class="templates_SortableItem_elementContainer__mqxpcPKqc1">
          <div id="7653caa9-31b7-4e2b-8233-f0bda43672ea">
            <div class="TEXT_TEMPLATE" contenteditable="true">
              <!-- Empty -->
            </div>
          </div>
        </div>
      </td>
      
      <!-- Extra column -->
      <td>
        <div id="faeb0bb6-9307-4ec9-9a7b-ba46c275fdce">
          <!-- Empty -->
        </div>
      </td>
    </tr>
  </tbody>
</table>
```

**Key Pattern:**
- **Table with 4 `<td>` columns** (not 3!)
- First 3 columns = LEFT/CENTER/RIGHT positions
- 4th column = Unknown purpose (possibly spacer)

---

### **2. Logo 2 Container (Found in Second Table)**

**Structure Pattern:**
```html
<table width="100%" border="0" cellspacing="0" cellpadding="0">
  <tbody>
    <tr>
      <!-- Logo 2 LEFT -->
      <td>
        <div id="9fa2920b-10f8-48d2-9947-b014398d21be">
          <div class="TEXT_TEMPLATE" contenteditable="true">
            <!-- Empty -->
          </div>
        </div>
      </td>
      
      <!-- Middle empty column -->
      <td>
        <div id="404e76cc-2740-4cf8-9b0b-4ec170a8d71f">
          <!-- Empty -->
        </div>
      </td>
      
      <!-- Logo 2 CENTER (or RIGHT?) -->
      <td>
        <div class="templates_SortableItem_element__jTMuD11Qhm">
          <div class="templates_Image_imageComponent__tqwK7j9G7t">
            <div class="templates_Image_resizable__ke4cWfggP1">
              <img src="Tilton.png" />
            </div>
          </div>
        </div>
      </td>
      
      <!-- Another empty column -->
      <td>
        <div id="7706f5af-b4d6-4910-a809-2242bb9e593f">
          <!-- Empty -->
        </div>
      </td>
    </tr>
  </tbody>
</table>
```

**Key Pattern:**
- **Table with 4 `<td>` columns**
- Logo 2 structure mirrors Logo 1
- Image at 3rd position (CENTER or RIGHT based on alignment)

---

## 🎯 Detected Container IDs

### **Logo 1 Containers:**
```javascript
LEFT:   "6f0b8570-c4dc-45bd-b746-40e3af9af3bb"  ✅ MATCHES hardcoded
CENTER: "7653caa9-31b7-4e2b-8233-f0bda43672ea"  ✅ MATCHES hardcoded
RIGHT:  (not explicitly shown, likely empty)
Extra:  "faeb0bb6-9307-4ec9-9a7b-ba46c275fdce"  ❓ Unknown
```

### **Logo 2 Containers:**
```javascript
LEFT:   "9fa2920b-10f8-48d2-9947-b014398d21be"  ✅ MATCHES hardcoded
Middle: "404e76cc-2740-4cf8-9b0b-4ec170a8d71f"  ❓ Unknown  
RIGHT:  "7706f5af-b4d6-4910-a809-2242bb9e593f"  ❓ Unknown
```

**⚠️ Issue:** Logo 2 CENTER ID doesn't appear in this HTML dump!
- Expected: `983932ae-d79a-40fe-a9ba-df07c9beee47`
- Not found in the HTML

---

## 🔧 Dynamic Detection Strategy

### **Approach 1: Detect Logo Containers by Table Structure**

**Detection Logic:**
```javascript
// Find all tables with exactly 4 columns
const logoTables = Array.from(document.querySelectorAll('table[width="100%"]')).filter(table => {
    const rows = table.querySelectorAll('tr');
    if (rows.length === 0) return false;
    
    const firstRow = rows[0];
    const cells = firstRow.querySelectorAll('td');
    
    // Logo containers have 4 <td> columns
    return cells.length === 4;
});

// For each logo table, check each column for:
// 1. Empty TEXT_TEMPLATE (empty position)
// 2. Image component (has logo)
// 3. Warning icon (needs replacement)
```

### **Approach 2: Detect by Parent Container Depth**

**Pattern Observed:**
Logo containers are deeply nested:
```
.templates_TemplateMart_editorSection__5mDytFem7Y
  └─ .sortableContainer
      └─ table (4 columns)
          └─ tr
              └─ td (x4)
                  └─ .templates_SortableItem_elementContainer__mqxpcPKqc1
```

### **Approach 3: Detect by Image Component Classes**

**Image Detection Classes:**
```css
.templates_Image_imageComponent__tqwK7j9G7t    /* Main image wrapper */
.templates_Image_resizable__ke4cWfggP1        /* Resizable container */
.templates_Image_draggableFalse__jANewuXF34   /* Image element */
.templates_Image_resizeIcon__9h37gGhXwx       /* Resize handle */
```

---

## ✅ Recommended Enhancement

### **Phase 1: Validate Hardcoded IDs Still Work**
Keep current detection but add fallback if IDs not found.

### **Phase 2: Add Table-Based Detection**
```python
async def _detect_logo_tables(self, page: Page) -> dict:
    """
    Detect Logo 1/2 containers by table structure instead of hardcoded IDs
    """
    return await page.evaluate("""
        () => {
            const tables = Array.from(document.querySelectorAll('table[width="100%"]'));
            const logoTables = [];
            
            tables.forEach((table, idx) => {
                const rows = table.querySelectorAll('tr');
                if (rows.length === 0) return;
                
                const firstRow = rows[0];
                const cells = firstRow.querySelectorAll('td');
                
                // Logo containers have 4 columns
                if (cells.length === 4) {
                    const positions = [];
                    
                    cells.forEach((cell, cellIdx) => {
                        const hasImage = cell.querySelector('.templates_Image_imageComponent__tqwK7j9G7t');
                        const hasWarning = cell.querySelector('.templates_Image_warningIcon__hCZHMuhEmb');
                        const isEmpty = !hasImage && cell.querySelector('.TEXT_TEMPLATE');
                        
                        positions.push({
                            index: cellIdx,
                            alignment: cellIdx === 0 ? 'LEFT' : cellIdx === 1 ? 'CENTER' : cellIdx === 2 ? 'RIGHT' : 'EXTRA',
                            hasImage: !!hasImage,
                            hasWarning: !!hasWarning,
                            isEmpty: !!isEmpty
                        });
                    });
                    
                    logoTables.push({
                        tableIndex: idx,
                        positions: positions
                    });
                }
            });
            
            return logoTables;
        }
    """)
```

---

## 🚨 Critical Observations

1. **Logo 1 CENTER has image** in this HTML dump (Tilton.png already inserted)
2. **Logo 2 has image at 3rd column** (CENTER or RIGHT position unclear)
3. **4-column structure** instead of expected 3-column
4. **Some container IDs don't match** the hardcoded list

### **This Explains Why:**
- "Service History Recap PDF" was being skipped
- Detection was failing for templates with different container IDs
- Need more robust detection beyond hardcoded UUIDs

---

## 📊 Next Steps

1. ✅ Document this structure analysis
2. 🔄 Implement table-based detection as fallback
3. 🔄 Test on multiple templates to confirm pattern
4. 🔄 Add alignment detection based on column index
5. 🔄 Sync findings to git
