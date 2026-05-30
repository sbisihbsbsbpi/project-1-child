#!/usr/bin/env python3
"""
Find logo in template - check iframes and template preview areas
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
        
        print("🔍 Searching for template preview area and iframes...")
        print("=" * 100)
        
        # First, check for iframes
        iframe_info = await page.evaluate("""
            () => {
                const iframes = document.querySelectorAll('iframe');
                return Array.from(iframes).map((iframe, idx) => ({
                    index: idx,
                    src: iframe.src?.substring(0, 150) || '',
                    id: iframe.id || '',
                    className: iframe.className || '',
                    width: iframe.getBoundingClientRect().width,
                    height: iframe.getBoundingClientRect().height,
                    visible: iframe.offsetParent !== null
                }));
            }
        """)
        
        print(f"\n📦 Found {len(iframe_info)} iframes:\n")
        
        for i, iframe_data in enumerate(iframe_info, 1):
            visible = "✅ VISIBLE" if iframe_data['visible'] else "❌ HIDDEN"
            print(f"{i}. {visible}")
            print(f"   ID: {iframe_data['id']}")
            print(f"   Class: {iframe_data['className']}")
            print(f"   Size: {iframe_data['width']:.0f}x{iframe_data['height']:.0f} px")
            print(f"   Src: {iframe_data['src']}")
            print()
        
        # Search for template preview/editor containers
        print("=" * 100)
        print("🎨 Searching for template editor/preview containers...")
        print("=" * 100)
        
        editor_containers = await page.evaluate("""
            () => {
                const results = [];
                const allDivs = document.querySelectorAll('div');
                
                allDivs.forEach(div => {
                    const id = div.id || '';
                    const className = div.className || '';
                    
                    // Look for preview, editor, canvas, template containers
                    if (id.toLowerCase().includes('preview') ||
                        id.toLowerCase().includes('editor') ||
                        id.toLowerCase().includes('canvas') ||
                        id.toLowerCase().includes('template') ||
                        (typeof className === 'string' && (
                            className.includes('preview') ||
                            className.includes('editor') ||
                            className.includes('canvas') ||
                            className.includes('template')
                        ))) {
                        
                        const rect = div.getBoundingClientRect();
                        
                        if (rect.width > 300 && rect.height > 200) {  // Substantial size
                            results.push({
                                id: id,
                                className: typeof className === 'string' ? className.substring(0, 80) : '',
                                width: rect.width,
                                height: rect.height,
                                top: rect.top,
                                left: rect.left,
                                visible: div.offsetParent !== null,
                                childCount: div.children.length
                            });
                        }
                    }
                });
                
                return results;
            }
        """)
        
        print(f"\n✅ Found {len(editor_containers)} potential editor/preview containers:\n")
        
        for i, container in enumerate(editor_containers[:10], 1):
            visible = "✅ VISIBLE" if container['visible'] else "❌ HIDDEN"
            print(f"{i}. {visible}")
            print(f"   ID: {container['id']}")
            print(f"   Class: {container['className']}")
            print(f"   Size: {container['width']:.0f}x{container['height']:.0f} px")
            print(f"   Position: top={container['top']:.0f}px, left={container['left']:.0f}px")
            print(f"   Children: {container['childCount']}")
            print()
        
        # Check inside iframes for images
        print("=" * 100)
        print("🔍 Checking inside iframes for logo images...")
        print("=" * 100)
        
        frames = page.frames
        print(f"\nTotal frames: {len(frames)}")
        
        for idx, frame in enumerate(frames):
            print(f"\nFrame {idx}: {frame.url[:100]}")
            
            try:
                # Search for images in this frame
                images = await frame.evaluate("""
                    () => {
                        const imgs = document.querySelectorAll('img');
                        return Array.from(imgs).map(img => ({
                            src: img.src?.substring(0, 150) || '',
                            alt: img.alt || '',
                            className: img.className || '',
                            width: img.getBoundingClientRect().width,
                            height: img.getBoundingClientRect().height
                        }));
                    }
                """)
                
                if images:
                    print(f"  Found {len(images)} images in this frame:")
                    for i, img in enumerate(images[:3], 1):
                        print(f"    {i}. {img['width']:.0f}x{img['height']:.0f}px - {img['src'][:80]}")
            except Exception as e:
                print(f"  ⚠️  Could not access frame: {e}")
        
        print("\n" + "=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
