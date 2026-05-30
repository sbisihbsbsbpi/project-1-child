#!/usr/bin/env python3
"""
Change Department Selection
Uncheck Sales, Select Service & Parts, then wait 20 seconds
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🔄 CHANGING DEPARTMENT FILTER SELECTION")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            pages = context.pages
            
            # Find templates page
            page = None
            for p in pages:
                if 'templates/list' in p.url:
                    page = p
                    break
            
            if not page:
                page = pages[0]
            
            print(f"✅ Using existing page: {page.url}\n")
            
            # Step 1: Click to open department dropdown
            print("🖱️  Step 1: Opening department dropdown...")
            await page.click('.ant-dropdown-trigger')
            await asyncio.sleep(1.5)
            print("   ✅ Dropdown opened\n")
            
            # Step 2: Get current state
            current_state = await page.evaluate("""
                () => {
                    const checkboxes = document.querySelectorAll('.ant-dropdown input[type="checkbox"]');
                    const state = [];
                    checkboxes.forEach((cb, i) => {
                        const label = cb.closest('label');
                        const text = label ? label.textContent.trim() : '';
                        state.push({
                            index: i,
                            text: text,
                            checked: cb.checked
                        });
                    });
                    return state;
                }
            """)
            
            print("📊 Current checkbox state:")
            for item in current_state[:5]:
                checked = "☑️" if item['checked'] else "☐"
                print(f"   {checked} Checkbox {item['index']}: {item['text'][:40]}")
            print()
            
            # Step 3: Find and click checkboxes for Sales, Service, Parts
            print("🔍 Step 2: Finding Sales, Service, Parts checkboxes...")
            
            department_checkboxes = await page.evaluate("""
                () => {
                    const departments = {
                        sales: null,
                        service: null,
                        parts: null
                    };
                    
                    // Look for checkboxes in the dropdown
                    const allLabels = document.querySelectorAll('.ant-dropdown label');
                    
                    allLabels.forEach(label => {
                        const text = label.textContent.trim().toLowerCase();
                        const checkbox = label.querySelector('input[type="checkbox"]');
                        
                        if (checkbox) {
                            if (text === 'sales' || text.includes('sales')) {
                                departments.sales = {
                                    text: label.textContent.trim(),
                                    checked: checkbox.checked,
                                    id: checkbox.id,
                                    dataTest: checkbox.getAttribute('data-test')
                                };
                            } else if (text === 'service' || text.includes('service')) {
                                departments.service = {
                                    text: label.textContent.trim(),
                                    checked: checkbox.checked,
                                    id: checkbox.id,
                                    dataTest: checkbox.getAttribute('data-test')
                                };
                            } else if (text === 'parts' || text.includes('parts')) {
                                departments.parts = {
                                    text: label.textContent.trim(),
                                    checked: checkbox.checked,
                                    id: checkbox.id,
                                    dataTest: checkbox.getAttribute('data-test')
                                };
                            }
                        }
                    });
                    
                    return departments;
                }
            """)
            
            print(f"   Sales: {department_checkboxes['sales']}")
            print(f"   Service: {department_checkboxes['service']}")
            print(f"   Parts: {department_checkboxes['parts']}\n")
            
            # Step 4: Use the react-select component approach
            print("🎯 Step 3: Clicking department options...")
            
            # Try clicking by visible text
            try:
                # Look for "Sales" option and click to uncheck
                sales_option = await page.query_selector('text=Sales')
                if sales_option:
                    print("   🖱️  Clicking Sales to uncheck...")
                    await sales_option.click()
                    await asyncio.sleep(0.5)
                    print("   ✅ Sales unchecked")
            except:
                print("   ⚠️  Could not find Sales option")
            
            try:
                # Click "Service" option
                service_option = await page.query_selector('text=Service')
                if service_option:
                    print("   🖱️  Clicking Service to select...")
                    await service_option.click()
                    await asyncio.sleep(0.5)
                    print("   ✅ Service selected")
            except:
                print("   ⚠️  Could not find Service option")
            
            try:
                # Click "Parts" option
                parts_option = await page.query_selector('text=Parts')
                if parts_option:
                    print("   🖱️  Clicking Parts to select...")
                    await parts_option.click()
                    await asyncio.sleep(0.5)
                    print("   ✅ Parts selected")
            except:
                print("   ⚠️  Could not find Parts option")
            
            print()
            
            # Step 5: Close dropdown by clicking elsewhere or pressing Escape
            print("🖱️  Step 4: Closing dropdown...")
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)
            print("   ✅ Dropdown closed\n")
            
            # Step 6: Verify the selection
            print("📊 Step 5: Verifying new selection...")
            new_selection = await page.evaluate("""
                () => {
                    const trigger = document.querySelector('.ant-dropdown-trigger');
                    return trigger ? trigger.innerText : 'Could not read';
                }
            """)
            print(f"   Current selection: {new_selection}\n")
            
            # Step 7: Wait 20 seconds
            print("⏳ Step 6: Waiting 20 seconds for page to update...")
            for i in range(20, 0, -1):
                print(f"   {i} seconds remaining...", end='\r')
                await asyncio.sleep(1)
            
            print("\n")
            print("=" * 100)
            print("✅ COMPLETE!")
            print("=" * 100)
            print()
            print(f"Final selection: {new_selection}")
            print("Waited 20 seconds for page updates to complete.")
            print()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
