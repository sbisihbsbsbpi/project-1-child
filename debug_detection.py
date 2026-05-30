#!/usr/bin/env python3
"""
Debug script to visualize what the detection is finding
Highlights header and logo elements, takes screenshots
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def main():
    logger.info("=" * 100)
    logger.info("🔍 DEBUG: DETECTION WITH VISUAL HIGHLIGHTS")
    logger.info("=" * 100)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]

        # Find Tekion tab
        working_tab = None
        for p in context.pages:
            if 'tekioncloud.com/templates' in p.url:
                working_tab = p
                logger.info(f"✅ Using existing tab: {p.url}")
                break

        if not working_tab:
            working_tab = await context.new_page()
            logger.info("✅ Created new tab")

        # Navigate to templates list
        logger.info("\n📍 Navigating to templates list...")
        await working_tab.goto("https://preprodapp.tekioncloud.com/templates/list", wait_until='domcontentloaded', timeout=15000)
        await working_tab.bring_to_front()
        await asyncio.sleep(5)
        logger.info("✅ Templates list loaded")

        # Navigate to the first CPRA template
        template_id = "CPRA_REQUEST_COMPLETION_DATA_DELETION_CLOSED_DOCUMENTS"
        logger.info(f"\n🌐 Opening template: {template_id}")
        edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        await working_tab.goto(edit_url, wait_until='domcontentloaded', timeout=20000)

        # Wait for page to be fully loaded
        logger.info("\n⏳ Waiting 17 seconds for template to fully load...")
        await asyncio.sleep(17)
        logger.info("✅ Template loaded")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load ignore list
        with open('logo_ignore_list.json') as f:
            ignore_list = json.load(f)
        
        logger.info("\n🔍 Running detection and adding highlights...")
        
        # Run detection with highlights
        result = await working_tab.evaluate("""
            (ignorePatterns) => {
                const debug = {
                    headerElements: [],
                    allImages: [],
                    logoImages: [],
                    ignoredImages: [],
                    headerFound: null,
                    logoFound: null
                };
                
                // Helper to check if element is ignored
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
                
                // 1. FIND HEADER BUTTON BY ID (IMPROVED)
                const headerButton = document.querySelector('#HEADER');

                if (headerButton) {
                    const rect = headerButton.getBoundingClientRect();
                    const computedStyle = window.getComputedStyle(headerButton);
                    const opacity = parseFloat(computedStyle.opacity);
                    const hasDisabledClass = headerButton.className.includes('disabledButton') ||
                                            headerButton.className.includes('disabled');
                    const isDisabled = headerButton.hasAttribute('disabled') ||
                                     headerButton.getAttribute('aria-disabled') === 'true';
                    const pointerEvents = computedStyle.pointerEvents;

                    const isGrayed = hasDisabledClass || opacity < 1 || pointerEvents === 'none' || isDisabled;

                    debug.headerFound = {
                        id: 'HEADER',
                        isGrayed: isGrayed,
                        hasDisabledClass: hasDisabledClass,
                        opacity: opacity,
                        disabled: isDisabled,
                        pointerEvents: pointerEvents,
                        position: { top: Math.round(rect.top), left: Math.round(rect.left) }
                    };

                    // Highlight header button
                    if (isGrayed) {
                        headerButton.style.outline = '5px solid red';
                        headerButton.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
                    } else {
                        headerButton.style.outline = '3px solid yellow';
                        headerButton.style.backgroundColor = 'rgba(255, 255, 0, 0.3)';
                    }
                }
                
                // 2. FIND ALL IMAGES (IMPROVED)
                const allImgs = document.querySelectorAll('img');
                let bestLogoCandidate = null;
                let bestLogoPosition = 99999;

                for (const img of allImgs) {
                    const src = img.src || '';
                    const rect = img.getBoundingClientRect();
                    const ignored = isIgnored(img);

                    const imgInfo = {
                        src: src.substring(0, 100),
                        alt: img.alt || '',
                        position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                        size: { width: Math.round(rect.width), height: Math.round(rect.height) },
                        parent: img.parentElement?.tagName || 'none',
                        ignored: ignored,
                        fromS3: src.includes('amazonaws.com'),
                        hasMediaPattern: src.includes('media_'),
                        inTable: img.parentElement?.tagName === 'TD'
                    };

                    debug.allImages.push(imgInfo);

                    if (ignored) {
                        debug.ignoredImages.push(imgInfo);
                        img.style.outline = '2px dashed gray';
                    } else if (src.includes('amazonaws.com') && src.includes('media_')) {
                        // Highlight S3 images in blue
                        img.style.outline = '3px solid blue';
                        img.style.backgroundColor = 'rgba(0, 0, 255, 0.2)';

                        debug.logoImages.push(imgInfo);

                        // Find topmost logo (best candidate)
                        const isReasonableSize = rect.width > 50 && rect.width < 500 &&
                                                rect.height > 20 && rect.height < 200;

                        if (isReasonableSize && rect.top < bestLogoPosition) {
                            bestLogoCandidate = imgInfo;
                            bestLogoPosition = rect.top;
                        }
                    }
                }

                // Check if best logo is in header area (IMPROVED: 50% or 600px threshold)
                if (bestLogoCandidate) {
                    const viewportHeight = window.innerHeight;
                    const threshold = Math.max(viewportHeight * 0.5, 600);
                    const isInHeaderArea = bestLogoCandidate.position.top < threshold;

                    // Find and highlight the logo
                    for (const img of allImgs) {
                        if (img.src.includes(bestLogoCandidate.src)) {
                            if (isInHeaderArea) {
                                img.style.outline = '5px solid green';
                                img.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
                            }
                            break;
                        }
                    }

                    debug.logoFound = {
                        ...bestLogoCandidate,
                        inHeaderArea: isInHeaderArea,
                        viewportHeight: viewportHeight,
                        threshold: Math.round(threshold)
                    };
                }
                
                return debug;
            }
        """, ignore_list['ignore_patterns'])
        
        # Wait for highlights to render
        await asyncio.sleep(2)
        
        # Take screenshot with highlights
        screenshot = f"debug_highlighted_{timestamp}.png"
        await working_tab.screenshot(path=screenshot, full_page=True)
        logger.info(f"\n📸 Screenshot saved: {screenshot}")
        
        # Print results
        logger.info("\n" + "=" * 100)
        logger.info("📊 DETECTION RESULTS")
        logger.info("=" * 100)
        
        logger.info(f"\n🔍 HEADER ELEMENTS FOUND: {len(result['headerElements'])}")
        for idx, h in enumerate(result['headerElements'][:10], 1):
            logger.info(f"\n  [{idx}] {h['tag']} - \"{h['text']}\"")
            logger.info(f"      Position: top={h['position']['top']}, left={h['position']['left']}, width={h['position']['width']}")
            logger.info(f"      Opacity: {h['opacity']}, Disabled: {h['disabled']}, PointerEvents: {h['pointerEvents']}")
            logger.info(f"      In Left Panel: {h['inLeftPanel']}")
        
        if result['headerFound']:
            logger.info(f"\n✅ HEADER BUTTON FOUND:")
            logger.info(f"   ID: {result['headerFound']['id']}")
            logger.info(f"   Grayed Out: {result['headerFound']['isGrayed']}")
            logger.info(f"   Has Disabled Class: {result['headerFound']['hasDisabledClass']}")
            logger.info(f"   Opacity: {result['headerFound']['opacity']}")
            logger.info(f"   Pointer Events: {result['headerFound']['pointerEvents']}")
            logger.info(f"   Position: {result['headerFound']['position']}")
        else:
            logger.info("\n❌ NO HEADER BUTTON FOUND")
        
        logger.info(f"\n\n🖼️  ALL IMAGES FOUND: {len(result['allImages'])}")
        for idx, img in enumerate(result['allImages'], 1):
            logger.info(f"\n  [{idx}] {img['parent']} > img")
            logger.info(f"      Size: {img['size']['width']}x{img['size']['height']}")
            logger.info(f"      Position: top={img['position']['top']}, left={img['position']['left']}")
            logger.info(f"      From S3: {img['fromS3']}, Has 'media_': {img['hasMediaPattern']}, In Table: {img['inTable']}")
            logger.info(f"      Ignored: {img['ignored']}")
            logger.info(f"      Src: {img['src']}...")
        
        logger.info(f"\n\n🚫 IGNORED IMAGES: {len(result['ignoredImages'])}")
        
        logger.info(f"\n\n🎨 POTENTIAL LOGOS (from S3): {len(result['logoImages'])}")
        for idx, img in enumerate(result['logoImages'], 1):
            logger.info(f"\n  [{idx}] {img['size']['width']}x{img['size']['height']} at top={img['position']['top']}")
            logger.info(f"      Parent: <{img['parent']}>")
            logger.info(f"      In Table: {img['inTable']}")
            logger.info(f"      Src: {img['src']}...")
        
        if result['logoFound']:
            logger.info(f"\n\n✅ LOGO FOUND:")
            logger.info(f"   Size: {result['logoFound']['size']['width']}x{result['logoFound']['size']['height']}")
            logger.info(f"   Position: top={result['logoFound']['position']['top']}")
            logger.info(f"   In Header Area: {result['logoFound']['inHeaderArea']}")
            logger.info(f"   Threshold: {result['logoFound']['threshold']}px (50% of {result['logoFound']['viewportHeight']}px or 600px)")
            logger.info(f"   Parent: <{result['logoFound']['parent']}>")
            logger.info(f"   In Table: {result['logoFound']['inTable']}")
            logger.info(f"   Src: {result['logoFound']['src']}...")
        else:
            logger.info("\n\n❌ NO LOGO FOUND")
        
        logger.info("\n" + "=" * 100)
        logger.info("🎨 HIGHLIGHT LEGEND:")
        logger.info("  🟡 Yellow outline = Header elements in left panel")
        logger.info("  🔴 Red outline = Grayed out Header button")
        logger.info("  🔵 Blue outline = S3 images (potential logos)")
        logger.info("  🟢 Green outline = Logo in header area (top 30%)")
        logger.info("  ⚪ Gray dashed = Ignored images")
        logger.info("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
