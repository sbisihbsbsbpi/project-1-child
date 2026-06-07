# Smart Logo Selection Fix

**Date:** June 8, 2026  
**Issue:** Script always used generic "Tilton.png" instead of dealership-specific logos like "Alfa Romeo of Cincinnati.jpg"  
**Impact:** All templates got generic logos even when dealership-specific logos were available  
**Fix:** Implemented smart logo selection with dealership name matching and Insert Image validation  

---

## 🎯 Problem Statement

### **The Issues:**

1. **Always Selected First Logo:**
   - Code: `replacement_logo = available_filenames[0]`
   - Result: Always "Tilton.png" (first alphabetically), never "Alfa Romeo of Cincinnati.jpg"

2. **No Dealership Name Matching:**
   - Didn't search for dealership name in logo filenames
   - Treated all logos equally (no priority ordering)

3. **Empty Containers Skipped Validation:**
   - Insert Image workflow used hardcoded `logo_media_id`
   - Never checked what logos were actually available
   - Never validated against media library

4. **No Smart Selection:**
   - No brand extraction (e.g., "Alfa Romeo" from "Alfa Romeo of Cincinnati")
   - No department-specific matching (Service vs Parts)
   - No priority: dealership > department > generic

---

## ✅ Solution: Smart Logo Selection System

### **New Priority System:**

1. **Exact dealership name match** (case-insensitive)
   - "Alfa Romeo of Cincinnati.jpg" for dealership "Alfa Romeo of Cincinnati"

2. **Brand name match**
   - "Alfa Romeo Logo.jpg" for brand "Alfa Romeo"
   - Extracts first 2 words as brand name

3. **Single word brand match**
   - "Alfa.png" matches "Alfa Romeo of Cincinnati"

4. **Department-specific**
   - "Service Logo.png" for Service department
   - "Parts Logo.png" for Parts department

5. **Generic fallback**
   - First available logo if no matches

---

## 🔧 Implementation Details

### **1. New Method: `_select_best_logo()`**

**Location:** Lines 3877-3992  
**Purpose:** Intelligent logo selection based on dealership name and departments

**Algorithm:**
```python
def _select_best_logo(available_logos, dealership_name, departments):
    # Priority 1: Exact match
    if dealership_name in logo.lower():
        return logo
    
    # Priority 2: Brand match (first 2 words)
    brand = " ".join(dealership_name.split()[:2])
    if brand in logo.lower():
        return logo
    
    # Priority 3: Single word match
    if first_word in logo.lower():
        return logo
    
    # Priority 4: Department match
    for dept in departments:
        if dept.lower() in logo.lower():
            return logo
    
    # Priority 5: Generic
    return available_logos[0]
```

---

### **2. New Method: `_get_available_logos_for_insert()`**

**Location:** Lines 4255-4368  
**Purpose:** Validate available logos from Insert Image popup (not just Change Image)

**Workflow:**
1. Click empty container to focus it
2. Click "Insert Image" button
3. Extract all available logo filenames from popup
4. Close popup (escape key)
5. Return same format as `_get_available_logos()`

---

### **3. Updated: Invalid Logo Replacement**

**Location:** Lines 818-825

**Before:**
```python
replacement_logo = available_filenames[0]  # Always first
```

**After:**
```python
replacement_logo = self._select_best_logo(
    available_filenames,
    dealership_name=template.get('dealershipName', ''),
    departments=template.get('departments', [])
)
```

---

### **4. Updated: Empty Container Processing**

**Location:** Lines 1247-1297

**New Logic:**
```python
# BEFORE processing empty containers:
if empty_count > 0:
    # Fetch available logos from Insert Image popup
    available_logos = await self._get_available_logos_for_insert(page, first_container)
    
    # Smart selection for ALL empty containers
    best_logo = self._select_best_logo(
        available_logos,
        dealership_name=template.get('dealershipName', ''),
        departments=template.get('departments', [])
    )
    
    # Use same best_logo for ALL empty containers in this template
    for container in containers:
        await self._insert_logo_to_container(page, container, logo_media_id, 
                                            target_filename=best_logo)
```

---

### **5. Updated: `_insert_logo_to_container()`**

**Location:** Lines 3349-3357

**New Signature:**
```python
async def _insert_logo_to_container(page, container_info, logo_media_id, 
                                    target_filename=None):
```

**Selection Logic:**
```python
# Use smart selection method instead of hardcoded first logo
selection = await self._select_logo_from_library(
    page, 
    target_filename=target_filename,  # "Alfa Romeo of Cincinnati.jpg"
    fallback_index=0
)
```

---

## 📊 Before vs After

### **Scenario: Alfa Romeo Dealership with 2 Empty Containers**

**Media Library Contains:**
- Tilton.png
- Alfa Romeo of Cincinnati.jpg
- Alfa Romeo Logo.png
- Service Logo.png

#### **Before Fix:**
```
Container 1: Insert "Tilton.png" (always first)
Container 2: Insert "Tilton.png" (always first)
Result: Generic logo ❌
```

#### **After Fix:**
```
Validation: Fetch available logos from Insert Image popup
Smart Selection:
  - Check: "Alfa Romeo of Cincinnati" in "Alfa Romeo of Cincinnati.jpg" ✅
  - Selected: "Alfa Romeo of Cincinnati.jpg"

Container 1: Insert "Alfa Romeo of Cincinnati.jpg" ✅
Container 2: Insert "Alfa Romeo of Cincinnati.jpg" ✅
Result: Dealership-specific logo ✅
```

---

## 🎯 Key Improvements

| Feature | Before | After |
|---------|--------|-------|
| Logo Selection | Always first (Tilton.png) | Smart dealership matching |
| Dealership Name | Ignored | Matched in filenames |
| Brand Extraction | No | Yes ("Alfa Romeo" from full name) |
| Department Match | No | Yes (Service/Parts logos) |
| Empty Container Validation | Skipped | Full validation via Insert Image popup |
| Consistency | Random | Same logo for all containers in template |

---

## 📝 Files Modified

1. **`logo_addition_diagnostics/temp_logo_adding_FINAL.py`**
   - Lines 818-825: Smart selection for invalid logo replacement
   - Lines 1247-1297: Validation for empty containers
   - Lines 3349-3357: Updated `_insert_logo_to_container()` signature
   - Lines 3456-3463: Smart selection in Insert Image workflow
   - Lines 3877-3992: New `_select_best_logo()` method (~115 lines)
   - Lines 4255-4368: New `_get_available_logos_for_insert()` method (~113 lines)

**Total:** ~250 new lines of code

---

## ✅ Testing Scenarios

**Test 1:** Template with "Screenshot_2022-02-10_at_5.25.15_PM.png"
- Validates against Change Image popup ✅
- Finds "Alfa Romeo of Cincinnati.jpg" ✅
- Replaces with dealership logo ✅

**Test 2:** Template with 2 empty Logo 1/2 containers
- Validates against Insert Image popup ✅
- Finds "Alfa Romeo of Cincinnati.jpg" ✅
- Inserts same dealership logo in both ✅

**Test 3:** No exact dealership match available
- Falls back to brand match ("Alfa Romeo Logo.jpg") ✅
- Or department match ("Service Logo.png") ✅
- Or generic (first available) ✅

---

## 🚀 Impact

**Before:** 100% generic logos (Tilton.png)  
**After:** Dealership-specific logos when available  
**Success Rate:** Priority matching ensures best logo selection  
**Maintenance:** Zero (no hardcoded dealership names)
