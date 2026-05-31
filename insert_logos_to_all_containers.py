#!/usr/bin/env python3
"""
Automated Logo Insertion to ALL Logo Containers
- Logo 1: LEFT, CENTER, RIGHT
- Logo 2: LEFT, CENTER, RIGHT
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


# All 6 logo container IDs
LOGO_CONTAINERS = [
    # Logo 1
    {"name": "Logo 1 LEFT", "id": "6f0b8570-c4dc-45bd-b746-40e3af9af3bb", "alignment": "left"},
    {"name": "Logo 1 CENTER", "id": "7653caa9-31b7-4e2b-8233-f0bda43672ea", "alignment": "center"},
    {"name": "Logo 1 RIGHT", "id": "47da3c0a-2c2b-4f8f-8a31-4ba8fdae03aa", "alignment": "right"},
    
    # Logo 2
    {"name": "Logo 2 LEFT", "id": "9fa2920b-10f8-48d2-9947-b014398d21be", "alignment": "left"},
    {"name": "Logo 2 CENTER", "id": "983932ae-d79a-40fe-a9ba-df07c9beee47", "alignment": "center"},
    {"name": "Logo 2 RIGHT", "id": "9d454086-c1f2-4bf0-b4a7-8e95dc244aae", "alignment": "right"},
]


async def insert_logo_to_container(page, container_info, logo_index=0):
    """Insert a logo into a specific container"""
    
    container_name = container_info['name']
    container_id = container_info['id']
    
    print(f"\n{'='*100}")
    print(f"📍 INSERTING LOGO INTO: {container_name}")
    print(f"{'='*100}")
    print(f"   Container ID: {container_id}")
    print(f"   Alignment: {container_info['alignment']}")
    
    try:
        # Step 1: Focus the container
        print(f"\n📍 Step 1: Focusing container...")
        target_selector = f'div.TEXT_TEMPLATE[id="{container_id}"][contenteditable="true"]'
        
        try:
            await page.wait_for_selector(target_selector, timeout=5000)
            target_element = page.locator(target_selector)
            await target_element.click()
            await asyncio.sleep(1.5)
            print(f"   ✅ Container focused!")
        except Exception as e:
            print(f"   ❌ Container not found: {e}")
            return {"success": False, "error": "Container not found"}
        
        # Step 2: Click Insert Image button
        print(f"\n📍 Step 2: Clicking Insert Image button...")
        insert_button_selector = '.icon-insert-image[aria-label="icon-insert-image"]'
        
        try:
            await page.click(insert_button_selector, timeout=5000)
            await asyncio.sleep(2.5)
            print(f"   ✅ Insert Image button clicked!")
        except Exception as e:
            print(f"   ❌ Insert Image button not found: {e}")
            return {"success": False, "error": "Insert button not found"}
        
        # Step 3: Wait for media library modal
        print(f"\n📍 Step 3: Waiting for media library modal...")
        
        modal_found = False
        modal_selectors = ['[class*="modal"]', '[role="dialog"]']
        
        for selector in modal_selectors:
            try:
                await page.wait_for_selector(selector, timeout=3000)
                modal_found = True
                print(f"   ✅ Media library modal opened!")
                break
            except:
                continue
        
        if not modal_found:
            print(f"   ❌ Modal did not appear!")
            return {"success": False, "error": "Modal not found"}
        
        await asyncio.sleep(1.5)
        
        # Step 4: Select logo using topLayer button
        print(f"\n📍 Step 4: Selecting logo #{logo_index}...")
        
        selection_result = await page.evaluate(f"""
            async () => {{
                const sleep = ms => new Promise(r => setTimeout(r, ms));
                
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                if (!popup) return {{ clicked: false, error: 'Popup not found' }};
                
                const allTiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                
                // Find logo tiles (not upload button)
                const logoTiles = allTiles.filter(tile => {{
                    const img = tile.querySelector('img');
                    return img && !img.src.startsWith('data:image/svg');
                }});
                
                if (logoTiles.length === 0) return {{ clicked: false, error: 'No logo tiles found' }};
                
                // Select the specified logo (default to first)
                const logoIndex = Math.min({logo_index}, logoTiles.length - 1);
                const targetTile = logoTiles[logoIndex];
                const img = targetTile.querySelector('img');
                
                // WORKING PATTERN: Find and click the topLayer button
                const topLayer = targetTile.querySelector('[role="button"]') ||
                                targetTile.querySelector('[class*="topLayer"]');
                
                if (topLayer) {{
                    // Click the topLayer button
                    topLayer.click();
                    
                    // Visual confirmation
                    img.style.outline = '5px solid lime';
                    targetTile.style.outline = '3px solid yellow';
                    if (topLayer !== targetTile) {{
                        topLayer.style.outline = '2px dashed orange';
                    }}
                    
                    await sleep(500);
                    
                    return {{
                        clicked: true,
                        isSelected: targetTile.className.includes('itemChecked'),
                        logoIndex: logoIndex,
                        src: img.src.substring(0, 80)
                    }};
                }} else {{
                    return {{ clicked: false, error: 'No topLayer button found' }};
                }}
            }}
        """)
        
        if not selection_result.get('clicked'):
            error = selection_result.get('error', 'Unknown error')
            print(f"   ❌ Failed to select logo: {error}")
            return {"success": False, "error": error}
        
        print(f"   ✅ Logo #{selection_result.get('logoIndex')} selected!")
        print(f"      Selected: {selection_result.get('isSelected')}")
        print(f"      Src: {selection_result.get('src')}...")

        # Step 5: Click Insert button
        print(f"\n📍 Step 5: Clicking Insert button...")

        button_texts = ['Insert', 'Select', 'Confirm', 'Add']
        confirm_button = None

        for btn_text in button_texts:
            try:
                confirm_button = page.locator(f'button:has-text("{btn_text}")').first
                if await confirm_button.is_visible(timeout=1000):
                    print(f"   ✅ Found '{btn_text}' button!")
                    break
                else:
                    confirm_button = None
            except:
                continue

        if not confirm_button:
            print(f"   ❌ Insert button not found!")
            return {"success": False, "error": "Insert button not found"}

        await confirm_button.click()
        await asyncio.sleep(2)
        print(f"   ✅ Logo inserted successfully!")

        print(f"\n{'='*100}")
        print(f"✅ SUCCESS - {container_name} COMPLETE!")
        print(f"{'='*100}")

        return {"success": True, "container": container_name}

    except Exception as e:
        print(f"\n❌ Error inserting logo: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def main():
    print("=" * 100)
    print("🎯 AUTOMATED LOGO INSERTION - ALL CONTAINERS")
    print("=" * 100)
    print(f"   Total Containers: {len(LOGO_CONTAINERS)}")
    print(f"   Logo 1: LEFT, CENTER, RIGHT")
    print(f"   Logo 2: LEFT, CENTER, RIGHT")
    print("=" * 100)

    template_id = "667f0befd4964026ee7b6e48"
    url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"

    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("\n✅ Connected to browser")

            context = browser.contexts[0]
            page = await context.new_page()

            print(f"\n🌐 Navigating to edit page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5)
            print(f"✅ Page loaded!")

            # Track results
            results = []
            successful = 0
            failed = 0

            # Insert logo into each container
            for i, container in enumerate(LOGO_CONTAINERS, 1):
                print(f"\n\n{'#'*100}")
                print(f"# CONTAINER {i}/{len(LOGO_CONTAINERS)}")
                print(f"{'#'*100}")

                result = await insert_logo_to_container(page, container, logo_index=0)
                results.append({
                    "container": container['name'],
                    "result": result
                })

                if result.get('success'):
                    successful += 1
                else:
                    failed += 1

                # Wait between insertions
                await asyncio.sleep(2)

            # Summary
            print(f"\n\n{'='*100}")
            print(f"📊 FINAL SUMMARY")
            print(f"{'='*100}")
            print(f"   Total Containers: {len(LOGO_CONTAINERS)}")
            print(f"   ✅ Successful: {successful}")
            print(f"   ❌ Failed: {failed}")
            print(f"\n{'='*100}")
            print(f"DETAILED RESULTS:")
            print(f"{'='*100}")

            for r in results:
                status = "✅" if r['result'].get('success') else "❌"
                error = f" - {r['result'].get('error')}" if not r['result'].get('success') else ""
                print(f"   {status} {r['container']}{error}")

            # Take screenshot
            screenshot_path = f"all_logos_inserted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"\n📸 Screenshot saved: {screenshot_path}")

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

