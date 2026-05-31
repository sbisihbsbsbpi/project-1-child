#!/usr/bin/env python3
"""
Detect All Logos in Media Library with Hover
- Hover over each logo
- Get filename
- Detect radio buttons
- Show selection mechanism
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
    print("🔍 MEDIA LIBRARY - HOVER OVER ALL LOGOS AND DETECT SELECTION")
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
            
            print(f"\n📍 Step 3: Detecting all logos with hover...")
            
            # Hover over each logo and detect
            logos_info = await page.evaluate("""
                async () => {
                    const sleep = ms => new Promise(r => setTimeout(r, ms));
                    
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { found: false, error: 'No popup found' };
                    
                    const allTiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    
                    // Find logo tiles (not upload button)
                    const logoTiles = allTiles.filter(tile => {
                        const img = tile.querySelector('img');
                        return img && !img.src.startsWith('data:image/svg');
                    });
                    
                    const logosInfo = [];
                    
                    // Hover over each logo
                    for (let i = 0; i < logoTiles.length; i++) {
                        const tile = logoTiles[i];
                        const img = tile.querySelector('img');
                        
                        // Extract filename from URL
                        const src = img.src;
                        const urlParts = src.split('/');
                        const filename = urlParts[urlParts.length - 1];
                        
                        // Count radio buttons before hover
                        const radiosBefore = popup.querySelectorAll('input[type="radio"]').length;
                        
                        // HOVER
                        const mouseOverEvent = new MouseEvent('mouseover', { 
                            bubbles: true, 
                            cancelable: true,
                            view: window
                        });
                        tile.dispatchEvent(mouseOverEvent);
                        
                        // Highlight with different color for each
                        const colors = ['red', 'blue', 'green', 'orange', 'purple'];
                        tile.style.outline = `5px solid ${colors[i % colors.length]}`;
                        
                        await sleep(800);
                        
                        // Count radio buttons after hover
                        const radiosAfter = popup.querySelectorAll('input[type="radio"]').length;
                        
                        // Check for radio button in this tile
                        const tileRadio = tile.querySelector('input[type="radio"]');
                        
                        // Check for the topLayer button
                        const topLayerButton = tile.querySelector('[class*="mediaTile_topLayer"][role="button"]');
                        
                        // Check if selected
                        const isSelected = tile.className.includes('itemChecked') || 
                                          tile.className.includes('selected');
                        
                        logosInfo.push({
                            index: i,
                            filename: filename,
                            src: src,
                            radiosBefore: radiosBefore,
                            radiosAfter: radiosAfter,
                            hasRadioInTile: tileRadio !== null,
                            radioValue: tileRadio ? tileRadio.value : null,
                            radioChecked: tileRadio ? tileRadio.checked : null,
                            hasTopLayerButton: topLayerButton !== null,
                            isSelected: isSelected,
                            tileClassName: tile.className
                        });
                        
                        await sleep(500);
                    }
                    
                    // Get all radios in popup
                    const allRadios = Array.from(popup.querySelectorAll('input[type="radio"]'));
                    const radiosInfo = allRadios.map((r, idx) => ({
                        index: idx,
                        name: r.name || '',
                        value: r.value || '',
                        checked: r.checked,
                        parentClass: r.parentElement ? r.parentElement.className : ''
                    }));
                    
                    return {
                        found: true,
                        totalLogos: logoTiles.length,
                        logos: logosInfo,
                        allRadios: radiosInfo
                    };
                }
            """)
            
            print(f"\n📊 LOGO DETECTION RESULTS:")
            print(f"   Total Logos: {logos_info.get('totalLogos', 0)}")
            print(f"   Total Radio Buttons: {len(logos_info.get('allRadios', []))}")
            
            print(f"\n🖼️  LOGO DETAILS:")
            for logo in logos_info.get('logos', []):
                print(f"\n   Logo #{logo['index']} - {logo['filename']}")
                print(f"      Has Radio in Tile: {logo['hasRadioInTile']}")
                if logo['hasRadioInTile']:
                    print(f"      Radio Value: {logo['radioValue']}")
                    print(f"      Radio Checked: {logo['radioChecked']}")
                print(f"      Has Top Layer Button: {logo['hasTopLayerButton']}")
                print(f"      Is Selected: {logo['isSelected']}")
                print(f"      Radios Before Hover: {logo['radiosBefore']}")
                print(f"      Radios After Hover: {logo['radiosAfter']}")
            
            if logos_info.get('allRadios'):
                print(f"\n📻 ALL RADIO BUTTONS IN POPUP:")
                for radio in logos_info['allRadios']:
                    checked = "☑" if radio['checked'] else "☐"
                    print(f"   {checked} Radio [{radio['index']}] name={radio['name']} value={radio['value'][:30]}...")
            
            # Save results
            output_file = f"all_logos_hover_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(logos_info, f, indent=2)
            
            print(f"\n💾 Full results saved to: {output_file}")
            
            print(f"\n⏸️  Keeping browser open - you should see colored outlines on each logo!")
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
