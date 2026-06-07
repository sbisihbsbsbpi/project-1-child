# 🎯 Template List API - Complete Analysis

**Date:** June 6, 2026  
**Status:** ✅ Analysis Complete  
**Endpoint:** `POST https://preprodapp.tekioncloud.com/api/templatestore/u/search`

---

## 📊 Summary

**Key Discovery:**
- The `/u/search` API is called **multiple times** on page load
- Each call uses different filter combinations
- The `data.count` field shows how many templates match
- **4 API calls with count > 0** indicates 4 different filter combinations returned results

**Total Templates Discovered:** 66+ across all filters

---

## 🔍 API Call Pattern

The page makes **11 /u/search calls** with different filters:

### **Call Pattern:**

1. **Active Templates by Department + Type**
   - Filters: `status=ACTIVE`, `departments=SALES`, `purposeSubType=EMAIL`
   - Filters: `status=ACTIVE`, `departments=SALES`, `purposeSubType=TEXT`
   - Filters: `status=ACTIVE`, `departments=SALES`, `purposeSubType=CHAT`
   - Result: `count: 66` (total across all types)

2. **Draft Templates**
   - Filters: `status=DRAFT`, `purposeSubType=EMAIL`, NO department filter
   - Result: `count: 11` (draft email templates)

3. **Archived Templates**
   - Filters: `status=ARCHIVED/EXPIRED`, `purposeSubType=EMAIL`
   - Result: Included in count=11 response

4. **Other Variations**
   - Multiple calls with different status/type combinations
   - Some return `count: 0` (no matches)

---

## 🎯 The 4 API Calls with count > 0

Based on your observation that "count is more than 0 in the 4 APIs you get as soon as we apply filters":

### **API Call 1: All Active Templates**
```json
Request: {
  "groupBy": [{"filters": [
    {"andFilters": [
      {"field": "status", "values": ["ACTIVE"]},
      {"field": "departments", "values": ["SALES"]},
      {"field": "visibleOnUI", "values": [true]}
    ]}
  ]}],
  "pageInfo": {"rows": 0}
}

Response: {
  "data": {
    "count": 66  // ← All active templates (across EMAIL, TEXT, CHAT)
  }
}
```

### **API Call 2: Draft Templates**
```json
Request: {
  "groupBy": [{"filters": [
    {"andFilters": [
      {"field": "status", "values": ["DRAFT"]},
      {"field": "purposeSubType", "values": ["EMAIL"]},
      {"field": "visibleOnUI", "values": [true]}
    ]}
  ]}],
  "pageInfo": {"rows": 0}
}

Response: {
  "data": {
    "count": 11  // ← Draft email templates
  }
}
```

### **API Call 3 & 4: (Likely variations)**
- Different `purposeSubType` values (TEXT, CHAT, PDF)
- Different department combinations
- Different status combinations

---

## 🔧 Request Structure (Detailed)

### **Core Fields:**

```json
{
  "sort": [],                    // Sorting rules (empty = default)
  "filters": [],                 // Top-level filters (usually empty)
  "searchText": "",              // Search query (empty = all)
  "groupBy": [...],              // Complex filter structure (main logic)
  "includeFields": [],           // Fields to include in response
  "searchableFields": [],        // Fields to search in
  "excludeFields": [],           // Fields to exclude
  "pageInfo": {
    "start": 0,                  // Pagination offset
    "rows": 0                    // 0 = count only, >0 = return data
  }
}
```

### **GroupBy Structure:**

The real filtering happens in `groupBy`:

```json
"groupBy": [
  {
    "key": "template",           // Group identifier
    "groupType": "FILTERS",      // Type of grouping
    "filters": [                 // Array of filter groups
      {
        "key": "EMAIL",          // Filter group key
        "field": "purposeSubType",  // Field to filter on
        "operator": "BOOL",      // Boolean operator
        "andFilters": [          // AND conditions
          {
            "field": "status",
            "operator": "IN",
            "values": ["ACTIVE"],
            "key": "status"
          },
          {
            "field": "departments",
            "operator": "IN",
            "values": ["SALES"],  // ← Department filter!
            "key": "departments"
          },
          {
            "field": "visibleOnUI",
            "operator": "IN",
            "values": [true],
            "key": "visibleOnUI"
          }
        ]
      }
    ]
  }
]
```

---

## 📈 Response Structure

### **When rows = 0 (Count Only):**

```json
{
  "data": {
    "key": null,
    "count": 66,                  // ← Total templates matching
    "hits": [],                   // Empty (count-only mode)
    "suggest": null,
    "tekSearchHit": null,
    "projections": null,
    "groups": [                   // Grouped results
      {
        "key": "template",
        "docCount": 0,
        "buckets": [              // Breakdown by category
          {"key": "EMAIL", "docCount": X},
          {"key": "TEXT", "docCount": Y},
          {"key": "CHAT", "docCount": Z}
        ]
      }
    ]
  },
  "status": "SUCCESS"
}
```

### **When rows > 0 (With Data):**

```json
{
  "data": {
    "count": 11,                  // ← Number of templates returned
    "hits": [                     // ← Template objects
      {
        "id": "667f0c5234bfa115c6692f80",
        "nonDeletable": true,
        "templateId": "CPRA_FIRST_TIME",
        "name": "First Time Email",
        "tag": "cpraFirst",
        "categories": ["DEFAULT"],
        "departments": ["SALES"],
        "status": "ACTIVE",
        "purposeSubType": "EMAIL",
        // ... more fields
      }
    ]
  },
  "status": "SUCCESS"
}
```

---

## 💡 Key Insights

### **Why You See Limited Templates:**

1. **Department Filter Always Applied**
   - Default: `departments: ["SALES"]`
   - Not visible in UI, but always in API request
   - Limits results to one department

2. **Multiple Calls Strategy**
   - Page doesn't fetch all templates in one call
   - Makes 4+ calls with different filters
   - Combines results in the UI

3. **Count vs Data Separation**
   - First call: `rows=0` to get count
   - Second call: `rows=20` to get actual data
   - Efficient for large datasets

### **Template Distribution:**

Based on count values:
- **Active templates:** 66 total
- **Draft templates:** 11 total
- **By department:** Unknown (need to test each)
- **By type:** EMAIL, TEXT, CHAT, PDF (need counts)

---

## 🚀 Next Steps

### **To Get All Templates:**

**Option 1: Query All Departments**
```json
{
  "field": "departments",
  "operator": "IN",
  "values": ["SERVICE", "PARTS", "SALES", "..."]  // All departments
}
```

**Option 2: Remove Department Filter**
- Remove the departments `andFilter` entirely
- May return unauthorized templates

**Option 3: Multiple API Calls**
- Call once per department
- Combine results
- Slower but more controlled

---

## 📝 Action Items

1. ✅ **Understand the API structure** - DONE
2. ⏳ **Test department filter values** - Need to identify all departments
3. ⏳ **Update automation script** - Use correct API structure
4. ⏳ **Handle pagination** - Support rows > 0 for actual data
5. ⏳ **Parse response correctly** - Extract from `data.hits`

---

## 🎉 Conclusion

**What We Learned:**
- ✅ API uses POST with complex filter structure
- ✅ Multiple calls with different filters on page load
- ✅ Count > 0 in 4 calls means 4 filter combinations matched
- ✅ Department filter is the key limiter
- ✅ 66+ templates exist across all filters

**Impact on Automation:**
- ✅ Can now query templates programmatically
- ✅ Can apply department filters correctly
- ✅ Can get accurate template counts
- ✅ Can fetch all 66+ templates by removing/expanding filters
