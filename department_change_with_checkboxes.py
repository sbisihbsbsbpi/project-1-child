#!/usr/bin/env python3
"""
Department Change Using Checkbox Strategy
Directly interact with checkboxes in the dropdown
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

async def main():
    print("🎯 Department Change: Using Checkbox Strategy\n")
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        # Find page
        page = None
        for p in context.pages:
            if '/templates/list' in p.url and '/edit/' not in p.url:
                page = p
                break
        
        if not page:
            page = context.pages[0]
            await page.goto("https://preprodapp.tekioncloud.com/templates/list")
            await asyncio.sleep(3)
        
        await page.bring_to_front()
        print(f"✅ Page: {page.url}\n")
        
        # Click department filter
        print("🖱️  Clicking department filter...")
        await page.click('.ant-dropdown-trigger')
        await asyncio.sleep(2)
        
        # Get HTML of dropdown
        print("📋 Getting dropdown HTML...\n")
        dropdown_html = await page.evaluate("""
            () => {
                const dropdown = document.querySelector('.ant-dropdown');
                return dropdown ? dropdown.outerHTML.substring(0, 5000) : 'Not found';
            }
        """)
        
        # Save to file for inspection
        with open('dropdown_html.txt', 'w') as f:
            f.write(dropdown_html)
        print("💾 Saved dropdown HTML to: dropdown_html.txt\n")
        
        # Try different selectors for the options
        print("🔍 Trying different strategies...\n")
        
        # Strategy 1: Click by nth checkbox
        print("Strategy 1: Using checkbox data-test attributes...")
        result = await page.evaluate("""
            () => {
                const checkboxes = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]');
                return Array.from(checkboxes).map((cb, i) => ({
                    index: i,
                    checked: cb.checked,
                    dataTest: cb.getAttribute('data-test'),
                    parentText: cb.closest('label')?.textContent?.trim() || 'No label'
                }));
            }
        """)
        
        print(f"   Found {len(result)} checkboxes:")
        for cb in result:
            checked = "☑" if cb['checked'] else "☐"
            print(f"   {checked} [{cb['index']}] {cb['parentText'][:50]}")
        print()
        
        # If we found checkboxes, interact with them
        if len(result) >= 3:
            print("🖱️  Clicking checkboxes directly...\n")
            
            # Assuming: 0=Sales, 1=Service, 2=Parts (verify from output above)
            # Uncheck Sales (index 0) if checked
            if result[0]['checked']:
                print("   Unchecking checkbox 0 (Sales)...")
                await page.evaluate("""
                    () => {
                        const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[0];
                        if (cb) cb.click();
                    }
                """)
                await asyncio.sleep(0.5)
            
            # Check Service (index 1) if not checked  
            if len(result) > 1 and not result[1]['checked']:
                print("   Checking checkbox 1 (Service)...")
                await page.evaluate("""
                    () => {
                        const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[1];
                        if (cb) cb.click();
                    }
                """)
                await asyncio.sleep(0.5)
            
            # Check Parts (index 2) if not checked
            if len(result) > 2 and not result[2]['checked']:
                print("   Checking checkbox 2 (Parts)...")
                await page.evaluate("""
                    () => {
                        const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[2];
                        if (cb) cb.click();
                    }
                """)
                await asyncio.sleep(0.5)
        
        # Close
        print("\n🖱️  Closing dropdown...")
        await page.keyboard.press('Escape')
        await asyncio.sleep(2)
        
        # Verify
        selection = await page.evaluate("""
            () => {
                const trigger = document.querySelector('.ant-dropdown-trigger');
                return trigger?.innerText || 'Not found';
            }
        """)
        
        print(f"\n✅ Selection: {selection}\n")
        
        # Wait 20 seconds
        print("⏳ Waiting 20 seconds...")
        await asyncio.sleep(20)
        
        print("\n✅ Complete!")

asyncio.run(main())
