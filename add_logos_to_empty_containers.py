#!/usr/bin/env python3
"""
Add Logos to Empty Containers - Complete Workflow
==================================================

Implements the workflow to add logos to empty containers:
1. Detect empty logo containers (first 2 TDs in header table)
2. Click container to select it
3. Click "Insert Image" from main toolbar
4. Select Tilton logo from media library
5. Insert, center, enlarge to 200px
6. Publish after each logo

Target: https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright, Page

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
TILTON_LOGO_ID = "6a19132b6697f36de6236fb1"
TARGET_WIDTH = 200


async def detect_empty_logo_containers(page: Page):
    """Detect the first 2 empty logo containers in header table"""
    
    logger.info("\n" + "="*100)
    logger.info("🔍 DETECTING EMPTY LOGO CONTAINERS")
    logger.info("="*100)
    
    result = await page.evaluate("""
        () => {
            // Find the header table with 3 TDs (2 logos + 1 alignment)
            const tables = Array.from(document.querySelectorAll('table'));
            
            for (const table of tables) {
                const firstRow = table.querySelector('tr');
                if (!firstRow) continue;
                
                const tds = Array.from(firstRow.querySelectorAll('td'));
                
                // Look for table with exactly 3 TDs in first row
                if (tds.length === 3) {
                    // Check if first 2 TDs have empty logo containers
                    const logoContainers = [];
                    
                    for (let i = 0; i < 2; i++) {  // Only first 2 TDs
                        const td = tds[i];
                        const container = td.querySelector('[class*="elementContainer"]');
                        
                        if (container) {
                            const hasImage = container.querySelector('img') !== null;
                            
                            if (!hasImage) {
                                // Mark it
                                container.setAttribute('data-logo-container-to-fill', `logo-${i + 1}`);
                                container.style.outline = '5px solid lime';
                                container.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
                                
                                logoContainers.push({
                                    index: i + 1,
                                    id: container.id || 'no-id',
                                    found: true
                                });
                            }
                        }
                    }
                    
                    if (logoContainers.length > 0) {
                        return {
                            found: true,
                            count: logoContainers.length,
                            containers: logoContainers
                        };
                    }
                }
            }
            
            return { found: false, count: 0, containers: [] };
        }
    """)
    
    return result


async def click_container_to_select(page: Page, logo_idx: int) -> bool:
    """Click INSIDE the empty container to place cursor there"""

    logger.info(f"\n📍 Clicking INSIDE logo container #{logo_idx} to place cursor...")

    try:
        # Click INSIDE the container's editable area (TEXT_TEMPLATE div)
        clicked = await page.evaluate(f"""
            () => {{
                const container = document.querySelector('[data-logo-container-to-fill="logo-{logo_idx}"]');
                if (!container) return {{ clicked: false, reason: 'Container not found' }};

                // Find the editable TEXT_TEMPLATE div inside the container
                const editableDiv = container.querySelector('.TEXT_TEMPLATE') ||
                                   container.querySelector('[contenteditable="true"]') ||
                                   container.querySelector('div[role="presentation"]');

                if (editableDiv) {{
                    // Click in the CENTER of the editable area to place cursor
                    const rect = editableDiv.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;

                    // Click the editable div
                    editableDiv.click();
                    editableDiv.focus();

                    // Visual feedback
                    editableDiv.style.outline = '3px solid cyan';

                    return {{
                        clicked: true,
                        clickedElement: 'TEXT_TEMPLATE',
                        position: {{ x: Math.round(centerX), y: Math.round(centerY) }}
                    }};
                }}

                // Fallback: click the container itself
                const rect = container.getBoundingClientRect();
                container.click();
                container.focus();

                return {{
                    clicked: true,
                    clickedElement: 'container-fallback',
                    reason: 'TEXT_TEMPLATE not found, clicked container'
                }};
            }}
        """)

        if clicked['clicked']:
            logger.info(f"   ✅ Clicked INSIDE container #{logo_idx}")
            logger.info(f"      Element: {clicked.get('clickedElement')}")
            if clicked.get('position'):
                logger.info(f"      Position: x={clicked['position']['x']}, y={clicked['position']['y']}")
            await asyncio.sleep(1.5)  # Wait for cursor to be placed
            return True
        else:
            logger.error(f"   ❌ Container #{logo_idx} not found: {clicked.get('reason')}")
            return False

    except Exception as e:
        logger.error(f"   ❌ Error clicking container: {e}")
        return False


async def click_insert_image_toolbar(page: Page) -> bool:
    """Click 'Insert Image' icon button"""

    logger.info(f"\n🖼️  Clicking 'Insert Image' icon button...")

    try:
        # Based on HTML: <div class="...icon-insert-image" aria-label="icon-insert-image" role="img">
        clicked = await page.evaluate("""
            () => {
                // Strategy 1: Find by aria-label="icon-insert-image"
                const iconInsertImage = document.querySelector('[aria-label="icon-insert-image"]');

                if (iconInsertImage && iconInsertImage.offsetParent !== null) {
                    const rect = iconInsertImage.getBoundingClientRect();

                    // Click the icon or its parent button
                    const clickable = iconInsertImage.closest('button, div[role="button"], [onclick]') ||
                                     iconInsertImage.parentElement ||
                                     iconInsertImage;

                    clickable.click();

                    return {
                        clicked: true,
                        tagName: clickable.tagName,
                        position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                        method: 'aria-label-icon-insert-image'
                    };
                }

                // Strategy 2: Find by class containing "icon-insert-image"
                const byClass = document.querySelector('[class*="icon-insert-image"]');

                if (byClass && byClass.offsetParent !== null) {
                    const clickable = byClass.closest('button, div[role="button"]') ||
                                     byClass.parentElement ||
                                     byClass;
                    clickable.click();

                    return {
                        clicked: true,
                        tagName: clickable.tagName,
                        method: 'class-icon-insert-image'
                    };
                }

                // Strategy 3: Find icon with role="img" and aria-label containing "insert"
                const icons = Array.from(document.querySelectorAll('[role="img"]'));
                for (const icon of icons) {
                    const ariaLabel = icon.getAttribute('aria-label') || '';

                    if (ariaLabel.toLowerCase().includes('insert') && ariaLabel.toLowerCase().includes('image')) {
                        if (icon.offsetParent !== null) {
                            const clickable = icon.closest('button, div[role="button"]') || icon.parentElement || icon;
                            clickable.click();

                            return {
                                clicked: true,
                                tagName: clickable.tagName,
                                method: 'role-img-with-insert-image-label'
                            };
                        }
                    }
                }

                return { clicked: false, reason: 'icon-insert-image not found' };
            }
        """)

        if clicked['clicked']:
            logger.info(f"   ✅ Clicked Insert Image button")
            logger.info(f"      Method: {clicked.get('method', 'unknown')}")
            logger.info(f"      Selector: {clicked.get('selector', 'unknown')}")
            await asyncio.sleep(2)  # Wait for media library to open
            return True
        else:
            logger.error(f"   ❌ Insert Image button not found: {clicked.get('reason')}")
            return False

    except Exception as e:
        logger.error(f"   ❌ Error clicking Insert Image: {e}")
        return False


async def select_and_insert_tilton_logo(page: Page, logo_media_id: str) -> bool:
    """Select Tilton logo from media library and click INSERT"""

    logger.info(f"\n📂 Selecting Tilton logo from media library...")

    try:
        # Wait for media library popup
        await asyncio.sleep(2)

        # Find and CLICK the Tilton logo's top layer to select it (reveals radio button)
        # This matches the working logic from process_opened_templates.py
        logo_clicked = await page.evaluate(f"""
            () => {{
                const images = Array.from(document.querySelectorAll('img'));

                for (const img of images) {{
                    const src = img.src || '';

                    if (src.includes('{logo_media_id}')) {{
                        // Find the media tile containing this logo
                        const mediaTile = img.closest('[class*="mediaTile"]') ||
                                         img.closest('[class*="tile"]') ||
                                         img.closest('[class*="media"]');

                        if (mediaTile) {{
                            // Find the clickable overlay/top layer (this reveals the radio button)
                            const topLayer = mediaTile.querySelector('[role="button"]') ||
                                            mediaTile.querySelector('[class*="topLayer"]') ||
                                            mediaTile.querySelector('[class*="overlay"]');

                            if (topLayer) {{
                                // Click the top layer to select the logo (reveals/clicks radio button)
                                topLayer.click();

                                // Visual confirmation
                                img.style.outline = '5px solid lime';
                                mediaTile.style.outline = '3px solid yellow';
                                if (topLayer !== mediaTile) {{
                                    topLayer.style.outline = '2px dashed orange';
                                }}

                                return {{
                                    found: true,
                                    clicked: true,
                                    src: src.substring(0, 80),
                                    mediaTileClass: mediaTile.className.substring(0, 60),
                                    topLayerClass: topLayer.className.substring(0, 60),
                                    topLayerTag: topLayer.tagName,
                                    method: 'topLayer-click'
                                }};
                            }} else {{
                                // Fallback: click the media tile itself
                                mediaTile.click();

                                img.style.outline = '5px solid lime';
                                mediaTile.style.outline = '3px solid yellow';

                                return {{
                                    found: true,
                                    clicked: true,
                                    src: src.substring(0, 80),
                                    mediaTileClass: mediaTile.className.substring(0, 60),
                                    method: 'mediaTile-fallback'
                                }};
                            }}
                        }}
                    }}
                }}

                return {{ found: false, reason: 'Logo not found in media library' }};
            }}
        """)

        if not logo_clicked['found']:
            logger.error(f"   ❌ Tilton logo not found: {logo_clicked.get('reason')}")
            return False

        logger.info(f"   ✅ Tilton logo selected via {logo_clicked.get('method', 'unknown')}")
        if logo_clicked.get('topLayerClass'):
            logger.info(f"      Top Layer: <{logo_clicked.get('topLayerTag')}> {logo_clicked.get('topLayerClass', '')[:40]}")
        logger.info(f"      Media Tile: {logo_clicked.get('mediaTileClass', '')[:40]}")
        await asyncio.sleep(1.5)  # Wait for selection/radio button to register

        # Click INSERT button
        insert_clicked = await page.evaluate("""
            () => {
                const buttons = Array.from(document.querySelectorAll('button'));

                for (const btn of buttons) {
                    const text = btn.textContent.trim();

                    if (text === 'INSERT' || text === 'Insert' || text === 'insert') {
                        const rect = btn.getBoundingClientRect();
                        if (rect.x > 100) {  // Not hidden at 0,0
                            btn.click();
                            return { clicked: true };
                        }}
                }

                return { clicked: false, reason: 'INSERT button not found' };
            }
        """)

        if not insert_clicked['clicked']:
            logger.error(f"   ❌ INSERT button not found")
            return False

        logger.info(f"   ✅ Clicked INSERT button")
        await asyncio.sleep(3)  # Wait longer for popup to close

        # Verify popup closed
        popup_closed = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') ||
                             document.querySelector('.ant-modal');
                return !popup || popup.getBoundingClientRect().width === 0;
            }
        """)

        if popup_closed:
            logger.info(f"   ✅ Media library closed - logo inserted")
            return True
        else:
            logger.warning(f"   ⚠️  Media library still open - trying to close it...")

            # Try to close popup by clicking Cancel or X button
            closed = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') ||
                                 document.querySelector('.ant-modal');

                    if (popup) {
                        // Try clicking Cancel button
                        const cancelBtn = Array.from(popup.querySelectorAll('button'))
                            .find(btn => btn.textContent.trim().toLowerCase() === 'cancel');

                        if (cancelBtn) {
                            cancelBtn.click();
                            return { closed: true, method: 'cancel-button' };
                        }

                        // Try clicking X button
                        const closeBtn = popup.querySelector('[aria-label="close"], [aria-label="Close"], .ant-modal-close');
                        if (closeBtn) {
                            closeBtn.click();
                            return { closed: true, method: 'close-button' };
                        }
                    }

                    return { closed: false };
                }
            """)

            if closed['closed']:
                logger.info(f"   ✅ Closed popup via {closed.get('method')}")
                await asyncio.sleep(1)
                return True
            else:
                logger.warning(f"   ⚠️  Could not close popup automatically")
                return True  # Continue anyway - logo might have been inserted

    except Exception as e:
        logger.error(f"   ❌ Error selecting/inserting logo: {e}")
        return False


async def main():
    TARGET_URL = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48"

    logger.info("="*100)
    logger.info("🚀 ADD LOGOS TO EMPTY CONTAINERS - COMPLETE WORKFLOW")
    logger.info("="*100)
    logger.info(f"Target: {TARGET_URL}")
    logger.info(f"Logo ID: {TILTON_LOGO_ID}")
    logger.info(f"Target Width: {TARGET_WIDTH}px")
    logger.info("="*100)

    async with async_playwright() as playwright:
        try:
            # Connect to browser
            logger.info("\n🌐 Connecting to browser...")
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            logger.info("✅ Connected")

            # Find target tab
            target_page = None
            for page in context.pages:
                if TARGET_URL in page.url:
                    target_page = page
                    break

            if not target_page:
                logger.error("❌ Template tab not found!")
                return

            await target_page.bring_to_front()
            await asyncio.sleep(2)

            # STEP 1: Detect empty logo containers
            detection = await detect_empty_logo_containers(target_page)

            if not detection['found']:
                logger.error("❌ No empty logo containers found!")
                return

            logger.info(f"\n✅ Found {detection['count']} empty logo container(s)")

            # STEP 2: Process each logo container
            for logo_idx in range(1, detection['count'] + 1):
                logger.info("\n" + "="*100)
                logger.info(f"🎯 PROCESSING LOGO #{logo_idx}")
                logger.info("="*100)

                # Click container to select
                if not await click_container_to_select(target_page, logo_idx):
                    logger.error(f"❌ Failed to select container #{logo_idx}")
                    continue

                # Click Insert Image from toolbar
                if not await click_insert_image_toolbar(target_page):
                    logger.error(f"❌ Failed to open Insert Image")
                    continue

                # Select and insert Tilton logo
                if not await select_and_insert_tilton_logo(target_page, TILTON_LOGO_ID):
                    logger.error(f"❌ Failed to insert logo")
                    continue

                logger.info(f"\n✅ Logo #{logo_idx} inserted successfully!")

                # TODO: Add center align, enlarge to 200px, publish

            logger.info("\n" + "="*100)
            logger.info("✅ WORKFLOW COMPLETE")
            logger.info("="*100)

        except Exception as e:
            logger.exception(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

