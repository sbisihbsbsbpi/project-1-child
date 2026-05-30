#!/usr/bin/env python3
import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://localhost:9223')
        page = await get_or_navigate_to_page(browser, 'https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6ea4', wait_for_load=True)
        
        result = await page.evaluate('''
            () => {
                const selectors = [
                    '[contenteditable="true"]',
                    '[class*="canvas"]',
                    '[class*="editor-content"]',
                    '[class*="template-body"]',
                    '[id*="editor"]',
                    'main'
                ];
                
                const results = [];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        results.push({
                            selector: sel,
                            images: el.querySelectorAll('img').length,
                            buttons: el.querySelectorAll('button').length,
                            found: true
                        });
                    } else {
                        results.push({ selector: sel, found: false });
                    }
                }
                
                return {
                    results: results,
                    totalImages: document.querySelectorAll('img').length,
                    totalButtons: document.querySelectorAll('button').length
                };
            }
        ''')
        
        print("Content Area Detection Results:")
        print("=" * 60)
        for r in result['results']:
            if r['found']:
                print(f"✅ {r['selector']}")
                print(f"   Images: {r['images']}, Buttons: {r['buttons']}")
            else:
                print(f"❌ {r['selector']} - not found")
        
        print()
        print(f"Total in page: Images={result['totalImages']}, Buttons={result['totalButtons']}")

asyncio.run(main())
