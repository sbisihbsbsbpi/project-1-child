#!/usr/bin/env python3
"""
Find Insert Image Button - Diagnostic Script
=============================================

Searches for any element with alt="Insert Image" or similar attributes.
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def find_insert_image_elements(page):
    """Find all elements related to Insert Image"""
    
    result = await page.evaluate("""
        () => {
            const result = {
                byAlt: [],
                byTitle: [],
                byAriaLabel: [],
                byText: [],
                allImages: []
            };
            
            // Find by alt="Insert Image"
            const byAlt = Array.from(document.querySelectorAll('[alt*="Insert Image"], [alt*="insert image"], img[alt*="Image"]'));
            byAlt.forEach(el => {
                const rect = el.getBoundingClientRect();
                const parent = el.closest('button') || el.closest('[role="button"]') || el.parentElement;
                
                result.byAlt.push({
                    tagName: el.tagName,
                    alt: el.getAttribute('alt'),
                    src: el.src ? el.src.substring(0, 80) : 'no-src',
                    position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                    visible: el.offsetParent !== null,
                    parent: {
                        tagName: parent?.tagName,
                        className: parent?.className.substring(0, 60),
                        onclick: parent?.onclick ? 'has-onclick' : 'no-onclick'
                    }
                });
                
                // Highlight it
                el.style.outline = '5px solid red';
                if (parent) parent.style.outline = '3px solid yellow';
            });
            
            // Find by title
            const byTitle = Array.from(document.querySelectorAll('[title*="Insert Image"], [title*="insert image"], [title*="Image"]'));
            byTitle.slice(0, 10).forEach(el => {
                const rect = el.getBoundingClientRect();
                result.byTitle.push({
                    tagName: el.tagName,
                    title: el.getAttribute('title'),
                    position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                    visible: el.offsetParent !== null
                });
            });
            
            // Find by aria-label
            const byAriaLabel = Array.from(document.querySelectorAll('[aria-label*="Insert Image"], [aria-label*="insert image"], [aria-label*="Image"]'));
            byAriaLabel.slice(0, 10).forEach(el => {
                const rect = el.getBoundingClientRect();
                result.byAriaLabel.push({
                    tagName: el.tagName,
                    ariaLabel: el.getAttribute('aria-label'),
                    position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                    visible: el.offsetParent !== null
                });
            });
            
            // Find buttons with "image" text
            const allButtons = Array.from(document.querySelectorAll('button, [role="button"]'));
            allButtons.forEach(btn => {
                const text = btn.textContent.toLowerCase();
                if (text.includes('image') && text.includes('insert')) {
                    const rect = btn.getBoundingClientRect();
                    result.byText.push({
                        tagName: btn.tagName,
                        text: btn.textContent.substring(0, 50),
                        position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                        visible: btn.offsetParent !== null
                    });
                }
            });
            
            // All images in toolbar area (top 200px)
            const allImgs = Array.from(document.querySelectorAll('img'));
            allImgs.forEach(img => {
                const rect = img.getBoundingClientRect();
                if (rect.top < 200 && rect.top > 60) {  // Toolbar area
                    result.allImages.push({
                        alt: img.alt,
                        src: img.src.substring(0, 80),
                        position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                        size: { width: Math.round(rect.width), height: Math.round(rect.height) }
                    });
                }
            });
            
            return result;
        }
    """)
    
    return result


async def main():
    TARGET_URL = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48"
    
    logger.info("="*100)
    logger.info("🔍 FINDING INSERT IMAGE BUTTON")
    logger.info("="*100)
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            
            target_page = None
            for page in context.pages:
                if TARGET_URL in page.url:
                    target_page = page
                    break
            
            if not target_page:
                logger.error("❌ Template not found!")
                return
            
            await target_page.bring_to_front()
            await asyncio.sleep(2)
            
            # First, click a logo container to select it
            logger.info("\n📍 Selecting logo container first...")
            await target_page.evaluate("""
                () => {
                    const tables = Array.from(document.querySelectorAll('table'));
                    for (const table of tables) {
                        const tds = Array.from(table.querySelector('tr')?.querySelectorAll('td') || []);
                        if (tds.length === 3) {
                            const container = tds[0].querySelector('[class*="elementContainer"]');
                            if (container) {
                                container.click();
                                container.focus();
                                return true;
                            }
                        }
                    }
                }
            """)
            await asyncio.sleep(1)
            logger.info("✅ Container selected")
            
            result = await find_insert_image_elements(target_page)
            
            logger.info(f"\n📊 RESULTS:")
            logger.info(f"   By alt attribute: {len(result['byAlt'])}")
            logger.info(f"   By title attribute: {len(result['byTitle'])}")
            logger.info(f"   By aria-label: {len(result['byAriaLabel'])}")
            logger.info(f"   By text: {len(result['byText'])}")
            logger.info(f"   All toolbar images: {len(result['allImages'])}")
            
            if result['byAlt']:
                logger.info(f"\n🎯 ELEMENTS WITH alt='Insert Image':")
                for i, el in enumerate(result['byAlt'], 1):
                    logger.info(f"\n   {i}. <{el['tagName']}>:")
                    logger.info(f"      alt: '{el['alt']}'")
                    logger.info(f"      src: {el['src']}")
                    logger.info(f"      Position: top={el['position']['top']}px, left={el['position']['left']}px")
                    logger.info(f"      Visible: {el['visible']}")
                    logger.info(f"      Parent: <{el['parent']['tagName']}> {el['parent']['className'][:40]}")
            
            if result['allImages']:
                logger.info(f"\n📸 ALL TOOLBAR IMAGES (top 10):")
                for i, img in enumerate(result['allImages'][:10], 1):
                    logger.info(f"   {i}. alt='{img['alt']}' @ top={img['position']['top']}px")
            
            logger.info("\n" + "="*100)
            logger.info("✅ Check browser - elements with alt should have RED outline!")
            logger.info("="*100)
            
        except Exception as e:
            logger.exception(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
