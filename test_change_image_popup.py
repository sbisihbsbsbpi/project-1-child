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
    logger.info("🔍 TESTING CHANGE IMAGE POPUP - DETECT & ANALYZE")
    logger.info("=" * 100)
    
    template_id = "667f0befd4964026ee7b6ea2"  # Service History Recap PDF
    url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    
    async with async_playwright() as playwright:
        # Connect to existing browser
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]

        # Get or create page
        pages = context.pages
        page = None
        for existing_page in pages:
            if template_id in existing_page.url:
                page = existing_page
                logger.info(f"✅ Found existing template page")
                break

        if not page:
            logger.info(f"Opening template: {url}")
            page = await context.new_page()
            await page.goto(url)
            await asyncio.sleep(20)  # Wait for load
        else:
            logger.info(f"Using existing template page (no reload)")
        
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

                return { clicked: false, reason: 'Change Image icon not found' };
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
            logger.error(f"❌ Change Image icon not found: {change_clicked.get('reason', 'Unknown')}")
            logger.info("\n📝 Change Image icon only appears on hover. Make sure logo is hovered.")
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
        
        # Step 5: Select an alternative logo
        logger.info("\n" + "=" * 100)
        logger.info("STEP 5: SELECTING ALTERNATIVE LOGO (Avoiding broken logos)")
        logger.info("=" * 100)

        # Known broken logo ID
        BROKEN_LOGO_ID = "6a0c6722864813539e4da7ae"
        GOOD_LOGO_ID = "6a19132b6697f36de6236fb1"  # Tilton.png

        # Find the good logo (not broken)
        available_logos = [l for l in popup_info.get('imageLogos', [])
                          if l['mediaId'] != 'unknown' and l['mediaId'] != BROKEN_LOGO_ID]

        if available_logos:
            # Prefer the known good logo
            target_logo = next((l for l in available_logos if l['mediaId'] == GOOD_LOGO_ID), available_logos[0])

            logger.info(f"\n🎯 Target logo to select:")
            logger.info(f"   Media ID: {target_logo['mediaId']}")
            logger.info(f"   Size: {target_logo['width']}x{target_logo['height']}px")
            logger.info(f"   Currently Selected: {target_logo['isSelected']}")
            logger.info(f"   URL: {target_logo['src']}")

            # Click the logo to select it
            selection_result = await page.evaluate(f"""
                () => {{
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return {{ success: false, reason: 'Popup not found' }};

                    // Find all images
                    const allImages = Array.from(popup.querySelectorAll('img'));
                    const targetImg = allImages[{target_logo['index']}];

                    if (!targetImg) return {{ success: false, reason: 'Target image not found' }};

                    // Find clickable container (media tile)
                    const container = targetImg.closest('[class*="mediaTile"]') || targetImg.parentElement;

                    if (!container) return {{ success: false, reason: 'Container not found' }};

                    // Click the container to select it
                    container.click();

                    return {{
                        success: true,
                        mediaId: '{target_logo['mediaId']}',
                        clicked: 'media tile container'
                    }};
                }}
            """)

            if selection_result['success']:
                logger.info(f"\n✅ Logo clicked!")
                logger.info(f"   Clicked: {selection_result['clicked']}")
                logger.info(f"   Media ID: {selection_result['mediaId']}")

                await asyncio.sleep(1)

                # Now click Insert button
                logger.info(f"\n📤 Clicking Insert button...")
                insert_clicked = await page.evaluate("""
                    () => {
                        const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                        if (!popup) return { success: false, reason: 'Popup not found' };

                        // Find Insert button
                        const buttons = Array.from(popup.querySelectorAll('button'));
                        const insertBtn = buttons.find(b => b.innerText === 'Insert');

                        if (!insertBtn) return { success: false, reason: 'Insert button not found' };

                        insertBtn.click();
                        return { success: true };
                    }
                """)

                if insert_clicked['success']:
                    logger.info(f"✅ Insert button clicked!")
                    await asyncio.sleep(2)
                    logger.info(f"\n🎉 Logo replacement complete!")
                else:
                    logger.error(f"❌ Failed to click Insert: {insert_clicked.get('reason', 'Unknown')}")
            else:
                logger.error(f"\n❌ Failed to select logo: {selection_result.get('reason', 'Unknown')}")
        else:
            logger.warning("\n⚠️  No alternative logos found (all are either unknown or broken)")

        logger.info("\n" + "=" * 100)
        logger.info("✅ TEST COMPLETE - Popup analyzed and alternative logo selected")
        logger.info("=" * 100)
        logger.info("\n✅ Analysis complete. Browser remains open for inspection.")

if __name__ == "__main__":
    asyncio.run(main())
