#!/usr/bin/env python3
"""
Helper script to open first 10 template tabs from template list page
"""

import asyncio
from playwright.async_api import async_playwright

async def open_first_10_templates():
    print("=" * 80)
    print("🌐 OPENING FIRST 10 TEMPLATE TABS")
    print("=" * 80)
    print()
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Find template list page
    list_page = None
    for page in context.pages:
        url = page.url
        if 'templates' in url:
            list_page = page
            print(f"Found page: {url}")
            break
    
    if not list_page:
        print("❌ No template page found")
        print("Please navigate to template list page first")
        await playwright.stop()
        return
    
    print(f"✅ Using page: {list_page.url}")
    print()
    
    # Get template edit URLs
    print("Detecting templates...")
    
    templates = await list_page.evaluate("""
        () => {
            const templates = [];
            
            // Find all edit buttons or template links
            const editButtons = Array.from(document.querySelectorAll('a, button'))
                .filter(el => {
                    const text = el.innerText || el.textContent || '';
                    const href = el.href || '';
                    return text.includes('Edit') || 
                           text.includes('RO Payment') ||
                           href.includes('templates/edit');
                });
            
            for (const btn of editButtons.slice(0, 10)) {
                let url = btn.href;
                
                // If it's an edit button, find the associated URL
                if (!url && btn.onclick) {
                    // Try to extract from onclick or find nearby link
                    const row = btn.closest('tr, div, li');
                    if (row) {
                        const link = row.querySelector('a[href*="templates/edit"]');
                        if (link) url = link.href;
                    }
                }
                
                // Find template name
                let name = '';
                const row = btn.closest('tr, div, li');
                if (row) {
                    const cells = row.querySelectorAll('td, div');
                    for (const cell of cells) {
                        const text = cell.innerText?.trim() || '';
                        if (text && text.length > 3 && text.length < 100 && !text.includes('Edit')) {
                            name = text;
                            break;
                        }
                    }
                }
                
                if (url) {
                    templates.push({ url, name: name || 'Template' });
                }
            }
            
            return templates;
        }
    """)
    
    print(f"Found {len(templates)} template(s)")
    print()
    
    if len(templates) == 0:
        print("❌ No templates found on this page")
        print()
        print("Alternative: Manually open template tabs")
        print("  1. Go to template list")
        print("  2. Cmd+Click on 'Edit' for each template")
        print("  3. Open first 10 templates")
        await playwright.stop()
        return
    
    # Open tabs
    opened = 0
    for idx, template in enumerate(templates[:10], 1):
        print(f"Opening {idx}/10: {template['name'][:50]}...")
        
        try:
            new_page = await context.new_page()
            await new_page.goto(template['url'])
            await asyncio.sleep(2.0)  # Wait for page load
            
            print(f"  ✅ Opened")
            opened += 1
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    print()
    print("=" * 80)
    print(f"✅ Opened {opened} template tabs")
    print("=" * 80)
    print()
    print("Next: Run batch_logo_replacement.py to process all tabs")
    
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(open_first_10_templates())
