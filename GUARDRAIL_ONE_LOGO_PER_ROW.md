# 🛡️ Guardrail: One Logo Per Row

**Date:** June 2, 2026  
**File:** `logo_addition_diagnostics/temp_logo_adding_FINAL.py`

---

## 🎯 **Purpose**

Ensure that each logo row (Logo 1, Logo 2, Logo 3, etc.) gets **ONLY ONE LOGO**, regardless of alignment (LEFT, CENTER, or RIGHT).

### ❌ **Problem Before Guardrail**

The system would process multiple containers from the same logo row:

```
Logo 1 CENTER - Has warning → Replace logo ✅
Logo 2 LEFT   - Empty       → Insert logo ❌ (unwanted)
Logo 2 CENTER - Empty       → Insert logo ❌ (unwanted)
```

**Result:** Logo 2 ends up with 2 logos (LEFT + CENTER) when it should have only 1.

---

## ✅ **Solution: Three-Layer Guardrail**

### **Layer 1: JavaScript Detection (Hardcoded IDs)**
**Location:** Lines 1255-1313

```javascript
// Track which logo rows have been processed
const logoRowsProcessed = new Set(); // e.g., 'Logo 1', 'Logo 2'

containerIds.forEach((id, idx) => {
    const logoRow = containerName.split(' ').slice(0, 2).join(' '); // "Logo 1"
    
    // Only add ONE empty container per logo row
    if (isEmpty && !logoRowsProcessed.has(logoRow)) {
        emptyContainers.push({...});
        logoRowsProcessed.add(logoRow); // ✅ Mark as processed
    }
    
    // Also track rows that already have images
    if (hasImage) {
        logoRowsProcessed.add(logoRow);
    }
});
```

### **Layer 2: JavaScript Detection (Table-Based)**
**Location:** Lines 1386-1466

```javascript
// Track which logo rows have been processed
const tableLogoRowsProcessed = new Set();

logoTables.forEach((logoTable, tableIdx) => {
    const logoRow = `Logo ${tableIdx + 1}`;
    
    // Only process if logo row hasn't been handled yet
    if (!tableLogoRowsProcessed.has(logoRow)) {
        // Add logo to replace or empty container
        tableLogoRowsProcessed.add(logoRow); // ✅ Mark as processed
    }
});
```

### **Layer 3: Python Processing**
**Location:** Lines 692-726, 728-766, 767-797

```python
# Track which logo rows have been processed
processed_logo_rows = set()

for logo_item in logos_to_replace:
    logo_row = ' '.join(logo_name.split()[:2])  # "Logo 1"
    
    # GUARDRAIL: Skip if already processed
    if logo_row in processed_logo_rows:
        logger.info(f"⏭️ Skipping {logo_name} - {logo_row} already has a logo")
        continue
    
    # Process logo...
    processed_logo_rows.add(logo_row)  # ✅ Mark as processed
```

---

## 📊 **How It Works**

### **Example 1: Logo with Warning**

**Template has:**
- Logo 1 CENTER - Has warning icon ⚠️
- Logo 2 LEFT   - Empty
- Logo 2 CENTER - Empty

**Processing Flow:**

1. **Detection Phase (JavaScript):**
   - Logo 1 CENTER has warning → Add to `logosToReplace`
   - Logo 2 LEFT is empty → Add to `emptyContainers`
   - Logo 2 CENTER is empty → ⏭️ **SKIPPED** (Logo 2 already processed)
   - **Result:** `logosToReplace = [Logo 1 CENTER]`, `emptyContainers = [Logo 2 LEFT]`

2. **Processing Phase (Python):**
   - Replace Logo 1 CENTER ✅
   - Insert into Logo 2 LEFT ✅
   - **Total:** 2 logos processed (1 per row)

### **Example 2: Multiple Empty Containers**

**Template has:**
- Logo 1 LEFT   - Empty
- Logo 1 CENTER - Empty
- Logo 1 RIGHT  - Empty

**Processing Flow:**

1. **Detection Phase (JavaScript):**
   - Logo 1 LEFT is empty → Add to `emptyContainers`, mark `Logo 1` as processed
   - Logo 1 CENTER is empty → ⏭️ **SKIPPED** (Logo 1 already processed)
   - Logo 1 RIGHT is empty → ⏭️ **SKIPPED** (Logo 1 already processed)
   - **Result:** `emptyContainers = [Logo 1 LEFT]`

2. **Processing Phase (Python):**
   - Insert into Logo 1 LEFT ✅
   - **Total:** 1 logo (exactly what we want)

---

## 🔍 **Log Messages**

### **JavaScript Detection Logs:**
```
✅ Logo 1 LEFT: isEmpty=true ✅ ADDED (first empty in Logo 1)
⏭️ Logo 1 CENTER: isEmpty=true ⏭️ SKIPPED (Logo 1 already has container)
⏭️ Logo 1 RIGHT: isEmpty=true ⏭️ SKIPPED (Logo 1 already has container)
```

### **Python Processing Logs:**
```
🎯 Inserting logo into Logo 1 LEFT...
   ✅ Logo inserted into Logo 1 LEFT
⏭️ Skipping Logo 1 CENTER - Logo 1 already has a logo
   GUARDRAIL: Only 1 logo per logo row allowed
```

---

## 🎯 **Key Benefits**

✅ **Prevents Duplicate Logos** - Each logo row gets exactly 1 logo  
✅ **Respects Alignment** - First discovered alignment is used  
✅ **Consistent Results** - Same behavior across all templates  
✅ **Clear Logging** - Easy to debug which logos were skipped and why  
✅ **Three-Layer Protection** - JavaScript detection + Python processing

---

## 📝 **Implementation Details**

### **What Counts as "Same Logo Row"?**

Logo rows are identified by the first two words of the container name:
- `"Logo 1 LEFT"` → Logo row: `"Logo 1"`
- `"Logo 1 CENTER"` → Logo row: `"Logo 1"`
- `"Logo 2 RIGHT"` → Logo row: `"Logo 2"`

### **Processing Order**

1. ✅ **Logos with warnings** (highest priority)
2. ✅ **Logos without warnings but need replacement**
3. ✅ **Empty containers** (lowest priority)

The guardrail applies to ALL three categories.

---

## 🚀 **Testing**

Run the production test to verify:

```bash
python3 run_truly_dynamic_test.py
```

**Expected behavior:**
- Each logo row processes exactly 1 logo
- Logs show "⏭️ SKIPPED" for additional containers in the same row
- No duplicate logos in any template

---

**Status:** ✅ Implemented and Active
