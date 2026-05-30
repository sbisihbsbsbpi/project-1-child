#!/usr/bin/env python3
"""
Element Identifier - Help user identify each element with extra details
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
        
        # Add element identifier overlay
        await page.evaluate("""
            () => {
                if (!window.navElements) {
                    console.error('Navigator not loaded');
                    return;
                }
                
                // Add permanent labels to ALL elements
                window.navElements.forEach((item, idx) => {
                    const el = item.el;
                    const label = document.createElement('div');
                    label.className = 'permanent-element-label';
                    label.textContent = '#' + (idx + 1);
                    label.style.cssText = `
                        position: absolute;
                        top: -25px;
                        left: 0;
                        background: rgba(255, 0, 0, 0.9);
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                        z-index: 2147483640;
                        font-family: Arial, sans-serif;
                        pointer-events: none;
                        border: 2px solid white;
                    `;
                    
                    // Make parent position relative if not already
                    const computed = window.getComputedStyle(el);
                    if (computed.position === 'static') {
                        el.style.position = 'relative';
                    }
                    
                    el.appendChild(label);
                });
                
                console.log('✅ Added permanent labels to all ' + window.navElements.length + ' elements');
            }
        """)
        
        print("=" * 100)
        print("🏷️  PERMANENT ELEMENT LABELS ADDED")
        print("=" * 100)
        print()
        print("✅ Every element now has a small RED label showing its number!")
        print()
        print("Now you can:")
        print("  1. See ALL element numbers at once")
        print("  2. Navigate using NEXT/PREV to pulse-highlight them")
        print("  3. Easily identify which is which")
        print()
        print("The labels show: #1, #2, #3, etc.")
        print()


if __name__ == "__main__":
    asyncio.run(main())
