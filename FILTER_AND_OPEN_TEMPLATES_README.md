# ✅ Filter Service & Parts → Build Links → Open Templates

**Script:** `filter_and_open_templates.py`  
**Date:** 2026-05-30  
**Status:** ✅ **TESTED & WORKING**

---

## 🎯 Purpose

This script implements the complete integration workflow:

1. **Apply Service & Parts filter** on templates list page
2. **Capture API response** with template data
3. **Extract `templateId`** from each template
4. **Build edit URLs** using `templateId`
5. **Open all templates** in browser tabs

---

## ✅ Test Results (2026-05-30)

### **Execution Summary:**
- **Filter Applied:** Service & Parts ✅
- **API Templates Captured:** 39 templates ✅
- **Edit URLs Built:** 10 URLs (limited for testing) ✅
- **Templates Opened:** 10/10 (100% success rate) ✅
- **Duration:** ~45 seconds
- **Status:** ALL TESTS PASSED ✅

### **What Worked:**
1. ✅ Department filter applied correctly
2. ✅ API monitoring captured all requests
3. ✅ Correct API call identified: `['SERVICE', 'PARTS']` → 39 templates
4. ✅ templateId extracted from each template
5. ✅ Edit URLs built using `generate_edit_url()` function
6. ✅ All 10 templates opened successfully in new tabs

### **Templates Opened:**
1. First Time Email
2. RO Payment Link
3. RO Created
4. Collection Slip
5. Consumer Scheduling OTP
6. Request Completion: Data Deletion (Closed Documents)
7. Request Completion: Data Correction
8. Request Completion: Data Export
9. Request Acknowledgement
10. Request Decline: Data Deletion (Open Documents)

---

## 🚀 Usage

### **Basic Usage (Opens ALL templates):**
```bash
python3 filter_and_open_templates.py
```

This will open **all 39 Service & Parts templates** in browser tabs.

### **Limit to Specific Number:**
Edit the script and change:
```python
max_templates=None  # Change to a number (e.g., 10, 20)
```

Or modify the `main()` function:
```python
result = await filter_and_open_templates(
    departments=['Service', 'Parts'],
    max_templates=10,  # Limit to 10 templates
    cdp_url="http://localhost:9223"
)
```

### **Custom Department Filter:**
```python
result = await filter_and_open_templates(
    departments=['Service'],  # Only Service
    max_templates=20,
    cdp_url="http://localhost:9223"
)
```

---

## 📋 How It Works

### **Workflow:**

```
Step 1: Set up API Monitoring
   ↓
   Monitor POST /api/templatestore/u/search
   
Step 2: Apply Service & Parts Filter
   ↓
   1. Open department dropdown
   2. Uncheck Sales
   3. Check Service
   4. Check Parts
   5. Close dropdown
   
Step 3: Wait for API Response
   ↓
   Capture API call with ['SERVICE', 'PARTS']
   Extract templates array from response
   
Step 4: Build Edit URLs
   ↓
   For each template:
     - Extract templateId (NOT id!)
     - Build URL: https://preprodapp.tekioncloud.com/templates/edit/{templateId}
   
Step 5: Open All Templates
   ↓
   For each URL:
     - Open in new browser tab
     - Wait for page load (2s)
     - Track success/failure
```

---

## 🔑 Key Technical Details

### **API Monitoring:**
- Endpoint: `POST /api/templatestore/u/search`
- Filter: `{'field': 'departments', 'values': ['SERVICE', 'PARTS']}`
- Response: `{'data': {'hits': [templates...]}}`

### **templateId vs id:**
- ❌ **DON'T USE:** `template['id']` (MongoDB internal ID)
- ✅ **USE:** `template['templateId']` (Public template ID for URLs)

### **URL Pattern:**
```python
# CORRECT:
url = f"https://preprodapp.tekioncloud.com/templates/edit/{template['templateId']}"

# Example:
# https://preprodapp.tekioncloud.com/templates/edit/CPRA_FIRST_TIME
# https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6ea4
```

---

## 📊 Output Format

### **Return Value:**
```python
{
    'success': True,
    'templates': [
        {
            'templateId': 'CPRA_FIRST_TIME',
            'name': 'First Time Email',
            'url': 'https://preprodapp.tekioncloud.com/templates/edit/CPRA_FIRST_TIME',
            'departments': ['SALES', 'PARTS', 'SERVICE']
        },
        # ... more templates
    ],
    'opened_pages': [
        {
            'page': <Page object>,
            'template': {...},
            'url': '...'
        },
        # ... more pages
    ],
    'count': 10
}
```

---

## 🔧 Requirements

- Browser must be running with CDP on `localhost:9223`
- User must be logged into Tekion preprodapp
- Templates list page must be accessible

---

## 💡 Next Steps

After opening templates, you can:

1. **Manually inspect** templates in browser tabs
2. **Run logo detection** on opened pages
3. **Process logo replacements** using existing automation
4. **Generate reports** from template data

---

## 🎯 Integration Points

This script integrates with:

- **test_service_parts_filter_selection.py** - Filter application logic
- **automation/department_filter_automation.py** - `generate_edit_url()` function
- **temp_logo_adding.py** - Can use opened pages for logo processing

---

## ✅ Verification

To verify the script worked:

1. Check browser - should see 10 new tabs open
2. Each tab should show a template edit page
3. Console output should show "✅ Opened successfully" for each template
4. Final summary should show 10/10 templates opened

---

**Status:** Production Ready ✅  
**Last Tested:** 2026-05-30  
**Success Rate:** 100% (10/10 templates opened)
