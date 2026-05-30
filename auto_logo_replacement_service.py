#!/usr/bin/env python3
"""
Automated Logo Replacement Service
Follows the Tekion logo removal pattern but adds/replaces logos instead
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Page, Browser
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'auto_logo_replacement_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutoLogoReplacementService:
    """Automated logo replacement service - fetches templates and processes them"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.template_list_page = None
        self.templates = []
        
    async def connect_to_browser(self, debug_port: int = 9223):
        """Connect to browser via CDP"""
        logger.info("=" * 80)
        logger.info("🔌 CONNECTING TO BROWSER")
        logger.info("=" * 80)
        
        try:
            self.playwright = await async_playwright().start()
            cdp_url = f"http://localhost:{debug_port}"
            
            logger.info(f"Connecting to CDP: {cdp_url}")
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            self.context = self.browser.contexts[0]
            
            logger.info(f"✅ Connected! Found {len(self.context.pages)} open tab(s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    async def navigate_to_template_list(self, base_url: str):
        """Navigate to template list page"""
        logger.info("=" * 80)
        logger.info("🌐 NAVIGATING TO TEMPLATE LIST")
        logger.info("=" * 80)
        
        try:
            # Check if template list already open
            for page in self.context.pages:
                if 'templates' in page.url:
                    self.template_list_page = page
                    logger.info(f"✅ Found existing template page: {page.url}")
                    break
            
            # If not found, open new page
            if not self.template_list_page:
                logger.info(f"Opening new page: {base_url}/templates/list")
                self.template_list_page = await self.context.new_page()
                await self.template_list_page.goto(f"{base_url}/templates/list")
                await asyncio.sleep(3.0)  # Wait for page load
            
            logger.info("✅ Template list page ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return False
    
    async def fetch_templates_from_api(self, max_templates: int = 10):
        """
        Fetch templates by intercepting the API response when page loads
        """
        logger.info("=" * 80)
        logger.info(f"📋 FETCHING TEMPLATES (max: {max_templates})")
        logger.info("=" * 80)

        try:
            templates_data = []
            response_received = asyncio.Event()

            # Set up API response interception
            async def handle_response(response):
                if '/api/templatestore/u/search' in response.url:
                    try:
                        data = await response.json()

                        # Extract template data
                        if 'data' in data and 'hits' in data['data']:
                            hits = data['data']['hits']

                            if len(hits) > 0 and len(templates_data) == 0:  # Only process first valid response
                                logger.info(f"✅ Intercepted API response with {len(hits)} templates")

                                for item in hits[:max_templates]:
                                    # Use templateId for the edit URL
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
                                    logger.info(f"  - {template_info['name']} (templateId: {template_info['id']})")

                                response_received.set()  # Signal that we got data

                    except Exception as e:
                        logger.error(f"Error parsing API response: {e}")

            # Listen for responses
            self.template_list_page.on('response', handle_response)

            # Reload page to trigger API call
            logger.info("Reloading page to trigger API call...")
            await self.template_list_page.reload()

            # Wait for response (max 10 seconds)
            try:
                await asyncio.wait_for(response_received.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("⚠️  Timeout waiting for API response")

            # Remove listener
            self.template_list_page.remove_listener('response', handle_response)

            if templates_data:
                self.templates = templates_data
                logger.info(f"✅ Successfully fetched {len(self.templates)} templates")
                return True
            else:
                logger.warning("⚠️  No templates fetched")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to fetch templates: {e}")
            return False

    async def open_template_tabs(self, base_url: str):
        """Open template edit pages in new tabs"""
        logger.info("=" * 80)
        logger.info(f"🌐 OPENING {len(self.templates)} TEMPLATE TABS")
        logger.info("=" * 80)

        opened_pages = []

        for idx, template in enumerate(self.templates, 1):
            try:
                template_url = f"{base_url}/templates/edit/{template['id']}"
                logger.info(f"Opening {idx}/{len(self.templates)}: {template['name']}")
                logger.info(f"  URL: {template_url}")

                # Open in new tab
                new_page = await self.context.new_page()
                await new_page.goto(template_url)
                await asyncio.sleep(2.0)  # Wait for page load

                opened_pages.append({
                    'page': new_page,
                    'template': template,
                    'url': template_url
                })

                logger.info(f"  ✅ Opened")

            except Exception as e:
                logger.error(f"  ❌ Failed to open template {template['id']}: {e}")

        logger.info(f"✅ Opened {len(opened_pages)}/{len(self.templates)} template tabs")
        return opened_pages

    async def replace_logo_in_template(
        self,
        page: Page,
        old_logo_media_id: str,
        new_logo_media_id: str,
        new_logo_name: str
    ) -> bool:
        """Replace logo in a single template page"""

        try:
            # Step 1: Find old logo
            logger.info("  Step 1: Finding old logo...")

            logo_found = await page.evaluate(f"""
                () => {{
                    const OLD_ID = "{old_logo_media_id}";
                    const images = Array.from(document.querySelectorAll('img'));

                    for (const img of images) {{
                        if (img.src.includes(OLD_ID)) {{
                            img.setAttribute('data-old-logo', 'true');
                            img.style.outline = '5px solid red';

                            let container = img.parentElement;
                            for (let i = 0; i < 5; i++) {{
                                if (!container) break;
                                const cls = container.className || '';
                                if (cls.includes('resizable') || cls.includes('imageComponent')) {{
                                    container.setAttribute('data-logo-container', 'true');
                                    container.style.outline = '5px solid orange';
                                    return true;
                                }}
                                container = container.parentElement;
                            }}

                            if (img.parentElement) {{
                                img.parentElement.setAttribute('data-logo-container', 'true');
                                img.parentElement.style.outline = '5px solid orange';
                                return true;
                            }}
                        }}
                    }}
                    return false;
                }}
            """)

            if not logo_found:
                logger.info("  ⚠️  Old logo not found - may already be updated")
                return True  # Not an error, just skip

            logger.info("  ✅ Old logo found")

            # Step 2: Hover to reveal toolbar
            logger.info("  Step 2: Hovering to reveal toolbar...")
            container = await page.query_selector('[data-logo-container="true"]')
            await container.hover()
            await asyncio.sleep(1.5)
            logger.info("  ✅ Toolbar revealed")

            # Step 3: Click Change Image
            logger.info("  Step 3: Clicking Change Image...")
            change_clicked = await page.evaluate("""
                () => {
                    const btn = document.querySelector('[title="Change Image"]') ||
                               document.querySelector('[aria-label="icon-switch"]');
                    if (btn) {
                        btn.click();
                        return true;
                    }
                    return false;
                }
            """)

            if not change_clicked:
                logger.error("  ❌ Change Image button not found")
                return False

            logger.info("  ✅ Change Image clicked")
            await asyncio.sleep(2.5)

            # Step 4: Select new logo
            logger.info(f"  Step 4: Selecting {new_logo_name}...")
            new_logo_clicked = await page.evaluate(f"""
                () => {{
                    const NEW_ID = "{new_logo_media_id}";
                    const images = Array.from(document.querySelectorAll('img'));

                    for (const img of images) {{
                        if (img.src.includes(NEW_ID)) {{
                            const parent = img.closest('div[class]');
                            if (parent) parent.click();
                            else img.click();
                            return true;
                        }}
                    }}
                    return false;
                }}
            """)

            if not new_logo_clicked:
                logger.error(f"  ❌ {new_logo_name} not found")
                return False

            logger.info(f"  ✅ {new_logo_name} selected")
            await asyncio.sleep(1.0)

            # Step 5: Click Insert
            logger.info("  Step 5: Clicking Insert...")
            insert_clicked = await page.evaluate("""
                () => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    for (const btn of btns) {
                        if (btn.innerText === 'Insert') {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)

            if not insert_clicked:
                logger.error("  ❌ Insert button not found")
                return False

            logger.info("  ✅ Insert clicked")
            await asyncio.sleep(2.0)

            logger.info("  ✅ Logo replacement complete")
            return True

        except Exception as e:
            logger.error(f"  ❌ Logo replacement failed: {e}")
            return False

    async def center_and_enlarge_logo(self, page: Page, new_logo_media_id: str, target_width: int = 160) -> bool:
        """Center align and enlarge the new logo"""

        try:
            # Find new logo
            logger.info("  Step 6: Center aligning logo...")

            logo_found = await page.evaluate(f"""
                () => {{
                    const NEW_ID = "{new_logo_media_id}";
                    const images = Array.from(document.querySelectorAll('img'));

                    for (const img of images) {{
                        if (img.src.includes(NEW_ID)) {{
                            const rect = img.getBoundingClientRect();
                            if (rect.width < 200) {{
                                img.setAttribute('data-new-logo', 'true');

                                let container = img.parentElement;
                                for (let i = 0; i < 5; i++) {{
                                    if (!container) break;
                                    if ((container.className || '').includes('resizable')) {{
                                        container.setAttribute('data-new-logo-container', 'true');
                                        return true;
                                    }}
                                    container = container.parentElement;
                                }}

                                if (img.parentElement) {{
                                    img.parentElement.setAttribute('data-new-logo-container', 'true');
                                    return true;
                                }}
                            }}
                        }}
                    }}
                    return false;
                }}
            """)

            if not logo_found:
                logger.warning("  ⚠️  New logo not found for alignment")
                return False

            # Hover to reveal toolbar
            container = await page.query_selector('[data-new-logo-container="true"]')
            await container.hover()
            await asyncio.sleep(1.5)

            # Click center align
            center_clicked = await page.evaluate("""
                () => {
                    const centerBtn = document.querySelector('[title="Center Align"]') ||
                                     document.querySelector('[aria-label="icon-center-align"]');
                    if (centerBtn) {
                        centerBtn.click();
                        return true;
                    }
                    return false;
                }
            """)

            if center_clicked:
                logger.info("  ✅ Logo centered")
            else:
                logger.warning("  ⚠️  Center align button not found")

            await asyncio.sleep(1.0)

            # Enlarge logo
            logger.info(f"  Step 7: Enlarging logo to {target_width}px...")

            result = await page.evaluate(f"""
                () => {{
                    const NEW_ID = "{new_logo_media_id}";
                    const targetWidth = {target_width};

                    const img = Array.from(document.querySelectorAll('img'))
                        .find(i => i.src.includes(NEW_ID) && i.getBoundingClientRect().width < 200);

                    if (!img) return {{ success: false }};

                    const beforeRect = img.getBoundingClientRect();
                    const before = {{
                        width: Math.round(beforeRect.width),
                        height: Math.round(beforeRect.height)
                    }};

                    let container = img.parentElement;
                    for (let i = 0; i < 5; i++) {{
                        if (!container) break;
                        if ((container.className || '').includes('resizable')) break;
                        container = container.parentElement;
                    }}

                    if (!container) container = img.parentElement;

                    container.style.width = targetWidth + 'px';
                    container.style.maxWidth = targetWidth + 'px';

                    img.style.width = targetWidth + 'px';
                    img.style.maxWidth = targetWidth + 'px';
                    img.style.height = 'auto';

                    container.offsetHeight;

                    const afterRect = img.getBoundingClientRect();
                    const after = {{
                        width: Math.round(afterRect.width),
                        height: Math.round(afterRect.height)
                    }};

                    return {{
                        success: true,
                        before: before,
                        after: after
                    }};
                }}
            """)

            if result.get('success'):
                before = result['before']
                after = result['after']
                logger.info(f"  ✅ Logo enlarged: {before['width']}x{before['height']} → {after['width']}x{after['height']}")
                return True
            else:
                logger.warning("  ⚠️  Failed to enlarge logo")
                return False

        except Exception as e:
            logger.error(f"  ❌ Center/enlarge failed: {e}")
            return False

    async def process_all_templates(
        self,
        base_url: str,
        old_logo_media_id: str,
        new_logo_media_id: str,
        new_logo_name: str,
        max_templates: int = 10,
        publish: bool = False
    ):
        """Main workflow - fetch and process templates"""

        logger.info("=" * 80)
        logger.info("🚀 AUTOMATED LOGO REPLACEMENT - FULL WORKFLOW")
        logger.info("=" * 80)
        logger.info(f"Max templates: {max_templates}")
        logger.info(f"Publish: {publish}")
        logger.info("=" * 80)

        # Step 1: Connect
        if not await self.connect_to_browser():
            return []

        # Step 2: Navigate to template list
        if not await self.navigate_to_template_list(base_url):
            return []

        # Step 3: Fetch templates
        if not await self.fetch_templates_from_api(max_templates):
            return []

        # Step 4: Open template tabs
        opened_pages = await self.open_template_tabs(base_url)

        if not opened_pages:
            logger.error("❌ No templates opened")
            return []

        # Step 5: Process each template
        logger.info("=" * 80)
        logger.info(f"🔄 PROCESSING {len(opened_pages)} TEMPLATES SEQUENTIALLY")
        logger.info("=" * 80)

        results = []

        for idx, page_info in enumerate(opened_pages, 1):
            page = page_info['page']
            template = page_info['template']

            logger.info("")
            logger.info("=" * 80)
            logger.info(f"TEMPLATE {idx}/{len(opened_pages)}: {template['name']}")
            logger.info("=" * 80)

            try:
                # Replace logo
                replace_success = await self.replace_logo_in_template(
                    page,
                    old_logo_media_id,
                    new_logo_media_id,
                    new_logo_name
                )

                if not replace_success:
                    logger.warning(f"⚠️  Logo replacement skipped or failed for {template['name']}")
                    results.append({
                        'template': template['name'],
                        'status': 'skipped',
                        'success': False
                    })
                    continue

                # Center and enlarge
                await self.center_and_enlarge_logo(page, new_logo_media_id, 160)

                # Note: Not publishing as per verification mode
                if not publish:
                    logger.info("  ⏸️  Skipping publish (verification mode)")

                results.append({
                    'template': template['name'],
                    'status': 'success',
                    'success': True
                })

                logger.info(f"  ✅ Template {idx} complete")

            except Exception as e:
                logger.error(f"  ❌ Error processing template: {e}")
                results.append({
                    'template': template['name'],
                    'status': 'error',
                    'success': False,
                    'error': str(e)
                })

        # Summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 PROCESSING SUMMARY")
        logger.info("=" * 80)

        for idx, result in enumerate(results, 1):
            status_icon = "✅" if result['success'] else "❌"
            logger.info(f"{idx}. {status_icon} {result['template']} - {result['status']}")

        successful = sum(1 for r in results if r['success'])
        logger.info("")
        logger.info(f"Total: {successful}/{len(results)} successful")
        logger.info("")
        logger.info("🔍 VERIFICATION MODE: All tabs kept open for manual review")
        logger.info("   Please check each template in the browser tabs")
        logger.info("")

        return results


async def main():
    """Main entry point"""

    service = AutoLogoReplacementService()

    results = await service.process_all_templates(
        base_url="https://preprodapp.tekioncloud.com",
        old_logo_media_id="6a0c6722864813539e4da7ae",  # Old Nucar logo
        new_logo_media_id="6a19132b6697f36de6236fb1",  # Tilton logo
        new_logo_name="Tilton.png",
        max_templates=10,
        publish=False  # Verification mode
    )

    return results


if __name__ == "__main__":
    results = asyncio.run(main())

    successful = sum(1 for r in results if r['success'])
    total = len(results)

    if successful == total:
        print(f"\n🎉 All {total} templates processed successfully!")
        exit(0)
    else:
        print(f"\n⚠️  {successful}/{total} templates processed successfully")
        exit(1)
