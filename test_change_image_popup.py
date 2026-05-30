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
        
        # Step 5: HIGHLIGHT radio buttons or selection items (VISUAL INSPECTION)
        logger.info("\n" + "=" * 100)
        logger.info("STEP 5: HIGHLIGHTING SELECTION ELEMENTS FOR VISUAL INSPECTION")
        logger.info("=" * 100)

        # Highlight all selectable elements
        highlight_result = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                if (!popup) return { found: false };

                // Check for radio buttons first
                const radios = Array.from(popup.querySelectorAll('input[type="radio"]'));

                if (radios.length > 0) {
                    // Highlight radio buttons
                    radios.forEach((radio, idx) => {
                        const container = radio.closest('div, label, li');
                        if (container) {
                            if (radio.checked) {
                                container.style.outline = '5px solid red';
                                container.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
                            } else {
                                container.style.outline = '5px solid green';
                                container.style.backgroundColor = 'rgba(0, 255, 0, 0.2)';
                            }
                        }
                    });

                    return {
                        found: true,
                        type: 'radio buttons',
                        count: radios.length,
                        checked: radios.filter(r => r.checked).length
                    };
                } else {
                    // Highlight media tiles (visual selection)
                    const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));

                    tiles.forEach((tile, idx) => {
                        const isSelected = tile.className.includes('itemChecked');
                        const img = tile.querySelector('img');
                        const src = img?.src || '';

                        // Extract media ID
                        const mediaId = src.match(/([a-f0-9]{24})/)?.[1] || 'unknown';

                        // Color code: Red = selected, Green = available, Yellow = broken logo
                        const isBroken = mediaId === '6a0c6722864813539e4da7ae';

                        if (isSelected) {
                            tile.style.outline = '5px solid red';
                            tile.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
                        } else if (isBroken) {
                            tile.style.outline = '5px solid orange';
                            tile.style.backgroundColor = 'rgba(255, 165, 0, 0.2)';
                        } else {
                            tile.style.outline = '5px solid green';
                            tile.style.backgroundColor = 'rgba(0, 255, 0, 0.2)';
                        }

                        // Add label
                        const label = document.createElement('div');
                        label.style.position = 'absolute';
                        label.style.top = '5px';
                        label.style.left = '5px';
                        label.style.background = 'black';
                        label.style.color = 'white';
                        label.style.padding = '5px';
                        label.style.fontSize = '12px';
                        label.style.fontWeight = 'bold';
                        label.style.zIndex = '9999';

                        if (isSelected) {
                            label.innerText = `SELECTED (${idx + 1})`;
                        } else if (isBroken) {
                            label.innerText = `BROKEN (${idx + 1})`;
                        } else {
                            label.innerText = `AVAILABLE (${idx + 1})`;
                        }

                        tile.style.position = 'relative';
                        tile.appendChild(label);
                    });

                    return {
                        found: true,
                        type: 'visual selection (media tiles)',
                        count: tiles.length,
                        selected: tiles.filter(t => t.className.includes('itemChecked')).length
                    };
                }
            }
        """)

        logger.info(f"\n🎨 Highlighting complete!")
        logger.info(f"   Type: {highlight_result.get('type', 'unknown')}")
        logger.info(f"   Total items: {highlight_result.get('count', 0)}")

        if highlight_result.get('type') == 'radio buttons':
            logger.info(f"   Checked (RED): {highlight_result.get('checked', 0)}")
            logger.info(f"   Unchecked (GREEN): {highlight_result.get('count', 0) - highlight_result.get('checked', 0)}")
        else:
            logger.info(f"   Selected (RED): {highlight_result.get('selected', 0)}")
            logger.info(f"   Available (GREEN): Items not selected or broken")
            logger.info(f"   Broken (ORANGE): Known broken logo")

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

        # Step 7: CHANGE RADIO BUTTON SELECTION
        logger.info("\n" + "=" * 100)
        logger.info("STEP 7: CHANGING RADIO BUTTON SELECTION")
        logger.info("=" * 100)

        # Get current radio state and select a different one
        radio_change_result = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                if (!popup) return { changed: false, reason: 'Popup not found' };

                const radios = Array.from(popup.querySelectorAll('input[type="radio"]'));
                if (radios.length === 0) return { changed: false, reason: 'No radio buttons found' };

                // Find currently checked radio
                const checkedRadio = radios.find(r => r.checked);
                const checkedIndex = radios.indexOf(checkedRadio);

                // Find first unchecked radio
                const uncheckedRadio = radios.find(r => !r.checked);

                if (!uncheckedRadio) {
                    return { changed: false, reason: 'No unchecked radio buttons available' };
                }

                const uncheckedIndex = radios.indexOf(uncheckedRadio);

                // Click the unchecked radio
                uncheckedRadio.click();

                // Wait a bit for state to update
                return new Promise(resolve => {
                    setTimeout(() => {
                        resolve({
                            changed: true,
                            previousIndex: checkedIndex,
                            newIndex: uncheckedIndex,
                            nowChecked: uncheckedRadio.checked
                        });
                    }, 500);
                });
            }
        """)

        if radio_change_result['changed']:
            logger.info(f"✅ Radio selection changed!")
            logger.info(f"   Previous: Radio #{radio_change_result.get('previousIndex', 'N/A')}")
            logger.info(f"   New: Radio #{radio_change_result['newIndex']}")
            logger.info(f"   Confirmed checked: {radio_change_result['nowChecked']}")

            await asyncio.sleep(1)  # Wait for UI to update

            # Step 8: DETECT INSERT BUTTON (AFTER radio change)
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
            else:
                logger.warning("⚠️  Insert button not found after change")
        else:
            logger.warning(f"⚠️  Could not change radio selection: {radio_change_result.get('reason', 'Unknown')}")

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
