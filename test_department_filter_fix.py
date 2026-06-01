#!/usr/bin/env python3
"""
Test Department Filter - Debug and Fix
Tests the exact same filter logic as the integrated button
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright


async def test_filter_application():
    """
    Test the department filter with detailed debugging
    """
    
    print("=" * 100)
    print("🧪 TESTING DEPARTMENT FILTER - SAME CODE AS BUTTON")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        try:
            # Connect to browser
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected via CDP\n")
            
            context = browser.contexts[0]
            
            # Navigate to templates page
            templates_url = "https://preprodapp.tekioncloud.com/templates/list"
            
            # Check for existing tab
            page = None
            for existing_page in context.pages:
                if templates_url in existing_page.url or '/templates/list' in existing_page.url:
                    page = existing_page
                    print(f"✅ Found existing templates list tab")
                    print(f"   URL: {existing_page.url}")
                    break
            
            # If not found, open new tab
            if not page:
                print(f"Opening new tab: {templates_url}")
                page = await context.new_page()
                await page.goto(templates_url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
                print("✅ Templates page loaded")
            else:
                # Reload existing page
                print("🔄 Refreshing existing tab...")
                await page.reload(wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
                print("✅ Tab refreshed")
            
            print("\n" + "=" * 100)
            print("🔍 STEP 1: INSPECT DROPDOWN BEFORE CLICKING")
            print("=" * 100)
            
            # Inspect the dropdown
            dropdown_info = await page.evaluate("""
                () => {
                    const triggers = Array.from(document.querySelectorAll('.ant-dropdown-trigger'));
                    return triggers.map((t, i) => ({
                        index: i,
                        text: t.textContent.trim().substring(0, 50),
                        className: t.className,
                        tagName: t.tagName,
                        isVisible: t.offsetParent !== null,
                        hasClickListener: true
                    }));
                }
            """)
            
            print(f"\nFound {len(dropdown_info)} dropdown triggers:")
            for info in dropdown_info:
                print(f"  [{info['index']}] {info['tagName']}: '{info['text']}'")
                print(f"      Visible: {info['isVisible']}, Classes: {info['className'][:80]}")
            
            print("\n" + "=" * 100)
            print("🔍 STEP 2: FINDING DEPARTMENT DROPDOWN")
            print("=" * 100)
            
            # Find department dropdown (same logic as integrated code)
            dropdown_clicked = await page.evaluate("""
                () => {
                    const triggers = Array.from(document.querySelectorAll('.ant-dropdown-trigger'));
                    
                    const deptDropdown = triggers.find(t => 
                        t.textContent.includes('Sales') || 
                        t.textContent.includes('Service') || 
                        t.textContent.includes('Parts')
                    );
                    
                    if (deptDropdown) {
                        console.log('Found department dropdown:', deptDropdown);
                        return { 
                            success: true, 
                            text: deptDropdown.textContent.trim(),
                            tagName: deptDropdown.tagName,
                            className: deptDropdown.className
                        };
                    }
                    return { success: false, error: 'Department dropdown not found' };
                }
            """)
            
            if not dropdown_clicked.get('success'):
                print(f"❌ Failed to find department dropdown: {dropdown_clicked.get('error')}")
                return
            
            print(f"✅ Found department dropdown:")
            print(f"   Tag: {dropdown_clicked.get('tagName')}")
            print(f"   Text: {dropdown_clicked.get('text')[:100]}")
            print(f"   Classes: {dropdown_clicked.get('className')[:80]}")

            print("\n" + "=" * 100)
            print("🔍 STEP 3: TRYING DIFFERENT CLICK METHODS")
            print("=" * 100)

            # Method 1: JavaScript click (current implementation)
            print("\n📍 Method 1: JavaScript .click()")
            js_click_result = await page.evaluate("""
                () => {
                    const triggers = Array.from(document.querySelectorAll('.ant-dropdown-trigger'));
                    const deptDropdown = triggers.find(t =>
                        t.textContent.includes('Sales') ||
                        t.textContent.includes('Service') ||
                        t.textContent.includes('Parts')
                    );

                    if (deptDropdown) {
                        deptDropdown.click();
                        return { success: true };
                    }
                    return { success: false };
                }
            """)
            print(f"   Result: {js_click_result}")
            await asyncio.sleep(2)

            # Check if menu appeared
            menu_visible = await page.evaluate("""
                () => {
                    const menu = document.querySelector('.ant-dropdown-menu');
                    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                    const visibleCheckboxes = Array.from(checkboxes).filter(cb => {
                        const style = window.getComputedStyle(cb);
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    });

                    return {
                        menuExists: !!menu,
                        menuVisible: menu ? menu.offsetParent !== null : false,
                        totalCheckboxes: checkboxes.length,
                        visibleCheckboxes: visibleCheckboxes.length,
                        checkboxDetails: visibleCheckboxes.slice(0, 5).map(cb => ({
                            type: cb.type,
                            dataTest: cb.getAttribute('data-test'),
                            dataTestId: cb.getAttribute('data-testid'),
                            name: cb.name,
                            id: cb.id,
                            parentText: cb.parentElement ? cb.parentElement.textContent.trim().substring(0, 30) : ''
                        }))
                    };
                }
            """)

            print(f"\n   After JS click:")
            print(f"      Menu exists: {menu_visible['menuExists']}")
            print(f"      Menu visible: {menu_visible['menuVisible']}")
            print(f"      Total checkboxes: {menu_visible['totalCheckboxes']}")
            print(f"      Visible checkboxes: {menu_visible['visibleCheckboxes']}")
            if menu_visible['checkboxDetails']:
                print(f"      Checkbox samples:")
                for cb in menu_visible['checkboxDetails']:
                    print(f"         - data-test: {cb['dataTest']}, parent: '{cb['parentText']}'")

            # Close any open menu
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)

            print("\n📍 Method 2: Playwright click() with selector")
            try:
                # Find the exact element with text
                await page.click('.ant-dropdown-trigger:has-text("Sales")', timeout=5000)
                print("   ✅ Playwright click executed")
                await asyncio.sleep(2)

                # Check if menu appeared
                menu_visible_2 = await page.evaluate("""
                    () => {
                        const menu = document.querySelector('.ant-dropdown-menu');
                        const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"]'))
                            .filter(cb => {
                                const style = window.getComputedStyle(cb);
                                return style.display !== 'none' && style.visibility !== 'hidden';
                            });

                        return {
                            menuVisible: menu ? menu.offsetParent !== null : false,
                            visibleCheckboxes: checkboxes.length
                        };
                    }
                """)

                print(f"   After Playwright click:")
                print(f"      Menu visible: {menu_visible_2['menuVisible']}")
                print(f"      Visible checkboxes: {menu_visible_2['visibleCheckboxes']}")

                if menu_visible_2['visibleCheckboxes'] > 0:
                    print("\n   ✅ SUCCESS! Dropdown opened with Playwright click!")
                else:
                    print("\n   ❌ Dropdown still didn't open")

            except Exception as e:
                print(f"   ❌ Playwright click failed: {e}")

            # Close menu
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)

            print("\n📍 Method 3: Playwright locator click")
            try:
                # Use locator API
                locator = page.locator('.ant-dropdown-trigger').filter(has_text="Sales").first
                await locator.click(timeout=5000)
                print("   ✅ Locator click executed")
                await asyncio.sleep(2)

                menu_visible_3 = await page.evaluate("""
                    () => {
                        const menu = document.querySelector('.ant-dropdown-menu');
                        return menu ? menu.offsetParent !== null : false;
                    }
                """)

                print(f"   Menu visible after locator click: {menu_visible_3}")

            except Exception as e:
                print(f"   ❌ Locator click failed: {e}")

            print("\n" + "=" * 100)
            print("🔍 STEP 4: DETAILED DOM INSPECTION")
            print("=" * 100)

            dom_structure = await page.evaluate("""
                () => {
                    const triggers = Array.from(document.querySelectorAll('.ant-dropdown-trigger'));
                    const deptTrigger = triggers.find(t =>
                        t.textContent.includes('Sales') ||
                        t.textContent.includes('Service') ||
                        t.textContent.includes('Parts')
                    );

                    if (!deptTrigger) return { found: false };

                    return {
                        found: true,
                        outerHTML: deptTrigger.outerHTML.substring(0, 500),
                        children: Array.from(deptTrigger.children).map(c => ({
                            tagName: c.tagName,
                            className: c.className,
                            text: c.textContent.trim().substring(0, 50)
                        })),
                        parent: {
                            tagName: deptTrigger.parentElement.tagName,
                            className: deptTrigger.parentElement.className
                        }
                    };
                }
            """)

            if dom_structure['found']:
                print("\n📋 Department Dropdown Structure:")
                print(f"   HTML: {dom_structure['outerHTML']}")
                print(f"\n   Children ({len(dom_structure['children'])}):")
                for child in dom_structure['children']:
                    print(f"      - <{child['tagName']}> class='{child['className'][:50]}' text='{child['text']}'")
                print(f"\n   Parent: <{dom_structure['parent']['tagName']}> class='{dom_structure['parent']['className'][:50]}'")

            print("\n" + "=" * 100)
            print("✅ TEST COMPLETE - Check results above")
            print("=" * 100)

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_filter_application())

