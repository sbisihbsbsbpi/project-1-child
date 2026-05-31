# 🎯 Logo Automation Enhancement Requirements

## Document Purpose
This document captures the complete logic requirements for the template logo automation system based on user clarifications on 2026-05-31.

---

## 📋 Core Requirements Summary

### **Logo Container Structure**
- Templates have **2 Logo containers** (Logo 1 and Logo 2)
- Each container has **3 alignment positions**: LEFT, CENTER, RIGHT
- **Total: 6 positions** across both containers
- **CENTER positions are primary targets** for logo placement

### **Current Container IDs (Hardcoded)**
```javascript
Logo 1 LEFT:   '6f0b8570-c4dc-45bd-b746-40e3af9af3bb'
Logo 1 CENTER: '7653caa9-31b7-4e2b-8233-f0bda43672ea'
Logo 1 RIGHT:  '47da3c0a-2c2b-4f8f-8a31-4ba8fdae03aa'
Logo 2 LEFT:   '9fa2920b-10f8-48d2-9947-b014398d21be'
Logo 2 CENTER: '983932ae-d79a-40fe-a9ba-df07c9beee47'
Logo 2 RIGHT:  '9d454086-c1f2-4bf0-b4a7-8e95dc244aae'
```

**Note:** These IDs may change when Tekion updates templates. Future enhancement: Dynamic detection by container structure instead of hardcoded UUIDs.

---

## 🔄 Complete Logic Breakdown

### **Scenario 1: Logo Containers Exist**

#### **Case 1A: Container has logo WITH warning icon**
```
Action: REPLACE logo using "Change Image" workflow
Steps:
  1. Hover over logo → Reveal toolbar
  2. Click "Change Image" icon
  3. Media library popup opens
  4. Select new logo (Tilton.png)
  5. Click "Insert" to confirm
  6. Check alignment → If not centered, click alignment icon → Select center
```

#### **Case 1B: Container has logo WITHOUT warning icon**
```
Action: REPLACE logo using "Change Image" workflow
Steps: Same as Case 1A
Note: Logo exists but no warning - still needs replacement
```

#### **Case 1C: Container is EMPTY (no logo)**
```
Action: INSERT logo using "Insert Image" workflow to CENTER position ONLY
Steps:
  1. Click on CENTER position container
  2. Click "Insert Image" toolbar button
  3. Media library popup opens
  4. Select new logo (Tilton.png)
  5. Click "Insert" to confirm
Note: Do NOT insert logos into LEFT or RIGHT positions
```

#### **Processing Priority**
- **ONLY process CENTER positions** (Logo 1 CENTER + Logo 2 CENTER) when inserting
- **PROCESS any position** that has a logo when replacing (then center align if needed)

---

### **Scenario 2: NO Logo Containers + NO Warnings**

#### **Case 2A: Header button ACTIVE (opacity=1.0)**
```
Meaning: Template has NO header structure
Action: ADD new header with logos
Steps:
  1. Click #HEADER button
  2. Click "+ Add Header" button
  3. Select first header template from popup
  4. Click "Insert"
  5. Verify header added (button becomes grayed)
  6. Add logos to header positions
```

#### **Case 2B: Header button GRAYED (opacity<1.0)**
```
Meaning: Header already exists
Action: SKIP template (no empty positions to fill)
```

---

### **Scenario 3: NO Logo Containers + Warnings Present**

#### **Case 3A: Header button GRAYED + Warnings detected**
```
Meaning: Header exists with logos that need replacement
Action: REPLACE actively selected logo
Steps:
  1. Detect currently selected logo (checked radio button in media library)
  2. Select new logo (Tilton.png)
  3. Click "Insert" to replace
Enhancement needed: Detect pre-selected radio button before clicking
```

---

## 🔧 Enhancement Requirements

### **Enhancement 1: Dynamic Container Detection**
**Current:** Hardcoded 6 UUIDs  
**Future:** Detect Logo 1/2 containers by:
- Container structure/pattern analysis
- CENTER alignment position detection
- Not relying on specific IDs

### **Enhancement 2: Selected Logo Detection**
**Current:** Always clicks first tile  
**Future:** Check if radio button already selected in media library popup
```javascript
// Check for pre-selected logo
const selectedRadio = popup.querySelector('input[type="radio"]:checked');
if (selectedRadio) {
    // A logo is already selected
    // Select different logo (Tilton.png)
} else {
    // No selection, select Tilton.png
}
```

### **Enhancement 3: Alignment Icon Detection & Centering**
**Required:** After replacing any logo:
```
1. Detect current alignment (left/center/right)
2. If NOT center:
   - Click alignment icon
   - Select center alignment option
   - Verify logo moved to center
```

### **Enhancement 4: Logo Detection Without Warning Icons**
**Issue:** Templates like "Service History Recap PDF" have logos but no warning icons  
**Solution:** Detect logos by:
- Checking for images in SortableItems
- Looking for resizable image containers
- Analyzing container structure patterns

### **Enhancement 5: Manual Review List**
**Required:** When detection fails or ambiguous:
```
Add to manual review list:
  - Template name
  - Template ID
  - Reason (e.g., "Has logos but IDs don't match", "Unknown structure")
  - Screenshot/URL for manual inspection
```

**Format:** Generate separate sheet in Excel report or dedicated JSON file

---

## 🎯 Processing Rules

### **Rule 1: Center Alignment Priority**
- When INSERTING logos → Only use CENTER positions
- When REPLACING logos → Any position, then move to center if needed
- LEFT and RIGHT positions remain empty when inserting new logos

### **Rule 2: Parallel Execution**
All detection logics run in parallel:
- Warning logo detection
- Empty container detection
- Empty header detection
- Header button state check

Then process ALL winning results (not just first match)

### **Rule 3: Template Type Handling**
| Template Type | Has Logo Containers? | Has Header? | Action |
|---------------|---------------------|-------------|--------|
| Email (standard) | ✅ Yes | ❌ No | Process Logo 1/2 containers |
| Email (CPRA) | ❌ No | Needs adding | Add header structure |
| PDF | ⚠️ Unknown | ⚠️ Unknown | Add to manual review |

---

## 📊 Expected Outcomes

### **Success Metrics**
- Logo 1 CENTER: Logo replaced/inserted
- Logo 2 CENTER: Logo replaced/inserted
- Alignment: Both logos centered
- Auto-publish: Template published if enabled

### **Manual Review Triggers**
- Container IDs don't match hardcoded list
- Logos detected but no warnings and not in known positions
- Header state ambiguous
- Detection contradictions (e.g., has logos + active header button)

---

## ❓ Open Questions (Awaiting Clarification)

### **Q1: Logo at Non-Center Position with Warning**
**Scenario:** Logo 1 LEFT has warning icon, Logo 1 CENTER is empty

**Option A:** Replace LEFT logo → Move to CENTER alignment
**Option B:** Replace LEFT logo → Leave at LEFT + Insert new logo at CENTER
**Option C:** Skip LEFT → Insert new logo at CENTER only

**Which approach should we use?**

---

### **Q2: Alignment Icon Detection Timing**
**Question:** When exactly should we check and apply center alignment?

**Option A:** Always after replacing any logo (proactive)
**Option B:** Only when detected as not centered (reactive)
**Option C:** Always after both insert and replace operations

**Which approach is correct?**

---

### **Q3: Service History Recap PDF Handling**
**Current state:** Has 2 Nucar logos, no warning icons, container IDs don't match

**Option A:** Skip entirely (add to manual review)
**Option B:** Try generic logo detection and replacement
**Option C:** Special handling for PDF templates with dynamic detection

**What should the script do?**

---

### **Q4: Multiple Logos in Same Container**
**Scenario:** Logo 1 container has logos at both LEFT and CENTER positions

**Option A:** Process both positions
**Option B:** Process only CENTER, ignore LEFT
**Option C:** Move LEFT to CENTER, delete LEFT position

**Expected behavior?**

---

### **Q5: Manual Review Report Format**
**Question:** How should manual review items be reported?

**Option A:** Separate Excel sheet named "Manual Review"
**Option B:** Dedicated JSON file `manual_review_TIMESTAMP.json`
**Option C:** Flag column in main Excel report
**Option D:** All of the above

**Preferred format?**
