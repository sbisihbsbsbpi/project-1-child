#!/usr/bin/env python3
"""
Identify Insert Icons - Find which navigator elements are the left panel insert icons
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page


async def main():
    template_id = '667f0befd4964026ee7b6ea4'
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        
        url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        page = await get_or_navigate_to_page(browser, url, wait_for_load=True)
        
        await asyncio.sleep(2)
        
        # Get elements with text content and aria labels
        result = await page.evaluate("""
            () => {
                if (!window.navElements) return { error: 'Navigator not loaded' };
                
                return {
                    total: window.navElements.length,
                    elements: window.navElements.map((item, idx) => {
                        const el = item.el;
                        const text = (el.textContent || '').trim();
                        const ariaLabel = el.getAttribute('aria-label') || '';
                        const title = el.title || '';
                        const closest = el.closest('[class*="insert"]') || el.closest('[class*="Insert"]');
                        
                        return {
                            index: idx + 1,
                            type: item.type,
                            text: text.substring(0, 50),
                            ariaLabel: ariaLabel,
                            title: title,
                            inInsertPanel: !!closest,
                            width: Math.round(item.rect.width),
                            height: Math.round(item.rect.height),
                            left: Math.round(item.rect.left),
                            top: Math.round(item.rect.top)
                        };
                    })
                };
            }
        """)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
            return
        
        print("=" * 100)
        print("🔍 SEARCHING FOR INSERT PANEL ICONS")
        print("=" * 100)
        print()
        
        # Look for elements in left panel (left < 450) with typical icon sizes
        left_panel = [e for e in result['elements'] if e['left'] < 450]
        
        print(f"Total elements: {result['total']}")
        print(f"Left panel elements (left < 450px): {len(left_panel)}")
        print()
        
        # Group by size to find icon patterns
        icon_sizes = {}
        for el in left_panel:
            size_key = f"{el['width']}x{el['height']}"
            if size_key not in icon_sizes:
                icon_sizes[size_key] = []
            icon_sizes[size_key].append(el)
        
        print("=" * 100)
        print("📊 LEFT PANEL ELEMENTS BY SIZE")
        print("=" * 100)
        print()
        
        for size, elements in sorted(icon_sizes.items(), key=lambda x: -len(x[1])):
            print(f"{size}: {len(elements)} elements")
            if len(elements) <= 5:  # Show details for less common sizes
                for el in elements:
                    print(f"  Element #{el['index']}: {el['type']} - \"{el['text'][:30]}\"")
        print()
        
        # Look for "Image" and "Cover Image" text
        print("=" * 100)
        print("🎯 LIKELY INSERT ICONS (by text content)")
        print("=" * 100)
        print()
        
        insert_keywords = ['image', 'video', 'button', 'link', 'attach', 'dealer logo', 'cover', 'header', 'separator', 'column']
        
        for el in left_panel:
            text_lower = (el['text'] + ' ' + el['ariaLabel'] + ' ' + el['title']).lower()
            if any(keyword in text_lower for keyword in insert_keywords):
                print(f"Element #{el['index']}: {el['width']}x{el['height']}px at ({el['left']}, {el['top']})")
                print(f"  Type: {el['type']}")
                print(f"  Text: \"{el['text'][:40]}\"")
                if el['ariaLabel']:
                    print(f"  Aria: \"{el['ariaLabel']}\"")
                print()


if __name__ == "__main__":
    asyncio.run(main())
