# 🎯 Service + Parts API Structure - COMPLETE

**Date:** June 6, 2026  
**Source:** User-provided actual payload from Network tab  
**Endpoint:** `POST https://preprodapp.tekioncloud.com/api/templatestore/u/search`

---

## ✅ ACTUAL SERVICE + PARTS PAYLOAD

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
      "values": ["ACTIVE"],
      "key": "status"
    },
    {
      "field": "purposeSubType",
      "operator": "IN",
      "values": ["EMAIL"],
      "key": "purposeSubType"
    },
    {
      "field": "visibleOnUI",
      "operator": "IN",
      "values": [true],
      "key": "visibleOnUI"
    },
    {
      "field": "departments",
      "operator": "IN",
      "values": ["SERVICE", "PARTS"]  // ← BOTH DEPARTMENTS
    }
  ],
  "searchText": "",
  "groupBy": [],
  "includeFields": [],
  "searchableFields": ["name"],
  "excludeFields": [
    "body",
    "htmlBody",
    "subject",
    "htmlSubject",
    "preHeader",
    "languages"
  ],
  "pageInfo": {
    "start": 0,
    "rows": 50  // ← Returns 50 templates, not just count
  }
}
```

---

## 🔍 KEY FINDINGS

### **1. Different Structure than Initial Page Load**

**Initial page load (SALES default):**
- Uses `groupBy` with nested `andFilters`
- Complex nested structure
- Multiple filter groups for EMAIL/TEXT/CHAT

**Service + Parts (this payload):**
- Uses flat `filters` array
- Simple, direct structure
- Single filter per field

### **2. Department Filter**

```json
{
  "field": "departments",
  "operator": "IN",
  "values": ["SERVICE", "PARTS"]  // ← Both selected
}
```

**For other combinations:**
- Service only: `["SERVICE"]`
- Parts only: `["PARTS"]`
- Sales only: `["SALES"]`
- All three: `["SERVICE", "PARTS", "SALES"]`

### **3. This is a DATA Query (not count-only)**

```json
"pageInfo": {
  "start": 0,
  "rows": 50  // ← Returns actual template objects
}
```

**Difference:**
- **Count query:** `rows: 0` → Only returns `data.count`
- **Data query:** `rows: 50` → Returns `data.count` + `data.hits` array

### **4. Filters Applied**

| Filter | Value | Meaning |
|--------|-------|---------|
| status | ACTIVE | Only active templates (not drafts/archived) |
| purposeSubType | EMAIL | Only email templates (not TEXT/CHAT/PDF) |
| visibleOnUI | true | Only templates visible in UI |
| departments | SERVICE, PARTS | Templates from both departments |

### **5. Excludes Large Fields**

```json
"excludeFields": [
  "body", "htmlBody", "subject", "htmlSubject", "preHeader", "languages"
]
```

**Why:** These fields contain large HTML/text content. Excluding them makes the response smaller and faster.

---

## 📊 Expected Response Structure

```json
{
  "data": {
    "key": null,
    "count": 45,  // ← Total ACTIVE EMAIL templates in SERVICE + PARTS
    "hits": [     // ← Array of up to 50 template objects
      {
        "id": "667f0c5234bfa115c6692f80",
        "templateId": "SOME_ID",
        "name": "Template Name",
        "departments": ["SERVICE"],
        "purposeSubType": "EMAIL",
        "status": "ACTIVE",
        "modifiedTime": "2024-06-28T10:15:00Z",
        // ... more fields (excluding body/htmlBody/subject etc.)
      },
      // ... more templates
    ],
    "suggest": null,
    "tekSearchHit": null,
    "projections": null,
    "groups": []
  },
  "status": "SUCCESS"
}
```

---

## 💡 Key Insights

### **Why Two Different Request Structures?**

**Theory:**
1. **Initial page load:** Uses `groupBy` to get counts for different categories (EMAIL, TEXT, CHAT) all at once
2. **After filter applied:** Uses simple `filters` to get actual template data for display

**This means:**
- Page load: Multiple count queries with `groupBy` structure
- User interaction: Simple data fetch with `filters` structure

### **The "4 APIs with count > 0" Observation**

When you apply Service + Parts filter, the page likely makes:
1. **Count queries** (groupBy structure, rows=0) - To update the category counts
2. **Data query** (filters structure, rows=50) - To display templates in the list

**Both would have `data.count` field, but:**
- Count queries: Just return the number
- Data queries: Return the number + actual template objects

---

## 🎯 What This Tells Us

### **Service + Parts EMAIL Templates**

Based on this payload, you were looking at:
- **ACTIVE** templates only
- **EMAIL** type only
- From **SERVICE + PARTS** departments combined

**The `data.count` in the response would tell us:**
- How many ACTIVE EMAIL templates exist in Service + Parts combined
- This is ONE specific query result (EMAIL only)
- There would be separate queries for TEXT, CHAT, PDF, etc.

### **Total Templates Calculation**

To get the TRUE total for Service + Parts, you'd need:
1. Count for EMAIL templates (this query)
2. Count for TEXT templates (similar query, different purposeSubType)
3. Count for CHAT templates
4. Count for PDF templates
5. etc.

Then SUM those counts = Total active templates in Service + Parts

---

## 📝 Summary

**What we learned from this payload:**

✅ **Structure:** Service + Parts uses simple `filters` array (not `groupBy`)  
✅ **Departments:** `["SERVICE", "PARTS"]` for combined filter  
✅ **Query Type:** Data fetch (rows=50), not just count  
✅ **Filters:** ACTIVE + EMAIL + visibleOnUI + Service/Parts  
✅ **Response:** Contains `data.count` + `data.hits` array

**What we still don't know:**
- The actual `data.count` value from the response
- Counts for other template types (TEXT, CHAT, PDF)
- Whether there are separate count queries with `groupBy`

**To get the complete picture:**
- Need to capture the RESPONSE to this request
- Or capture all API calls when Service + Parts is applied

---

## 🚀 Next Steps

1. **If you have the response:** Share the `data.count` value
2. **If you want to capture more:** Run the monitor while applying filters
3. **If you're done:** We have enough to understand the API structure

**The key finding:** Service + Parts uses `["SERVICE", "PARTS"]` in the departments filter! 🎉
