# 🚀 Template Logo Update Tool - Technical Implementation Plan

**Date:** 2026-05-29  
**Analysis:** Based on Real Template Data (35KB - 270KB payloads)

---

## 📊 Real Data Summary

**Templates Found:** 39 (SERVICE & PARTS)  
**Sizes:** 35KB - 270KB per template  
**Components per template:** 3 - 22 components  
**Logo Types:** 2 distinct types

---

## 🎯 Two Types of Logo Updates

### Type 1: Attachment/Thumbnail Logo
**Target Field:** `thumbnail.mediaId`  
**Usage:** Email attachment logo (appears in email clients as attached image)  
**Example:** Data Privacy templates (CPRA)

```json
{
  "thumbnail": {
    "mediaId": "6a1914fb6697f36de6236fb5",
    "name": null
  }
}
```

### Type 2: Header Logo (Embedded)
**Target Field:** `body` → `INSERT_HEADER` component → `{{MEDIA_URL_xxx}}`  
**Usage:** Logo embedded in email HTML header  
**Example:** Repair Orders, Service Appointments

```json
{
  "key": "INSERT_HEADER",
  "componentProps": {
    "html": "<img src='{{MEDIA_URL_6a191313710089188b66521e}}' />"
  }
}
```

**⚠️ Important:** Some templates have BOTH types with DIFFERENT media IDs!

---

## 🔧 Complete Workflow

### Step 1: Search & Display Templates
```
POST /api/templatestore/u/search
→ Returns 39 templates (lightweight, ~50KB total)
→ Show in UI with filters
```

### Step 2: Upload New Logo
```
POST /api/media/upload
→ Returns { mediaId: "NEW_ID" }
```

### Step 3: Fetch Individual Templates
```
GET /api/templatestore/u/fetch/{templateId}
→ Returns full template (35KB - 270KB)
→ Parse and prepare for update
```

### Step 4: Update Logo
**For Thumbnail:**
```javascript
template.thumbnail.mediaId = newMediaId;
```

**For Header:**
```javascript
const body = JSON.parse(template.body);
const header = body.find(c => c.key === 'INSERT_HEADER');
header.componentProps.html = 
  header.componentProps.html.replace(
    /{{MEDIA_URL_[a-f0-9]+}}/g,
    `{{MEDIA_URL_${newMediaId}}}`
  );
template.body = JSON.stringify(body);
```

### Step 5: Send Update
```
POST /api/templatestore/u/update
→ Send ENTIRE template object
→ Must include all fields (26+ required fields)
```

---

## 💻 Recommended Tech Stack (2024-2026)

### 1. Large JSON Processing
**Problem:** Templates up to 270KB need parsing  
**Solution:** Web Workers for offloading

```typescript
// Use Web Workers for JSON parsing
const worker = new Worker('/workers/templateProcessor.worker.ts');
worker.postMessage({ templates, action: 'parse' });
worker.onmessage = (e) => setParsedTemplates(e.data);
```

**Why:** Prevents UI freezing when processing 39 × 270KB = ~10MB of data

**Libraries:**
- ✅ Native Web Workers (built-in, zero dependencies)
- ✅ Comlink (makes Web Workers easier): `npm install comlink`

---

### 2. Async Batch Processing
**Problem:** 28 templates need updates, can't do all at once  
**Solution:** Concurrency control with modern patterns

```typescript
// Use p-limit or similar pattern
import pLimit from 'p-limit';

const limit = pLimit(3); // 3 concurrent requests

const results = await Promise.all(
  templates.map(template => 
    limit(() => updateTemplate(template))
  )
);
```

**Libraries:**
- ✅ **p-limit** (4.0+): `npm install p-limit` - Simple, modern
- ✅ **TanStack Pacer**: For advanced batching with progress
- ❌ Avoid: async.js (outdated, callback-based)

---

### 3. Progress Tracking
**Problem:** Users need real-time feedback  
**Solution:** State management with fine-grained updates

```typescript
// Use Zustand or React state
const [progress, setProgress] = useState({
  total: 28,
  completed: 0,
  failed: 0,
  current: null
});

// Update per template
onTemplateComplete(() => {
  setProgress(p => ({ ...p, completed: p.completed + 1 }));
});
```

**Libraries:**
- ✅ React 18+ `useState` (simple cases)
- ✅ **Zustand** (complex state): `npm install zustand`
- ✅ **TanStack Query** (for API state): `npm install @tanstack/react-query`

---

### 4. Excel Export
**Problem:** Generate results report  
**Solution:** Modern spreadsheet library

```typescript
import * as XLSX from 'xlsx';

const worksheet = XLSX.utils.json_to_sheet(results);
const workbook = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(workbook, worksheet, 'Results');
XLSX.writeFile(workbook, 'template-logo-update.xlsx');
```

**Libraries:**
- ✅ **SheetJS (xlsx)**: `npm install xlsx` - Industry standard, 2024-2026 compatible

---

## 🎨 UI Component Structure

```
TemplateLogoManager/
├── Step1: TemplateSearch
│   ├── HeaderParser (paste cURL)
│   ├── TemplateGrid (39 templates)
│   ├── Filters (department, category, has logo)
│   └── Selection (checkboxes)
├── Step2: LogoUpload
│   ├── FileUploader (drag & drop)
│   ├── Preview (show uploaded logo)
│   └── LogoTypeSelector (thumbnail vs header vs both)
├── Step3: Verification
│   ├── BeforeAfter (side-by-side preview)
│   ├── TemplateList (selected templates)
│   └── ConfirmButton
└── Step4: Execution
    ├── ProgressBar (0-100%)
    ├── LiveLog (template by template)
    ├── ResultsTable (success/fail/skipped)
    └── ExcelExport
```

---

## 📦 Recommended Dependencies

```json
{
  "dependencies": {
    "comlink": "^4.4.1",
    "p-limit": "^6.1.0",
    "xlsx": "^0.18.5",
    "@tanstack/react-query": "^5.0.0"
  }
}
```

**Total size:** ~500KB (acceptable for admin tool)

---

## ⚡ Performance Optimizations

1. **Lazy Load Web Worker:** Only load when processing >10 templates
2. **Streaming Updates:** Update UI after every 3 templates (not every one)
3. **Request Batching:** Max 3-5 concurrent API calls
4. **Template Caching:** Cache fetched templates in memory (avoid re-fetch)
5. **Debounced Search:** 300ms delay on search input

---

## 🔒 Safety Features

1. **Skip if logo exists** (default behavior)
2. **Dry run mode** (preview changes without applying)
3. **Rollback support** (keep old mediaId in report)
4. **Validation:** Verify mediaId exists before update
5. **Error recovery:** Continue on failure, report at end

---

## 🚀 Next Steps

1. ✅ Install dependencies: `p-limit`, `xlsx`, `comlink`
2. ✅ Create Web Worker for JSON processing
3. ✅ Build UI components (Step 1-4)
4. ✅ Implement batch update with concurrency control
5. ✅ Add Excel export
6. ✅ Test with real templates

**Ready to build!** 🎯
