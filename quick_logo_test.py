#!/usr/bin/env python3
"""
Quick test to verify logo replacement works
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("=" * 80)
    logger.info("🔍 QUICK LOGO REPLACEMENT TEST")
    logger.info("=" * 80)

    template_id = "667f0befd4964026ee7b6ea2"  # Service History Recap PDF

    async with async_playwright() as playwright:
        try:
            # Connect to existing browser
            logger.info("🌐 Connecting to browser via CDP...")
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            logger.info("✅ Connected successfully")

            # Check for existing pages
            pages = context.pages
            logger.info(f"📄 Found {len(pages)} open page(s)")
            
            # Find or create template edit page
            page = None
            for existing_page in pages:
                if template_id in existing_page.url:
                    page = existing_page
                    logger.info(f"✅ Found existing template page: {page.url[:80]}...")
                    break
            
            if not page:
                logger.info(f"📂 Opening new page for template {template_id}")
                page = await context.new_page()
                edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
                logger.info(f"🌐 Navigating to: {edit_url}")
                
                await page.goto(edit_url, wait_until='networkidle', timeout=30000)
                logger.info("⏳ Waiting 10 seconds for full load...")
                await asyncio.sleep(10)
                logger.info("✅ Page loaded")
            
            # Find logos with warnings
            logger.info("\n" + "=" * 80)
            logger.info("🔍 Searching for logos with warnings...")
            logger.info("=" * 80)
            
            logos_count = await page.evaluate("""
                () => {
                    const warningIcons = document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb');
                    return warningIcons.length;
                }
            """)
            
            logger.info(f"✅ Found {logos_count} logo(s) with warning icons")
            
            if logos_count == 0:
                logger.warning("⚠️  No logos with warnings found. Template may already be fixed!")
                logger.info("\n💡 Checking all images in template...")
                
                all_images = await page.evaluate("""
                    () => {
                        const images = document.querySelectorAll('img');
                        return Array.from(images).map(img => ({
                            src: img.src.substring(0, 100),
                            width: img.width,
                            height: img.height
                        }));
                    }
                """)
                
                logger.info(f"   Found {len(all_images)} total images:")
                for idx, img in enumerate(all_images[:10], 1):
                    logger.info(f"   {idx}. {img['width']}x{img['height']} - {img['src']}")
                
                return
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ TEST COMPLETE - Logo detection working!")
            logger.info("=" * 80)
            logger.info(f"   Found: {logos_count} logo(s) with warnings")
            logger.info(f"   Template ID: {template_id}")
            logger.info(f"   Page URL: {page.url}")
            logger.info("\n💡 Ready to proceed with logo replacement automation")
            
        except Exception as e:
            logger.error(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
