#!/usr/bin/env python3
"""
Open template edit page and find logo position
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
        
        # Use existing tab
        page = context.pages[0]
        await page.bring_to_front()
        
        print("🔗 Opening template edit page...")
        await page.goto("https://preprodapp.tekioncloud.com/templates/edit/CPRA_REQUEST_COMPLETION_DATA_DELETION_CLOSED_DOCUMENTS")
        
        print("⏳ Waiting for page to load...")
        await asyncio.sleep(5)
        
        print("\n🔍 Searching for logo elements...\n")
        print("=" * 100)
        
        # Search for logo-related elements
        logo_info = await page.evaluate("""
            () => {
                const results = [];
                
                // Search for images
                const images = document.querySelectorAll('img');
                images.forEach((img, idx) => {
                    const src = img.src || '';
                    const alt = img.alt || '';
                    const classes = img.className || '';
                    
                    // Check if likely a logo
                    if (src.toLowerCase().includes('logo') || 
                        alt.toLowerCase().includes('logo') ||
                        classes.toLowerCase().includes('logo') ||
                        src.includes('nucar') ||
                        src.includes('tilton')) {
                        
                        const rect = img.getBoundingClientRect();
                        results.push({
                            type: 'img',
                            index: idx,
                            src: src.substring(0, 150),
                            alt: alt,
                            className: classes,
                            width: rect.width,
                            height: rect.height,
                            top: rect.top,
                            left: rect.left,
                            visible: img.offsetParent !== null,
                            parent: img.parentElement?.tagName || 'N/A',
                            parentClass: img.parentElement?.className || ''
                        });
                    }
                });
                
                // Search for elements with 'logo' in text, id, or class
                const allElements = document.querySelectorAll('*');
                allElements.forEach((el, idx) => {
                    const id = el.id || '';
                    const classes = el.className || '';
                    const text = el.textContent?.trim().substring(0, 50) || '';
                    
                    if (id.toLowerCase().includes('logo') || 
                        (typeof classes === 'string' && classes.toLowerCase().includes('logo'))) {
                        
                        const rect = el.getBoundingClientRect();
                        
                        // Skip if already found as img
                        if (el.tagName !== 'IMG' || !results.find(r => r.type === 'img' && r.src === el.src)) {
                            results.push({
                                type: el.tagName.toLowerCase(),
                                index: idx,
                                id: id,
                                className: typeof classes === 'string' ? classes.substring(0, 80) : '',
                                text: text,
                                width: rect.width,
                                height: rect.height,
                                top: rect.top,
                                left: rect.left,
                                visible: el.offsetParent !== null
                            });
                        }
                    }
                });
                
                return results;
            }
        """)
        
        if logo_info:
            print(f"✅ Found {len(logo_info)} logo-related elements:\n")
            
            for i, info in enumerate(logo_info, 1):
                visible = "✅ VISIBLE" if info['visible'] else "❌ HIDDEN"
                print(f"{i}. {visible} - {info['type'].upper()}")
                
                if info['type'] == 'img':
                    print(f"   Src: {info['src']}")
                    print(f"   Alt: {info['alt']}")
                    print(f"   Class: {info['className']}")
                    print(f"   Parent: <{info['parent']}> class=\"{info['parentClass'][:60]}\"")
                else:
                    print(f"   ID: {info.get('id', 'N/A')}")
                    print(f"   Class: {info.get('className', 'N/A')}")
                    print(f"   Text: {info.get('text', 'N/A')}")
                
                print(f"   Size: {info['width']:.0f}x{info['height']:.0f} px")
                print(f"   Position: top={info['top']:.0f}px, left={info['left']:.0f}px")
                print()
        else:
            print("❌ No logo elements found with keyword 'logo'")
            print("\n🔍 Let me search for all images on the page...\n")
            
            # Find all images
            all_images = await page.evaluate("""
                () => {
                    const images = document.querySelectorAll('img');
                    return Array.from(images).map((img, idx) => ({
                        index: idx,
                        src: img.src?.substring(0, 150) || '',
                        alt: img.alt || '',
                        className: img.className || '',
                        width: img.getBoundingClientRect().width,
                        height: img.getBoundingClientRect().height,
                        visible: img.offsetParent !== null
                    }));
                }
            """)
            
            print(f"Found {len(all_images)} total images:\n")
            for i, img in enumerate(all_images[:10], 1):  # Show first 10
                visible = "✅" if img['visible'] else "❌"
                print(f"{i}. {visible} {img['width']:.0f}x{img['height']:.0f}px")
                print(f"   {img['src']}")
                print()
        
        print("=" * 100)
        
        # Save screenshot
        print("\n📸 Taking screenshot...")
        await page.screenshot(path='template_edit_page.png', full_page=True)
        print("✅ Screenshot saved: template_edit_page.png")


if __name__ == "__main__":
    asyncio.run(main())
