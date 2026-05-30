#!/usr/bin/env python3
"""
Find which API response contains actual template data
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
        
        print("🔍 Looking for API response with template data...")
        print("=" * 80)
        
        response_count = 0
        found_templates = False
        
        async def handle_response(response):
            nonlocal response_count, found_templates
            
            if '/api/templatestore/u/search' in response.url:
                response_count += 1
                try:
                    data = await response.json()
                    
                    # Check if this response has actual template hits
                    if 'data' in data and 'hits' in data['data']:
                        hits = data['data']['hits']
                        
                        if hits and len(hits) > 0:
                            print(f"\n✅ Response #{response_count}: FOUND {len(hits)} TEMPLATES!")
                            print(f"   First template: {hits[0].get('name', 'N/A')}")
                            print(f"   Template ID: {hits[0].get('id', 'N/A')}")
                            
                            # Save this one
                            with open(f'template_response_{response_count}.json', 'w') as f:
                                json.dump(data, f, indent=2)
                            print(f"   💾 Saved to template_response_{response_count}.json")
                            
                            found_templates = True
                        else:
                            print(f"\n❌ Response #{response_count}: hits array is EMPTY")
                    else:
                        print(f"\n❌ Response #{response_count}: No 'hits' in data")
                    
                except Exception as e:
                    print(f"\n❌ Response #{response_count}: Error - {e}")
        
        page.on('response', handle_response)
        
        print("\n⏳ Reloading page...")
        await page.reload(wait_until='domcontentloaded')
        
        # Wait for all responses
        await asyncio.sleep(8)
        
        page.remove_listener('response', handle_response)
        
        print(f"\n" + "=" * 80)
        if found_templates:
            print("✅ Found template data in API responses!")
        else:
            print("❌ No template data found - templates might load differently")
        print(f"Total API calls captured: {response_count}")


if __name__ == "__main__":
    asyncio.run(main())
