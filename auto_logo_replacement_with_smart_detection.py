#!/usr/bin/env python3
"""
Automated Logo Replacement with Smart Detection
Combines API interception, smart logo detection, and UI automation
"""

import asyncio
from playwright.async_api import async_playwright
from smart_logo_detector import SmartLogoDetector
from datetime import datetime
import logging

# Setup logging
log_filename = f"auto_logo_replacement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SmartLogoReplacementService:
    """
    Logo replacement service with smart dynamic detection
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.template_list_page = None
        self.templates = []
        self.detector = SmartLogoDetector()
    
    async def connect_to_browser(self):
        """Connect to existing browser via CDP"""
        logger.info("=" * 80)
        logger.info("🔌 CONNECTING TO BROWSER")
        logger.info("=" * 80)
        
        self.playwright = await async_playwright().start()
        
        cdp_url = "http://localhost:9223"
        logger.info(f"Connecting to CDP: {cdp_url}")
        
        self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
        self.context = self.browser.contexts[0]
        
        logger.info(f"✅ Connected! Found {len(self.context.pages)} open tab(s)")
    
    async def navigate_to_template_list(self, base_url: str):
        """Navigate to or find template list page"""
        logger.info("=" * 80)
        logger.info("🌐 NAVIGATING TO TEMPLATE LIST")
        logger.info("=" * 80)
        
        template_list_url = f"{base_url}/templates/list"
        
        # Check if template list already open
        for page in self.context.pages:
            if template_list_url in page.url:
                self.template_list_page = page
                logger.info(f"✅ Found existing template page: {page.url}")
                break
        
        if not self.template_list_page:
            self.template_list_page = await self.context.new_page()
            await self.template_list_page.goto(template_list_url)
            await self.template_list_page.wait_for_load_state('networkidle')
            logger.info(f"✅ Navigated to: {template_list_url}")
        
        logger.info("✅ Template list page ready")
    
    async def fetch_templates_via_interception(self, max_templates: int = 10):
        """Fetch templates by intercepting API response"""
        logger.info("=" * 80)
        logger.info(f"📋 FETCHING TEMPLATES VIA API INTERCEPTION (max: {max_templates})")
        logger.info("=" * 80)
        
        templates_data = []
        response_received = asyncio.Event()
        
        async def handle_response(response):
            if '/api/templatestore/u/search' in response.url:
                try:
                    data = await response.json()
                    
                    if 'data' in data and 'hits' in data['data']:
                        hits = data['data']['hits']
                        
                        if len(hits) > 0 and len(templates_data) == 0:
                            logger.info(f"✅ Intercepted API response with {len(hits)} templates")
                            
                            for item in hits[:max_templates]:
                                template_id = item.get('templateId') or item.get('id')
                                
                                template_info = {
                                    'id': template_id,
                                    'mongodb_id': item.get('id'),
                                    'name': item.get('name', 'Unknown Template'),
                                    'type': item.get('purposeSubType', 'EMAIL'),
                                    'departments': item.get('departments', []),
                                    'status': item.get('status', 'ACTIVE')
                                }
                                templates_data.append(template_info)
                                logger.info(f\"  - {template_info['name']} (templateId: {template_info['id']})\")
                            
                            response_received.set()
                
                except Exception as e:
                    logger.error(f\"Error parsing API response: {e}\")
        
        # Listen for responses
        self.template_list_page.on('response', handle_response)
        
        # Reload to trigger API call
        logger.info(\"Reloading page to trigger API call...\")
        await self.template_list_page.reload()
        
        # Wait for response
        try:
            await asyncio.wait_for(response_received.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning(\"⚠️  Timeout waiting for API response\")
        
        # Remove listener
        self.template_list_page.remove_listener('response', handle_response)
        
        if templates_data:
            self.templates = templates_data
            logger.info(f\"✅ Successfully fetched {len(self.templates)} templates\")
            return True
        else:
            logger.warning(\"⚠️  No templates fetched\")
            return False
    
    async def open_template_tabs(self, base_url: str):
        """Open all templates in separate tabs\"\"\"
        logger.info(\"=\" * 80)
        logger.info(f\"🌐 OPENING {len(self.templates)} TEMPLATE TABS\")
        logger.info(\"=\" * 80)
        
        opened_pages = []
        
        for idx, template in enumerate(self.templates, 1):
            logger.info(f\"Opening {idx}/{len(self.templates)}: {template['name']}\")
            
            url = f\"{base_url}/templates/edit/{template['id']}\"
            logger.info(f\"  URL: {url}\")
            
            page = await self.context.new_page()
            await page.goto(url)
            await page.wait_for_load_state('networkidle')

            opened_pages.append({
                'page': page,
                'template': template
            })

            logger.info(f"  ✅ Opened")

        logger.info(f"✅ Opened {len(opened_pages)}/{len(self.templates)} template tabs")
        return opened_pages

    async def process_template_with_smart_detection(
        self,
        page,
        template_info: dict,
        old_logo_media_id: str,
        new_logo_media_id: str,
        new_logo_name: str,
        publish: bool = False
    ):
        """Process single template using smart detection"""

        logger.info(f"  Step 1: Running smart logo detection...")

        # Run smart detection
        detection_results = await self.detector.detect_logos(page)

        # Find old logo specifically
        old_logo = None
        for logo in detection_results['detected_logos']:
            if logo.get('mediaId') == old_logo_media_id:
                old_logo = logo
                logger.info(f"  ✅ Found old logo: {logo['width']}x{logo['height']} at {logo['position']['location']}")
                logger.info(f"     Detection: {logo['detection_method']} (confidence: {logo['confidence']}%)")
                break

        if not old_logo:
            logger.info("  ⚪ No old logo found - template may not have logo or already updated")
            return {'status': 'skipped', 'reason': 'no_old_logo'}

        # Replace logo using UI automation
        logger.info(f"  Step 2: Replacing logo via UI automation...")

        try:
            # Find the image element by media ID
            img_selector = f'img[src*="{old_logo_media_id}"]'

            # Wait for image to be visible
            await page.wait_for_selector(img_selector, timeout=5000)

            # Hover to reveal toolbar
            logger.info(f"  Step 3: Hovering to reveal toolbar...")
            await page.hover(img_selector)
            await asyncio.sleep(0.5)

            # Click "Change Image" button
            logger.info(f"  Step 4: Clicking Change Image...")
            change_image_btn = page.locator('button:has-text("Change Image")')
            await change_image_btn.wait_for(state='visible', timeout=3000)
            await change_image_btn.click()
            await asyncio.sleep(1)

            # Wait for media library modal
            logger.info(f"  Step 5: Waiting for media library...")
            await page.wait_for_selector('div[role="dialog"]', timeout=5000)

            # Search and select new logo
            logger.info(f"  Step 6: Selecting {new_logo_name}...")

            # Click on the new logo image in the modal
            new_logo_selector = f'img[src*="{new_logo_media_id}"]'
            await page.wait_for_selector(new_logo_selector, timeout=5000)
            await page.click(new_logo_selector)
            await asyncio.sleep(0.5)

            # Click Insert button
            logger.info(f"  Step 7: Clicking Insert...")
            insert_btn = page.locator('button:has-text("Insert")')
            await insert_btn.click()
            await asyncio.sleep(1)

            logger.info(f"  ✅ Logo replaced successfully!")

            # Center align and enlarge
            logger.info(f"  Step 8: Formatting logo (center + enlarge to 160px)...")

            # Select the new logo
            new_img_selector = f'img[src*="{new_logo_media_id}"]'
            await page.click(new_img_selector)
            await asyncio.sleep(0.5)

            # Center align (click center align button if available)
            try:
                center_btn = page.locator('button[aria-label="Center"]')
                if await center_btn.count() > 0:
                    await center_btn.click()
                    await asyncio.sleep(0.3)
                    logger.info(f"  ✅ Center aligned")
            except:
                logger.info(f"  ⚠️  Center align button not found")

            # Resize to 160px width
            try:
                # This may vary depending on the UI
                width_input = page.locator('input[aria-label*="width"], input[placeholder*="width"]')
                if await width_input.count() > 0:
                    await width_input.fill('160')
                    await asyncio.sleep(0.3)
                    logger.info(f"  ✅ Resized to 160px width")
            except:
                logger.info(f"  ⚠️  Width input not found")

            # Publish if requested
            if publish:
                logger.info(f"  Step 9: Publishing changes...")

                # Click Publish button
                publish_btn = page.locator('button:has-text("Publish")')
                await publish_btn.click()
                await asyncio.sleep(1)

                # Confirm in modal
                confirm_publish_btn = page.locator('div[role="dialog"] button:has-text("Publish")')
                if await confirm_publish_btn.count() > 0:
                    await confirm_publish_btn.click()
                    await asyncio.sleep(2)
                    logger.info(f"  ✅ Published!")
            else:
                logger.info(f"  ⏸️  Skipping publish (verification mode)")

            return {'status': 'success', 'logos_replaced': 1}

        except Exception as e:
            logger.error(f"  ❌ Error during replacement: {e}")
            return {'status': 'error', 'error': str(e)}


async def main():
    service = SmartLogoReplacementService()

    try:
        # Connect to browser
        await service.connect_to_browser()

        # Navigate to template list
        await service.navigate_to_template_list("https://preprodapp.tekioncloud.com")

        # Fetch templates via API interception
        success = await service.fetch_templates_via_interception(max_templates=10)

        if not success:
            logger.error("Failed to fetch templates")
            return

        # Open all template tabs
        opened_pages = await service.open_template_tabs("https://preprodapp.tekioncloud.com")

        # Process each template with smart detection
        logger.info("=" * 80)
        logger.info(f"🔄 PROCESSING {len(opened_pages)} TEMPLATES WITH SMART DETECTION")
        logger.info("=" * 80)

        results_summary = []

        for idx, page_info in enumerate(opened_pages, 1):
            page = page_info['page']
            template = page_info['template']

            logger.info("")
            logger.info("=" * 80)
            logger.info(f"TEMPLATE {idx}/{len(opened_pages)}: {template['name']}")
            logger.info("=" * 80)

            result = await service.process_template_with_smart_detection(
                page=page,
                template_info=template,
                old_logo_media_id="6a0c6722864813539e4da7ae",  # Old Nucar logo
                new_logo_media_id="6a19132b6697f36de6236fb1",  # New Tilton logo
                new_logo_name="Tilton.png",
                publish=False  # Verification mode
            )

            results_summary.append({
                'template': template['name'],
                'result': result
            })

            logger.info(f"  ✅ Template {idx} complete")

        # Final summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 FINAL SUMMARY")
        logger.info("=" * 80)

        success_count = sum(1 for r in results_summary if r['result']['status'] == 'success')
        skipped_count = sum(1 for r in results_summary if r['result']['status'] == 'skipped')
        error_count = sum(1 for r in results_summary if r['result']['status'] == 'error')

        logger.info(f"Total templates processed: {len(results_summary)}")
        logger.info(f"✅ Successful replacements: {success_count}")
        logger.info(f"⚪ Skipped (no logo): {skipped_count}")
        logger.info(f"❌ Errors: {error_count}")
        logger.info("")

        logger.info("🎉 All templates processed with smart detection!")

    finally:
        # Keep browser open - don't close
        pass


if __name__ == "__main__":
    asyncio.run(main())

