#!/usr/bin/env python3
"""
Final Robust Department Change
Waits for dropdown options to load, then changes selection
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🎯 ROBUST DEPARTMENT CHANGE: Uncheck Sales, Check Service & Parts")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            
            # Find templates list page
            templates_page = None
            for page in context.pages:
                if '/templates/list' in page.url and '/edit/' not in page.url:
                    templates_page = page
                    break
            
            if not templates_page:
                templates_page = context.pages[0] if context.pages else await context.new_page()
                await templates_page.goto("https://preprodapp.tekioncloud.com/templates/list")
                await asyncio.sleep(3)
            
            await templates_page.bring_to_front()
            print(f"✅ Using page: {templates_page.url}\n")
            
            # Open dropdown
            print("🖱️  Opening department dropdown...")
            await templates_page.click('.ant-dropdown-trigger')
            
            # Wait for dropdown content to load (wait for react-select or options)
            print("⏳ Waiting for dropdown options to load...")
            await asyncio.sleep(3)
            
            # Take screenshot
            await templates_page.screenshot(path="dropdown_opened.png")
            print("📸 Screenshot: dropdown_opened.png\n")
            
            # Look for options by searching all text
            print("🔍 Searching for department options...\n")
            
            all_text = await templates_page.evaluate("""
                () => {
                    const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                    if (!dropdown) return [];
                    
                    const texts = [];
                    const allEls = dropdown.querySelectorAll('*');
                    
                    allEls.forEach(el => {
                        const text = el.textContent?.trim();
                        if (text && text.length < 50 && el.offsetParent) {
                            texts.push({
                                text: text,
                                tag: el.tagName,
                                clickable: el.onclick || el.style.cursor === 'pointer' || el.tagName === 'LABEL'
                            });
                        }
                    });
                    
                    return texts;
                }
            """)
            
            # Filter for Sales, Service, Parts
            dept_texts = [t for t in all_text if t['text'] in ['Sales', 'Service', 'Parts']]
            print(f"Found {len(dept_texts)} department text elements:")
            for t in dept_texts[:10]:
                print(f"   - {t['text']} ({t['tag']})")
            print()
            
            # Now click them using JavaScript within dropdown
            print("🖱️  Changing selections...\n")
            
            # Click Sales to uncheck
            print("   Clicking Sales (to uncheck)...")
            clicked = await templates_page.evaluate("""
                () => {
                    const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                    if (!dropdown) return false;
                    
                    const allEls = dropdown.querySelectorAll('*');
                    for (let el of allEls) {
                        if (el.textContent.trim() === 'Sales' && 
                            (el.tagName === 'LABEL' || el.children.length <= 1)) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            print(f"   {'✅' if clicked else '❌'} Sales\n")
            await asyncio.sleep(1)
            
            # Click Service to check
            print("   Clicking Service (to check)...")
            clicked = await templates_page.evaluate("""
                () => {
                    const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                    if (!dropdown) return false;
                    
                    const allEls = dropdown.querySelectorAll('*');
                    for (let el of allEls) {
                        if (el.textContent.trim() === 'Service' && 
                            (el.tagName === 'LABEL' || el.children.length <= 1)) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            print(f"   {'✅' if clicked else '❌'} Service\n")
            await asyncio.sleep(1)
            
            # Click Parts to check
            print("   Clicking Parts (to check)...")
            clicked = await templates_page.evaluate("""
                () => {
                    const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                    if (!dropdown) return false;
                    
                    const allEls = dropdown.querySelectorAll('*');
                    for (let el of allEls) {
                        if (el.textContent.trim() === 'Parts' && 
                            (el.tagName === 'LABEL' || el.children.length <= 1)) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            print(f"   {'✅' if clicked else '❌'} Parts\n")
            await asyncio.sleep(1)
            
            # Close dropdown
            print("🖱️  Closing dropdown...")
            await templates_page.keyboard.press('Escape')
            await asyncio.sleep(2)
            print("✅ Closed\n")
            
            # Verify
            selection = await templates_page.evaluate("""
                () => {
                    const trigger = document.querySelector('.ant-dropdown-trigger');
                    return trigger?.innerText || 'Not found';
                }
            """)
            
            print("=" * 100)
            print(f"📊 CURRENT SELECTION: {selection}")
            print("=" * 100)
            print()
            
            # Wait 20 seconds
            print("⏳ Waiting 20 seconds...\n")
            for i in range(20, 0, -1):
                if i % 5 == 0:
                    tabs = await templates_page.evaluate("""
                        () => document.querySelectorAll('[role="tab"]').length
                    """)
                    print(f"   [{20-i:2d}s] Page active, {tabs} tabs visible")
                await asyncio.sleep(1)
            
            print("\n" + "=" * 100)
            print("✅ COMPLETE!")
            print("=" * 100)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
