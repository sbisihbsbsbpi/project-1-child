#!/usr/bin/env python3
"""
Parallel Playwright Logo Updater - Uses FULL Playwright automation on existing tabs
Updates all templates in parallel using proper hover + click workflow
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
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


async def update_single_template(page: Page, template_id: str, replacement_logo: str) -> dict:
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
                        logos.push({
                            index: idx + 1,
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
            return {'template_id': template_id, 'status': 'no_logos', 'updated': 0}

        # Step 2: Update each logo that needs updating
        updated_count = 0
        for logo in logos:
            if logo['needsUpdate']:
                logger.info(f"   🔄 Updating logo {logo['index']}: {logo['filename']}")

                # Get the container
                container_selector = f'[data-learned-logo]:has(img)'
                containers = await page.query_selector_all(container_selector)

                if logo['index'] - 1 < len(containers):
                    container = containers[logo['index'] - 1]

                    # Hover on image parent (subcontainer) - THIS IS KEY!
                    img_parent = await container.query_selector('img')
                    if img_parent:
                        parent_element = await img_parent.evaluate_handle('el => el.parentElement')
                        await parent_element.as_element().hover(force=True)
                        await page.wait_for_timeout(2000)

                        # Click Change Image icon
                        clicked = await page.evaluate("""
                            (idx) => {
                                const containers = document.querySelectorAll('[data-learned-logo]');
                                if (idx >= containers.length) return false;

                                const container = containers[idx];
                                const changeIcon = container.querySelector('[aria-label="icon-switch"]') ||
                                                  container.querySelector('[title="Change Image"]');

                                if (changeIcon) {
                                    changeIcon.click();
                                    return true;
                                }
                                return false;
                            }
                        """, logo['index'] - 1)

                        if clicked:
                            await page.wait_for_timeout(2000)

                            # Select first actual file logo (not data URI)
                            selected = await page.evaluate("""
                                () => {
                                    const popup = document.querySelector('[role="dialog"]');
                                    if (!popup) return false;

                                    const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                                    // Skip data URIs - select first actual file
                                    for (let tile of tiles) {
                                        const img = tile.querySelector('img');
                                        if (img && img.src && !img.src.startsWith('data:')) {
                                            tile.click();
                                            return true;
                                        }
                                    }
                                    return false;
                                }
                            """)

                            if selected:
                                await page.wait_for_timeout(1000)

                                # Click Insert
                                inserted = await page.evaluate("""
                                    () => {
                                        const popup = document.querySelector('[role="dialog"]');
                                        if (!popup) return false;

                                        const buttons = Array.from(popup.querySelectorAll('button'));
                                        const insertBtn = buttons.find(b =>
                                            b.textContent.toLowerCase().includes('insert')
                                        );

                                        if (insertBtn) {
                                            insertBtn.click();
                                            return true;
                                        }
                                        return false;
                                    }
                                """)

                                if inserted:
                                    updated_count += 1
                                    logger.info(f"   ✅ Logo {logo['index']} updated")
                                    await page.wait_for_timeout(1000)

        logger.info(f"✅ Template {template_id}: Updated {updated_count}/{len([l for l in logos if l['needsUpdate']])} logo(s)")

        return {
            'template_id': template_id,
            'status': 'success',
            'total_logos': len(logos),
            'updated': updated_count
        }

    except Exception as e:
        logger.error(f"❌ Template {template_id}: Error - {e}")
        return {'template_id': template_id, 'status': 'error', 'error': str(e), 'updated': 0}


async def main():
    logger.info("="*100)
    logger.info("🚀 PARALLEL PLAYWRIGHT LOGO UPDATER")
    logger.info("="*100)

    async with async_playwright() as playwright:
        # Connect to existing browser
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]

        # Get all template pages
        all_pages = context.pages
        template_pages = [p for p in all_pages if "/templates/edit/" in p.url]

        logger.info(f"\n📊 Found {len(template_pages)} template tab(s)")

        if not template_pages:
            logger.error("❌ No template tabs found!")
            return

        # Extract template IDs
        template_ids = []
        for page in template_pages:
            url = page.url
            template_id = url.split('/templates/edit/')[-1].split('?')[0] if '/templates/edit/' in url else None
            template_ids.append(template_id)

        logger.info(f"📋 Template IDs: {template_ids[:5]}{'...' if len(template_ids) > 5 else ''}")

        # Process all templates in parallel
        logger.info(f"\n🔄 Processing all {len(template_pages)} templates in parallel...")

        # Define replacement logo (first actual file, not data URI)
        replacement_logo = "57a630e9-0c62-498e-9bc6-a054b82f9930.jpeg"

        # Create tasks for all templates
        tasks = [
            update_single_template(template_pages[i], template_ids[i], replacement_logo)
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
        errors = sum(1 for r in results if r['status'] == 'error')
        no_logos = sum(1 for r in results if r['status'] == 'no_logos')
        total_updated = sum(r.get('updated', 0) for r in results)

        logger.info(f"\nTotal templates: {total}")
        logger.info(f"✅ Successful: {successful}")
        logger.info(f"⏭️  No logos: {no_logos}")
        logger.info(f"❌ Errors: {errors}")
        logger.info(f"📝 Total logos updated: {total_updated}")

        logger.info(f"\n📁 Full log: {log_file}")
        logger.info("="*100)


if __name__ == "__main__":
    asyncio.run(main())


async def main():
    logger.info("="*100)
    logger.info("🚀 PARALLEL PLAYWRIGHT LOGO UPDATER")
