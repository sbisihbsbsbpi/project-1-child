#!/usr/bin/env python3
"""
Test script to detect and analyze the Change Image popup
Just opens popup and shows what's in it
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("=" * 100)
    logger.info("🔍 COMPLETE FLOW: LIST → EDIT → POPUP → RADIO BUTTONS")
    logger.info("=" * 100)

    template_id = "667f0befd4964026ee7b6ea2"  # Service History Recap PDF

    async with async_playwright() as playwright:
        # Connect to existing browser
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]

        # ====================================================================
        # STEP 0: Start from Template List Page
        # ====================================================================
        logger.info("\n" + "=" * 100)
        logger.info("STEP 0: Starting from Template List Page")
        logger.info("=" * 100)

        pages = context.pages
        list_page = None

        # Check if template list is already open
        for existing_page in pages:
            if '/templates/list' in existing_page.url and '/edit/' not in existing_page.url:
                list_page = existing_page
                logger.info(f"✅ Found existing template list page")
                break

        if not list_page:
            logger.info("Opening template list page...")
            list_page = await context.new_page()
            await list_page.goto("https://preprodapp.tekioncloud.com/templates/list",
                               wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(3)
            logger.info(f"✅ Opened template list page")

        logger.info(f"Current URL: {list_page.url}")

        # ====================================================================
        # STEP 0b: Navigate to Specific Template (by ID)
        # ====================================================================
        logger.info("\n" + "=" * 100)
        logger.info("STEP 0b: Navigating to Specific Template")
        logger.info("=" * 100)

        # Check if template edit page is already open
        page = None
        for existing_page in pages:
            if template_id in existing_page.url:
                page = existing_page
                logger.info(f"✅ Found existing template edit page")
                break

        if not page:
            # Navigate to the template edit page from list
            edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
            logger.info(f"Navigating to template: {template_id}")
            logger.info(f"URL: {edit_url}")

            # Use the list page to navigate
            await list_page.goto(edit_url, wait_until='domcontentloaded', timeout=15000)
            page = list_page

            logger.info("⏳ Waiting for template to fully load (20 seconds)...")
            await asyncio.sleep(20)
            logger.info("✅ Template editor loaded")
        else:
            logger.info(f"Using existing template editor (no reload)")
        
        logger.info("\n" + "=" * 100)
        logger.info("STEP 1: Finding logo with warning")
        logger.info("=" * 100)
        
        # Find logo with warning
        container_found = await page.evaluate("""
            () => {
                const warningIcon = document.querySelector('.templates_Image_warningIcon__hCZHMuhEmb');
                if (!warningIcon) return false;
                
                const sortableItem = warningIcon.closest('[class*="SortableItem"]');
                if (sortableItem) {
                    sortableItem.setAttribute('data-logo-to-inspect', 'true');
                    return true;
                }
                return false;
            }
        """)
        
        if not container_found:
            logger.error("❌ No logo with warning found")
            return
        
        logger.info("✅ Found logo with warning")
        
        logger.info("\n" + "=" * 100)
        logger.info("STEP 2: Hovering to reveal toolbar")
        logger.info("=" * 100)
        
        container = await page.query_selector('[data-logo-to-inspect="true"]')
        await container.hover(force=True)
        await asyncio.sleep(3)  # Wait longer for toolbar animations
        logger.info("✅ Hovered and toolbar revealed")
        
        logger.info("\n" + "=" * 100)
        logger.info("STEP 3: Clicking CHANGE IMAGE icon (icon-switch) to open popup")
        logger.info("=" * 100)

        # Check if popup is already open
        popup_already_open = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                return popup && popup.getBoundingClientRect().width > 0;
            }
        """)

        if popup_already_open:
            logger.info("✅ Popup already open! Skipping click step.")
        else:
            # Click the "Change Image" icon (icon-switch with title="Change Image")
            logger.info("\n   Attempting to click Change Image icon...")
            change_clicked = await page.evaluate("""
                () => {
                    const container = document.querySelector('[data-logo-to-inspect="true"]');
                    if (!container) return { clicked: false, reason: 'No container' };

                    // Find Change Image icon (icon-switch)
                    const changeIcon = container.querySelector('[aria-label="icon-switch"]') ||
                                      container.querySelector('[title="Change Image"]');

                    if (changeIcon) {
                        changeIcon.click();
                        return { clicked: true, icon: 'icon-switch (Change Image)' };
                    }

                    return { clicked: false, reason: 'Change Image icon not found in toolbar' };
                }
            """)

            if change_clicked['clicked']:
                logger.info(f"✅ Change Image icon clicked!")
                await asyncio.sleep(3)  # Wait for popup to appear

                # Check if popup opened
                popup_opened = await page.evaluate("""
                    () => {
                        const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                        return popup && popup.getBoundingClientRect().width > 0;
                    }
                """)

                if popup_opened:
                    logger.info("✅ Popup opened after clicking Change Image icon!")
                else:
                    logger.warning("⚠️  No popup appeared after clicking Change Image icon")
                    return
            else:
                logger.error(f"❌ {change_clicked.get('reason', 'Unknown error')}")
                logger.info("\n💡 Tip: The Change Image icon only appears when hovering over the logo")
                logger.info("   If popup is already open in browser, the script will detect it and continue.")
                return

        await asyncio.sleep(1)
        
        logger.info("\n" + "=" * 100)
        logger.info("STEP 4: ANALYZING POPUP - DETECTING RADIO BUTTONS & LOGOS")
        logger.info("=" * 100)

        popup_info = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                if (!popup) return { found: false };

                // 🎯 STRATEGY 1: Find radio buttons (most reliable)
                const radios = Array.from(popup.querySelectorAll('input[type="radio"]'));

                const radioLogos = radios.map((radio, idx) => {
                    // Find the container for this radio
                    const container = radio.closest('div[class*="item"], label, div[role="button"], div[class*="card"], li');

                    // Find associated image
                    const img = container?.querySelector('img');
                    const src = img?.src || '';

                    // Extract media ID from URL
                    const mediaIdMatch = src.match(/media_([a-f0-9]{24})/);
                    const mediaId = mediaIdMatch ? mediaIdMatch[1] : 'unknown';

                    return {
                        index: idx,
                        isChecked: radio.checked,  // ✅ Source of truth
                        radioId: radio.id || 'no-id',
                        radioName: radio.name || 'no-name',
                        mediaId: mediaId,
                        src: src.substring(0, 150),
                        width: img?.width || 0,
                        height: img?.height || 0,
                        containerClasses: container?.className || 'no container',
                        hasImage: img !== null
                    };
                });

                // 🎯 STRATEGY 2: Find all images (fallback if no radios)
                const allImages = Array.from(popup.querySelectorAll('img'));

                const imageLogos = allImages.map((img, idx) => {
                    const src = img.src || '';

                    // Find closest media tile container (Tekion specific)
                    const parent = img.closest('[class*="mediaTile"]') ||
                                  img.closest('div[class*="item"]') ||
                                  img.closest('div[role="button"]') ||
                                  img.closest('div[class*="card"]') ||
                                  img.closest('li');

                    // Check if this logo is selected/active (Tekion specific: itemChecked class)
                    const isSelected = parent?.className?.includes('itemChecked') ||
                                      parent?.className?.includes('selected') ||
                                      parent?.className?.includes('active') ||
                                      parent?.getAttribute('aria-selected') === 'true' ||
                                      parent?.querySelector('[class*="check"]') !== null;

                    // Extract media ID from URL (handle both formats)
                    // Format 1: media_6a0c6722864813539e4da7ae_.png (with trailing underscore)
                    // Format 2: 6a19132b6697f36de6236fb1/Tilton.png (just the ID)
                    let mediaId = 'unknown';
                    const match1 = src.match(/([a-f0-9]{24})/);  // Any 24-char hex ID

                    if (match1) {
                        mediaId = match1[1];
                    }

                    return {
                        index: idx,
                        src: src.substring(0, 150),
                        mediaId: mediaId,
                        width: img.width,
                        height: img.height,
                        isSelected: isSelected,
                        parentClasses: parent?.className || 'no parent'
                    };
                });

                return {
                    found: true,
                    title: popup.querySelector('h2, h3, .ant-modal-title')?.innerText || 'No title',
                    hasRadioButtons: radios.length > 0,
                    radioCount: radios.length,
                    radioLogos: radioLogos,
                    imageCount: allImages.length,
                    imageLogos: imageLogos,
                    buttons: Array.from(popup.querySelectorAll('button')).map(b => b.innerText),
                    hasSearchBox: popup.querySelector('input[type="search"], input[placeholder*="search" i]') !== null
                };
            }
        """)

        if popup_info['found']:
            logger.info("✅ POPUP DETECTED!")
            logger.info(f"\n📋 POPUP DETAILS:")
            logger.info(f"   Title: {popup_info['title']}")
            logger.info(f"   Has Radio Buttons: {popup_info['hasRadioButtons']}")
            logger.info(f"   Radio Count: {popup_info['radioCount']}")
            logger.info(f"   Image Count: {popup_info['imageCount']}")
            logger.info(f"   Has Search Box: {popup_info['hasSearchBox']}")
            logger.info(f"   Buttons: {popup_info['buttons']}")

            # Display radio button information (PRIMARY SOURCE)
            if popup_info['hasRadioButtons']:
                logger.info(f"\n📻 RADIO BUTTON LOGOS (Source of Truth):")
                logger.info("=" * 80)

                for radio in popup_info['radioLogos']:
                    checked_emoji = "✅ CHECKED (Currently Selected)" if radio['isChecked'] else "⭕ Unchecked (Available)"
                    logger.info(f"\n   Radio #{radio['index'] + 1}: {checked_emoji}")
                    logger.info(f"      Has Image: {radio['hasImage']}")
                    if radio['hasImage']:
                        logger.info(f"      Media ID: {radio['mediaId']}")
                        logger.info(f"      Size: {radio['width']}x{radio['height']}px")
                        logger.info(f"      URL: {radio['src']}")
                    logger.info(f"      Radio ID: {radio['radioId']}")
                    logger.info(f"      Radio Name: {radio['radioName']}")
                    logger.info(f"      Container Classes: {radio['containerClasses'][:100]}")

                # Find available (unchecked) radios
                unchecked_radios = [r for r in popup_info['radioLogos'] if not r['isChecked']]
                checked_radios = [r for r in popup_info['radioLogos'] if r['isChecked']]

                logger.info(f"\n🎯 SELECTION STATUS:")
                logger.info(f"   Currently Selected (checked): {len(checked_radios)}")
                if checked_radios:
                    for radio in checked_radios:
                        logger.info(f"      ✅ Radio #{radio['index'] + 1} - Media ID: {radio['mediaId']}")

                logger.info(f"\n   Available (unchecked): {len(unchecked_radios)}")
                if unchecked_radios:
                    logger.info(f"   Recommended to select:")
                    for radio in unchecked_radios[:3]:  # Show first 3
                        if radio['hasImage']:
                            logger.info(f"      ⭕ Radio #{radio['index'] + 1} - Media ID: {radio['mediaId']} ({radio['width']}x{radio['height']}px)")
                        else:
                            logger.info(f"      ⭕ Radio #{radio['index'] + 1} - (No image associated)")

            # Display image information (FALLBACK)
            else:
                logger.info(f"\n🖼️  IMAGE LOGOS (Visual State Detection):")
                logger.info("=" * 80)
                logger.info("   ⚠️  No radio buttons found, using visual state detection")

                for logo in popup_info['imageLogos']:
                    selected_emoji = "✅ SELECTED" if logo['isSelected'] else "⭕ Available"
                    logger.info(f"\n   Logo #{logo['index'] + 1}: {selected_emoji}")
                    logger.info(f"      Media ID: {logo['mediaId']}")
                    logger.info(f"      Size: {logo['width']}x{logo['height']}px")
                    logger.info(f"      Selected: {logo['isSelected']}")
                    logger.info(f"      Parent Classes: {logo['parentClasses'][:100]}")
                    logger.info(f"      URL: {logo['src']}")

                # Find logos that are NOT selected (candidates for replacement)
                available_logos = [l for l in popup_info['imageLogos'] if not l['isSelected']]
                logger.info(f"\n🎯 AVAILABLE LOGOS (not selected):")
                logger.info(f"   Count: {len(available_logos)}")
                if available_logos:
                    logger.info(f"\n   Recommended to use:")
                    for logo in available_logos[:3]:  # Show first 3
                        logger.info(f"      - Media ID: {logo['mediaId']} ({logo['width']}x{logo['height']}px)")
        else:
            logger.error("❌ Popup not found")
        
        # Step 5: HOVER OVER TILES TO REVEAL HIDDEN ELEMENTS (Radio Buttons & Delete Icons)
        logger.info("\n" + "=" * 100)
        logger.info("STEP 5: HOVERING OVER TILES TO REVEAL RADIO BUTTONS & DELETE ICONS")
        logger.info("=" * 100)

        # First, get all tiles
        tiles_info = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                if (!popup) return { found: false, tiles: [] };

                const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));

                return {
                    found: true,
                    tileCount: tiles.length,
                    tiles: tiles.map((tile, idx) => ({
                        index: idx,
                        isSelected: tile.className.includes('itemChecked')
                    }))
                };
            }
        """)

        if not tiles_info['found']:
            logger.warning("⚠️  No media tiles found in popup")
        else:
            logger.info(f"✅ Found {tiles_info['tileCount']} media tiles")
            logger.info(f"   Hovering over each tile to detect hidden elements...")

            # Hover over each tile and detect what appears
            hover_results = []

            for tile_idx in range(tiles_info['tileCount']):
                logger.info(f"\n   🖱️  Hovering over tile #{tile_idx + 1}...")

                hover_detection = await page.evaluate(f"""
                    async () => {{
                        const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                        const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                        const tile = tiles[{tile_idx}];

                        if (!tile) return {{ found: false }};

                        // Get state BEFORE hover
                        const beforeRadios = tile.querySelectorAll('input[type="radio"]').length;
                        const beforeDelete = tile.querySelectorAll('[aria-label*="delete" i], [class*="delete" i], [title*="delete" i]').length;

                        // Trigger hover
                        tile.dispatchEvent(new MouseEvent('mouseenter', {{ bubbles: true }}));

                        // Wait for hover effects to appear
                        await new Promise(resolve => setTimeout(resolve, 300));

                        // Get state AFTER hover
                        const afterRadios = tile.querySelectorAll('input[type="radio"]');
                        const afterDelete = tile.querySelectorAll('[aria-label*="delete" i], [class*="delete" i], [title*="delete" i]');

                        // Get img info
                        const img = tile.querySelector('img');
                        const src = img?.src || '';
                        const mediaId = src.match(/([a-f0-9]{{24}})/)?.[1] || 'unknown';

                        // Get file name if visible
                        const fileName = tile.textContent.includes('.png') || tile.textContent.includes('.jpg') ?
                                        tile.textContent.match(/[^\\s]+\\.(png|jpg|jpeg|gif|svg)/i)?.[0] : null;

                        const result = {{
                            found: true,
                            tileIndex: {tile_idx},
                            mediaId: mediaId,
                            fileName: fileName,
                            isSelected: tile.className.includes('itemChecked'),
                            beforeHover: {{
                                radioButtons: beforeRadios,
                                deleteIcons: beforeDelete
                            }},
                            afterHover: {{
                                radioButtons: afterRadios.length,
                                deleteIcons: afterDelete.length,
                                radioDetails: Array.from(afterRadios).map(r => ({{
                                    checked: r.checked,
                                    id: r.id,
                                    name: r.name,
                                    value: r.value
                                }})),
                                deleteDetails: Array.from(afterDelete).map(d => ({{
                                    ariaLabel: d.getAttribute('aria-label'),
                                    className: d.className.substring(0, 50),
                                    tagName: d.tagName
                                }}))
                            }}
                        }};

                        // Keep hover active for inspection
                        return result;
                    }}
                """)

                if hover_detection['found']:
                    after = hover_detection['afterHover']

                    # Log what was found
                    logger.info(f"      Media ID: {hover_detection['mediaId']}")
                    if hover_detection['fileName']:
                        logger.info(f"      File Name: {hover_detection['fileName']}")

                    if after['radioButtons'] > 0:
                        logger.info(f"      ✅ Radio Button appeared! ({after['radioButtons']} found)")
                        for radio in after['radioDetails']:
                            checked_str = "🔴 CHECKED" if radio['checked'] else "⭕ UNCHECKED"
                            logger.info(f"         {checked_str} - ID: {radio['id']}")
                    else:
                        logger.info(f"      ❌ No radio button on hover")

                    if after['deleteIcons'] > 0:
                        logger.info(f"      🗑️  Delete Icon appeared! ({after['deleteIcons']} found)")
                        for delete_icon in after['deleteDetails']:
                            logger.info(f"         Tag: {delete_icon['tagName']}, Label: {delete_icon['ariaLabel']}")
                    else:
                        logger.info(f"      ❌ No delete icon on hover")

                    hover_results.append(hover_detection)

                # Small delay between hovers
                await asyncio.sleep(0.3)

            # Summary
            logger.info("\n" + "=" * 80)
            logger.info("📊 HOVER DETECTION SUMMARY")
            logger.info("=" * 80)

            tiles_with_radios = [r for r in hover_results if r['afterHover']['radioButtons'] > 0]
            tiles_with_delete = [r for r in hover_results if r['afterHover']['deleteIcons'] > 0]

            logger.info(f"\n   Total tiles hovered: {len(hover_results)}")
            logger.info(f"   Tiles with radio buttons: {len(tiles_with_radios)}")
            logger.info(f"   Tiles with delete icons: {len(tiles_with_delete)}")

        # Step 5b: SKIP HIGHLIGHTING (will highlight only radio buttons after selection change)
        logger.info("\n" + "=" * 100)
        logger.info("STEP 5b: SKIPPING LOGO HIGHLIGHTING (will highlight only radio buttons later)")
        logger.info("=" * 100)
        logger.info("   ℹ️  Logos will NOT be highlighted - only radio buttons and Insert button")

        # Step 6: DETECT INSERT BUTTON (BEFORE radio change)
        logger.info("\n" + "=" * 100)
        logger.info("STEP 6: DETECTING INSERT BUTTON (BEFORE Selection Change)")
        logger.info("=" * 100)

        insert_before = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                if (!popup) return { found: false };

                const buttons = Array.from(popup.querySelectorAll('button'));
                const insertBtn = buttons.find(b =>
                    b.textContent.trim().toLowerCase().includes('insert') ||
                    b.textContent.trim().toLowerCase().includes('update') ||
                    b.textContent.trim().toLowerCase().includes('save')
                );

                if (!insertBtn) return { found: false };

                return {
                    found: true,
                    text: insertBtn.textContent.trim(),
                    disabled: insertBtn.disabled,
                    className: insertBtn.className
                };
            }
        """)

        if insert_before['found']:
            logger.info(f"✅ Insert button found!")
            logger.info(f"   Text: {insert_before['text']}")
            logger.info(f"   Disabled: {insert_before['disabled']}")
            logger.info(f"   State: {'🔴 DISABLED' if insert_before['disabled'] else '🟢 ENABLED'}")
        else:
            logger.warning("⚠️  Insert button not found in popup")

        # Step 7: CHANGE SELECTION BY CLICKING A DIFFERENT TILE
        logger.info("\n" + "=" * 100)
        logger.info("STEP 7: CHANGING SELECTION (CLICKING DIFFERENT TILE)")
        logger.info("=" * 100)

        # Click on a different media tile to change selection
        radio_change_result = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                if (!popup) return { changed: false, reason: 'Popup not found' };

                const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                if (tiles.length === 0) return { changed: false, reason: 'No media tiles found' };

                // Find currently selected tile
                const selectedTile = tiles.find(t => t.className.includes('itemChecked'));
                const selectedIndex = tiles.indexOf(selectedTile);

                // Find first unselected tile (skip broken logo)
                const targetTile = tiles.find(t => {
                    if (t.className.includes('itemChecked')) return false;

                    const img = t.querySelector('img');
                    const src = img?.src || '';
                    const mediaId = src.match(/([a-f0-9]{24})/)?.[1];

                    // Skip known broken logo
                    return mediaId !== '6a0c6722864813539e4da7ae';
                });

                if (!targetTile) {
                    return { changed: false, reason: 'No alternative tile found' };
                }

                const targetIndex = tiles.indexOf(targetTile);

                // Get media ID of target
                const targetImg = targetTile.querySelector('img');
                const targetSrc = targetImg?.src || '';
                const targetMediaId = targetSrc.match(/([a-f0-9]{24})/)?.[1] || 'unknown';

                // Click the target tile
                targetTile.click();

                // Wait for state to update
                return new Promise(resolve => {
                    setTimeout(() => {
                        resolve({
                            changed: true,
                            previousIndex: selectedIndex,
                            newIndex: targetIndex,
                            newMediaId: targetMediaId,
                            totalTiles: tiles.length
                        });
                    }, 500);
                });
            }
        """)

        if radio_change_result['changed']:
            logger.info(f"✅ Selection changed successfully!")
            logger.info(f"   Total tiles: {radio_change_result['totalTiles']}")
            logger.info(f"   Previous tile: #{radio_change_result.get('previousIndex', -1) + 1}")
            logger.info(f"   New tile: #{radio_change_result['newIndex'] + 1}")
            logger.info(f"   New Media ID: {radio_change_result['newMediaId']}")

            await asyncio.sleep(1.5)  # Wait for UI to update

            # Step 8: HIGHLIGHT RADIO BUTTONS & INSERT BUTTON
            logger.info("\n" + "=" * 100)
            logger.info("STEP 8a: HIGHLIGHTING RADIO BUTTONS (if visible)")
            logger.info("=" * 100)

            # Highlight radio buttons
            radio_highlight = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { found: false };

                    const radios = Array.from(popup.querySelectorAll('input[type="radio"]'));
                    if (radios.length === 0) return { found: false, reason: 'No radio buttons visible' };

                    radios.forEach(radio => {
                        const container = radio.closest('div, label, li');
                        if (container) {
                            if (radio.checked) {
                                // RED for selected
                                container.style.outline = '5px solid red';
                                container.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
                                container.style.boxShadow = '0 0 20px rgba(255, 0, 0, 0.8)';
                            } else {
                                // GREEN for available
                                container.style.outline = '3px solid green';
                                container.style.backgroundColor = 'rgba(0, 255, 0, 0.2)';
                            }
                        }
                    });

                    return {
                        found: true,
                        count: radios.length,
                        checked: radios.filter(r => r.checked).length
                    };
                }
            """)

            if radio_highlight['found']:
                logger.info(f"✅ Radio buttons highlighted!")
                logger.info(f"   Total radios: {radio_highlight['count']}")
                logger.info(f"   Selected (RED): {radio_highlight['checked']}")
                logger.info(f"   Available (GREEN): {radio_highlight['count'] - radio_highlight['checked']}")
            else:
                logger.info(f"⚠️  No radio buttons to highlight: {radio_highlight.get('reason', 'unknown')}")

            # Step 8b: DETECT & HIGHLIGHT INSERT BUTTON (AFTER selection change)
            logger.info("\n" + "=" * 100)
            logger.info("STEP 8b: DETECTING & HIGHLIGHTING INSERT BUTTON")
            logger.info("\n" + "=" * 100)
            logger.info("STEP 8: DETECTING INSERT BUTTON (AFTER Selection Change)")
            logger.info("=" * 100)

            insert_after = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { found: false };

                    const buttons = Array.from(popup.querySelectorAll('button'));
                    const insertBtn = buttons.find(b =>
                        b.textContent.trim().toLowerCase().includes('insert') ||
                        b.textContent.trim().toLowerCase().includes('update') ||
                        b.textContent.trim().toLowerCase().includes('save')
                    );

                    if (!insertBtn) return { found: false };

                    // Highlight the Insert button
                    insertBtn.style.outline = '5px solid yellow';
                    insertBtn.style.backgroundColor = 'rgba(255, 255, 0, 0.4)';
                    insertBtn.style.boxShadow = '0 0 20px rgba(255, 255, 0, 0.8)';

                    return {
                        found: true,
                        text: insertBtn.textContent.trim(),
                        disabled: insertBtn.disabled,
                        className: insertBtn.className
                    };
                }
            """)

            if insert_after['found']:
                logger.info(f"✅ Insert button detected after change!")
                logger.info(f"   Text: {insert_after['text']}")
                logger.info(f"   Disabled: {insert_after['disabled']}")
                logger.info(f"   State: {'🔴 DISABLED' if insert_after['disabled'] else '🟢 ENABLED'}")
                logger.info(f"   💛 Button highlighted in YELLOW")

                # Compare states
                logger.info("\n" + "=" * 100)
                logger.info("📊 INSERT BUTTON STATE COMPARISON")
                logger.info("=" * 100)

                logger.info(f"\n   BEFORE radio change:")
                logger.info(f"      Disabled: {insert_before.get('disabled', 'N/A')}")

                logger.info(f"\n   AFTER radio change:")
                logger.info(f"      Disabled: {insert_after['disabled']}")

                if insert_before.get('disabled') != insert_after['disabled']:
                    logger.info(f"\n   🎯 STATE CHANGED!")
                    if not insert_after['disabled']:
                        logger.info(f"      ✅ Button is now ENABLED - Ready to insert!")
                    else:
                        logger.info(f"      ❌ Button became DISABLED")
                else:
                    logger.info(f"\n   ℹ️  Button state remained the same")

                # Step 9: CLICK INSERT BUTTON
                logger.info("\n" + "=" * 100)
                logger.info("STEP 9: CLICKING INSERT BUTTON")
                logger.info("=" * 100)

                if not insert_after['disabled']:
                    logger.info("🖱️  Clicking Insert button...")

                    click_result = await page.evaluate("""
                        () => {
                            const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                            if (!popup) return { clicked: false, reason: 'No popup found' };

                            const buttons = Array.from(popup.querySelectorAll('button'));
                            const insertBtn = buttons.find(b =>
                                b.textContent.trim().toLowerCase().includes('insert') ||
                                b.textContent.trim().toLowerCase().includes('update') ||
                                b.textContent.trim().toLowerCase().includes('save')
                            );

                            if (!insertBtn) return { clicked: false, reason: 'Insert button not found' };
                            if (insertBtn.disabled) return { clicked: false, reason: 'Button is disabled' };

                            insertBtn.click();
                            return {
                                clicked: true,
                                buttonText: insertBtn.textContent.trim()
                            };
                        }
                    """)

                    if click_result['clicked']:
                        logger.info(f"✅ Insert button clicked: '{click_result['buttonText']}'")

                        # Wait for popup to close
                        await asyncio.sleep(2)

                        # Check if popup closed
                        popup_closed = await page.evaluate("""
                            () => {
                                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                                return !popup || popup.getBoundingClientRect().width === 0;
                            }
                        """)

                        if popup_closed:
                            logger.info("✅ Popup closed successfully")
                            logger.info("✅ Logo replacement complete!")
                        else:
                            logger.warning("⚠️  Popup still open after clicking Insert")
                    else:
                        logger.error(f"❌ Failed to click Insert button: {click_result.get('reason')}")
                else:
                    logger.warning("⚠️  Insert button is DISABLED - cannot click")
                    logger.info("   Will pause for manual inspection instead")
            else:
                logger.warning("⚠️  Insert button not found after change")
        else:
            logger.warning(f"⚠️  Could not change selection: {radio_change_result.get('reason', 'Unknown')}")

        logger.info("\n" + "=" * 100)
        logger.info("⏸️  PAUSED FOR VISUAL INSPECTION")
        logger.info("=" * 100)
        logger.info("\n📋 Color Legend:")
        logger.info("   🔴 RED    = Currently selected / checked radio button")
        logger.info("   🟢 GREEN  = Available to select")
        logger.info("   🟠 ORANGE = Broken logo (should avoid)")
        logger.info("   💛 YELLOW = Insert/Update button (highlighted after radio change)")
        logger.info("\n✋ Script paused. Check the browser to see highlighted elements.")
        logger.info("   Press Ctrl+C when done inspecting...")

        # Keep browser open for inspection
        try:
            await asyncio.sleep(3600)  # Wait 1 hour or until Ctrl+C
        except KeyboardInterrupt:
            logger.info("\n\n✅ Inspection complete. Exiting...")

        logger.info("\n" + "=" * 100)
        logger.info("✅ TEST COMPLETE - Popup analyzed and alternative logo selected")
        logger.info("=" * 100)
        logger.info("\n✅ Analysis complete. Browser remains open for inspection.")

if __name__ == "__main__":
    asyncio.run(main())
