#!/usr/bin/env python3
"""
Final Department Change: Uncheck Sales, Check Service & Parts
Then wait 20 seconds
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🎯 FINAL DEPARTMENT CHANGE: Service & Parts ONLY")
    print("=" * 100)
    print()
    
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
            
            print(f"✅ Using page: {page.url}\n")
            
            # Open dropdown
            print("🖱️  Opening department dropdown...")
            await page.click('.ant-dropdown-trigger')
            await asyncio.sleep(2)
            print("   ✅ Opened\n")
            
            # Uncheck Sales (click it to toggle off)
            print("🖱️  Step 1: Unchecking Sales...")
            try:
                await page.click('text="Sales"', timeout=2000)
                await asyncio.sleep(0.5)
                print("   ✅ Sales unchecked\n")
            except:
                print("   ⚠️  Could not click Sales\n")
            
            # Check Service
            print("🖱️  Step 2: Checking Service...")
            try:
                await page.click('text="Service"', timeout=2000)
                await asyncio.sleep(0.5)
                print("   ✅ Service checked\n")
            except:
                print("   ⚠️  Could not click Service\n")
            
            # Parts should already be checked, but let's verify
            print("📊 Checking current state...")
            
            # Close dropdown
            print("🖱️  Closing dropdown...")
            await page.keyboard.press('Escape')
            await asyncio.sleep(2)
            print("   ✅ Closed\n")
            
            # Verify
            selection = await page.evaluate("""
                () => {
                    const trigger = document.querySelector('.ant-dropdown-trigger');
                    const deptDiv = trigger?.querySelector('#departments');
                    return deptDiv?.innerText || trigger?.innerText || 'Not found';
                }
            """)
            
            print("=" * 100)
            print(f"📊 CURRENT SELECTION: {selection}")
            print("=" * 100)
            print()
            
            # Wait 20 seconds and show progress
            print("⏳ Waiting 20 seconds for page to update...")
            print()
            for i in range(20, 0, -1):
                # Check tab counts every 5 seconds
                if i % 5 == 0:
                    tabs = await page.evaluate("""
                        () => {
                            const tabs = [];
                            document.querySelectorAll('[role="tab"]').forEach(tab => {
                                tabs.push(tab.textContent.trim());
                            });
                            return tabs;
                        }
                    """)
                    print(f"   [{20-i}s] Tabs: {' | '.join(tabs)}")
                
                print(f"   {i} seconds remaining...", end='\r')
                await asyncio.sleep(1)
            
            print("\n")
            
            # Final check
            print("=" * 100)
            print("✅ FINAL STATUS AFTER 20 SECONDS")
            print("=" * 100)
            
            final_selection = await page.evaluate("""
                () => {
                    const trigger = document.querySelector('.ant-dropdown-trigger');
                    const deptDiv = trigger?.querySelector('#departments');
                    return deptDiv?.innerText || trigger?.innerText || 'Not found';
                }
            """)
            
            final_tabs = await page.evaluate("""
                () => {
                    const tabs = [];
                    document.querySelectorAll('[role="tab"]').forEach(tab => {
                        const text = tab.textContent.trim();
                        const active = tab.getAttribute('aria-selected') === 'true';
                        tabs.push({ text, active });
                    });
                    return tabs;
                }
            """)
            
            print(f"\n🎛️  Department Selection: {final_selection}")
            print(f"\n📑 Tabs:")
            for tab in final_tabs:
                active_icon = "✓" if tab['active'] else " "
                print(f"   {active_icon} {tab['text']}")
            
            print("\n" + "=" * 100)
            print("✅ COMPLETE!")
            print("=" * 100)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
