#!/usr/bin/env python3
"""
Inspect the actual API response structure
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        # Find templates page
        page = None
        for p in context.pages:
            if 'templates/list' in p.url:
                page = p
                break
        
        if not page:
            print("❌ Templates page not found")
            return
        
        await page.bring_to_front()
        
        print("🔍 Intercepting API calls...")
        print("=" * 80)
        
        captured_responses = []
        
        async def handle_response(response):
            if '/api/templatestore/u/search' in response.url:
                try:
                    data = await response.json()
                    captured_responses.append(data)
                    
                    print(f"\n📥 API Response #{len(captured_responses)}:")
                    print(f"   URL: {response.url}")
                    print(f"   Status: {response.status}")
                    
                    # Show structure
                    if 'data' in data:
                        data_obj = data['data']
                        print(f"   data keys: {list(data_obj.keys())}")
                        
                        if 'groups' in data_obj:
                            print(f"   groups: {len(data_obj['groups'])} groups")
                            for i, group in enumerate(data_obj['groups']):
                                print(f"     Group {i}: {group.get('label', 'N/A')} - {len(group.get('hits', []))} hits")
                        
                        if 'hits' in data_obj:
                            print(f"   hits: {len(data_obj['hits'])} templates")
                        
                        if 'totalCount' in data_obj:
                            print(f"   totalCount: {data_obj['totalCount']}")
                    
                    # Save to file
                    with open(f'api_response_{len(captured_responses)}.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"   💾 Saved to api_response_{len(captured_responses)}.json")
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
        
        page.on('response', handle_response)
        
        print("\n⏳ Reloading page to capture API calls...")
        await page.reload(wait_until='domcontentloaded')
        
        # Wait a bit for all responses
        await asyncio.sleep(5)
        
        page.remove_listener('response', handle_response)
        
        print(f"\n✅ Captured {len(captured_responses)} API responses")


if __name__ == "__main__":
    asyncio.run(main())
