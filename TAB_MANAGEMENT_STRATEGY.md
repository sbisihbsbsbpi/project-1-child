# 🗂️ Tab Management Strategy for Logo Updates

## 🚨 Why Tab Management is CRITICAL

When updating logos across multiple Tekion templates, **improper tab management causes**:

1. **❌ Lost Context** - Losing track of which template you're editing
2. **❌ Tab Proliferation** - Opening 50+ tabs for 50 templates = browser crash
3. **❌ Memory Leaks** - Each tab consumes memory, slowing down automation
4. **❌ Wrong Updates** - Updating the wrong template if you lose tab tracking
5. **❌ Failed Saves** - Trying to save in a closed/stale tab
6. **❌ Timeout Issues** - Too many tabs = slower performance
7. **❌ Race Conditions** - Multiple tabs loading simultaneously = conflicts

---

## ✅ CORRECT Tab Management Strategy

### **Option 1: Single Tab Reuse (RECOMMENDED)**

**Use ONE tab for all template edits - reuse it for each template**

```python
async def update_all_templates(templates):
    # Connect to existing browser
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Find or create ONE working tab
    working_tab = None
    for page in context.pages:
        if 'tekioncloud.com/templates' in page.url:
            working_tab = page
            break
    
    if not working_tab:
        working_tab = await context.new_page()
    
    # Use THIS SAME TAB for all templates
    for template in templates:
        # Navigate to template
        await working_tab.goto(f"https://preprodapp.tekioncloud.com/templates/edit/{template['id']}")
        await working_tab.wait_for_load_state('networkidle')
        
        # Update logo
        await update_logo_in_page(working_tab)
        
        # Save
        await save_template(working_tab)
        
        # REUSE same tab for next template
        # NO new_page() here!
    
    # Close the one tab at the end
    await working_tab.close()
```

**Benefits:**
- ✅ Only 1 tab open at a time
- ✅ Minimal memory usage
- ✅ No tab confusion
- ✅ Easy to track progress
- ✅ Clean and predictable

---

### **Option 2: Tab Pool (For Parallel Processing)**

**Use a small pool of tabs (e.g., 3-5) for parallel processing**

```python
async def update_templates_parallel(templates, pool_size=3):
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Create tab pool
    tab_pool = []
    for i in range(pool_size):
        tab = await context.new_page()
        tab_pool.append(tab)
    
    # Process templates in batches
    for i in range(0, len(templates), pool_size):
        batch = templates[i:i+pool_size]
        tasks = []
        
        for idx, template in enumerate(batch):
            tab = tab_pool[idx]
            tasks.append(update_template(tab, template))
        
        # Wait for batch to complete
        await asyncio.gather(*tasks)
    
    # Close all tabs in pool
    for tab in tab_pool:
        await tab.close()
```

**Benefits:**
- ✅ Faster (parallel processing)
- ✅ Controlled tab count
- ✅ Better resource management
- ⚠️ More complex error handling needed

---

### **Option 3: Tab Cleanup Pattern**

**Open, use, close immediately - never accumulate tabs**

```python
async def update_template_with_cleanup(template_id):
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Create new tab
    tab = await context.new_page()
    
    try:
        # Do work
        await tab.goto(f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}")
        await update_logo_in_page(tab)
        await save_template(tab)
        
    finally:
        # ALWAYS close the tab, even if error occurs
        await tab.close()
```

**Benefits:**
- ✅ Guaranteed cleanup
- ✅ No orphaned tabs
- ✅ Safe error handling

---

## 🎯 RECOMMENDED APPROACH

**For Tekion Logo Updates: Use Option 1 (Single Tab Reuse)**

```python
async def batch_update_logos(template_ids):
    """
    Update logos in multiple templates using ONE reusable tab
    """
    
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Find existing Tekion tab or create one
    working_tab = None
    for page in context.pages:
        if 'tekioncloud.com/templates' in page.url:
            working_tab = page
            print(f"✅ Using existing Tekion tab")
            break
    
    if not working_tab:
        working_tab = await context.new_page()
        print(f"✅ Created new working tab")
    
    await working_tab.bring_to_front()
    
    results = []
    
    for idx, template_id in enumerate(template_ids, 1):
        print(f"\n[{idx}/{len(template_ids)}] Processing: {template_id}")
        
        try:
            # Navigate to template (REUSING same tab)
            await working_tab.goto(
                f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}",
                wait_until='networkidle'
            )
            
            # Find and replace logo
            logo_found = await find_and_replace_logo(working_tab)
            
            if logo_found:
                # Save changes
                await save_template(working_tab)
                results.append({'id': template_id, 'status': 'success'})
            else:
                results.append({'id': template_id, 'status': 'no_logo'})
                
        except Exception as e:
            results.append({'id': template_id, 'status': 'error', 'error': str(e)})
    
    print(f"\n✅ Processed {len(template_ids)} templates using 1 tab")
    return results
```

---

## 🚫 ANTI-PATTERNS (DON'T DO THIS)

### ❌ Opening Unlimited Tabs
```python
# BAD - Opens 50 tabs for 50 templates!
for template in templates:
    new_tab = await context.new_page()  # ❌ Never closed!
    await new_tab.goto(template_url)
```

### ❌ Losing Tab References
```python
# BAD - Creates tab but doesn't track it
await context.new_page()
await page.goto(url)  # ❌ Which page? The old one!
```

### ❌ Not Cleaning Up
```python
# BAD - Never closes tabs
tab = await context.new_page()
await do_work(tab)
# ❌ Tab stays open forever
```

---

## 📊 Tab Tracking Best Practices

### 1. Always Know Your Tab Count
```python
print(f"Tabs before: {len(context.pages)}")
# ... do work ...
print(f"Tabs after: {len(context.pages)}")
```

### 2. Use Tab Identifiers
```python
# Tag tabs for easy identification
tab._custom_id = f"template_{template_id}"
```

### 3. Periodic Cleanup
```python
# Close any stale tabs before starting
for page in context.pages:
    if page.url == 'about:blank' or 'chrome-error' in page.url:
        await page.close()
```

---

## 🎯 Summary

| Approach | Tabs Used | Speed | Memory | Complexity | Best For |
|----------|-----------|-------|--------|------------|----------|
| **Single Tab Reuse** | 1 | Medium | Low | Low | **Logo updates** ✅ |
| Tab Pool | 3-5 | Fast | Medium | Medium | Large batches |
| One-shot Cleanup | N | Slow | Low | Low | One-off tasks |

**For Tekion logo replacement: Use Single Tab Reuse! ✅**
