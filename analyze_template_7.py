#!/usr/bin/env python3
"""
Analyze 7th template (Service History Recap PDF) specifically
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
    logger.info("🔍 ANALYZING TEMPLATE #7: Service History Recap PDF")
    logger.info("   Template ID: 667f0befd4964026ee7b6ea2")
    logger.info("=" * 100)
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        # Find Tekion tab
        working_tab = None
        for p in context.pages:
            if 'tekioncloud.com/templates' in p.url:
                working_tab = p
                logger.info("✅ Using existing tab")
                break
        
        if not working_tab:
            working_tab = await context.new_page()
            logger.info("✅ Created new tab")
        
        # Navigate to template #7
        template_id = "667f0befd4964026ee7b6ea2"
        logger.info(f"\n🌐 Opening template: {template_id}")
        edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        await working_tab.goto(edit_url, wait_until='domcontentloaded', timeout=20000)
        
        # Wait for full load
        logger.info("\n⏳ Waiting 17 seconds for template to fully load...")
        await asyncio.sleep(17)
        logger.info("✅ Template loaded")
        
        # Load ignore list
        with open('logo_ignore_list.json') as f:
            ignore_list = json.load(f)
        
        logger.info("\n🔍 Running detection and highlighting...")
        
        # Run detection and highlight ALL logos by position
        result = await working_tab.evaluate("""
            (ignorePatterns) => {
                const debug = {
                    headerButton: null,
                    allImages: [],
                    logos: { header: null, top: null, bottom: null },
                    logoCount: 0
                };

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

                // CHECK HEADER BUTTON
                const headerButton = document.querySelector('#HEADER');
                if (headerButton) {
                    const rect = headerButton.getBoundingClientRect();
                    const computedStyle = window.getComputedStyle(headerButton);
                    const hasDisabledClass = headerButton.className.includes('disabledButton');
                    const opacity = parseFloat(computedStyle.opacity);
                    const isGrayed = hasDisabledClass || opacity < 1;

                    debug.headerButton = {
                        isGrayed, hasDisabledClass, opacity,
                        position: { top: Math.round(rect.top), left: Math.round(rect.left) }
                    };

                    headerButton.style.outline = isGrayed ? '5px solid red' : '3px solid yellow';
                    headerButton.style.backgroundColor = isGrayed ? 'rgba(255,0,0,0.3)' : 'rgba(255,255,0,0.3)';
                }

                // FIND ALL LOGOS BY POSITION
                const HEADER_THRESHOLD = 600;   // top < 600 = header
                const TOP_THRESHOLD = 1200;     // 600 <= top < 1200 = top/body
                                                // top >= 1200 = bottom

                const allImgs = document.querySelectorAll('img');
                const logosByPosition = { header: [], top: [], bottom: [] };

                for (const img of allImgs) {
                    const src = img.src || '';
                    const rect = img.getBoundingClientRect();
                    const ignored = isIgnored(img);

                    const imgInfo = {
                        src: src.substring(0, 120),
                        position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                        size: { width: Math.round(rect.width), height: Math.round(rect.height) },
                        parent: img.parentElement?.tagName || 'none',
                        ignored, fromS3: src.includes('amazonaws.com'), hasMediaPattern: src.includes('media_')
                    };

                    debug.allImages.push(imgInfo);

                    if (ignored) {
                        img.style.outline = '2px dashed gray';
                    } else if (src.includes('amazonaws.com') && src.includes('media_')) {
                        const isReasonableSize = rect.width > 50 && rect.height > 20;

                        if (isReasonableSize) {
                            // Classify by position
                            if (rect.top < HEADER_THRESHOLD) {
                                logosByPosition.header.push({ img, info: imgInfo });
                            } else if (rect.top < TOP_THRESHOLD) {
                                logosByPosition.top.push({ img, info: imgInfo });
                            } else {
                                logosByPosition.bottom.push({ img, info: imgInfo });
                            }
                        }
                    }
                }

                // Highlight and store logos by position
                // HEADER logos - GREEN
                if (logosByPosition.header.length > 0) {
                    const logo = logosByPosition.header[0];
                    logo.img.style.outline = '8px solid green';
                    logo.img.style.backgroundColor = 'rgba(0,255,0,0.4)';
                    debug.logos.header = logo.info;
                    debug.logoCount++;
                }

                // TOP/BODY logos - BLUE
                if (logosByPosition.top.length > 0) {
                    const logo = logosByPosition.top[0];
                    logo.img.style.outline = '6px solid blue';
                    logo.img.style.backgroundColor = 'rgba(0,0,255,0.4)';
                    debug.logos.top = logo.info;
                    debug.logoCount++;
                }

                // BOTTOM logos - ORANGE
                if (logosByPosition.bottom.length > 0) {
                    const logo = logosByPosition.bottom[0];
                    logo.img.style.outline = '6px solid orange';
                    logo.img.style.backgroundColor = 'rgba(255,165,0,0.4)';
                    debug.logos.bottom = logo.info;
                    debug.logoCount++;
                }

                return debug;
            }
        """, ignore_list['ignore_patterns'])
        
        await asyncio.sleep(2)
        
        # Screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot = f"template_7_analysis_{timestamp}.png"
        await working_tab.screenshot(path=screenshot, full_page=True)
        
        # Results
        logger.info("\n" + "=" * 100)
        logger.info("📊 RESULTS")
        logger.info("=" * 100)
        
        if result['headerButton']:
            h = result['headerButton']
            logger.info(f"\n🔘 HEADER BUTTON: {'✅ GRAYED OUT' if h['isGrayed'] else '⭐ AVAILABLE'}")
            logger.info(f"   Disabled Class: {h['hasDisabledClass']}, Opacity: {h['opacity']}")

        logger.info(f"\n\n🖼️  ALL IMAGES: {len(result['allImages'])}")
        for idx, img in enumerate(result['allImages'], 1):
            logger.info(f"  [{idx}] {img['size']['width']}x{img['size']['height']} at top={img['position']['top']}, S3={img['fromS3']}, media_={img['hasMediaPattern']}")

        logger.info(f"\n\n🎯 LOGOS DETECTED: {result['logoCount']}")
        logger.info("=" * 100)

        if result['logos']['header']:
            l = result['logos']['header']
            logger.info(f"\n🟢 HEADER LOGO (top < 600px):")
            logger.info(f"   Size: {l['size']['width']}x{l['size']['height']}")
            logger.info(f"   Position: top={l['position']['top']}, left={l['position']['left']}")
            logger.info(f"   Parent: <{l['parent']}>")
            logger.info(f"   Src: {l['src']}...")
            logger.info(f"   Highlight: 🟢 GREEN (8px outline)")
        else:
            logger.info("\n❌ HEADER LOGO: Not found")

        if result['logos']['top']:
            l = result['logos']['top']
            logger.info(f"\n🔵 TOP/BODY LOGO (600px ≤ top < 1200px):")
            logger.info(f"   Size: {l['size']['width']}x{l['size']['height']}")
            logger.info(f"   Position: top={l['position']['top']}, left={l['position']['left']}")
            logger.info(f"   Parent: <{l['parent']}>")
            logger.info(f"   Src: {l['src']}...")
            logger.info(f"   Highlight: 🔵 BLUE (6px outline)")
        else:
            logger.info("\n❌ TOP/BODY LOGO: Not found")

        if result['logos']['bottom']:
            l = result['logos']['bottom']
            logger.info(f"\n🟠 BOTTOM LOGO (top ≥ 1200px):")
            logger.info(f"   Size: {l['size']['width']}x{l['size']['height']}")
            logger.info(f"   Position: top={l['position']['top']}, left={l['position']['left']}")
            logger.info(f"   Parent: <{l['parent']}>")
            logger.info(f"   Src: {l['src']}...")
            logger.info(f"   Highlight: 🟠 ORANGE (6px outline)")
        else:
            logger.info("\n❌ BOTTOM LOGO: Not found")
        
        logger.info(f"\n📸 Screenshot: {screenshot}")
        logger.info("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
