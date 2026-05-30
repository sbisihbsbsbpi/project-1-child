#!/usr/bin/env python3
"""
Parallel Tab Logo Warning Detection & Update Script
====================================================

LOGIC:
- NO WARNING + Logo exists → SKIP (no update needed)
- WARNING exists → UPDATE (remove & re-add)
- NO Logo → UPDATE (add logo)

FEATURES:
- Opens templates in separate tabs (parallel processing)
- Detects warnings (.templates_Image_warningIcon__hCZHMuhEmb)
- Detects logo existence (header position)
- Updates only when needed
- Keeps tabs open for manual verification
- Does NOT click publish (verification mode)
- Generates detailed report

WORKFLOW PER TEMPLATE:
1. Open template in new tab
2. Wait for full load (17 seconds)
3. Detect warning icons
4. Detect logo existence
5. Decide: SKIP or UPDATE
6. If UPDATE:
   - Remove existing logo (if has warning)
   - Add new logo/header
   - Verify success
7. Keep tab open for manual review
8. Report results

USAGE:
    python3 parallel_logo_warning_updater.py --max-templates 5
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Page
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'parallel_logo_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ParallelLogoUpdater:
    """Parallel tab manager for logo warning detection & update"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.template_list_page = None
        self.templates = []
        self.results = []
    
    async def connect_to_browser(self, debug_port: int = 9223):
        """Connect to existing browser via CDP"""
        logger.info("=" * 100)
        logger.info("🔌 CONNECTING TO BROWSER")
        logger.info("=" * 100)
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
        self.context = self.browser.contexts[0]
        
        logger.info(f"✅ Connected! Found {len(self.context.pages)} open tab(s)")
    
    async def navigate_to_template_list(self, base_url: str):
        """Navigate to template list page"""
        logger.info("=" * 100)
        logger.info("🌐 NAVIGATING TO TEMPLATE LIST")
        logger.info("=" * 100)

        try:
            # Check if template list already open
            self.template_list_page = None
            for page in self.context.pages:
                if 'templates/list' in page.url:
                    self.template_list_page = page
                    logger.info(f"✅ Found existing template list page: {page.url}")
                    break

            # If not found, open new page
            if not self.template_list_page:
                logger.info(f"Opening new page: {base_url}/templates/list")
                self.template_list_page = await self.context.new_page()
                await self.template_list_page.goto(f"{base_url}/templates/list", wait_until='domcontentloaded', timeout=60000)
                await asyncio.sleep(3)  # Wait for page load

            logger.info("✅ Template list page ready")
            return True

        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return False

    async def fetch_templates(self, max_templates: int = 5):
        """Fetch templates from API by intercepting response"""
        logger.info("=" * 100)
        logger.info(f"📋 FETCHING TEMPLATES (max: {max_templates})")
        logger.info("=" * 100)

        if not self.template_list_page:
            logger.error("❌ Template list page not available")
            return False
        
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
                                # ONLY use templateId - no fallback to id
                                template_id = item.get('templateId')

                                if not template_id:
                                    logger.error(f"⚠️  Template '{item.get('name', 'Unknown')}' missing templateId - SKIPPING")
                                    continue

                                template_info = {
                                    'id': template_id,
                                    'mongodb_id': item.get('id'),  # Keep for reference only
                                    'name': item.get('name', 'Unknown'),
                                    'departments': item.get('departments', []),
                                    'status': item.get('status', 'ACTIVE')
                                }
                                templates_data.append(template_info)
                                logger.info(f"  - {template_info['name']} (templateId: {template_id})")

                            response_received.set()
                except Exception as e:
                    logger.error(f"Error parsing API: {e}")

        self.template_list_page.on('response', handle_response)

        logger.info("Reloading page to trigger API call...")
        await self.template_list_page.reload()

        try:
            await asyncio.wait_for(response_received.wait(), timeout=15.0)
        except asyncio.TimeoutError:
            logger.warning("⚠️  Timeout waiting for API response")

        self.template_list_page.remove_listener('response', handle_response)

        self.templates = templates_data
        logger.info(f"✅ Fetched {len(self.templates)} templates")
        return len(self.templates) > 0
    
    async def open_template_tabs(self, base_url: str):
        """Open all templates in separate tabs"""
        logger.info("=" * 100)
        logger.info(f"🌐 OPENING {len(self.templates)} TEMPLATE TABS")
        logger.info("=" * 100)
        
        opened_pages = []

        for idx, template in enumerate(self.templates, 1):
            try:
                template_url = f"{base_url}/templates/edit/{template['id']}"
                logger.info(f"[{idx}/{len(self.templates)}] Opening: {template['name']}")
                logger.info(f"  URL: {template_url}")

                # Open in new tab
                new_page = await self.context.new_page()
                await new_page.goto(template_url, wait_until='domcontentloaded', timeout=60000)

                # Store page with template info
                opened_pages.append({
                    'page': new_page,
                    'template': template,
                    'url': template_url
                })

                logger.info(f"  ✅ Opened")
                await asyncio.sleep(1)  # Brief delay between opens

            except Exception as e:
                logger.error(f"  ❌ Failed: {e}")

        logger.info(f"✅ Opened {len(opened_pages)}/{len(self.templates)} tabs")
        return opened_pages

    async def wait_for_template_loaded(self, page: Page):
        """Wait for template editor to fully load with progress updates"""
        logger.info("      ⏳ Waiting for template to load...")

        try:
            # Wait for editor UI
            await page.wait_for_selector('text=/Image|Video|Button/', timeout=15000)
            await page.wait_for_function("""
                () => {
                    const spinners = document.querySelectorAll('[class*="loading"], [class*="spinner"]');
                    return spinners.length === 0 || Array.from(spinners).every(s => s.offsetParent === null);
                }
            """, timeout=10000)

            # Wait for content to render with progress
            logger.info("      🔄 Loading template content...")
            await asyncio.sleep(5)  # Template content
            logger.info("      🖼️  Loading images...")
            await asyncio.sleep(6)  # Images/logos
            logger.info("      ⚙️  Finalizing state...")
            await asyncio.sleep(6)  # Header state finalization

            logger.info("      ✅ Template fully loaded (17s total)")

        except Exception as e:
            logger.warning(f"      ⚠️  Timeout: {e}")
            await asyncio.sleep(17)  # Fallback

    async def detect_warnings_and_logo(self, page: Page) -> Dict:
        """
        Detect warning icons and logo existence
        Returns: {
            'hasWarnings': bool,
            'warningCount': int,
            'hasLogo': bool,
            'logoPosition': str (header/top/bottom),
            'headerButtonGrayed': bool
        }
        """
        logger.info("      🔍 Detecting warnings and logo...")

        # Load ignore list
        with open('logo_ignore_list.json') as f:
            ignore_list = json.load(f)

        result = await page.evaluate("""
            (ignorePatterns) => {
                const analysis = {
                    hasWarnings: false,
                    warningCount: 0,
                    warnings: [],
                    hasLogo: false,
                    logoPosition: null,
                    logoDetails: null,
                    headerButtonGrayed: false
                };

                // Helper to check if element is ignored
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

                // 1. DETECT WARNING ICONS
                const warningIcons = document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb');

                for (const icon of warningIcons) {
                    const parent = icon.closest('[class*="SortableItem"]');
                    const img = parent ? parent.querySelector('img') : null;

                    if (img && !isIgnored(img)) {
                        const rect = icon.getBoundingClientRect();
                        analysis.warnings.push({
                            position: { x: Math.round(rect.left), y: Math.round(rect.top) },
                            imageSrc: img.src.substring(0, 100)
                        });
                    }
                }

                analysis.hasWarnings = analysis.warnings.length > 0;
                analysis.warningCount = analysis.warnings.length;

                // 2. DETECT LOGO IN HEADER POSITION
                const HEADER_THRESHOLD = 600;
                const allImgs = document.querySelectorAll('img');

                for (const img of allImgs) {
                    if (isIgnored(img)) continue;

                    const src = img.src || '';
                    const rect = img.getBoundingClientRect();

                    // Look for S3 dealer logos
                    if (src.includes('amazonaws.com') && src.includes('media_')) {
                        const isReasonableSize = rect.width > 50 && rect.width < 500 &&
                                                rect.height > 20 && rect.height < 200;

                        if (isReasonableSize && rect.top < HEADER_THRESHOLD) {
                            analysis.hasLogo = true;
                            analysis.logoPosition = 'header';
                            analysis.logoDetails = {
                                src: src.substring(0, 150),
                                position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                                size: { width: Math.round(rect.width), height: Math.round(rect.height) }
                            };
                            break;
                        }
                    }
                }

                // 3. CHECK HEADER BUTTON STATE
                const headerBtn = document.querySelector('#HEADER');
                if (headerBtn) {
                    const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                    analysis.headerButtonGrayed = opacity < 1;
                }

                return analysis;
            }
        """, ignore_list['ignore_patterns'])

        logger.info(f"      📊 Results:")
        logger.info(f"         Warnings: {result['warningCount']}")
        logger.info(f"         Logo exists: {result['hasLogo']}")
        logger.info(f"         Header button grayed: {result['headerButtonGrayed']}")

        return result

    async def decide_action(self, analysis: Dict) -> str:
        """
        Decide what action to take based on analysis

        Returns: 'SKIP', 'UPDATE_REMOVE_READD', 'UPDATE_ADD_NEW'
        """
        has_warnings = analysis['hasWarnings']
        has_logo = analysis['hasLogo']

        if not has_warnings and has_logo:
            # Perfect state - no action needed
            return 'SKIP'
        elif has_warnings and has_logo:
            # Logo exists but has warnings - need to remove and re-add
            return 'UPDATE_REMOVE_READD'
        else:
            # No logo or no logo with warnings - add new
            return 'UPDATE_ADD_NEW'

    async def remove_logo_with_warning(self, page: Page) -> bool:
        """Remove logo that has warning icon"""
        logger.info("      🗑️  Removing logo with warning...")

        try:
            # Step 1: Find logo container with warning
            container_found = await page.evaluate("""
                () => {
                    const warningIcon = document.querySelector('.templates_Image_warningIcon__hCZHMuhEmb');
                    if (!warningIcon) return false;

                    const sortableItem = warningIcon.closest('[class*="SortableItem"]');
                    if (sortableItem) {
                        sortableItem.setAttribute('data-logo-to-remove', 'true');
                        return true;
                    }
                    return false;
                }
            """)

            if not container_found:
                logger.error("      ❌ Logo container not found")
                return False

            # Step 2: Hover to reveal X button
            logger.info("      Hovering to reveal remove button...")
            container = await page.query_selector('[data-logo-to-remove="true"]')
            await container.hover()
            await asyncio.sleep(1.5)

            # Step 3: Click X button
            logger.info("      Clicking remove button...")
            remove_clicked = await page.evaluate("""
                () => {
                    const container = document.querySelector('[data-logo-to-remove="true"]');
                    if (!container) return false;

                    const removeBtn = container.querySelector('[class*="removeBtn"]');
                    if (removeBtn) {
                        removeBtn.click();
                        return true;
                    }
                    return false;
                }
            """)

            if not remove_clicked:
                logger.error("      ❌ Remove button not found")
                return False

            logger.info("      ✅ Logo removed")
            await asyncio.sleep(2)

            # Step 4: Verify header button becomes active
            header_active = await page.evaluate("""
                () => {
                    const headerBtn = document.querySelector('#HEADER');
                    if (!headerBtn) return false;

                    const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                    return opacity === 1.0;
                }
            """)

            logger.info(f"      Header button active: {header_active}")
            return True

        except Exception as e:
            logger.error(f"      ❌ Error removing logo: {e}")
            return False

    async def add_header_with_logo(self, page: Page) -> bool:
        """
        Add new header using the discovered workflow:
        1. Click #HEADER button
        2. Click "+ Add Header" placeholder
        3. Select template (radio button)
        4. Click Insert
        """
        logger.info("      ➕ Adding new header with logo...")

        try:
            # Step 1: Click #HEADER button
            logger.info("      Step 1: Clicking #HEADER button...")
            header_clicked = await page.evaluate("""
                () => {
                    const headerBtn = document.querySelector('#HEADER');
                    if (!headerBtn) return false;

                    const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                    if (opacity < 1) return false;  // Not active

                    headerBtn.click();
                    return true;
                }
            """)

            if not header_clicked:
                logger.error("      ❌ #HEADER button not active or not found")
                return False

            logger.info("      ✅ #HEADER button clicked")
            await asyncio.sleep(2)

            # Step 2: Find and click "+ Add Header" placeholder
            logger.info("      Step 2: Finding '+ Add Header' button...")
            add_header_btn_found = await page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    for (const btn of buttons) {
                        if (btn.textContent.trim() === '+ Add Header') {
                            btn.setAttribute('data-add-header-btn', 'true');
                            return true;
                        }
                    }
                    return false;
                }
            """)

            if not add_header_btn_found:
                logger.error("      ❌ '+ Add Header' button not found")
                return False

            logger.info("      Clicking '+ Add Header' button...")
            add_header_btn = await page.query_selector('[data-add-header-btn="true"]')
            await add_header_btn.click()
            await asyncio.sleep(2)

            # Step 3: Verify "Insert Header" popup opened
            logger.info("      Step 3: Verifying 'Insert Header' popup...")
            popup_opened = await page.evaluate("""
                () => {
                    const modal = document.querySelector('.ant-modal');
                    if (!modal) return false;

                    const title = modal.querySelector('.ant-modal-title');
                    return title && title.textContent.includes('Insert Header');
                }
            """)

            if not popup_opened:
                logger.error("      ❌ 'Insert Header' popup not found")
                return False

            logger.info("      ✅ 'Insert Header' popup opened")

            # Step 4: Select first template (radio button)
            logger.info("      Step 4: Selecting template...")
            radio_clicked = await page.evaluate("""
                () => {
                    const modal = document.querySelector('.ant-modal');
                    if (!modal) return false;

                    const radio = modal.querySelector('input[type="radio"]');
                    if (radio) {
                        radio.click();
                        return true;
                    }
                    return false;
                }
            """)

            if not radio_clicked:
                logger.error("      ❌ Radio button not found")
                return False

            logger.info("      ✅ Template selected")
            await asyncio.sleep(1)

            # Step 5: Click Insert button
            logger.info("      Step 5: Clicking Insert...")
            insert_clicked = await page.evaluate("""
                () => {
                    const modal = document.querySelector('.ant-modal');
                    if (!modal) return false;

                    const buttons = modal.querySelectorAll('button');
                    for (const btn of buttons) {
                        if (btn.textContent.trim() === 'Insert') {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)

            if not insert_clicked:
                logger.error("      ❌ Insert button not found")
                return False

            logger.info("      ✅ Insert clicked")
            await asyncio.sleep(3)

            # Step 6: Verify header was added
            logger.info("      Step 6: Verifying header added...")
            header_added = await page.evaluate("""
                () => {
                    const headerBtn = document.querySelector('#HEADER');
                    if (!headerBtn) return false;

                    const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                    return opacity < 1;  // Should be grayed again
                }
            """)

            logger.info(f"      Header added: {header_added}")
            return header_added

        except Exception as e:
            logger.error(f"      ❌ Error adding header: {e}")
            return False

    async def process_single_template(self, page_info: Dict) -> Dict:
        """Process a single template tab"""
        page = page_info['page']
        template = page_info['template']

        logger.info("=" * 100)
        logger.info(f"🔄 PROCESSING: {template['name']}")
        logger.info(f"   ID: {template['id']}")
        logger.info("=" * 100)

        result = {
            'template_id': template['id'],
            'template_name': template['name'],
            'action': None,
            'success': False,
            'warnings_detected': 0,
            'logo_exists': False,
            'error': None
        }

        try:
            # Step 1: Wait for template to load
            await self.wait_for_template_loaded(page)

            # Step 2: Detect warnings and logo
            analysis = await self.detect_warnings_and_logo(page)

            result['warnings_detected'] = analysis['warningCount']
            result['logo_exists'] = analysis['hasLogo']

            # Step 3: Decide action
            action = await self.decide_action(analysis)
            result['action'] = action

            logger.info(f"   📋 Decision: {action}")

            if action == 'SKIP':
                logger.info("   ⏭️  SKIPPING - No warnings and logo exists")
                result['success'] = True
                result['message'] = "No update needed - template is good"

            elif action == 'UPDATE_REMOVE_READD':
                logger.info("   🔄 UPDATING - Remove and re-add logo")

                # Remove existing logo with warning
                removed = await self.remove_logo_with_warning(page)
                if not removed:
                    result['error'] = "Failed to remove logo"
                    return result

                # Add new header
                added = await self.add_header_with_logo(page)
                if added:
                    result['success'] = True
                    result['message'] = "Logo removed and re-added successfully"
                else:
                    result['error'] = "Failed to add new header"

            elif action == 'UPDATE_ADD_NEW':
                logger.info("   ➕ UPDATING - Add new logo")

                # Add new header
                added = await self.add_header_with_logo(page)
                if added:
                    result['success'] = True
                    result['message'] = "New logo added successfully"
                else:
                    result['error'] = "Failed to add new header"

            # Final verification
            if result['success']:
                logger.info("   ✅ SUCCESS")
                logger.info(f"   📝 {result['message']}")
            else:
                logger.error(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"   ❌ ERROR: {e}")
            result['error'] = str(e)

        return result

    async def process_all_templates_parallel(self, opened_pages: List[Dict]):
        """Process all template tabs in parallel"""
        logger.info("=" * 100)
        logger.info("🚀 PROCESSING ALL TEMPLATES IN PARALLEL")
        logger.info("=" * 100)

        # Create tasks for parallel processing
        tasks = []
        for page_info in opened_pages:
            task = self.process_single_template(page_info)
            tasks.append(task)

        # Run all tasks concurrently
        self.results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        for i, result in enumerate(self.results):
            if isinstance(result, Exception):
                logger.error(f"Template {i} failed with exception: {result}")
                self.results[i] = {
                    'template_id': opened_pages[i]['template']['id'],
                    'template_name': opened_pages[i]['template']['name'],
                    'action': 'ERROR',
                    'success': False,
                    'error': str(result)
                }

    async def generate_report(self):
        """Generate detailed report"""
        logger.info("=" * 100)
        logger.info("📊 GENERATING REPORT")
        logger.info("=" * 100)

        # Summary statistics
        total = len(self.results)
        skipped = sum(1 for r in self.results if r.get('action') == 'SKIP')
        updated = sum(1 for r in self.results if r.get('action') in ['UPDATE_REMOVE_READD', 'UPDATE_ADD_NEW'] and r.get('success'))
        failed = sum(1 for r in self.results if not r.get('success') and r.get('action') != 'SKIP')

        logger.info(f"\n📈 SUMMARY:")
        logger.info(f"   Total templates: {total}")
        logger.info(f"   ⏭️  Skipped (no update needed): {skipped}")
        logger.info(f"   ✅ Updated successfully: {updated}")
        logger.info(f"   ❌ Failed: {failed}")

        # Detailed results
        logger.info(f"\n📋 DETAILED RESULTS:")
        for result in self.results:
            status_emoji = "✅" if result.get('success') else ("⏭️" if result.get('action') == 'SKIP' else "❌")
            logger.info(f"\n   {status_emoji} {result.get('template_name', 'Unknown')}")
            logger.info(f"      ID: {result.get('template_id', 'Unknown')}")
            logger.info(f"      Action: {result.get('action', 'None')}")
            logger.info(f"      Warnings: {result.get('warnings_detected', 0)}")
            logger.info(f"      Logo exists: {result.get('logo_exists', False)}")
            if result.get('message'):
                logger.info(f"      Message: {result['message']}")
            if result.get('error'):
                logger.info(f"      Error: {result['error']}")

        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"logo_update_report_{timestamp}.csv"

        df = pd.DataFrame(self.results)
        df.to_csv(csv_filename, index=False)

        logger.info(f"\n💾 Report saved to: {csv_filename}")

        logger.info("\n" + "=" * 100)
        logger.info("✅ ALL TEMPLATES PROCESSED - TABS KEPT OPEN FOR VERIFICATION")
        logger.info("=" * 100)
        logger.info("\n⚠️  IMPORTANT:")
        logger.info("   - Review each tab manually")
        logger.info("   - Verify logos look correct")
        logger.info("   - DO NOT CLICK PUBLISH until verified")
        logger.info("   - Use the report CSV for tracking")
        logger.info("=" * 100)


async def main():
    """Main execution"""
    logger.info("=" * 100)
    logger.info("🚀 PARALLEL TAB LOGO WARNING UPDATER")
    logger.info("=" * 100)

    # Get max templates from command line or default to 5
    max_templates = 5
    if len(sys.argv) > 1:
        try:
            max_templates = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid number: {sys.argv[1]}, using default: 5")

    logger.info(f"Processing max {max_templates} templates\n")

    updater = ParallelLogoUpdater()

    try:
        # Step 1: Connect to browser
        await updater.connect_to_browser()

        # Step 2: Navigate to template list
        if not await updater.navigate_to_template_list("https://preprodapp.tekioncloud.com"):
            logger.error("❌ Failed to navigate to template list")
            return

        # Step 3: Fetch templates
        if not await updater.fetch_templates(max_templates=max_templates):
            logger.error("❌ Failed to fetch templates")
            return

        if not updater.templates:
            logger.error("❌ No templates fetched")
            return

        # Step 4: Open template tabs
        opened_pages = await updater.open_template_tabs("https://preprodapp.tekioncloud.com")

        if not opened_pages:
            logger.error("❌ No tabs opened")
            return

        # Step 5: Process all templates in parallel
        await updater.process_all_templates_parallel(opened_pages)

        # Step 6: Generate report
        await updater.generate_report()

        # DON'T STOP - Keep tabs open for verification
        logger.info("\n🔍 VERIFICATION MODE")
        logger.info("   Browser tabs will remain open")
        logger.info("   Press Ctrl+C when done verifying")

        # Keep script running
        while True:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("\n\n✋ Interrupted by user")
        logger.info("Tabs will remain open for continued verification")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
