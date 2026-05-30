#!/usr/bin/env python3
"""
Visual Analysis: Find ALL elements in the template by looking at what's actually rendered
Goal: Manually update logos, so we need to see what the user sees
"""

import asyncio
import json
from playwright.async_api import async_playwright
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page


async def main():
    template_id = '667f0befd4964026ee7b6ea4'
    
    print("=" * 100)
    print("🔍 VISUAL TEMPLATE ANALYSIS - WHAT THE USER SEES")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        
        # Navigate to template
        url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        page = await get_or_navigate_to_page(browser, url, wait_for_load=True)
        
        print("✅ Template editor loaded")
        await asyncio.sleep(3)  # Wait for editor to fully render
        print()
        
        # ========================================
        # SCAN 1: ALL IMAGES (including in editor)
        # ========================================
        print("=" * 100)
        print("📸 SCAN 1: ALL IMAGES IN THE PAGE")
        print("=" * 100)
        print()
        
        all_images = await page.evaluate("""
            () => {
                const images = Array.from(document.querySelectorAll('img'));
                
                return images.map((img, idx) => {
                    const rect = img.getBoundingClientRect();
                    const src = img.src || '';
                    const alt = img.alt || '';
                    
                    // Extract media ID
                    const mediaIdMatch = src.match(/([a-f0-9]{24})/);
                    const mediaId = mediaIdMatch ? mediaIdMatch[1] : null;
                    
                    // Get parent info
                    const parent = img.parentElement;
                    const parentClass = parent ? parent.className : '';
                    const parentTag = parent ? parent.tagName : '';
                    
                    return {
                        index: idx,
                        mediaId: mediaId,
                        src: src.substring(0, 80),
                        alt: alt,
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        visible: rect.width > 0 && rect.height > 0,
                        parentTag: parentTag,
                        parentClass: parentClass.substring(0, 50)
                    };
                }).filter(img => img.visible);
            }
        """)
        
        print(f"Total Visible Images: {len(all_images)}")
        print()
        
        for i, img in enumerate(all_images, 1):
            print(f"{i}. Image:")
            print(f"   📏 Size: {img['width']}x{img['height']}")
            print(f"   📍 Position: top={img['top']}px, left={img['left']}px")
            print(f"   🆔 Media ID: {img['mediaId'] or '❌ NONE'}")
            print(f"   🏷️  Alt: {img['alt'] or '(empty)'}")
            print(f"   📦 Parent: <{img['parentTag']}> class=\"{img['parentClass']}\"")
            print(f"   🔗 Src: {img['src']}...")
            print()
        
        # ========================================
        # SCAN 2: EDITOR CONTENT AREA
        # ========================================
        print("=" * 100)
        print("✏️  SCAN 2: EDITOR CONTENT AREA (Where user edits)")
        print("=" * 100)
        print()
        
        editor_scan = await page.evaluate("""
            () => {
                // Find the editor container (where template components are)
                const editorSelectors = [
                    '[contenteditable="true"]',
                    '[class*="editor"]',
                    '[class*="canvas"]',
                    '[class*="content"]',
                    'iframe'
                ];
                
                let editorElement = null;
                let selectorUsed = null;
                
                for (const selector of editorSelectors) {
                    const el = document.querySelector(selector);
                    if (el) {
                        editorElement = el;
                        selectorUsed = selector;
                        break;
                    }
                }
                
                if (!editorElement) {
                    return { found: false };
                }
                
                // Get all elements in editor
                const allElements = Array.from(editorElement.querySelectorAll('*'));
                
                return {
                    found: true,
                    selector: selectorUsed,
                    totalElements: allElements.length,
                    images: Array.from(editorElement.querySelectorAll('img')).map(img => ({
                        src: img.src.substring(0, 80),
                        alt: img.alt,
                        width: Math.round(img.getBoundingClientRect().width),
                        height: Math.round(img.getBoundingClientRect().height)
                    })),
                    buttons: Array.from(editorElement.querySelectorAll('button, a[href]')).length,
                    textBlocks: Array.from(editorElement.querySelectorAll('p, div, span')).length
                };
            }
        """)
        
        if editor_scan.get('found'):
            print(f"✅ Found editor: {editor_scan['selector']}")
            print(f"   Total elements: {editor_scan['totalElements']}")
            print(f"   Images: {len(editor_scan.get('images', []))}")
            print(f"   Buttons/Links: {editor_scan.get('buttons', 0)}")
            print(f"   Text blocks: {editor_scan.get('textBlocks', 0)}")
            print()
            
            if editor_scan.get('images'):
                print("   Images in editor:")
                for i, img in enumerate(editor_scan['images'], 1):
                    print(f"      {i}. {img['width']}x{img['height']} - {img['alt'] or '(no alt)'}")
                print()
        else:
            print("❌ Could not find editor content area")
            print()
        
        # ========================================
        # SCAN 3: TAKE SCREENSHOT
        # ========================================
        print("=" * 100)
        print("📷 SCAN 3: TAKING SCREENSHOT")
        print("=" * 100)
        print()
        
        screenshot_path = f"template_screenshot_{template_id}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"✅ Screenshot saved: {screenshot_path}")
        print()
        
        # ========================================
        # SCAN 4: COMPONENT STRUCTURE FROM JSON
        # ========================================
        print("=" * 100)
        print("📦 SCAN 4: TEMPLATE COMPONENTS FROM JSON")
        print("=" * 100)
        print()
        
        # Load the body JSON we saved earlier
        with open('template_body_full.json', 'r') as f:
            body = json.load(f)
        
        print(f"Total Components: {len(body)}")
        print()
        
        logo_count = 0
        for i, comp in enumerate(body, 1):
            comp_key = comp.get('key')
            props = comp.get('componentProps', {})
            
            print(f"{i}. {comp_key}")
            
            # Check if it's a logo
            if comp_key == 'INSERT_IMAGE':
                media_id = props.get('selectedImage', {}).get('mediaId')
                if media_id:
                    logo_count += 1
                    print(f"   🎨 LOGO DETECTED!")
                    print(f"   Media ID: {media_id}")
                    print(f"   Width: {props.get('imageDimensions', {}).get('width', 'auto')}")
                    print(f"   → THIS IS LOGO #{logo_count}")
            
            elif comp_key == 'INSERT_BUTTON':
                print(f"   🔘 Button")
            
            elif comp_key == 'TEXT_TEMPLATE':
                html = props.get('html', '')
                text_preview = html[:80].replace('<', '&lt;').replace('>', '&gt;')
                print(f"   📝 Text: {text_preview}...")
            
            elif 'FOOTER' in comp_key:
                print(f"   👣 Footer component")
            
            print()
        
        # ========================================
        # SUMMARY
        # ========================================
        print("=" * 100)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 100)
        print()
        print(f"Total Components in Template: {len(body)}")
        print(f"Logos Found in Components: {logo_count}")
        print(f"Total Visible Images on Page: {len(all_images)}")
        print()
        print("Logo Locations:")
        print("  1. thumbnail.mediaId field (API)")
        print(f"  2. Component #2 (INSERT_IMAGE) - Visual position: TOP of email")
        print()


if __name__ == "__main__":
    asyncio.run(main())
