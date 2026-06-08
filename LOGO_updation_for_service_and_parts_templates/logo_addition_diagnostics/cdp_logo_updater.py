#!/usr/bin/env python3
"""
CDP Logo Updater - Validate and Update Logos via Existing Browser Tabs
========================================================================

This script connects to existing browser tabs via CDP and:
1. Validates detected logos against media library
2. Updates invalid/placeholder logos with correct dealer logos
3. Logs every interaction in detail

Usage:
    python3 cdp_logo_updater.py
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from playwright.async_api import async_playwright, Page
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Setup detailed logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"cdp_logo_updater_{timestamp}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CDPLogoUpdater:
    """Updates logos in existing browser tabs via CDP"""
    
    def __init__(self, cdp_url: str = "http://localhost:9223"):
        self.cdp_url = cdp_url
        self.results = []
        
    async def get_available_logos(self, page: Page) -> dict:
        """Get list of available logos from media library popup"""
        logger.info("   📚 Opening media library to fetch available logos...")
        
        try:
            # Step 1: Find a logo container
            container_found = await page.evaluate("""
                () => {
                    const container = document.querySelector('[data-learned-logo]');
                    return container !== null;
                }
            """)
            
            if not container_found:
                return {'success': False, 'error': 'No logo container found'}
            
            logger.debug("   ✓ Logo container found")
            
            # Step 2: Hover over the IMAGE PARENT (subcontainer) to trigger controls
            logger.debug("   → Hovering over image parent (subcontainer) to show toolbar...")

            # Get the image parent element
            img_parent_hoverable = await page.evaluate_handle("""
                () => {
                    const container = document.querySelector('[data-learned-logo]');
                    if (!container) return null;
                    const img = container.querySelector('img');
                    return img ? img.parentElement : container;
                }
            """)

            if img_parent_hoverable:
                await img_parent_hoverable.as_element().hover(force=True)
                await page.wait_for_timeout(2000)  # Wait for toolbar to appear
            else:
                logger.warning("   ⚠️  Could not find image parent to hover on")
                return {'success': False, 'error': 'Image parent not found'}
            
            # Step 3: Click the "Change Image" icon (icon-switch)
            logger.debug("   → Clicking 'Change Image' icon...")
            change_clicked = await page.evaluate("""
                () => {
                    const container = document.querySelector('[data-learned-logo]');
                    if (!container) return { clicked: false, reason: 'Container not found' };

                    // Strategy 1: Look for icon-switch in container
                    let changeIcon = container.querySelector('[aria-label="icon-switch"]') ||
                                   container.querySelector('[title="Change Image"]');

                    if (changeIcon) {
                        changeIcon.click();
                        return { clicked: true, method: 'direct-container' };
                    }

                    // Strategy 2: Look in closest SortableItem parent
                    const sortableItem = container.closest('[class*="SortableItem"]');
                    if (sortableItem) {
                        changeIcon = sortableItem.querySelector('[aria-label="icon-switch"]') ||
                                   sortableItem.querySelector('[title="Change Image"]');

                        if (changeIcon) {
                            changeIcon.click();
                            return { clicked: true, method: 'sortable-item' };
                        }
                    }

                    return { clicked: false, reason: 'Change Image icon not found' };
                }
            """)

            if not change_clicked['clicked']:
                logger.warning(f"   ⚠️  Could not click Change Image icon: {change_clicked.get('reason', 'unknown')}")
                return {'success': False, 'error': change_clicked.get('reason', 'Change icon not found')}
            
            logger.debug("   ✓ Clicked 'Change Image' button")
            
            # Step 4: Wait for media library modal to open
            logger.debug("   → Waiting for media library modal...")
            await page.wait_for_timeout(3000)  # Increased timeout

            # Step 5: Extract available logos from the modal
            logger.debug("   → Extracting available logos from modal...")

            # First, check what modal elements exist
            modal_debug = await page.evaluate("""
                () => {
                    const modals = document.querySelectorAll('[role="dialog"], [class*="modal"], [class*="Modal"], [class*="drawer"], [class*="Drawer"]');
                    const debugInfo = {
                        modalCount: modals.length,
                        modalClasses: Array.from(modals).map(m => m.className),
                        totalImages: 0
                    };

                    if (modals.length > 0) {
                        const modal = modals[modals.length - 1]; // Get the latest modal
                        const allImgs = modal.querySelectorAll('img');
                        debugInfo.totalImages = allImgs.length;
                    }

                    return debugInfo;
                }
            """)

            logger.debug(f"   → Modal debug: {modal_debug['modalCount']} modals, {modal_debug['totalImages']} images")

            # Now extract logos with improved selectors
            logos = await page.evaluate("""
                () => {
                    // Try multiple modal selectors (newest first)
                    const modalSelectors = [
                        '[role="dialog"]',
                        '[class*="Drawer"]',
                        '[class*="drawer"]',
                        '[class*="Modal"]',
                        '[class*="modal"]'
                    ];

                    let modal = null;
                    for (const selector of modalSelectors) {
                        const modals = document.querySelectorAll(selector);
                        if (modals.length > 0) {
                            modal = modals[modals.length - 1]; // Get last/newest modal
                            break;
                        }
                    }

                    if (!modal) return [];

                    // Find all images in the modal (including lazy-loaded ones)
                    const images = modal.querySelectorAll('img, [style*="background-image"]');
                    const logos = [];

                    images.forEach(img => {
                        let src = null;

                        // Handle img tags
                        if (img.tagName === 'IMG') {
                            src = img.src;
                        }
                        // Handle background images
                        else if (img.style.backgroundImage) {
                            const match = img.style.backgroundImage.match(/url\(['"]?([^'"]+)['"]?\)/);
                            if (match) src = match[1];
                        }

                        if (!src) return;

                        // Skip UI icons and Tekion logo
                        if (src.includes('/icon-') ||
                            src.includes('/common/CRM/') ||
                            src.includes('tekion-logo')) return;

                        const filename = src.split('/').pop().split('?')[0];
                        const rect = img.getBoundingClientRect();

                        // Include any visible image (even small thumbnails)
                        if (rect.width > 10 && rect.height > 10) {
                            logos.push({
                                filename: filename,
                                src: src.substring(0, 100),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            });
                        }
                    });

                    // De-duplicate by filename
                    const unique = [];
                    const seen = new Set();
                    logos.forEach(logo => {
                        if (!seen.has(logo.filename)) {
                            seen.add(logo.filename);
                            unique.push(logo);
                        }
                    });

                    return unique;
                }
            """)
            
            logger.info(f"   ✅ Found {len(logos)} available logos in media library")
            for idx, logo in enumerate(logos[:10], 1):
                logger.debug(f"      {idx}. {logo['filename']} ({logo['width']}x{logo['height']}px)")
            
            if len(logos) > 10:
                logger.debug(f"      ... and {len(logos) - 10} more")
            
            # Step 6: Close the modal
            logger.debug("   → Closing media library modal...")
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
            
            return {
                'success': True,
                'logos': logos,
                'count': len(logos)
            }
            
        except Exception as e:
            logger.error(f"   ❌ Error getting available logos: {e}")
            return {'success': False, 'error': str(e)}

    async def validate_detected_logos(self, page: Page, available_logos: list) -> dict:
        """Validate detected logos against available logos"""
        logger.info("   🔍 Validating detected logos...")

        # Extract detected logos from page
        detected = await page.evaluate("""
            () => {
                const containers = document.querySelectorAll('[data-learned-logo]');
                const logos = [];

                containers.forEach((container, idx) => {
                    const img = container.querySelector('img');
                    const isGreen = container.style.outline.includes('lime') ||
                                   container.style.outline.includes('green');

                    if (img && isGreen) {
                        logos.push({
                            index: idx + 1,
                            marker: container.getAttribute('data-learned-logo'),
                            src: img.src,
                            filename: img.src.split('/').pop().split('?')[0],
                            alt: img.alt || ''
                        });
                    }
                });

                return logos;
            }
        """)

        logger.info(f"   📊 Found {len(detected)} green-bordered logo(s) to validate")

        available_filenames = [logo['filename'] for logo in available_logos]
        invalid_logos = []
        valid_logos = []

        for logo in detected:
            filename = logo['filename']
            logger.debug(f"   → Validating logo {logo['index']}: '{filename}'")

            if filename in available_filenames:
                logger.info(f"   ✅ Logo {logo['index']} '{filename}' is VALID (in media library)")
                valid_logos.append(logo)
            else:
                logger.warning(f"   ⚠️  Logo {logo['index']} '{filename}' is INVALID (NOT in media library)")
                invalid_logos.append(logo)

        return {
            'detected_count': len(detected),
            'valid': valid_logos,
            'invalid': invalid_logos,
            'valid_count': len(valid_logos),
            'invalid_count': len(invalid_logos)
        }

    async def select_best_replacement_logo(self, available_logos: list,
                                          template_name: str = '') -> str:
        """Select best replacement logo from available logos"""
        logger.info("   🎯 Selecting best replacement logo...")

        if not available_logos:
            logger.error("   ❌ No available logos to choose from!")
            return None

        # Strategy 1: Look for dealer name match
        if template_name:
            template_lower = template_name.lower()
            for logo in available_logos:
                if any(word in logo['filename'].lower() for word in template_lower.split()):
                    logger.info(f"   ✅ Found name match: '{logo['filename']}'")
                    return logo['filename']

        # Strategy 2: Skip data URIs and obvious placeholders
        placeholder_patterns = ['screenshot', 'example', 'sample', 'test', 'placeholder']

        # Filter out data URIs (inline SVGs/images) and placeholders
        actual_files = [
            logo for logo in available_logos
            if not logo['filename'].startswith('svg+xml;base64,') and
               not logo['filename'].startswith('data:') and
               not logo['filename'].startswith('image/') and
               not any(p in logo['filename'].lower() for p in placeholder_patterns)
        ]

        if actual_files:
            selected = actual_files[0]['filename']
            logger.info(f"   ✅ Selected actual image file: '{selected}'")
            return selected

        # Strategy 3: Just pick the first one
        selected = available_logos[0]['filename']
        logger.warning(f"   ⚠️  No smart match found, using first available: '{selected}'")
        return selected

    async def update_logo(self, page: Page, logo_index: int, replacement_filename: str) -> bool:
        """Update a logo to use a different image from media library"""
        logger.info(f"   🔄 Updating logo {logo_index} to '{replacement_filename}'...")

        try:
            # Step 1: Find the logo container
            logger.debug(f"   → Finding logo container {logo_index}...")
            container_selector = f'[data-learned-logo="container-{logo_index}"]'

            # Step 2: Hover over it
            logger.debug(f"   → Hovering over logo {logo_index}...")
            await page.hover(container_selector)
            await page.wait_for_timeout(500)

            # Step 3: Click change image button
            logger.debug(f"   → Opening change image dialog...")
            clicked = await page.evaluate("""
                (containerSelector) => {
                    const container = document.querySelector(containerSelector);
                    if (!container) return false;

                    // Trigger hover
                    const img = container.querySelector('img');
                    if (img) {
                        img.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                    }

                    // Wait a bit for controls to appear, then click
                    setTimeout(() => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const changeBtn = buttons.find(btn =>
                            btn.textContent.includes('Change')
                        );
                        if (changeBtn) changeBtn.click();
                    }, 300);

                    return true;
                }
            """, container_selector)

            if not clicked:
                logger.error(f"   ❌ Failed to open change dialog for logo {logo_index}")
                return False

            await page.wait_for_timeout(2000)
            logger.debug(f"   ✓ Change dialog opened")

            # Step 4: Find and click the replacement logo in the modal
            logger.debug(f"   → Searching for '{replacement_filename}' in media library...")
            logo_selected = await page.evaluate("""
                (targetFilename) => {
                    const modal = document.querySelector('[role="dialog"], [class*="modal"]');
                    if (!modal) return false;

                    const images = Array.from(modal.querySelectorAll('img'));
                    const targetImg = images.find(img => {
                        const filename = img.src.split('/').pop().split('?')[0];
                        return filename === targetFilename;
                    });

                    if (targetImg) {
                        targetImg.click();
                        return true;
                    }

                    return false;
                }
            """, replacement_filename)

            if not logo_selected:
                logger.error(f"   ❌ Could not find '{replacement_filename}' in modal")
                await page.keyboard.press('Escape')
                return False

            logger.debug(f"   ✓ Selected '{replacement_filename}'")
            await page.wait_for_timeout(500)

            # Step 5: Click "Save" or "Apply" button
            logger.debug(f"   → Saving changes...")
            saved = await page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const saveBtn = buttons.find(btn =>
                        btn.textContent.includes('Save') ||
                        btn.textContent.includes('Apply') ||
                        btn.textContent.includes('Done')
                    );

                    if (saveBtn) {
                        saveBtn.click();
                        return true;
                    }
                    return false;
                }
            """)

            if not saved:
                logger.warning(f"   ⚠️  Could not find Save button, pressing Enter...")
                await page.keyboard.press('Enter')

            await page.wait_for_timeout(1000)
            logger.info(f"   ✅ Logo {logo_index} updated successfully!")
            return True

        except Exception as e:
            logger.error(f"   ❌ Error updating logo {logo_index}: {e}")
            return False

    async def process_template_page(self, page: Page, tab_number: int) -> dict:
        """Process a single template page - validate and update logos"""
        logger.info(f"\n{'='*100}")
        logger.info(f"📄 TAB {tab_number}: {page.url[:80]}...")
        logger.info(f"{'='*100}")

        result = {
            'tab': tab_number,
            'url': page.url,
            'template_id': page.url.split('/')[-1] if '/edit/' in page.url else 'unknown',
            'status': 'unknown',
            'logos_detected': 0,
            'logos_valid': 0,
            'logos_invalid': 0,
            'logos_updated': 0,
            'error': None
        }

        try:
            # Get template name
            template_name = await page.title()
            logger.info(f"📝 Template: {template_name}")

            # Step 1: Get available logos from media library
            available_result = await self.get_available_logos(page)

            if not available_result['success']:
                logger.error(f"❌ Failed to get media library: {available_result['error']}")
                result['status'] = 'error'
                result['error'] = available_result['error']
                return result

            available_logos = available_result['logos']
            logger.info(f"✅ Media library loaded: {len(available_logos)} logos available")

            # Step 2: Validate detected logos
            validation = await self.validate_detected_logos(page, available_logos)

            result['logos_detected'] = validation['detected_count']
            result['logos_valid'] = validation['valid_count']
            result['logos_invalid'] = validation['invalid_count']

            logger.info(f"\n📊 VALIDATION SUMMARY:")
            logger.info(f"   • Total detected: {validation['detected_count']}")
            logger.info(f"   • Valid: {validation['valid_count']}")
            logger.info(f"   • Invalid: {validation['invalid_count']}")

            # Step 3: Update invalid logos
            if validation['invalid_count'] > 0:
                logger.info(f"\n🔧 UPDATING {validation['invalid_count']} INVALID LOGO(S)...")

                # Select replacement logo
                replacement = await self.select_best_replacement_logo(
                    available_logos,
                    template_name
                )

                if not replacement:
                    logger.error(f"❌ No replacement logo available!")
                    result['status'] = 'error'
                    result['error'] = 'No replacement logo'
                    return result

                logger.info(f"📝 Will replace with: '{replacement}'")

                # Update each invalid logo
                updated_count = 0
                for logo in validation['invalid']:
                    logger.info(f"\n🔄 Updating logo {logo['index']}...")
                    logger.info(f"   Current: '{logo['filename']}'")
                    logger.info(f"   New: '{replacement}'")

                    success = await self.update_logo(page, logo['index'], replacement)

                    if success:
                        updated_count += 1
                        logger.info(f"   ✅ Logo {logo['index']} updated!")
                    else:
                        logger.error(f"   ❌ Logo {logo['index']} update failed!")

                result['logos_updated'] = updated_count
                logger.info(f"\n✅ Updated {updated_count}/{validation['invalid_count']} invalid logos")
                result['status'] = 'updated'

            elif validation['valid_count'] > 0:
                logger.info(f"\n✅ All {validation['valid_count']} logos are valid - no updates needed")
                result['status'] = 'valid'

            else:
                logger.info(f"\n⚠️  No logos detected in this template")
                result['status'] = 'no_logos'

        except Exception as e:
            logger.error(f"❌ Error processing template: {e}")
            import traceback
            traceback.print_exc()
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    async def run(self, max_templates: int = None):
        """Main entry point - process all template tabs"""
        logger.info("="*100)
        logger.info("🚀 CDP LOGO UPDATER - Starting")
        logger.info(f"📁 Log file: {log_file}")
        logger.info("="*100)

        async with async_playwright() as playwright:
            try:
                # Connect to existing browser
                logger.info(f"\n🌐 Connecting to browser at {self.cdp_url}...")
                browser = await playwright.chromium.connect_over_cdp(self.cdp_url)

                contexts = browser.contexts
                logger.info(f"✅ Connected! Found {len(contexts)} browser context(s)")

                if not contexts:
                    logger.error("❌ No browser contexts found")
                    return

                context = contexts[0]
                pages = context.pages
                logger.info(f"📑 Found {len(pages)} open tab(s)")

                # Filter for template editor pages
                template_pages = []
                for page in pages:
                    if "/templates/edit/" in page.url:
                        template_pages.append(page)

                logger.info(f"✅ Found {len(template_pages)} template editor tab(s)")

                if not template_pages:
                    logger.error("❌ No template editor tabs found")
                    return

                # Limit to max_templates if specified
                if max_templates:
                    template_pages = template_pages[:max_templates]
                    logger.info(f"📊 Processing first {max_templates} template(s)")

                # Process each template page
                for idx, page in enumerate(template_pages, 1):
                    result = await self.process_template_page(page, idx)
                    self.results.append(result)

                # Print final summary
                logger.info(f"\n{'='*100}")
                logger.info(f"📊 FINAL SUMMARY - Processed {len(self.results)} template(s)")
                logger.info(f"{'='*100}")

                for result in self.results:
                    status_icon = {
                        'updated': '🔄',
                        'valid': '✅',
                        'no_logos': '⚠️',
                        'error': '❌'
                    }.get(result['status'], '❓')

                    logger.info(f"{status_icon} Tab {result['tab']}: {result['status'].upper()}")
                    logger.info(f"   Template ID: {result['template_id']}")
                    logger.info(f"   Detected: {result['logos_detected']}, Valid: {result['logos_valid']}, Invalid: {result['logos_invalid']}, Updated: {result['logos_updated']}")
                    if result['error']:
                        logger.info(f"   Error: {result['error']}")

                logger.info(f"\n{'='*100}")
                logger.info(f"✅ Processing complete!")
                logger.info(f"📁 Full log: {log_file}")
                logger.info(f"{'='*100}")

            except Exception as e:
                logger.error(f"❌ Fatal error: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Update logos in existing browser tabs via CDP')
    parser.add_argument('--max', type=int, help='Maximum number of templates to process')
    parser.add_argument('--cdp-url', default='http://localhost:9223', help='CDP URL (default: http://localhost:9223)')

    args = parser.parse_args()

    updater = CDPLogoUpdater(cdp_url=args.cdp_url)
    asyncio.run(updater.run(max_templates=args.max))
