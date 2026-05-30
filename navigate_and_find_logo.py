#!/usr/bin/env python3
"""
Navigate to Tekion template and find the actual logo for replacement
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
        
        print("🌐 Current URL:", page.url)
        
        # Navigate to template edit page
        template_url = "https://preprodapp.tekioncloud.com/templates/edit/CPRA_REQUEST_COMPLETION_DATA_DELETION_CLOSED_DOCUMENTS"
        
        print(f"\n🔗 Navigating to template edit page...")
        await page.goto(template_url)
        await asyncio.sleep(5)  # Wait for page to load
        
        print("✅ Page loaded\n")
        print("=" * 100)
        print("🔍 Searching for ALL images (excluding ignored UI elements)...")
        print("=" * 100)
        
        # Load ignore list
        with open('logo_ignore_list.json') as f:
            ignore_list = json.load(f)
        
        # Search for all images
        all_images = await page.evaluate("""
            (ignorePatterns) => {
                const results = [];
                
                // Helper to check if ignored
                function isIgnored(el) {
                    if (ignorePatterns.ids.includes(el.id)) return true;
                    const classes = el.className || '';
                    for (const pattern of ignorePatterns.class_names) {
                        if (classes.includes(pattern)) return true;
                    }
                    for (const parentSelector of ignorePatterns.parent_selectors) {
                        if (el.closest(parentSelector)) return true;
                    }
                    return false;
                }
                
                const allImgs = document.querySelectorAll('img');
                
                allImgs.forEach((img, idx) => {
                    if (isIgnored(img)) return;
                    
                    const rect = img.getBoundingClientRect();
                    const src = img.src || '';
                    const alt = img.alt || '';
                    
                    results.push({
                        index: idx,
                        src: src,
                        alt: alt,
                        className: img.className || '',
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        left: rect.left,
                        visible: img.offsetParent !== null,
                        parent: img.parentElement?.tagName || '',
                        parentClass: img.parentElement?.className?.substring(0, 80) || '',
                        parentId: img.parentElement?.id || ''
                    });
                });
                
                return results;
            }
        """, ignore_list['ignore_patterns'])
        
        print(f"\n✅ Found {len(all_images)} images (excluding UI elements):\n")
        
        if all_images:
            for i, img in enumerate(all_images, 1):
                visible = "✅ VISIBLE" if img['visible'] else "❌ HIDDEN"
                print(f"{i}. {visible}")
                print(f"   Src: {img['src'][:120]}")
                print(f"   Alt: {img['alt']}")
                print(f"   Size: {img['width']:.0f}x{img['height']:.0f} px")
                print(f"   Position: top={img['top']:.0f}px, left={img['left']:.0f}px")
                print(f"   Parent: <{img['parent']}> id=\"{img['parentId']}\" class=\"{img['parentClass'][:60]}\"")
                
                # Check if this looks like a logo
                is_logo = ('logo' in img['src'].lower() or 
                          'logo' in img['alt'].lower() or
                          'nucar' in img['src'].lower() or
                          'tilton' in img['src'].lower())
                
                if is_logo:
                    print(f"   🎯 LIKELY LOGO!")
                print()
        else:
            print("⚠️  No images found (after filtering out UI elements)")
            
            # Let's check what we're filtering out
            print("\n" + "=" * 100)
            print("📊 Checking what's being filtered...")
            print("=" * 100)
            
            filtered_count = await page.evaluate("""
                (ignorePatterns) => {
                    function isIgnored(el) {
                        if (ignorePatterns.ids.includes(el.id)) return true;
                        const classes = el.className || '';
                        for (const pattern of ignorePatterns.class_names) {
                            if (classes.includes(pattern)) return true;
                        }
                        return false;
                    }
                    
                    const allImgs = document.querySelectorAll('img');
                    let filtered = 0;
                    allImgs.forEach(img => {
                        if (isIgnored(img)) filtered++;
                    });
                    return { total: allImgs.length, filtered: filtered };
                }
            """, ignore_list['ignore_patterns'])
            
            print(f"\nTotal images on page: {filtered_count['total']}")
            print(f"Filtered out as UI: {filtered_count['filtered']}")
            print(f"Remaining: {filtered_count['total'] - filtered_count['filtered']}")
        
        print("\n" + "=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
