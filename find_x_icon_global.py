#!/usr/bin/env python3
"""
Find X icon globally by hovering over logo and checking what appears
"""

import asyncio
import json
from playwright.async_api import async_playwright

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def main():
    logger.info("=" * 100)
    logger.info("🔍 GLOBAL SEARCH: Find X Icon After Hover")
    logger.info("=" * 100)
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        working_tab = None
        for p in context.pages:
            if 'tekioncloud.com/templates' in p.url:
                working_tab = p
                break
        
        if not working_tab:
            logger.error("❌ No Tekion tab found")
            return
        
        logger.info("✅ Using existing tab")
        
        with open('logo_ignore_list.json') as f:
            ignore_list = json.load(f)
        
        logger.info("\n📋 Step 1: Find logo and get all buttons BEFORE hover")
        
        # Get all buttons before hover
        before_buttons = await working_tab.evaluate("""
            () => {
                const allButtons = document.querySelectorAll('button, svg, i, [role="button"], [class*="icon"], [class*="Icon"], [data-action]');
                return Array.from(allButtons).map((btn, idx) => ({
                    index: idx,
                    tagName: btn.tagName,
                    className: btn.className || '',
                    visible: btn.offsetWidth > 0 && btn.offsetHeight > 0,
                    opacity: parseFloat(getComputedStyle(btn).opacity),
                    display: getComputedStyle(btn).display
                }));
            }
        """)
        
        visible_before = [b for b in before_buttons if b['visible'] and b['opacity'] > 0 and b['display'] != 'none']
        logger.info(f"   Total buttons/icons: {len(before_buttons)}")
        logger.info(f"   Visible before hover: {len(visible_before)}")
        
        logger.info("\n📋 Step 2: Hover over OUTER CONTAINER of logo using Playwright")

        # Find logo and get its outer container
        container_info = await working_tab.evaluate("""
            (ignorePatterns) => {
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

                // Find logo
                const allImgs = document.querySelectorAll('img');
                let logoImg = null;

                for (const img of allImgs) {
                    if (isIgnored(img)) continue;
                    const src = img.src || '';
                    const rect = img.getBoundingClientRect();
                    if (src.includes('amazonaws.com') && src.includes('media_')) {
                        if (rect.width > 50 && rect.height > 20 && rect.top < 600) {
                            logoImg = img;
                            break;
                        }
                    }
                }

                if (!logoImg) return null;

                // Find outer container - go up several levels
                // Try TD, TR, TABLE levels
                let container = logoImg.closest('td') ||
                               logoImg.closest('div') ||
                               logoImg.parentElement;

                // Mark it for Playwright to find
                container.setAttribute('data-logo-container-temp', 'true');

                return {
                    tagName: container.tagName,
                    className: container.className || '',
                    id: container.id || ''
                };
            }
        """, ignore_list['ignore_patterns'])

        if not container_info:
            logger.error("   ❌ Logo container not found")
            return

        logger.info(f"   ✅ Logo container: <{container_info['tagName']}>")
        if container_info['className']:
            logger.info(f"      Class: {container_info['className'][:100]}")

        # Hover over the container using Playwright
        try:
            container = await working_tab.query_selector('[data-logo-container-temp="true"]')
            if container:
                logger.info("   ✅ Hovering over outer container...")
                await container.hover()
                logger.info("   ✅ Mouse hovering over container")
                await asyncio.sleep(1.5)  # Wait for X to appear
            else:
                logger.error("   ❌ Container not found")
                return
        except Exception as e:
            logger.error(f"   ❌ Hover failed: {e}")
            return
        
        logger.info("\n📋 Step 3: Get all buttons AFTER hover and find NEW ones")
        
        after_buttons = await working_tab.evaluate("""
            () => {
                const allButtons = document.querySelectorAll('button, svg, i, [role="button"], [class*="icon"], [class*="Icon"], [data-action]');
                return Array.from(allButtons).map((btn, idx) => {
                    const rect = btn.getBoundingClientRect();
                    return {
                        index: idx,
                        tagName: btn.tagName,
                        className: btn.className || '',
                        id: btn.id || '',
                        visible: btn.offsetWidth > 0 && btn.offsetHeight > 0,
                        opacity: parseFloat(getComputedStyle(btn).opacity),
                        display: getComputedStyle(btn).display,
                        position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                        size: { width: Math.round(rect.width), height: Math.round(rect.height) },
                        innerHTML: btn.innerHTML.substring(0, 80),
                        ariaLabel: btn.getAttribute('aria-label') || ''
                    };
                });
            }
        """)
        
        visible_after = [b for b in after_buttons if b['visible'] and b['opacity'] > 0 and b['display'] != 'none']
        logger.info(f"   Total buttons/icons: {len(after_buttons)}")
        logger.info(f"   Visible after hover: {len(visible_after)}")
        
        # Find newly appeared or changed buttons
        logger.info(f"\n📊 CHANGE DETECTED: {len(visible_after) - len(visible_before)} new visible elements")
        
        if len(visible_after) > len(visible_before):
            logger.info(f"\n🆕 NEWLY VISIBLE ELEMENTS:")
            new_count = len(visible_after) - len(visible_before)
            for btn in visible_after[-new_count:]:
                logger.info(f"\n  <{btn['tagName']}>")
                if btn['className']:
                    logger.info(f"    Class: {btn['className'][:100]}")
                if btn['id']:
                    logger.info(f"    ID: {btn['id']}")
                if btn['ariaLabel']:
                    logger.info(f"    Aria-label: {btn['ariaLabel']}")
                logger.info(f"    Position: top={btn['position']['top']}, left={btn['position']['left']}")
                logger.info(f"    Size: {btn['size']['width']}x{btn['size']['height']}")
                logger.info(f"    Opacity: {btn['opacity']}")
                if btn['innerHTML']:
                    logger.info(f"    HTML: {btn['innerHTML'][:60]}...")
        
        # Also check for elements near the logo position
        logger.info(f"\n📍 ELEMENTS NEAR LOGO POSITION:")
        
        logo_pos = await working_tab.evaluate("""
            () => {
                const logo = document.querySelector('img[src*="amazonaws.com"][src*="media_"]');
                if (!logo) return null;
                const rect = logo.getBoundingClientRect();
                return { top: Math.round(rect.top), left: Math.round(rect.left), right: Math.round(rect.right), bottom: Math.round(rect.bottom) };
            }
        """)
        
        if logo_pos:
            logger.info(f"   Logo position: top={logo_pos['top']}, left={logo_pos['left']}, right={logo_pos['right']}, bottom={logo_pos['bottom']}")
            
            nearby = [b for b in visible_after if 
                     abs(b['position']['top'] - logo_pos['top']) < 100 or
                     abs(b['position']['left'] - logo_pos['left']) < 100]
            
            logger.info(f"   Found {len(nearby)} elements near logo")
            
            for btn in nearby[:10]:
                logger.info(f"\n  <{btn['tagName']}> at ({btn['position']['top']}, {btn['position']['left']})")
                if btn['className']:
                    logger.info(f"    Class: {btn['className'][:80]}")
                if btn['innerHTML']:
                    logger.info(f"    HTML: {btn['innerHTML'][:60]}...")
        
        logger.info("\n" + "=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
