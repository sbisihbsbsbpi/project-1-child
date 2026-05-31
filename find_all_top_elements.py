#!/usr/bin/env python3
"""
Find ALL Elements in Top Area - Broad Search
=============================================

Searches for ALL elements (not just SortableItem) in the top header area
to find the orange-bordered logo containers from the screenshot.
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def find_all_top_elements(page):
    """Find ALL elements in top area of template"""
    
    result = await page.evaluate("""
        () => {
            const result = {
                topElements: [],
                orangeBorderedCandidates: []
            };
            
            // Find ALL divs and TDs in very top area
            const allElements = Array.from(document.querySelectorAll('div, td'));
            
            // Filter for elements in VERY top area (y < 120px based on screenshot)
            const topElements = allElements.filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.top >= 30 && rect.top < 120 && 
                       rect.width > 50 && rect.height > 20;
            });
            
            // Analyze each element
            topElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                const computedStyle = window.getComputedStyle(el);
                const hasImage = el.querySelector('img') !== null;
                const textContent = el.textContent.trim();
                
                const elementInfo = {
                    tagName: el.tagName,
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    hasImage: hasImage,
                    textLength: textContent.length,
                    textPreview: textContent.substring(0, 40),
                    className: el.className.substring(0, 100),
                    style: {
                        border: computedStyle.border,
                        borderColor: computedStyle.borderColor,
                        outline: computedStyle.outline,
                        backgroundColor: computedStyle.backgroundColor
                    },
                    childCount: el.children.length
                };
                
                result.topElements.push(elementInfo);
                
                // Check if this looks like a logo placeholder
                // (empty, reasonable size, in top header area)
                const isEmpty = !hasImage && textContent.length === 0;
                const reasonableLogoSize = rect.width >= 80 && rect.width <= 400 &&
                                          rect.height >= 30 && rect.height <= 100;
                
                if (isEmpty && reasonableLogoSize) {
                    result.orangeBorderedCandidates.push(elementInfo);
                    
                    // Mark it visually
                    el.style.outline = '10px solid lime';
                    el.style.backgroundColor = 'rgba(0, 255, 0, 0.5)';
                    el.style.boxShadow = '0 0 30px lime';
                }
            });
            
            // Sort candidates by left position
            result.orangeBorderedCandidates.sort((a, b) => a.position.left - b.position.left);
            
            return result;
        }
    """)
    
    return result


async def main():
    TARGET_URL = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48"
    
    logger.info("="*100)
    logger.info("🔍 FINDING ALL TOP ELEMENTS (BROAD SEARCH)")
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
            
            detection = await find_all_top_elements(target_page)
            
            logger.info(f"\n📊 RESULTS:")
            logger.info(f"   Total elements in top area: {len(detection['topElements'])}")
            logger.info(f"   🎯 Logo placeholder candidates: {len(detection['orangeBorderedCandidates'])}")
            
            if detection['topElements']:
                logger.info(f"\n📦 ALL TOP ELEMENTS (first 20):")
                for i, el in enumerate(detection['topElements'][:20], 1):
                    logger.info(f"\n   {i}. <{el['tagName']}>:")
                    logger.info(f"      Pos: top={el['position']['top']}px, left={el['position']['left']}px")
                    logger.info(f"      Size: {el['position']['width']}x{el['position']['height']}px")
                    logger.info(f"      Has Image: {el['hasImage']}, Text: '{el['textPreview']}'")
                    logger.info(f"      Border: {el['style']['border']}")
                    logger.info(f"      Class: {el['className'][:60]}")
            
            if detection['orangeBorderedCandidates']:
                logger.info(f"\n🎯 LOGO PLACEHOLDER CANDIDATES ({len(detection['orangeBorderedCandidates'])}):")
                for i, candidate in enumerate(detection['orangeBorderedCandidates'], 1):
                    logger.info(f"\n   Candidate #{i}:")
                    logger.info(f"      <{candidate['tagName']}> at top={candidate['position']['top']}px, left={candidate['position']['left']}px")
                    logger.info(f"      Size: {candidate['position']['width']}x{candidate['position']['height']}px")
            
            logger.info("\n" + "="*100)
            logger.info("✅ Check browser for LIME-highlighted elements!")
            logger.info("="*100)
            
        except Exception as e:
            logger.exception(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
