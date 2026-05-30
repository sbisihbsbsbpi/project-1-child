#!/usr/bin/env python3
"""
Batch Header & Logo Detector for Tekion Templates
Detects if Header is grayed out and logo is in header position for all templates
Filters by SERVICE & PARTS departments
"""

import asyncio
import sys
import os
import json
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def wait_for_template_editor_loaded(page):
    """Wait for template editor to fully load"""
    logger.info("      ⏳ Waiting for template editor to load...")

    try:
        # Wait for the Inserts panel to be visible (indicates editor is ready)
        await page.wait_for_selector('text=/Image|Video|Button/', timeout=15000)
        logger.info("      ✅ Inserts panel visible")

        # Wait for any loading spinners to disappear
        await page.wait_for_function("""
            () => {
                const spinners = document.querySelectorAll('[class*="loading"], [class*="spinner"], [class*="Loading"]');
                return spinners.length === 0 || Array.from(spinners).every(s => s.offsetParent === null);
            }
        """, timeout=10000)
        logger.info("      ✅ No loading indicators")

        # Wait for template canvas/preview to render
        logger.info("      ⏳ Waiting for template content to render...")
        await asyncio.sleep(5)

        # Extra buffer for dynamic content to settle (logos, images, header state)
        logger.info("      ⏳ Waiting for images and dynamic content...")
        await asyncio.sleep(6)

        # Additional wait for header button state to finalize
        logger.info("      ⏳ Waiting for header state to finalize...")
        await asyncio.sleep(6)

        logger.info("      ✅ Template fully loaded (waited 17 seconds total)")

    except Exception as e:
        logger.warning(f"      ⚠️ Timeout waiting for editor: {e}")
        # Fallback to longer fixed wait
        await asyncio.sleep(17)


async def detect_header_and_logo_in_template(page, template_id):
    """
    Detect if Header option is grayed out and logo is in header position
    Returns: dict with detection results
    """

    # Wait for template editor to fully load
    await wait_for_template_editor_loaded(page)

    # Load ignore list for logo detection
    with open('logo_ignore_list.json') as f:
        ignore_list = json.load(f)

    result = await page.evaluate("""
        (ignorePatterns) => {
            const analysis = {
                templateId: window.location.pathname.split('/').pop(),
                headerGrayedOut: false,
                logoInHeader: false,
                logoDetails: null,
                headerDetails: null
            };

            // Helper to check if element is ignored (UI elements)
            function isIgnored(el) {
                if (!el) return true;
                if (ignorePatterns.ids.includes(el.id)) return true;
                const classes = el.className || '';
                for (const pattern of ignorePatterns.class_names) {
                    if (classes.includes(pattern)) return true;
                }
                for (const parentSelector of ignorePatterns.parent_selectors) {
                    if (el.closest(parentSelector)) return true;
                }
                return false;
            }

            // 1. CHECK IF HEADER IS GRAYED OUT
            // IMPROVED: Direct search by ID
            const headerButton = document.querySelector('#HEADER');

            if (headerButton) {
                const rect = headerButton.getBoundingClientRect();
                const computedStyle = window.getComputedStyle(headerButton);

                // Check if disabled via class name
                const hasDisabledClass = headerButton.className.includes('disabledButton') ||
                                        headerButton.className.includes('disabled');

                // Check CSS properties
                const opacity = parseFloat(computedStyle.opacity);
                const pointerEvents = computedStyle.pointerEvents;
                const isDisabled = headerButton.hasAttribute('disabled') ||
                                 headerButton.getAttribute('aria-disabled') === 'true';

                // Header is grayed if: has disabled class OR opacity < 1 OR pointer-events none
                const isGrayed = hasDisabledClass || opacity < 1 || pointerEvents === 'none' || isDisabled;

                analysis.headerGrayedOut = isGrayed;
                analysis.headerDetails = {
                    id: 'HEADER',
                    hasDisabledClass: hasDisabledClass,
                    opacity: opacity,
                    pointerEvents: pointerEvents,
                    disabled: isDisabled,
                    position: { top: Math.round(rect.top), left: Math.round(rect.left) }
                };
            }

            // 2. DETECT ALL LOGOS BY POSITION (HEADER/TOP/BOTTOM)
            const HEADER_THRESHOLD = 600;   // top < 600 = header
            const TOP_THRESHOLD = 1200;     // 600 <= top < 1200 = top/body
                                            // top >= 1200 = bottom

            const allImgs = document.querySelectorAll('img');
            const logosByPosition = { header: [], top: [], bottom: [] };

            for (const img of allImgs) {
                if (isIgnored(img)) continue;

                const src = img.src || '';
                const rect = img.getBoundingClientRect();

                // Look for S3 images with media_ pattern (dealer logos)
                if (src.includes('amazonaws.com') && src.includes('media_')) {

                    // Check if reasonable logo size
                    const isReasonableSize = rect.width > 50 && rect.width < 500 &&
                                            rect.height > 20 && rect.height < 200;

                    if (isReasonableSize) {
                        const logoInfo = {
                            src: src.substring(0, 150),
                            position: {
                                top: Math.round(rect.top),
                                left: Math.round(rect.left)
                            },
                            size: {
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            },
                            parent: img.parentElement?.tagName || 'unknown'
                        };

                        // Classify by position
                        if (rect.top < HEADER_THRESHOLD) {
                            logosByPosition.header.push(logoInfo);
                        } else if (rect.top < TOP_THRESHOLD) {
                            logosByPosition.top.push(logoInfo);
                        } else {
                            logosByPosition.bottom.push(logoInfo);
                        }
                    }
                }
            }

            // Store detected logos
            analysis.logos = {
                header: logosByPosition.header.length > 0 ? logosByPosition.header[0] : null,
                top: logosByPosition.top.length > 0 ? logosByPosition.top[0] : null,
                bottom: logosByPosition.bottom.length > 0 ? logosByPosition.bottom[0] : null
            };

            // Legacy support: logoInHeader = has header logo
            analysis.logoInHeader = analysis.logos.header !== null;
            analysis.logoDetails = analysis.logos.header;

            // Count total logos
            analysis.logoCount = (analysis.logos.header ? 1 : 0) +
                                (analysis.logos.top ? 1 : 0) +
                                (analysis.logos.bottom ? 1 : 0);

            return analysis;
        }
    """, ignore_list['ignore_patterns'])

    return result


async def wait_for_page_fully_loaded(page):
    """Wait for templates list page to fully load"""
    logger.info("   Waiting for page to fully load...")

    # Wait for the main grid/table to appear
    try:
        await page.wait_for_selector('table, [class*="grid"], [class*="list"]', timeout=10000)
        await asyncio.sleep(2)
        logger.info("   ✅ Page loaded")
    except:
        logger.warning("   ⚠️ Could not find grid, continuing anyway...")
        await asyncio.sleep(3)


async def get_filtered_templates(page, departments=['Service', 'Parts']):
    """
    Apply department filter and get template list via API
    """

    logger.info(f"🎯 Applying filter: {', '.join(departments)}")

    # Wait for page to be fully loaded first
    await wait_for_page_fully_loaded(page)

    # Capture templates via API interception
    templates = []
    response_received = asyncio.Event()

    async def handle_response(response):
        nonlocal templates
        if '/api/templatestore/u/search' in response.url:
            try:
                data = await response.json()
                if 'data' in data and 'hits' in data['data']:
                    hits = data['data']['hits']
                    if hits:
                        templates.extend(hits)
                        logger.info(f"   📥 Captured {len(hits)} templates from API")
                        response_received.set()
            except:
                pass

    page.on('response', handle_response)

    # Wait a moment to see if API already fired from page load
    logger.info("   ⏳ Waiting for initial API response...")
    await asyncio.sleep(4)

    if not response_received.is_set():
        # Try reloading to trigger API
        logger.info("   🔄 Reloading page to trigger API...")
        await page.reload(wait_until='domcontentloaded')
        logger.info("   ⏳ Waiting for templates to load after reload...")
        await asyncio.sleep(5)

    try:
        await asyncio.wait_for(response_received.wait(), timeout=15.0)
    except asyncio.TimeoutError:
        logger.warning("⚠️  Timeout waiting for API response")

    page.remove_listener('response', handle_response)

    logger.info(f"✅ Found {len(templates)} templates")
    return templates


async def main():
    logger.info("=" * 100)
    logger.info("🔍 BATCH HEADER & LOGO DETECTOR FOR TEKION TEMPLATES")
    logger.info("=" * 100)
    logger.info("Filters: SERVICE + PARTS departments")
    logger.info("Detects: Header grayed out + Logo in header position")
    logger.info("=" * 100)

    async with async_playwright() as playwright:
        # Connect to existing browser
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]

        # Find existing Tekion tab or create new one
        working_tab = None
        for p in context.pages:
            if 'tekioncloud.com/templates' in p.url:
                working_tab = p
                logger.info("\n✅ Using existing Tekion tab")
                break

        if not working_tab:
            working_tab = await context.new_page()
            logger.info("\n✅ Created new tab")

        # Always navigate to templates list to start fresh
        logger.info("📍 Navigating to templates list page...")
        await working_tab.goto("https://preprodapp.tekioncloud.com/templates/list", wait_until='domcontentloaded', timeout=15000)
        await working_tab.bring_to_front()
        await asyncio.sleep(3)

        # Step 1: Apply filter and get template list
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 1: GET FILTERED TEMPLATE LIST")
        logger.info("=" * 100)

        templates = await get_filtered_templates(working_tab, departments=['Service', 'Parts'])

        if not templates:
            logger.error("❌ No templates found!")
            return

        logger.info(f"\nFound {len(templates)} templates to analyze")

        # Step 2: Analyze each template
        logger.info("\n" + "=" * 100)
        logger.info("🔍 STEP 2: ANALYZE EACH TEMPLATE")
        logger.info("=" * 100)

        results = []

        for idx, template in enumerate(templates, 1):
            template_id = template.get('templateId') or template.get('id')
            template_name = template.get('name', 'Unknown')
            departments = ', '.join(template.get('departments', []))

            logger.info(f"\n[{idx}/{len(templates)}] {template_name}")
            logger.info(f"   ID: {template_id}")
            logger.info(f"   Departments: {departments}")

            try:
                # Navigate to template edit page
                logger.info(f"   🌐 Loading template editor...")
                edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
                await working_tab.goto(edit_url, wait_until='domcontentloaded', timeout=20000)

                # Detect header and logo (includes its own wait logic)
                detection = await detect_header_and_logo_in_template(working_tab, template_id)

                # Log results
                header_status = "✅ GRAYED (Header used)" if detection['headerGrayedOut'] else "⭐ Available"

                # Count logos
                logo_count = detection.get('logoCount', 0)
                logos_found = []
                if detection['logos']['header']:
                    logos_found.append("🟢 Header")
                if detection['logos']['top']:
                    logos_found.append("🔵 Top")
                if detection['logos']['bottom']:
                    logos_found.append("🟠 Bottom")

                logo_status = f"{logo_count} logo(s): {', '.join(logos_found)}" if logos_found else "❌ No logos"

                logger.info(f"   Header Button: {header_status}")
                logger.info(f"   Logos: {logo_status}")

                # Store result
                result = {
                    'template_id': template_id,
                    'name': template_name,
                    'departments': departments,
                    'header_grayed_out': detection['headerGrayedOut'],
                    'logo_count': detection.get('logoCount', 0),
                    'has_header_logo': detection['logos']['header'] is not None,
                    'has_top_logo': detection['logos']['top'] is not None,
                    'has_bottom_logo': detection['logos']['bottom'] is not None,
                    'header_logo_url': detection['logos']['header']['src'] if detection['logos']['header'] else None,
                    'top_logo_url': detection['logos']['top']['src'] if detection['logos']['top'] else None,
                    'bottom_logo_url': detection['logos']['bottom']['src'] if detection['logos']['bottom'] else None,
                    # Legacy fields
                    'logo_in_header': detection['logoInHeader'],
                    'has_logo': detection['logoDetails'] is not None,
                    'logo_url': detection['logoDetails']['src'] if detection['logoDetails'] else None,
                    'header_opacity': detection['headerDetails']['opacity'] if detection['headerDetails'] else None
                }
                results.append(result)

            except Exception as e:
                logger.error(f"   ❌ Error: {e}")
                results.append({
                    'template_id': template_id,
                    'name': template_name,
                    'departments': departments,
                    'header_grayed_out': False,
                    'logo_in_header': False,
                    'has_logo': False,
                    'logo_url': None,
                    'header_opacity': None,
                    'error': str(e)
                })

        # Step 3: Generate report
        logger.info("\n" + "=" * 100)
        logger.info("📊 STEP 3: GENERATE REPORT")
        logger.info("=" * 100)

        df = pd.DataFrame(results)

        # Save to files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"header_logo_analysis_{timestamp}.csv"
        json_file = f"header_logo_analysis_{timestamp}.json"

        df.to_csv(csv_file, index=False)

        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"\n✅ Saved to:")
        logger.info(f"   - {csv_file}")
        logger.info(f"   - {json_file}")

        # Summary statistics
        logger.info("\n" + "=" * 100)
        logger.info("📈 SUMMARY")
        logger.info("=" * 100)

        total = len(results)
        header_grayed = sum(1 for r in results if r['header_grayed_out'])
        logo_in_header = sum(1 for r in results if r['logo_in_header'])
        both = sum(1 for r in results if r['header_grayed_out'] and r['logo_in_header'])

        logger.info(f"\nTotal templates analyzed: {total}")
        logger.info(f"Header grayed out: {header_grayed} ({header_grayed/total*100:.1f}%)")
        logger.info(f"Logo in header position: {logo_in_header} ({logo_in_header/total*100:.1f}%)")
        logger.info(f"Both (header used + logo): {both} ({both/total*100:.1f}%)")

        # Show templates with both conditions
        if both > 0:
            logger.info(f"\n🎯 Templates with HEADER USED + LOGO IN HEADER ({both}):")
            logger.info("=" * 100)

            for r in results:
                if r['header_grayed_out'] and r['logo_in_header']:
                    logger.info(f"\n✅ {r['name']}")
                    logger.info(f"   ID: {r['template_id']}")
                    logger.info(f"   Departments: {r['departments']}")
                    if r['logo_url']:
                        logger.info(f"   Logo: {r['logo_url'][:80]}...")

        logger.info("\n" + "=" * 100)
        logger.info("✅ ANALYSIS COMPLETE")
        logger.info("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
