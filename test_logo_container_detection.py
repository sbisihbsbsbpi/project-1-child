#!/usr/bin/env python3
"""
TEST: Logo 1 & Logo 2 Container Detection - June 2, 2026
=========================================================

This test specifically detects and shows:
1. Logo 1 containers (LEFT, CENTER, RIGHT)
2. Logo 2 containers (LEFT, CENTER, RIGHT)
3. Warning logos and their departments
4. Which specific containers have logos

Author: Test Suite
Date: 2026-06-02
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
TEST_TEMPLATE_ID = "667f0befd4964026ee7b6ea2"  # Service History Recap PDF
CDP_URL = "http://localhost:9223"
BASE_URL = "https://preprodapp.tekioncloud.com"

async def test_logo_containers(page):
    """Detect all Logo 1 & Logo 2 containers"""
    logger.info("\n" + "="*100)
    logger.info("🔍 LOGO CONTAINER DETECTION TEST")
    logger.info("="*100)

    detection_result = await page.evaluate("""
        () => {
            // LOGO 1 & LOGO 2 CONTAINER IDS (hardcoded positions)
            const containerIds = [
                '6f0b8570-c4dc-45bd-b746-40e3af9af3bb',  // Logo 1 LEFT
                '7653caa9-31b7-4e2b-8233-f0bda43672ea',  // Logo 1 CENTER
                '47da3c0a-2c2b-4f8f-8a31-4ba8fdae03aa',  // Logo 1 RIGHT
                '9fa2920b-10f8-48d2-9947-b014398d21be',  // Logo 2 LEFT
                '983932ae-d79a-40fe-a9ba-df07c9beee47',  // Logo 2 CENTER
                '9d454086-c1f2-4bf0-b4a7-8e95dc244aae'   // Logo 2 RIGHT
            ];

            const containerNames = [
                'Logo 1 LEFT', 'Logo 1 CENTER', 'Logo 1 RIGHT',
                'Logo 2 LEFT', 'Logo 2 CENTER', 'Logo 2 RIGHT'
            ];

            const results = {
                logo1Containers: [],
                logo2Containers: [],
                warningLogos: [],
                summary: {}
            };

            // Check each container
            containerIds.forEach((id, idx) => {
                const container = document.querySelector(`div.TEXT_TEMPLATE[id="${id}"][contenteditable="true"]`);
                const name = containerNames[idx];
                const position = idx < 3 ? 'Logo 1' : 'Logo 2';
                const alignment = idx % 3 === 0 ? 'LEFT' : (idx % 3 === 1 ? 'CENTER' : 'RIGHT');

                const info = {
                    name: name,
                    id: id,
                    position: position,
                    alignment: alignment,
                    found: container !== null,
                    hasImage: false,
                    isEmpty: false,
                    htmlLength: 0,
                    top: 0,
                    hasWarning: false
                };

                if (container) {
                    const hasImage = container.querySelector('img') !== null;
                    const htmlLength = container.innerHTML.trim().length;
                    const isEmpty = !hasImage && htmlLength < 300;
                    const rect = container.getBoundingClientRect();

                    // Check if this container has a warning icon
                    const warning = container.querySelector('.templates_Image_warningIcon__hCZHMuhEmb');

                    info.hasImage = hasImage;
                    info.isEmpty = isEmpty;
                    info.htmlLength = htmlLength;
                    info.top = Math.round(rect.top);
                    info.hasWarning = warning !== null;
                }

                if (idx < 3) {
                    results.logo1Containers.push(info);
                } else {
                    results.logo2Containers.push(info);
                }
            });

            // Find ALL warning icons (not just in Logo 1/2 containers)
            const warnings = document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb');

            warnings.forEach((icon, idx) => {
                const sortable = icon.closest('[class*="SortableItem"]');
                if (sortable) {
                    const rect = sortable.getBoundingClientRect();
                    const nearbyText = sortable.innerText || sortable.textContent || '';
                    const upperText = nearbyText.toUpperCase();

                    // Detect department
                    let department = 'unknown';
                    if (upperText.includes('SERVICE')) department = 'Service';
                    else if (upperText.includes('SALES')) department = 'Sales';
                    else if (upperText.includes('PARTS')) department = 'Parts';
                    else if (rect.top < 600) department = 'header';

                    // Try to find which Logo 1/2 container this is in
                    let inContainer = 'unknown';
                    const parentId = sortable.closest('div[id]')?.id || '';
                    if (containerIds.includes(parentId)) {
                        inContainer = containerNames[containerIds.indexOf(parentId)];
                    }

                    results.warningLogos.push({
                        index: idx + 1,
                        department: department,
                        position: Math.round(rect.top),
                        inContainer: inContainer,
                        parentId: parentId.substring(0, 20) + '...',
                        textSnippet: nearbyText.substring(0, 100).replace(/\\n/g, ' ')
                    });
                }
            });

            // Summary
            results.summary = {
                totalLogo1Found: results.logo1Containers.filter(c => c.found).length,
                totalLogo2Found: results.logo2Containers.filter(c => c.found).length,
                logo1WithImages: results.logo1Containers.filter(c => c.hasImage).length,
                logo2WithImages: results.logo2Containers.filter(c => c.hasImage).length,
                logo1Empty: results.logo1Containers.filter(c => c.isEmpty).length,
                logo2Empty: results.logo2Containers.filter(c => c.isEmpty).length,
                totalWarnings: warnings.length
            };

            return results;
        }
    """)

    # Print Logo 1 containers
    logger.info("\n📦 LOGO 1 CONTAINERS (3 positions):")
    logger.info("="*100)
    for container in detection_result['logo1Containers']:
        status = "✅ FOUND" if container['found'] else "❌ NOT FOUND"
        logger.info(f"  {status}: {container['name']}")
        if container['found']:
            logger.info(f"     - Has Image: {container['hasImage']}")
            logger.info(f"     - Is Empty: {container['isEmpty']}")
            logger.info(f"     - Has Warning: {container['hasWarning']}")
            logger.info(f"     - Position: {container['top']}px from top")
            logger.info(f"     - HTML Length: {container['htmlLength']} chars")
            logger.info(f"     - ID: {container['id'][:30]}...")

    # Print Logo 2 containers
    logger.info("\n📦 LOGO 2 CONTAINERS (3 positions):")
    logger.info("="*100)
    for container in detection_result['logo2Containers']:
        status = "✅ FOUND" if container['found'] else "❌ NOT FOUND"
        logger.info(f"  {status}: {container['name']}")
        if container['found']:
            logger.info(f"     - Has Image: {container['hasImage']}")
            logger.info(f"     - Is Empty: {container['isEmpty']}")
            logger.info(f"     - Has Warning: {container['hasWarning']}")
            logger.info(f"     - Position: {container['top']}px from top")
            logger.info(f"     - HTML Length: {container['htmlLength']} chars")
            logger.info(f"     - ID: {container['id'][:30]}...")

    # Print warning logos
    logger.info("\n⚠️  WARNING LOGOS DETECTED:")
    logger.info("="*100)
    if detection_result['warningLogos']:
        for warning in detection_result['warningLogos']:
            logger.info(f"  Warning Logo #{warning['index']}:")
            logger.info(f"     - Department: {warning['department']}")
            logger.info(f"     - Position: {warning['position']}px from top")
            logger.info(f"     - In Container: {warning['inContainer']}")
            logger.info(f"     - Parent ID: {warning['parentId']}")
            if warning['textSnippet'].strip():
                logger.info(f"     - Text Snippet: '{warning['textSnippet']}'")
            logger.info("")
    else:
        logger.info("  No warning logos found")

    # Print summary
    logger.info("\n📊 SUMMARY:")
    logger.info("="*100)
    summary = detection_result['summary']
    logger.info(f"  Logo 1 Containers Found: {summary['totalLogo1Found']}/3")
    logger.info(f"  Logo 2 Containers Found: {summary['totalLogo2Found']}/3")
    logger.info(f"  Logo 1 with Images: {summary['logo1WithImages']}")
    logger.info(f"  Logo 2 with Images: {summary['logo2WithImages']}")
    logger.info(f"  Logo 1 Empty: {summary['logo1Empty']}")
    logger.info(f"  Logo 2 Empty: {summary['logo2Empty']}")
    logger.info(f"  Total Warnings: {summary['totalWarnings']}")

    return detection_result


async def main():
    """Main test execution"""
    logger.info("="*100)
    logger.info("🧪 LOGO 1 & LOGO 2 CONTAINER DETECTION TEST")
    logger.info("="*100)
    logger.info(f"Test Template: {TEST_TEMPLATE_ID}")
    logger.info(f"CDP URL: {CDP_URL}")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*100)

    async with async_playwright() as playwright:
        try:
            # Connect to existing browser
            browser = await playwright.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]

            # Find or create template edit page
            pages = context.pages
            page = None

            for existing_page in pages:
                if TEST_TEMPLATE_ID in existing_page.url:
                    page = existing_page
                    logger.info(f"✅ Found existing template edit page")
                    break

            if not page:
                logger.info("Opening template edit page...")
                page = await context.new_page()
                edit_url = f"{BASE_URL}/templates/edit/{TEST_TEMPLATE_ID}"
                await page.goto(edit_url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(10)
                logger.info("✅ Template editor loaded")

            # Run detection
            result = await test_logo_containers(page)

            # HIGHLIGHT WARNING LOGOS IN THE BROWSER
            logger.info("\n" + "="*100)
            logger.info("🎨 HIGHLIGHTING WARNING LOGOS IN BROWSER")
            logger.info("="*100)

            highlight_result = await page.evaluate("""
                () => {
                    const warnings = document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb');
                    const highlighted = [];

                    warnings.forEach((icon, idx) => {
                        const sortable = icon.closest('[class*="SortableItem"]');
                        if (sortable) {
                            // Add thick red border and background
                            sortable.style.border = '5px solid red';
                            sortable.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
                            sortable.style.padding = '10px';

                            // Add a label
                            const label = document.createElement('div');
                            label.style.cssText = `
                                position: absolute;
                                top: -30px;
                                left: 0;
                                background: red;
                                color: white;
                                padding: 5px 10px;
                                font-weight: bold;
                                font-size: 14px;
                                z-index: 10000;
                                border-radius: 5px;
                            `;
                            label.textContent = `WARNING LOGO #${idx + 1}`;

                            sortable.style.position = 'relative';
                            sortable.insertBefore(label, sortable.firstChild);

                            // Scroll to first warning logo
                            if (idx === 0) {
                                sortable.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            }

                            const rect = sortable.getBoundingClientRect();
                            highlighted.push({
                                index: idx + 1,
                                top: Math.round(rect.top + window.scrollY),
                                visible: true
                            });
                        }
                    });

                    return {
                        total: warnings.length,
                        highlighted: highlighted
                    };
                }
            """)

            logger.info(f"✅ Highlighted {highlight_result['total']} warning logos in the browser")
            for h in highlight_result['highlighted']:
                logger.info(f"   - Warning Logo #{h['index']} is now highlighted with RED BORDER")

            logger.info("\n🔍 INSPECT THE BROWSER NOW:")
            logger.info("   - Warning logos have RED BORDERS")
            logger.info("   - Labels show 'WARNING LOGO #1', 'WARNING LOGO #2', etc.")
            logger.info("   - First logo has been scrolled into view")
            logger.info("")

            # Wait for user to inspect
            logger.info("⏸️  Waiting 30 seconds for inspection...")
            await asyncio.sleep(30)

            # Final analysis
            logger.info("\n" + "="*100)
            logger.info("🎯 ANALYSIS:")
            logger.info("="*100)

            if result['warningLogos']:
                for warning in result['warningLogos']:
                    if warning['inContainer'] != 'unknown':
                        logger.info(f"✅ Warning logo is in: {warning['inContainer']}")
                        logger.info(f"   Department detected: {warning['department']}")
                    else:
                        logger.info(f"⚠️  Warning logo not in any Logo 1/2 container")
                        logger.info(f"   This logo is outside the 6 hardcoded positions")
                        logger.info(f"   Position: {warning['position']}px")
                        logger.info(f"   Department: {warning['department']}")
            else:
                logger.info("No warning logos found on this template")

            logger.info("\n" + "="*100)
            logger.info("✅ DETECTION COMPLETE")
            logger.info("="*100)

        except Exception as e:
            logger.exception(f"❌ Fatal error during test execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())
