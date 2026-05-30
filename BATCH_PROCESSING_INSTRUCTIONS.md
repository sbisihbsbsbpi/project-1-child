# Batch Logo Replacement - Step-by-Step Instructions

## 🎯 Goal
Process first 10 templates sequentially without publishing for verification

## 📋 Step 1: Open Template Tabs (MANUAL)

Since the template list page requires scrolling/clicking, please manually open the tabs:

### In Browser:
1. Go to: `https://preprodapp.tekioncloud.com/templates/list`
2. You should see "39 Result(s)" - list of templates
3. For the **first 10 templates** in the list:
   - **Cmd+Click** (Mac) or **Ctrl+Click** (Windows) on each template name or "Edit" button
   - This will open each in a new tab
4. After opening 10 tabs, proceed to Step 2

### Quick Method:
- Right-click template → "Open Link in New Tab"
- Repeat for first 10 templates

---

## 🚀 Step 2: Run Batch Processing

Once you have 10 template tabs open, run:

```bash
python3 batch_logo_replacement.py
```

### What it will do:
✅ Detect all open template tabs  
✅ Process each sequentially (one at a time)  
✅ Replace logo with Tilton.png  
✅ Center align  
✅ Enlarge to 160px  
❌ **NOT publish** (for your verification)  
✅ Keep all tabs open for manual review  

---

## 🔍 Step 3: Verify Changes

After processing completes:

1. **Review each tab** in the browser
2. **Check that**:
   - ✅ Old Nucar logo is replaced with Tilton logo
   - ✅ Logo is center aligned
   - ✅ Logo is larger (160px width)
3. **If satisfied**, you can publish manually or run publish script

---

## 📊 Step 4: Review Results

The script will output:
- Summary of all processed templates
- Success/failure status for each
- Log file: `batch_logo_replacement_YYYYMMDD_HHMMSS.log`

Example output:
```
================================================================================
📊 BATCH PROCESSING SUMMARY
================================================================================
1. ✅ RO Payment Link - success
2. ✅ Service Reminder - success
3. ❌ Appointment Confirmation - failed
...
Total: 8/10 successful

🔍 VERIFICATION MODE: All tabs kept open for manual verification
   Please review each template in the browser tabs
```

---

## 🔧 Troubleshooting

### "No template tabs found"
- Make sure you opened the template **EDIT** pages, not just the list
- URLs should contain: `templates/edit/XXXXX`

### "Template already has new logo"
- Template was processed before, will skip automatically

### Processing fails on a template
- Script will continue to next template
- Failed template tab will remain open
- Check the log file for error details

---

## ✅ Alternative: Process Currently Open Tabs

If you already have some template tabs open:

```bash
# This will process whatever templates are currently open
python3 batch_logo_replacement.py
```

The script automatically detects all open template tabs!

---

## 📝 Current Status

**Browser Status**: You have the template list page open  
**Action Needed**: Open first 10 individual template tabs  
**Ready to Run**: `batch_logo_replacement.py` once tabs are open  

---

## 🎬 Ready to Start?

1. ✅ Open 10 template tabs (Cmd+Click on each)
2. ✅ Run: `python3 batch_logo_replacement.py`
3. ✅ Wait for completion (~3-5 minutes)
4. ✅ Review all tabs
5. ✅ Decide: publish or make adjustments

**Let me know when you've opened the tabs and I'll start the batch processing!** 🚀
