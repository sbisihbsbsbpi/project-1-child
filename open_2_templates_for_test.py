#!/usr/bin/env python3
"""
Open exactly 2 templates for testing center align and enlarge
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://localhost:9223')
        context = browser.contexts[0]
        
        # Test with 2 different templates
        templates = [
            {
                'id': '667f0befd4964026ee7b6e46',
                'name': 'RO Invoiced'
            },
            {
                'id': '667f0befd4964026ee7b6e48',
                'name': 'Customer Pay Closed'
            }
        ]
        
        print("=" * 80)
        print("🚀 OPENING 2 TEMPLATES FOR TESTING")
        print("=" * 80)
        print()
        
        for i, template in enumerate(templates, 1):
            url = f"https://preprodapp.tekioncloud.com/templates/edit/{template['id']}"
            print(f"[{i}/2] Opening: {template['name']}")
            print(f"   URL: {url}")
            
            page = await context.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)
            
            print(f"   ✅ Opened successfully")
            print()
        
        print("=" * 80)
        print("✅ 2 TEMPLATES OPENED")
        print("=" * 80)
        print()
        print("Now run: python3 process_opened_templates.py")

asyncio.run(main())
