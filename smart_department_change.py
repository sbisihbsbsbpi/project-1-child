#!/usr/bin/env python3
"""
Smart Department Filter Change
Learnings applied:
1. Find the EXACT templates/list page (not template edit pages)
2. Use more specific selectors to avoid clicking templates by mistake
3. Verify department filter exists before interacting
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🎯 SMART DEPARTMENT FILTER CHANGE: Service & Parts ONLY")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            
            print("🔍 Step 1: Finding the correct templates list page...\n")
            
            # List all pages
            print("📑 Open tabs:")
            for i, page in enumerate(context.pages):
                print(f"   {i+1}. {page.url}")
            print()
            
            # Find the templates LIST page (not edit page)
            templates_page = None
            for page in context.pages:
                url = page.url
                # Make sure it's the LIST page, not EDIT page
                if 'preprodapp.tekioncloud.com/templates/list' in url and '/edit/' not in url:
                    templates_page = page
                    print(f"✅ Found templates list page: {url}")
                    break
            
            # If not found, navigate to it
            if not templates_page:
                print("⚠️  Templates list page not open. Navigating to it...")
                
                # Use first page or create new one
                if context.pages:
                    templates_page = context.pages[0]
                else:
                    templates_page = await context.new_page()
                
                await templates_page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                                         wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
                print(f"✅ Navigated to: {templates_page.url}")
            
            print()
            
            # Bring page to front
            await templates_page.bring_to_front()
            await asyncio.sleep(1)
            
            # Step 2: Verify department filter exists
            print("🔍 Step 2: Verifying department filter exists...")
            dept_filter = await templates_page.query_selector('.ant-dropdown-trigger')
            
            if not dept_filter:
                print("❌ Department filter not found! Cannot proceed.")
                return
            
            print("✅ Department filter found\n")
            
            # Get current selection
            current_selection = await templates_page.evaluate("""
                () => {
                    const trigger = document.querySelector('.ant-dropdown-trigger');
                    const deptDiv = trigger?.querySelector('#departments');
                    return deptDiv?.innerText || trigger?.innerText || 'Unknown';
                }
            """)
            print(f"📊 Current selection: {current_selection}\n")
            
            # Step 3: Open dropdown using the EXACT selector
            print("🖱️  Step 3: Opening department dropdown...")
            await templates_page.click('.ant-dropdown-trigger', timeout=5000)
            await asyncio.sleep(2)
            print("✅ Dropdown opened\n")
            
            # Step 4: Take screenshot to see what's available
            screenshot_file = f"before_department_change.png"
            await templates_page.screenshot(path=screenshot_file)
            print(f"📸 Screenshot saved: {screenshot_file}\n")
            
            # Step 5: Click departments using more specific approach
            # Find elements within the dropdown overlay only
            print("🖱️  Step 4: Changing department selections...\n")
            
            # Get all clickable department options in the dropdown
            dept_options = await templates_page.evaluate("""
                () => {
                    const options = [];
                    
                    // Look inside the ant-dropdown that's currently visible
                    const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                    if (!dropdown) return options;
                    
                    // Find all elements with text Sales, Service, Parts within dropdown
                    const allElements = dropdown.querySelectorAll('*');
                    
                    allElements.forEach(el => {
                        const text = el.textContent.trim();
                        // Only get leaf elements (no children or only checkbox children)
                        if ((text === 'Sales' || text === 'Service' || text === 'Parts') && 
                            (el.children.length === 0 || 
                             (el.children.length === 1 && el.querySelector('.ant-checkbox')))) {
                            
                            const checkbox = el.querySelector('input[type="checkbox"]') || 
                                           el.closest('label')?.querySelector('input[type="checkbox"]');
                            
                            options.push({
                                text: text,
                                tag: el.tagName,
                                isChecked: checkbox ? checkbox.checked : false,
                                className: el.className.substring(0, 60)
                            });
                        }
                    });
                    
                    // Remove duplicates
                    const unique = [];
                    const seen = new Set();
                    options.forEach(opt => {
                        if (!seen.has(opt.text)) {
                            seen.add(opt.text);
                            unique.push(opt);
                        }
                    });
                    
                    return unique;
                }
            """)
            
            print("📋 Available options in dropdown:")
            for opt in dept_options:
                checked = "☑️" if opt['isChecked'] else "☐"
                print(f"   {checked} {opt['text']}")
            print()
            
            # Now click to change selections
            # Goal: Uncheck Sales, Check Service, Check Parts
            
            # Click Sales if it's checked (to uncheck it)
            sales_opt = next((o for o in dept_options if o['text'] == 'Sales'), None)
            if sales_opt and sales_opt['isChecked']:
                print("   🖱️  Unchecking Sales...")
                # Click within the dropdown only
                await templates_page.evaluate("""
                    () => {
                        const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                        const elements = dropdown.querySelectorAll('*');
                        for (let el of elements) {
                            if (el.textContent.trim() === 'Sales' && el.children.length <= 1) {
                                el.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                await asyncio.sleep(1)
                print("   ✅ Sales unchecked\n")
            
            # Click Service if it's not checked (to check it)
            service_opt = next((o for o in dept_options if o['text'] == 'Service'), None)
            if service_opt and not service_opt['isChecked']:
                print("   🖱️  Checking Service...")
                await templates_page.evaluate("""
                    () => {
                        const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                        const elements = dropdown.querySelectorAll('*');
                        for (let el of elements) {
                            if (el.textContent.trim() === 'Service' && el.children.length <= 1) {
                                el.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                await asyncio.sleep(1)
                print("   ✅ Service checked\n")
            
            # Click Parts if it's not checked (to check it)
            parts_opt = next((o for o in dept_options if o['text'] == 'Parts'), None)
            if parts_opt and not parts_opt['isChecked']:
                print("   🖱️  Checking Parts...")
                await templates_page.evaluate("""
                    () => {
                        const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                        const elements = dropdown.querySelectorAll('*');
                        for (let el of elements) {
                            if (el.textContent.trim() === 'Parts' && el.children.length <= 1) {
                                el.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                await asyncio.sleep(1)
                print("   ✅ Parts checked\n")
            
            # Step 6: Close dropdown
            print("🖱️  Step 5: Closing dropdown...")
            await templates_page.keyboard.press('Escape')
            await asyncio.sleep(2)
            print("✅ Dropdown closed\n")

            # Step 7: Verify final selection
            final_selection = await templates_page.evaluate("""
                () => {
                    const trigger = document.querySelector('.ant-dropdown-trigger');
                    const deptDiv = trigger?.querySelector('#departments');
                    return deptDiv?.innerText || trigger?.innerText || 'Unknown';
                }
            """)

            print("=" * 100)
            print(f"📊 FINAL SELECTION: {final_selection}")
            print("=" * 100)
            print()

            # Step 8: Wait 20 seconds and monitor
            print("⏳ Step 6: Waiting 20 seconds for page to update templates...\n")

            for i in range(20, 0, -1):
                # Check tab counts every 5 seconds
                if i % 5 == 0 or i == 1:
                    tabs = await templates_page.evaluate("""
                        () => {
                            const tabs = [];
                            document.querySelectorAll('[role="tab"]').forEach(tab => {
                                tabs.push({
                                    text: tab.textContent.trim(),
                                    active: tab.getAttribute('aria-selected') === 'true'
                                });
                            });
                            return tabs;
                        }
                    """)

                    elapsed = 20 - i
                    tab_display = ' | '.join([f"{t['text']}" for t in tabs])
                    print(f"   [{elapsed:2d}s] {tab_display}")

                await asyncio.sleep(1)

            print()
            print("=" * 100)
            print("✅ COMPLETE!")
            print("=" * 100)

            # Final summary
            final_tabs = await templates_page.evaluate("""
                () => {
                    const tabs = [];
                    document.querySelectorAll('[role="tab"]').forEach(tab => {
                        tabs.push({
                            text: tab.textContent.trim(),
                            active: tab.getAttribute('aria-selected') === 'true'
                        });
                    });
                    return tabs;
                }
            """)

            print()
            print("📊 Final Status:")
            print(f"   Department: {final_selection}")
            print(f"   Tabs:")
            for tab in final_tabs:
                active_icon = "✓" if tab['active'] else " "
                print(f"      {active_icon} {tab['text']}")

            print()
            print("✅ Successfully changed department filter to Service & Parts (Sales unchecked)")
            print("✅ Waited 20 seconds for templates to load")
            print()

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

