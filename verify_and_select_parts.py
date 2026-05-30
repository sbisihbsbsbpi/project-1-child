#!/usr/bin/env python3
"""
Verify current selection and ensure Parts is also selected
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("🔍 Verifying department selection and adding Parts...\n")
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            pages = context.pages
            
            page = None
            for p in pages:
                if 'templates/list' in p.url:
                    page = p
                    break
            
            if not page:
                page = pages[0]
            
            # Check current selection
            print("📊 Checking current department selection...")
            current = await page.evaluate("""
                () => {
                    const trigger = document.querySelector('.ant-dropdown-trigger');
                    if (!trigger) return 'Not found';
                    
                    const deptDiv = trigger.querySelector('#departments');
                    if (!deptDiv) return trigger.innerText;
                    
                    return deptDiv.innerText;
                }
            """)
            print(f"   Current: {current}\n")
            
            # Open dropdown again
            print("🖱️  Opening dropdown to select Parts...")
            await page.click('.ant-dropdown-trigger')
            await asyncio.sleep(2)
            
            # Take screenshot
            screenshot_file = f"after_selection_{asyncio.get_event_loop().time():.0f}.png"
            await page.screenshot(path=screenshot_file)
            print(f"   📸 Screenshot: {screenshot_file}\n")
            
            # Get all visible options
            options = await page.evaluate("""
                () => {
                    const visible = [];
                    document.querySelectorAll('*').forEach(el => {
                        if (el.offsetParent && el.children.length === 0) {
                            const text = el.textContent.trim();
                            if (text === 'Sales' || text === 'Service' || text === 'Parts') {
                                visible.push({
                                    text: text,
                                    tag: el.tagName,
                                    clickable: true
                                });
                            }
                        }
                    });
                    return visible;
                }
            """)
            
            print("📋 Visible department options:")
            for opt in options:
                print(f"   - {opt['text']}")
            print()
            
            # Try to click Parts
            print("🖱️  Attempting to click Parts...")
            try:
                # Try multiple strategies
                parts_clicked = False
                
                # Strategy 1: Direct text selector
                try:
                    await page.click('text="Parts"', timeout=2000)
                    parts_clicked = True
                    print("   ✅ Parts clicked (text selector)")
                except:
                    pass
                
                # Strategy 2: Look for label containing "Parts"
                if not parts_clicked:
                    try:
                        await page.click('label:has-text("Parts")', timeout=2000)
                        parts_clicked = True
                        print("   ✅ Parts clicked (label selector)")
                    except:
                        pass
                
                # Strategy 3: Use JavaScript to find and click
                if not parts_clicked:
                    clicked = await page.evaluate("""
                        () => {
                            const elements = document.querySelectorAll('*');
                            for (let el of elements) {
                                if (el.children.length === 0 && el.textContent.trim() === 'Parts') {
                                    el.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    if clicked:
                        parts_clicked = True
                        print("   ✅ Parts clicked (JavaScript)")
                
                if not parts_clicked:
                    print("   ⚠️  Could not click Parts")
                    
            except Exception as e:
                print(f"   ⚠️  Error clicking Parts: {e}")
            
            await asyncio.sleep(1)
            
            # Close dropdown
            print("\n🖱️  Closing dropdown...")
            await page.keyboard.press('Escape')
            await asyncio.sleep(2)
            
            # Verify final selection
            print("\n✅ Final verification...")
            final = await page.evaluate("""
                () => {
                    const trigger = document.querySelector('.ant-dropdown-trigger');
                    if (!trigger) return 'Not found';
                    
                    const deptDiv = trigger.querySelector('#departments');
                    if (!deptDiv) return trigger.innerText;
                    
                    return deptDiv.innerText;
                }
            """)
            
            print(f"   Final selection: {final}")
            
            # Check tab counts
            print("\n📑 Checking tab counts after filter change...")
            tabs = await page.evaluate("""
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
            
            for tab in tabs:
                active = "✓" if tab['active'] else " "
                print(f"   {active} {tab['text']}")
            
            print("\n✅ Done!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
