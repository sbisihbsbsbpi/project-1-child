#!/usr/bin/env python3
"""
Find the ACTUAL logo image in the template content (not UI elements)
Using the existing Tekion tab
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
        
        print("🔍 Searching for ACTUAL logo in template content...")
        print("   (Ignoring UI elements)")
        print("=" * 100)
        
        # Load ignore list
        with open('logo_ignore_list.json') as f:
            ignore_list = json.load(f)
        
        # Search for logo images
        logo_results = await page.evaluate("""
            (ignorePatterns) => {
                const results = [];
                
                // Helper function to check if element should be ignored
                function isIgnored(el) {
                    // Check ID
                    if (ignorePatterns.ids.includes(el.id)) {
                        return true;
                    }
                    
                    // Check class names
                    const classes = el.className || '';
                    for (const pattern of ignorePatterns.class_names) {
                        if (classes.includes(pattern)) {
                            return true;
                        }
                    }
                    
                    // Check if inside ignored parent
                    for (const parentSelector of ignorePatterns.parent_selectors) {
                        if (el.closest(parentSelector)) {
                            return true;
                        }
                    }
                    
                    return false;
                }
                
                // Find all images
                const allImages = document.querySelectorAll('img');
                
                allImages.forEach((img, idx) => {
                    // Skip if ignored
                    if (isIgnored(img)) {
                        return;
                    }
                    
                    const src = img.src || '';
                    const alt = img.alt || '';
                    const className = img.className || '';
                    const rect = img.getBoundingClientRect();
                    
                    // Look for logos (nucar, tilton, or dealership-related)
                    const isLogo = src.toLowerCase().includes('logo') ||
                                   src.toLowerCase().includes('nucar') ||
                                   src.toLowerCase().includes('tilton') ||
                                   alt.toLowerCase().includes('logo') ||
                                   alt.toLowerCase().includes('dealer');
                    
                    if (isLogo || rect.width > 0) {
                        results.push({
                            index: idx,
                            src: src.substring(0, 200),
                            alt: alt,
                            className: className.substring(0, 100),
                            width: rect.width,
                            height: rect.height,
                            top: rect.top,
                            left: rect.left,
                            visible: img.offsetParent !== null,
                            isLogo: isLogo,
                            parent: img.parentElement?.tagName || 'N/A',
                            parentClass: img.parentElement?.className?.substring(0, 80) || '',
                            parentId: img.parentElement?.id || ''
                        });
                    }
                });
                
                return results;
            }
        """, ignore_list['ignore_patterns'])
        
        print(f"\n✅ Found {len(logo_results)} images in template content:\n")
        
        template_logos = []
        other_images = []
        
        for img in logo_results:
            if img['isLogo']:
                template_logos.append(img)
            else:
                other_images.append(img)
        
        # Show logos first
        if template_logos:
            print("🎯 LOGO IMAGES (likely candidates for replacement):")
            print("=" * 100)
            for i, img in enumerate(template_logos, 1):
                visible = "✅ VISIBLE" if img['visible'] else "❌ HIDDEN"
                print(f"\n{i}. {visible}")
                print(f"   Src: {img['src']}")
                print(f"   Alt: {img['alt']}")
                print(f"   Size: {img['width']:.0f}x{img['height']:.0f} px")
                print(f"   Position: top={img['top']:.0f}px, left={img['left']:.0f}px")
                print(f"   Parent: <{img['parent']}> id=\"{img['parentId']}\" class=\"{img['parentClass']}\"")
                print(f"   Class: {img['className']}")
        else:
            print("⚠️  No logo images found in template content!")
        
        # Show other images
        if other_images:
            print(f"\n\n📷 OTHER IMAGES ({len(other_images)} found):")
            print("=" * 100)
            for i, img in enumerate(other_images[:5], 1):  # Show first 5
                visible = "✅" if img['visible'] else "❌"
                print(f"\n{i}. {visible} {img['width']:.0f}x{img['height']:.0f}px - {img['parent']}")
                print(f"   {img['src'][:100]}")
        
        print("\n" + "=" * 100)
        print("💡 TIP: The actual logo to replace will be in the template editor/preview area")
        print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
