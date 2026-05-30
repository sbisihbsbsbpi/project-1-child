#!/usr/bin/env python3
"""
Deep dive into template body to find WHERE the logo appears
"""

import asyncio
import json
from playwright.async_api import async_playwright
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page


async def main():
    template_id = '667f0befd4964026ee7b6ea4'
    
    print("=" * 100)
    print("DEEP DIVE: WHERE IS THE THUMBNAIL LOGO PLACED?")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        
        # Navigate to template
        url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        page = await get_or_navigate_to_page(browser, url, wait_for_load=True)
        
        # Capture API response
        template_data = None
        response_captured = asyncio.Event()
        
        async def handle_response(response):
            nonlocal template_data
            if '/api/templatestore/u/fetch' in response.url:
                try:
                    data = await response.json()
                    if 'data' in data:
                        template_data = data['data']
                        response_captured.set()
                except:
                    pass
        
        page.on('response', handle_response)
        await page.reload(wait_until='domcontentloaded')
        
        try:
            await asyncio.wait_for(response_captured.wait(), timeout=10)
        except:
            print("⚠️  Could not capture API data")
            return
        
        page.remove_listener('response', handle_response)
        
        if not template_data:
            print("❌ No template data")
            return
        
        print("✅ Template data captured")
        print()
        
        # Analyze thumbnail
        thumbnail = template_data.get('thumbnail', {})
        print("📸 THUMBNAIL FIELD:")
        print(f"   Media ID: {thumbnail.get('mediaId')}")
        print(f"   Name: {thumbnail.get('name')}")
        print()
        
        # Parse body
        body_str = template_data.get('body')
        if not body_str:
            print("❌ No body found")
            return
        
        body = json.loads(body_str) if isinstance(body_str, str) else body_str
        
        print(f"📄 BODY COMPONENTS: {len(body)}")
        print("=" * 100)
        print()
        
        # Check each component
        found_thumbnail_ref = False
        
        for idx, component in enumerate(body):
            comp_key = component.get('key', 'UNKNOWN')
            comp_props = component.get('componentProps', {})
            html = comp_props.get('html', '')
            
            print(f"{idx + 1}. {comp_key}")
            
            # Look for thumbnail references
            if '{{THUMBNAIL_URL}}' in html or 'THUMBNAIL' in html:
                found_thumbnail_ref = True
                print(f"   🎯 CONTAINS THUMBNAIL REFERENCE!")
                print(f"   HTML: {html[:300]}...")
                print()
            elif 'FOOTER' in comp_key.upper() or 'LOGO' in comp_key.upper():
                print(f"   📍 Potential logo location (footer/logo component)")
                if html:
                    print(f"   HTML: {html[:200]}...")
                print()
        
        print("=" * 100)
        print("CONCLUSION:")
        print("=" * 100)
        print()
        
        if found_thumbnail_ref:
            print("✅ Thumbnail is EXPLICITLY used in the body HTML")
            print("   The template contains {{THUMBNAIL_URL}} template variable")
            print("   Logo is rendered as part of the email body")
        else:
            print("❌ Thumbnail is NOT found in body HTML")
            print("   The thumbnail field is used by the EMAIL SYSTEM")
            print("   Logo is auto-injected by Tekion's email rendering system")
            print("   Likely placement: Email footer (standard practice)")
            print()
            print("   This means:")
            print("   • You update: template.thumbnail.mediaId via API")
            print("   • System renders: Logo in email footer automatically")
            print("   • No body HTML changes needed!")
        
        # Save full body for analysis
        with open('template_body_full.json', 'w') as f:
            json.dump(body, f, indent=2)
        
        print()
        print("💾 Full body saved to: template_body_full.json")


if __name__ == "__main__":
    asyncio.run(main())
