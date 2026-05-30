#!/usr/bin/env python3
"""
Click Template by Index
Click on a specific template row by index (1-based)
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def click_template(template_index=11):
    """
    Click on a template by its index (1-based, excluding header row)
    
    Args:
        template_index (int): Template row number (1 = first template, 11 = 11th template)
    """
    
    print("=" * 100)
    print(f"🖱️  CLICK TEMPLATE #{template_index}")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            
            # Find templates page
            print("🔍 Step 1: Finding templates list page...")
            page = None
            
            for p in context.pages:
                if '/templates/list' in p.url and '/edit/' not in p.url:
                    page = p
                    print(f"   ✅ Found: {p.url}")
                    break
            
            if not page:
                print("   ⚠️  Not found. Navigating...")
                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                              wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
                print(f"   ✅ Navigated to: {page.url}")
            
            await page.bring_to_front()
            print()
            
            # Get all template rows
            print("📋 Step 2: Getting all template rows...")
            
            template_rows = await page.evaluate("""
                () => {
                    const grid = document.querySelector('[role="grid"]');
                    if (!grid) return null;
                    
                    const allRows = Array.from(grid.querySelectorAll('[role="row"]'));
                    
                    // First row is usually the header
                    const dataRows = allRows.slice(1); // Skip header
                    
                    return dataRows.map((row, index) => {
                        const nameCell = row.querySelector('[role="gridcell"]:nth-child(2)');
                        const cells = Array.from(row.querySelectorAll('[role="gridcell"]'));
                        
                        return {
                            index: index + 1, // 1-based
                            name: nameCell ? nameCell.textContent.trim() : 'Unknown',
                            cellCount: cells.length,
                            hasCheckbox: row.querySelector('input[type="checkbox"]') !== null
                        };
                    });
                }
            """)
            
            if not template_rows:
                print("   ❌ No template rows found")
                return
            
            print(f"   ✅ Found {len(template_rows)} template rows\n")
            
            # Show all templates
            print("📋 All Templates:")
            for row in template_rows[:15]:  # Show first 15
                print(f"   {row['index']:2d}. {row['name'][:80]}")
            if len(template_rows) > 15:
                print(f"   ... and {len(template_rows) - 15} more")
            print()
            
            # Check if requested index exists
            if template_index < 1 or template_index > len(template_rows):
                print(f"❌ Template index {template_index} out of range (1-{len(template_rows)})")
                return
            
            target_template = template_rows[template_index - 1]
            
            print(f"🎯 Step 3: Clicking template #{template_index}...")
            print(f"   Name: {target_template['name']}")
            print()
            
            # Click the template name in the specific row
            # Row index in selector is 0-based, but we add 1 to skip header, so it's template_index + 1
            row_selector = f"[role='grid'] [role='row']:nth-child({template_index + 1})"
            name_cell_selector = f"{row_selector} [role='gridcell']:nth-child(2)"
            
            # Take screenshot before clicking
            await page.screenshot(path='before_click_template.png')
            print("📸 Screenshot saved: before_click_template.png")
            
            # Click the template name
            await page.click(name_cell_selector)
            print(f"   ✅ Clicked on template name")
            print()
            
            # Wait for navigation
            print("⏳ Step 4: Waiting for template editor to load...")
            await asyncio.sleep(3)
            
            # Get new URL
            new_url = page.url
            print(f"   New URL: {new_url}")
            
            if '/edit/' in new_url:
                print("   ✅ Template editor opened!")
            else:
                print("   ⚠️  URL didn't change to editor")
            
            # Take screenshot after
            await page.screenshot(path='after_click_template.png')
            print("   📸 Screenshot saved: after_click_template.png")
            print()
            
            print("=" * 100)
            print("✅ TEMPLATE CLICKED SUCCESSFULLY")
            print("=" * 100)
            print(f"Template: {target_template['name']}")
            print(f"Index: {template_index}")
            print(f"Current URL: {new_url}")
            print("=" * 100)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    await click_template(template_index=11)


if __name__ == "__main__":
    asyncio.run(main())
