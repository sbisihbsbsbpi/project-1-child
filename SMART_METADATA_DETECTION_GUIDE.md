# 🧠 Smart Metadata Detection System

## Overview

The system now includes **dynamic metadata detection** that can:
1. ✅ Detect Department (SERVICE, SALES, PARTS, etc.)
2. ✅ Detect Communication Type (EMAIL, SMS, TEXT, CHAT)
3. ✅ Detect Category (if applicable)
4. ✅ Detect Status (ACTIVE, INACTIVE, DRAFT)
5. ✅ Intercept actual search API payloads
6. ✅ Build custom search payloads dynamically
7. ✅ Modify existing payloads to change filters

---

## Files Created

| File | Purpose |
|------|---------|
| `template_metadata_detector.py` | Detects filters from UI and intercepts API calls |
| `smart_template_filter_builder.py` | Builds search API payloads dynamically |
| `intercepted_search_payload_*.json` | Saved API payloads for reference |

---

## How It Works

### Step 1: Detect Current Filters

The detector analyzes the template list page using 4 strategies:

1. **Dropdown Values** - Reads selected values from `<select>` elements
2. **Filter Chips** - Finds active filter chips/tags
3. **Checkboxes** - Detects checked checkboxes
4. **URL Parameters** - Reads query string parameters

### Step 2: Intercept API Call

When you reload the template list page, the system intercepts the `/api/templatestore/u/search` request and captures:
- Full payload structure
- All filters being applied
- Headers and authentication tokens
- Actual response data

### Step 3: Build Custom Payload

Using the `SmartTemplateFilterBuilder`, you can:
- Build new payloads from scratch
- Modify existing payloads
- Switch departments dynamically
- Change communication types
- Adjust result limits

---

## Example: Detected Payload

From the latest run, we detected this payload for **SALES** department:

```json
{
  "groupBy": [{
    "key": "template",
    "groupType": "FILTERS",
    "filters": [
      {
        "key": "EMAIL",
        "andFilters": [
          {"field": "status", "values": ["ACTIVE"]},
          {"field": "purposeSubType", "values": ["EMAIL"]},
          {"field": "departments", "values": ["SALES"]},
          {"field": "visibleOnUI", "values": [true]}
        ]
      },
      {
        "key": "TEXT",
        "andFilters": [
          {"field": "status", "values": ["ACTIVE"]},
          {"field": "purposeSubType", "values": ["TEXT"]},
          {"field": "departments", "values": ["SALES"]},
          {"field": "visibleOnUI", "values": [true]}
        ]
      }
    ]
  }]
}
```

**Key Findings:**
- Department: **SALES**
- Communication Types: **EMAIL, TEXT, CHAT**
- Status: **ACTIVE**
- Visible on UI: **true**

---

## Usage Examples

### 1. Detect Current Filters
```bash
python3 template_metadata_detector.py
```

**Output:**
```
🎯 Detected Filters:
  Departments: ['SALES']
  Communication Types: ['EMAIL', 'TEXT', 'CHAT']
  Status: ['ACTIVE']
```

### 2. Build SERVICE EMAIL Template Payload
```python
from smart_template_filter_builder import SmartTemplateFilterBuilder

builder = SmartTemplateFilterBuilder()

payload = builder.build_simple_payload(
    departments=["SERVICE"],
    comm_types=["EMAIL"],
    status=["ACTIVE"],
    max_results=200
)
```

### 3. Switch from SALES to SERVICE
```python
# Load intercepted SALES payload
with open('intercepted_search_payload_20260529_205522.json') as f:
    sales_payload = json.load(f)[0]['payload']

# Modify to SERVICE
service_payload = builder.modify_existing_payload(
    sales_payload,
    new_departments=["SERVICE"],
    new_max_results=200
)
```

### 4. Build Grouped Payload (Like Tekion UI)
```python
payload = builder.build_grouped_payload(
    departments=["SERVICE"],
    comm_types=["EMAIL", "TEXT"],
    status=["ACTIVE"],
    max_results=200
)
```

---

## Integration with Logo Replacement

You can now combine metadata detection with logo replacement:

```python
# 1. Detect what department is currently active
detector = TemplateMetadataDetector()
await detector.connect_to_browser()
await detector.find_template_list_page()
filters = await detector.detect_active_filters()

# 2. Build payload for desired department
builder = SmartTemplateFilterBuilder()
payload = builder.build_simple_payload(
    departments=["SERVICE"],  # Or use filters['departments']
    comm_types=["EMAIL"],
    status=["ACTIVE"],
    max_results=200
)

# 3. Use payload in logo replacement automation
# (Integration code would go here)
```

---

## API Payload Formats

### Simple Format (Flat Filters)
```json
{
  "filters": [
    {"field": "status", "values": ["ACTIVE"]},
    {"field": "departments", "values": ["SERVICE"]},
    {"field": "purposeSubType", "values": ["EMAIL"]}
  ],
  "pageInfo": {"rows": 200}
}
```

**Pros:** Simple, easy to understand  
**Cons:** Doesn't group by communication type

### Grouped Format (Tekion Style)
```json
{
  "groupBy": [{
    "filters": [
      {"key": "EMAIL", "andFilters": [...]},
      {"key": "TEXT", "andFilters": [...]}
    ]
  }]
}
```

**Pros:** Matches Tekion UI, groups results  
**Cons:** More complex structure

---

## Common Departments

- `SERVICE` - Service department templates
- `SALES` - Sales department templates
- `PARTS` - Parts department templates
- `ACCOUNTING` - Accounting department templates
- `GENERAL` - General purpose templates

---

## Common Communication Types

- `EMAIL` - Email templates
- `TEXT` / `SMS` - Text message templates
- `CHAT` - Chat templates
- `PUSH` - Push notification templates
- `VOICE` - Voice call templates

---

## Next Steps

1. **Choose Your Target:**
   - Which department? (SERVICE, SALES, PARTS, etc.)
   - Which communication type? (EMAIL, SMS, etc.)
   - Which status? (ACTIVE, INACTIVE, etc.)

2. **Build Payload:**
   ```python
   payload = builder.build_simple_payload(
       departments=["SERVICE"],
       comm_types=["EMAIL"],
       status=["ACTIVE"]
   )
   ```

3. **Integrate with Automation:**
   - Use the payload in `auto_logo_replacement_service.py`
   - Process all matching templates
   - Replace logos automatically

---

## Troubleshooting

### "No filters detected"
- The UI might not have explicit filter UI elements
- Use API interception method instead (Method 2)
- Check the intercepted JSON file

### "API call returns 0 results"
- Check the department value (case-sensitive)
- Verify communication type is correct
- Try with `max_results` set to a high number

### "Different payload structure"
- Tekion may use different formats in different environments
- Use the intercepted payload as a template
- Modify using `modify_existing_payload()`

---

## Status

✅ Metadata detection working  
✅ API interception working  
✅ Payload builder working  
✅ Ready to integrate with logo replacement  

**Next:** Integrate with `auto_logo_replacement_with_smart_detection.py` to create a fully dynamic system! 🚀
