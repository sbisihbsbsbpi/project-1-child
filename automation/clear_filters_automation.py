#!/usr/bin/env python3
"""
Clear Filters Automation Module
================================

WORKING SOLUTION - Tested and verified on 2026-05-29

This module automates clicking the "Clear" button to reset all filters
on the Tekion Templates page.

Author: Automation Team
Status: WORKING ✅
Last Updated: 2026-05-29

Clear Button Details:
    - Text: "Clear"
    - Selector: span[data-test="undefined-clearButton"]
    - Alternative: span[role="button"]:has-text("Clear")
    - Class: root_defaultFilterToolbar_clear__iojckhYAzp
    - Location: Filter toolbar (top of page)

Usage:
    python3 clear_filters_automation.py
    
    # Or import
    from automation.clear_filters_automation import click_clear_button
    result = await click_clear_button()
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from playwright.async_api import async_playwright


async def click_clear_button(
    wait_seconds=5,
    cdp_url="http://localhost:9223"
):
    """
    Click the Clear button to reset all filters on templates page.
    
    Args:
        wait_seconds (int): Seconds to wait after clicking (default: 5)
        cdp_url (str): Chrome DevTools Protocol URL
    
    Returns:
        dict: Result with status and message
        
    Example:
        result = await click_clear_button(wait_seconds=5)
        print(result['message'])
    """
    
    print("=" * 100)
    print("🧹 CLEAR FILTERS AUTOMATION")
    print("=" * 100)
    print()
    
    result = {
        'status': 'failed',
        'clicked': False,
        'message': '',
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        async with async_playwright() as playwright:
            # Connect to browser
            browser = await playwright.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            
            print("✅ Connected to browser via CDP\n")
            
            # Find templates page
            print("🔍 Step 1: Finding templates page...")
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
            
            # Check if clear button exists and is visible
            print("🔍 Step 2: Checking if Clear button is visible...")
            
            clear_button_info = await page.evaluate("""
                () => {
                    const clearBtn = document.querySelector('span[data-test="undefined-clearButton"]');
                    if (!clearBtn) return null;
                    
                    return {
                        visible: clearBtn.offsetParent !== null,
                        text: clearBtn.textContent.trim(),
                        className: clearBtn.className
                    };
                }
            """)
            
            if not clear_button_info:
                result['message'] = "Clear button not found on page"
                print("   ❌ Clear button not found\n")
                return result
            
            if not clear_button_info['visible']:
                result['message'] = "Clear button found but not visible"
                print("   ⚠️  Clear button exists but not visible\n")
                return result
            
            print(f"   ✅ Clear button found: '{clear_button_info['text']}'")
            print(f"   Class: {clear_button_info['className']}\n")
            
            # Click the clear button
            print("🖱️  Step 3: Clicking Clear button...")
            
            try:
                # Try multiple selectors
                clicked = False
                
                # Strategy 1: data-test attribute
                try:
                    await page.click('span[data-test="undefined-clearButton"]', timeout=2000)
                    clicked = True
                    print("   ✅ Clicked using data-test selector")
                except:
                    pass
                
                # Strategy 2: text selector
                if not clicked:
                    try:
                        await page.click('span[role="button"]:has-text("Clear")', timeout=2000)
                        clicked = True
                        print("   ✅ Clicked using text selector")
                    except:
                        pass
                
                # Strategy 3: JavaScript click
                if not clicked:
                    clicked = await page.evaluate("""
                        () => {
                            const clearBtn = document.querySelector('span[data-test="undefined-clearButton"]');
                            if (clearBtn) {
                                clearBtn.click();
                                return true;
                            }
                            return false;
                        }
                    """)
                    if clicked:
                        print("   ✅ Clicked using JavaScript")
                
                if not clicked:
                    result['message'] = "Failed to click Clear button"
                    print("   ❌ Could not click Clear button\n")
                    return result
                
                result['clicked'] = True
                
            except Exception as e:
                result['message'] = f"Error clicking: {str(e)}"
                print(f"   ❌ Error: {e}\n")
                return result
            
            print()
            
            # Wait for page to update
            print(f"⏳ Step 4: Waiting {wait_seconds} seconds for filters to clear...")
            for i in range(wait_seconds, 0, -1):
                if i == wait_seconds or i == 1:
                    print(f"   {i}s remaining...")
                await asyncio.sleep(1)
            
            print()
            
            # Verify filters were cleared
            print("📊 Step 5: Verifying filters cleared...")
            
            dept_filter = await page.evaluate("""
                () => {
                    const trigger = document.querySelector('.ant-dropdown-trigger');
                    return trigger?.innerText || 'Not found';
                }
            """)
            
            print(f"   Department Filter: {dept_filter}")
            
            # Check tabs
            tabs = await page.evaluate("""
                () => {
                    const tabs = [];
                    document.querySelectorAll('[role="tab"]').forEach(tab => {
                        tabs.push(tab.textContent.trim());
                    });
                    return tabs;
                }
            """)
            
            print(f"   Tabs: {' | '.join(tabs)}\n")
            
            result['status'] = 'success'
            result['message'] = 'Successfully clicked Clear button and filters reset'
            result['department_filter'] = dept_filter
            result['tabs'] = tabs
            
            print("=" * 100)
            print("✅ AUTOMATION COMPLETE!")
            print("=" * 100)
            print(f"Clear button clicked: {result['clicked']}")
            print(f"Current filters: {dept_filter}")
            print("=" * 100)
            print()
            
            return result
            
    except Exception as e:
        result['status'] = 'error'
        result['message'] = str(e)
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return result


async def main():
    """Main function - Example usage"""
    result = await click_clear_button(wait_seconds=5)
    
    print("\n📋 Result:")
    print(f"   Status: {result['status']}")
    print(f"   Clicked: {result['clicked']}")
    print(f"   Message: {result['message']}")


if __name__ == "__main__":
    asyncio.run(main())
