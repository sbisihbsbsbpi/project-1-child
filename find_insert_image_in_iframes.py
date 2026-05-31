#!/usr/bin/env python3
"""
Find Insert Image in iframes
=============================

Searches for "Insert Image" across all iframes on the page.
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    TARGET_URL = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48"
    
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
            
            # Select container first
            logger.info("\n📍 Selecting container...")
            await target_page.evaluate("""
                () => {
                    const tables = Array.from(document.querySelectorAll('table'));
                    for (const table of tables) {
                        const tds = Array.from(table.querySelector('tr')?.querySelectorAll('td') || []);
                        if (tds.length === 3) {
                            const container = tds[0].querySelector('[class*="elementContainer"]');
                            if (container) {
                                container.click();
                                return true;
                            }
                        }
                    }
                }
            """)
            await asyncio.sleep(2)
            
            # Check main page
            logger.info("\n🔍 Searching main page...")
            main_result = await target_page.evaluate("""
                () => {
                    const all = Array.from(document.querySelectorAll('*'));
                    const matches = [];
                    
                    for (const el of all) {
                        const text = el.textContent?.trim() || '';
                        if (text === 'Insert Image' || text.toLowerCase().includes('insert image')) {
                            const rect = el.getBoundingClientRect();
                            matches.push({
                                tagName: el.tagName,
                                text: text.substring(0, 50),
                                className: el.className.substring(0, 60),
                                position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                                visible: el.offsetParent !== null
                            });
                        }
                    }
                    
                    return matches;
                }
            """)
            
            logger.info(f"   Found {len(main_result)} matches on main page")
            for i, match in enumerate(main_result[:5], 1):
                logger.info(f"   {i}. <{match['tagName']}> '{match['text']}' @ top={match['position']['top']}px, visible={match['visible']}")
            
            # Check all iframes
            frames = target_page.frames
            logger.info(f"\n🖼️  Found {len(frames)} frames total")
            
            for i, frame in enumerate(frames):
                logger.info(f"\n   Frame {i}: {frame.url[:80] if frame.url else 'no-url'}")
                
                try:
                    frame_result = await frame.evaluate("""
                        () => {
                            const all = Array.from(document.querySelectorAll('*'));
                            const matches = [];
                            
                            for (const el of all) {
                                const text = el.textContent?.trim() || '';
                                if (text === 'Insert Image' || (text.toLowerCase().includes('insert') && text.toLowerCase().includes('image'))) {
                                    const rect = el.getBoundingClientRect();
                                    matches.push({
                                        tagName: el.tagName,
                                        text: text.substring(0, 50),
                                        position: { top: Math.round(rect.top), left: Math.round(rect.left) }
                                    });
                                }
                            }
                            
                            return matches.slice(0, 10);
                        }
                    """)
                    
                    if frame_result:
                        logger.info(f"      ✅ Found {len(frame_result)} matches in this frame!")
                        for match in frame_result[:3]:
                            logger.info(f"         <{match['tagName']}> '{match['text']}'")
                except Exception as e:
                    logger.info(f"      ⚠️  Could not access frame: {str(e)[:50]}")
            
            logger.info("\n" + "="*100)
            logger.info("✅ Search complete!")
            logger.info("="*100)
            
        except Exception as e:
            logger.exception(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
