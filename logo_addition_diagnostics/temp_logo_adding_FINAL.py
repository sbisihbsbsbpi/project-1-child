#!/usr/bin/env python3
"""
⭐⭐⭐ FINAL INTEGRATED SCRIPT - COMPLETE AUTOMATION ⭐⭐⭐
===========================================================

TEMP LOGO ADDING FINAL - All Features Integrated
=================================================

🚀 STATUS: PRODUCTION READY - FULLY INTEGRATED
✅ Features:
   1. Department filtering (Service & Parts)
   2. API interception & template fetching
   3. Logo detection (warnings + empty containers + headers)
   4. Logo replacement (Change Image workflow)
   5. Logo insertion (Insert Image workflow)
   6. Center align & enlarge logos (NEW!)
   7. Auto-publish (2-click workflow) (NEW!)
   8. Sequential processing
   9. Excel reporting

📅 Last Updated: 2026-05-31
🔗 Git: refactor/phase-1-quick-fixes

Usage:
    python3 temp_logo_adding_FINAL.py --departments Service Parts --max 5
    python3 temp_logo_adding_FINAL.py --all

Author: Automation Team
"""

import asyncio
import sys
import os
import logging
import argparse
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

# ============================================================
# ENHANCED LOGGING SYSTEM
# ============================================================

class EnhancedLogger:
    """Enhanced logger with detailed tracking and file output"""

    def __init__(self, log_file: str = None):
        """Initialize enhanced logger with file and console output"""

        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Generate log filename with timestamp
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"temp_logo_automation_{timestamp}.log"
        else:
            log_file = log_dir / log_file

        self.log_file = log_file

        # Setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Console handler - INFO level
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        # File handler - DEBUG level (captures everything)
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)8s] - %(funcName)25s:%(lineno)4d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

        # Detection tracking
        self.detection_log = []

        self.info("=" * 100)
        self.info(f"📝 ENHANCED LOGGING INITIALIZED")
        self.info(f"📄 Log file: {log_file}")
        self.info("=" * 100)

    def info(self, msg: str):
        """Log info message"""
        self.logger.info(msg)

    def debug(self, msg: str):
        """Log debug message (file only)"""
        self.logger.debug(msg)

    def warning(self, msg: str):
        """Log warning message"""
        self.logger.warning(msg)

    def error(self, msg: str):
        """Log error message"""
        self.logger.error(msg)

    def exception(self, msg: str):
        """Log exception with traceback"""
        self.logger.exception(msg)

    def log_detection(self, template_name: str, detection_result: Dict):
        """Log detailed detection results"""

        entry = {
            'timestamp': datetime.now().isoformat(),
            'template': template_name,
            'warnings_count': detection_result.get('warningsCount', 0),
            'empty_containers_count': detection_result.get('emptyCount', 0),
            'header_containers_count': detection_result.get('headerCount', 0),
            'empty_containers': detection_result.get('emptyContainers', []),
            'header_containers': detection_result.get('headerContainers', [])
        }

        self.detection_log.append(entry)

        # Log to file
        self.debug("=" * 80)
        self.debug(f"DETECTION RESULT for: {template_name}")
        self.debug("-" * 80)

        # Print JavaScript debug output
        if 'debug' in detection_result:
            self.debug("JavaScript Detection Debug Output:")
            for line in detection_result['debug']:
                self.debug(f"  {line}")
            self.debug("-" * 80)

        self.debug(f"SUMMARY:")
        self.debug(f"  Warnings detected: {entry['warnings_count']}")
        self.debug(f"  Empty Logo 1/2 containers: {entry['empty_containers_count']}")
        self.debug(f"  Empty header containers: {entry['header_containers_count']}")

        # Detailed container check results
        if 'containerCheckResults' in detection_result:
            self.debug("")
            self.debug("Logo 1/2 Container Check Results:")
            for check in detection_result['containerCheckResults']:
                self.debug(f"  {check['name']:15s} → found={check['found']}, hasImage={check['hasImage']}, isEmpty={check['isEmpty']}, htmlLen={check['htmlLength']}")

        # Detailed header check results
        if 'headerCheckResults' in detection_result:
            self.debug("")
            self.debug("Header Container Check Results:")
            for check in detection_result['headerCheckResults']:
                self.debug(f"  Position {check['position']} → hasContainer={check['hasContainer']}, hasImage={check['hasImage']}, isEmpty={check['isEmpty']}")

        if entry['empty_containers']:
            self.debug("")
            self.debug("Empty containers to process:")
            for container in entry['empty_containers']:
                self.debug(f"  - {container.get('name')}: ID={container.get('id')}")

        if entry['header_containers']:
            self.debug("")
            self.debug("Header containers to process:")
            for header in entry['header_containers']:
                self.debug(f"  - {header.get('name')}: Position={header.get('position')}")

        self.debug("=" * 80)

    def log_action(self, action: str, target: str, success: bool, details: str = ""):
        """Log action taken on a logo"""

        status = "✅ SUCCESS" if success else "❌ FAILED"
        msg = f"[{action:15s}] {target:30s} → {status}"
        if details:
            msg += f" | {details}"

        if success:
            self.debug(msg)
        else:
            self.warning(msg)

    def save_detection_log(self, filename: str = None):
        """Save detection log as JSON"""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/detection_log_{timestamp}.json"

        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.detection_log, f, indent=2, ensure_ascii=False)

        self.info(f"📊 Detection log saved: {filename}")
        return filename

# Initialize enhanced logger
logger = EnhancedLogger()


class TempLogoAdditionFinalService:
    """
    Final integrated service combining ALL logo automation features:
    - Department filtering
    - API interception
    - Logo detection (warnings, empty containers, headers)
    - Logo replacement/insertion
    - Center align & enlarge
    - Auto-publish
    - Excel reporting
    """
    
    def __init__(self):
        self.results = []
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.start_time = None
        self.published_count = 0
        self.centered_count = 0
        self.enlarged_count = 0
        
    async def run(self,
                  departments: Optional[List[str]] = None,
                  max_templates: int = None,
                  logo_media_id: str = "6a19132b6697f36de6236fb1",
                  logo_width: int = 160,
                  auto_publish: bool = True,
                  cdp_url: str = "http://localhost:9223",
                  base_url: str = "https://preprodapp.tekioncloud.com"):
        """
        Main execution flow with all features
        
        Args:
            departments: List of departments to filter (None = all)
            max_templates: Maximum number of templates to process (None = all)
            logo_media_id: Media ID of logo to add (Tilton.png default)
            logo_width: Width of logo in pixels
            auto_publish: Enable auto-publish after logo updates
            cdp_url: Chrome DevTools Protocol URL
            base_url: Base URL of Tekion application
        """
        
        self.start_time = datetime.now()
        
        logger.info("=" * 100)
        logger.info("🚀 TEMP LOGO ADDING FINAL - COMPLETE AUTOMATION")
        logger.info("=" * 100)
        logger.info(f"Departments: {', '.join(departments) if departments else 'ALL'}")
        logger.info(f"Max Templates: {max_templates if max_templates else 'ALL'}")
        logger.info(f"Logo Media ID: {logo_media_id}")
        logger.info(f"Logo Width: {logo_width}px")
        logger.info(f"Auto-Publish: {'✅ ENABLED' if auto_publish else '❌ DISABLED'}")
        logger.info(f"CDP URL: {cdp_url}")
        logger.info(f"Base URL: {base_url}")
        logger.info("=" * 100)
        
        async with async_playwright() as playwright:
            try:
                # Connect to existing browser
                logger.info("\n🌐 Connecting to browser...")
                browser = await playwright.chromium.connect_over_cdp(cdp_url)
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                logger.info("✅ Connected to browser")
                
                # Step 1: Navigate to templates list
                page = await context.new_page()
                list_url = f"{base_url}/templates/list"
                logger.info(f"\n📍 Navigating to: {list_url}")
                await page.goto(list_url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
                
                # Step 2: Apply department filter
                if departments:
                    logger.info(f"\n{'='*100}")
                    logger.info("🎯 STEP 1: APPLYING DEPARTMENT FILTER")
                    logger.info(f"{'='*100}")
                    templates = await self._apply_filter_and_capture(page, departments, base_url)
                else:
                    logger.info("\n⚠️  No department filter specified - fetching all templates")
                    templates = await self._capture_all_templates(page)
                
                if not templates:
                    logger.error("❌ No templates found!")
                    return

                # Limit templates if specified
                if max_templates:
                    templates = templates[:max_templates]
                    logger.info(f"📊 Limited to first {max_templates} templates")

                logger.info(f"\n✅ Found {len(templates)} template(s) to process")

                # Step 3: Process each template sequentially
                logger.info(f"\n{'='*100}")
                logger.info("📋 STEP 2: PROCESSING TEMPLATES")
                logger.info(f"{'='*100}")

                for idx, template in enumerate(templates, 1):
                    await self._process_template(
                        context,
                        template,
                        idx,
                        len(templates),
                        logo_media_id,
                        logo_width,
                        auto_publish,
                        base_url
                    )

                # Close the filter page
                await page.close()

                # Step 4: Generate report
                logger.info(f"\n{'='*100}")
                logger.info("📊 GENERATING REPORT")
                logger.info(f"{'='*100}")

                report_path = self._generate_excel_report()

                # Save detection log
                detection_log_path = logger.save_detection_log()

                # Summary
                duration = (datetime.now() - self.start_time).total_seconds()

                logger.info(f"\n{'='*100}")
                logger.info("✅ AUTOMATION COMPLETE!")
                logger.info(f"{'='*100}")
                logger.info(f"Total Templates: {len(templates)}")
                logger.info(f"Processed: {self.processed}")
                logger.info(f"Successful: {self.successful}")
                logger.info(f"Failed: {self.failed}")
                logger.info(f"Published: {self.published_count}")
                logger.info(f"Centered: {self.centered_count}")
                logger.info(f"Enlarged: {self.enlarged_count}")
                logger.info(f"Duration: {duration:.1f}s")
                logger.info(f"Report: {report_path}")
                logger.info(f"Detection Log: {detection_log_path}")
                logger.info(f"Main Log: {logger.log_file}")
                logger.info(f"{'='*100}")

            except Exception as e:
                logger.exception(f"❌ Fatal error: {e}")

    async def _apply_filter_and_capture(self, page: Page, departments: List[str], base_url: str) -> List[Dict]:
        """Apply department filter and capture templates via API"""

        templates = []
        response_received = asyncio.Event()

        async def handle_response(response):
            nonlocal templates
            if '/api/templatestore/u/search' in response.url:
                try:
                    data = await response.json()
                    if 'data' in data and 'hits' in data['data']:
                        hits = data['data']['hits']
                        if hits:
                            templates.extend(hits)
                            logger.info(f"   📥 Captured {len(hits)} templates from API")
                            response_received.set()
                except:
                    pass

        page.on('response', handle_response)

        # Department mapping
        dept_map = {'Sales': 0, 'Service': 1, 'Parts': 2}

        try:
            # Open dropdown
            logger.info("   1. Opening department dropdown...")
            await page.click('.ant-dropdown-trigger', timeout=5000)
            await asyncio.sleep(1)

            # Uncheck all first
            logger.info("   2. Unchecking all departments...")
            for dept_name in ['Sales', 'Service', 'Parts']:
                await page.evaluate(f"""
                    () => {{
                        const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map[dept_name]}];
                        if (cb && cb.checked) cb.click();
                    }}
                """)
                await asyncio.sleep(0.3)

            # Check selected departments
            logger.info(f"   3. Checking: {', '.join(departments)}")
            for dept_name in departments:
                if dept_name in dept_map:
                    await page.evaluate(f"""
                        () => {{
                            const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map[dept_name]}];
                            if (cb && !cb.checked) cb.click();
                        }}
                    """)
                    await asyncio.sleep(0.3)

            # Close dropdown
            logger.info("   4. Closing dropdown...")
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)

            # Wait for API response
            logger.info("   5. Waiting for API response...")
            try:
                await asyncio.wait_for(response_received.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("   ⚠️  API response timeout")

            page.remove_listener('response', handle_response)

            logger.info(f"   ✅ Filter applied: {len(templates)} templates captured")

        except Exception as e:
            logger.exception(f"   ❌ Filter application failed: {e}")
            page.remove_listener('response', handle_response)

        return templates

    async def _capture_all_templates(self, page: Page) -> List[Dict]:
        """Capture all templates without filtering"""

        templates = []
        response_received = asyncio.Event()

        async def handle_response(response):
            nonlocal templates
            if '/api/templatestore/u/search' in response.url:
                try:
                    data = await response.json()
                    if 'data' in data and 'hits' in data['data']:
                        templates.extend(data['data']['hits'])
                        response_received.set()
                except:
                    pass

        page.on('response', handle_response)
        await page.reload()

        try:
            await asyncio.wait_for(response_received.wait(), timeout=10.0)
        except:
            pass

        page.remove_listener('response', handle_response)
        return templates

    async def _process_template(self, context: BrowserContext, template: Dict, idx: int, total: int,
                                logo_media_id: str, logo_width: int, auto_publish: bool, base_url: str):
        """Process single template with all features"""

        template_id = template.get('templateId') or template.get('id')
        template_name = template.get('name', 'Unknown')

        logger.info(f"\n{'='*100}")
        logger.info(f"📄 TEMPLATE {idx}/{total}: {template_name}")
        logger.info(f"   ID: {template_id}")
        logger.info(f"   Departments: {', '.join(template.get('departments', []))}")
        logger.info(f"{'='*100}")

        try:
            # Open template edit page
            page = await context.new_page()
            edit_url = f"{base_url}/templates/edit/{template_id}"
            logger.info(f"   🌐 Opening: {edit_url}")
            await page.goto(edit_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(10)  # Increased from 5 to 10 seconds - warning icons take time to render

            # Detect logos to process
            detection_result = await self._detect_logos(page)

            # Log detailed detection results
            logger.log_detection(template_name, detection_result)

            warnings_count = detection_result['warningsCount']
            empty_count = detection_result['emptyCount']
            header_count = detection_result['headerCount']
            replace_count = detection_result.get('replaceCount', 0)

            # DEBUG: Print detection result
            logger.debug(f"   Detection result: warnings={warnings_count}, empty={empty_count}, headers={header_count}, replace={replace_count}")
            logger.debug(f"   Logo tables found: {len(detection_result.get('logoTables', []))}")
            logger.debug(f"   Logos to replace: {len(detection_result.get('logosToReplace', []))}")

            # Print debug messages from JavaScript
            debug_msgs = detection_result.get('debug', [])
            if debug_msgs:
                logger.debug(f"   JavaScript detection debug ({len(debug_msgs)} messages):")
                for msg in debug_msgs[:30]:  # Show first 30 debug messages
                    logger.debug(f"     {msg}")

            if warnings_count == 0 and empty_count == 0 and header_count == 0 and replace_count == 0:
                # No standard logo containers detected - check if we should add a header
                logger.info("   ℹ️  No Logo 1/2 containers or headers detected")
                logger.debug(f"   Detection returned: warnings={warnings_count}, empty={empty_count}, headers={header_count}")

                # Check container detection results to see if containers exist at all
                container_results = detection_result.get('containerCheckResults', [])
                all_containers_not_found = all(not c.get('found', False) for c in container_results)

                if all_containers_not_found:
                    logger.info("   📋 Logo 1/2 containers (by hardcoded IDs) not found - doing deeper check...")

                    # ADDITIONAL CHECK: Look for ANY logo containers or images in the template
                    has_any_logos = await page.evaluate("""
                        () => {
                            // Check for any warning icons (indicates logo containers exist)
                            const warnings = document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb');
                            if (warnings.length > 0) return { found: true, reason: 'warning icons', count: warnings.length };

                            // Check for any resizable image containers (common in templates)
                            const resizableImages = document.querySelectorAll('[class*="resizable"] img, [class*="Image"] img');
                            if (resizableImages.length > 0) return { found: true, reason: 'resizable images', count: resizableImages.length };

                            // Check for any SortableItem with images (template structure)
                            const sortableItems = document.querySelectorAll('[class*="SortableItem"]');
                            for (const item of sortableItems) {
                                const img = item.querySelector('img');
                                if (img && img.src && !img.src.includes('icon')) {
                                    return { found: true, reason: 'sortable item images', count: 1 };
                                }
                            }

                            return { found: false, reason: 'none', count: 0 };
                        }
                    """)

                    logger.debug(f"   Any logos check: {has_any_logos}")

                    if has_any_logos.get('found'):
                        logger.info(f"   ⚠️  Template has logos ({has_any_logos['reason']}: {has_any_logos['count']}) but IDs don't match hardcoded list")
                        logger.info(f"   ℹ️  This template uses a different structure - skipping to avoid duplicate header")
                        self.results.append({
                            'template': template_name,
                            'id': template_id,
                            'status': 'skipped',
                            'reason': f"Has logos but different structure ({has_any_logos['reason']})",
                            'logos_processed': 0,
                            'published': False
                        })
                        await page.close()
                        return

                    # No logos at all - check if #HEADER button is active (can add header)
                    logger.info("   ✅ No logos detected anywhere - checking if we can add header...")

                    button_state = await page.evaluate("""
                        () => {
                            const headerBtn = document.querySelector('#HEADER');
                            if (!headerBtn) return { found: false };

                            const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                            return {
                                found: true,
                                opacity: opacity,
                                isActive: opacity === 1.0,
                                isGrayed: opacity < 1.0
                            };
                        }
                    """)

                    logger.debug(f"   Header button state: {button_state}")

                    if button_state.get('found') and button_state.get('isActive'):
                        # Header button is active - we can add a header!
                        logger.info(f"   🎯 #HEADER button is active (opacity={button_state['opacity']}) - adding header with logos...")

                        header_added = await self._add_header_with_logo(page, logo_media_id)

                        if header_added:
                            logger.info("   ✅ Header added successfully!")

                            # Auto-publish if enabled
                            published = False
                            if auto_publish:
                                logger.info(f"\n   📤 Auto-publishing template...")
                                if await self._publish_template(page, template_name):
                                    published = True
                                    self.published_count += 1
                                    logger.info(f"   ✅ Template published successfully!")
                                else:
                                    logger.warning(f"   ⚠️  Publish failed or skipped")

                            self.processed += 1
                            self.successful += 1
                            self.results.append({
                                'template': template_name,
                                'id': template_id,
                                'status': 'success',
                                'action': 'header_added',
                                'logos_processed': 1,  # Count header as 1 logo
                                'published': published,
                                'departments': ', '.join(template.get('departments', []))
                            })

                            logger.info(f"\n   ✅ Template {idx} complete:")
                            logger.info(f"      Action: Header added with logo")
                            logger.info(f"      Published: {'✅' if published else '❌'}")

                            # Keep tab open for verification
                            # await page.close()
                            return
                        else:
                            logger.warning("   ⚠️  Failed to add header")
                            self.failed += 1
                            self.processed += 1
                            self.results.append({
                                'template': template_name,
                                'id': template_id,
                                'status': 'failed',
                                'reason': 'Header addition failed',
                                'logos_processed': 0,
                                'published': False
                            })
                            await page.close()
                            return

                    elif button_state.get('found') and button_state.get('isGrayed'):
                        logger.info(f"   ℹ️  #HEADER button is grayed (opacity={button_state['opacity']}) - header already exists but no empty positions")
                    else:
                        logger.info("   ℹ️  #HEADER button not found")

                # No action to take - skip template
                logger.info("   ⏭️  Skipping template")
                self.results.append({
                    'template': template_name,
                    'id': template_id,
                    'status': 'skipped',
                    'reason': 'No logos to process and cannot add header',
                    'logos_processed': 0,
                    'published': False
                })
                await page.close()
                return

            # Get replace count from detection result
            replace_count = detection_result.get('replaceCount', 0)
            logos_to_replace = detection_result.get('logosToReplace', [])

            logger.info(f"   ✅ Detected:")
            logger.info(f"      - Logos with warnings: {warnings_count}")
            logger.info(f"      - Logos without warnings (to replace): {replace_count}")
            logger.info(f"      - Empty Logo 1/2 containers: {empty_count}")
            logger.info(f"      - Empty header containers: {header_count}")

            logos_processed = 0
            logos_centered = 0
            logos_enlarged = 0

            # Process logos with warnings (CHANGE IMAGE)
            logger.debug(f"Starting warning logo processing: {warnings_count} warnings detected")
            template_departments = template.get('departments', [])
            logger.debug(f"Template departments for verification: {template_departments}")

            for logo_idx in range(1, warnings_count + 1):
                logger.info(f"\n   🎯 Processing warning logo {logo_idx}/{warnings_count}...")
                logger.debug(f"   Attempting REPLACE workflow for warning logo #{logo_idx}")

                if await self._replace_logo(page, logo_idx, logo_media_id, template_departments):
                    logos_processed += 1
                    logger.info(f"   ✅ Logo {logo_idx} replaced")
                    logger.log_action("REPLACE", f"Warning Logo {logo_idx}", True, "Used Change Image workflow")

                    # Center align
                    logger.debug(f"   Attempting to center warning logo #{logo_idx}")
                    if await self._center_logo(page, logo_idx):
                        logos_centered += 1
                        logger.log_action("CENTER", f"Warning Logo {logo_idx}", True)
                    else:
                        logger.log_action("CENTER", f"Warning Logo {logo_idx}", False)

                    # Enlarge
                    logger.debug(f"   Attempting to enlarge warning logo #{logo_idx} to {logo_width}px")
                    if await self._enlarge_logo(page, logo_idx, logo_media_id, logo_width):
                        logos_enlarged += 1
                        logger.log_action("ENLARGE", f"Warning Logo {logo_idx}", True, f"Target: {logo_width}px")
                    else:
                        logger.log_action("ENLARGE", f"Warning Logo {logo_idx}", False)
                else:
                    logger.warning(f"   ⚠️  Logo {logo_idx} replacement failed")
                    logger.log_action("REPLACE", f"Warning Logo {logo_idx}", False, "Change Image workflow failed")

            # Process logos WITHOUT warnings (CHANGE IMAGE - detected by table-based detection)
            logger.debug(f"Starting logo replacement (without warnings): {replace_count} logos detected")
            for logo_item in logos_to_replace:
                logo_idx = logo_item['index']
                logo_name = logo_item['name']
                current_alignment = logo_item.get('alignment', 'UNKNOWN')

                logger.info(f"\n   🎯 Replacing logo {logo_idx}/{replace_count}: {logo_name}...")
                logger.info(f"   Current alignment: {current_alignment} (will keep same position)")
                logger.debug(f"   Attempting REPLACE workflow for logo without warning")

                if await self._replace_logo_without_warning(page, logo_idx, logo_media_id):
                    logos_processed += 1
                    logger.info(f"   ✅ Logo replaced: {logo_name}")
                    logger.log_action("REPLACE", logo_name, True, f"Kept at {current_alignment} alignment")

                    # Do NOT center existing logos - keep them at their current alignment
                    logger.debug(f"   Keeping logo at {current_alignment} alignment (not centering)")

                    # Enlarge
                    logger.debug(f"   Attempting to enlarge logo to {logo_width}px")
                    if await self._enlarge_logo_without_warning(page, logo_idx, logo_media_id, logo_width):
                        logos_enlarged += 1
                        logger.log_action("ENLARGE", logo_name, True, f"Target: {logo_width}px")
                    else:
                        logger.log_action("ENLARGE", logo_name, False)
                else:
                    logger.warning(f"   ⚠️  Logo replacement failed: {logo_name}")
                    logger.log_action("REPLACE", logo_name, False, "Change Image workflow failed")

            # Process empty Logo 1/2 containers (INSERT IMAGE)
            logger.debug(f"Starting empty container processing: {empty_count} empty containers detected")
            for container in detection_result['emptyContainers']:
                container_name = container['name']
                container_id = container['id']
                logger.info(f"\n   🎯 Inserting logo into {container_name}...")
                logger.debug(f"   Container ID: {container_id}")
                logger.debug(f"   Attempting INSERT workflow for empty container")

                if await self._insert_logo_to_container(page, container, logo_media_id):
                    logos_processed += 1
                    logger.info(f"   ✅ Logo inserted into {container_name}")
                    logger.log_action("INSERT", container_name, True, f"ID: {container_id}")
                else:
                    logger.warning(f"   ⚠️  Failed to insert logo into {container_name}")
                    logger.log_action("INSERT", container_name, False, f"ID: {container_id}")

            # Process empty header containers (INSERT IMAGE FOR HEADERS)
            logger.debug(f"Starting header processing: {header_count} empty headers detected")
            for header in detection_result['headerContainers']:
                header_name = header['name']
                header_pos = header.get('position', 'unknown')
                logger.info(f"\n   🎯 Inserting logo into {header_name}...")
                logger.debug(f"   Header position: {header_pos}")
                logger.debug(f"   Attempting INSERT workflow for header container")

                if await self._insert_logo_to_header(page, header, logo_media_id):
                    logos_processed += 1
                    logger.info(f"   ✅ Logo inserted into {header_name}")
                    logger.log_action("INSERT", header_name, True, f"Position: {header_pos}")
                else:
                    logger.warning(f"   ⚠️  Failed to insert logo into {header_name}")
                    logger.log_action("INSERT", header_name, False, f"Position: {header_pos}")

            # Auto-publish if enabled and logos were processed
            published = False
            if auto_publish and logos_processed > 0:
                logger.info(f"\n   📤 Auto-publishing template...")
                if await self._publish_template(page, template_name):
                    published = True
                    self.published_count += 1
                    logger.info(f"   ✅ Template published successfully!")
                else:
                    logger.warning(f"   ⚠️  Publish failed or skipped")
            elif not auto_publish:
                logger.info(f"\n   ⏸️  Auto-publish disabled - skipping")

            # Update counters
            self.centered_count += logos_centered
            self.enlarged_count += logos_enlarged

            # Record results
            total_logos = warnings_count + empty_count + header_count
            if logos_processed == total_logos:
                self.successful += 1
                status = 'success'
            elif logos_processed > 0:
                self.successful += 1
                status = 'partial'
            else:
                self.failed += 1
                status = 'failed'

            self.processed += 1
            self.results.append({
                'template': template_name,
                'id': template_id,
                'status': status,
                'warnings': warnings_count,
                'empty_containers': empty_count,
                'empty_headers': header_count,
                'total_logos': total_logos,
                'logos_processed': logos_processed,
                'logos_centered': logos_centered,
                'logos_enlarged': logos_enlarged,
                'published': published,
                'departments': ', '.join(template.get('departments', []))
            })

            logger.info(f"\n   ✅ Template {idx} complete:")
            logger.info(f"      Processed: {logos_processed}/{total_logos}")
            logger.info(f"      Centered: {logos_centered}")
            logger.info(f"      Enlarged: {logos_enlarged}")
            logger.info(f"      Published: {'✅' if published else '❌'}")

            # Keep tab open for verification
            # await page.close()

        except Exception as e:
            logger.exception(f"   ❌ Error processing template: {e}")
            self.failed += 1
            self.processed += 1
            self.results.append({
                'template': template_name,
                'id': template_id,
                'status': 'error',
                'error': str(e),
                'logos_processed': 0,
                'published': False
            })

    async def _detect_logos(self, page: Page) -> Dict:
        """Detect all logos: warnings, empty Logo 1/2 containers, empty headers"""

        return await page.evaluate("""
            () => {
                const debug = [];

                // Find logos with warnings - UPDATED to handle new CSS class structure
                debug.push('=== WARNING DETECTION ===');

                // Try multiple selectors for warning icons (Tekion changes class hashes)
                const warningSelectors = [
                    '.templates_errorWarningIconsWithPopover_warningIcon__fT9Rzb2vrs',  // NEW class (2026)
                    '.icon-alert1',  // Generic icon class
                    '[class*="errorWarningIconsWithPopover_warningIcon"]',  // Partial match
                    '.templates_Image_warningIcon__hCZHMuhEmb'  // OLD class (legacy)
                ];

                let warnings = [];
                for (const selector of warningSelectors) {
                    warnings = Array.from(document.querySelectorAll(selector));
                    if (warnings.length > 0) {
                        debug.push(`Found ${warnings.length} warning icons using selector: ${selector}`);
                        break;
                    }
                }

                if (warnings.length === 0) {
                    debug.push('Found 0 warning icons (tried all selectors)');
                }

                // CRITICAL: Detect department for each warning logo to prevent wrong logo updates
                warnings.forEach((icon, idx) => {
                    const sortableItem = icon.closest('[class*="SortableItem"]');
                    if (sortableItem) {
                        // Detect department by checking container position and content
                        const department = detectLogoDepartment(sortableItem, icon);

                        sortableItem.setAttribute('data-logo-to-inspect', `warning-logo-${idx + 1}`);
                        sortableItem.setAttribute('data-logo-department', department || 'unknown');

                        debug.push(`  Warning ${idx + 1}: Marked sortableItem (Department: ${department || 'UNKNOWN'})`);
                    } else {
                        debug.push(`  Warning ${idx + 1}: No sortableItem found!`);
                    }
                });

                // Helper function to detect logo department
                function detectLogoDepartment(container, warningIcon) {
                    // Strategy 1: Check for department text near the logo
                    const nearbyText = container.innerText || container.textContent || '';
                    const upperText = nearbyText.toUpperCase();

                    if (upperText.includes('SERVICE')) return 'Service';
                    if (upperText.includes('SALES')) return 'Sales';
                    if (upperText.includes('PARTS')) return 'Parts';

                    // Strategy 2: Check parent containers for department indicators
                    let parent = container.parentElement;
                    let depth = 0;
                    while (parent && depth < 5) {
                        const parentText = (parent.innerText || parent.textContent || '').toUpperCase();
                        if (parentText.includes('SERVICE') && parentText.length < 1000) return 'Service';
                        if (parentText.includes('SALES') && parentText.length < 1000) return 'Sales';
                        if (parentText.includes('PARTS') && parentText.length < 1000) return 'Parts';
                        parent = parent.parentElement;
                        depth++;
                    }

                    // Strategy 3: Check logo position (header vs body)
                    const rect = container.getBoundingClientRect();
                    const isHeader = rect.top < 600;

                    if (isHeader) {
                        // Header logos are typically shared across all departments
                        return 'header';
                    }

                    // Unable to determine - mark as unknown
                    return 'unknown';
                }

                // Find empty Logo 1/2 containers (6 positions)
                debug.push('\\n=== LOGO 1/2 CONTAINER DETECTION ===');
                const containerIds = [
                    '6f0b8570-c4dc-45bd-b746-40e3af9af3bb',  // Logo 1 LEFT
                    '7653caa9-31b7-4e2b-8233-f0bda43672ea',  // Logo 1 CENTER
                    '47da3c0a-2c2b-4f8f-8a31-4ba8fdae03aa',  // Logo 1 RIGHT
                    '9fa2920b-10f8-48d2-9947-b014398d21be',  // Logo 2 LEFT
                    '983932ae-d79a-40fe-a9ba-df07c9beee47',  // Logo 2 CENTER
                    '9d454086-c1f2-4bf0-b4a7-8e95dc244aae'   // Logo 2 RIGHT
                ];

                const containerNames = ['Logo 1 LEFT', 'Logo 1 CENTER', 'Logo 1 RIGHT',
                                       'Logo 2 LEFT', 'Logo 2 CENTER', 'Logo 2 RIGHT'];

                const emptyContainers = [];
                const containerCheckResults = [];

                containerIds.forEach((id, idx) => {
                    const container = document.querySelector(`div.TEXT_TEMPLATE[id="${id}"][contenteditable="true"]`);
                    const checkResult = {
                        name: containerNames[idx],
                        id: id,
                        found: container !== null,
                        hasImage: false,
                        isEmpty: false,
                        htmlLength: 0
                    };

                    if (container) {
                        const hasImage = container.querySelector('img') !== null;
                        const htmlLength = container.innerHTML.trim().length;
                        const isEmpty = !hasImage && htmlLength < 300;

                        checkResult.hasImage = hasImage;
                        checkResult.htmlLength = htmlLength;
                        checkResult.isEmpty = isEmpty;

                        if (isEmpty) {
                            container.setAttribute('data-empty-container', `empty-${idx + 1}`);
                            emptyContainers.push({
                                index: idx + 1,
                                id: id,
                                name: containerNames[idx],
                                type: 'logo_container'
                            });
                        }
                    }

                    containerCheckResults.push(checkResult);
                    debug.push(`  ${checkResult.name}: found=${checkResult.found}, hasImage=${checkResult.hasImage}, isEmpty=${checkResult.isEmpty}`);
                });

                // FALLBACK: Table-based Logo 1/2 detection (if hardcoded IDs didn't work)
                debug.push('\\n=== TABLE-BASED LOGO DETECTION (Fallback) ===');
                const allTables = Array.from(document.querySelectorAll('table'));
                debug.push(`Scanning ${allTables.length} tables for logo containers...`);
                const logoTables = [];
                const logosToReplace = []; // NEW: Track logos without warnings that need replacement

                allTables.forEach((table, tableIdx) => {
                    const firstRow = table.querySelector('tr');
                    if (!firstRow) return;

                    const cells = Array.from(firstRow.querySelectorAll('td'));

                    // Logo containers have 4 or 5 columns
                    if (cells.length === 4 || cells.length === 5) {
                        const tableInfo = {
                            tableIndex: tableIdx,
                            positions: []
                        };

                        cells.forEach((cell, cellIdx) => {
                            const imageComponent = cell.querySelector('.templates_Image_imageComponent__tqwK7j9G7t');
                            const hasImage = imageComponent !== null;
                            // Updated warning selector to handle new CSS classes
                            const hasWarning = cell.querySelector('.templates_errorWarningIconsWithPopover_warningIcon__fT9Rzb2vrs, .icon-alert1, [class*="errorWarningIconsWithPopover_warningIcon"], .templates_Image_warningIcon__hCZHMuhEmb') !== null;
                            const textTemplate = cell.querySelector('.TEXT_TEMPLATE[contenteditable="true"]');
                            const isEmpty = !hasImage && textTemplate !== null;

                            let alignment;
                            if (cells.length === 4) {
                                // 4-cell table: LEFT, CENTER, RIGHT, EXTRA
                                alignment = cellIdx === 0 ? 'LEFT' :
                                          cellIdx === 1 ? 'CENTER' :
                                          cellIdx === 2 ? 'RIGHT' : 'EXTRA';
                            } else {
                                // 5-cell table: FAR_LEFT, LEFT, CENTER, RIGHT, FAR_RIGHT
                                alignment = cellIdx === 0 ? 'FAR_LEFT' :
                                          cellIdx === 1 ? 'LEFT' :
                                          cellIdx === 2 ? 'CENTER' :
                                          cellIdx === 3 ? 'RIGHT' : 'FAR_RIGHT';
                            }

                            tableInfo.positions.push({
                                cellIndex: cellIdx,
                                alignment: alignment,
                                hasImage: hasImage,
                                hasWarning: hasWarning,
                                isEmpty: isEmpty,
                                textTemplateId: textTemplate ? textTemplate.id : null,
                                imageComponent: imageComponent
                            });
                        });

                        // Only count as logo table if it has at least one image or empty position in first 3 columns
                        const relevantPositions = tableInfo.positions.slice(0, 3);
                        const hasRelevantContent = relevantPositions.some(p => p.hasImage || p.isEmpty);

                        if (hasRelevantContent) {
                            logoTables.push(tableInfo);
                            debug.push(`  Found logo table #${logoTables.length} (table index ${tableIdx}): ${cells.length} columns`);
                            tableInfo.positions.forEach(pos => {
                                if (pos.alignment !== 'EXTRA' && pos.alignment !== 'FAR_LEFT' && pos.alignment !== 'FAR_RIGHT') {
                                    debug.push(`    ${pos.alignment}: hasImage=${pos.hasImage}, hasWarning=${pos.hasWarning}, isEmpty=${pos.isEmpty}, id=${pos.textTemplateId}`);
                                }
                            });
                        }
                    }
                });

                debug.push(`Found ${logoTables.length} logo tables total`);

                // Process table-based detection if we found logo tables
                if (logoTables.length > 0) {
                    debug.push('\\n=== PROCESSING TABLE-BASED DETECTION ===');

                    logoTables.forEach((logoTable, tableIdx) => {
                        const logoNumber = tableIdx + 1; // Logo 1, Logo 2, etc.

                        logoTable.positions.forEach((pos, posIdx) => {
                            if (pos.alignment === 'EXTRA') return; // Skip 4th column

                            const containerName = `Logo ${logoNumber} ${pos.alignment}`;

                            // PRIORITY 1: Logos WITH warnings need replacement (wrong logo)
                            // Logos WITHOUT warnings are correct - skip them!
                            if (pos.hasImage && pos.hasWarning) {
                                // Mark image component for replacement
                                if (pos.imageComponent) {
                                    const replaceIdx = logosToReplace.length + 1;
                                    pos.imageComponent.setAttribute('data-logo-to-replace', `replace-logo-${replaceIdx}`);

                                    logosToReplace.push({
                                        index: replaceIdx,
                                        name: containerName,
                                        type: 'logo_with_warning_table_based',
                                        tableIndex: tableIdx,
                                        cellIndex: pos.cellIndex,
                                        alignment: pos.alignment,
                                        hasWarning: true,
                                        needsCentering: false  // Keep at current alignment
                                    });

                                    debug.push(`  Found logo to REPLACE: ${containerName} (hasWarning=true, keepAlignment=${pos.alignment})`);
                                }
                            }
                            // Skip logos without warnings - they're already correct!
                            else if (pos.hasImage && !pos.hasWarning) {
                                debug.push(`  Skipping ${containerName}: Logo exists without warning (already correct)`);
                            }
                            // PRIORITY 2: Empty CENTER positions can have logos inserted (only if hardcoded IDs didn't find them)
                            else if (pos.isEmpty && pos.alignment === 'CENTER' && emptyContainers.length === 0) {
                                const containerId = pos.textTemplateId || `table-${tableIdx}-cell-${pos.cellIndex}`;

                                emptyContainers.push({
                                    index: emptyContainers.length + 1,
                                    id: containerId,
                                    name: containerName,
                                    type: 'logo_container_table_based',
                                    tableIndex: tableIdx,
                                    cellIndex: pos.cellIndex,
                                    alignment: pos.alignment
                                });

                                debug.push(`  Added empty CENTER: ${containerName} (ID: ${containerId})`);
                            }
                            // PRIORITY 3: Empty LEFT/RIGHT positions are skipped (will be empty after centering)
                            else if (pos.isEmpty && pos.alignment !== 'CENTER') {
                                debug.push(`  Skipping empty ${pos.alignment}: ${containerName} (only CENTER positions get new logos)`);
                            }
                        });
                    });

                    debug.push(`\\nTable-based detection summary:`);
                    debug.push(`  - Logos to REPLACE: ${logosToReplace.length}`);
                    debug.push(`  - Empty CENTER positions: ${emptyContainers.length}`);
                }

                // Find empty HEADER containers
                debug.push('\\n=== HEADER CONTAINER DETECTION ===');
                const headerContainers = [];
                const headerCheckResults = [];
                const tables = Array.from(document.querySelectorAll('table'));
                debug.push(`Found ${tables.length} tables`);

                for (const table of tables) {
                    const firstRow = table.querySelector('tr');
                    if (!firstRow) continue;

                    const tds = Array.from(firstRow.querySelectorAll('td'));
                    debug.push(`  Table has ${tds.length} cells in first row`);

                    if (tds.length === 3) {
                        debug.push(`  Checking first 2 cells for header logos...`);
                        for (let i = 0; i < 2; i++) {
                            const td = tds[i];
                            const elementContainer = td.querySelector('[class*="elementContainer"]');

                            const headerCheck = {
                                position: i + 1,
                                hasContainer: elementContainer !== null,
                                hasImage: false,
                                hasTextTemplate: false,
                                isEmpty: false
                            };

                            if (elementContainer) {
                                const hasImage = elementContainer.querySelector('img') !== null;
                                const textTemplate = elementContainer.querySelector('.TEXT_TEMPLATE') ||
                                                    elementContainer.querySelector('[contenteditable="true"]');

                                headerCheck.hasImage = hasImage;
                                headerCheck.hasTextTemplate = textTemplate !== null;
                                headerCheck.isEmpty = !hasImage && textTemplate !== null;

                                if (!hasImage && textTemplate) {
                                    const headerId = textTemplate.id || `header-${Date.now()}-${i}`;
                                    textTemplate.setAttribute('data-empty-header', `header-${i + 1}`);
                                    elementContainer.setAttribute('data-header-container', `header-${i + 1}`);

                                    headerContainers.push({
                                        index: headerContainers.length + 1,
                                        id: headerId,
                                        name: `Header Logo ${i + 1}`,
                                        type: 'header',
                                        position: i + 1
                                    });
                                }
                            }

                            headerCheckResults.push(headerCheck);
                            debug.push(`    Position ${i + 1}: hasContainer=${headerCheck.hasContainer}, hasImage=${headerCheck.hasImage}, isEmpty=${headerCheck.isEmpty}`);
                        }

                        if (headerContainers.length > 0) {
                            debug.push(`  Found ${headerContainers.length} empty header containers, stopping table search`);
                            break;
                        }
                    }
                }

                return {
                    warningsCount: warnings.length,
                    emptyCount: emptyContainers.length,
                    headerCount: headerContainers.length,
                    emptyContainers: emptyContainers,
                    headerContainers: headerContainers,
                    containerCheckResults: containerCheckResults,
                    headerCheckResults: headerCheckResults,
                    logoTables: logoTables,
                    logosToReplace: logosToReplace || [],
                    replaceCount: (logosToReplace || []).length,
                    debug: debug
                };
            }
        """)

    async def _replace_logo(self, page: Page, logo_idx: int, logo_media_id: str,
                           template_departments: List[str] = None) -> bool:
        """Replace logo with warning icon using Change Image workflow

        Args:
            page: Playwright page object
            logo_idx: Index of logo to replace (1-based)
            logo_media_id: Media ID of replacement logo
            template_departments: List of departments this template belongs to (for verification)
        """

        try:
            # Find the outer container (SortableItem) marked with data attribute
            outer_container = await page.query_selector(f'[data-logo-to-inspect="warning-logo-{logo_idx}"]')
            if not outer_container:
                return False

            # CRITICAL: Verify logo department matches template department
            logo_department = await outer_container.get_attribute('data-logo-department')

            if template_departments and logo_department:
                # Check if logo department matches any of the template's departments
                logo_dept_normalized = logo_department.lower()
                template_depts_normalized = [d.lower() for d in template_departments]

                # Allow 'header' logos (shared across departments) and 'unknown' (can't determine)
                if logo_dept_normalized not in ['header', 'unknown']:
                    if logo_dept_normalized not in template_depts_normalized:
                        logger.warning(
                            f"⚠️  DEPARTMENT MISMATCH DETECTED! "
                            f"Logo department: '{logo_department}', "
                            f"Template departments: {template_departments}"
                        )
                        logger.warning(f"   Skipping logo {logo_idx} to prevent wrong department update")
                        return False
                    else:
                        logger.info(f"   ✅ Department verified: Logo '{logo_department}' matches template {template_departments}")
                else:
                    logger.info(f"   ℹ️  Logo department: '{logo_department}' - allowing update")
            elif logo_department:
                logger.warning(f"   ⚠️  No template departments provided for verification (logo dept: {logo_department})")
            else:
                logger.warning(f"   ⚠️  Could not detect logo department - proceeding with caution")

            # BREAKTHROUGH FIX: Hover over SUB-CONTAINER (imageComponent), not outer container!
            # The toolbar only appears when hovering over templates_Image_imageComponent
            sub_container = await outer_container.query_selector('[class*="imageComponent"]')
            if not sub_container:
                logger.warning(f"Sub-container (imageComponent) not found for logo {logo_idx}")
                return False

            # Hover over the sub-container to reveal toolbar
            await sub_container.hover(force=True)
            await asyncio.sleep(3)

            # Check if popup already open
            popup_open = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    return popup && popup.getBoundingClientRect().width > 0;
                }
            """)

            if not popup_open:
                # Click Change Image icon (now toolbar should be visible!)
                change_clicked = await page.evaluate(f"""
                    () => {{
                        const container = document.querySelector('[data-logo-to-inspect="warning-logo-{logo_idx}"]');
                        if (!container) return {{ clicked: false, reason: 'Container not found' }};

                        // Find the sub-container first
                        const subContainer = container.querySelector('[class*="imageComponent"]');
                        if (!subContainer) return {{ clicked: false, reason: 'Sub-container not found' }};

                        // Look for Change Image icon within the sub-container area
                        const changeIcon = subContainer.querySelector('[aria-label="icon-switch"]') ||
                                          subContainer.querySelector('[title="Change Image"]') ||
                                          container.querySelector('[aria-label="icon-switch"]') ||
                                          container.querySelector('[title="Change Image"]');

                        if (changeIcon) {{
                            changeIcon.click();
                            return {{ clicked: true }};
                        }}
                        return {{ clicked: false, reason: 'Change Image icon not found in toolbar' }};
                    }}
                """)

                if not change_clicked['clicked']:
                    logger.warning(f"Failed to click Change Image: {change_clicked.get('reason', 'Unknown')}")
                    return False

                await asyncio.sleep(3)

            # Select Tilton.png (tile #1)
            selection = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { success: false };

                    const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    if (tiles.length === 0) return { success: false };

                    const targetTile = tiles[0];
                    const topLayer = targetTile.querySelector('[role="button"]') ||
                                    targetTile.querySelector('[class*="topLayer"]');

                    if (topLayer) {
                        topLayer.click();
                        return { success: true };
                    }
                    return { success: false };
                }
            """)

            if not selection['success']:
                return False

            await asyncio.sleep(1.5)

            # Click INSERT
            insert_result = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { clicked: false };

                    const buttons = Array.from(popup.querySelectorAll('button'));
                    const insertBtn = buttons.find(b => b.textContent.trim().toLowerCase().includes('insert'));

                    if (insertBtn && !insertBtn.disabled) {
                        insertBtn.click();
                        return { clicked: true };
                    }
                    return { clicked: false };
                }
            """)

            if not insert_result['clicked']:
                return False

            await asyncio.sleep(2)

            # Verify popup closed
            popup_closed = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    return !popup || popup.getBoundingClientRect().width === 0;
                }
            """)

            return popup_closed

        except Exception as e:
            logger.exception(f"      Error replacing logo: {e}")
            return False

    async def _replace_logo_without_warning(self, page: Page, logo_idx: int, logo_media_id: str) -> bool:
        """Replace logo WITHOUT warning icon (detected by table-based detection) using Change Image workflow"""

        try:
            # Find the image component marked for replacement (this is already the imageComponent)
            image_component = await page.query_selector(f'[data-logo-to-replace="replace-logo-{logo_idx}"]')
            if not image_component:
                logger.warning(f"Image component not found for replace-logo-{logo_idx}")
                return False

            # BREAKTHROUGH FIX: Hover over the imageComponent (sub-container) to reveal toolbar
            # The data-logo-to-replace is set on templates_Image_imageComponent, which is the correct element!
            logger.debug(f"Hovering over image component to reveal toolbar...")
            await image_component.hover(force=True)
            await asyncio.sleep(3)  # Wait for toolbar to appear

            # Check if media library popup is already open
            popup_open = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    return popup && popup.getBoundingClientRect().width > 0;
                }
            """)

            if not popup_open:
                # Click the Change Image icon (icon-switch) using selector instead of coordinates
                # This is more reliable than coordinate-based clicking
                change_clicked = await page.evaluate(f"""
                    () => {{
                        const imageComponent = document.querySelector('[data-logo-to-replace="replace-logo-{logo_idx}"]');
                        if (!imageComponent) return {{ clicked: false, reason: 'Image component not found' }};

                        // Find the Change Image icon - it should be visible after hover
                        // Look in the parent SortableItem container where the toolbar appears
                        const sortableItem = imageComponent.closest('[class*="SortableItem"]');
                        if (!sortableItem) return {{ clicked: false, reason: 'SortableItem not found' }};

                        const changeIcon = sortableItem.querySelector('[aria-label="icon-switch"]') ||
                                          sortableItem.querySelector('[title="Change Image"]') ||
                                          imageComponent.querySelector('[aria-label="icon-switch"]') ||
                                          imageComponent.querySelector('[title="Change Image"]');

                        if (changeIcon) {{
                            changeIcon.click();
                            return {{ clicked: true }};
                        }}
                        return {{ clicked: false, reason: 'Change Image icon not found in toolbar' }};
                    }}
                """)

                if not change_clicked['clicked']:
                    logger.warning(f"Failed to click Change Image icon: {change_clicked.get('reason', 'Unknown')}")
                    return False

                await asyncio.sleep(2)

                # Check if popup opened after clicking Change Image icon
                popup_open_after_click = await page.evaluate("""
                    () => {
                        const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                        return popup && popup.getBoundingClientRect().width > 0;
                    }
                """)

                if popup_open_after_click:
                    logger.debug("Successfully opened popup via Change Image icon")
                else:
                    logger.warning("Popup didn't open after clicking Change Image icon")
                    return False

            await asyncio.sleep(2)

            # Wait for media library popup
            popup_visible = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    return popup && popup.getBoundingClientRect().width > 0;
                }
            """)

            if not popup_visible:
                logger.warning("Media library popup did not appear")
                return False

            # Select Tilton.png (tile #1)
            selection = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { success: false };

                    const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    if (tiles.length === 0) return { success: false };

                    const targetTile = tiles[0];
                    const topLayer = targetTile.querySelector('[role="button"]') ||
                                    targetTile.querySelector('[class*="topLayer"]');

                    if (topLayer) {
                        topLayer.click();
                        return { success: true };
                    }
                    return { success: false };
                }
            """)

            if not selection['success']:
                logger.warning("Could not select logo from media library")
                return False

            await asyncio.sleep(1.5)

            # Click INSERT
            insert_result = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { clicked: false };

                    const buttons = Array.from(popup.querySelectorAll('button'));
                    const insertBtn = buttons.find(b => b.textContent.trim().toLowerCase().includes('insert'));

                    if (insertBtn && !insertBtn.disabled) {
                        insertBtn.click();
                        return { clicked: true };
                    }
                    return { clicked: false };
                }
            """)

            if not insert_result['clicked']:
                logger.warning("Could not click INSERT button")
                return False

            await asyncio.sleep(2)

            # Verify popup closed
            popup_closed = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    return !popup || popup.getBoundingClientRect().width === 0;
                }
            """)

            return popup_closed

        except Exception as e:
            logger.error(f"Error in _replace_logo_without_warning: {e}")
            return False

    async def _center_logo_without_warning(self, page: Page, logo_idx: int) -> bool:
        """Center align a logo that was replaced (without warning icon)"""
        try:
            # For now, return True as placeholder
            # TODO: Implement center alignment logic
            logger.debug(f"Center alignment for logo {logo_idx} - not yet implemented")
            return False
        except Exception as e:
            logger.error(f"Error in _center_logo_without_warning: {e}")
            return False

    async def _enlarge_logo_without_warning(self, page: Page, logo_idx: int, logo_media_id: str, logo_width: str) -> bool:
        """Enlarge a logo that was replaced (without warning icon)"""
        try:
            # For now, return True as placeholder
            # TODO: Implement enlarge logic
            logger.debug(f"Enlarge logo {logo_idx} to {logo_width} - not yet implemented")
            return False
        except Exception as e:
            logger.error(f"Error in _enlarge_logo_without_warning: {e}")
            return False

    async def _center_logo(self, page: Page, logo_idx: int) -> bool:
        """Center align a logo"""

        try:
            container = await page.query_selector(f'[data-logo-to-inspect="warning-logo-{logo_idx}"]')
            if not container:
                return False

            await container.hover(force=True)
            await asyncio.sleep(1.5)

            center_result = await page.evaluate(f"""
                () => {{
                    const container = document.querySelector('[data-logo-to-inspect="warning-logo-{logo_idx}"]');
                    if (!container) return {{ clicked: false }};

                    const centerBtn = container.querySelector('[title="Center Align"]') ||
                                     container.querySelector('[aria-label="icon-center-align"]') ||
                                     document.querySelector('[title="Center Align"]');

                    if (centerBtn) {{
                        centerBtn.click();
                        return {{ clicked: true }};
                    }}
                    return {{ clicked: false }};
                }}
            """)

            if center_result['clicked']:
                await asyncio.sleep(0.5)
                return True
            return False

        except:
            return False

    async def _enlarge_logo(self, page: Page, logo_idx: int, logo_media_id: str, target_width: int) -> bool:
        """Detect and enlarge logo to target width"""

        try:
            # Detect current size
            detection = await page.evaluate(f"""
                () => {{
                    const MEDIA_ID = "{logo_media_id}";
                    const allLogos = Array.from(document.querySelectorAll('img'))
                        .filter(i => i.src.includes(MEDIA_ID));

                    if (allLogos.length === 0 || {logo_idx} > allLogos.length)
                        return {{ found: false }};

                    const img = allLogos[{logo_idx} - 1];
                    if (!img) return {{ found: false }};

                    const rect = img.getBoundingClientRect();
                    return {{
                        found: true,
                        currentWidth: Math.round(rect.width),
                        currentHeight: Math.round(rect.height)
                    }};
                }}
            """)

            if not detection.get('found'):
                return False

            current_w = detection['currentWidth']

            # Check if enlargement needed
            if current_w >= target_width:
                return True  # Already at target size

            # Enlarge
            enlarge_result = await page.evaluate(f"""
                () => {{
                    const MEDIA_ID = "{logo_media_id}";
                    const TARGET_WIDTH = {target_width};

                    const allLogos = Array.from(document.querySelectorAll('img'))
                        .filter(i => i.src.includes(MEDIA_ID));

                    if (allLogos.length === 0) return {{ success: false }};

                    const img = allLogos[{logo_idx} - 1];
                    if (!img) return {{ success: false }};

                    // Find container
                    let container = img.parentElement;
                    for (let i = 0; i < 5; i++) {{
                        if (!container) break;
                        if ((container.className || '').includes('resizable') ||
                            (container.className || '').includes('Image')) break;
                        container = container.parentElement;
                    }}

                    if (!container) container = img.parentElement;

                    // Apply width
                    container.style.width = TARGET_WIDTH + 'px';
                    container.style.maxWidth = TARGET_WIDTH + 'px';
                    img.style.width = TARGET_WIDTH + 'px';
                    img.style.maxWidth = TARGET_WIDTH + 'px';
                    img.style.height = 'auto';

                    container.offsetHeight; // Force reflow

                    const afterRect = img.getBoundingClientRect();
                    return {{
                        success: true,
                        afterWidth: Math.round(afterRect.width)
                    }};
                }}
            """)

            if enlarge_result.get('success'):
                await asyncio.sleep(0.5)
                return True
            return False

        except:
            return False

    async def _insert_logo_to_container(self, page: Page, container_info: Dict, logo_media_id: str) -> bool:
        """Insert logo into empty Logo 1/2 container"""

        try:
            # Focus container
            target_selector = f'div.TEXT_TEMPLATE[id="{container_info["id"]}"][contenteditable="true"]'

            try:
                await page.wait_for_selector(target_selector, timeout=5000)
                await page.click(target_selector)
                await asyncio.sleep(1.5)
            except:
                return False

            # Click Insert Image button
            try:
                await page.click('.icon-insert-image[aria-label="icon-insert-image"]', timeout=5000)
                await asyncio.sleep(2.5)
            except:
                return False

            # Wait for media library
            modal_found = False
            for selector in ['[class*="modal"]', '[role="dialog"]']:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    modal_found = True
                    break
                except:
                    continue

            if not modal_found:
                return False

            await asyncio.sleep(1.5)

            # Select logo using topLayer
            selection = await page.evaluate("""
                async () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { clicked: false };

                    const allTiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    if (allTiles.length === 0) return { clicked: false };

                    const tile = allTiles[0];
                    const topLayer = tile.querySelector('[class*="topLayer"]') ||
                                    tile.querySelector('[role="button"]');

                    if (topLayer) {
                        topLayer.click();
                        return { clicked: true };
                    }
                    return { clicked: false };
                }
            """)

            if not selection['clicked']:
                return False

            await asyncio.sleep(2)

            # Click INSERT
            insert_result = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { clicked: false };

                    const buttons = Array.from(popup.querySelectorAll('button'));
                    const insertBtn = buttons.find(b => b.textContent.trim().toLowerCase().includes('insert'));

                    if (insertBtn && !insertBtn.disabled) {
                        insertBtn.click();
                        return { clicked: true };
                    }
                    return { clicked: false };
                }
            """)

            if not insert_result['clicked']:
                return False

            await asyncio.sleep(2)
            return True

        except:
            return False

    async def _insert_logo_to_header(self, page: Page, header_info: Dict, logo_media_id: str) -> bool:
        """Insert logo into empty header container"""

        try:
            # Click the header container by position
            clicked = await page.evaluate(f"""
                () => {{
                    const headerContainer = document.querySelector('[data-header-container="header-{header_info['position']}"]');
                    if (!headerContainer) return {{ success: false }};

                    const textTemplate = headerContainer.querySelector('.TEXT_TEMPLATE') ||
                                        headerContainer.querySelector('[contenteditable="true"]');

                    if (textTemplate) {{
                        textTemplate.click();
                        textTemplate.focus();
                        return {{ success: true }};
                    }}
                    return {{ success: false }};
                }}
            """)

            if not clicked['success']:
                return False

            await asyncio.sleep(1.5)

            # Click Insert Image
            try:
                await page.click('.icon-insert-image[aria-label="icon-insert-image"]', timeout=5000)
                await asyncio.sleep(2.5)
            except:
                return False

            # Wait for modal
            modal_found = False
            for selector in ['[class*="modal"]', '[role="dialog"]']:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    modal_found = True
                    break
                except:
                    continue

            if not modal_found:
                return False

            await asyncio.sleep(1.5)

            # Select logo
            selection = await page.evaluate("""
                async () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { clicked: false };

                    const allTiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    if (allTiles.length === 0) return { clicked: false };

                    const tile = allTiles[0];
                    const topLayer = tile.querySelector('[class*="topLayer"]') ||
                                    tile.querySelector('[role="button"]');

                    if (topLayer) {
                        topLayer.click();
                        return { clicked: true };
                    }
                    return { clicked: false };
                }
            """)

            if not selection['clicked']:
                return False

            await asyncio.sleep(2)

            # Click INSERT
            insert_result = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { clicked: false };

                    const buttons = Array.from(popup.querySelectorAll('button'));
                    const insertBtn = buttons.find(b => b.textContent.trim().toLowerCase().includes('insert'));

                    if (insertBtn && !insertBtn.disabled) {
                        insertBtn.click();
                        return { clicked: true };
                    }
                    return { clicked: false };
                }
            """)

            if not insert_result['clicked']:
                return False

            await asyncio.sleep(2)
            return True

        except:
            return False

    async def _add_header_with_logo(self, page: Page, logo_media_id: str) -> bool:
        """
        Add new header when template has no Logo 1/2 containers.
        This is used for templates like CPRA that don't have the standard layout.

        Workflow:
        1. Check if #HEADER button is active (opacity=1.0)
        2. Click #HEADER button
        3. Click "+ Add Header" button
        4. Select first template from popup
        5. Click Insert
        6. Add logos to the header positions

        Returns:
            True if header added successfully, False otherwise
        """

        try:
            logger.info("      ➕ Adding new header with logo...")

            # Step 1: Check #HEADER button state
            logger.debug("      Step 1: Checking #HEADER button state...")

            button_state = await page.evaluate("""
                () => {
                    const headerBtn = document.querySelector('#HEADER');
                    if (!headerBtn) return { found: false };

                    const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                    return {
                        found: true,
                        opacity: opacity,
                        isActive: opacity === 1.0,
                        isGrayed: opacity < 1.0
                    };
                }
            """)

            if not button_state['found']:
                logger.warning("      ⚠️  #HEADER button not found in DOM")
                return False

            if button_state['isGrayed']:
                logger.warning(f"      ⚠️  #HEADER button is grayed (opacity={button_state['opacity']}) - header already exists")
                return False

            logger.debug(f"      ✅ #HEADER button is active (opacity={button_state['opacity']})")

            # Step 2: Click #HEADER button
            logger.debug("      Step 2: Clicking #HEADER button...")

            header_clicked = await page.evaluate("""
                () => {
                    const headerBtn = document.querySelector('#HEADER');
                    if (!headerBtn) return false;
                    headerBtn.click();
                    return true;
                }
            """)

            if not header_clicked:
                logger.warning("      ⚠️  Failed to click #HEADER button")
                return False

            logger.debug("      ✅ #HEADER button clicked")
            await asyncio.sleep(2)

            # Step 3: Find and click "+ Add Header" button
            logger.debug("      Step 3: Finding '+ Add Header' button...")

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
                logger.warning("      ⚠️  '+ Add Header' button not found")
                return False

            logger.debug("      Clicking '+ Add Header' button...")
            add_header_btn = await page.query_selector('[data-add-header-btn="true"]')
            await add_header_btn.click()
            await asyncio.sleep(2)

            # Step 4: Verify "Insert Header" popup opened
            logger.debug("      Step 4: Verifying 'Insert Header' popup...")

            popup_opened = await page.evaluate("""
                () => {
                    const modal = document.querySelector('.ant-modal');
                    if (!modal) return false;

                    const title = modal.querySelector('.ant-modal-title');
                    return title && title.textContent.includes('Insert Header');
                }
            """)

            if not popup_opened:
                logger.warning("      ⚠️  'Insert Header' popup not found")
                return False

            logger.debug("      ✅ 'Insert Header' popup opened")

            # Step 5: Select first template (radio button)
            logger.debug("      Step 5: Selecting header template...")

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
                logger.warning("      ⚠️  Radio button not found")
                return False

            logger.debug("      ✅ Header template selected")
            await asyncio.sleep(1)

            # Step 6: Click Insert button
            logger.debug("      Step 6: Clicking Insert...")

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
                logger.warning("      ⚠️  Insert button not found")
                return False

            logger.debug("      ✅ Insert clicked")
            await asyncio.sleep(3)

            # Step 7: Verify header was added (button should be grayed now)
            logger.debug("      Step 7: Verifying header added...")

            header_added = await page.evaluate("""
                () => {
                    const headerBtn = document.querySelector('#HEADER');
                    if (!headerBtn) return false;

                    const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                    return opacity < 1.0;  // Should be grayed after adding
                }
            """)

            if header_added:
                logger.info("      ✅ Header added successfully!")
                logger.log_action("ADD_HEADER", "New Header", True, "Header structure created")
                return True
            else:
                logger.warning("      ⚠️  Header verification failed")
                logger.log_action("ADD_HEADER", "New Header", False, "Button still active after insert")
                return False

        except Exception as e:
            logger.exception(f"      ❌ Error adding header: {e}")
            logger.log_action("ADD_HEADER", "New Header", False, f"Exception: {str(e)}")
            return False

    async def _publish_template(self, page: Page, template_name: str) -> bool:
        """Publish template with 2-click workflow"""

        try:
            logger.info(f"      Step 1: Clicking main PUBLISH button...")

            # Find visible publish button
            publish_btns = await page.query_selector_all('button:has-text("Publish")')

            main_publish = None
            for btn in publish_btns:
                try:
                    box = await btn.bounding_box()
                    if box and box['x'] > 100:  # Avoid hidden buttons at 0,0
                        main_publish = btn
                        break
                except:
                    continue

            if not main_publish:
                logger.warning("      ⚠️  Publish button not found")
                return False

            # Click #1
            await main_publish.click()
            logger.info("      ✅ Clicked PUBLISH (1st click)")
            await asyncio.sleep(2.5)

            # Check if modal opened
            logger.info("      Step 2: Checking for modal...")

            modal_open = await page.evaluate("""
                () => {
                    const modal = document.querySelector('.ant-modal');
                    return modal && modal.getBoundingClientRect().width > 0;
                }
            """)

            if not modal_open:
                logger.info("      ⚠️  No modal - changes might be auto-saved")
                return True

            logger.info("      Step 3: Clicking PUBLISH in modal (2nd click)...")

            # Click #2 in modal
            modal_publish = await page.query_selector('.ant-modal button:has-text("Publish")')

            if modal_publish:
                await modal_publish.click()
                logger.info("      ✅ Clicked modal PUBLISH (2nd click)")
            else:
                # JavaScript fallback
                clicked = await page.evaluate("""
                    () => {
                        const modal = document.querySelector('.ant-modal');
                        if (modal) {
                            const btn = Array.from(modal.querySelectorAll('button'))
                                .find(b => b.innerText === 'Publish');
                            if (btn) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)

                if clicked:
                    logger.info("      ✅ Clicked via JavaScript (2nd click)")
                else:
                    logger.warning("      ⚠️  Could not click modal button")
                    return False

            await asyncio.sleep(2.5)

            # Verify modal closed
            logger.info("      Step 4: Verifying publish...")

            modal_closed = await page.evaluate("""
                () => {
                    const modal = document.querySelector('.ant-modal');
                    return !modal || modal.getBoundingClientRect().width === 0;
                }
            """)

            if modal_closed:
                logger.info("      ✅ Publish verified!")
                return True
            else:
                logger.warning("      ⚠️  Modal still open")
                return False

        except Exception as e:
            logger.exception(f"      ❌ Publish error: {e}")
            return False

    def _generate_excel_report(self) -> str:
        """Generate Excel report with results"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"temp_logo_results_FINAL_{timestamp}.xlsx"

        try:
            df = pd.DataFrame(self.results)

            # Reorder columns
            cols = ['template', 'id', 'status', 'logos_processed', 'warnings',
                   'empty_containers', 'empty_headers', 'total_logos',
                   'logos_centered', 'logos_enlarged', 'published', 'departments']

            # Only include columns that exist
            cols = [c for c in cols if c in df.columns]
            df = df[cols]

            # Write to Excel
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Results', index=False)

                # Auto-adjust column widths
                worksheet = writer.sheets['Results']
                for idx, col in enumerate(df.columns, 1):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)

            logger.info(f"   ✅ Excel report generated: {filename}")
            return filename

        except Exception as e:
            logger.exception(f"   ❌ Error generating report: {e}")
            return "report_generation_failed.xlsx"


# Main entry point
async def main():
    """Main entry point for the script"""

    parser = argparse.ArgumentParser(description='Temp Logo Adding Final - Complete Automation')
    parser.add_argument('--departments', '-d', nargs='+', choices=['Sales', 'Service', 'Parts'],
                       help='Department(s) to filter')
    parser.add_argument('--all', action='store_true', help='Process all templates (no filter)')
    parser.add_argument('--max', '-m', type=int, help='Maximum templates to process')
    parser.add_argument('--no-publish', action='store_true', help='Disable auto-publish')

    args = parser.parse_args()

    # Determine departments
    if args.all:
        departments = None
    elif args.departments:
        departments = args.departments
    else:
        # Default to Service & Parts
        departments = ['Service', 'Parts']

    # Create service and run
    service = TempLogoAdditionFinalService()

    await service.run(
        departments=departments,
        max_templates=args.max,
        auto_publish=not args.no_publish
    )


if __name__ == "__main__":
    asyncio.run(main())


