#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        templates = []
        response_received = asyncio.Event()
        
        async def handle_response(response):
            nonlocal templates
            if '/api/templatestore/u/search' in response.url:
                try:
                    data = await response.json()
                    if 'data' in data and 'hits' in data['data']:
                        hits = data['data']['hits']
                        templates.extend(hits)
                        response_received.set()
                except: pass
        
        page = await context.new_page()
        page.on('response', handle_response)
        
        await page.goto("https://preprodapp.tekioncloud.com/templates/list", wait_until='domcontentloaded')
        await asyncio.sleep(3)
        
        try:
            await asyncio.wait_for(response_received.wait(), timeout=10.0)
        except: pass
        
        page.remove_listener('response', handle_response)
        await page.close()
        
        print(f"Total templates: {len(templates)}")
        if templates:
            print(f"\nFirst template:")
            t = templates[0]
            print(f"  Name: {t.get('name')}")
            print(f"  ID: {t.get('templateId') or t.get('id')}")
            print(f"  Departments: {t.get('departments')}")
            print(f"  Department Type: {type(t.get('departments'))}")
            print(f"\nAll keys: {list(t.keys())[:20]}")

if __name__ == "__main__":
    asyncio.run(main())
