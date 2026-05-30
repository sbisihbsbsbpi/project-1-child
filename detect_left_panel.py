#!/usr/bin/env python3
"""
Detect Left Panel - Find and analyze the left sidebar insert panel
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
        
        # Detect left panel elements
        result = await page.evaluate("""
            () => {
                const leftPanelElements = [];
                
                // Find the left panel (Inserts panel)
                const possibleSelectors = [
                    '[class*="insert"]',
                    '[class*="Insert"]',
                    '[class*="sidebar"]',
                    '[class*="Sidebar"]',
                    '[class*="panel"]',
                    '[class*="Panel"]',
                    'aside',
                    '[role="complementary"]'
                ];
                
                let leftPanel = null;
                for (const sel of possibleSelectors) {
                    const panels = document.querySelectorAll(sel);
                    for (const panel of panels) {
                        const rect = panel.getBoundingClientRect();
                        // Left panel should be on the left side and reasonably tall
                        if (rect.left < 300 && rect.height > 400) {
                            leftPanel = panel;
                            break;
                        }
                    }
                    if (leftPanel) break;
                }
                
                if (leftPanel) {
                    // Find all clickable elements in the left panel
                    const selectors = ['button', 'a', 'div[role="button"]', '[class*="icon"]', '[class*="Icon"]'];
                    
                    selectors.forEach(sel => {
                        leftPanel.querySelectorAll(sel).forEach(el => {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 10 && rect.height > 10) {
                                const text = (el.textContent || el.title || el.ariaLabel || '').trim();
                                leftPanelElements.push({
                                    type: el.tagName.toLowerCase(),
                                    text: text.substring(0, 30),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height),
                                    left: Math.round(rect.left),
                                    top: Math.round(rect.top),
                                    className: el.className
                                });
                            }
                        });
                    });
                    
                    return {
                        found: true,
                        panelRect: {
                            left: Math.round(leftPanel.getBoundingClientRect().left),
                            top: Math.round(leftPanel.getBoundingClientRect().top),
                            width: Math.round(leftPanel.getBoundingClientRect().width),
                            height: Math.round(leftPanel.getBoundingClientRect().height)
                        },
                        elements: leftPanelElements,
                        totalElements: leftPanelElements.length
                    };
                }
                
                return { found: false };
            }
        """)
        
        if not result['found']:
            print("❌ Left panel not detected")
            print("Searching entire left side of page...")
            
            # Fallback: find all elements on left side
            result = await page.evaluate("""
                () => {
                    const leftElements = [];
                    const allElements = document.querySelectorAll('*');
                    
                    allElements.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        // Left side: left < 300px, reasonable size
                        if (rect.left < 300 && rect.width > 20 && rect.width < 200 && rect.height > 20 && rect.height < 200) {
                            const text = (el.textContent || '').trim();
                            if (text.length < 50) {  // Avoid large containers
                                leftElements.push({
                                    type: el.tagName.toLowerCase(),
                                    text: text.substring(0, 30),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height),
                                    left: Math.round(rect.left),
                                    top: Math.round(rect.top)
                                });
                            }
                        }
                    });
                    
                    return {
                        found: true,
                        elements: leftElements,
                        totalElements: leftElements.length
                    };
                }
            """)
        
        print("=" * 100)
        print("📋 LEFT PANEL ELEMENTS DETECTED")
        print("=" * 100)
        print()
        
        if 'panelRect' in result:
            print("Left Panel Found:")
            print(f"  Position: left={result['panelRect']['left']}px, top={result['panelRect']['top']}px")
            print(f"  Size: {result['panelRect']['width']}x{result['panelRect']['height']}px")
            print()
        
        print(f"Total elements found: {result['totalElements']}")
        print()
        
        # Group by type
        from collections import defaultdict
        by_type = defaultdict(list)
        
        for el in result['elements']:
            by_type[el['type']].append(el)
        
        print("By Type:")
        for typ, elements in sorted(by_type.items()):
            print(f"  {typ}: {len(elements)} elements")
        print()
        
        # Show insert-related elements
        print("=" * 100)
        print("🎨 INSERT PANEL ICONS (Image, Video, Button, etc.)")
        print("=" * 100)
        print()
        
        insert_keywords = ['image', 'video', 'button', 'link', 'attach', 'logo', 'cover', 'header', 
                          'separator', 'column', 'tag', 'sender', 'dealer', 'signature']
        
        insert_elements = []
        for el in result['elements']:
            text_lower = el['text'].lower()
            if any(keyword in text_lower for keyword in insert_keywords):
                insert_elements.append(el)
        
        if insert_elements:
            for i, el in enumerate(insert_elements[:20], 1):
                print(f"{i}. {el['type']}: \"{el['text']}\"")
                print(f"   Size: {el['width']}x{el['height']}px at ({el['left']}, {el['top']})")
                print()
        else:
            print("⚠️  No insert elements found by text matching")
            print("Showing all left panel elements:")
            print()
            for i, el in enumerate(result['elements'][:30], 1):
                print(f"{i}. {el['type']}: \"{el['text']}\"")
                print(f"   Size: {el['width']}x{el['height']}px")
                print()
        
        print("=" * 100)
        print("🎯 PATTERN DETECTED")
        print("=" * 100)
        print()
        print("These left panel elements should be BLOCKED:")
        print("  - They are editor UI controls (Insert > Image, Video, etc.)")
        print("  - They are NOT template content")
        print("  - Position: left < 300px")
        print()


if __name__ == "__main__":
    asyncio.run(main())
