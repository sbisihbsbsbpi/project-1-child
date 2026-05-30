#!/usr/bin/env python3
"""
Process Logo Replacement on Already-Opened Templates
====================================================

This script processes logos on templates that are ALREADY open in the browser.
Instead of opening new tabs, it uses the existing tabs from filter_and_open_templates.py

Author: Automation Team
Date: 2026-05-30
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright, Page

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_open_template_tabs(context):
    """Find all open template edit pages"""

    logger.info("🔍 Scanning browser for open template tabs...")

    template_tabs = []
    for page in context.pages:
        url = page.url
        if '/templates/edit/' in url:
            # Extract template ID from URL
            template_id = url.split('/templates/edit/')[-1].split('?')[0]

            # Get page title for template name
            try:
                title = await page.title()
            except:
                title = f"Template {template_id}"

            template_tabs.append({
                'page': page,
                'templateId': template_id,
                'url': url,
                'title': title
            })

    logger.info(f"✅ Found {len(template_tabs)} open template tabs")
    return template_tabs


async def replace_logo(page: Page, logo_idx: int, logo_media_id: str) -> bool:
    """Replace a single logo"""

    try:
        # Step 1: Hover over logo to reveal toolbar
        container = await page.query_selector(f'[data-logo-to-inspect="logo-{logo_idx}"]')
        if not container:
            logger.warning(f"      Logo container not found")
            return False

        await container.hover(force=True)
        await asyncio.sleep(3)

        # Step 2: Click "Change Image" icon
        popup_already_open = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') ||
                             document.querySelector('.ant-modal');
                return popup && popup.getBoundingClientRect().width > 0;
            }
        """)

        if not popup_already_open:
            change_clicked = await page.evaluate(f"""
                () => {{
                    const container = document.querySelector('[data-logo-to-inspect="logo-{logo_idx}"]');
                    if (!container) return {{ clicked: false }};

                    const changeIcon = container.querySelector('[aria-label="icon-switch"]') ||
                                      container.querySelector('[title="Change Image"]');

                    if (changeIcon) {{
                        changeIcon.click();
                        return {{ clicked: true }};
                    }}
                    return {{ clicked: false }};
                }}
            """)

            if not change_clicked['clicked']:
                logger.warning("      Change Image icon not found")
                return False

            await asyncio.sleep(3)

        # Step 3: Select Tilton.png (tile #1)
        selection_result = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') ||
                             document.querySelector('.ant-modal');
                if (!popup) return { success: false, reason: 'No popup' };

                const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                if (tiles.length === 0) return { success: false, reason: 'No tiles found' };

                const targetTile = tiles[0];
                const topLayer = targetTile.querySelector('[role="button"]') ||
                                targetTile.querySelector('[class*="topLayer"]');

                if (topLayer) {
                    topLayer.click();
                    return { success: true, tile: 1 };
                }

                return { success: false, reason: 'No clickable layer' };
            }
        """)

        if not selection_result['success']:
            logger.warning(f"      Selection failed: {selection_result.get('reason')}")
            return False

        await asyncio.sleep(1.5)

        # Step 4: Click INSERT button
        insert_result = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') ||
                             document.querySelector('.ant-modal');
                if (!popup) return { clicked: false };

                const buttons = Array.from(popup.querySelectorAll('button'));
                const insertBtn = buttons.find(b =>
                    b.textContent.trim().toLowerCase().includes('insert')
                );

                if (insertBtn && !insertBtn.disabled) {
                    insertBtn.click();
                    return { clicked: true };
                }
                return { clicked: false };
            }
        """)

        if not insert_result['clicked']:
            logger.warning("      INSERT button not found or disabled")
            return False

        await asyncio.sleep(2)

        # Step 5: Verify popup closed
        popup_closed = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') ||
                             document.querySelector('.ant-modal');
                return !popup || popup.getBoundingClientRect().width === 0;
            }
        """)

        return popup_closed

    except Exception as e:
        logger.exception(f"      Error replacing logo: {e}")
        return False


async def add_header_with_logo(page: Page) -> bool:
    """
    Add new header using the discovered workflow (from parallel_logo_warning_updater.py).
    Used for templates without logo containers (e.g., CPRA templates).
    """
    logger.info("      ➕ Adding new header with logo...")

    try:
        # Step 1: Wait for #HEADER button to become active
        logger.info("      Step 1: Checking #HEADER button state...")

        button_state = await page.evaluate("""
            () => {
                const headerBtn = document.querySelector('#HEADER');
                if (!headerBtn) return { found: false };

                const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                return {
                    found: true,
                    opacity: opacity,
                    active: opacity === 1.0
                };
            }
        """)

        if not button_state['found']:
            logger.error("      ❌ #HEADER button not found in DOM")
            return False

        if not button_state['active']:
            logger.error(f"      ❌ #HEADER button is grayed (opacity={button_state['opacity']})")
            return False

        logger.info(f"      ✅ #HEADER button is active (opacity={button_state['opacity']})")

        # Click the button
        header_clicked = await page.evaluate("""
            () => {
                const headerBtn = document.querySelector('#HEADER');
                if (!headerBtn) return false;
                headerBtn.click();
                return true;
            }
        """)

        if not header_clicked:
            logger.error("      ❌ Failed to click #HEADER button")
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


async def process_template_tab(page: Page, template_info: dict, idx: int, total: int):
    """Process logos in a single template tab - with two-check system"""

    logger.info(f"\n{'='*100}")
    logger.info(f"📄 TEMPLATE {idx}/{total}: {template_info['title'][:60]}")
    logger.info(f"   ID: {template_info['templateId']}")
    logger.info(f"   URL: {template_info['url'][:80]}")
    logger.info(f"{'='*100}")

    template_id = template_info['templateId']

    try:
        # Bring page to front
        await page.bring_to_front()
        await asyncio.sleep(2)

        # ============================================================
        # CHECK #1: Look for logo containers (warning icons)
        # ============================================================
        logos_info = await page.evaluate("""
            () => {
                const warnings = Array.from(
                    document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb')
                );

                if (warnings.length === 0) return { found: false, count: 0 };

                warnings.forEach((icon, idx) => {
                    const sortableItem = icon.closest('[class*="SortableItem"]');
                    if (sortableItem) {
                        sortableItem.setAttribute('data-logo-to-inspect', `logo-${idx + 1}`);
                    }
                });

                return { found: true, count: warnings.length };
            }
        """)

        if logos_info['found']:
            # Has logo containers - process normally
            logger.info(f"   ✅ Found {logos_info['count']} logo(s) with warnings")

            # Process each logo
            logos_processed = 0
            for logo_idx in range(1, logos_info['count'] + 1):
                logger.info(f"\n   🎯 Processing logo {logo_idx}/{logos_info['count']}...")

                success = await replace_logo(page, logo_idx, "6a19132b6697f36de6236fb1")

                if success:
                    logos_processed += 1
                    logger.info(f"   ✅ Logo {logo_idx} replaced successfully")
                else:
                    logger.warning(f"   ⚠️  Logo {logo_idx} replacement failed")

            # Return results
            if logos_processed == logos_info['count']:
                status = 'success'
            elif logos_processed > 0:
                status = 'partial'
            else:
                status = 'failed'

            logger.info(f"\n   ✅ Template complete: {logos_processed}/{logos_info['count']} logos replaced")

            return {
                'template': template_info['title'],
                'id': template_id,
                'status': status,
                'action': 'logo_replacement',
                'logos_found': logos_info['count'],
                'logos_processed': logos_processed
            }

        # ============================================================
        # No logo containers detected - TWO MORE CHECKS NEEDED
        # ============================================================

        # CHECK #2A: Is this a CPRA template? (naming convention)
        is_cpra_template = template_id.startswith('CPRA_')

        if is_cpra_template:
            logger.info(f"   ℹ️  CPRA template detected: {template_id}")

        # CHECK #2B: Check header button state
        logger.info("   🔍 No logos with warnings - checking header button state...")
        button_state = await page.evaluate("""
            () => {
                const btn = document.querySelector('#HEADER');
                if (!btn) return { found: false };

                const opacity = parseFloat(getComputedStyle(btn).opacity);
                return {
                    found: true,
                    opacity: opacity,
                    isGrayed: opacity < 1.0,
                    isActive: opacity === 1.0
                };
            }
        """)

        if not button_state['found']:
            logger.error("   ❌ #HEADER button not found")
            return {
                'template': template_info['title'],
                'id': template_id,
                'status': 'error',
                'reason': 'Header button not found',
                'logos_processed': 0
            }

        if button_state['isGrayed']:
            # Has header structure (just no logos with warnings)
            logger.info(f"   ℹ️  Header exists (opacity={button_state['opacity']}) - skipping")
            return {
                'template': template_info['title'],
                'id': template_id,
                'status': 'skipped',
                'reason': 'Header exists, no logos with warnings',
                'logos_processed': 0
            }

        elif button_state['isActive']:
            # No header structure - ADD header with logo
            logger.info(f"   ➕ No header (opacity={button_state['opacity']}) - adding header...")

            added = await add_header_with_logo(page)

            if added:
                logger.info("   ✅ Header added successfully")
                return {
                    'template': template_info['title'],
                    'id': template_id,
                    'status': 'success',
                    'action': 'header_added',
                    'logos_processed': 1  # Count as 1 logo added
                }
            else:
                logger.error("   ❌ Failed to add header")
                return {
                    'template': template_info['title'],
                    'id': template_id,
                    'status': 'failed',
                    'reason': 'Header addition failed',
                    'logos_processed': 0
                }

    except Exception as e:
        logger.exception(f"   ❌ Error processing template: {e}")
        return {
            'template': template_info['title'],
            'id': template_info['templateId'],
            'status': 'error',
            'error': str(e),
            'logos_processed': 0
        }


async def main():
    """Main entry point"""

    start_time = datetime.now()
    results = []

    logger.info("=" * 100)
    logger.info("🚀 PROCESS LOGOS ON ALREADY-OPENED TEMPLATES (WITH TWO-CHECK SYSTEM)")
    logger.info("=" * 100)
    logger.info("Logo Media ID: 6a19132b6697f36de6236fb1 (Tilton.png)")
    logger.info("Features: Logo Replacement + Header Addition for CPRA templates")
    logger.info("=" * 100)

    async with async_playwright() as playwright:
        try:
            # Connect to browser
            logger.info("\n🌐 Connecting to browser via CDP...")
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            logger.info("✅ Connected to browser")

            # Get open template tabs
            template_tabs = await get_open_template_tabs(context)

            if not template_tabs:
                logger.error("❌ No open template tabs found!")
                logger.info("💡 Please run: python3 filter_and_open_templates.py first")
                return

            logger.info(f"\n✅ Processing {len(template_tabs)} templates")

            # Process each template
            for idx, tab_info in enumerate(template_tabs, 1):
                result = await process_template_tab(
                    tab_info['page'],
                    tab_info,
                    idx,
                    len(template_tabs)
                )
                results.append(result)

            # Generate report
            logger.info("\n" + "=" * 100)
            logger.info("📊 GENERATING REPORT")
            logger.info("=" * 100)

            if results:
                df = pd.DataFrame(results)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"logo_processing_results_{timestamp}.xlsx"
                df.to_excel(filename, index=False, engine='openpyxl')
                logger.info(f"✅ Report saved: {filename}")

            # Print summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            successful = sum(1 for r in results if r['status'] == 'success')
            partial = sum(1 for r in results if r['status'] == 'partial')
            skipped = sum(1 for r in results if r['status'] == 'skipped')
            failed = sum(1 for r in results if r['status'] in ['failed', 'error'])

            # Count actions
            logo_replacements = sum(1 for r in results if r.get('action') == 'logo_replacement')
            headers_added = sum(1 for r in results if r.get('action') == 'header_added')

            logger.info("\n" + "=" * 100)
            logger.info("📊 FINAL SUMMARY")
            logger.info("=" * 100)
            logger.info(f"✅ Successful: {successful}")
            logger.info(f"   - Logo Replacements: {logo_replacements}")
            logger.info(f"   - Headers Added: {headers_added}")
            logger.info(f"⚠️  Partial: {partial}")
            logger.info(f"ℹ️  Skipped: {skipped}")
            logger.info(f"❌ Failed: {failed}")
            logger.info(f"📋 Total Processed: {len(results)}")
            logger.info(f"⏱️  Duration: {duration:.1f} seconds")
            logger.info("=" * 100)

        except Exception as e:
            logger.exception(f"❌ Fatal error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
