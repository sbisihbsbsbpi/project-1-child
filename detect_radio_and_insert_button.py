#!/usr/bin/env python3
"""
Detect Radio Buttons & Insert Button State After Selection Change
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
    logger.info("🎯 RADIO BUTTON DETECTION & INSERT BUTTON TRACKING")
    logger.info("=" * 100)
    
    template_id = "667f0befd4964026ee7b6ea2"  # Service History Recap PDF
    url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    
    async with async_playwright() as playwright:
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
            await asyncio.sleep(20)
        else:
            logger.info(f"Using existing template page")
        
        # STEP 1: Find logo and open popup
        logger.info("\n" + "=" * 100)
        logger.info("STEP 1: Opening Change Image Popup")
        logger.info("=" * 100)
        
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
        
        # Check if popup is already open
        popup_already_open = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                return popup && popup.getBoundingClientRect().width > 0;
            }
        """)

        if popup_already_open:
            logger.info("✅ Popup already open, skipping hover and click")
        else:
            # Hover and click Change Image
            logger.info("Hovering over logo to reveal toolbar...")
            container = await page.query_selector('[data-logo-to-inspect="true"]')
            await container.hover(force=True)
            await asyncio.sleep(3)  # Wait longer for toolbar
        
        change_clicked = await page.evaluate("""
            () => {
                const container = document.querySelector('[data-logo-to-inspect="true"]');
                const changeIcon = container?.querySelector('[aria-label="icon-switch"]') ||
                                  container?.querySelector('[title="Change Image"]');
                if (changeIcon) {
                    changeIcon.click();
                    return true;
                }
                return false;
            }
        """)
        
        if not change_clicked:
            logger.error("❌ Change Image icon not found")
            return
        
        logger.info("✅ Clicked Change Image icon")
        await asyncio.sleep(3)
        
        # STEP 2: Detect all radio buttons
        logger.info("\n" + "=" * 100)
        logger.info("STEP 2: Detecting Radio Buttons")
        logger.info("=" * 100)
        
        radio_info = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                if (!popup) return { found: false };
                
                const radios = Array.from(popup.querySelectorAll('input[type="radio"]'));
                
                return {
                    found: true,
                    radios: radios.map((radio, idx) => {
                        const container = radio.closest('div, label, li');
                        const img = container?.querySelector('img');
                        const src = img?.src || '';
                        const mediaId = src.match(/([a-f0-9]{24})/)?.[1] || 'unknown';
                        
                        return {
                            index: idx,
                            isChecked: radio.checked,
                            mediaId: mediaId,
                            radioId: radio.id || `radio-${idx}`,
                            hasImage: img !== null,
                            width: img?.width || 0,
                            height: img?.height || 0
                        };
                    })
                };
            }
        """)
        
        if not radio_info['found']:
            logger.error("❌ Popup not found")
            return
        
        logger.info(f"\n✅ Found {len(radio_info['radios'])} radio buttons")
        
        for radio in radio_info['radios']:
            status = "🔴 CHECKED" if radio['isChecked'] else "⭕ UNCHECKED"
            logger.info(f"   Radio #{radio['index']}: {status} - Media: {radio['mediaId']}")
        
        # STEP 3: Highlight radio buttons
        logger.info("\n" + "=" * 100)
        logger.info("STEP 3: Highlighting Radio Buttons")
        logger.info("=" * 100)
        
        await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                const radios = Array.from(popup.querySelectorAll('input[type="radio"]'));
                
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
                        container.style.position = 'relative';
                        
                        // Add number badge
                        const badge = document.createElement('div');
                        badge.style.cssText = `
                            position: absolute; top: 5px; right: 5px;
                            background: black; color: white; padding: 5px 10px;
                            font-size: 14px; font-weight: bold; border-radius: 50%;
                            z-index: 9999;
                        `;
                        badge.textContent = idx + 1;
                        container.appendChild(badge);
                    }
                });
            }
        """)

        logger.info("✅ Radio buttons highlighted!")
        logger.info("\n🎨 Color Legend:")
        logger.info("   🔴 RED    = Currently selected")
        logger.info("   🟢 GREEN  = Available to select")

        # STEP 4: Check Insert button BEFORE selection change
        logger.info("\n" + "=" * 100)
        logger.info("STEP 4: Checking Insert Button State (BEFORE change)")
        logger.info("=" * 100)

        insert_before = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                const buttons = Array.from(popup.querySelectorAll('button'));

                const insertBtn = buttons.find(b =>
                    b.textContent.trim().toLowerCase().includes('insert') ||
                    b.textContent.trim().toLowerCase().includes('update') ||
                    b.textContent.trim().toLowerCase().includes('save')
                );

                return {
                    found: insertBtn !== undefined,
                    text: insertBtn?.textContent.trim() || 'N/A',
                    disabled: insertBtn?.disabled || false,
                    className: insertBtn?.className || 'N/A'
                };
            }
        """)

        logger.info(f"   Insert Button Found: {insert_before['found']}")
        logger.info(f"   Button Text: {insert_before['text']}")
        logger.info(f"   Disabled: {insert_before['disabled']}")

        # STEP 5: Change radio button selection
        logger.info("\n" + "=" * 100)
        logger.info("STEP 5: Changing Radio Selection")
        logger.info("=" * 100)

        # Find first unchecked radio
        unchecked = [r for r in radio_info['radios'] if not r['isChecked']]

        if not unchecked:
            logger.warning("⚠️  All radios are unchecked or only one exists")
        else:
            target_radio = unchecked[0]
            logger.info(f"   Selecting Radio #{target_radio['index']} (Media: {target_radio['mediaId']})")

            # Click the radio button
            selection_result = await page.evaluate(f"""
                () => {{
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    const radios = Array.from(popup.querySelectorAll('input[type="radio"]'));
                    const targetRadio = radios[{target_radio['index']}];

                    if (targetRadio) {{
                        targetRadio.click();
                        return {{
                            clicked: true,
                            nowChecked: targetRadio.checked
                        }};
                    }}
                    return {{ clicked: false }};
                }}
            """)

            if selection_result['clicked']:
                logger.info(f"   ✅ Clicked radio #{target_radio['index']}")
                logger.info(f"   Radio is now checked: {selection_result['nowChecked']}")
                await asyncio.sleep(1)

                # STEP 6: Check Insert button AFTER selection change
                logger.info("\n" + "=" * 100)
                logger.info("STEP 6: Checking Insert Button State (AFTER change)")
                logger.info("=" * 100)

                insert_after = await page.evaluate("""
                    () => {
                        const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                        const buttons = Array.from(popup.querySelectorAll('button'));

                        const insertBtn = buttons.find(b =>
                            b.textContent.trim().toLowerCase().includes('insert') ||
                            b.textContent.trim().toLowerCase().includes('update') ||
                            b.textContent.trim().toLowerCase().includes('save')
                        );

                        return {
                            found: insertBtn !== undefined,
                            text: insertBtn?.textContent.trim() || 'N/A',
                            disabled: insertBtn?.disabled || false,
                            className: insertBtn?.className || 'N/A'
                        };
                    }
                """)

                logger.info(f"   Insert Button Found: {insert_after['found']}")
                logger.info(f"   Button Text: {insert_after['text']}")
                logger.info(f"   Disabled: {insert_after['disabled']}")

                # STEP 7: Compare button states
                logger.info("\n" + "=" * 100)
                logger.info("STEP 7: Insert Button State Comparison")
                logger.info("=" * 100)

                logger.info(f"\n   BEFORE Selection Change:")
                logger.info(f"      Text: {insert_before['text']}")
                logger.info(f"      Disabled: {insert_before['disabled']}")

                logger.info(f"\n   AFTER Selection Change:")
                logger.info(f"      Text: {insert_after['text']}")
                logger.info(f"      Disabled: {insert_after['disabled']}")

                if insert_before['disabled'] != insert_after['disabled']:
                    logger.info(f"\n   🎯 STATE CHANGED!")
                    if not insert_after['disabled']:
                        logger.info(f"      ✅ Button is now ENABLED - Ready to insert!")
                    else:
                        logger.info(f"      ❌ Button is now DISABLED")
                else:
                    logger.info(f"\n   ℹ️  Button state did not change")

                # Highlight the Insert button
                await page.evaluate("""
                    () => {
                        const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                        const buttons = Array.from(popup.querySelectorAll('button'));
                        const insertBtn = buttons.find(b =>
                            b.textContent.trim().toLowerCase().includes('insert') ||
                            b.textContent.trim().toLowerCase().includes('update') ||
                            b.textContent.trim().toLowerCase().includes('save')
                        );

                        if (insertBtn) {
                            insertBtn.style.outline = '5px solid yellow';
                            insertBtn.style.backgroundColor = 'rgba(255, 255, 0, 0.3)';
                        }
                    }
                """)

                logger.info("\n   💛 Insert button highlighted in YELLOW")
            else:
                logger.error("   ❌ Failed to click radio button")

        logger.info("\n" + "=" * 100)
        logger.info("⏸️  PAUSED FOR INSPECTION")
        logger.info("=" * 100)
        logger.info("\n   Check browser to see:")
        logger.info("   - 🔴 RED = Selected radio")
        logger.info("   - 🟢 GREEN = Available radios")
        logger.info("   - 💛 YELLOW = Insert/Update button")
        logger.info("\n   Press Ctrl+C to exit...")

        try:
            await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("\n\n✅ Exiting...")

if __name__ == "__main__":
    asyncio.run(main())

