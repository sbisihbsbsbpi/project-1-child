#!/usr/bin/env python3
"""
Show Navigator View - Display elements exactly as they appear in the navigator
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
    print("🔍 NAVIGATOR VIEW - Elements as YOU see them")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        
        url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        page = await get_or_navigate_to_page(browser, url, wait_for_load=True)
        
        print("✅ Template editor loaded")
        await asyncio.sleep(2)
        
        # Get ONLY the shown elements (what you see in navigator)
        result = await page.evaluate("""
            () => {
                if (!window.navElements) {
                    return { error: 'Navigator not loaded yet' };
                }
                
                return {
                    total: window.navElements.length,
                    elements: window.navElements.map((item, idx) => ({
                        navigatorIndex: idx + 1,  // This is what YOU see in the navigator UI
                        type: item.type,
                        width: Math.round(item.rect.width),
                        height: Math.round(item.rect.height),
                        position: {
                            top: Math.round(item.rect.top),
                            left: Math.round(item.rect.left)
                        }
                    }))
                };
            }
        """)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"Total elements in navigator: {result['total']}")
        print()
        print("=" * 100)
        print("📋 NAVIGATOR ELEMENTS (This is what YOU see when navigating)")
        print("=" * 100)
        print()
        
        # User's specifications based on navigator index
        user_specs = {
            1: "IGNORE",
            2: "Scrollbar",
            3: "Scrollbar",
            4: "IGNORE",
            5: "IGNORE",
            6: "Back button",
            7: "Settings button",
            8: "Draft button",
            9: "Publish button",
            10: "KEEP (useful)",
            11: "IGNORE",
            12: "IGNORE",
            13: "IGNORE",
            14: "IGNORE",
            15: "IGNORE",
            16: "IGNORE",
            17: "IGNORE",
            18: "KEEP (useful)",
            19: "IGNORE",
            20: "✅ BOTTOM-RIGHT LOGO"
        }
        
        for el in result['elements']:
            idx = el['navigatorIndex']
            spec = user_specs.get(idx, "")
            marker = ""
            
            if idx == 20:
                marker = " ⭐⭐⭐ LOGO ⭐⭐⭐"
            elif idx == 10 or idx == 18:
                marker = " 👍 KEEP"
            elif spec and "button" in spec.lower():
                marker = " 🚫 UI CONTROL"
            elif spec == "Scrollbar":
                marker = " 🚫 SCROLLBAR"
            elif spec == "IGNORE":
                marker = " 🚫 IGNORE"
            
            print(f"Navigator Element #{idx}: {el['type']}{marker}")
            if spec:
                print(f"  User spec: {spec}")
            print(f"  Size: {el['width']}x{el['height']}px")
            print(f"  Position: top={el['position']['top']}px, left={el['position']['left']}px")
            print()
        
        print("=" * 100)
        print("🎯 SUMMARY")
        print("=" * 100)
        print()
        
        # Find element #20
        el20 = result['elements'][19] if len(result['elements']) >= 20 else None
        if el20:
            print("✅ ELEMENT #20 (Bottom-Right Logo):")
            print(f"   Type: {el20['type']}")
            print(f"   Size: {el20['width']}x{el20['height']}px")
            print(f"   Position: top={el20['position']['top']}px, left={el20['position']['left']}px")
            
            # Check if it matches our known Tilton logo
            if '6a19132b' in el20['type']:
                print("   ✅ CONFIRMED: This is the Tilton logo (6a19132b6697f36de6236fb1)")
            elif '78213cf8' in el20['type']:
                print("   ⚠️  This appears to be a different logo (78213cf8...)")
            print()
        else:
            print("❌ Element #20 not found - navigator has fewer than 20 elements")
            print()


if __name__ == "__main__":
    asyncio.run(main())
