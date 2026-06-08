#!/usr/bin/env python3
"""
Diagnostic Script - Check logo insertion issues
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🔍 LOGO INSERTION DIAGNOSTIC")
    print("=" * 100)
    
    # Template that failed: RO Invoiced
    template_id = "667f0befd4964026ee7b6e46"
    template_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            
            # Find existing tab or create new one
            pages = context.pages
            page = None
            
            for p in pages:
                if template_url in p.url:
                    page = p
                    print(f"✅ Found existing tab: {template_url}")
                    break
            
            if not page:
                page = await context.new_page()
                print(f"🌐 Opening new tab: {template_url}")
                await page.goto(template_url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
            
            print("\n📊 DIAGNOSTIC CHECKS:")
            print("=" * 100)
            
            # 1. Find logo containers
            print("\n1️⃣ DETECTING LOGO CONTAINERS:")
            containers = await page.evaluate("""
                () => {
                    const containers = [];
                    
                    // Find all TEXT_TEMPLATE elements
                    document.querySelectorAll('.TEXT_TEMPLATE[contenteditable="true"]').forEach(el => {
                        const parent = el.closest('[data-cell-identifier]');
                        const cellId = parent?.getAttribute('data-cell-identifier');
                        
                        if (cellId && (cellId.includes('Logo 1') || cellId.includes('Logo 2'))) {
                            const rect = el.getBoundingClientRect();
                            const isEmpty = el.textContent.trim() === '' && !el.querySelector('img');
                            
                            containers.push({
                                id: el.id,
                                cellId: cellId,
                                isEmpty: isEmpty,
                                visible: rect.width > 0 && rect.height > 0,
                                rect: {
                                    top: rect.top,
                                    left: rect.left,
                                    width: rect.width,
                                    height: rect.height
                                },
                                hasImages: el.querySelectorAll('img').length,
                                textContent: el.textContent.substring(0, 50)
                            });
                        }
                    });
                    
                    return containers;
                }
            """)
            
            print(f"   Found {len(containers)} logo containers:")
            for i, c in enumerate(containers, 1):
                status = "✅ EMPTY" if c['isEmpty'] else "⚠️  HAS CONTENT"
                visible = "👁️ VISIBLE" if c['visible'] else "❌ HIDDEN"
                print(f"   {i}. {c['cellId']} - {status} - {visible}")
                print(f"      ID: {c['id']}")
                print(f"      Rect: {c['rect']}")
                if not c['isEmpty']:
                    print(f"      Content: {c['textContent']}")
                    print(f"      Images: {c['hasImages']}")
            
            if not containers:
                print("   ❌ NO LOGO CONTAINERS FOUND!")
                return
            
            # 2. Test clicking first empty container
            empty_containers = [c for c in containers if c['isEmpty']]
            if not empty_containers:
                print("\n   ⚠️  No empty containers to test")
                return
            
            test_container = empty_containers[0]
            print(f"\n2️⃣ TESTING CONTAINER CLICK: {test_container['cellId']}")
            print(f"   Container ID: {test_container['id']}")
            
            # Try clicking
            target_selector = f'div.TEXT_TEMPLATE[id="{test_container["id"]}"][contenteditable="true"]'
            print(f"   Selector: {target_selector}")
            
            try:
                await page.click(target_selector, force=True, timeout=5000)
                print("   ✅ Click successful (force)")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"   ❌ Click failed: {e}")
                # Try JS click
                try:
                    await page.evaluate(f"""
                        document.querySelector('{target_selector.replace("'", "\\'")}').click()
                    """)
                    print("   ✅ JavaScript click successful")
                    await asyncio.sleep(2)
                except Exception as e2:
                    print(f"   ❌ JavaScript click also failed: {e2}")
                    return
            
            # 3. Check if toolbar appeared
            print(f"\n3️⃣ CHECKING FOR TOOLBAR:")
            toolbar_info = await page.evaluate("""
                () => {
                    // Look for toolbar/menu with insert image button
                    const toolbarSelectors = [
                        '[class*="toolbar"]',
                        '[class*="menu"]',
                        '[class*="editor-toolbar"]',
                        '[class*="ck-toolbar"]',
                        '.ql-toolbar',
                        '[role="toolbar"]'
                    ];
                    
                    const toolbars = [];
                    toolbarSelectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(tb => {
                            const rect = tb.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                toolbars.push({
                                    selector: sel,
                                    className: tb.className,
                                    visible: true,
                                    rect: {
                                        top: rect.top,
                                        left: rect.left,
                                        width: rect.width,
                                        height: rect.height
                                    },
                                    buttons: Array.from(tb.querySelectorAll('button, [role="button"], [class*="icon"]')).map(btn => ({
                                        text: btn.textContent.trim().substring(0, 30),
                                        ariaLabel: btn.getAttribute('aria-label'),
                                        className: btn.className.substring(0, 80)
                                    }))
                                });
                            }
                        });
                    });
                    
                    // Also check for floating toolbars/popovers
                    const allIcons = Array.from(document.querySelectorAll('[class*="icon-"], [aria-label*="icon"]'));
                    const visibleIcons = allIcons.filter(icon => {
                        const rect = icon.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    }).map(icon => ({
                        ariaLabel: icon.getAttribute('aria-label'),
                        className: icon.className.substring(0, 80),
                        tagName: icon.tagName
                    }));
                    
                    return {
                        toolbars: toolbars,
                        allVisibleIcons: visibleIcons.slice(0, 30)
                    };
                }
            """)
            
            print(f"   Found {len(toolbar_info['toolbars'])} visible toolbars:")
            for i, tb in enumerate(toolbar_info['toolbars'], 1):
                print(f"\n   Toolbar {i}:")
                print(f"      Selector: {tb['selector']}")
                print(f"      Rect: {tb['rect']}")
                print(f"      Buttons: {len(tb['buttons'])}")
                for j, btn in enumerate(tb['buttons'][:10], 1):
                    print(f"         {j}. {btn['ariaLabel'] or btn['text'] or 'No label'}")
            
            print(f"\n   All visible icons ({len(toolbar_info['allVisibleIcons'])}):")
            for i, icon in enumerate(toolbar_info['allVisibleIcons'], 1):
                print(f"      {i}. {icon['ariaLabel']} | {icon['tagName']} | {icon['className']}")
            
            # 4. Look specifically for insert image button
            print(f"\n4️⃣ SEARCHING FOR INSERT IMAGE BUTTON:")
            insert_btn_info = await page.evaluate("""
                () => {
                    const selectors = [
                        '.icon-insert-image',
                        '[aria-label*="insert" i][aria-label*="image" i]',
                        '[class*="insert"][class*="image"]',
                        '[title*="Insert Image" i]',
                        'button:has-text("Image")',
                        'button:has-text("Insert")'
                    ];
                    
                    const results = [];
                    selectors.forEach(sel => {
                        try {
                            const els = document.querySelectorAll(sel);
                            if (els.length > 0) {
                                results.push({
                                    selector: sel,
                                    count: els.length,
                                    found: true
                                });
                            }
                        } catch(e) {
                            results.push({
                                selector: sel,
                                error: e.message
                            });
                        }
                    });
                    
                    return results;
                }
            """)
            
            found_any = False
            for result in insert_btn_info:
                if result.get('found'):
                    print(f"   ✅ {result['selector']} - Found {result['count']} elements")
                    found_any = True
                elif result.get('error'):
                    print(f"   ⚠️  {result['selector']} - Error: {result['error']}")
                else:
                    print(f"   ❌ {result['selector']} - Not found")
            
            if not found_any:
                print("\n   ❌ NO INSERT IMAGE BUTTON FOUND!")
                print("\n   💡 This suggests the toolbar is not appearing when clicking the container.")
                print("   💡 Possible reasons:")
                print("      1. The editor needs different interaction (double-click, specific focus)")
                print("      2. The toolbar appears in a different location")
                print("      3. The editor type is different than expected")
            
            print("\n" + "=" * 100)
            print("✅ DIAGNOSTIC COMPLETE")
            print("=" * 100)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
