#!/usr/bin/env python3
"""
Detect Clear Button on Templates Page
Looking for clear/reset buttons related to filters
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("🔍 Detecting Clear Button on Templates Page\n")
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            
            # Find templates page
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
            
            # Look for clear buttons
            print("🔍 Searching for clear/reset buttons...\n")
            
            clear_buttons = await page.evaluate("""
                () => {
                    const buttons = [];
                    
                    // Strategy 1: Look for buttons with text containing "clear", "reset", "remove"
                    document.querySelectorAll('button').forEach((btn, i) => {
                        const text = btn.textContent.trim().toLowerCase();
                        if (text.includes('clear') || text.includes('reset') || 
                            text.includes('remove') || text === 'x' || text === '×') {
                            buttons.push({
                                index: i,
                                text: btn.textContent.trim(),
                                className: btn.className.substring(0, 80),
                                visible: btn.offsetParent !== null,
                                disabled: btn.disabled,
                                ariaLabel: btn.getAttribute('aria-label'),
                                dataTest: btn.getAttribute('data-test'),
                                html: btn.outerHTML.substring(0, 300)
                            });
                        }
                    });
                    
                    // Strategy 2: Look for clear icons
                    document.querySelectorAll('[class*="clear"], [class*="close"], [class*="remove"]').forEach(el => {
                        if (el.offsetParent !== null && 
                            (el.tagName === 'BUTTON' || el.tagName === 'SPAN' || el.tagName === 'DIV')) {
                            const clickable = el.onclick || el.style.cursor === 'pointer';
                            if (clickable || el.tagName === 'BUTTON') {
                                buttons.push({
                                    tag: el.tagName,
                                    text: el.textContent.trim().substring(0, 50),
                                    className: el.className.substring(0, 80),
                                    visible: true,
                                    clickable: clickable,
                                    html: el.outerHTML.substring(0, 300)
                                });
                            }
                        }
                    });
                    
                    // Strategy 3: Look for clear in department filter specifically
                    const deptFilter = document.querySelector('.ant-dropdown-trigger');
                    if (deptFilter) {
                        const clearInFilter = deptFilter.querySelectorAll('[class*="clear"], [class*="close"]');
                        clearInFilter.forEach(el => {
                            buttons.push({
                                location: 'department_filter',
                                tag: el.tagName,
                                text: el.textContent.trim().substring(0, 50),
                                className: el.className.substring(0, 80),
                                visible: el.offsetParent !== null,
                                html: el.outerHTML.substring(0, 300)
                            });
                        });
                    }
                    
                    return buttons;
                }
            """)
            
            print(f"📋 Found {len(clear_buttons)} potential clear buttons:\n")
            
            for i, btn in enumerate(clear_buttons, 1):
                print(f"{i}. {btn.get('tag', 'BUTTON')}")
                if btn.get('text'):
                    print(f"   Text: {btn['text']}")
                if btn.get('className'):
                    print(f"   Class: {btn['className']}")
                if btn.get('location'):
                    print(f"   Location: {btn['location']}")
                if btn.get('ariaLabel'):
                    print(f"   Aria-Label: {btn['ariaLabel']}")
                if btn.get('dataTest'):
                    print(f"   Data-Test: {btn['dataTest']}")
                print(f"   Visible: {btn.get('visible', 'Unknown')}")
                print()
            
            # Now open department filter to see if clear button appears
            print("🖱️  Opening department filter to check for clear button...\n")
            await page.click('.ant-dropdown-trigger')
            await asyncio.sleep(2)
            
            # Check again for clear button in dropdown
            clear_in_dropdown = await page.evaluate("""
                () => {
                    const buttons = [];
                    const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                    
                    if (dropdown) {
                        // Look for clear/close/reset buttons in dropdown
                        dropdown.querySelectorAll('button, span, div').forEach(el => {
                            const text = el.textContent.trim().toLowerCase();
                            const classes = el.className.toLowerCase();
                            
                            if (text.includes('clear') || text.includes('reset') || 
                                classes.includes('clear') || classes.includes('close') ||
                                text === 'x' || text === '×') {
                                
                                buttons.push({
                                    tag: el.tagName,
                                    text: el.textContent.trim(),
                                    className: el.className.substring(0, 80),
                                    clickable: el.onclick || el.tagName === 'BUTTON' || el.style.cursor === 'pointer',
                                    html: el.outerHTML.substring(0, 400)
                                });
                            }
                        });
                    }
                    
                    return buttons;
                }
            """)
            
            print(f"📋 Clear buttons in dropdown: {len(clear_in_dropdown)}\n")
            
            for i, btn in enumerate(clear_in_dropdown, 1):
                print(f"{i}. {btn['tag']}")
                print(f"   Text: {btn['text']}")
                print(f"   Class: {btn['className']}")
                print(f"   Clickable: {btn['clickable']}")
                print()
            
            # Take screenshot
            screenshot_file = f"clear_button_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_file)
            print(f"📸 Screenshot: {screenshot_file}\n")
            
            # Close dropdown
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)
            
            # Save results
            results = {
                'timestamp': datetime.now().isoformat(),
                'page_url': page.url,
                'clear_buttons_found': len(clear_buttons),
                'clear_buttons_in_dropdown': len(clear_in_dropdown),
                'buttons': clear_buttons,
                'dropdown_buttons': clear_in_dropdown
            }
            
            filename = f"clear_button_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"💾 Results saved to: {filename}")
            
            print("\n" + "=" * 80)
            print("✅ DETECTION COMPLETE")
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
