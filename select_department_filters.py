#!/usr/bin/env python3
"""
Department Filter Selector
Uses existing CDP connection to select Service & Parts departments
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright
from cdp_utils import get_or_navigate_to_page, print_cdp_info


async def select_departments(page, departments=['SERVICE', 'PARTS']):
    """
    Select specific departments from the dropdown
    
    Args:
        page: Playwright page object
        departments: List of department names to select
    """
    
    print(f"🎯 Target Departments: {', '.join(departments)}")
    print()
    
    # Step 1: Click the department filter dropdown
    print("1️⃣  Clicking department filter dropdown...")
    
    try:
        # Click the Ant Design dropdown trigger
        await page.click('.ant-dropdown-trigger', timeout=5000)
        await asyncio.sleep(1)
        print("   ✅ Dropdown opened")
    except Exception as e:
        print(f"   ❌ Failed to open dropdown: {e}")
        return False
    
    # Step 2: Wait for dropdown menu to appear
    print("\n2️⃣  Waiting for dropdown menu...")
    
    try:
        # Ant Design dropdowns create a separate overlay
        await page.wait_for_selector('.ant-dropdown-menu', timeout=5000)
        await asyncio.sleep(0.5)
        print("   ✅ Menu appeared")
    except Exception as e:
        print(f"   ❌ Menu not found: {e}")
        return False
    
    # Step 3: Get all available department options
    print("\n3️⃣  Scanning available departments...")
    
    available_options = await page.evaluate("""
        () => {
            const menu = document.querySelector('.ant-dropdown-menu');
            if (!menu) return [];
            
            const items = menu.querySelectorAll('.ant-dropdown-menu-item');
            const options = [];
            
            items.forEach(item => {
                const text = item.textContent.trim();
                options.push({
                    text: text,
                    className: item.className
                });
            });
            
            return options;
        }
    """)
    
    print(f"   Found {len(available_options)} options:")
    for opt in available_options:
        print(f"     • {opt['text']}")
    
    # Step 4: Click on each target department
    print(f"\n4️⃣  Selecting departments...")
    
    for dept in departments:
        print(f"\n   📍 Selecting: {dept}")
        
        # Find and click the department option
        clicked = await page.evaluate(f"""
            () => {{
                const menu = document.querySelector('.ant-dropdown-menu');
                if (!menu) return false;
                
                const items = menu.querySelectorAll('.ant-dropdown-menu-item');
                
                for (let item of items) {{
                    const text = item.textContent.trim().toUpperCase();
                    if (text === '{dept}' || text.includes('{dept}')) {{
                        item.click();
                        console.log('Clicked:', text);
                        return true;
                    }}
                }}
                
                return false;
            }}
        """)
        
        if clicked:
            print(f"      ✅ Clicked {dept}")
            await asyncio.sleep(1)
            
            # Check if dropdown closed (single-select) or stayed open (multi-select)
            dropdown_visible = await page.evaluate("""
                () => {
                    const menu = document.querySelector('.ant-dropdown-menu');
                    return menu && menu.offsetParent !== null;
                }
            """)
            
            if not dropdown_visible:
                print(f"      ⚠️  Dropdown closed - opening again for next selection")
                # Re-open dropdown for next selection
                await page.click('.ant-dropdown-trigger', timeout=5000)
                await asyncio.sleep(1)
        else:
            print(f"      ❌ Failed to find {dept}")
    
    # Step 5: Close dropdown if still open
    print("\n5️⃣  Finalizing selection...")
    
    dropdown_still_open = await page.evaluate("""
        () => {
            const menu = document.querySelector('.ant-dropdown-menu');
            return menu && menu.offsetParent !== null;
        }
    """)
    
    if dropdown_still_open:
        # Click outside to close dropdown
        await page.evaluate("""
            () => {
                const menu = document.querySelector('.ant-dropdown-menu');
                if (menu) {
                    // Click on body or press Escape
                    document.body.click();
                }
            }
        """)
        await asyncio.sleep(0.5)
        print("   ✅ Dropdown closed")
    
    # Step 6: Verify current selection
    print("\n6️⃣  Verifying selection...")
    
    current_selection = await page.evaluate("""
        () => {
            const trigger = document.querySelector('.ant-dropdown-trigger');
            if (!trigger) return 'Unknown';
            
            // Clean up the text (remove CSS injection)
            const text = trigger.textContent.trim();
            return text.split('{')[0].split('}').pop().trim() || text;
        }
    """)
    
    print(f"   Current selection: {current_selection}")
    
    return True


async def main():
    print("=" * 80)
    print("🎯 DEPARTMENT FILTER SELECTOR")
    print("=" * 80)
    print()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser via CDP")
            print_cdp_info(browser)
            print()
            
            # Use existing tab
            page = await get_or_navigate_to_page(
                browser,
                "https://preprodapp.tekioncloud.com/templates/list",
                wait_for_load=True
            )
            
            print()
            print("=" * 80)
            print("🔄 STARTING DEPARTMENT SELECTION")
            print("=" * 80)
            print()
            
            # Select SERVICE and PARTS
            success = await select_departments(page, departments=['SERVICE', 'PARTS'])
            
            print()
            print("=" * 80)
            if success:
                print("✅ DEPARTMENT SELECTION COMPLETE")
            else:
                print("⚠️  DEPARTMENT SELECTION INCOMPLETE")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
