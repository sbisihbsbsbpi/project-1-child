#!/usr/bin/env python3
"""
Test the integrated temp_logo_adding.py on specific template
URL: https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_single_template():
    """Test the integrated logic on one template"""
    
    template_id = "667f0befd4964026ee7b6e48"
    edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    logo_media_id = "6a19132b6697f36de6236fb1"  # Tilton.png
    
    logger.info("=" * 100)
    logger.info("🧪 TESTING INTEGRATED LOGIC ON SINGLE TEMPLATE")
    logger.info("=" * 100)
    logger.info(f"Template ID: {template_id}")
    logger.info(f"URL: {edit_url}")
    logger.info("=" * 100)
    
    try:
        async with async_playwright() as playwright:
            # Connect to existing browser
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            
            # Open template
            page = await context.new_page()
            logger.info(f"\n📍 Opening template...")
            await page.goto(edit_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(5)
            
            # Import the service class
            from temp_logo_adding import TempLogoAdditionService
            
            service = TempLogoAdditionService()
            
            # Use the _process_template method directly
            template_data = {
                'templateId': template_id,
                'name': 'Test Template',
                'departments': ['Service']
            }
            
            await service._process_template(
                context=context,
                template=template_data,
                idx=1,
                total=1,
                logo_media_id=logo_media_id,
                base_url="https://preprodapp.tekioncloud.com"
            )
            
            logger.info("\n" + "=" * 100)
            logger.info("✅ TEST COMPLETE")
            logger.info("=" * 100)
            logger.info(f"Results: {service.results}")
            logger.info(f"Processed: {service.processed}")
            logger.info(f"Successful: {service.successful}")
            logger.info(f"Failed: {service.failed}")
            
    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(test_single_template())
