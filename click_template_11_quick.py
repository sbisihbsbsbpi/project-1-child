#!/usr/bin/env python3
"""
Quick click on 11th template
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("🖱️  Clicking template #11...\n")
    
    async with async_playwright() as playwright:
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
            await asyncio.sleep(2)
        
        await page.bring_to_front()
        print(f"✅ Page: {page.url}\n")
        
        # Get template info
        templates = await page.evaluate("""
            () => {
                const rows = document.querySelectorAll('[role="grid"] [role="row"]');
                const dataRows = Array.from(rows).slice(1); // Skip header
                
                return dataRows.map((row, i) => {
                    const nameCell = row.querySelector('[role="gridcell"]:nth-child(2)');
                    return {
                        index: i + 1,
                        name: nameCell ? nameCell.textContent.trim() : 'Unknown'
                    };
                });
            }
        """)
        
        print(f"📋 Found {len(templates)} templates\n")
        
        if len(templates) >= 11:
            target = templates[10]  # 0-based, so 10 = 11th
            print(f"🎯 Template #11: {target['name']}\n")
            
            # Click it
            print("🖱️  Clicking...")
            selector = f"[role='grid'] [role='row']:nth-child(12) [role='gridcell']:nth-child(2)"
            await page.click(selector)
            print("   ✅ Clicked!\n")
            
            # Wait a bit
            await asyncio.sleep(2)
            
            print(f"📍 New URL: {page.url}\n")
            
            if '/edit/' in page.url:
                print("✅ Template editor opened!")
            else:
                print("⚠️  Still on list page")
                
        else:
            print(f"❌ Only {len(templates)} templates found, need at least 11")


if __name__ == "__main__":
    asyncio.run(main())
