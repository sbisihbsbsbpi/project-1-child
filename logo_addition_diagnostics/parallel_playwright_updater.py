#!/usr/bin/env python3
"""
Parallel Playwright Logo Updater - Uses FULL Playwright automation on existing tabs
Updates all templates in parallel using proper hover + click workflow

IMPROVEMENTS (June 8, 2026):
- Fixed hover target: Now hovers on [class*="imageComponent"] subcontainer
- Increased wait time from 2s to 3s after hover
- Added comprehensive error handling and logging
- Sequential logo processing within each template (prevents modal conflicts)
- Added validation after updates
- Added retry logic for failed clicks
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from playwright.async_api import async_playwright, Page

# Setup logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = log_dir / f'parallel_playwright_{timestamp}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def update_single_logo(page: Page, logo: Dict, logo_idx: int, max_retries: int = 2) -> bool:
    """Update a single logo with retry logic"""

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(f"      🔄 Retry {attempt}/{max_retries} for logo {logo_idx}")

            # Step 1: Find the container with specific data attribute
            container_selector = f'[data-learned-logo="container-{logo_idx}"]'
            container = await page.query_selector(container_selector)

            if not container:
                logger.warning(f"      ⚠️  Container not found: {container_selector}")
                return False

            # Step 2: Find the imageComponent subcontainer - THIS IS THE KEY FIX!
            sub_container = await container.query_selector('[class*="imageComponent"]')
            if not sub_container:
                logger.warning(f"      ⚠️  imageComponent not found for logo {logo_idx}")
                return False

            logger.debug(f"      → Found imageComponent subcontainer")

            # Step 3: Hover on the subcontainer to reveal toolbar (3 seconds, not 2!)
            await sub_container.hover(force=True)
            await page.wait_for_timeout(3000)
            logger.debug(f"      → Hovered for 3s, toolbar should be visible")

            # Step 4: Click Change Image icon
            clicked = await page.evaluate("""
                (idx) => {
                    const container = document.querySelector(`[data-learned-logo="container-${idx}"]`);
                    if (!container) return { success: false, reason: 'Container not found' };

                    // Look for Change Image icon in subcontainer area
                    const subContainer = container.querySelector('[class*="imageComponent"]');
                    if (!subContainer) return { success: false, reason: 'subContainer not found' };

                    const changeIcon = subContainer.querySelector('[aria-label="icon-switch"]') ||
                                      subContainer.querySelector('[title="Change Image"]') ||
                                      container.querySelector('[aria-label="icon-switch"]') ||
                                      container.querySelector('[title="Change Image"]');

                    if (changeIcon) {
                        changeIcon.click();
                        return { success: true };
                    }
                    return { success: false, reason: 'Change Image icon not found' };
                }
            """, logo_idx)

            if not clicked.get('success'):
                logger.warning(f"      ⚠️  Failed to click Change Image: {clicked.get('reason', 'Unknown')}")
                if attempt < max_retries - 1:
                    await page.wait_for_timeout(1000)
                    continue
                return False

            await page.wait_for_timeout(2000)
            logger.debug(f"      → Change Image clicked, modal should be open")

            # Step 5: Select first actual file logo (not data URI)
            selected = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]');
                    if (!popup) return { success: false, reason: 'Modal not found' };

                    const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    if (tiles.length === 0) return { success: false, reason: 'No media tiles' };

                    // Skip data URIs - select first actual file
                    for (let tile of tiles) {
                        const img = tile.querySelector('img');
                        if (img && img.src && !img.src.startsWith('data:')) {
                            const filename = img.src.split('/').pop().split('?')[0];
                            tile.click();
                            return { success: true, filename: filename };
                        }
                    }
                    return { success: false, reason: 'No valid media files found' };
                }
            """)

            if not selected.get('success'):
                logger.warning(f"      ⚠️  Failed to select logo: {selected.get('reason', 'Unknown')}")
                # Close modal
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(500)
                if attempt < max_retries - 1:
                    continue
                return False

            logger.debug(f"      → Selected logo: {selected.get('filename', 'unknown')}")
            await page.wait_for_timeout(1000)

            # Step 6: Click Insert button
            inserted = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]');
                    if (!popup) return { success: false, reason: 'Modal closed' };

                    const buttons = Array.from(popup.querySelectorAll('button'));
                    const insertBtn = buttons.find(b =>
                        b.textContent.toLowerCase().includes('insert')
                    );

                    if (insertBtn && !insertBtn.disabled) {
                        insertBtn.click();
                        return { success: true };
                    }
                    return { success: false, reason: 'Insert button not found or disabled' };
                }
            """)

            if not inserted.get('success'):
                logger.warning(f"      ⚠️  Failed to click Insert: {inserted.get('reason', 'Unknown')}")
                # Close modal
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(500)
                if attempt < max_retries - 1:
                    continue
                return False

            logger.debug(f"      → Insert clicked")
            await page.wait_for_timeout(1500)

            # Step 7: Validate the logo actually changed
            new_filename = await page.evaluate("""
                (idx) => {
                    const container = document.querySelector(`[data-learned-logo="container-${idx}"]`);
                    const img = container?.querySelector('img');
                    return img?.src.split('/').pop().split('?')[0];
                }
            """, logo_idx)

            if new_filename and new_filename != logo['filename']:
                logger.info(f"      ✅ Logo {logo_idx} verified: {logo['filename'][:30]}... → {new_filename[:30]}...")
                return True
            else:
                logger.warning(f"      ⚠️  Logo {logo_idx} may not have changed (filename still: {new_filename})")
                if attempt < max_retries - 1:
                    await page.wait_for_timeout(1000)
                    continue
                return False

        except Exception as e:
            logger.error(f"      ❌ Error updating logo {logo_idx}: {e}")
            if attempt < max_retries - 1:
                await page.wait_for_timeout(1000)
                continue
            return False

    return False


async def update_single_template(page: Page, template_id: str, replacement_logo: str, dry_run: bool = False) -> dict:
    """Update logos in a single template using full Playwright automation"""

    try:
        logger.info(f"🔄 Processing template {template_id}...")

        # Step 1: Get detected logos
        logos = await page.evaluate("""
            () => {
                const containers = document.querySelectorAll('[data-learned-logo]');
                const logos = [];

                containers.forEach((container, idx) => {
                    const img = container.querySelector('img');
                    if (img) {
                        const filename = img.src.split('/').pop().split('?')[0];
                        const dataAttr = container.getAttribute('data-learned-logo');
                        logos.push({
                            index: idx + 1,
                            dataAttr: dataAttr,
                            filename: filename,
                            needsUpdate: filename.includes('Screenshot_2022-02-10_at_5.25.15_PM.png')
                        });
                    }
                });

                return logos;
            }
        """)

        if not logos:
            logger.info(f"   ⏭️  No logos detected - skipping")
            return {'template_id': template_id, 'status': 'no_logos', 'updated': 0, 'failed': 0}

        logos_needing_update = [l for l in logos if l['needsUpdate']]
        if not logos_needing_update:
            logger.info(f"   ✅ All {len(logos)} logo(s) already correct - skipping")
            return {'template_id': template_id, 'status': 'already_correct', 'updated': 0, 'failed': 0}

        logger.info(f"   📊 Found {len(logos)} logo(s), {len(logos_needing_update)} need updating")

        if dry_run:
            logger.info(f"   🔍 DRY RUN - Would update: {[l['filename'][:40] for l in logos_needing_update]}")
            return {'template_id': template_id, 'status': 'dry_run', 'updated': 0, 'failed': 0}

        # Step 2: Update each logo sequentially (prevents modal conflicts)
        updated_count = 0
        failed_count = 0
        failed_logos = []

        for logo in logos:
            if logo['needsUpdate']:
                logger.info(f"   🔄 Updating logo {logo['index']}: {logo['filename'][:50]}...")

                success = await update_single_logo(page, logo, logo['index'])

                if success:
                    updated_count += 1
                else:
                    failed_count += 1
                    failed_logos.append({
                        'index': logo['index'],
                        'filename': logo['filename']
                    })

                # Small delay between logos to avoid conflicts
                await page.wait_for_timeout(500)

        status_emoji = "✅" if failed_count == 0 else "⚠️"
        logger.info(f"{status_emoji} Template {template_id}: Updated {updated_count}/{len(logos_needing_update)}, Failed: {failed_count}")

        return {
            'template_id': template_id,
            'status': 'success' if failed_count == 0 else 'partial',
            'total_logos': len(logos),
            'updated': updated_count,
            'failed': failed_count,
            'failed_logos': failed_logos
        }

    except Exception as e:
        logger.error(f"❌ Template {template_id}: Error - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {'template_id': template_id, 'status': 'error', 'error': str(e), 'updated': 0, 'failed': 0}


async def main(dry_run: bool = False, max_templates: int = None):
    logger.info("="*100)
    logger.info("🚀 PARALLEL PLAYWRIGHT LOGO UPDATER (IMPROVED)")
    logger.info("="*100)

    if dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")

    async with async_playwright() as playwright:
        # Connect to existing browser
        logger.info("\n🔌 Connecting to browser via CDP...")
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]

        # Get all template pages
        all_pages = context.pages
        template_pages = [p for p in all_pages if "/templates/edit/" in p.url]

        logger.info(f"📊 Found {len(template_pages)} template tab(s)")

        if not template_pages:
            logger.error("❌ No template tabs found!")
            return

        # Apply max_templates limit if specified
        if max_templates and max_templates < len(template_pages):
            logger.info(f"⚙️  Limiting to first {max_templates} templates")
            template_pages = template_pages[:max_templates]

        # Extract template IDs
        template_ids = []
        for page in template_pages:
            url = page.url
            template_id = url.split('/templates/edit/')[-1].split('?')[0] if '/templates/edit/' in url else None
            template_ids.append(template_id)

        logger.info(f"📋 Template IDs: {template_ids[:5]}{'...' if len(template_ids) > 5 else ''}")

        # Process all templates in parallel
        logger.info(f"\n🔄 Processing {len(template_pages)} template(s) in parallel...")
        logger.info("   (Logos within each template are processed sequentially)")

        # Define replacement logo (first actual file, not data URI)
        replacement_logo = "57a630e9-0c62-498e-9bc6-a054b82f9930.jpeg"

        # Create tasks for all templates
        tasks = [
            update_single_template(template_pages[i], template_ids[i], replacement_logo, dry_run)
            for i in range(len(template_pages))
        ]

        # Run all updates in parallel
        results = await asyncio.gather(*tasks)

        # Summary
        logger.info("\n" + "="*100)
        logger.info("📊 FINAL SUMMARY")
        logger.info("="*100)

        total = len(results)
        successful = sum(1 for r in results if r['status'] == 'success')
        partial = sum(1 for r in results if r['status'] == 'partial')
        errors = sum(1 for r in results if r['status'] == 'error')
        no_logos = sum(1 for r in results if r['status'] == 'no_logos')
        already_correct = sum(1 for r in results if r['status'] == 'already_correct')

        total_updated = sum(r.get('updated', 0) for r in results)
        total_failed = sum(r.get('failed', 0) for r in results)

        logger.info(f"\n📈 Templates:")
        logger.info(f"   Total processed: {total}")
        logger.info(f"   ✅ Fully successful: {successful}")
        logger.info(f"   ⚠️  Partially successful: {partial}")
        logger.info(f"   ✓  Already correct: {already_correct}")
        logger.info(f"   ⏭️  No logos detected: {no_logos}")
        logger.info(f"   ❌ Errors: {errors}")

        logger.info(f"\n📝 Logo Updates:")
        logger.info(f"   ✅ Successfully updated: {total_updated}")
        logger.info(f"   ❌ Failed: {total_failed}")

        if total_updated > 0:
            success_rate = (total_updated / (total_updated + total_failed)) * 100 if (total_updated + total_failed) > 0 else 0
            logger.info(f"   📊 Success rate: {success_rate:.1f}%")

        # Save failed templates for retry
        failed_templates = [
            {
                'template_id': r['template_id'],
                'failed_logos': r.get('failed_logos', [])
            }
            for r in results if r.get('failed', 0) > 0
        ]

        if failed_templates and not dry_run:
            failed_file = log_dir / f'failed_templates_{timestamp}.json'
            with open(failed_file, 'w') as f:
                json.dump(failed_templates, f, indent=2)
            logger.info(f"\n⚠️  Failed templates saved to: {failed_file}")

        logger.info(f"\n📁 Full log: {log_file}")
        logger.info("="*100)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Parallel Playwright Logo Updater')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--max-templates', type=int, help='Limit number of templates to process')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    asyncio.run(main(dry_run=args.dry_run, max_templates=args.max_templates))
