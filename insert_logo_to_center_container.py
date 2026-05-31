#!/usr/bin/env python3
"""
Automated Logo Insertion to Logo 2 CENTER Container
1. Click on Logo 2 CENTER container (983932ae-d79a-40fe-a9ba-df07c9beee47)
2. Click Insert Image button
3. Select a logo from media library
4. Insert the logo
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🎯 AUTOMATED LOGO INSERTION - Logo 2 CENTER Container")
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
            
            print(f"\n📍 Step 1: Locating Logo 2 CENTER container...")
            print(f"   Target ID: {target_id}")
            
            # Find the contenteditable element
            target_selector = f'div.TEXT_TEMPLATE[id="{target_id}"][contenteditable="true"]'
            
            # Wait for element to be visible
            try:
                await page.wait_for_selector(target_selector, timeout=10000)
                print(f"   ✅ Logo 2 CENTER container found!")
            except Exception as e:
                print(f"   ❌ Container not found: {e}")
                return
            
            # Click on the container to focus it
            print(f"\n📍 Step 2: Clicking on Logo 2 CENTER container to focus it...")
            target_element = page.locator(target_selector)
            await target_element.click()
            await asyncio.sleep(2)
            print(f"   ✅ Container focused!")
            
            # Find and click the Insert Image button
            print(f"\n📍 Step 3: Finding Insert Image button...")
            
            # Try multiple selectors for the insert image button
            insert_button_selectors = [
                '.icon-insert-image[aria-label="icon-insert-image"]',
                'div.icon-insert-image',
                '[class*="icon-insert-image"]'
            ]
            
            insert_button = None
            for selector in insert_button_selectors:
                try:
                    buttons = await page.query_selector_all(selector)
                    if buttons:
                        # Find visible button
                        for btn in buttons:
                            if await btn.is_visible():
                                insert_button = btn
                                print(f"   ✅ Insert Image button found with selector: {selector}")
                                break
                        if insert_button:
                            break
                except:
                    continue
            
            if not insert_button:
                print(f"   ❌ Insert Image button not found!")
                print(f"   💡 Trying alternative approach - looking for toolbar buttons...")
                
                # Wait a bit for toolbar to appear
                await asyncio.sleep(2)
                
                # Try to find any insert-related button in the toolbar
                all_buttons = await page.query_selector_all('div[role="img"]')
                print(f"   Found {len(all_buttons)} potential buttons")
                
                for i, btn in enumerate(all_buttons):
                    try:
                        aria_label = await btn.get_attribute('aria-label')
                        if aria_label and 'insert' in aria_label.lower():
                            print(f"   Found button with aria-label: {aria_label}")
                            insert_button = btn
                            break
                    except:
                        continue
            
            if insert_button:
                print(f"\n📍 Step 4: Clicking Insert Image button...")
                await insert_button.click()
                await asyncio.sleep(3)
                print(f"   ✅ Insert Image button clicked!")
                
                # Wait for media library modal to appear
                print(f"\n📍 Step 5: Waiting for media library modal...")
                
                # Look for the media library modal
                modal_selectors = [
                    '[class*="modal"]',
                    '[class*="Modal"]',
                    '[role="dialog"]',
                    '[class*="mediaTile"]'
                ]
                
                modal_found = False
                for selector in modal_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        modal_found = True
                        print(f"   ✅ Media library modal appeared! (selector: {selector})")
                        break
                    except:
                        continue
                
                if modal_found:
                    await asyncio.sleep(2)

                    print(f"\n📍 Step 6: Looking for logo images in media library...")

                    # The media library doesn't use radio buttons - it uses clickable mediaTile containers
                    media_result = await page.evaluate("""
                        () => {
                            const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                            if (!popup) return { found: false, error: 'Popup not found' };

                            // Find all mediaTile containers (these are the actual logo tiles, excluding upload button)
                            const allTiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                            const logoTiles = allTiles.filter(tile => {
                                const img = tile.querySelector('img');
                                // Filter out upload SVG buttons (they use data:image/svg)
                                return img && !img.src.startsWith('data:image/svg');
                            });

                            return {
                                found: true,
                                totalTiles: allTiles.length,
                                logoTiles: logoTiles.length,
                                tiles: logoTiles.map((tile, idx) => {
                                    const img = tile.querySelector('img');
                                    return {
                                        index: idx,
                                        className: tile.className,
                                        isSelected: tile.className.includes('itemChecked'),
                                        imgSrc: img ? img.src.substring(0, 100) : 'No image'
                                    };
                                })
                            };
                        }
                    """)

                    if media_result.get('found'):
                        print(f"   ✅ Found {media_result['logoTiles']} logo tiles!")

                        # Show all logo tiles
                        for tile in media_result['tiles'][:5]:  # Show first 5
                            selected = "✓" if tile['isSelected'] else "○"
                            print(f"      {selected} Tile [{tile['index']}]: {tile['imgSrc'][:60]}...")

                        if media_result['logoTiles'] > 0:
                            print(f"\n📍 Step 7: Hovering over and clicking first logo tile...")

                            # Hover then click the first logo tile (like we did with the X delete button)
                            selection_result = await page.evaluate("""
                                async () => {
                                    const sleep = ms => new Promise(r => setTimeout(r, ms));

                                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                                    const allTiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));

                                    // Find logo tiles (not upload button)
                                    const logoTiles = allTiles.filter(tile => {
                                        const img = tile.querySelector('img');
                                        return img && !img.src.startsWith('data:image/svg');
                                    });

                                    if (logoTiles.length > 0) {
                                        const firstTile = logoTiles[0];

                                        // HOVER over the tile first
                                        const mouseOverEvent = new MouseEvent('mouseover', {
                                            bubbles: true,
                                            cancelable: true,
                                            view: window
                                        });
                                        firstTile.dispatchEvent(mouseOverEvent);

                                        const mouseEnterEvent = new MouseEvent('mouseenter', {
                                            bubbles: true,
                                            cancelable: true,
                                            view: window
                                        });
                                        firstTile.dispatchEvent(mouseEnterEvent);

                                        // Add visual highlight for debugging
                                        firstTile.style.outline = '4px solid yellow';

                                        // Wait for hover effects to appear
                                        await sleep(1000);

                                        // Now CLICK the tile
                                        firstTile.click();

                                        // Dispatch click event too
                                        const clickEvent = new MouseEvent('click', {
                                            bubbles: true,
                                            cancelable: true,
                                            view: window
                                        });
                                        firstTile.dispatchEvent(clickEvent);

                                        // Wait a bit and check if it's selected
                                        await sleep(500);

                                        return {
                                            clicked: true,
                                            isNowSelected: firstTile.className.includes('itemChecked')
                                        };
                                    }
                                    return { clicked: false };
                                }
                            """)

                            if selection_result.get('clicked'):
                                print(f"   ✅ Logo tile clicked! (Selected: {selection_result.get('isNowSelected')})")
                            else:
                                print(f"   ❌ Failed to click logo tile!")
                        else:
                            print(f"   ❌ No logo tiles found!")
                    else:
                        print(f"   ❌ Could not find media tiles!")

                    await asyncio.sleep(2)

                    # Look for Insert/Select/Confirm button
                    print(f"\n📍 Step 8: Looking for Insert/Confirm button...")

                    button_texts = ['Insert', 'Select', 'Confirm', 'Add', 'OK', 'Choose']
                    confirm_button = None

                    for btn_text in button_texts:
                        try:
                            # Try to find button by text
                            confirm_button = page.locator(f'button:has-text("{btn_text}")').first
                            if await confirm_button.is_visible(timeout=1000):
                                print(f"   ✅ Found '{btn_text}' button!")
                                break
                            else:
                                confirm_button = None
                        except:
                            continue

                    if confirm_button:
                        print(f"\n📍 Step 9: Clicking Insert/Confirm button...")
                        await confirm_button.click()
                        await asyncio.sleep(2)
                        print(f"   ✅ Logo inserted successfully!")

                        print("\n" + "=" * 100)
                        print("🎉 SUCCESS - LOGO INSERTION COMPLETE!")
                        print("=" * 100)
                        print(f"\n✅ Logo has been inserted into Logo 2 CENTER container")
                        print(f"✅ Container ID: {target_id}")
                        print(f"✅ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        print("\n💡 Check the template editor to see the inserted logo!")
                    else:
                        print(f"   ⚠️  Could not find Insert/Confirm button")
                        print(f"   💡 The logo may still be selected - check the modal")
                else:
                    print(f"   ❌ Media library modal did not appear!")
                    print(f"   💡 The insert image button might not have worked")
            else:
                print(f"   ❌ Could not find Insert Image button!")
                print(f"   💡 Possible reasons:")
                print(f"      - Button not visible")
                print(f"      - Need to click on container first")
                print(f"      - Button in a different location")

            # Take screenshot for debugging
            screenshot_path = f"logo_insertion_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"\n📸 Screenshot saved: {screenshot_path}")

            print(f"\n⏸️  Keeping browser open for inspection...")
            print(f"   Press Ctrl+C to close")

            # Keep running to inspect
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

