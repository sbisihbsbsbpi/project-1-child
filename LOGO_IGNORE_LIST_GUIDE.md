# 🚫 Logo Ignore List Guide

## Purpose

This ignore list contains UI elements that should be **excluded** when searching for and replacing logos in Tekion email templates. These are interface controls and navigation elements, **not** the actual logo images that appear in email templates.

---

## Ignored Elements

### 1. DEALER_LOGO Button (Left Sidebar)
- **ID**: `DEALER_LOGO`
- **Selector**: `[id='DEALER_LOGO']`
- **Class**: `templates_Button_buttonContainer__kq2SVPms85`
- **Location**: Left sidebar toolbar
- **Position**: top=316px, left=174px
- **Size**: 76x148px
- **Why Ignore**: This is the **draggable UI button** used to add logos to templates, not an actual logo image

### 2. DEALER_LOGO Mini Button (Canvas Area)
- **ID**: `DEALER_LOGO`
- **Selector**: `[id='DEALER_LOGO'].templates_Button_minBtnContainer__tGQDbBVBtt`
- **Class**: `templates_Button_minBtnContainer__tGQDbBVBtt`
- **Location**: Template canvas area
- **Position**: top=769px, left=750px
- **Size**: 38x22px
- **Why Ignore**: This is the **minimized UI control** in the canvas, not an actual logo image

### 3. Dealership Logo Icons
- **Selector**: `.icon-dealership-logo`, `.icon-dealership`
- **Why Ignore**: These are **icon fonts** for UI decoration, not image files

### 4. Application Navigation Logos
- **Side Nav Logo Panel**: `.root_sideNav_logoPanel__jY9KXvUhAF`
- **Header Logo Panel**: `.root_headerSkeleton_logoPanel__724Vc5EbwR`
- **Brand Logo Link**: `.root_logo_logo__jKbdgWD2mE`
- **Why Ignore**: These are **application branding** elements, not template content

---

## Quick Ignore Patterns

### Class Names to Ignore:
```
- root_sideNav_logoPanel
- root_headerSkeleton_logoPanel
- root_logo_logo
- templates_Button_buttonContainer
- templates_Button_minBtnContainer
- icon-dealership
- icon-dealership-logo
```

### IDs to Ignore:
```
- DEALER_LOGO
```

### Parent Containers to Ignore:
```
- .templates_Button_buttonContainer__kq2SVPms85
- .templates_Button_minBtnContainer__tGQDbBVBtt
```

---

## How to Find ACTUAL Logos to Replace

The **real logos** that need to be replaced (Nucar → Tilton) will be:

✅ **`<img>` tags** inside the email template editor/preview  
✅ Images with `src` containing "nucar" or "tilton"  
✅ **NOT** inside any of the ignored parent containers above  
✅ Located in the **template content area** (not in toolbars or navigation)  

---

## Usage Example

When searching for logos to replace:

```python
# Filter out ignored elements
def is_ignored_element(element):
    """Check if element should be ignored"""
    
    # Load ignore list
    with open('logo_ignore_list.json') as f:
        ignore_list = json.load(f)
    
    # Check ID
    if element.get('id') in ignore_list['ignore_patterns']['ids']:
        return True
    
    # Check class names
    element_classes = element.get('className', '')
    for ignored_class in ignore_list['ignore_patterns']['class_names']:
        if ignored_class in element_classes:
            return True
    
    # Check parent containers
    # ... (check if element is inside ignored parents)
    
    return False
```

---

## File Location

- **Ignore List**: `logo_ignore_list.json`
- **This Guide**: `LOGO_IGNORE_LIST_GUIDE.md`

---

## Summary

🚫 **IGNORE**: UI buttons, navigation logos, icon fonts  
✅ **SEARCH**: `<img>` tags in template content with "nucar" or "tilton" in src  

The ignore list ensures we only target the **actual logo images** in email templates, not the UI controls!
