#!/usr/bin/env python3
"""
Debug script to find the X icon structure
"""

import asyncio
import json
from playwright.async_api import async_playwright

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def main():
    logger.info("=" * 100)
    logger.info("🔍 DEBUG: Find X Icon Structure")
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
        
        # Load ignore list
        with open('logo_ignore_list.json') as f:
            ignore_list = json.load(f)
        
        logger.info("\n🔍 Searching for logo and ALL nearby elements...")
        
        result = await working_tab.evaluate("""
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
                
                if (!logoImg) return { success: false, error: 'Logo not found' };
                
                // Get all ancestors up to 5 levels
                const ancestors = [];
                let current = logoImg;
                for (let i = 0; i < 5 && current.parentElement; i++) {
                    current = current.parentElement;
                    ancestors.push({
                        level: i + 1,
                        tagName: current.tagName,
                        id: current.id || '',
                        className: current.className || '',
                        outerHTML: current.outerHTML.substring(0, 500)
                    });
                }
                
                // Simulate hover on each ancestor and check for buttons/icons
                logoImg.style.outline = '8px solid red';
                
                const buttonsFound = [];
                
                // Search in each ancestor
                for (let i = 0; i < ancestors.length; i++) {
                    const ancestor = current;
                    if (!ancestor) continue;
                    
                    // Find all buttons, svgs, and icons in this ancestor
                    const buttons = ancestor.querySelectorAll('button, svg, i, [class*="icon"], [class*="Icon"], [role="button"]');
                    
                    for (const btn of buttons) {
                        const btnRect = btn.getBoundingClientRect();
                        if (btnRect.width > 0 && btnRect.height > 0) {
                            buttonsFound.push({
                                ancestorLevel: i + 1,
                                tagName: btn.tagName,
                                className: btn.className || '',
                                id: btn.id || '',
                                ariaLabel: btn.getAttribute('aria-label') || '',
                                dataAction: btn.getAttribute('data-action') || '',
                                innerHTML: btn.innerHTML.substring(0, 100),
                                position: { top: Math.round(btnRect.top), left: Math.round(btnRect.left) },
                                size: { width: Math.round(btnRect.width), height: Math.round(btnRect.height) }
                            });
                        }
                    }
                    
                    current = current.parentElement;
                }
                
                return {
                    success: true,
                    ancestors: ancestors,
                    buttonsFound: buttonsFound
                };
            }
        """, ignore_list['ignore_patterns'])
        
        if not result['success']:
            logger.error(f"❌ {result.get('error')}")
            return
        
        logger.info(f"\n📦 ANCESTORS ({len(result['ancestors'])}):")
        for anc in result['ancestors']:
            logger.info(f"\n  Level {anc['level']}: <{anc['tagName']}>")
            if anc['id']:
                logger.info(f"    ID: {anc['id']}")
            if anc['className']:
                logger.info(f"    Class: {anc['className'][:100]}")
            logger.info(f"    HTML: {anc['outerHTML'][:200]}...")
        
        logger.info(f"\n\n🔘 BUTTONS/ICONS FOUND ({len(result['buttonsFound'])}):")
        for btn in result['buttonsFound']:
            logger.info(f"\n  In Ancestor Level {btn['ancestorLevel']}: <{btn['tagName']}>")
            if btn['className']:
                logger.info(f"    Class: {btn['className'][:100]}")
            if btn['id']:
                logger.info(f"    ID: {btn['id']}")
            if btn['ariaLabel']:
                logger.info(f"    Aria-label: {btn['ariaLabel']}")
            if btn['dataAction']:
                logger.info(f"    Data-action: {btn['dataAction']}")
            logger.info(f"    Position: top={btn['position']['top']}, left={btn['position']['left']}")
            logger.info(f"    Size: {btn['size']['width']}x{btn['size']['height']}")
            if btn['innerHTML']:
                logger.info(f"    HTML: {btn['innerHTML'][:80]}...")
        
        logger.info("\n" + "=" * 100)
        logger.info("💡 Look for buttons/icons that might be the delete/X button")
        logger.info("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
