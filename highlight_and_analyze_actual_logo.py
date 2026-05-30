#!/usr/bin/env python3
"""
Highlight and analyze the ACTUAL logo in the template
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        # Use existing tab
        page = context.pages[0]
        await page.bring_to_front()
        
        print("🎯 Highlighting the ACTUAL template logo...")
        print("=" * 100)
        
        # Find and highlight the logo
        logo_details = await page.evaluate("""
            () => {
                const allImgs = document.querySelectorAll('img');
                const logo = Array.from(allImgs).find(img => {
                    const src = img.src || '';
                    return src.includes('amazonaws.com') && 
                           src.includes('media_') &&
                           img.parentElement?.tagName === 'TD';
                });
                
                if (!logo) return null;
                
                // Highlight the logo
                logo.style.border = '5px solid lime';
                logo.style.boxShadow = '0 0 20px rgba(0, 255, 0, 0.8)';
                logo.style.outline = '3px dashed yellow';
                logo.style.outlineOffset = '5px';
                
                // Add badge
                const badge = document.createElement('div');
                badge.textContent = '🎯 LOGO';
                badge.style.cssText = `
                    position: absolute;
                    top: -40px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: lime;
                    color: black;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 16px;
                    z-index: 999999;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    white-space: nowrap;
                `;
                
                const parent = logo.parentElement;
                parent.style.position = 'relative';
                parent.appendChild(badge);
                
                // Get full details
                const rect = logo.getBoundingClientRect();
                const computedStyle = window.getComputedStyle(logo);
                
                return {
                    src: logo.src,
                    alt: logo.alt || '',
                    className: logo.className || '',
                    id: logo.id || '',
                    width: rect.width,
                    height: rect.height,
                    naturalWidth: logo.naturalWidth,
                    naturalHeight: logo.naturalHeight,
                    top: rect.top,
                    left: rect.left,
                    display: computedStyle.display,
                    maxWidth: computedStyle.maxWidth,
                    maxHeight: computedStyle.maxHeight,
                    parent: {
                        tag: parent.tagName,
                        className: parent.className || '',
                        id: parent.id || '',
                        innerHTML: parent.innerHTML.substring(0, 200)
                    },
                    outerHTML: logo.outerHTML.substring(0, 500)
                };
            }
        """)
        
        if logo_details:
            print("\n✅ FOUND AND HIGHLIGHTED THE ACTUAL TEMPLATE LOGO!\n")
            print("=" * 100)
            print("📸 LOGO DETAILS:")
            print("=" * 100)
            print()
            print(f"🌐 Source URL:")
            print(f"   {logo_details['src']}")
            print()
            print(f"📏 Dimensions:")
            print(f"   Display Size: {logo_details['width']:.0f} x {logo_details['height']:.0f} px")
            print(f"   Natural Size: {logo_details['naturalWidth']} x {logo_details['naturalHeight']} px")
            print(f"   Max Width: {logo_details['maxWidth']}")
            print(f"   Max Height: {logo_details['maxHeight']}")
            print()
            print(f"📍 Position:")
            print(f"   Top: {logo_details['top']:.0f}px")
            print(f"   Left: {logo_details['left']:.0f}px")
            print()
            print(f"🏷️  Attributes:")
            print(f"   ID: {logo_details['id'] or 'N/A'}")
            print(f"   Class: {logo_details['className'] or 'N/A'}")
            print(f"   Alt: {logo_details['alt'] or 'N/A'}")
            print()
            print(f"👨‍👩‍👧 Parent Element:")
            print(f"   Tag: <{logo_details['parent']['tag']}>")
            print(f"   ID: {logo_details['parent']['id'] or 'N/A'}")
            print(f"   Class: {logo_details['parent']['className'] or 'N/A'}")
            print()
            print(f"💻 HTML:")
            print(f"   {logo_details['outerHTML']}")
            print()
            print("=" * 100)
            print("✅ STATUS:")
            print("=" * 100)
            print()
            print("  🟢 Logo is now highlighted with:")
            print("     - Lime green border (5px)")
            print("     - Yellow dashed outline")
            print("     - Green glow shadow")
            print("     - '🎯 LOGO' badge above it")
            print()
            print("  📸 Taking screenshot...")
            
            await page.screenshot(path='actual_logo_highlighted.png', full_page=True)
            print("  ✅ Screenshot saved: actual_logo_highlighted.png")
            print()
            print("=" * 100)
            print("🎯 THIS IS THE LOGO TO REPLACE (Nucar → Tilton)")
            print("=" * 100)
        else:
            print("❌ Logo not found!")


if __name__ == "__main__":
    asyncio.run(main())
