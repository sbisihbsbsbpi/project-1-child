#!/usr/bin/env python3
"""
Highlight Template #7 - ALL logos and header button in RED
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
    logger.info("🔴 HIGHLIGHTING TEMPLATE #7 - RED HIGHLIGHTS ONLY")
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
        
        logger.info("\n🔴 Highlighting ALL logos and header button in RED...")
        
        # Highlight everything in RED
        result = await working_tab.evaluate("""
            (ignorePatterns) => {
                const results = {
                    headerHighlighted: false,
                    logosHighlighted: 0,
                    logos: []
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
                
                // 1. HIGHLIGHT HEADER BUTTON IN RED
                const headerButton = document.querySelector('#HEADER');
                if (headerButton) {
                    headerButton.style.outline = '8px solid red';
                    headerButton.style.backgroundColor = 'rgba(255, 0, 0, 0.5)';
                    headerButton.style.boxShadow = '0 0 20px red';
                    results.headerHighlighted = true;
                }
                
                // 2. HIGHLIGHT LOGOS - RED for header, BLUE for top/body
                const HEADER_THRESHOLD = 600;
                const allImgs = document.querySelectorAll('img');

                for (const img of allImgs) {
                    if (isIgnored(img)) continue;

                    const src = img.src || '';
                    const rect = img.getBoundingClientRect();

                    // Find S3 logos
                    if (src.includes('amazonaws.com') && src.includes('media_')) {
                        const isReasonableSize = rect.width > 50 && rect.height > 20;

                        if (isReasonableSize) {
                            // Logo #1 (top < 600) = RED
                            // Logo #2 (top >= 600) = BLUE
                            const isHeaderLogo = rect.top < HEADER_THRESHOLD;

                            if (isHeaderLogo) {
                                // LOGO #1 - RED
                                img.style.outline = '10px solid red';
                                img.style.backgroundColor = 'rgba(255, 0, 0, 0.5)';
                                img.style.boxShadow = '0 0 30px red';
                            } else {
                                // LOGO #2 - BLUE
                                img.style.outline = '10px solid blue';
                                img.style.backgroundColor = 'rgba(0, 0, 255, 0.5)';
                                img.style.boxShadow = '0 0 30px blue';
                            }

                            results.logosHighlighted++;
                            results.logos.push({
                                position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                                size: { width: Math.round(rect.width), height: Math.round(rect.height) },
                                src: src.substring(0, 120),
                                color: isHeaderLogo ? 'RED' : 'BLUE'
                            });
                        }
                    }
                }
                
                return results;
            }
        """, ignore_list['ignore_patterns'])
        
        await asyncio.sleep(2)
        
        # Take screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot = f"template_7_red_highlights_{timestamp}.png"
        await working_tab.screenshot(path=screenshot, full_page=True)
        
        # Print results
        logger.info("\n" + "=" * 100)
        logger.info("🔴 RED HIGHLIGHTS APPLIED")
        logger.info("=" * 100)
        
        if result['headerHighlighted']:
            logger.info("\n✅ HEADER BUTTON: Highlighted in RED")
        else:
            logger.info("\n❌ HEADER BUTTON: Not found")
        
        logger.info(f"\n✅ LOGOS HIGHLIGHTED: {result['logosHighlighted']}")

        for idx, logo in enumerate(result['logos'], 1):
            color_emoji = "🔴" if logo['color'] == 'RED' else "🔵"
            logger.info(f"\n{color_emoji} LOGO #{idx} ({logo['color']}):")
            logger.info(f"   Position: top={logo['position']['top']}, left={logo['position']['left']}")
            logger.info(f"   Size: {logo['size']['width']}x{logo['size']['height']}")
            logger.info(f"   Src: {logo['src']}...")

        logger.info(f"\n📸 Screenshot: {screenshot}")
        logger.info("=" * 100)
        logger.info("\n🔴 Header button and Logo #1 are highlighted in RED")
        logger.info("🔵 Logo #2 is highlighted in BLUE")
        logger.info("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
