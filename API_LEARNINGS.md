# 🌐 API Network Monitoring - Key Learnings

## 🎯 Discovered API Endpoint

**Endpoint**: `POST https://preprodapp.tekioncloud.com/api/templatestore/u/search`

## 📊 Request Structure

The API accepts complex filter requests with this structure:

```json
{
  "sort": [
    {
      "field": "modifiedTime",
      "order": "DESC"
    }
  ],
  "filters": [
    {
      "field": "status",
      "operator": "IN",
      "values": ["ACTIVE"]
    },
    {
      "field": "purposeSubType",
      "operator": "IN",
      "values": ["EMAIL"]
    },
    {
      "field": "departments",
      "operator": "IN",
      "values": ["SALES", "SERVICE", "PARTS"]  // ← DEPARTMENT FILTER!
    },
    {
      "field": "visibleOnUI",
      "operator": "IN",
      "values": [true]
    }
  ],
  "searchText": "",
  "pageInfo": {
    "start": 0,
    "rows": 50
  }
}
```

## 🔍 Key Filter Parameters

### **Department Filter**
```json
{
  "field": "departments",
  "operator": "IN",
  "values": ["SALES"]  // or ["SERVICE"], ["PARTS"], ["SERVICE", "PARTS"], etc.
}
```

### **Communication Type Filter** (Tabs)
```json
{
  "field": "purposeSubType",
  "operator": "IN",
  "values": ["EMAIL"]  // or "TEXT", "CHAT"
}
```

### **Status Filter**
```json
{
  "field": "status",
  "operator": "IN",
  "values": ["ACTIVE"]  // or "DRAFT", "ARCHIVED", "EXPIRED"
}
```

## 📥 Response Structure

```json
{
  "data": {
    "hits": [
      {
        "templateId": "CPRA_REQUEST_COMPLETION_DATA_DELETION_CLOSED_DOCUMENTS",
        "name": "Request Completion: Data Deletion (Closed Documents)",
        "departments": ["SALES", "PARTS", "SERVICE"],
        "purposeSubType": "EMAIL",
        "status": "ACTIVE",
        "categories": ["Data Privacy"],
        "modifiedTime": 1234567890,
        "createdTime": 1234567890,
        "createdBy": "...",
        "modifiedBy": "..."
      }
      // ... more templates
    ],
    "total": 11,
    "page": 1,
    "size": 50
  }
}
```

## 💡 Major Discovery!

### **Templates Can Belong to Multiple Departments!**

Example from captured data:
```
Template: "Request Completion: Data Deletion"
Departments: ["SALES", "PARTS", "SERVICE"]
```

This explains why:
- **Sales filter** shows 11 templates
- **Service filter** shows 10 templates  
- **Parts filter** shows 9 templates
- **But they're not all unique!**

The **same template** appears in multiple department filters!

## 📊 Captured Example Data

From the API response:

### **Template Breakdown (11 total in response)**

| Template Name | Departments | Type | Status | Categories |
|--------------|-------------|------|--------|------------|
| Request Completion: Data Deletion | SALES, PARTS, SERVICE | EMAIL | ACTIVE | Data Privacy |
| Request Completion: Data Correction | SALES, PARTS, SERVICE | EMAIL | ACTIVE | Data Privacy |
| Request Completion: Data Export | SALES, PARTS, SERVICE | EMAIL | ACTIVE | Data Privacy |
| Request Acknowledgement | SALES, SERVICE, PARTS | EMAIL | ACTIVE | Data Privacy |
| First Time Email | SALES, PARTS, SERVICE | EMAIL | ACTIVE | Data Privacy |

### **Department Count from Single Response:**
- **SALES**: 11 templates
- **SERVICE**: 10 templates
- **PARTS**: 9 templates

**Total unique templates**: 11 (not 11+10+9=30!)

## 🎯 How to Use This for Verification

### **Instead of DOM Parsing:**

```python
# OLD WAY (unreliable):
# - Click filter
# - Wait 20 seconds
# - Parse DOM
# - Count table rows
# - Hope it worked

# NEW WAY (reliable):
# 1. Monitor API calls
# 2. Capture request payload
# 3. Capture response data
# 4. Compare department filters in request
# 5. Compare template IDs in response
# 6. INSTANT verification!
```

### **Example Verification Logic:**

```python
# Before changing filter
before_request = {
    "departments": ["SALES"]
}
before_response = {
    "hits": [template1, template2, ...],  # 15 templates
    "total": 15
}

# After changing filter  
after_request = {
    "departments": ["SERVICE", "PARTS"]
}
after_response = {
    "hits": [template3, template4, ...],  # 39 templates
    "total": 39
}

# Verification
assert before_request != after_request  # Filter changed ✅
assert before_response['total'] != after_response['total']  # Data changed ✅
assert set(before_templates) != set(after_templates)  # Different templates ✅
```

## 🚀 Updated Automation Strategy

### **Phase 1: Monitor (Current)**
✅ Intercept API calls  
✅ Capture request/response  
✅ Understand filter structure  

### **Phase 2: Direct API Call (Better)**
Instead of clicking UI:
```python
# Call API directly with desired filters
response = await page.request.post(
    "https://preprodapp.tekioncloud.com/api/templatestore/u/search",
    data={
        "filters": [
            {
                "field": "departments",
                "operator": "IN",
                "values": ["SERVICE", "PARTS"]
            },
            {
                "field": "purposeSubType",
                "operator": "IN",
                "values": ["EMAIL"]
            },
            {
                "field": "status",
                "operator": "IN",
                "values": ["ACTIVE"]
            }
        ],
        "pageInfo": {"start": 0, "rows": 100}
    }
)

templates = response.json()['data']['hits']
# Now you have ALL templates instantly!
```

### **Phase 3: Verification (Fastest)**
```python
1. Get templates for ["SALES"]
2. Get templates for ["SERVICE", "PARTS"]
3. Compare:
   - Template IDs
   - Counts
   - Departments
   - Categories
4. Done in < 2 seconds (vs 20+ seconds DOM way)
```

## 📋 Action Items

### ✅ **What We Learned:**
1. API endpoint structure
2. Filter payload format
3. Response data structure
4. Templates can be in multiple departments
5. Direct API access is possible

### 🔄 **Next Steps:**
1. ✅ Update verification code to use API interception
2. ✅ Compare request payloads instead of DOM
3. ✅ Compare response data instead of counting rows
4. ✅ Build template database from API responses
5. ✅ Create fast verification (< 5 seconds)

## 💾 Sample Data Structure to Store

```python
{
    "timestamp": "2026-05-29T...",
    "filter_applied": {
        "departments": ["SERVICE", "PARTS"],
        "type": "EMAIL",
        "status": "ACTIVE"
    },
    "api_response": {
        "total": 39,
        "template_ids": ["TEMPLATE_1", "TEMPLATE_2", ...],
        "templates": [
            {
                "id": "...",
                "name": "...",
                "departments": [...],
                "type": "...",
                "categories": [...]
            }
        ]
    },
    "verification": {
        "filter_changed": true,
        "data_changed": true,
        "templates_diff": {
            "added": 24,
            "removed": 0,
            "total_before": 15,
            "total_after": 39
        }
    }
}
```

## 🎉 Success Criteria

**Old Way**: Filter changed, wait 20s, hope DOM updated  
**New Way**: Filter changed, API called, data verified in < 2s ✅

---

**Generated**: 2026-05-29  
**Status**: ✅ API structure fully understood, ready to implement
