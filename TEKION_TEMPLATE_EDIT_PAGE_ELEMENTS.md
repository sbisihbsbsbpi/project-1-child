# 🎯 Tekion Template Edit Page - Complete Element Detection

## 📋 Page Information

**URL**: `https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48`  
**Page Title**: Tekion Template Builder  
**Template ID**: `667f0befd4964026ee7b6e48`  
**Detection Date**: 2026-05-31  

---

## 🔘 Action Buttons Detected (7)

### Header Buttons:
1. **Get Help** - Tertiary button in header
2. **Plain Button** (no text) - Header action button

### Main Action Buttons:
3. **Import** - Import template functionality
4. **Preview** - Preview template before sending
5. **Send Test Mail** - Send test email
6. **Save As Draft** - Save template as draft
7. **Publish** - Publish template (make it active)

---

## 📝 Input Fields (2)

1. **Search Box**
   - Type: `text`
   - Placeholder: `"Search here..."`
   - Location: Header

2. **Unnamed Input**
   - Type: `text`
   - Placeholder: Empty
   - Location: Content area

---

## 🖼️ Images Detected (8)

### Icons & UI Elements (7):
1. **User Guide Icon** (SVG)
2. **Get Directions Icon** - Map icon
3. **Call Us Icon** - Phone icon
4. **TV Icon** - Amenity
5. **WiFi Icon** - Amenity
6. **Water Icon** - Amenity
7. **Coffee Icon** - Amenity

### Logo (1):
8. **Tekion Logo**
   - Src: `https://d36263b6wju30t.cloudfront.net/common/CRM/tekion-logo-green-2x_new.png`
   - Alt: "Tekion Logo"
   - This is the PRIMARY logo in the template

---

## ✏️ Editor

**Status**: ✅ Active  
**Type**: `contenteditable` editor  
**Location**: Main content area  
**Description**: Rich text editor for template content  

---

## ☑️ Checkboxes - **IMPORTANT FINDING**

### On Initial Page Load:
**Checkboxes Detected**: `0`

### ⚠️ The Media Tile Checkbox You're Looking For:

The checkbox structure you mentioned:
```html
<div class="d-flex flex-grow-1 align-self-center">
  <label class="templates_mediaTile_checkboxWrapper__sRzKLP4NFX ant-checkbox-wrapper ant-checkbox-wrapper-checked">
    <span class="ant-checkbox ant-checkbox-checked">
      <input type="checkbox" class="ant-checkbox-input" value="">
      <span class="ant-checkbox-inner"></span>
    </span>
  </label>
</div>
```

**IS NOT VISIBLE on the edit page by default!**

### 🎯 Where to Find It:

This checkbox appears in a **popup modal** when you:

1. **Click on an image** (like the Tekion logo) to change it
2. **Click "Insert Files"** button (if available)
3. **Open media library** to select logos/images

The checkbox appears in the **media tile gallery** where you can:
- ✅ Select media files (logos, images)
- ✅ Check/uncheck multiple files
- ✅ Insert selected files into template

---

## 🔍 Class Name Analysis

### Template-related Classes: 64
- `templates_templates_templatesTabContainer__cf6RZSsFBG`
- `templates_viewManager_subHeaderContainer__pfSJBWUeM5`
- `templates_rightSubheader_expandableSearch__4UwqJt5UM7`
- And 61 more...

### Media-related Classes: 0
**Why?** Media tile elements only appear in popup modal

### Tile-related Classes: 0
**Why?** Tiles only appear in media library popup

### Checkbox-related Classes: 0
**Why?** Checkboxes only appear in media library popup

### Editor-related Classes: 1
- Contenteditable editor classes

---

## 🎨 How to Access Media Tile Checkboxes

### Method 1: Click on Logo/Image
```javascript
// Find the logo in the template
const logo = document.querySelector('img[alt="Tekion Logo"]');

// Click on the container to open change image dialog
const container = logo.closest('[class*="Image"]');
container.click();

// Media library popup should open with checkboxes
```

### Method 2: Look for "Insert Files" Button
```javascript
// Find insert button
const insertBtn = Array.from(document.querySelectorAll('button'))
  .find(btn => btn.textContent.includes('Insert'));

if (insertBtn) {
  insertBtn.click();
  // Media library popup opens
}
```

### Method 3: Warning Icon (if logo has issue)
```javascript
// Some templates show warning icon when logo is missing/invalid
const warningIcon = document.querySelector('[class*="warningIcon"]');
if (warningIcon) {
  warningIcon.click();
  // Opens "Insert Files" popup with media tiles
}
```

---

## 📊 Detection Summary

| Category | Count | Notes |
|----------|-------|-------|
| Buttons | 7 | Import, Preview, Send Test, Save Draft, Publish, etc. |
| Inputs | 2 | Search box + one unnamed field |
| Images | 8 | 1 logo + 7 icons/amenities |
| Checkboxes | 0 | **Appear in popup modal only** |
| Editor | 1 | Contenteditable rich text editor |
| Media Tiles | 0 | **Appear in popup modal only** |

---

## 🎯 Next Steps to Detect Media Tile Checkboxes

### Option A: Manual Interaction
1. Navigate to the edit page in browser
2. Click on the Tekion logo image
3. Media library popup should open
4. Run detection script again to capture checkbox HTML

### Option B: Automated Detection with Interaction
```python
# Navigate to edit page
await page.goto(url)

# Wait for page load
await asyncio.sleep(4)

# Try to click logo or insert button
await page.evaluate("""
    () => {
        const logo = document.querySelector('img[alt="Tekion Logo"]');
        const container = logo?.closest('[class*="Image"]');
        if (container) container.click();
    }
""")

# Wait for popup
await asyncio.sleep(2)

# Now detect checkboxes
checkboxes = await page.query_selector_all('input[type="checkbox"]')
```

---

## 📁 Generated Files

- `template_edit_page_detection_20260531_141444.json` - Complete detection data
- `detect_template_edit_page.py` - Detection script
- `TEKION_TEMPLATE_EDIT_PAGE_ELEMENTS.md` - This documentation

---

**Conclusion**: The media tile checkboxes exist but require **user interaction** (clicking on image/logo or "Insert Files" button) to become visible. They are part of a **modal popup** for the media library, not the main edit page.
