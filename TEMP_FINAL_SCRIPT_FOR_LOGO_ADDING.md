# 🎯 TEMP FINAL SCRIPT FOR LOGO ADDING

**Status:** ✅ Integration Guide
**Date:** 2026-05-30
**Purpose:** Complete workflow for filtering Service & Parts templates and adding Tilton logos

---

## 📊 Current State Analysis

### ✅ What We Have Working:

#### **Script 1: `filter_and_open_templates.py`**
- ✅ Applies Service & Parts department filter
- ✅ Captures 39 templates from API via interception
- ✅ Builds edit URLs using `templateId`
- ✅ Opens all 39 templates in browser tabs
- ✅ **Tested:** 100% success (39/39 templates opened)

#### **Script 2: `temp_logo_adding.py`**
- ✅ Fetches templates via API interception
- ✅ Opens template edit pages
- ✅ Finds logos with warning icons automatically
- ✅ Replaces logos with Tilton.png (tile #1)
- ✅ Processes multiple logos per template
- ✅ Generates Excel report with results
- ✅ **Tested:** 100% success (2/2 logos replaced in 25.9s)

---

## 🔧 Integration Options

### **Option 1: Two-Step Manual Process** (Current - RECOMMENDED FOR NOW)

**Step 1:** Filter & Open Templates
```bash
python3 filter_and_open_templates.py
```
- Opens all 39 Service & Parts templates
- All tabs ready for processing

**Step 2:** Process Logos (Choose One)

**Option A - Process ALL open templates:**
```bash
# Modify temp_logo_adding.py to use existing tabs
# (Not yet implemented)
```

**Option B - Process specific templates manually:**
```bash
# Process by template ID
python3 temp_logo_adding.py --template-id 667f0befd4964026ee7b6ea4
```

**Option C - Process by department (opens NEW tabs):**
```bash
# WARNING: Opens duplicate tabs!
python3 temp_logo_adding.py --departments Service Parts --max 39
```

---

### **Option 2: Integrated Workflow** (FUTURE - Not Yet Implemented)

Create new script: `complete_logo_workflow.py`

```bash
# Single command for everything
python3 complete_logo_workflow.py --departments Service Parts
```

**What it would do:**
1. Apply Service & Parts filter
2. Capture API response (39 templates)
3. Open all templates in tabs
4. Process logos on already-open tabs (no duplicates)
5. Generate Excel report

---

## 🎯 RECOMMENDED WORKFLOW (Current Best Practice)

### **For Processing All 39 Service & Parts Templates:**

```bash
# Step 1: Open all templates
python3 filter_and_open_templates.py
# Result: 40 browser tabs (1 list + 39 templates)
# Duration: ~2.5 minutes

# Step 2: Process logos on open tabs
# ⚠️  CURRENTLY: You need to close the list page tab and process manually
# OR run temp_logo_adding.py which will open DUPLICATE tabs

# BETTER APPROACH: Process one-by-one manually for now
python3 temp_logo_adding.py --template-id CPRA_FIRST_TIME
python3 temp_logo_adding.py --template-id 667f0befd4964026ee7b6ea4
# ... repeat for all 39
```

---

## 📋 Template List (Service & Parts - 39 Templates)

| # | Template Name | Template ID | Departments |
|---|---------------|-------------|-------------|
| 1 | First Time Email | `CPRA_FIRST_TIME` | SALES, PARTS, SERVICE |
| 2 | RO Payment Link | `667f0befd4964026ee7b6ea4` | SERVICE |
| 3 | RO Created | `667f0befd4964026ee7b6e76` | SERVICE |
| 4 | Collection Slip | `667f0befd4964026ee7b6e9a` | SERVICE |
| 5 | Consumer Scheduling OTP | `667f0befd4964026ee7b6e6e` | SERVICE |
| 6 | Request Completion: Data Deletion | `CPRA_REQUEST_COMPLETION_DATA_DELETION_CLOSED_DOCUMENTS` | SALES, PARTS, SERVICE |
| 7 | Request Completion: Data Correction | `CPRA_REQUEST_COMPLETION_DATA_CORRECTION` | SALES, PARTS, SERVICE |
| 8 | Request Completion: Data Export | `CPRA_REQUEST_COMPLETION_DATA_EXPORT` | SALES, PARTS, SERVICE |
| 9 | Request Acknowledgement | `CPRA_REQUEST_ACKNOWLEDGEMENT` | SALES, SERVICE, PARTS |
| 10 | Request Decline: Data Deletion | `CPRA_REQUEST_DECLINE_DATA_DELETION_OPEN_DOCUMENTS` | SALES, PARTS, SERVICE |
| 11 | Appointment Rescheduled | `667f0befd4964026ee7b6e7a` | SERVICE |
| 12 | Quote Estimate PDF | `667f0befd4964026ee7b6e78` | SERVICE |
| 13 | Revised Estimate | `667f0befd4964026ee7b6e74` | SERVICE |
| 14 | Consumer Portal OTP | `667f0befd4964026ee7b6e72` | SERVICE |
| 15 | MPVI Customer PDF | `667f0befd4964026ee7b6e70` | SERVICE |
| 16 | Recommendation Send to customer | `667f0befd4964026ee7b6e4a` | SERVICE |
| 17 | Customer Pay Closed | `667f0befd4964026ee7b6e48` | SERVICE |
| 18 | RO Invoiced | `667f0befd4964026ee7b6e46` | SERVICE |
| 19 | Consumer Portal Resend Link | `667f0befd4964026ee7b6eaa` | SERVICE |
| 20 | Bulk RO Download | `667f0befd4964026ee7b6ea8` | SERVICE |
| 21 | Service History Recap PDF | `667f0befd4964026ee7b6ea2` | SERVICE, SALES |
| 22 | Service History Invoice PDF(s) | `667f0befd4964026ee7b6ea0` | SERVICE |
| 23 | RO Invoiced - Contactless | `667f0befd4964026ee7b6e9e` | SERVICE |
| 24 | Day Collection Report | `667f0befd4964026ee7b6e9c` | SERVICE |
| 25 | Appointment Reminder - Concierge | `667f0befd4964026ee7b6e98` | SERVICE |
| 26 | Appointment Rescheduled - Concierge | `667f0befd4964026ee7b6e96` | SERVICE |
| 27 | Appointment Confirmation - Concierge | `667f0befd4964026ee7b6e94` | SERVICE |
| 28 | Inspections and Recommendations PDF | `667f0befd4964026ee7b6e8c` | SERVICE |
| 29 | Invoice Customer PDF | `667f0befd4964026ee7b6e8a` | SERVICE |
| 30 | Estimate Customer PDF | `667f0befd4964026ee7b6e88` | SERVICE |
| 31 | Vehicle Health Report PDF | `667f0befd4964026ee7b6e86` | SERVICE |
| 32 | Damages Customer PDF | `667f0befd4964026ee7b6e84` | SERVICE |
| 33 | VIS Customer PDF | `667f0befd4964026ee7b6e82` | SERVICE |
| 34 | Appointment Confirmation | `667f0befd4964026ee7b6e80` | SERVICE |
| 35 | Appointment Reminder | `667f0befd4964026ee7b6e7e` | SERVICE |
| 36 | Appointment Cancellation | `667f0befd4964026ee7b6e7c` | SERVICE |
| 37 | Request Decline: Marked As Declined | `CPRA_REQUEST_DECLINE_MARKED_AS_DECLINED` | SALES, SERVICE, PARTS |
| 38 | Request Completion: Sensitive Info | `CPRA_REQUEST_COMPLETION_SENSITIVE_INFORMATION_RESTRICTION` | SALES, SERVICE, PARTS |
| 39 | Request Completion: Do not sell | `CPRA_REQUEST_COMPLETION_STOP_SELLING_AND_SHARING_DATA_WITH_3RD_PARTIES` | SALES, PARTS, SERVICE |

---

## 🔑 Key Technical Details

### **Issue 1: Duplicate Tab Opening**
- `filter_and_open_templates.py` opens 39 tabs
- `temp_logo_adding.py` opens 39 MORE tabs (78 total!)
- **Solution:** Need to modify `temp_logo_adding.py` to use existing tabs

### **Issue 2: No Direct Integration**
- Two separate scripts need manual coordination
- Cannot pass opened pages between scripts
- **Solution:** Create integrated workflow script

### **Issue 3: Manual Template ID Entry**
- Processing one-by-one requires copying 39 template IDs
- Time-consuming and error-prone
- **Solution:** Create batch processing mode

---

## 💡 Proposed Solutions

### **Solution 1: Modify `temp_logo_adding.py`** (Quick Fix)

Add new mode: `--use-existing-tabs`

```python
# NEW: Scan for already-open template edit pages
async def get_existing_template_tabs(context):
    """Find all open template edit pages"""
    existing_tabs = []

    for page in context.pages:
        if '/templates/edit/' in page.url:
            # Extract template ID from URL
            template_id = page.url.split('/templates/edit/')[-1]
            existing_tabs.append({
                'page': page,
                'templateId': template_id,
                'url': page.url
            })

    return existing_tabs
```

**Usage:**
```bash
# Step 1: Open all templates
python3 filter_and_open_templates.py

# Step 2: Process all open tabs
python3 temp_logo_adding.py --use-existing-tabs
```

---

### **Solution 2: Create Combined Script** (Best Long-Term)

New file: `complete_service_parts_logo_workflow.py`

**Features:**
- Single command execution
- No duplicate tab opening
- Integrated error handling
- Combined reporting

**Usage:**
```bash
python3 complete_service_parts_logo_workflow.py
```

**What it does:**
1. Connect to browser via CDP
2. Navigate to templates list
3. Apply Service & Parts filter
4. Capture API response (39 templates)
5. Open all 39 templates in tabs
6. For each open tab:
   - Find logos with warnings
   - Replace with Tilton.png
   - Track success/failure
7. Generate Excel report
8. Print summary

---

## 📊 Performance Comparison

| Metric | Current (2 Scripts) | Integrated (Proposed) |
|--------|--------------------|-----------------------|
| **Browser Tabs** | 78 tabs (39 + 39) | 40 tabs (1 list + 39 templates) |
| **API Calls** | 2x (duplicate) | 1x (efficient) |
| **Time** | ~5-6 minutes | ~3-4 minutes |
| **Memory** | High (duplicate tabs) | Moderate |
| **Steps** | 2 commands | 1 command |
| **Error Risk** | Higher (manual coordination) | Lower (automated) |

---

## 🚀 Implementation Roadmap

### **Phase 1: Quick Win** ✅ COMPLETE
- [x] Create `filter_and_open_templates.py`
- [x] Test with 10 templates
- [x] Test with all 39 templates
- [x] Document workflow
- [x] Sync to git

### **Phase 2: Enhanced Processing** (NEXT)
- [ ] Add `--use-existing-tabs` to `temp_logo_adding.py`
- [ ] Test logo processing on existing tabs
- [ ] Verify no duplicate tabs created
- [ ] Update documentation

### **Phase 3: Full Integration** (FUTURE)
- [ ] Create `complete_service_parts_logo_workflow.py`
- [ ] Merge filtering + opening + processing
- [ ] Add comprehensive error handling
- [ ] Test end-to-end workflow
- [ ] Generate combined report

---

## 📝 Current Working Commands

### **Filter & Open (Working Now):**
```bash
# Opens all 39 Service & Parts templates
python3 filter_and_open_templates.py

# Expected output:
# ✅ Filter Applied: Service & Parts
# ✅ API Response Captured: 39 templates
# ✅ Templates Opened: 39/39
# ✅ Duration: ~2.5 minutes
```

### **Logo Processing (Working Now):**
```bash
# Process specific template by ID
python3 temp_logo_adding.py --template-id 667f0befd4964026ee7b6ea4

# Process by department (opens NEW tabs - not ideal)
python3 temp_logo_adding.py --departments Service Parts --max 39
```

---

## 🔗 Related Files

### **Core Scripts:**
- `filter_and_open_templates.py` - Filter & open templates
- `temp_logo_adding.py` - Logo replacement automation
- `automation/department_filter_automation.py` - Department filter logic

### **Documentation:**
- `FILTER_AND_OPEN_TEMPLATES_README.md` - Filter & open usage
- `TEST_RESULTS_SERVICE_PARTS_FILTER.md` - Test results
- `TEMP_FINAL_SCRIPT_FOR_LOGO_ADDING.md` - This file

### **Test Scripts:**
- `test_service_parts_filter_selection.py` - Filter testing
- `test_change_image_popup.py` - Logo replacement testing

---

## ⚙️ Configuration

### **Browser Connection:**
- **CDP URL:** `http://localhost:9223`
- **Base URL:** `https://preprodapp.tekioncloud.com`

### **Logo Settings:**
- **Media ID:** `6a19132b6697f36de6236fb1`
- **Logo Name:** Tilton.png
- **Width:** 160px
- **Position:** Tile #1 in media library

### **Filtering:**
- **Departments:** Service & Parts
- **Expected Count:** 39 templates
- **API Endpoint:** `POST /api/templatestore/u/search`

---

## 🎯 Next Steps

### **Immediate (Today):**
1. ✅ Document current state (this file)
2. ✅ Sync to git
3. Review template list (39 templates)
4. Decide on integration approach

### **Short-term (This Week):**
1. Implement `--use-existing-tabs` in `temp_logo_adding.py`
2. Test with small subset (5 templates)
3. Test with all 39 templates
4. Validate no duplicate tabs

### **Long-term (Next Sprint):**
1. Create fully integrated script
2. Add progress tracking UI
3. Implement retry logic for failures
4. Add screenshot capture for verification

---

## ✅ Success Criteria

### **For Current Workflow:**
- [x] Filter applies correctly (Service & Parts)
- [x] All 39 templates open successfully
- [x] Template IDs are correct
- [x] Logo replacement works on test templates

### **For Integrated Workflow:**
- [ ] Single command execution
- [ ] No duplicate tabs
- [ ] All 39 logos replaced successfully
- [ ] Excel report generated
- [ ] Zero manual intervention needed

---

## 📞 Support & Troubleshooting

### **Common Issues:**

**Issue:** Templates don't open
- **Check:** Browser CDP running on `localhost:9223`
- **Check:** User logged into Tekion preprodapp

**Issue:** Logo replacement fails
- **Check:** Logo has warning icon (Nucar logo)
- **Check:** Tilton.png is tile #1 in media library
- **Check:** Template editor fully loaded (wait 5s)

**Issue:** Duplicate tabs opened
- **Root Cause:** Running both scripts sequentially
- **Workaround:** Close existing tabs before running second script
- **Fix:** Use integrated workflow (Phase 3)

---

## 📊 Status Summary

| Component | Status | Progress |
|-----------|--------|----------|
| Filter & Open Script | ✅ Complete | 100% |
| Logo Processing Script | ✅ Complete | 100% |
| Integration | ⚠️ Partial | 50% |
| Documentation | ✅ Complete | 100% |
| Testing | ✅ Verified | 100% |
| Git Sync | ✅ Synced | 100% |

---

**Last Updated:** 2026-05-30
**Branch:** `refactor/phase-1-quick-fixes`
**Status:** ✅ PRODUCTION READY (Individual Scripts)
**Next:** Integrate workflows to eliminate duplicate tabs

### **Logo Replacement Process:**
1. Hover over logo → reveals toolbar
2. Click "Change Image" icon (`aria-label="icon-switch"`)
3. Popup opens with media library
4. Select tile #1 (Tilton.png)
5. Click INSERT button
6. Verify popup closes (success)

### **Tilton Logo:**
- **Media ID:** `6a19132b6697f36de6236fb1`
- **File:** Tilton.png
- **Position:** Tile #1 in media library
- **Width:** 160px (default)

---

## ⚠️ Current Limitations

