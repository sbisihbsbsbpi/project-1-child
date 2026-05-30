# 🔍 Tekion Templates Page - Comprehensive Detection Guide

## Overview

The Template Page Detector analyzes **EVERYTHING** on the Tekion templates list page at:
**https://preprodapp.tekioncloud.com/templates/list**

---

## 🎯 What It Detects

### 1. **Page Information**
- Page title
- URL structure
- Viewport dimensions
- Document ready state
- Cookie count

### 2. **Filters & Controls**
- ✅ **Department Filter** (Ant Design dropdown)
  - Current selection (Sales, Service, Parts, etc.)
  - Dropdown trigger element
  - Available options
  
- ✅ **Dropdowns/Comboboxes**
  - All role="combobox" elements
  - aria-expanded state
  - Current text/value
  
- ✅ **Checkboxes**
  - Checked/unchecked state
  - Labels
  - Disabled status
  
- ✅ **Filter Chips/Tags**
  - Active filters
  - Close buttons
  - Text content
  
- ✅ **Search Boxes**
  - Placeholders
  - Current values
  - All search inputs

### 3. **UI Elements**
- ✅ **Buttons** (text, type, disabled state)
- ✅ **Links** (href, text)
- ✅ **Tables** (headers, rows, columns)
- ✅ **Lists** (UL/OL, item count)
- ✅ **Images** (src, alt, dimensions)
- ✅ **Iframes**
- ✅ **Modals/Dialogs**

### 4. **Templates (via API)**
- Intercepts `/api/templatestore/u/search` API calls
- Captures all template metadata:
  - Template ID
  - Name
  - Departments
  - Communication type (EMAIL, SMS, etc.)
  - Status (ACTIVE, DRAFT, etc.)
  - Created/Modified dates
  - Descriptions

### 5. **API Endpoints**
- **ALL** API calls made by the page
- HTTP methods (GET, POST, PUT, DELETE)
- Request headers
- Domains accessed
- Resource types

**Key Endpoints Detected:**
```
/api/templatestore/u/search          # Template search
/api/templatestore/u/setup/fetch     # Setup data
/api/templatestore/u/media/library   # Media library
/api/userservice/u/employee/profile  # User profile
/api/rolesandpermissionservice/...   # Permissions
```

### 6. **Interactive Elements**
- Clickable elements (buttons, links, role="button")
- Editable elements (contenteditable, inputs, textareas)
- Draggable elements
- Sortable elements

### 7. **Forms**
- Form elements (action, method)
- Input fields (type, name, placeholder, required)
- Select dropdowns (options count)
- Textareas

### 8. **Navigation**
- Nav elements
- Breadcrumbs
- Pagination controls
- Tabs
- Menus

### 9. **Layout Structure**
- Containers
- Rows
- Columns  
- Grid layouts
- Flexbox layouts

### 10. **Metadata**
- Meta tags
- Scripts loaded
- Stylesheets
- Fonts loaded

---

## 🚀 How to Use

### Method 1: Standalone Script

```bash
python3 detect_all_template_page_elements.py
```

### Method 2: API Endpoint

```bash
curl -X POST http://localhost:8001/api/templates/detect-all
```

### Method 3: Python Code

```python
from template_page_detector import template_page_detector
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp("http://localhost:9223")
    results = await template_page_detector.detect_all(browser)
    print(results)
```

---

## 📊 Output

### Console Summary
- Executive summary with counts
- Detailed breakdowns by category
- Sample elements
- Key findings

### JSON File
Complete detection results saved to:
```
template_page_detection_YYYYMMDD_HHMMSS.json
```

Includes:
- Timestamps
- Full element details
- API call logs
- Template metadata
- All detected components

---

## 🔍 Detection Examples

### Department Filter Detection
```json
{
  "department_filter": {
    "type": "ant-dropdown",
    "text": "Sales",
    "className": "ant-dropdown-trigger",
    "visible": true
  }
}
```

### Template Detection
```json
{
  "templates": [
    {
      "templateId": "STANDARD_APPOINTMENT_EMAIL",
      "name": "Standard Appointment",
      "departments": ["SALES"],
      "purposeSubType": "EMAIL",
      "status": "ACTIVE"
    }
  ]
}
```

### API Endpoints
```json
{
  "endpoints": [
    "https://preprodapp.tekioncloud.com/api/templatestore/u/search",
    "https://preprodapp.tekioncloud.com/api/templatestore/u/setup/fetch"
  ],
  "methods": {
    "POST": 8,
    "GET": 24
  }
}
```

---

## 🎯 Use Cases

1. **Automation Testing**: Verify all UI elements exist
2. **API Monitoring**: Track all endpoint calls
3. **UI Analysis**: Understand page structure
4. **Template Management**: Get comprehensive template data
5. **Filter Detection**: Identify available filters
6. **Debugging**: See what's actually on the page
7. **Documentation**: Auto-generate page specs

---

## 🔧 Advanced Features

### Real-time API Interception
- Monitors all network traffic
- Captures request/response data
- Identifies authentication patterns

### Smart Element Detection
- Handles Ant Design components
- Detects dynamic content
- Waits for page load completion

### Comprehensive Logging
- Timestamped entries
- Categorized by type
- Full stack traces on errors

---

## 📋 Detected Statistics (Sample)

```
Page Title:        Tekion Template Builder
Buttons:           12
Links:             7  
API Calls:         32
Clickable:         41
Department:        Sales
Search Boxes:      2
Pagination:        15
Tabs:              3
Containers:        18
Flexbox:           28
```

---

## ✅ Success Indicators

- ✅ Page loaded successfully
- ✅ Department filter detected
- ✅ API calls intercepted
- ✅ Templates captured
- ✅ All UI elements found
- ✅ JSON report generated

---

## 🚨 Prerequisites

1. **Browser Connection**: CDP on localhost:9223
2. **Authentication**: Valid Tekion session
3. **Network Access**: To preprodapp.tekioncloud.com
4. **Python**: 3.8+ with Playwright

---

## 💡 Tips

- Run after logging into Tekion
- Keep browser tab active during detection
- Wait 3-5 seconds after page load
- Check JSON for complete details
- Use for smoke testing new features

---

**Generated by Template Page Detector v1.0**
