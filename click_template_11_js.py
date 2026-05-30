#!/usr/bin/env python3
"""
Click template #11 using JavaScript
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 80)
    print("🖱️  CLICK TEMPLATE #11")
    print("=" * 80)
    print()
    
    try:
        async with async_playwright() as playwright:
            print("🔌 Connecting to browser...")
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            print("✅ Connected\n")
            
            # Find templates page
            print("🔍 Finding templates page...")
            page = None
            for p in context.pages:
                url = p.url
                if '/templates/list' in url and '/edit/' not in url:
                    page = p
                    print(f"✅ Found: {url}\n")
                    break
            
            if not page:
                print("Using first page...")
                page = context.pages[0]
            
            await page.bring_to_front()
            
            # Click using JavaScript
            print("📋 Getting template #11 info and clicking...")
            
            result = await page.evaluate("""
                () => {
                    const grid = document.querySelector('[role="grid"]');
                    if (!grid) return { error: 'No grid found' };
                    
                    const rows = Array.from(grid.querySelectorAll('[role="row"]'));
                    const dataRows = rows.slice(1); // Skip header
                    
                    if (dataRows.length < 11) {
                        return { error: `Only ${dataRows.length} templates found` };
                    }
                    
                    const targetRow = dataRows[10]; // 0-based, so 10 = 11th
                    const nameCell = targetRow.querySelector('[role="gridcell"]:nth-child(2)');
                    
                    if (!nameCell) {
                        return { error: 'Name cell not found' };
                    }
                    
                    const templateName = nameCell.textContent.trim();
                    
                    // Click it
                    nameCell.click();
                    
                    return {
                        success: true,
                        index: 11,
                        name: templateName,
                        totalTemplates: dataRows.length
                    };
                }
            """)
            
            if result.get('error'):
                print(f"❌ Error: {result['error']}\n")
                return
            
            print(f"✅ Clicked template #{result['index']}")
            print(f"   Name: {result['name']}")
            print(f"   Total templates: {result['totalTemplates']}\n")
            
            # Wait for page to change
            print("⏳ Waiting for navigation...")
            await asyncio.sleep(3)
            
            new_url = page.url
            print(f"📍 Current URL: {new_url}\n")
            
            if '/edit/' in new_url:
                print("=" * 80)
                print("✅ SUCCESS - Template editor opened!")
                print("=" * 80)
            else:
                print("=" * 80)
                print("⚠️  Still on list page")
                print("=" * 80)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
