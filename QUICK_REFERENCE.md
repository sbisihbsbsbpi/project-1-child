# Logo Replacement Automation - Quick Reference

## 🚀 Quick Start (1-2-3)

```bash
# 1. Start browser with debugging
/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser --remote-debugging-port=9223 &

# 2. Open template in browser
# Navigate to: https://preprodapp.tekioncloud.com/templates/edit/{templateId}

# 3. Run automation
python3 logo_replacement_automation.py
```

## 📋 Common Commands

### Run Full Automation (Default)
```bash
python3 logo_replacement_automation.py
```
- Replaces logo
- Centers alignment
- Enlarges to 160px
- Publishes changes

### Run Tests
```bash
python3 test_logo_automation.py
```

### Interactive Examples
```bash
python3 example_logo_configs.py
```

## ⚙️ Configuration Quick Reference

### Basic Config
```python
config = LogoReplacementConfig(
    old_logo_media_id="6a0c6722864813539e4da7ae",
    new_logo_media_id="6a19132b6697f36de6236fb1",
    new_logo_name="Tilton.png"
)
```

### Custom Port
```python
config = LogoReplacementConfig(
    ...,
    chrome_debug_port=9222  # Different port
)
```

## 🎛️ Workflow Options

### Full Workflow (Everything)
```python
await automation.execute_full_workflow(
    center_align=True,
    enlarge=True,
    target_width=160,
    publish=True
)
```

### Preview Only (No Publish)
```python
await automation.execute_full_workflow(
    center_align=True,
    enlarge=True,
    target_width=160,
    publish=False  # ← Preview mode
)
```

### Just Replace (No Formatting)
```python
await automation.execute_full_workflow(
    center_align=False,
    enlarge=False,
    publish=False
)
```

### Custom Size
```python
await automation.execute_full_workflow(
    enlarge=True,
    target_width=200,  # ← 200px instead of 160px
    publish=True
)
```

## 🔍 Finding Media IDs

### From Browser DevTools
```javascript
// In browser console, find image element
img = document.querySelector('img[src*="amazonaws"]')

// Extract media ID from URL
img.src.match(/([a-f0-9]{24})/)[1]
// Returns: "6a19132b6697f36de6236fb1"
```

### From Network Tab
1. Open DevTools → Network tab
2. Upload/view image
3. Look at request URL
4. Media ID is the 24-character hex string

## 📊 Status Indicators

### Logs to Watch For

✅ **Success**
```
✅ Connected to browser
✅ Old logo found and marked
✅ Clicked Insert button
✅ Logo replacement successful!
✅ WORKFLOW COMPLETED SUCCESSFULLY!
```

❌ **Errors**
```
❌ Template tab not found
❌ Old logo not found in template
❌ Insert button not found
❌ Logo replacement failed
```

⚠️ **Warnings**
```
⚠️  Center Align button not found
⚠️  Logo size unchanged
⚠️  Modal still open - publish might have failed
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection failed" | Start browser with `--remote-debugging-port=9223` |
| "Template tab not found" | Open template edit page in browser |
| "Old logo not found" | Check media ID is correct |
| "New logo not found" | Verify logo is uploaded to media library |
| Modal won't close | Check network - might be slow response |

## 📁 Log Files

Logs saved to:
```
logo_replacement_YYYYMMDD_HHMMSS.log
```

View live:
```bash
tail -f logo_replacement_*.log
```

## 🔧 Manual Step-by-Step

If automation fails, manual fallback:

```python
automation = LogoReplacementAutomation(config)

# Step 1
await automation.connect()

# Step 2
state = await automation.detect_current_state()
print(state)

# Step 3
await automation.replace_logo()

# Step 4
await automation.center_align_logo()

# Step 5
await automation.enlarge_logo(160)

# Step 6
await automation.publish_changes()
```

## 🎯 Media IDs Reference

### Known Logos

| Logo | Media ID | Size |
|------|----------|------|
| Old Nucar | `6a0c6722864813539e4da7ae` | 80x21px |
| Tilton.png | `6a19132b6697f36de6236fb1` | 228x138px |

### Add Your Logos
```python
# Add to example_logo_configs.py
YOUR_LOGO_CONFIG = LogoReplacementConfig(
    old_logo_media_id="YOUR_OLD_ID",
    new_logo_media_id="YOUR_NEW_ID",
    new_logo_name="YourLogo.png"
)
```

## 📞 Support

Check these files for detailed info:
- `README_LOGO_AUTOMATION.md` - Full documentation
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `example_logo_configs.py` - Code examples

---

**Pro Tip**: Run with `publish=False` first to preview changes before committing! 💡
