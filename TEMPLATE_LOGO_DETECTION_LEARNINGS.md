# Template Logo Detection Learnings

**Updated:** 2026-05-30

## 📊 Analysis Results from First Template

### Template: RO Payment Link (ID: 667f0befd4964026ee7b6ea4)

---

## ✅ What We Learned

### 1. Logo Storage Patterns

**Pattern A: Thumbnail Field Only** ⭐ (Detected in first template)
```json
{
  "thumbnail": {
    "mediaId": "630f4b45e21b8400077a8e0c"
  }
}
```

- Logo is stored in `template.thumbnail.mediaId` field
- Logo is **NOT** rendered in the template body HTML
- Logo is **NOT** visible in the DOM when viewing the template
- **Update Method:** Direct API PATCH to `thumbnail.mediaId` field ✅

**Pattern B: INSERT_HEADER Component** (Not found in first template)
```json
{
  "body": [
    {
      "key": "INSERT_HEADER",
      "componentProps": {
        "html": "<img src='{{MEDIA_URL_6a19132b6697f36de6236fb1}}' />"
      }
    }
  ]
}
```

- Logo embedded in header HTML using `{{MEDIA_URL_xxx}}` template variable
- **Update Method:** Regex replace media ID in HTML string

**Pattern C: INSERT_IMAGE Component** ⭐ (FOUND in first template!)
```json
{
  "body": [
    {
      "key": "INSERT_IMAGE",
      "componentProps": {
        "mediaId": "6a19132b6697f36de6236fb1"
      }
    }
  ]
}
```

- Logo as standalone image component
- **Update Method:** Direct field replacement in component props

**Pattern D: Dual Storage (Thumbnail + INSERT_IMAGE)** ⭐ (**ACTUAL pattern in first template!**)
```json
{
  "thumbnail": {
    "mediaId": "630f4b45e21b8400077a8e0c"
  },
  "body": [
    {
      "key": "INSERT_IMAGE",
      "componentProps": {
        "selectedImage": {
          "mediaId": "630f4b45e21b8400077a8e0c"  // SAME ID!
        }
      }
    }
  ]
}
```

- Logo stored in BOTH places (redundant)
- **Visual Placement:** INSERT_IMAGE is component #2, so logo appears **near top of email** (after greeting)
- **Update Method:** Must update BOTH locations! ✅
  1. Update `thumbnail.mediaId`
  2. Update `body[X].componentProps.selectedImage.mediaId`

---

## 🚫 What's NOT a Logo

### UI Icons in Editor (False Positives to Avoid)

**Example Found:**
```
Type:     data:image/svg+xml;base64,... (inline SVG)
Alt:      "userGuide"
Size:     28x28 pixels
Purpose:  Help icon in editor UI
```

**Rejection Heuristics:**
- ❌ Data URLs (especially inline SVG)
- ❌ Alt text contains: icon, guide, help, menu, button
- ❌ Size < 40x40 pixels (too small for logos)
- ❌ No media ID found in src

---

## 📏 Updated Size Thresholds

| Element Type | Width | Height | Reasoning |
|--------------|-------|--------|-----------|
| **Logo (typical)** | 60-300px | 20-150px | Based on real logo sizes |
| **UI Icon** | < 40px | < 40px | Editor interface elements |
| **Minimum detection** | 20px | 10px | Safety threshold |

**Aspect Ratio for Logos:** 1.5 to 8.0 (wide horizontal logos)

---

## 🎯 Detection Confidence Scoring

| Signal | Points | Example |
|--------|--------|---------|
| Known media ID match | +40 | `6a19132b6697f36de6236fb1` |
| Filename contains "logo" | +30 | `dealership-logo.png` |
| Alt text contains "logo" | +20 | `alt="Company Logo"` |
| Typical logo size | +20 | 200x60 pixels |
| Logo aspect ratio | +15 | 3.5:1 ratio |
| Logo position | +15 | bottom-center, top-center |
| Logo container class | +15 | class="footer-logo" |
| **UI icon rejection** | **-50** | data:image/svg, alt="icon" |

**Threshold:** ≥50 points = Logo candidate

---

## 📊 URL Pattern Distribution

From first template analysis:

| Pattern | Count | Purpose |
|---------|-------|---------|
| `data:image/svg+xml;base64,...` | 1 | UI icons (NOT logos) |
| `https://.../{24-char-hex}...` | 0 | Media library images |
| `/api/media/...` | 0 | Relative media URLs |

**Learning:** Templates may have NO visible logos in DOM if using thumbnail-only pattern!

---

## 🔧 Update Strategies by Pattern

### Strategy 1: Thumbnail Field (API-based)
```python
# PATCH /api/templatestore/u/{templateId}
{
  "thumbnail": {
    "mediaId": "NEW_LOGO_MEDIA_ID"
  }
}
```
**Pros:** Simple, reliable, no DOM manipulation  
**Cons:** Only works for thumbnail field

### Strategy 2: Body JSON Component (API-based)
```python
# Parse body JSON
# Find component with old mediaId
# Replace with new mediaId
# PATCH back to API
```
**Pros:** Works for header/image components  
**Cons:** Requires JSON parsing and regex

### Strategy 3: UI Automation (Playwright)
```python
# Click on image in editor
# Open media library
# Select new logo
# Save
```
**Pros:** Works for any logo type  
**Cons:** Brittle, slow, UI-dependent

---

## 📈 Next Steps

1. ✅ Analyzed first template (RO Payment Link)
2. ⏳ Analyze 5-10 more templates to find other patterns
3. ⏳ Build pattern-specific update logic
4. ⏳ Create automated logo replacement service

---

## 🧠 Key Insights

1. **Not all logos are visible in the DOM** - some exist only in API metadata
2. **UI icons are common false positives** - need negative signals to reject them
3. **Multiple logo patterns exist** - need strategy per pattern
4. **API-based detection is most reliable** - Level 1 detection should be primary
5. **DOM detection is supplementary** - use for visual verification only
