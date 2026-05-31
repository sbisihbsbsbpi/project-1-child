#!/usr/bin/env python3
"""
Process Logo Replacement on Already-Opened Templates
====================================================

This script processes logos on templates that are ALREADY open in the browser.
Instead of opening new tabs, it uses the existing tabs from filter_and_open_templates.py

ENHANCED VERSION with:
- Retry logic for resilient operations
- Advanced error handling and recovery
- Performance optimization
- Configurable settings
- Comprehensive validation

Author: Automation Team
Date: 2026-05-30
Enhanced: 2026-05-31
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright, Page

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION - Easy customization
# ============================================================
CONFIG = {
    'logo_media_id': '6a19132b6697f36de6236fb1',  # Tilton logo
    'target_logo_width': 200,  # pixels
    'max_retries': 3,  # retry attempts for failed operations
    'retry_delay': 2,  # seconds between retries
    'operation_timeout': 30,  # seconds
    'hover_delay': 1.5,  # seconds
    'click_delay': 3,  # seconds after click actions
    'verification_delay': 2,  # seconds for verification
}

def get_config(key: str):
    """Get configuration value"""
    return CONFIG.get(key)


# ============================================================
# UTILITY FUNCTIONS - Retry logic and error handling
# ============================================================

async def retry_async_operation(operation, max_retries: int = None, delay: float = None, operation_name: str = "Operation"):
    """
    Retry an async operation with exponential backoff

    Args:
        operation: Async function to retry
        max_retries: Maximum number of retry attempts
        delay: Base delay between retries (seconds)
        operation_name: Name for logging

    Returns:
        Result from successful operation or None if all retries fail
    """
    if max_retries is None:
        max_retries = get_config('max_retries')
    if delay is None:
        delay = get_config('retry_delay')

    for attempt in range(1, max_retries + 1):
        try:
            result = await operation()
            if result:  # Success
                if attempt > 1:
                    logger.info(f"      ✅ {operation_name} succeeded on attempt {attempt}")
                return result
            else:
                if attempt < max_retries:
                    wait_time = delay * attempt  # Exponential backoff
                    logger.warning(f"      ⚠️  {operation_name} attempt {attempt} returned False, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        except Exception as e:
            if attempt < max_retries:
                wait_time = delay * attempt
                logger.warning(f"      ⚠️  {operation_name} attempt {attempt} failed: {e}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"      ❌ {operation_name} failed after {max_retries} attempts: {e}")
                return None

    logger.error(f"      ❌ {operation_name} failed after {max_retries} attempts")
    return None


async def safe_page_evaluate(page: Page, script: str, operation_name: str = "Evaluate") -> Optional[Dict]:
    """
    Safely evaluate JavaScript with error handling

    Args:
        page: Playwright Page object
        script: JavaScript code to evaluate
        operation_name: Name for logging

    Returns:
        Result dict or None on failure
    """
    try:
        result = await page.evaluate(script)
        return result
    except Exception as e:
        logger.error(f"      ❌ {operation_name} JS evaluation failed: {e}")
        return None


class PerformanceMonitor:
    """Monitor and track performance metrics"""

    def __init__(self):
        self.start_time = None
        self.operation_times = []

    def start(self):
        """Start timing"""
        self.start_time = datetime.now()

    def record_operation(self, operation_name: str, duration: float):
        """Record an operation's duration"""
        self.operation_times.append({
            'operation': operation_name,
            'duration': duration
        })

    def get_summary(self) -> Dict:
        """Get performance summary"""
        if not self.start_time:
            return {}

        total_duration = (datetime.now() - self.start_time).total_seconds()
        avg_operation_time = sum(op['duration'] for op in self.operation_times) / len(self.operation_times) if self.operation_times else 0

        return {
            'total_duration': total_duration,
            'total_operations': len(self.operation_times),
            'avg_operation_time': avg_operation_time,
            'operations': self.operation_times
        }


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
    """
    Replace a single logo with retry logic

    Args:
        page: Playwright Page object
        logo_idx: Logo index (1-based)
        logo_media_id: New logo media ID

    Returns:
        True if successful, False otherwise
    """

    try:
        # Step 1: Hover over logo to reveal toolbar (with validation)
        container = await page.query_selector(f'[data-logo-to-inspect="logo-{logo_idx}"]')
        if not container:
            logger.warning(f"      ⚠️  Logo container #{logo_idx} not found")
            return False

        await container.hover(force=True)
        await asyncio.sleep(get_config('hover_delay'))

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
                logger.warning("      ⚠️  Change Image icon not found")
                return False

            await asyncio.sleep(get_config('click_delay'))

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

        if not popup_closed:
            logger.warning("      Popup did not close after insert")
            return False

        # Step 6: Mark the replaced logo container for post-processing
        await page.evaluate(f"""
            () => {{
                const container = document.querySelector('[data-logo-to-inspect="logo-{logo_idx}"]');
                if (container) {{
                    container.setAttribute('data-logo-replaced', 'true');
                }}
            }}
        """)

        return True

    except Exception as e:
        logger.exception(f"      Error replacing logo: {e}")
        return False


async def center_align_logo(page: Page, logo_idx: int, logo_media_id: str) -> bool:
    """Center align a logo after replacement"""

    try:
        logger.info(f"      📍 Center aligning logo {logo_idx}...")

        # Find the logo container
        container = await page.query_selector(f'[data-logo-to-inspect="logo-{logo_idx}"]')
        if not container:
            logger.warning(f"      Container not found for centering")
            return False

        # Hover to reveal toolbar
        await container.hover(force=True)
        await asyncio.sleep(1.5)

        # Click center align button
        center_result = await page.evaluate(f"""
            () => {{
                const container = document.querySelector('[data-logo-to-inspect="logo-{logo_idx}"]');
                if (!container) return {{ clicked: false, reason: 'Container not found' }};

                // Look for center align button in toolbar (same line as change image)
                const centerBtn = container.querySelector('[title="Center Align"]') ||
                                 container.querySelector('[aria-label="icon-center-align"]') ||
                                 container.querySelector('[aria-label*="Center"]') ||
                                 document.querySelector('[title="Center Align"]') ||
                                 document.querySelector('[aria-label="icon-center-align"]');

                if (centerBtn) {{
                    centerBtn.click();
                    return {{ clicked: true }};
                }}

                return {{ clicked: false, reason: 'Button not found' }};
            }}
        """)

        if center_result['clicked']:
            logger.info(f"      ✅ Logo {logo_idx} centered")
            await asyncio.sleep(0.5)
            return True
        else:
            logger.warning(f"      ⚠️  Center button not found: {center_result.get('reason', 'unknown')}")
            return False

    except Exception as e:
        logger.exception(f"      Error centering logo: {e}")
        return False


async def detect_and_enlarge_logo(page: Page, logo_idx: int, logo_media_id: str, target_width: int = 160) -> bool:
    """
    Detect actual logo pixel dimensions and intelligently enlarge based on size.
    Shows exact pixel measurements and calculates optimal enlargement.
    """

    try:
        logger.info(f"      📏 Detecting logo {logo_idx} pixel dimensions...")

        # Step 1: Detect actual size
        detection_result = await page.evaluate(f"""
            () => {{
                const MEDIA_ID = "{logo_media_id}";
                const LOGO_INDEX = {logo_idx};

                // Find ALL logo images by media ID, then select by index
                const allLogos = Array.from(document.querySelectorAll('img'))
                    .filter(i => i.src.includes(MEDIA_ID));

                if (allLogos.length === 0) return {{ found: false, reason: 'No logos found' }};
                if (LOGO_INDEX > allLogos.length) return {{ found: false, reason: `Only ${{allLogos.length}} logos found, requested index ${{LOGO_INDEX}}` }};

                // Get the specific logo by index (1-based)
                const img = allLogos[LOGO_INDEX - 1];

                if (!img) return {{ found: false, reason: 'Image not found at index' }};

                const rect = img.getBoundingClientRect();
                const currentWidth = Math.round(rect.width);
                const currentHeight = Math.round(rect.height);

                // Get natural dimensions (actual image file size)
                const naturalWidth = img.naturalWidth;
                const naturalHeight = img.naturalHeight;

                // Get computed styles
                const computedStyle = window.getComputedStyle(img);
                const displayWidth = computedStyle.width;
                const displayHeight = computedStyle.height;

                return {{
                    found: true,
                    currentWidth: currentWidth,
                    currentHeight: currentHeight,
                    naturalWidth: naturalWidth,
                    naturalHeight: naturalHeight,
                    displayWidth: displayWidth,
                    displayHeight: displayHeight,
                    aspectRatio: (currentWidth / currentHeight).toFixed(2)
                }};
            }}
        """)

        if not detection_result.get('found'):
            logger.warning(f"      ⚠️  {detection_result.get('reason', 'Image not found')}")
            return False

        # Log detected dimensions
        current_w = detection_result['currentWidth']
        current_h = detection_result['currentHeight']
        natural_w = detection_result['naturalWidth']
        natural_h = detection_result['naturalHeight']
        aspect_ratio = detection_result['aspectRatio']

        logger.info(f"      📊 Detected dimensions:")
        logger.info(f"         Current display: {current_w}x{current_h}px")
        logger.info(f"         Natural (file):  {natural_w}x{natural_h}px")
        logger.info(f"         Aspect ratio:    {aspect_ratio}:1")

        # Step 2: Determine if enlargement is needed
        if current_w >= target_width:
            logger.info(f"      ✅ Logo is already {current_w}px wide (target: {target_width}px) - no enlargement needed")
            return True

        # Step 3: Calculate optimal enlargement
        enlargement_ratio = target_width / current_w
        suggested_height = int(current_h * enlargement_ratio)

        logger.info(f"      🔍 Logo is small ({current_w}px < {target_width}px target)")
        logger.info(f"      📐 Enlargement ratio: {enlargement_ratio:.2f}x")
        logger.info(f"      🎯 Target size: {target_width}x{suggested_height}px")

        # Step 4: Perform enlargement
        enlargement_result = await page.evaluate(f"""
            () => {{
                const MEDIA_ID = "{logo_media_id}";
                const TARGET_WIDTH = {target_width};
                const LOGO_INDEX = {logo_idx};

                // Find ALL logo images, then select by index
                const allLogos = Array.from(document.querySelectorAll('img'))
                    .filter(i => i.src.includes(MEDIA_ID));

                if (allLogos.length === 0) return {{ success: false, reason: 'No logos found' }};

                // Get the specific logo by index (1-based)
                const img = allLogos[LOGO_INDEX - 1];

                if (!img) return {{ success: false, reason: 'Image not found at index' }};

                const beforeRect = img.getBoundingClientRect();
                const beforeWidth = Math.round(beforeRect.width);
                const beforeHeight = Math.round(beforeRect.height);

                // Find resizable container
                let container = img.parentElement;
                for (let i = 0; i < 5; i++) {{
                    if (!container) break;
                    if ((container.className || '').includes('resizable')) break;
                    if ((container.className || '').includes('Image')) break;
                    container = container.parentElement;
                }}

                if (!container) container = img.parentElement;

                // Apply enlargement
                container.style.width = TARGET_WIDTH + 'px';
                container.style.maxWidth = TARGET_WIDTH + 'px';
                container.style.minWidth = TARGET_WIDTH + 'px';

                img.style.width = TARGET_WIDTH + 'px';
                img.style.maxWidth = TARGET_WIDTH + 'px';
                img.style.minWidth = TARGET_WIDTH + 'px';
                img.style.height = 'auto';

                // Force reflow
                container.offsetHeight;

                // Wait a bit for rendering
                const afterRect = img.getBoundingClientRect();
                const afterWidth = Math.round(afterRect.width);
                const afterHeight = Math.round(afterRect.height);

                return {{
                    success: true,
                    before: {{ width: beforeWidth, height: beforeHeight }},
                    after: {{ width: afterWidth, height: afterHeight }},
                    containerApplied: true
                }};
            }}
        """)

        if not enlargement_result.get('success'):
            logger.warning(f"      ⚠️  Enlargement failed: {enlargement_result.get('reason', 'Unknown error')}")
            return False

        # Step 5: Verify and report results
        before = enlargement_result['before']
        after = enlargement_result['after']

        if after['width'] > before['width']:
            increase_px = after['width'] - before['width']
            increase_pct = ((after['width'] / before['width']) - 1) * 100

            logger.info(f"      ✅ Logo enlarged successfully:")
            logger.info(f"         Before: {before['width']}x{before['height']}px")
            logger.info(f"         After:  {after['width']}x{after['height']}px")
            logger.info(f"         Increase: +{increase_px}px width (+{increase_pct:.1f}%)")

            await asyncio.sleep(0.5)
            return True
        else:
            logger.warning(f"      ⚠️  Logo size unchanged: {after['width']}x{after['height']}px")
            return False

    except Exception as e:
        logger.exception(f"      ❌ Error in size detection/enlargement: {e}")
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
            logos_centered = 0
            logos_enlarged = 0

            for logo_idx in range(1, logos_info['count'] + 1):
                logger.info(f"\n   🎯 Processing logo {logo_idx}/{logos_info['count']}...")

                operation_start = datetime.now()

                # Step 1: Replace logo (with retry)
                logo_media_id = get_config('logo_media_id')
                success = await retry_async_operation(
                    lambda: replace_logo(page, logo_idx, logo_media_id),
                    operation_name=f"Replace logo {logo_idx}"
                )

                if success:
                    logos_processed += 1
                    logger.info(f"   ✅ Logo {logo_idx} replaced successfully")

                    # Step 2: Center align the logo (with retry)
                    center_success = await retry_async_operation(
                        lambda: center_align_logo(page, logo_idx, logo_media_id),
                        max_retries=2,
                        operation_name=f"Center align logo {logo_idx}"
                    )
                    if center_success:
                        logos_centered += 1

                    # Step 3: Detect size and enlarge (with retry)
                    target_width = get_config('target_logo_width')
                    enlarge_success = await retry_async_operation(
                        lambda: detect_and_enlarge_logo(page, logo_idx, logo_media_id, target_width=target_width),
                        max_retries=2,
                        operation_name=f"Enlarge logo {logo_idx}"
                    )
                    if enlarge_success:
                        logos_enlarged += 1

                    # Calculate operation time
                    operation_time = (datetime.now() - operation_start).total_seconds()
                    logger.info(f"   ⏱️  Logo {logo_idx} processing time: {operation_time:.1f}s")
                else:
                    logger.warning(f"   ⚠️  Logo {logo_idx} replacement failed after all retries")

            # Return results
            if logos_processed == logos_info['count']:
                status = 'success'
            elif logos_processed > 0:
                status = 'partial'
            else:
                status = 'failed'

            logger.info(f"\n   ✅ Template complete:")
            logger.info(f"      - Logos replaced: {logos_processed}/{logos_info['count']}")
            logger.info(f"      - Logos centered: {logos_centered}/{logos_processed}")
            logger.info(f"      - Logos enlarged: {logos_enlarged}/{logos_processed}")

            return {
                'template': template_info['title'],
                'id': template_id,
                'status': status,
                'action': 'logo_replacement',
                'logos_found': logos_info['count'],
                'logos_processed': logos_processed,
                'logos_centered': logos_centered,
                'logos_enlarged': logos_enlarged
            }

        # ============================================================
        # CHECK #1.5: Look for logo containers WITHOUT WARNING ICONS
        # ============================================================
        # No warnings found - check if logo CONTAINERS exist (without warnings)
        logger.info("   🔍 No warnings found - checking for logo containers...")

        logo_containers_info = await page.evaluate("""
            () => {
                // Look for logo containers by their class patterns
                // These are the containers that would have warning icons if logos were wrong
                const containers = Array.from(
                    document.querySelectorAll('[class*="SortableItem"]')
                ).filter(item => {
                    // Check if this container has an image
                    const hasImage = item.querySelector('img') !== null;
                    // Check if it does NOT have a warning icon
                    const hasWarning = item.querySelector('.templates_Image_warningIcon__hCZHMuhEmb') !== null;

                    // Container with image but no warning = logo is correct
                    return hasImage && !hasWarning;
                });

                if (containers.length === 0) return { found: false, count: 0 };

                return {
                    found: true,
                    count: containers.length,
                    // Get some info about the logos for logging
                    logoInfo: containers.map(c => {
                        const img = c.querySelector('img');
                        return {
                            src: img?.src?.substring(0, 100) || 'unknown',
                            alt: img?.alt || 'no-alt',
                            width: img?.width || 0,
                            height: img?.height || 0
                        };
                    })
                };
            }
        """)

        if logo_containers_info['found']:
            # Has logo containers WITHOUT warnings = logos are already correct!
            logger.info(f"   ✅ Found {logo_containers_info['count']} logo container(s) without warnings")
            logger.info(f"   ℹ️  Logos are already correct (no action needed)")

            # Log some details about the logos found
            for i, logo_info in enumerate(logo_containers_info.get('logoInfo', []), 1):
                logger.info(f"      Logo {i}: {logo_info.get('width', 0)}x{logo_info.get('height', 0)} - {logo_info.get('alt', 'no-alt')}")

            return {
                'template': template_info['title'],
                'id': template_id,
                'status': 'skipped',
                'reason': 'Logos already correct (containers exist without warnings)',
                'action': 'none_needed',
                'logos_found': logo_containers_info['count'],
                'logos_processed': 0,
                'logo_details': logo_containers_info.get('logoInfo', [])
            }

        # ============================================================
        # CHECK #2: No logo containers at all - check for header addition
        # ============================================================

        # CHECK #2A: Is this a CPRA template? (naming convention)
        is_cpra_template = template_id.startswith('CPRA_')

        if is_cpra_template:
            logger.info(f"   ℹ️  CPRA template detected: {template_id}")

        # CHECK #2B: Check header button state
        logger.info("   🔍 No logo containers found - checking header button state...")
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
            # Has header structure (but no logo containers at all)
            logger.info(f"   ℹ️  Header exists (opacity={button_state['opacity']}) - skipping")
            return {
                'template': template_info['title'],
                'id': template_id,
                'status': 'skipped',
                'reason': 'Header exists, no logo containers',
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
