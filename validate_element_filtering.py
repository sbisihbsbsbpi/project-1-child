#!/usr/bin/env python3
"""
Validate Element Filtering - Check if our smart filtering is working
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page


async def main():
    template_id = '667f0befd4964026ee7b6ea4'
    
    print("=" * 100)
    print("🔍 VALIDATING ELEMENT FILTERING")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        
        url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        page = await get_or_navigate_to_page(browser, url, wait_for_load=True)
        
        print("✅ Template editor loaded")
        await asyncio.sleep(3)
        
        # Get element count from the navigator
        result = await page.evaluate("""
            () => {
                return {
                    totalFound: window.navElements ? window.navElements.length : 0,
                    elements: window.navElements ? window.navElements.map((item, idx) => ({
                        index: idx + 1,
                        type: item.type,
                        width: Math.round(item.rect.width),
                        height: Math.round(item.rect.height),
                        position: {
                            top: Math.round(item.rect.top),
                            left: Math.round(item.rect.left)
                        }
                    })) : []
                };
            }
        """)
        
        print(f"Total Elements Found (after filtering): {result['totalFound']}")
        print()
        
        print("=" * 100)
        print("📋 ELEMENT LIST")
        print("=" * 100)
        print()
        
        for el in result['elements']:
            print(f"Element #{el['index']}: {el['type']}")
            print(f"  Size: {el['width']}x{el['height']}px")
            print(f"  Position: top={el['position']['top']}px, left={el['position']['left']}px")
            print()
        
        print("=" * 100)
        print("🎯 ANALYSIS")
        print("=" * 100)
        print()
        
        # Count by type
        images = [e for e in result['elements'] if 'IMAGE' in e['type']]
        buttons = [e for e in result['elements'] if 'BUTTON' in e['type']]
        other = [e for e in result['elements'] if 'IMAGE' not in e['type'] and 'BUTTON' not in e['type']]
        
        print(f"Images: {len(images)}")
        print(f"Buttons: {len(buttons)}")
        print(f"Other: {len(other)}")
        print()
        
        print("🔎 Expected Results:")
        print("  - Should see FAR FEWER elements than before (~20)")
        print("  - Should NOT see: scrollbars, back/settings/draft/publish buttons")
        print("  - Should see: template content elements only")
        print("  - Element #20 (or similar) should be the bottom-right logo")
        print()
        
        # Find likely logo candidates
        logo_candidates = [e for e in result['elements'] if 'IMAGE' in e['type'] and e['width'] > 50 and e['height'] > 30]
        
        if logo_candidates:
            print("🎯 Logo Candidates Found:")
            for candidate in logo_candidates:
                print(f"  - Element #{candidate['index']}: {candidate['type']}")
                print(f"    Size: {candidate['width']}x{candidate['height']}px")
            print()
        
        print("✅ Validation complete!")
        print()
        print("👉 Now navigate through the elements in the browser to verify filtering!")


if __name__ == "__main__":
    asyncio.run(main())
