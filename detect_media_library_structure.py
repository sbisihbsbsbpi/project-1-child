#!/usr/bin/env python3
"""
Detect Media Library Structure
Hover over logos and inspect the selection mechanism
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🔍 MEDIA LIBRARY STRUCTURE DETECTION")
    print("=" * 100)
    
    template_id = "667f0befd4964026ee7b6e48"
    url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    target_id = "983932ae-d79a-40fe-a9ba-df07c9beee47"
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            page = await context.new_page()
            
            print(f"🌐 Navigating to edit page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5)
            
            print(f"\n📍 Step 1: Focusing Logo 2 CENTER container...")
            target_selector = f'div.TEXT_TEMPLATE[id="{target_id}"][contenteditable="true"]'
            
            await page.wait_for_selector(target_selector, timeout=10000)
            target_element = page.locator(target_selector)
            await target_element.click()
            await asyncio.sleep(2)
            print(f"   ✅ Container focused!")
            
            print(f"\n📍 Step 2: Opening Insert Image modal...")
            insert_button_selector = '.icon-insert-image[aria-label="icon-insert-image"]'
            await page.click(insert_button_selector)
            await asyncio.sleep(3)
            print(f"   ✅ Modal opened!")
            
            print(f"\n📍 Step 3: Analyzing media library structure...")
            
            # Get complete structure
            structure = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { found: false, error: 'No popup found' };
                    
                    // Find all images
                    const images = Array.from(popup.querySelectorAll('img'));
                    
                    // Check for radio buttons
                    const radios = Array.from(popup.querySelectorAll('input[type="radio"]'));
                    
                    // Check for checkboxes
                    const checkboxes = Array.from(popup.querySelectorAll('input[type="checkbox"]'));
                    
                    // Analyze first few images and their containers
                    const imageInfo = images.slice(0, 5).map((img, idx) => {
                        const parent = img.parentElement;
                        const mediaTile = img.closest('[class*="mediaTile"]');
                        const hasRadio = mediaTile ? mediaTile.querySelector('input[type="radio"]') !== null : false;
                        const hasCheckbox = mediaTile ? mediaTile.querySelector('input[type="checkbox"]') !== null : false;
                        
                        return {
                            index: idx,
                            src: img.src.substring(0, 100),
                            parentTag: parent.tagName,
                            parentClass: parent.className,
                            mediaTileClass: mediaTile ? mediaTile.className : 'No mediaTile',
                            hasRadio: hasRadio,
                            hasCheckbox: hasCheckbox,
                            isSelected: mediaTile ? mediaTile.className.includes('itemChecked') : false
                        };
                    });
                    
                    return {
                        found: true,
                        totalImages: images.length,
                        totalRadios: radios.length,
                        totalCheckboxes: checkboxes.length,
                        imageInfo: imageInfo
                    };
                }
            """)
            
            print(f"\n📊 MEDIA LIBRARY STRUCTURE:")
            print(f"   Total Images: {structure.get('totalImages', 0)}")
            print(f"   Total Radio Buttons: {structure.get('totalRadios', 0)}")
            print(f"   Total Checkboxes: {structure.get('totalCheckboxes', 0)}")
            
            print(f"\n🖼️  FIRST 5 IMAGES:")
            for img in structure.get('imageInfo', []):
                print(f"\n   Image #{img['index']}:")
                print(f"      Parent: <{img['parentTag']} class=\"{img['parentClass'][:50]}...\">")
                print(f"      MediaTile: {img['mediaTileClass'][:50]}...")
                print(f"      Has Radio: {img['hasRadio']}")
                print(f"      Has Checkbox: {img['hasCheckbox']}")
                print(f"      Is Selected: {img['isSelected']}")
                print(f"      Src: {img['src'][:80]}...")
            
            # Now hover over first image and see what happens
            print(f"\n📍 Step 4: Hovering over first image to detect changes...")
            
            hover_result = await page.evaluate("""
                async () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    const images = Array.from(popup.querySelectorAll('img'));
                    const firstImg = images[0];
                    
                    if (!firstImg) return { error: 'No image found' };
                    
                    const mediaTile = firstImg.closest('[class*="mediaTile"]');
                    
                    // Capture state before hover
                    const beforeRadios = popup.querySelectorAll('input[type="radio"]').length;
                    const beforeChecks = popup.querySelectorAll('input[type="checkbox"]').length;
                    
                    // Hover
                    const mouseEvent = new MouseEvent('mouseover', { bubbles: true, cancelable: true });
                    mediaTile.dispatchEvent(mouseEvent);
                    
                    await new Promise(r => setTimeout(r, 1000));
                    
                    // Capture state after hover
                    const afterRadios = popup.querySelectorAll('input[type="radio"]').length;
                    const afterChecks = popup.querySelectorAll('input[type="checkbox"]').length;
                    
                    // Get full HTML of the mediaTile
                    const html = mediaTile ? mediaTile.outerHTML.substring(0, 2000) : '';
                    
                    return {
                        beforeRadios,
                        beforeChecks,
                        afterRadios,
                        afterChecks,
                        mediaTileHTML: html
                    };
                }
            """)
            
            print(f"\n📊 HOVER DETECTION RESULTS:")
            print(f"   Radios Before: {hover_result.get('beforeRadios', 0)}")
            print(f"   Radios After: {hover_result.get('afterRadios', 0)}")
            print(f"   Checkboxes Before: {hover_result.get('beforeChecks', 0)}")
            print(f"   Checkboxes After: {hover_result.get('afterChecks', 0)}")
            
            # Save results
            output_file = f"media_library_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump({'structure': structure, 'hover_result': hover_result}, f, indent=2)
            
            print(f"\n💾 Full results saved to: {output_file}")
            
            print(f"\n⏸️  Keeping browser open for inspection...")
            print(f"   Press Ctrl+C to close")
            
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n\n👋 Closing...")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
