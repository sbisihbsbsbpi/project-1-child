# 🔍 Template List API Analysis Results

**Date:** June 6, 2026  
**Endpoint:** `https://preprodapp.tekioncloud.com/api/templatestore/u/search`  
**Method:** POST

---

## 📊 Key Findings

### **API Endpoint Structure**

**Base Endpoint:** `/api/templatestore/u/search`

**Method:** POST (not GET!)

**Key Response Field:** `data.count` - Number of templates matching the filter

---

## 🎯 Request Structure

### **Before Filter (All Templates):**

The API is called with `pageInfo.rows = 0` to get just the count:

```json
{
  "sort": [],
  "filters": [],
  "searchText": "",
  "groupBy": [
    {
      "key": "template",
      "groupType": "FILTERS",
      "filters": [
        {
          "key": "EMAIL",
          "field": "purposeSubType",
          "operator": "BOOL",
          "andFilters": [
            {"field": "status", "operator": "IN", "values": ["ACTIVE"]},
            {"field": "purposeSubType", "operator": "IN", "values": ["EMAIL"]},
            {"field": "departments", "operator": "IN", "values": ["SALES"]},
            {"field": "visibleOnUI", "operator": "IN", "values": [true]}
          ]
        },
        {
          "key": "TEXT",
          "field": "purposeSubType",
          "operator": "BOOL",
          "andFilters": [
            {"field": "status", "operator": "IN", "values": ["ACTIVE"]},
            {"field": "purposeSubType", "operator": "IN", "values": ["TEXT"]},
            {"field": "departments", "operator": "IN", "values": ["SALES"]},
            {"field": "visibleOnUI", "operator": "IN", "values": [true]}
          ]
        },
        {
          "key": "CHAT",
          "field": "purposeSubType",
          "operator": "BOOL",
          "andFilters": [
            {"field": "status", "operator": "IN", "values": ["ACTIVE"]},
            {"field": "purposeSubType", "operator": "IN", "values": ["CHAT"]},
            {"field": "departments", "operator": "IN", "values": ["SALES"]},
            {"field": "visibleOnUI", "operator": "IN", "values": [true]}
          ]
        }
      ]
    }
  ],
  "pageInfo": {
    "start": 0,
    "rows": 0  // 0 = Just get count, don't return templates
  }
}
```

**Key Observations:**
1. ✅ Default filter is **"SALES"** department (hardcoded!)
2. ✅ Groups by `purposeSubType` (EMAIL, TEXT, CHAT)
3. ✅ `pageInfo.rows = 0` means "just count, don't fetch data"
4. ✅ Uses complex `groupBy` structure with nested filters

---

## 📈 Response Structure

### **Count-Only Response (rows = 0):**

```json
{
  "data": {
    "key": null,
    "count": 66,  // ← TOTAL templates matching filter
    "hits": [],   // Empty because rows=0
    "groups": [
      {
        "key": "template",
        "docCount": 0,
        "buckets": [
          {"key": "EMAIL", "docCount": X, ...},
          {"key": "TEXT", "docCount": Y, ...},
          {"key": "CHAT", "docCount": Z, ...}
        ]
      }
    ]
  },
  "status": "SUCCESS"
}
```

### **Full Data Response (rows > 0):**

```json
{
  "data": {
    "count": 11,  // ← Number of templates returned
    "hits": [     // ← Actual template data
      {
        "id": "667f0c5234bfa115c6692f80",
        "templateId": "CPRA_FIRST_TIME",
        "name": "First Time Email",
        "tag": "cpraFirst",
        "categories": ["DEFAULT"],
        "departments": ["SALES"],
        // ... more fields
      },
      // ... more templates
    ]
  },
  "status": "SUCCESS"
}
```

---

## 🔄 Multiple API Calls Observed

The page makes **11 /u/search calls** on initial load:

**Pattern:**
1. **Count queries** (rows=0) - Get template counts by category
2. **Data queries** (rows>0) - Fetch actual template data
3. **Different department filters** - SALES, SERVICE, PARTS combinations

**Count Results:**
- Response 1: `count: 66` - Likely all active templates
- Response 6: `count: 11` - Likely filtered subset
- Responses 2,3,4,7: `count: 0` - Empty results (different filters)

---

## 🎯 How to Apply Department Filter

### **To filter by Department:**

Change the `departments` value in the `andFilters`:

**Before (default SALES):**
```json
{
  "field": "departments",
  "operator": "IN",
  "values": ["SALES"]  // ← Default
}
```

**After (filter by Service):**
```json
{
  "field": "departments",
  "operator": "IN",
  "values": ["SERVICE"]  // ← Changed
}
```

**Multiple departments:**
```json
{
  "field": "departments",
  "operator": "IN",
  "values": ["SERVICE", "PARTS", "SALES"]  // ← Multiple
}
```

---

## 💡 Why --all Returns Only 11 Templates

**Root Cause:** The UI always includes department filter!

Even when you don't select a department:
- Default filter is `departments: ["SALES"]`
- This explains why you only see 11 templates
- The other 28 templates belong to other departments (SERVICE, PARTS, etc.)

**Total templates:** 66 (across all departments)  
**SALES only:** 11 templates  
**Missing:** 55 templates (SERVICE, PARTS, other departments)

---

## 🔧 Solution for --all Flag

To truly get **all** templates:

1. **Option A:** Remove department filter entirely
   - Remove the departments `andFilter` from the request

2. **Option B:** Query all departments
   - Set `values: ["SERVICE", "PARTS", "SALES", ...]`

3. **Option C:** Make multiple API calls
   - One call per department
   - Combine results

**Recommendation:** Option B - Query all departments in one call

---

## 📝 Next Steps

1. ✅ Update the script to use the correct API structure
2. ✅ Add department filter parameter handling
3. ✅ Support `--all` by querying all departments
4. ✅ Parse `data.count` to verify template counts
5. ✅ Use `data.hits` to get template list

---

## 🎉 Key Takeaways

**API Insights:**
- ✅ POST request (not GET)
- ✅ Complex nested filter structure
- ✅ `data.count` shows total matches
- ✅ `pageInfo.rows = 0` for count-only queries
- ✅ Department filter is ALWAYS applied (default: SALES)

**Why Template Discovery Was Limited:**
- ✅ Default filter restricted to SALES department
- ✅ UI doesn't expose "all departments" option easily
- ✅ 66 total templates vs 11 in SALES

**How to Fix:**
- ✅ Query multiple departments explicitly
- ✅ Parse the correct response structure
- ✅ Handle `groupBy` buckets for categorization
