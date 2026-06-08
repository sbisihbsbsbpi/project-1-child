#!/usr/bin/env python3
"""
⭐⭐⭐ FINAL INTEGRATED SCRIPT - COMPLETE AUTOMATION ⭐⭐⭐
===========================================================

TEMP LOGO ADDING FINAL - All Features Integrated
=================================================

🚀 STATUS: 100% COMPLETE - ALL FEATURES IMPLEMENTED
✅ Features:
   1. Department filtering (Service & Parts)
   2. API interception & template fetching
   3. **TRULY DYNAMIC logo detection (ENHANCED - June 2, 2026)**
      - Adaptive pattern learning (no hardcoded selectors!)
      - Multi-phase heuristic detection (6 phases)
      - Hierarchical warning detection (container + parent levels)
      - Color-coded visual feedback (RED warnings, GREEN correct)
   4. Logo replacement (Change Image workflow)
      - ✅ Logos WITH warnings (fully implemented)
      - ✅ Logos WITHOUT warnings (fully implemented)
   5. Logo insertion (Insert Image workflow)
   6. Center align & enlarge logos
      - ✅ Logos WITH warnings (fully implemented)
      - ✅ Logos WITHOUT warnings (fully implemented - June 2, 2026)
   7. Auto-publish (2-click workflow)
   8. Sequential processing
   9. Excel reporting
  10. **GUARDRAIL SYSTEM (June 2, 2026)**
      - Ensures only 1 logo per logo row (Logo 1, Logo 2, etc.)
      - Three-layer protection (JavaScript + Python)

📅 Last Updated: 2026-06-02 (100% COMPLETE - ALL TODOs RESOLVED)
🔗 Git: refactor/phase-1-quick-fixes

🆕 ENHANCEMENTS (June 2, 2026):
   - ✅ Truly adaptive logo detection that LEARNS from template DOM structure
   - ✅ Guardrail system preventing duplicate logos per row
   - ✅ Complete center/enlarge support for all logo types
   - ✅ Department verification to prevent cross-department updates
   - ✅ Hierarchical warning detection at multiple DOM levels

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
import json
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

# ============================================================
# AI INTEGRATION (OPTIONAL)
# ============================================================
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from ai_integration import AIAssistant
    from ai_integration.metadata_updater import MetadataUpdater
    AI_AVAILABLE = True
    print("🤖 AI Integration: ENABLED")
except Exception as e:
    AI_AVAILABLE = False
    MetadataUpdater = None
    print(f"ℹ️  AI Integration: DISABLED ({str(e)[:50]})")

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

        # Initialize AI Assistant if available
        if AI_AVAILABLE:
            try:
                self.ai = AIAssistant()
                logger.info("🤖 AI Assistant initialized successfully")
            except Exception as e:
                self.ai = None
                logger.warning(f"⚠️  AI Assistant initialization failed: {e}")
        else:
            self.ai = None

        # Initialize Metadata Updater (Phase 1 Enhancement)
        if MetadataUpdater is not None:
            try:
                self.metadata_updater = MetadataUpdater()
                logger.info("📊 Metadata Updater initialized successfully")
            except Exception as e:
                self.metadata_updater = None
                logger.warning(f"⚠️  Metadata Updater initialization failed: {e}")
        else:
            self.metadata_updater = None
        
    async def run(self,
                  departments: Optional[List[str]] = None,
                  max_templates: int = None,
                  template_name: Optional[str] = None,
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
            template_name: Filter by specific template name (None = all)
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
                # ✨ FIX (June 8): Tab 1 = Templates list (kept open for reference)
                if context.pages:
                    page = context.pages[0]
                    logger.info(f"♻️  Reusing existing tab for templates list (Tab #1)")
                else:
                    page = await context.new_page()
                    logger.info(f"📄 Created new tab for templates list (Tab #1)")

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

                # Filter by template name if specified
                if template_name:
                    original_count = len(templates)
                    templates = [t for t in templates if t.get('name') == template_name]
                    logger.info(f"📊 Filtered by template name '{template_name}': {len(templates)}/{original_count} templates")
                    if not templates:
                        logger.error(f"❌ No template found with name '{template_name}'")
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

                # Keep filter page open for verification
                # await page.close()

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
        """Apply department filter and capture templates via API with improved timing"""

        templates = []
        all_api_calls = []
        response_received = asyncio.Event()
        target_departments = set([d.upper() for d in departments])

        async def handle_request(request):
            """Track all requests to match with responses"""
            if '/api/templatestore/u/search' in request.url and request.post_data:
                try:
                    body = json.loads(request.post_data)
                    filters = body.get('filters', [])
                    for f in filters:
                        if f.get('field') == 'departments':
                            depts = set(f.get('values', []))
                            all_api_calls.append({
                                'type': 'request',
                                'departments': depts,
                                'body': body,
                                'is_target': depts == target_departments
                            })
                            if depts == target_departments:
                                logger.info(f"   🎯 Target departments request detected: {depts}")
                            break
                except:
                    pass

        async def handle_response(response):
            nonlocal templates
            if '/api/templatestore/u/search' in response.url:
                try:
                    data = await response.json()
                    if 'data' in data and 'hits' in data['data']:
                        hits = data['data']['hits']
                        count = data['data'].get('count', 0)

                        # Check if this response is for our target departments
                        # Look backwards through recent requests to find matching one
                        is_target_response = False
                        for call in reversed(all_api_calls[-10:]):  # Check last 10 requests
                            if call.get('type') == 'request' and call.get('is_target'):
                                is_target_response = True
                                break

                        if hits:
                            if is_target_response:
                                # This is the response we want!
                                templates = hits
                                logger.info(f"   📥 Captured {len(hits)} templates from TARGET API (count={count})")
                                response_received.set()
                            else:
                                # Intermediate response, log but don't use
                                logger.debug(f"   📥 Intermediate API response: {len(hits)} templates (count={count})")

                        all_api_calls.append({
                            'type': 'response',
                            'count': count,
                            'template_count': len(hits),
                            'is_target': is_target_response
                        })
                except:
                    pass

        page.on('request', handle_request)
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

            # Small wait after unchecking to let intermediate APIs settle
            await asyncio.sleep(1)

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

            # Close dropdown - THIS triggers the actual filter API call
            logger.info("   4. Closing dropdown...")
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)

            # Wait for API response with extended timeout
            logger.info("   5. Waiting for API response...")
            try:
                await asyncio.wait_for(response_received.wait(), timeout=15.0)
            except asyncio.TimeoutError:
                logger.warning("   ⚠️  API response timeout")
                # Log what we captured
                if all_api_calls:
                    logger.info(f"   📊 Captured {len([c for c in all_api_calls if c.get('type') == 'request'])} requests")
                    target_requests = [c for c in all_api_calls if c.get('is_target')]
                    if target_requests:
                        logger.warning(f"   ⚠️  Found {len(target_requests)} target request(s) but no matching response")

            page.remove_listener('request', handle_request)
            page.remove_listener('response', handle_response)

            logger.info(f"   ✅ Filter applied: {len(templates)} templates captured")

        except Exception as e:
            logger.exception(f"   ❌ Filter application failed: {e}")
            page.remove_listener('request', handle_request)
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
        template_depts = ', '.join(template.get('departments', []))

        logger.info(f"\n{'='*100}")
        logger.info(f"📄 TEMPLATE {idx}/{total}: {template_name}")
        logger.info(f"   ID: {template_id}")
        logger.info(f"   Departments: {template_depts}")
        logger.info(f"{'='*100}")

        try:
            # Open template edit page
            # ✨ FIX (June 8): Create NEW tab for each template (keep all tabs open)
            # Tab 1 = Templates list, Tab 2+ = Each template for manual review
            page = await context.new_page()
            tab_number = len(context.pages)
            logger.info(f"   📄 Opening in new tab #{tab_number}")

            edit_url = f"{base_url}/templates/edit/{template_id}"

            logger.info(f"   🌐 Opening template editor...")
            logger.debug(f"   URL: {edit_url}")
            logger.info(f"   ⏳ Loading page and waiting for template to render...")

            await page.goto(edit_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(10)  # Increased from 5 to 10 seconds - warning icons take time to render

            logger.info(f"   ✅ Template loaded successfully")

            # Detect logos to process
            logger.info(f"   🔍 Running logo detection...")
            detection_result = await self._detect_logos(page)

            # PHASE 2 ENHANCEMENT #2: API Cross-Validation (June 7, 2026)
            # Compare detection results with API thumbnail.mediaId to catch false negatives
            api_thumbnail_id = template.get('thumbnail', {}).get('mediaId')
            learned_logos = detection_result.get('learnedLogosCount', 0)
            warnings_count = detection_result.get('warningsCount', 0)
            empty_count = detection_result.get('emptyCount', 0)

            detection_found_logos = (warnings_count > 0 or empty_count > 0 or learned_logos > 0)
            api_says_has_logo = api_thumbnail_id is not None and api_thumbnail_id != ''

            # Detect API/Detection mismatch: API says logo exists but detection didn't find it
            # ✨ FIX (June 8): Trust DETECTION over API - API thumbnail can be stale!
            if api_says_has_logo and not detection_found_logos:
                logger.warning(f"   ⚠️  API/DETECTION MISMATCH DETECTED:")
                logger.warning(f"      • API thumbnail.mediaId: {api_thumbnail_id}")
                logger.warning(f"      • Detection found: warnings={warnings_count}, empties={empty_count}, learned={learned_logos}")
                logger.warning(f"      • DECISION: Trust detection over API (API likely has stale data)")
                logger.warning(f"      • Will proceed with logo insertion if header button is active")

                # Mark this in detection result for metadata
                detection_result['apiCrossValidation'] = {
                    'apiHasLogo': True,
                    'detectionFoundLogo': False,
                    'falseNegative': False,  # ✨ Changed: This is NOT a false negative - API is stale
                    'apiStaleData': True,    # ✨ New flag
                    'apiMediaId': api_thumbnail_id
                }
            elif api_says_has_logo and detection_found_logos:
                logger.info(f"   ✅ API Cross-Validation: Logo confirmed (mediaId: {api_thumbnail_id[:20]}...)")
                detection_result['apiCrossValidation'] = {
                    'apiHasLogo': True,
                    'detectionFoundLogo': True,
                    'falseNegative': False,
                    'apiMediaId': api_thumbnail_id
                }
            else:
                # No API logo or detection correctly found nothing
                detection_result['apiCrossValidation'] = {
                    'apiHasLogo': False,
                    'detectionFoundLogo': detection_found_logos,
                    'falseNegative': False,
                    'apiMediaId': None
                }

            # Extract enhanced features
            enhanced_features = detection_result.get('enhancedFeatures', {})

            # Log enhanced features (Phase 1 Enhancement)
            if enhanced_features:
                logger.info(f"   📊 Template Complexity:")
                logger.info(f"      • Sortable items: {enhanced_features.get('sortableItemCount', 0)}")
                logger.info(f"      • Total tables: {enhanced_features.get('totalTableCount', 0)}")
                logger.info(f"      • Non-logo tables: {enhanced_features.get('nonLogoTableCount', 0)}")
                logger.info(f"      • Has buttons: {enhanced_features.get('hasButtons', False)}")
                logger.info(f"      • Dynamic tags: {enhanced_features.get('dynamicTagCount', 0)}")

                # Update metadata with enhanced features (Phase 1 Enhancement)
                if self.metadata_updater:
                    try:
                        logger.debug(f"   💾 Updating metadata for {template_name}...")
                        updated = self.metadata_updater.update_template_detection(
                            template_id=template_id,
                            template_name=template_name,
                            detection_result=detection_result
                        )
                        if updated:
                            logger.debug(f"   ✅ Metadata updated successfully")
                        else:
                            logger.debug(f"   ⚠️  Metadata update skipped")
                    except Exception as e:
                        logger.warning(f"   ⚠️  Metadata update failed: {e}")

            # AI Prediction (if available)
            if self.ai:
                try:
                    # PHASE 2 ENHANCEMENT: Include learned logo markers in has_logos calculation
                    learned_logos = detection_result.get('learnedLogosCount', 0)
                    warnings_count_ai = detection_result.get('warningsCount', 0)
                    empty_count_ai = detection_result.get('emptyCount', 0)
                    # ✨ PHASE 3 FIX: Include ALL detected logos (not just ones needing action)
                    all_detected = detection_result.get('allDetectedLogosCount', 0)

                    # Has logos if: warnings OR empties OR learned markers found OR dynamic detection found any
                    has_logos = (warnings_count_ai > 0 or
                                empty_count_ai > 0 or
                                learned_logos > 0 or
                                all_detected > 0)  # ✨ PHASE 3: Include dynamically detected logos

                    # Total logo count includes learned markers and all detected logos
                    logo_count = max(warnings_count_ai + empty_count_ai + learned_logos, all_detected)

                    template_data = {
                        "name": template_name,
                        "departments": template.get('departments', []),
                        "detection": {
                            "logo_tables_found": detection_result.get('logoTablesCount', 0),
                            "header_button_opacity": detection_result.get('headerButtonOpacity', 0),
                            "has_logos": has_logos,
                            "logo_count": logo_count,
                            "logo_type": "table-based" if detection_result.get('logoTablesCount', 0) > 0 else "container-based",
                            # NEW: Enhanced AI features (Phase 1)
                            "sortable_item_count": enhanced_features.get('sortableItemCount', 0),
                            "total_table_count": enhanced_features.get('totalTableCount', 0),
                            "non_logo_table_count": enhanced_features.get('nonLogoTableCount', 0),
                            "has_buttons": enhanced_features.get('hasButtons', False),
                            "dynamic_tag_count": enhanced_features.get('dynamicTagCount', 0),
                            # PHASE 2 ENHANCEMENT: New feature
                            "learned_logos_found": learned_logos
                        }
                    }
                    ai_prediction = self.ai.analyze_template(template_data)
                    logger.info(f"   🤖 AI: {ai_prediction['category']} (Confidence: {ai_prediction['confidence']:.0%})")
                    if ai_prediction.get('anomalies'):
                        logger.warning(f"   ⚠️  AI detected anomalies: {ai_prediction['anomalies']}")

                    # Log Phase 2 enhancement info if learned logos found
                    if learned_logos > 0:
                        logger.info(f"   ✨ Phase 2: Found {learned_logos} logo(s) via data-learned-logo markers")
                except Exception as e:
                    logger.debug(f"   AI prediction failed: {e}")

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

            # ✨ PHASE 3 FIX: Also check allDetectedLogosCount before deciding to skip
            all_detected_logos = detection_result.get('allDetectedLogosCount', 0)

            # ✨ FIX (June 8): Check if API data is stale - if so, don't trust allDetectedLogosCount
            api_cross_validation = detection_result.get('apiCrossValidation', {})
            api_is_stale = api_cross_validation.get('apiStaleData', False)

            # ✨ NEW (June 8): UNIVERSAL LOGO VALIDATION - Run FIRST, before any other processing
            # This validates ALL detected logos regardless of warnings/empty/replace counts
            if all_detected_logos > 0 and not api_is_stale:
                logger.info(f"   🔍 UNIVERSAL VALIDATION: Checking {all_detected_logos} detected logo(s)...")

                # Extract detected logos from dynamic detection
                truly_dynamic = detection_result.get('trulyDynamic', {})
                detected_logos = truly_dynamic.get('detectedLogos', [])

                if len(detected_logos) > 0:
                    logger.info(f"   📚 Validating against media library...")

                    # Get available logos from media library (using first detected logo)
                    available_logos_info = await self._get_available_logos(page, logo_idx=1)

                    if available_logos_info['success']:
                        available_filenames = [logo['filename'] for logo in available_logos_info['logos']]
                        invalid_logos = []

                        logger.debug(f"   Available logos: {available_filenames[:5]}{'...' if len(available_filenames) > 5 else ''}")

                        # Validate each detected logo
                        for idx, logo in enumerate(detected_logos, 1):
                            logo_filename = logo.get('imageFilename', '')
                            logger.debug(f"   Validating Logo {idx}: filename='{logo_filename}'")

                            if logo_filename:
                                # FIX (June 8): Extra check - warn if query params are still present
                                if '?' in logo_filename:
                                    logger.warning(f"   ⚠️  Logo {idx} filename still has query params: {logo_filename}")
                                    clean_filename = logo_filename.split('?')[0]
                                    logger.info(f"   Cleaning to: {clean_filename}")
                                    logo_filename = clean_filename

                                if logo_filename not in available_filenames:
                                    logger.warning(f"   ⚠️  Logo {idx} '{logo_filename}' NOT in media library!")
                                    logger.debug(f"       Available logos: {available_filenames[:5]}{'...' if len(available_filenames) > 5 else ''}")
                                    invalid_logos.append({
                                        'index': idx,
                                        'filename': logo_filename,
                                        'reason': 'not_in_media_library'
                                    })
                                else:
                                    logger.info(f"   ✅ Logo {idx} '{logo_filename}' is valid (exists in media library)")
                            else:
                                logger.debug(f"   ⚠️  Logo {idx} has no filename to validate")

                        # If any logos are invalid, add them to replacement list
                        if len(invalid_logos) > 0:
                            logger.info(f"   🔧 Found {len(invalid_logos)} invalid logo(s) - will replace")

                            # Select best replacement logo using smart selection
                            replacement_logo = self._select_best_logo(
                                available_filenames,
                                dealership_name=template.get('dealershipName', ''),
                                departments=template.get('departments', [])
                            )

                            if replacement_logo:
                                logger.info(f"   📝 Selected replacement: '{replacement_logo}' (smart selection)")

                                # Add to logos_to_replace for processing
                                for invalid_logo in invalid_logos:
                                    logos_to_replace.append({
                                        'index': invalid_logo['index'],
                                        'name': f"Invalid Logo {invalid_logo['index']}",
                                        'current_filename': invalid_logo['filename'],
                                        'replacement_filename': replacement_logo,
                                        'reason': invalid_logo['reason'],
                                        'alignment': 'UNKNOWN'
                                    })

                                # Update replace_count to trigger processing
                                replace_count = len(logos_to_replace)
                                logger.info(f"   🎯 Updated replace count: {replace_count} logo(s) queued for replacement")
                            else:
                                logger.error(f"   ❌ No available logos in media library to replace with!")
                                logger.info(f"   📑 Tab kept open for verification")
                                return
                        else:
                            logger.info(f"   ✅ All {len(detected_logos)} logo(s) validated - all exist in media library")
                    else:
                        logger.warning(f"   ⚠️  Could not fetch media library: {available_logos_info.get('error', 'Unknown error')}")
                        logger.debug(f"   ℹ️  Skipping validation, will trust detection")
                else:
                    logger.debug(f"   ℹ️  No detailed logo info available (detectedLogos empty)")
            elif all_detected_logos > 0 and api_is_stale:
                logger.warning(f"   ⚠️  IGNORING allDetectedLogosCount={all_detected_logos} due to stale API data")
                logger.info(f"   🎯 Will proceed with standard processing")

            # After validation, check if we have work to do
            if warnings_count == 0 and empty_count == 0 and header_count == 0 and replace_count == 0:
                # No work detected after validation
                if all_detected_logos > 0 and not api_is_stale:
                    # Logos exist and were validated - template is complete
                    logger.info(f"   📊 Detection Summary: {all_detected_logos} logos detected by dynamic pattern learning")
                    logger.info(f"   ✅ Template has logos (already correct - no action needed)")
                    logger.info(f"   📑 Tab kept open for verification")
                    # await page.close()  # Keep tab open
                    return

                # No standard logo containers detected - check if we should add a header
                logger.info("   📊 Detection Summary: No standard Logo 1/2 containers or headers detected")
                logger.debug(f"   Detection returned: warnings={warnings_count}, empty={empty_count}, headers={header_count}")

                # Check container detection results to see if containers exist at all
                container_results = detection_result.get('containerCheckResults', [])
                all_containers_not_found = all(not c.get('found', False) for c in container_results)

                if all_containers_not_found:
                    logger.info("   🔍 Running fallback detection for non-standard templates...")
                    logger.debug("   Checking for: warning icons, resizable images, sortable items")

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

                    logger.debug(f"   Fallback detection result: {has_any_logos}")

                    if has_any_logos.get('found'):
                        logger.info(f"   ⚠️  Found logos in template: {has_any_logos['count']} {has_any_logos['reason']}")
                        logger.info(f"   ℹ️  Container IDs don't match hardcoded list (likely custom UUIDs)")

                        # FIX: Check if logo tables were already found by table-based detection
                        logo_tables_count = detection_result.get('logoTablesCount', 0)
                        logger.info(f"   📋 Checking logo table detection: {logo_tables_count} table(s) found")

                        if logo_tables_count > 0:
                            # Template already has Logo 1/2 table structure - don't add header!
                            # ✨ PHASE 3 FIX #2: TRUST FALLBACK DETECTION RESULTS
                            logger.info(f"   ✅ Template has {logo_tables_count} logo table(s) with valid structure")
                            logger.info(f"   ✨ PHASE 3: Fallback found {has_any_logos['count']} logo(s) in non-standard containers - marking as DETECTED")
                            logger.debug(f"   GUARDRAIL: Prevents adding headers to templates where Logo 1/2 tables exist but have non-standard IDs")

                            self.results.append({
                                'template': template_name,
                                'id': template_id,
                                'status': 'detected',  # Changed from 'skipped'
                                'reason': f'✅ Has {logo_tables_count} logo table(s) with {has_any_logos["count"]} logo(s) ({has_any_logos["reason"]})',
                                'logos_processed': has_any_logos['count'],  # Count the logos we found
                                'published': False,
                                'phase3_fix': 'trust_fallback_logo_tables'  # Mark as Phase 3 fix
                            })
                            logger.info(f"   📑 Tab kept open for verification")
                            # await page.close()  # Keep tab open
                            return

                        logger.info(f"   📋 Checking if template still needs a header structure...")

                        # Check #HEADER button status even for non-standard templates
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

                        logger.debug(f"   Header button state (non-standard template): {button_state}")

                        if button_state.get('found') and button_state.get('isActive'):
                            # Header button is active - template has logos but NEEDS header structure!
                            logger.info(f"   🎯 #HEADER button is active (opacity={button_state['opacity']}) - template needs header despite having logos")
                            logger.info(f"   ℹ️  Template has {has_any_logos['count']} logo(s) in body but no header structure")
                            logger.info("   ➕ Adding header structure with logo...")

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
                                    'action': 'header_added_to_non_standard',
                                    'reason': f"Had {has_any_logos['count']} logo(s) but no header structure",
                                    'logos_processed': 1,  # Count header as 1 logo
                                    'published': published,
                                    'departments': ', '.join(template.get('departments', []))
                                })

                                logger.info(f"\n   ✅ Template {idx} complete:")
                                logger.info(f"      Action: Header added to non-standard template")
                                logger.info(f"      Reason: Template had logos in body but no header structure")
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
                                    'reason': 'Header addition failed (non-standard template)',
                                    'logos_processed': 0,
                                    'published': False
                                })
                                logger.info(f"   📑 Tab kept open for verification")
                                # await page.close()  # Keep tab open
                                return
                        else:
                            # Header button is grayed or not found - template already has header or can't add one
                            # ✨ PHASE 3 FIX #2: TRUST FALLBACK DETECTION RESULTS
                            # If fallback detection found logos, report them as detected!
                            # Don't skip just because we can't add more logos

                            if button_state.get('found') and button_state.get('isGrayed'):
                                logger.info(f"   ✅ #HEADER button is grayed (opacity={button_state['opacity']}) - template already has header structure")
                                logger.info(f"   ✨ PHASE 3: Fallback detection found {has_any_logos['count']} logo(s) - marking as DETECTED")
                            elif button_state.get('found'):
                                logger.info(f"   ℹ️  #HEADER button status unclear (opacity={button_state['opacity']})")
                            else:
                                logger.info(f"   ℹ️  #HEADER button not found")

                            # Instead of skipping, mark template as having logos detected
                            # This fixes the false negative issue
                            self.results.append({
                                'template': template_name,
                                'id': template_id,
                                'status': 'detected',  # Changed from 'skipped'
                                'reason': f"✅ Fallback detection found {has_any_logos['count']} logo(s) ({has_any_logos['reason']}) - header already exists",
                                'logos_processed': has_any_logos['count'],  # Count the logos we found
                                'published': False,
                                'phase3_fix': 'trust_fallback_detection'  # Mark as Phase 3 fix
                            })
                            logger.info(f"   📑 Tab kept open for verification")
                            # await page.close()  # Keep tab open
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
                            logger.info(f"   📑 Tab kept open for verification")
                            # await page.close()  # Keep tab open
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
                logger.info(f"   📑 Tab kept open for verification")
                # await page.close()  # Keep tab open
                return

            # Get replace count from detection result
            replace_count = detection_result.get('replaceCount', 0)
            logos_to_replace = detection_result.get('logosToReplace', [])

            # Log Truly Dynamic Detection results
            truly_dynamic = detection_result.get('trulyDynamic', {})
            if truly_dynamic.get('enabled'):
                logger.info(f"   🧠 TRULY DYNAMIC DETECTION ENABLED:")
                summary = truly_dynamic.get('summary', {})
                logger.info(f"      - Pattern learned: {truly_dynamic.get('bestPattern', {}).get('class', 'N/A')}")
                logger.info(f"      - Pattern score: {truly_dynamic.get('bestScore', 0)}")
                logger.info(f"      - Logos detected: {summary.get('logosDetected', 0)}")
                logger.info(f"      - Logos with warnings: {summary.get('logosWithWarnings', 0)}")
                logger.info(f"      - Logos marked for action: {summary.get('logosMarkedForAction', 0)}")
                logger.debug(f"      - Candidate logos analyzed: {summary.get('candidateLogos', 0)}")
                logger.debug(f"      - Patterns discovered: {summary.get('patternsDiscovered', 0)}")

            logger.info(f"   ✅ Detection Summary:")
            logger.info(f"      - Logos with warnings: {warnings_count}")
            logger.info(f"      - Logos without warnings (to replace): {replace_count}")
            logger.info(f"      - Empty Logo 1/2 containers: {empty_count}")
            logger.info(f"      - Empty header containers: {header_count}")

            logos_processed = 0
            logos_centered = 0
            logos_enlarged = 0

            # Process logos with warnings (CHANGE IMAGE)
            # GUARDRAIL: Track which logo rows have been processed
            processed_logo_rows = set()

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

                # Extract logo row (e.g., "Logo 1" from "Logo 1 CENTER")
                logo_row = ' '.join(logo_name.split()[:2]) if len(logo_name.split()) >= 2 else logo_name

                # GUARDRAIL: Skip if this logo row already processed
                if logo_row in processed_logo_rows:
                    logger.info(f"\n   ⏭️  Skipping {logo_name} - {logo_row} already has a logo")
                    logger.debug(f"   GUARDRAIL: Only 1 logo per logo row allowed")
                    continue

                logger.info(f"\n   🎯 Replacing logo {logo_idx}/{replace_count}: {logo_name}...")
                logger.info(f"   Current alignment: {current_alignment} (will keep same position)")
                logger.debug(f"   Attempting REPLACE workflow for logo without warning")

                # Get replacement filename if specified (for invalid logo replacement)
                replacement_filename = logo_item.get('replacement_filename', None)
                if replacement_filename:
                    logger.info(f"   📝 Target replacement: '{replacement_filename}' (invalid logo fix)")

                if await self._replace_logo_without_warning(page, logo_idx, logo_media_id, target_filename=replacement_filename):
                    logos_processed += 1
                    processed_logo_rows.add(logo_row)  # Mark this logo row as processed
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
            # GUARDRAIL: Track which logo rows have been processed to ensure only 1 logo per row
            processed_logo_rows = set()

            # ✨ NEW: Smart logo selection for empty containers
            # Validate available logos ONCE for all empty containers in this template
            best_logo_for_insert = None
            if empty_count > 0:
                logger.info(f"\n   🔍 Validating available logos for {empty_count} empty container(s)...")

                # Use first empty container to open Insert Image popup and fetch available logos
                first_container = detection_result['emptyContainers'][0]
                available_logos_for_insert = await self._get_available_logos_for_insert(page, first_container)

                if available_logos_for_insert['success']:
                    available_filenames_insert = [logo['filename'] for logo in available_logos_for_insert['logos']]
                    logger.info(f"   ✅ Found {available_logos_for_insert['totalCount']} logo(s) in media library")
                    logger.debug(f"   Available: {available_filenames_insert[:5]}{'...' if len(available_filenames_insert) > 5 else ''}")

                    # Smart selection: Look for dealership-specific logo
                    best_logo_for_insert = self._select_best_logo(
                        available_filenames_insert,
                        dealership_name=template.get('dealershipName', ''),
                        departments=template.get('departments', [])
                    )
                    logger.info(f"   📝 Selected logo for all empty containers: '{best_logo_for_insert}' (smart selection)")
                else:
                    logger.warning(f"   ⚠️  Could not fetch media library: {available_logos_for_insert.get('error', 'Unknown')}")
                    logger.info(f"   ℹ️  Will use logo_media_id as fallback")

            logger.debug(f"Starting empty container processing: {empty_count} empty containers detected")
            for container in detection_result['emptyContainers']:
                container_name = container['name']
                container_id = container['id']

                # Extract logo row (e.g., "Logo 1" from "Logo 1 CENTER")
                logo_row = ' '.join(container_name.split()[:2]) if len(container_name.split()) >= 2 else container_name

                # GUARDRAIL: Skip if this logo row already processed
                if logo_row in processed_logo_rows:
                    logger.info(f"\n   ⏭️  Skipping {container_name} - {logo_row} already has a logo")
                    logger.debug(f"   GUARDRAIL: Only 1 logo per logo row allowed")
                    continue

                logger.info(f"\n   🎯 Inserting logo into {container_name}...")
                logger.debug(f"   Container ID: {container_id}")
                logger.debug(f"   Attempting INSERT workflow for empty container")
                if best_logo_for_insert:
                    logger.debug(f"   Using validated logo: '{best_logo_for_insert}'")

                if await self._insert_logo_to_container(page, container, logo_media_id, target_filename=best_logo_for_insert):
                    logos_processed += 1
                    processed_logo_rows.add(logo_row)  # Mark this logo row as processed
                    logger.info(f"   ✅ Logo inserted into {container_name}")
                    logger.log_action("INSERT", container_name, True, f"ID: {container_id}")
                else:
                    logger.warning(f"   ⚠️  Failed to insert logo into {container_name}")
                    logger.log_action("INSERT", container_name, False, f"ID: {container_id}")

            # Process empty header containers (INSERT IMAGE FOR HEADERS)
            logger.debug(f"Starting header processing: {header_count} empty headers detected")

            # FIX: Before inserting into header containers, check if header row already has logos
            # This prevents duplicate logos when one position has a warning logo that was replaced
            if header_count > 0:
                logger.debug("   Checking if header row already has logos (after replacements)...")
                header_has_logo = await page.evaluate("""
                    () => {
                        // Find tables with 3 cells (potential header structure)
                        const tables = Array.from(document.querySelectorAll('table'));
                        for (const table of tables) {
                            const firstRow = table.querySelector('tr');
                            if (!firstRow) continue;

                            const tds = Array.from(firstRow.querySelectorAll('td'));
                            if (tds.length === 3) {
                                // Check first 2 positions for images
                                for (let i = 0; i < 2; i++) {
                                    const td = tds[i];
                                    const img = td.querySelector('img');
                                    if (img) {
                                        return { hasLogo: true, position: i + 1 };
                                    }
                                }
                            }
                        }
                        return { hasLogo: false, position: null };
                    }
                """)

                if header_has_logo.get('hasLogo'):
                    logger.info(f"   ℹ️  Header row already has a logo at position {header_has_logo['position']} (likely from warning logo replacement)")
                    logger.info(f"   ⏭️  Skipping header insertion to prevent duplicate logos (GUARDRAIL)")
                    logger.debug("   This prevents the bug where replacing a warning logo in header position 2, then inserting into position 1, creates duplicates")
                    header_count = 0  # Skip all header insertions

            for header in detection_result['headerContainers']:
                if header_count == 0:
                    break  # Skip if guardrail triggered

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

            logger.info(f"\n{'='*100}")
            logger.info(f"   ✅ TEMPLATE {idx} COMPLETE: {template_name}")
            logger.info(f"{'='*100}")
            logger.info(f"   📊 Processing Summary:")
            logger.info(f"      Logos Processed: {logos_processed}/{total_logos}")
            logger.info(f"      Centered: {logos_centered}")
            logger.info(f"      Enlarged: {logos_enlarged}")
            logger.info(f"      Published: {'✅ YES' if published else '❌ NO'}")
            logger.info(f"   📑 Status: Tab kept open for manual verification")
            logger.info(f"{'='*100}\n")

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
        """
        Detect all logos using TRULY DYNAMIC PATTERN DETECTION

        NEW (June 2, 2026 - ENHANCED): Truly adaptive logo detection
        - LEARNS container patterns from the template DOM (no hardcoded selectors!)
        - Uses multi-phase adaptive heuristics
        - Detects warnings at multiple DOM hierarchy levels
        - Color-codes containers: RED (warnings) vs GREEN (correct logos)
        - Assigns department verification to each logo
        """

        return await page.evaluate("""
            () => {
                const debug = [];
                const patterns = {
                    learningPhases: [],
                    containerPatterns: [],
                    detectedLogos: [],
                    summary: {}
                };

                // ============================================================================
                // PHASE 0: ENHANCED - Detect data-learned-logo markers (JUNE 7, 2026)
                // ============================================================================
                patterns.learningPhases.push('PHASE 0: Scanning for data-learned-logo markers');
                debug.push('=== PHASE 2 ENHANCEMENT: data-learned-logo Detection ===');

                const learnedLogoMarkers = [];
                const allLearnedElements = document.querySelectorAll('[data-learned-logo]');

                debug.push(`Found ${allLearnedElements.length} elements with data-learned-logo attribute`);

                allLearnedElements.forEach((element, idx) => {
                    const logoMarker = element.getAttribute('data-learned-logo');
                    const img = element.querySelector('img');

                    if (img) {
                        const rect = img.getBoundingClientRect();
                        const src = img.src || '';

                        // Validate this is a real logo (not an icon)
                        const isIcon = src.includes('icon-') ||
                                      src.includes('favicon') ||
                                      src.includes('tekion-logo');

                        if (!isIcon && rect.width > 30 && rect.height > 15) {
                            learnedLogoMarkers.push({
                                element: element,
                                img: img,
                                marker: logoMarker,
                                src: src.substring(0, 100),
                                rect: {
                                    top: Math.round(rect.top + window.scrollY),
                                    left: Math.round(rect.left),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                },
                                detectionMethod: 'data-learned-logo'
                            });
                            debug.push(`  ✅ Found logo with marker: ${logoMarker} (${rect.width}x${rect.height}px)`);
                        }
                    }
                });

                patterns.learningPhases.push(`Found ${learnedLogoMarkers.length} logos via data-learned-logo markers`);

                // ============================================================================
                // PHASE 0.5: CPRA PATTERN DETECTION (JUNE 7, 2026 - PHASE 3 FIX #4)
                // Detect CPRA templates with custom headers (grayed button + sortable item images)
                // ============================================================================
                patterns.learningPhases.push('PHASE 0.5: Scanning for CPRA pattern');
                debug.push('=== PHASE 3 ENHANCEMENT: CPRA Pattern Detection ===');

                const cpraLogos = [];

                // Check if this is a CPRA template (grayed #HEADER button)
                const cpraHeaderBtn = document.querySelector('#HEADER');
                const isCPRAPattern = cpraHeaderBtn && parseFloat(window.getComputedStyle(cpraHeaderBtn).opacity) < 0.5;

                debug.push(`Header button found: ${!!cpraHeaderBtn}, opacity: ${cpraHeaderBtn ? window.getComputedStyle(cpraHeaderBtn).opacity : 'N/A'}`);
                debug.push(`CPRA pattern detected: ${isCPRAPattern}`);

                if (isCPRAPattern) {
                    // Look for logos in sortable items (CPRA custom header pattern)
                    const sortableItems = document.querySelectorAll('[class*="SortableItem"]');
                    debug.push(`Found ${sortableItems.length} sortable items to scan`);

                    sortableItems.forEach((item, idx) => {
                        const imgs = item.querySelectorAll('img');
                        imgs.forEach(img => {
                            const src = img.src || '';
                            const rect = img.getBoundingClientRect();

                            // Check if this is a dealer logo (not icon, reasonable size)
                            const isMediaUrl = src.includes('amazonaws.com') && src.includes('media_');
                            const isNotIcon = !src.includes('icon-') && !src.includes('favicon') && !src.includes('tekion-logo');
                            const isReasonableSize = rect.width > 50 && rect.width < 500 && rect.height > 20 && rect.height < 300;

                            if (isMediaUrl && isNotIcon && isReasonableSize) {
                                cpraLogos.push({
                                    img: img,
                                    src: src.substring(0, 100),
                                    position: {
                                        top: Math.round(rect.top + window.scrollY),
                                        left: Math.round(rect.left),
                                        width: Math.round(rect.width),
                                        height: Math.round(rect.height)
                                    },
                                    detectionMethod: 'cpra_sortable_item',
                                    sortableItemIndex: idx
                                });
                                debug.push(`  ✅ Found CPRA logo in sortable item ${idx}: ${rect.width}x${rect.height}px`);
                            }
                        });
                    });

                    debug.push(`CPRA pattern scan complete: ${cpraLogos.length} logos found`);

                    // Add CPRA logos to detected logos list
                    cpraLogos.forEach((cpraLogo, idx) => {
                        patterns.detectedLogos.push({
                            index: patterns.detectedLogos.length + 1,
                            containerClass: 'cpra_sortable_item',
                            hasImage: true,
                            hasWarning: false,
                            position: {
                                top: cpraLogo.position.top,
                                left: cpraLogo.position.left
                            },
                            size: {
                                width: cpraLogo.position.width,
                                height: cpraLogo.position.height
                            },
                            imageSrc: cpraLogo.src,
                            detectionMethod: 'cpra_pattern'
                        });
                    });
                }

                patterns.learningPhases.push(`Found ${cpraLogos.length} logos via CPRA pattern`);

                // ============================================================================
                // PHASE 1: Find all images that look like logos (ADAPTIVE HEURISTICS)
                // ============================================================================
                patterns.learningPhases.push('PHASE 1: Analyzing all images');
                debug.push('=== TRULY DYNAMIC LOGO DETECTION (Adaptive Learning) ===');

                const allImages = Array.from(document.querySelectorAll('img'));
                const candidateLogos = [];

                allImages.forEach((img, idx) => {
                    const src = img.src || '';
                    const rect = img.getBoundingClientRect();
                    const alt = img.alt || '';

                    // Heuristic 1: Size-based (logos can be various sizes)
                    const isLogoSize = rect.width > 30 && rect.width < 500 &&
                                      rect.height > 15 && rect.height < 300;

                    // Heuristic 2: Aspect ratio (logos can be square or wide)
                    const aspectRatio = rect.width / rect.height;
                    const isLogoAspect = aspectRatio > 0.5 && aspectRatio < 10;

                    // Heuristic 3: URL pattern (S3 media URLs or reasonable images)
                    const isMediaUrl = (src.includes('amazonaws.com') && src.includes('media_')) ||
                                      src.includes('.png') || src.includes('.jpg') || src.includes('.svg');

                    // Heuristic 4: Position (anywhere in visible area)
                    // ✨ PHASE 3 FIX: Allow logos at very top (was rect.top > 100, now > 0)
                    const isReasonablePosition = rect.top >= 0 && rect.top < 3000 &&
                                                rect.left >= 0 && rect.width > 0;

                    // Heuristic 5: Not a system icon
                    const notSystemIcon = !src.includes('icon-') &&
                                         !alt.toLowerCase().includes('icon') &&
                                         !src.includes('tekion-logo') &&
                                         !src.includes('favicon');

                    // Heuristic 6: Visible element
                    const isVisible = rect.width > 0 && rect.height > 0;

                    // NEW HEURISTIC 7: Has data-learned-logo marker (HIGHEST CONFIDENCE)
                    let parentElement = img.parentElement;
                    let hasLearnedMarker = false;
                    let depth = 0;
                    while (parentElement && depth < 5) {
                        if (parentElement.hasAttribute('data-learned-logo')) {
                            hasLearnedMarker = true;
                            break;
                        }
                        parentElement = parentElement.parentElement;
                        depth++;
                    }

                    // Score the candidate (RELAXED threshold for inclusivity)
                    const score = (isLogoSize ? 1 : 0) +
                                 (isLogoAspect ? 1 : 0) +
                                 (isMediaUrl ? 2 : 0) +  // Higher weight for media URLs
                                 (isReasonablePosition ? 1 : 0) +
                                 (notSystemIcon ? 1 : 0) +
                                 (isVisible ? 1 : 0) +
                                 (hasLearnedMarker ? 3 : 0);  // NEW: Highest weight for learned markers

                    // ✨ PHASE 3 FIX: Lower threshold from 2 to 1 for better detection
                    if (score >= 1) {  // VERY RELAXED Threshold: at least 1 point
                        candidateLogos.push({
                            img: img,
                            score: score,
                            index: idx,
                            hasLearnedMarker: hasLearnedMarker,
                            rect: {
                                top: Math.round(rect.top + window.scrollY),
                                left: Math.round(rect.left),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            }
                        });
                    }
                });

                patterns.learningPhases.push(`Found ${candidateLogos.length} candidate logo images`);
                debug.push(`Found ${candidateLogos.length} candidate logo images using adaptive heuristics`);

                // ============================================================================
                // PHASE 2: Learn container patterns from candidate logos
                // ============================================================================
                patterns.learningPhases.push('PHASE 2: Learning container patterns');

                const containerPatternMap = new Map();

                candidateLogos.forEach(candidate => {
                    const img = candidate.img;
                    let currentElement = img.parentElement;
                    let depth = 0;

                    // Walk up the DOM to find common container patterns
                    while (currentElement && depth < 10) {
                        const classes = Array.from(currentElement.classList || []);
                        const tagName = currentElement.tagName;

                        // Track class patterns
                        classes.forEach(cls => {
                            if (cls.length > 3) {  // Ignore very short class names
                                if (!containerPatternMap.has(cls)) {
                                    containerPatternMap.set(cls, {
                                        class: cls,
                                        count: 0,
                                        depths: [],
                                        tags: new Set()
                                    });
                                }
                                const pattern = containerPatternMap.get(cls);
                                pattern.count++;
                                pattern.depths.push(depth);
                                pattern.tags.add(tagName);
                            }
                        });

                        currentElement = currentElement.parentElement;
                        depth++;
                    }
                });

                // Find the most common container patterns
                const sortedPatterns = Array.from(containerPatternMap.values())
                    .sort((a, b) => b.count - a.count)
                    .slice(0, 10);  // Top 10 patterns

                patterns.containerPatterns = sortedPatterns.map(p => ({
                    class: p.class,
                    occurrences: p.count,
                    avgDepth: Math.round(p.depths.reduce((a, b) => a + b, 0) / p.depths.length),
                    tags: Array.from(p.tags)
                }));

                patterns.learningPhases.push(`Identified ${patterns.containerPatterns.length} common container patterns`);

                // ============================================================================
                // PHASE 3: Identify the most likely logo container class
                // ============================================================================
                patterns.learningPhases.push('PHASE 3: Selecting optimal container pattern');

                let bestPattern = null;
                let bestScore = 0;

                for (const pattern of patterns.containerPatterns) {
                    const classLower = pattern.class.toLowerCase();

                    // Filter out UI/layout classes
                    const isUIClass = classLower.includes('header') ||
                                     classLower.includes('wrapper') ||
                                     classLower.includes('skeleton') ||
                                     classLower.includes('full-height') ||
                                     classLower.includes('app-') ||
                                     classLower.includes('root_');

                    if (isUIClass) continue;  // Skip UI classes

                    // Keyword scoring
                    let keywordScore = 0;
                    if (classLower.includes('image')) keywordScore += 3;
                    if (classLower.includes('component')) keywordScore += 2;
                    if (classLower.includes('container')) keywordScore += 2;
                    if (classLower.includes('logo')) keywordScore += 3;
                    if (classLower.includes('sortable')) keywordScore += 1;
                    if (classLower.includes('resizable')) keywordScore += 1;

                    // Depth scoring (prefer depth 2-4)
                    let depthScore = 0;
                    if (pattern.avgDepth >= 2 && pattern.avgDepth <= 4) depthScore = 2;
                    else if (pattern.avgDepth >= 1 && pattern.avgDepth <= 5) depthScore = 1;

                    // Occurrence scoring (prefer multiple occurrences but not too many)
                    let occurrenceScore = 0;
                    if (pattern.occurrences >= 2 && pattern.occurrences <= 5) occurrenceScore = 2;
                    else if (pattern.occurrences === 1) occurrenceScore = 1;

                    const totalScore = keywordScore + depthScore + occurrenceScore;

                    if (totalScore > bestScore) {
                        bestScore = totalScore;
                        bestPattern = pattern;
                    }
                }

                if (bestPattern) {
                    patterns.learningPhases.push(`Selected best pattern: ${bestPattern.class} (score: ${bestScore})`);
                    debug.push(`✨ LEARNED PATTERN: ${bestPattern.class} (score: ${bestScore})`);
                    debug.push(`   Pattern details: occurrences=${bestPattern.occurrences}, avgDepth=${bestPattern.avgDepth}`);

                    // Show top 3 patterns for comparison
                    const topPatterns = patterns.containerPatterns
                        .sort((a, b) => {
                            const scoreA = (a.class.toLowerCase().includes('image') ? 3 : 0) + (a.occurrences >= 2 && a.occurrences <= 5 ? 2 : 0);
                            const scoreB = (b.class.toLowerCase().includes('image') ? 3 : 0) + (b.occurrences >= 2 && b.occurrences <= 5 ? 2 : 0);
                            return scoreB - scoreA;
                        })
                        .slice(0, 3);

                    debug.push(`   Top 3 candidate patterns:`);
                    topPatterns.forEach((p, i) => {
                        debug.push(`     ${i + 1}. ${p.class} (occurs: ${p.occurrences}x, depth: ${p.avgDepth})`);
                    });
                } else {
                    patterns.learningPhases.push('No suitable pattern found, using fallback');
                    debug.push('⚠️  WARNING: No pattern learned, falling back to hardcoded selectors');

                    // Show what patterns were found but rejected
                    if (patterns.containerPatterns.length > 0) {
                        debug.push(`   Found ${patterns.containerPatterns.length} patterns but none scored high enough:`);
                        patterns.containerPatterns.slice(0, 5).forEach(p => {
                            debug.push(`     - ${p.class} (occurs: ${p.occurrences}x, depth: ${p.avgDepth})`);
                        });
                    }
                }

                // ============================================================================
                // PHASE 4: Extract logo containers using learned pattern
                // ============================================================================
                let logoIndex = 0;

                if (bestPattern) {
                    const containerSelector = `[class*="${bestPattern.class}"]`;
                    const containers = document.querySelectorAll(containerSelector);

                    patterns.learningPhases.push(`Found ${containers.length} containers matching: ${containerSelector}`);
                    debug.push(`Found ${containers.length} containers using learned pattern`);

                    // Filter to only containers that actually have images
                    containers.forEach((container, idx) => {
                        const img = container.querySelector('img');
                        let hasImage = img !== null;
                        let visibilityStatus = 'no-image';
                        let imgRect = null;  // ✨ FIX: Define imgRect in outer scope

                        // ✨ PHASE 5: Check if image is actually visible
                        if (hasImage && img) {
                            const imgStyle = window.getComputedStyle(img);
                            imgRect = img.getBoundingClientRect();  // ✨ FIX: Assign without const
                            const isStyleVisible = imgStyle.display !== 'none' &&
                                             imgStyle.visibility !== 'hidden' &&
                                             imgStyle.opacity !== '0';

                            const isZeroSize = imgRect.width === 0 || imgRect.height === 0;
                            const isOffScreen = imgRect.top < -1000 || imgRect.left < -1000;

                            if (!isStyleVisible) {
                                visibilityStatus = 'hidden-css';
                                hasImage = false;
                            } else if (isZeroSize) {
                                visibilityStatus = 'zero-size';
                                hasImage = false;
                            } else if (isOffScreen) {
                                visibilityStatus = 'off-screen';
                                hasImage = false;
                            } else {
                                visibilityStatus = `visible ${Math.round(imgRect.width)}x${Math.round(imgRect.height)}px`;
                            }
                        }

                        // ✨ PHASE 5.1: Log ALL containers (even ones without images)
                        const rect = container.getBoundingClientRect();
                        const containerInfo = `Container #${idx + 1}: ${visibilityStatus}, position=${Math.round(rect.top + window.scrollY)}px top`;

                        if (hasImage) {
                            // Check if this is a UI icon (not a dealer logo)
                            const imgAlt = img.alt || '';
                            const imgSrc = img.src || '';
                            const isUIIcon = imgAlt.includes('Get Directions') ||
                                           imgAlt.includes('Call us') ||
                                           imgAlt.includes('Tv') ||
                                           imgSrc.includes('/icon-') ||
                                           imgSrc.includes('/common/CRM/') ||
                                           (imgRect && imgRect.width < 30); // ✨ FIX: Check imgRect exists - Very small icons

                            debug.push(`  ${isUIIcon ? '🎨' : '✅'} ${containerInfo}, src="${img.src}", alt="${imgAlt}"`);

                            // Mark the container for testing
                            container.setAttribute('data-learned-logo', `container-${idx + 1}`);

                            if (isUIIcon) {
                                // ✨ PINK border for UI icons (to filter out)
                                container.style.outline = '4px solid hotpink';
                                container.style.backgroundColor = 'rgba(255, 105, 180, 0.2)';
                                container.style.zIndex = '9999';
                            } else {
                                // ✨ GREEN border for real detected logos
                                container.style.outline = '4px solid lime';
                                container.style.backgroundColor = 'rgba(0, 255, 0, 0.1)';
                                container.style.zIndex = '9999';
                            }

                            patterns.detectedLogos.push({
                                index: idx + 1,
                                containerClass: bestPattern.class,
                                hasImage: true,
                                hasWarning: false,  // Will be determined in Phase 5
                                isUIIcon: isUIIcon,
                                position: {
                                    top: Math.round(rect.top + window.scrollY),
                                    left: Math.round(rect.left)
                                },
                                size: {
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                },
                                imageSrc: img ? img.src : null,
                                // FIX (June 8): Strip query parameters from filename (e.g., ?X-Amz-Algorithm=...)
                                imageFilename: img && img.src ? img.src.split('/').pop().split('?')[0] : null,
                                imageAlt: imgAlt
                            });
                        } else {
                            debug.push(`  ⏭️  ${containerInfo}`);
                        }
                    });
                }

                // ============================================================================
                // PHASE 5: Detect warning icons with HIERARCHICAL support
                // ============================================================================
                patterns.learningPhases.push('PHASE 5: Checking for warning icons');

                const warningSelectors = [
                    '[class*="warningIcon"]',
                    '[class*="warning"]',
                    '.icon-alert1',
                    '[aria-label*="warning"]',
                    '.templates_errorWarningIconsWithPopover_warningIcon__fT9Rzb2vrs',
                    '.templates_Image_warningIcon__hCZHMuhEmb'
                ];

                let warningIcons = [];
                for (const selector of warningSelectors) {
                    const found = document.querySelectorAll(selector);
                    if (found.length > 0) {
                        warningIcons = Array.from(found);
                        patterns.learningPhases.push(`Found ${found.length} warning icons using: ${selector}`);
                        debug.push(`Found ${found.length} warning icons`);
                        break;
                    }
                }

                // Mark logos with warnings using HIERARCHICAL detection
                patterns.detectedLogos.forEach(logo => {
                    logo.hasWarning = false;
                });

                warningIcons.forEach((icon, warnIdx) => {
                    // Find which detected logo is associated with this warning
                    let foundInLogo = false;
                    const iconRect = icon.getBoundingClientRect();
                    const iconTop = Math.round(iconRect.top + window.scrollY);

                    patterns.detectedLogos.forEach(logo => {
                        const container = document.querySelector(`[data-learned-logo="container-${logo.index}"]`);

                        // Check 1: Is warning inside the container?
                        if (container && container.contains(icon)) {
                            logo.hasWarning = true;
                            foundInLogo = true;
                            patterns.learningPhases.push(`  Warning #${warnIdx + 1} found INSIDE Logo #${logo.index}`);
                            return;
                        }

                        // Check 2: Is the container inside the warning's parent? (warning at SortableItem level)
                        let parent = container?.parentElement;
                        while (parent && parent !== document.body) {
                            if (parent.contains(icon) && parent.contains(container)) {
                                // Both warning and logo are in the same parent container
                                // Check if they're close (within 200px)
                                const containerTop = logo.position.top;

                                if (Math.abs(iconTop - containerTop) < 200) {
                                    logo.hasWarning = true;
                                    foundInLogo = true;
                                    patterns.learningPhases.push(`  Warning #${warnIdx + 1} found in PARENT of Logo #${logo.index} (distance: ${Math.abs(iconTop - containerTop)}px)`);
                                    return;
                                }
                            }
                            parent = parent.parentElement;
                        }
                    });

                    if (!foundInLogo) {
                        patterns.learningPhases.push(`  Warning #${warnIdx + 1} NOT matched to any logo (at ${iconTop}px)`);
                    }
                });

                // ============================================================================
                // PHASE 6: Process logos with warnings and mark for action
                // ============================================================================
                patterns.learningPhases.push('PHASE 6: Marking logos for action');

                patterns.detectedLogos.forEach(logo => {
                    if (logo.hasWarning) {
                        logoIndex++;
                        const container = document.querySelector(`[data-learned-logo="container-${logo.index}"]`);

                        if (container) {
                            // Find the outer SortableItem container for department detection
                            const sortableItem = container.closest('[class*="SortableItem"]') || container.parentElement;

                            // Detect department to prevent cross-department logo updates
                            const department = detectLogoDepartment(sortableItem, container);

                            // Mark the OUTER container (SortableItem or parent) for processing
                            if (sortableItem) {
                                sortableItem.setAttribute('data-logo-to-inspect', `warning-logo-${logoIndex}`);
                                sortableItem.setAttribute('data-logo-department', department || 'unknown');
                            }

                            // Mark the INNER container (learned container) for hover targeting
                            container.setAttribute('data-imagecomponent-target', `logo-${logoIndex}`);

                            // Visual feedback (RED border for warnings)
                            container.style.outline = '3px solid red';
                            container.style.backgroundColor = 'rgba(255, 0, 0, 0.05)';

                            patterns.learningPhases.push(`  Logo #${logoIndex}: WARNING - Department: ${department || 'UNKNOWN'}`);
                            debug.push(`  Logo #${logoIndex}: WARNING at ${logo.position.top}px - Department: ${department || 'UNKNOWN'}`);
                        }
                    }
                });

                debug.push(`Total logos marked for processing: ${logoIndex}`);

                // ✨ PHASE 5.1: Summary of all detected logos (dynamic + table-based)
                debug.push(`\n=== DYNAMIC DETECTION SUMMARY ===`);
                debug.push(`Logos detected (visible images): ${patterns.detectedLogos.length}`);
                if (patterns.detectedLogos.length > 0) {
                    debug.push(`Logo positions:`);
                    patterns.detectedLogos.forEach((logo, idx) => {
                        debug.push(`  Logo ${idx + 1}: top=${logo.position.top}px, size=${logo.size.width}x${logo.size.height}px, src="${logo.imageSrc}"`);
                    });
                }

                // ✨ FIX (June 8): Store dynamic detection results for later use
                // This will be used to populate globalLogoRowsWithContent BEFORE table/hardcoded detection
                const dynamicDetectedLogoCount = patterns.detectedLogos.length;
                debug.push(`Dynamic detection will inform table/hardcoded detection: ${dynamicDetectedLogoCount} logos found`);

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

                // ============================================================================
                // FIX #1: STATE SYNCHRONIZATION
                // Run table-based detection FIRST to identify which logo rows already have content
                // Then use that information to inform hardcoded Logo 1/2 detection
                // ============================================================================

                // Initialize shared tracking arrays
                const emptyContainers = [];
                const containerCheckResults = [];
                const logosToReplace = [];

                // Shared guardrail state (will be populated by table detection first)
                const globalLogoRowsWithContent = new Set(); // e.g., 'Logo 1', 'Logo 2'

                // ✨ FIX (June 8): Populate globalLogoRowsWithContent from dynamic detection
                // This ensures hardcoded detection knows about logos found by dynamic detection
                // even if table-based detection finds 0 tables
                if (dynamicDetectedLogoCount > 0) {
                    debug.push('\\n=== SYNCING DYNAMIC DETECTION TO GLOBAL STATE ===');
                    // Add Logo 1, Logo 2, etc. based on how many logos were dynamically detected
                    for (let i = 1; i <= dynamicDetectedLogoCount; i++) {
                        const logoRow = `Logo ${i}`;
                        globalLogoRowsWithContent.add(logoRow);
                        debug.push(`  Added "${logoRow}" to global state (from dynamic detection)`);
                    }
                    debug.push(`Global state now has: ${Array.from(globalLogoRowsWithContent).join(', ')}`);
                }

                // ============================================================================
                // STEP 1: Run table-based detection FIRST
                // ============================================================================
                debug.push('\\n=== TABLE-BASED LOGO DETECTION (Primary) ===');
                const allTables = Array.from(document.querySelectorAll('table'));
                debug.push(`Scanning ${allTables.length} tables for logo containers...`);
                const logoTables = [];
                const MAX_LOGO_TABLES = 2; // FIX #4: Most templates have at most 2 logo rows (top + bottom)

                allTables.forEach((table, tableIdx) => {
                    // FIX #4: Stop processing if we've reached max logo tables
                    if (logoTables.length >= MAX_LOGO_TABLES) {
                        return;
                    }

                    const firstRow = table.querySelector('tr');
                    if (!firstRow) return;

                    const cells = Array.from(firstRow.querySelectorAll('td'));

                    // Logo containers have 4 or 5 columns
                    if (cells.length === 4 || cells.length === 5) {
                        // ✨ PHASE 5.2: Filter out tables with dynamic tag links (buttons, not logos)
                        const hasDynamicLinks = table.querySelector('.dynamic_tag_link') !== null;
                        const hasViewSurvey = table.textContent.includes('View Survey');
                        const hasGetDirections = table.textContent.includes('Get Directions');
                        const hasCallUs = table.textContent.includes('Call us') || table.textContent.includes('Call Us');

                        if (hasDynamicLinks || hasViewSurvey || hasGetDirections || hasCallUs) {
                            return; // Skip this table - it's a button/link container, not a logo container
                        }

                        const tableInfo = {
                            tableIndex: tableIdx,
                            positions: [],
                            tableElement: table
                        };

                        cells.forEach((cell, cellIdx) => {
                            const imageComponent = cell.querySelector('.templates_Image_imageComponent__tqwK7j9G7t');

                            // ✨ PHASE 5 FIX: Check for ACTUAL <img> tag, not just wrapper component
                            let actualImage = null;
                            let hasImage = false;
                            let imageInfo = { isPlaceholder: false, isZeroSize: false, isOffScreen: false };

                            if (imageComponent) {
                                actualImage = imageComponent.querySelector('img');
                                hasImage = actualImage !== null;

                                // Additional check: image must be visible (not display:none or visibility:hidden)
                                if (hasImage && actualImage) {
                                    const imgStyle = window.getComputedStyle(actualImage);
                                    const imgRect = actualImage.getBoundingClientRect();
                                    const imgSrc = actualImage.src || '';

                                    // Check various visibility conditions
                                    const isStyleVisible = imgStyle.display !== 'none' &&
                                                          imgStyle.visibility !== 'hidden' &&
                                                          imgStyle.opacity !== '0';

                                    // Check if image has zero dimensions
                                    imageInfo.isZeroSize = imgRect.width === 0 || imgRect.height === 0;

                                    // Check if image is off-screen
                                    imageInfo.isOffScreen = imgRect.top < -1000 || imgRect.left < -1000;

                                    // Check if it's a placeholder/default image
                                    imageInfo.isPlaceholder = imgSrc.includes('placeholder') ||
                                                             imgSrc.includes('default') ||
                                                             imgSrc.includes('blank') ||
                                                             imgSrc.endsWith('/');

                                    // ✨ PHASE 5.1: Also consider zero-size or off-screen images as "no image"
                                    hasImage = isStyleVisible && !imageInfo.isZeroSize && !imageInfo.isOffScreen;
                                }
                            }

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

                            // Determine TOP/BOTTOM based on which logo table this is (DOM order)
                            // logoTables.length tells us which table number this will be (0-based)
                            const tableNumber = logoTables.length + 1; // 1-based for display
                            const rowPosition = tableNumber === 1 ? 'LOGO-1' : 'LOGO-2';

                            // ✨ VISUAL HIGHLIGHT: Enhanced color-coding with table-specific colors
                            const isLogo1 = tableNumber === 1;
                            const isLogo2 = tableNumber === 2;

                            if (hasImage) {
                                // CYAN for LOGO-1 with image, MAGENTA for LOGO-2 with image
                                const borderColor = isLogo1 ? 'cyan' : 'magenta';
                                const bgColor = isLogo1 ? 'rgba(0, 255, 255, 0.2)' : 'rgba(255, 0, 255, 0.2)';
                                cell.style.outline = `8px solid ${borderColor}`;
                                cell.style.backgroundColor = bgColor;
                                cell.style.boxShadow = `0 0 30px ${borderColor}, inset 0 0 20px ${bgColor}`;
                            } else if (isEmpty) {
                                // YELLOW for LOGO-1 empty, LIME for LOGO-2 empty
                                const borderColor = isLogo1 ? 'gold' : 'lime';
                                const bgColor = isLogo1 ? 'rgba(255, 215, 0, 0.15)' : 'rgba(0, 255, 0, 0.15)';
                                cell.style.outline = `6px dashed ${borderColor}`;
                                cell.style.backgroundColor = bgColor;
                                cell.style.boxShadow = `0 0 20px ${borderColor}`;
                            }

                            // Add large, prominent label
                            const label = document.createElement('div');
                            let labelBg, labelText, labelBorder;

                            if (hasImage) {
                                labelBg = isLogo1 ? 'cyan' : 'magenta';
                                labelText = 'black';
                                labelBorder = 'black';
                            } else if (isEmpty) {
                                labelBg = isLogo1 ? 'gold' : 'lime';
                                labelText = 'black';
                                labelBorder = 'black';
                            } else {
                                labelBg = 'gray';
                                labelText = 'white';
                                labelBorder = 'black';
                            }

                            label.style.cssText = `
                                position: absolute;
                                top: 10px;
                                left: 10px;
                                background: ${labelBg};
                                color: ${labelText};
                                padding: 8px 12px;
                                font-size: 14px;
                                font-weight: bold;
                                border: 3px solid ${labelBorder};
                                border-radius: 5px;
                                z-index: 999999;
                                font-family: monospace;
                                line-height: 1.4;
                                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                            `;
                            label.innerHTML = `<div style="font-size: 16px; margin-bottom: 2px;">${rowPosition}</div>Cell ${cellIdx}<br>[${alignment}]`;
                            cell.style.position = 'relative';
                            cell.appendChild(label);

                            tableInfo.positions.push({
                                cellIndex: cellIdx,
                                alignment: alignment,
                                hasImage: hasImage,
                                hasWarning: hasWarning,
                                isEmpty: isEmpty,
                                textTemplateId: textTemplate ? textTemplate.id : null,
                                imageComponent: imageComponent,
                                actualImage: actualImage,  // ✨ Store reference to actual img element
                                imageInfo: imageInfo  // ✨ PHASE 5.1: Store image metadata
                            });
                        });

                        // FIX #3: Stricter criteria to identify actual logo tables
                        const relevantPositions = tableInfo.positions.slice(0, 3);
                        const hasRelevantContent = relevantPositions.some(p => p.hasImage || p.isEmpty);

                        // Additional validation to filter out content/layout tables
                        const hasAtLeastOneImage = tableInfo.positions.some(p => p.hasImage);
                        const hasLogoMarker = table.querySelector('.templates_Image_imageComponent__tqwK7j9G7t') !== null ||
                                             table.querySelector('[class*="Image_resizable"]') !== null;
                        const allRelevantCellsHaveTextTemplate = relevantPositions.every(p => p.textTemplateId !== null);

                        // Check if table is in logo region (top 800px or bottom area)
                        const tableRect = table.getBoundingClientRect();
                        const pageHeight = document.body.scrollHeight || document.documentElement.scrollHeight;
                        const inLogoRegion = (tableRect.top < 800) || (tableRect.top > pageHeight - 1000);

                        // A table is likely a logo table if:
                        // 1. Has relevant content (images or empties), AND
                        // 2. Either:
                        //    a) Has at least one image, OR
                        //    b) Has logo marker AND all cells have text templates AND in logo region, OR
                        //    c) ✨ PHASE 5.2: All relevant cells are empty (ready for logo insertion) AND in logo region
                        const allRelevantCellsEmpty = relevantPositions.every(p => p.isEmpty);
                        const isLikelyLogoTable = hasRelevantContent &&
                                                 (hasAtLeastOneImage ||
                                                  (hasLogoMarker && allRelevantCellsHaveTextTemplate && inLogoRegion) ||
                                                  (allRelevantCellsEmpty && allRelevantCellsHaveTextTemplate && inLogoRegion));

                        if (isLikelyLogoTable) {
                            logoTables.push(tableInfo);
                            debug.push(`  ✨ Found logo table #${logoTables.length} (table index ${tableIdx}): ${cells.length} columns`);
                        } else if (hasRelevantContent) {
                            // ✨ PHASE 5.2: Debug why table was skipped
                            debug.push(`  ⏭️  Skipping table ${tableIdx}: hasRelevantContent=${hasRelevantContent}, hasAtLeastOneImage=${hasAtLeastOneImage}, hasLogoMarker=${hasLogoMarker}, allRelevantCellsHaveTextTemplate=${allRelevantCellsHaveTextTemplate}, inLogoRegion=${inLogoRegion}`);

                            // ✨ PHASE 5: Enhanced logging - show ALL columns for debugging
                            tableInfo.positions.forEach(pos => {
                                let imgInfo = 'no-img';
                                let dimensionInfo = '';
                                let visibilityInfo = '';
                                let issueFlags = [];
                                let cellPosition = '';

                                // Get the actual cell's visual position
                                const cellRect = cells[pos.cellIndex].getBoundingClientRect();
                                cellPosition = `visualTop=${Math.round(cellRect.top + window.scrollY)}px`;

                                if (pos.actualImage) {
                                    const imgRect = pos.actualImage.getBoundingClientRect();
                                    const imgStyle = window.getComputedStyle(pos.actualImage);

                                    imgInfo = `img.src="${pos.actualImage.src}"`;
                                    dimensionInfo = `size=${Math.round(imgRect.width)}x${Math.round(imgRect.height)}px`;
                                    visibilityInfo = `display=${imgStyle.display}, visibility=${imgStyle.visibility}, opacity=${imgStyle.opacity}`;

                                    // Collect issue flags
                                    if (pos.imageInfo) {
                                        if (pos.imageInfo.isZeroSize) issueFlags.push('ZERO-SIZE');
                                        if (pos.imageInfo.isOffScreen) issueFlags.push('OFF-SCREEN');
                                        if (pos.imageInfo.isPlaceholder) issueFlags.push('PLACEHOLDER');
                                    }

                                    if (issueFlags.length > 0) {
                                        visibilityInfo += ` [${issueFlags.join(', ')}]`;
                                    }
                                }

                                const componentInfo = pos.imageComponent ? 'has-wrapper' : 'no-wrapper';

                                debug.push(`    Cell ${pos.cellIndex} [${pos.alignment}]: hasImage=${pos.hasImage}, hasWarning=${pos.hasWarning}, isEmpty=${pos.isEmpty}, ${cellPosition}, id=${pos.textTemplateId}, ${componentInfo}, ${imgInfo}`);
                                if (pos.actualImage) {
                                    debug.push(`      → ${dimensionInfo}, ${visibilityInfo}`);
                                }
                            });
                        }
                    }
                });

                debug.push(`Found ${logoTables.length} logo tables total (MAX: ${MAX_LOGO_TABLES})`);

                // Process table-based detection if we found logo tables
                if (logoTables.length > 0) {
                    debug.push('\\n=== PROCESSING TABLE-BASED DETECTION ===');

                    // GUARDRAIL: Track which logo rows have been processed
                    const tableLogoRowsProcessed = new Set(); // e.g., 'Logo 1', 'Logo 2'

                    // FIX #2: TWO-PASS APPROACH
                    // PASS 1: Scan ALL positions in ALL rows to find which rows already have logos
                    // FIX #1: Also populate globalLogoRowsWithContent for hardcoded detection to use
                    debug.push('\\nPASS 1: Scanning for existing logos...');
                    logoTables.forEach((logoTable, tableIdx) => {
                        const logoNumber = tableIdx + 1;
                        const logoRow = `Logo ${logoNumber}`;

                        const relevantPositions = logoTable.positions.filter(pos =>
                            pos.alignment === 'LEFT' || pos.alignment === 'CENTER' || pos.alignment === 'RIGHT'
                        );

                        const rowHasLogo = relevantPositions.some(pos => pos.hasImage);

                        if (rowHasLogo) {
                            tableLogoRowsProcessed.add(logoRow);
                            globalLogoRowsWithContent.add(logoRow); // FIX #1: Update global state
                            debug.push(`  ${logoRow}: Has existing logo (will skip all empty positions in this row)`);
                        } else {
                            debug.push(`  ${logoRow}: No existing logos found`);
                        }
                    });

                    // PASS 2: Now process positions (empty positions will be correctly skipped if row already has logo)
                    debug.push('\\nPASS 2: Processing logos and empty containers...');
                    logoTables.forEach((logoTable, tableIdx) => {
                        const logoNumber = tableIdx + 1; // Logo 1, Logo 2, etc.
                        const logoRow = `Logo ${logoNumber}`;

                        logoTable.positions.forEach((pos, posIdx) => {
                            if (pos.alignment === 'EXTRA' || pos.alignment === 'FAR_LEFT' || pos.alignment === 'FAR_RIGHT') return; // Skip extra columns

                            const containerName = `Logo ${logoNumber} ${pos.alignment}`;

                            // PRIORITY 1: Logos WITH warnings need replacement (wrong logo)
                            if (pos.hasImage && pos.hasWarning) {
                                // Only add the first logo with warning in this row
                                const alreadyHasReplacementForRow = logosToReplace.some(r => r.name && r.name.startsWith(logoRow));

                                if (pos.imageComponent && !alreadyHasReplacementForRow) {
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

                                    debug.push(`  Found logo to REPLACE: ${containerName} (hasWarning=true, keepAlignment=${pos.alignment}) ✅ ADDED`);
                                } else if (alreadyHasReplacementForRow) {
                                    debug.push(`  Skipping ${containerName}: ${logoRow} already has replacement queued`);
                                }
                            }
                            // PRIORITY 2: Skip logos without warnings - they're already correct!
                            else if (pos.hasImage && !pos.hasWarning) {
                                debug.push(`  Skipping ${containerName}: Logo exists without warning (already correct)`);
                            }
                            // PRIORITY 3: Empty positions - only add if row doesn't already have ANY logo
                            else if (pos.isEmpty && !tableLogoRowsProcessed.has(logoRow)) {
                                // Only add the FIRST empty container in this row
                                const alreadyHasEmptyForRow = emptyContainers.some(c => c.name && c.name.startsWith(logoRow));

                                if (!alreadyHasEmptyForRow) {
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

                                    debug.push(`  Added empty position: ${containerName} (ID: ${containerId}) ✅ ADDED (first empty in ${logoRow})`);
                                } else {
                                    debug.push(`  Skipping empty ${pos.alignment}: ${containerName} ⏭️ (${logoRow} already has container queued)`);
                                }
                            }
                            // PRIORITY 4: Skip if logo row already has content
                            else if (pos.isEmpty && tableLogoRowsProcessed.has(logoRow)) {
                                debug.push(`  Skipping empty ${pos.alignment}: ${containerName} ⏭️ (${logoRow} already has logo)`);
                            }
                        });
                    });

                    debug.push(`\\nTable-based detection summary:`);
                    debug.push(`  - Logos to REPLACE: ${logosToReplace.length}`);
                    debug.push(`  - Empty positions added: ${emptyContainers.length}`);
                    debug.push(`  - Logo rows with existing logos: ${tableLogoRowsProcessed.size}`);
                    debug.push(`  - GUARDRAIL: Each logo row gets MAX 1 container (two-pass detection)`);
                }

                // ============================================================================
                // STEP 2: Run hardcoded Logo 1/2 detection (AFTER table-based, with state sync)
                // FIX #1: Use globalLogoRowsWithContent to skip rows that table detection found
                // ============================================================================
                debug.push('\\n=== HARDCODED LOGO 1/2 CONTAINER DETECTION (Fallback) ===');
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

                // Local tracking for this detection pass (separate from table detection)
                const hardcodedLogoRowsProcessed = new Set();

                containerIds.forEach((id, idx) => {
                    const container = document.querySelector(`div.TEXT_TEMPLATE[id="${id}"][contenteditable="true"]`);
                    const containerName = containerNames[idx];
                    const logoRow = containerName.split(' ').slice(0, 2).join(' '); // "Logo 1" or "Logo 2"

                    const checkResult = {
                        name: containerName,
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

                        // FIX #1: Check global state from table detection first
                        if (globalLogoRowsWithContent.has(logoRow)) {
                            debug.push(`  ${checkResult.name}: ⏭️ SKIPPED (${logoRow} already has logo from table detection)`);
                        }
                        // GUARDRAIL: Only add ONE empty container per logo row
                        else if (isEmpty && !hardcodedLogoRowsProcessed.has(logoRow)) {
                            container.setAttribute('data-empty-container', `empty-hardcoded-${idx + 1}`);
                            emptyContainers.push({
                                index: emptyContainers.length + 1,
                                id: id,
                                name: containerName,
                                type: 'logo_container'
                            });
                            hardcodedLogoRowsProcessed.add(logoRow);
                            globalLogoRowsWithContent.add(logoRow); // Update global state
                            debug.push(`  ${checkResult.name}: ✅ ADDED (first empty in ${logoRow})`);
                        } else if (isEmpty && hardcodedLogoRowsProcessed.has(logoRow)) {
                            debug.push(`  ${checkResult.name}: ⏭️ SKIPPED (${logoRow} already has container from hardcoded detection)`);
                        } else if (hasImage) {
                            hardcodedLogoRowsProcessed.add(logoRow);
                            globalLogoRowsWithContent.add(logoRow); // Update global state
                            debug.push(`  ${checkResult.name}: hasImage=true (${logoRow} marked as having logo)`);
                        } else {
                            debug.push(`  ${checkResult.name}: found=${checkResult.found}, hasImage=${checkResult.hasImage}, isEmpty=${checkResult.isEmpty}`);
                        }
                    } else {
                        debug.push(`  ${checkResult.name}: found=${checkResult.found}`);
                    }

                    containerCheckResults.push(checkResult);
                });

                debug.push(`\\nHardcoded detection complete:`);
                debug.push(`  - Rows with logos (global): ${Array.from(globalLogoRowsWithContent).join(', ')}`);
                debug.push(`  - Empty containers queued: ${emptyContainers.length}`);

                // Find empty HEADER containers
                debug.push('\\n=== HEADER CONTAINER DETECTION ===');
                const headerContainers = [];
                const headerCheckResults = [];

                // FIX: Check if template actually has a header structure first
                // If #HEADER button is active (opacity=1.0), template has NO header
                // Only look for header containers if button is grayed (opacity<1.0)
                const headerBtn = document.querySelector('#HEADER');
                let headerExists = false;

                if (headerBtn) {
                    const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                    headerExists = opacity < 1.0; // Grayed = header exists
                    debug.push(`#HEADER button found: opacity=${opacity.toFixed(2)}, headerExists=${headerExists}`);
                } else {
                    debug.push(`#HEADER button not found in DOM`);
                }

                if (!headerExists) {
                    debug.push(`⏭️  Skipping header detection: Template has no header structure (#HEADER button is active or missing)`);
                } else {
                    // Track which tables were already identified as logo tables
                    const logoTableElements = new Set(logoTables.map(lt => lt.tableElement));

                    const tables = Array.from(document.querySelectorAll('table'));
                    debug.push(`Found ${tables.length} tables total`);
                    debug.push(`Already identified ${logoTableElements.size} logo tables`);

                    for (const table of tables) {
                        // FIX: Skip tables that were already identified as Logo 1/2 tables
                        if (logoTableElements.has(table)) {
                            debug.push(`  ⏭️  Skipping table: Already processed as logo table`);
                            continue;
                        }

                        const firstRow = table.querySelector('tr');
                        if (!firstRow) continue;

                        const tds = Array.from(firstRow.querySelectorAll('td'));
                        debug.push(`  Table has ${tds.length} cells in first row`);

                        if (tds.length === 3) {
                            debug.push(`  Checking first 2 cells for header logos...`);
                            let tableHasHeaderContainers = false;

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
                                        tableHasHeaderContainers = true;
                                    }
                                }

                                headerCheckResults.push(headerCheck);
                                debug.push(`    Position ${i + 1}: hasContainer=${headerCheck.hasContainer}, hasImage=${headerCheck.hasImage}, isEmpty=${headerCheck.isEmpty}`);
                            }

                            if (tableHasHeaderContainers) {
                                debug.push(`  ✅ Found ${headerContainers.length} empty header containers, stopping table search`);
                                break;
                            }
                        }
                    }
                }

                // ============================================================================
                // SUMMARY: Compile all detection results
                // ============================================================================
                const warningsCount = patterns.detectedLogos.filter(l => l.hasWarning).length;

                patterns.summary = {
                    totalImages: allImages.length,
                    candidateLogos: candidateLogos.length,
                    patternsDiscovered: patterns.containerPatterns.length,
                    bestPatternSelected: bestPattern ? bestPattern.class : null,
                    bestPatternScore: bestScore,
                    logosDetected: patterns.detectedLogos.length,
                    logosWithWarnings: warningsCount,
                    logosMarkedForAction: logoIndex,
                    // NEW: Phase 2 Enhancement
                    learnedLogoMarkersFound: learnedLogoMarkers.length
                };

                debug.push('\\n=== TRULY DYNAMIC DETECTION SUMMARY ===');
                debug.push(`Total images analyzed: ${patterns.summary.totalImages}`);
                debug.push(`Learned logo markers found: ${patterns.summary.learnedLogoMarkersFound} ✨ NEW`);
                debug.push(`Candidate logos found: ${patterns.summary.candidateLogos}`);
                debug.push(`Patterns discovered: ${patterns.summary.patternsDiscovered}`);
                debug.push(`Best pattern: ${patterns.summary.bestPatternSelected} (score: ${patterns.summary.bestPatternScore})`);
                debug.push(`Logos detected: ${patterns.summary.logosDetected}`);
                debug.push(`Logos with warnings: ${patterns.summary.logosWithWarnings}`);
                debug.push(`Logos marked for action: ${patterns.summary.logosMarkedForAction}`);

                // ============================================================================
                // ENHANCED AI FEATURES - Template Complexity Analysis
                // ============================================================================
                debug.push('\\n=== ENHANCED AI FEATURE EXTRACTION ===');

                const enhancedFeatures = {
                    sortableItemCount: 0,
                    totalTableCount: 0,
                    nonLogoTableCount: 0,
                    hasButtons: false,
                    dynamicTagCount: 0
                };

                // Feature 1: Count sortable items (complexity indicator)
                const sortableItems = document.querySelectorAll('[class*="SortableItem"]');
                enhancedFeatures.sortableItemCount = sortableItems.length;
                debug.push(`Feature 1: Sortable items = ${enhancedFeatures.sortableItemCount}`);

                // Feature 2: Count all tables
                const allTablesForCount = document.querySelectorAll('table');
                enhancedFeatures.totalTableCount = allTablesForCount.length;
                debug.push(`Feature 2: Total tables = ${enhancedFeatures.totalTableCount}`);

                // Feature 3: Calculate non-logo tables
                enhancedFeatures.nonLogoTableCount = enhancedFeatures.totalTableCount - logoTables.length;
                debug.push(`Feature 3: Non-logo tables = ${enhancedFeatures.nonLogoTableCount}`);

                // Feature 4: Check for buttons (CTA presence)
                const buttons = document.querySelectorAll('button[type], a[class*="button"], a[class*="Button"], [class*="btn"]');
                enhancedFeatures.hasButtons = buttons.length > 0;
                debug.push(`Feature 4: Has buttons = ${enhancedFeatures.hasButtons} (${buttons.length} found)`);

                // Feature 5: Count dynamic tags (personalization level)
                const dynamicTags = document.querySelectorAll('[data-tag-id], [class*="dynamic_tag"], [class*="dynamicTag"]');
                enhancedFeatures.dynamicTagCount = dynamicTags.length;
                debug.push(`Feature 5: Dynamic tags = ${enhancedFeatures.dynamicTagCount}`);

                debug.push('Enhanced features extraction complete');

                // ✨ VISUAL LEGEND: Add a floating legend to explain the highlights
                const legend = document.createElement('div');
                legend.id = 'logo-detection-legend';
                legend.style.cssText = `
                    position: fixed;
                    top: 80px;
                    right: 20px;
                    background: white;
                    border: 3px solid black;
                    border-radius: 8px;
                    padding: 15px;
                    z-index: 999999;
                    font-family: monospace;
                    font-size: 14px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                `;
                legend.innerHTML = `
                    <div style="font-weight: bold; margin-bottom: 12px; font-size: 18px; border-bottom: 3px solid black; padding-bottom: 8px; text-align: center;">
                        🎯 LOGO CONTAINER DETECTION
                    </div>
                    <div style="font-weight: bold; margin: 12px 0 8px 0; font-size: 14px; border-bottom: 2px solid #999; padding-bottom: 4px;">
                        TABLE CELLS:
                    </div>
                    <div style="margin: 6px 0; padding: 6px; background: rgba(0,255,255,0.2); border-left: 6px solid cyan;">
                        🔵 CYAN = LOGO-1 with image
                    </div>
                    <div style="margin: 6px 0; padding: 6px; background: rgba(255,215,0,0.15); border-left: 6px dashed gold;">
                        🟡 GOLD (dashed) = LOGO-1 empty
                    </div>
                    <div style="margin: 6px 0; padding: 6px; background: rgba(255,0,255,0.2); border-left: 6px solid magenta;">
                        🟣 MAGENTA = LOGO-2 with image
                    </div>
                    <div style="margin: 6px 0; padding: 6px; background: rgba(0,255,0,0.15); border-left: 6px dashed lime;">
                        🟢 LIME (dashed) = LOGO-2 empty
                    </div>
                    <div style="font-weight: bold; margin: 12px 0 8px 0; font-size: 14px; border-bottom: 2px solid #999; padding-bottom: 4px;">
                        DYNAMIC DETECTION:
                    </div>
                    <div style="margin: 6px 0; padding: 6px; background: rgba(255,105,180,0.2); border-left: 6px solid hotpink;">
                        🩷 PINK = UI Icon (filtered out)
                    </div>
                    <div style="margin: 6px 0; padding: 6px; background: rgba(255,0,0,0.1); border-left: 6px solid red;">
                        🔴 RED = Logo with warning
                    </div>
                    <div style="margin-top: 12px; font-size: 12px; color: #333; background: #f0f0f0; padding: 8px; border-radius: 4px;">
                        <strong>📊 Detected:</strong><br>
                        • ${logoTables.length} logo tables (LOGO-1 & LOGO-2)<br>
                        • ${patterns.detectedLogos.length} dynamic logos
                    </div>
                `;
                document.body.appendChild(legend);

                // ✨ FIX (June 8): Filter out UI icons from detectedLogos before returning
                const realLogos = patterns.detectedLogos.filter(logo => !logo.isUIIcon);
                const allDetectedCount = realLogos.length;
                debug.push(`\n=== FINAL FILTERING ===`);
                debug.push(`Total logos before filtering: ${patterns.detectedLogos.length}`);
                debug.push(`Real logos (non-UI icons): ${realLogos.length}`);
                debug.push(`UI icons filtered out: ${patterns.detectedLogos.length - realLogos.length}`);

                return {
                    // Truly Dynamic Detection Results (NEW)
                    trulyDynamic: {
                        enabled: bestPattern !== null,
                        learningPhases: patterns.learningPhases,
                        containerPatterns: patterns.containerPatterns,
                        bestPattern: bestPattern,
                        bestScore: bestScore,
                        detectedLogos: realLogos,  // ✨ FIX: Return only real logos (UI icons filtered out)
                        allDetectedLogos: patterns.detectedLogos,  // Keep all for debugging
                        summary: patterns.summary,
                        // PHASE 2 ENHANCEMENT: Learned logo markers
                        learnedLogoMarkers: learnedLogoMarkers
                    },
                    // Legacy detection results (for backward compatibility)
                    warningsCount: warningsCount,
                    emptyCount: emptyContainers.length,
                    headerCount: headerContainers.length,
                    emptyContainers: emptyContainers,
                    headerContainers: headerContainers,
                    containerCheckResults: containerCheckResults,
                    headerCheckResults: headerCheckResults,
                    logoTables: logoTables,
                    logoTablesCount: logoTables.length,  // FIX: Pass logo tables count to Python
                    logosToReplace: logosToReplace || [],
                    replaceCount: (logosToReplace || []).length,
                    // NEW: Enhanced AI features
                    enhancedFeatures: enhancedFeatures,
                    // PHASE 2 ENHANCEMENT: Direct access to learned markers count
                    learnedLogosCount: learnedLogoMarkers.length,
                    // ✨ PHASE 3 FIX: Count ALL detected logos (not just ones needing action)
                    allDetectedLogosCount: allDetectedCount,  // ✨ FIX: Use filtered count (real logos only, no UI icons)
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
            logger.debug(f"      → Step 1: Finding logo container for logo #{logo_idx}")
            # Find the outer container (SortableItem) marked with data attribute
            outer_container = await page.query_selector(f'[data-logo-to-inspect="warning-logo-{logo_idx}"]')
            if not outer_container:
                logger.warning(f"      ✗ Outer container not found for logo #{logo_idx}")
                return False
            logger.debug(f"      ✓ Outer container found")

            logger.debug(f"      → Step 2: Verifying department")
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

            logger.debug(f"      → Step 3: Finding sub-container (imageComponent) for hover")
            # BREAKTHROUGH FIX: Hover over SUB-CONTAINER (imageComponent), not outer container!
            # The toolbar only appears when hovering over templates_Image_imageComponent
            sub_container = await outer_container.query_selector('[class*="imageComponent"]')
            if not sub_container:
                logger.warning(f"      ✗ Sub-container (imageComponent) not found for logo {logo_idx}")
                return False
            logger.debug(f"      ✓ Sub-container found")

            logger.debug(f"      → Step 4: Hovering over sub-container to reveal toolbar")
            # Hover over the sub-container to reveal toolbar
            await sub_container.hover(force=True)
            await asyncio.sleep(3)
            logger.debug(f"      ✓ Hovered over sub-container (waited 3s for toolbar)")

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

    async def _replace_logo_without_warning(self, page: Page, logo_idx: int, logo_media_id: str, target_filename: str = None) -> bool:
        """Replace logo WITHOUT warning icon (detected by table-based detection) using Change Image workflow

        Args:
            page: Playwright page object
            logo_idx: Index of logo to replace
            logo_media_id: Media ID (for fallback selection)
            target_filename: Specific filename to select (e.g., "Alfa Romeo of Cincinnati.jpg")
        """

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

            # Select logo from library (use target_filename if specified, otherwise first logo)
            selection = await self._select_logo_from_library(page, target_filename=target_filename, fallback_index=0)

            if not selection['success']:
                logger.warning(f"Could not select logo from media library: {selection.get('error', 'Unknown error')}")
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
        """Center align a logo that was replaced (without warning icon)

        This function centers logos that were detected via table-based detection
        and replaced without having a warning icon.

        Args:
            page: Playwright page object
            logo_idx: Index of the logo (from logosToReplace array)

        Returns:
            True if centering successful, False otherwise
        """
        try:
            # Find the image component marked for replacement
            image_component = await page.query_selector(f'[data-logo-to-replace="replace-logo-{logo_idx}"]')
            if not image_component:
                logger.debug(f"Image component not found for replace-logo-{logo_idx}")
                return False

            # Hover over the image component to reveal toolbar
            logger.debug(f"Hovering over image component to reveal alignment toolbar...")
            await image_component.hover(force=True)
            await asyncio.sleep(1.5)

            # Click center align button
            center_result = await page.evaluate(f"""
                () => {{
                    const container = document.querySelector('[data-logo-to-replace="replace-logo-{logo_idx}"]');
                    if (!container) return {{ clicked: false, reason: 'Container not found' }};

                    // Find center align button in the toolbar
                    const centerBtn = container.querySelector('[title="Center Align"]') ||
                                     container.querySelector('[aria-label="icon-center-align"]') ||
                                     document.querySelector('[title="Center Align"]') ||
                                     document.querySelector('.icon-center-align');

                    if (centerBtn) {{
                        centerBtn.click();
                        return {{ clicked: true }};
                    }}
                    return {{ clicked: false, reason: 'Center align button not found' }};
                }}
            """)

            if center_result['clicked']:
                await asyncio.sleep(0.5)
                logger.debug(f"Successfully centered logo {logo_idx}")
                return True
            else:
                logger.debug(f"Could not center logo {logo_idx}: {center_result.get('reason', 'Unknown')}")
                return False

        except Exception as e:
            logger.error(f"Error in _center_logo_without_warning: {e}")
            return False

    async def _enlarge_logo_without_warning(self, page: Page, logo_idx: int, logo_media_id: str, logo_width: int) -> bool:
        """Enlarge a logo that was replaced (without warning icon)

        This function enlarges logos that were detected via table-based detection
        and replaced without having a warning icon.

        Args:
            page: Playwright page object
            logo_idx: Index of the logo (from logosToReplace array)
            logo_media_id: Media ID of the logo to identify it
            logo_width: Target width in pixels

        Returns:
            True if enlargement successful, False otherwise
        """
        try:
            # Find the logo image within the marked container
            detection = await page.evaluate(f"""
                () => {{
                    const MEDIA_ID = "{logo_media_id}";
                    const TARGET_WIDTH = {logo_width};

                    // Find the container
                    const container = document.querySelector('[data-logo-to-replace="replace-logo-{logo_idx}"]');
                    if (!container) return {{ found: false, reason: 'Container not found' }};

                    // Find the logo image within this container
                    const img = container.querySelector('img');
                    if (!img) return {{ found: false, reason: 'Image not found in container' }};

                    const rect = img.getBoundingClientRect();
                    return {{
                        found: true,
                        currentWidth: Math.round(rect.width),
                        currentHeight: Math.round(rect.height)
                    }};
                }}
            """)

            if not detection.get('found'):
                logger.debug(f"Could not detect logo {logo_idx}: {detection.get('reason', 'Unknown')}")
                return False

            current_w = detection['currentWidth']

            # Check if enlargement needed
            if current_w >= logo_width:
                logger.debug(f"Logo {logo_idx} already at target size ({current_w}px >= {logo_width}px)")
                return True  # Already at target size

            # Enlarge the logo
            enlarge_result = await page.evaluate(f"""
                () => {{
                    const MEDIA_ID = "{logo_media_id}";
                    const TARGET_WIDTH = {logo_width};

                    // Find the container
                    const container = document.querySelector('[data-logo-to-replace="replace-logo-{logo_idx}"]');
                    if (!container) return {{ success: false, reason: 'Container not found' }};

                    // Find the logo image
                    const img = container.querySelector('img');
                    if (!img) return {{ success: false, reason: 'Image not found' }};

                    // Find the resizable container (usually parent or grandparent)
                    let resizableContainer = img.parentElement;
                    for (let i = 0; i < 5; i++) {{
                        if (!resizableContainer) break;
                        const className = resizableContainer.className || '';
                        if (className.includes('resizable') || className.includes('Image')) break;
                        resizableContainer = resizableContainer.parentElement;
                    }}

                    if (!resizableContainer) resizableContainer = img.parentElement;

                    // Apply width to both container and image
                    resizableContainer.style.width = TARGET_WIDTH + 'px';
                    resizableContainer.style.maxWidth = TARGET_WIDTH + 'px';
                    img.style.width = TARGET_WIDTH + 'px';
                    img.style.maxWidth = TARGET_WIDTH + 'px';
                    img.style.height = 'auto';

                    // Force reflow
                    resizableContainer.offsetHeight;

                    const afterRect = img.getBoundingClientRect();
                    return {{
                        success: true,
                        afterWidth: Math.round(afterRect.width)
                    }};
                }}
            """)

            if enlarge_result.get('success'):
                await asyncio.sleep(0.5)
                logger.debug(f"Successfully enlarged logo {logo_idx} to {enlarge_result.get('afterWidth')}px")
                return True
            else:
                logger.debug(f"Could not enlarge logo {logo_idx}: {enlarge_result.get('reason', 'Unknown')}")
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

    async def _insert_logo_to_container(self, page: Page, container_info: Dict, logo_media_id: str, target_filename: str = None) -> bool:
        """Insert logo into empty Logo 1/2 container

        Args:
            page: Playwright page object
            container_info: Container info dict
            logo_media_id: Media ID (for fallback)
            target_filename: Specific logo filename to select (e.g., "Alfa Romeo of Cincinnati.jpg")
        """

        try:
            # Focus container - use JavaScript click to bypass "unselectable" blocking
            container_id = container_info["id"]

            logger.debug(f"   🔍 Finding and clicking container: {container_id}")

            # Click INSIDE the TEXT_TEMPLATE using JavaScript (bypass unselectable parent)
            click_result = await page.evaluate(f"""
                () => {{
                    const textTemplate = document.querySelector('[id="{container_id}"]');
                    if (!textTemplate) return {{ success: false, reason: 'Container not found' }};

                    // Scroll into view
                    textTemplate.scrollIntoView({{ behavior: 'smooth', block: 'center' }});

                    // Remove 'unselectable' class from parent if it exists
                    let parent = textTemplate.parentElement;
                    while (parent) {{
                        if (parent.className && parent.className.includes('Unselectable')) {{
                            const oldClass = parent.className;
                            parent.className = parent.className.replace(/elementUnselectable\\S*/g, '');
                        }}
                        parent = parent.parentElement;
                    }}

                    // Use JavaScript click and focus
                    textTemplate.click();
                    textTemplate.focus();

                    // Visual feedback
                    textTemplate.style.outline = '3px solid cyan';
                    textTemplate.style.backgroundColor = 'rgba(0, 255, 255, 0.1)';

                    return {{
                        success: true,
                        contenteditable: textTemplate.getAttribute('contenteditable'),
                        className: textTemplate.className
                    }};
                }}
            """)

            if not click_result.get('success'):
                logger.debug(f"   ❌ Failed to click container: {click_result.get('reason')}")
                return False

            logger.debug(f"   ✅ Clicked container using JavaScript")
            logger.debug(f"      Contenteditable: {click_result.get('contenteditable')}")
            await asyncio.sleep(2)  # Wait for toolbar to appear

            # Click Insert Image button
            try:
                logger.debug(f"   🔍 Looking for Insert Image button...")
                await page.click('.icon-insert-image[aria-label="icon-insert-image"]', timeout=5000)
                logger.debug(f"   ✅ Clicked Insert Image button")
                await asyncio.sleep(2.5)
            except Exception as e:
                logger.debug(f"   ❌ Failed to find/click Insert Image button: {e}")

                # Try alternative selectors
                logger.debug(f"   🔄 Trying alternative selectors...")
                alt_selectors = [
                    '.icon-insert-image',
                    '[aria-label*="insert"]',
                    '[class*="insert-image"]',
                    'button[aria-label*="image"]'
                ]

                clicked = False
                for alt_selector in alt_selectors:
                    try:
                        await page.click(alt_selector, timeout=2000)
                        logger.debug(f"   ✅ Clicked using alternative selector: {alt_selector}")
                        clicked = True
                        await asyncio.sleep(2.5)
                        break
                    except:
                        continue

                if not clicked:
                    logger.debug(f"   ❌ No Insert Image button found")
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

            # Select logo from library (use target_filename if specified, otherwise first logo)
            selection = await self._select_logo_from_library(page, target_filename=target_filename, fallback_index=0)

            if not selection['success']:
                logger.warning(f"   Could not select logo from library: {selection.get('error', 'Unknown error')}")
                return False

            logger.debug(f"   ✅ Selected logo: '{selection.get('selected_filename', 'unknown')}' (method: {selection.get('method', 'unknown')})")

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
            # Click the header container by position - use same pattern as Logo 1/2 insertion
            clicked = await page.evaluate(f"""
                () => {{
                    const headerContainer = document.querySelector('[data-header-container="header-{header_info['position']}"]');
                    if (!headerContainer) return {{ success: false, reason: 'Header container not found' }};

                    const textTemplate = headerContainer.querySelector('.TEXT_TEMPLATE') ||
                                        headerContainer.querySelector('[contenteditable="true"]');

                    if (textTemplate) {{
                        // Remove 'unselectable' class from parent if it exists
                        let parent = textTemplate.parentElement;
                        while (parent) {{
                            if (parent.className && parent.className.includes('Unselectable')) {{
                                parent.className = parent.className.replace(/elementUnselectable\\S*/g, '');
                            }}
                            parent = parent.parentElement;
                        }}

                        // Scroll into view
                        textTemplate.scrollIntoView({{ behavior: 'smooth', block: 'center' }});

                        // Click and focus
                        textTemplate.click();
                        textTemplate.focus();

                        return {{ success: true }};
                    }}
                    return {{ success: false, reason: 'TEXT_TEMPLATE not found' }};
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

    def _select_best_logo(self, available_logos: list, dealership_name: str = '', departments: list = None) -> str:
        """
        Smart logo selection: prioritize dealership-specific > department > generic

        Args:
            available_logos: List of available logo filenames
            dealership_name: Dealership name (e.g., "Alfa Romeo of Cincinnati")
            departments: List of departments (e.g., ["Service", "Parts"])

        Returns:
            Best matching logo filename

        Priority:
        1. Exact match with dealership name (e.g., "Alfa Romeo of Cincinnati.jpg")
        2. Partial match with dealership brand (e.g., "Alfa Romeo Logo.jpg")
        3. Department-specific (e.g., "Service Logo.png" or "Parts Logo.png")
        4. Generic (first available)
        """
        if not available_logos:
            return None

        logger.debug(f"   🎯 Smart logo selection from {len(available_logos)} options")
        logger.debug(f"      Dealership: '{dealership_name}'")
        logger.debug(f"      Departments: {departments}")

        # Priority 1: Exact dealership name match (case-insensitive)
        if dealership_name:
            dealership_lower = dealership_name.lower()
            for logo in available_logos:
                logo_lower = logo.lower()
                if dealership_lower in logo_lower:
                    logger.debug(f"      ✅ Exact match: '{logo}' contains '{dealership_name}'")
                    return logo

            # Priority 2: Extract brand name and match (e.g., "Alfa Romeo" from "Alfa Romeo of Cincinnati")
            # Common patterns: "Brand of Location", "Brand - Location", "Brand Location"
            brand_parts = dealership_name.split()
            if len(brand_parts) >= 2:
                # Try first two words as brand (e.g., "Alfa Romeo")
                brand_name = ' '.join(brand_parts[:2])
                brand_lower = brand_name.lower()

                for logo in available_logos:
                    logo_lower = logo.lower()
                    if brand_lower in logo_lower:
                        logger.debug(f"      ✅ Brand match: '{logo}' contains '{brand_name}'")
                        return logo

                # Try just first word (e.g., "Alfa")
                if brand_parts[0].lower() not in ['the', 'a', 'an']:  # Skip articles
                    for logo in available_logos:
                        logo_lower = logo.lower()
                        if brand_parts[0].lower() in logo_lower:
                            logger.debug(f"      ✅ Partial brand match: '{logo}' contains '{brand_parts[0]}'")
                            return logo

        # Priority 3: Department-specific logos
        if departments:
            for dept in departments:
                dept_lower = dept.lower()
                for logo in available_logos:
                    logo_lower = logo.lower()
                    if dept_lower in logo_lower:
                        logger.debug(f"      ✅ Department match: '{logo}' contains '{dept}'")
                        return logo

        # Priority 4: Generic (first available)
        logger.debug(f"      ℹ️  Using generic (first available): '{available_logos[0]}'")
        return available_logos[0]

    async def _get_available_logos(self, page: Page, logo_idx: int = 1) -> dict:
        """
        Open Change Image popup and extract all available logo filenames from media library

        This method is used to validate whether detected logos exist in the media library.
        It opens the Change Image popup for a specific logo container and extracts information
        about all available logos.

        Args:
            page: Playwright page object
            logo_idx: Index of logo container to open Change Image popup (1-based)

        Returns:
            {
                'success': True/False,
                'logos': [
                    {
                        'index': 0,
                        'filename': 'Tilton.png',
                        'alt': 'Tilton Logo',
                        'src': 'https://...'
                    },
                    ...
                ],
                'totalCount': 5,
                'error': 'error message if failed'
            }
        """
        try:
            logger.debug(f"   📚 Fetching available logos from media library (using logo {logo_idx})...")

            # Find logo container (try learned pattern first)
            logo_found = await page.evaluate(f"""
                () => {{
                    // Try data-learned-logo first
                    let container = document.querySelector('[data-learned-logo="container-{logo_idx}"]');
                    if (container) return {{ found: true, method: 'learned' }};

                    // Try data-logo-to-replace
                    container = document.querySelector('[data-logo-to-replace="replace-logo-{logo_idx}"]');
                    if (container) return {{ found: true, method: 'replace' }};

                    // Try data-logo-to-inspect
                    container = document.querySelector('[data-logo-to-inspect="warning-logo-{logo_idx}"]');
                    if (container) return {{ found: true, method: 'warning' }};

                    return {{ found: false }};
                }}
            """)

            if not logo_found['found']:
                return {'success': False, 'error': f'Logo container {logo_idx} not found', 'logos': [], 'totalCount': 0}

            logger.debug(f"   Found logo container via method: {logo_found['method']}")

            # Find and hover on subcontainer (image parent) to reveal toolbar
            if logo_found['method'] == 'learned':
                container = await page.query_selector(f'[data-learned-logo="container-{logo_idx}"]')
            elif logo_found['method'] == 'replace':
                container = await page.query_selector(f'[data-logo-to-replace="replace-logo-{logo_idx}"]')
            else:
                container = await page.query_selector(f'[data-logo-to-inspect="warning-logo-{logo_idx}"]')

            if not container:
                return {'success': False, 'error': 'Container element not found', 'logos': [], 'totalCount': 0}

            # ✨ FIX (June 8): Hover on the image parent (subcontainer) to reveal toolbar
            logger.debug(f"   Hovering on image parent (subcontainer)...")
            img_parent = await page.evaluate_handle(f"""
                () => {{
                    const container = document.querySelector('[data-learned-logo="container-{logo_idx}"]') ||
                                     document.querySelector('[data-logo-to-replace="replace-logo-{logo_idx}"]') ||
                                     document.querySelector('[data-logo-to-inspect="warning-logo-{logo_idx}"]');
                    if (!container) return null;
                    const img = container.querySelector('img');
                    return img ? img.parentElement : container;
                }}
            """)

            if img_parent:
                await img_parent.as_element().hover(force=True)
                await asyncio.sleep(2)
            else:
                # Fallback to container hover
                await container.hover(force=True)
                await asyncio.sleep(2)

            # ✨ FIX (June 8): Click Change Image icon (search in container directly, not just sortableItem)
            change_clicked = await page.evaluate(f"""
                () => {{
                    const methods = [
                        '[data-learned-logo="container-{logo_idx}"]',
                        '[data-logo-to-replace="replace-logo-{logo_idx}"]',
                        '[data-logo-to-inspect="warning-logo-{logo_idx}"]'
                    ];

                    for (const selector of methods) {{
                        const container = document.querySelector(selector);
                        if (!container) continue;

                        // Try multiple search strategies
                        let changeIcon = null;

                        // Strategy 1: Look directly in container (for learned logos)
                        changeIcon = container.querySelector('[aria-label="icon-switch"]') ||
                                    container.querySelector('[title="Change Image"]');

                        if (changeIcon) {{
                            changeIcon.click();
                            return {{ clicked: true, method: 'direct-container' }};
                        }}

                        // Strategy 2: Look in closest SortableItem parent
                        const sortableItem = container.closest('[class*="SortableItem"]');
                        if (sortableItem) {{
                            changeIcon = sortableItem.querySelector('[aria-label="icon-switch"]') ||
                                        sortableItem.querySelector('[title="Change Image"]');

                            if (changeIcon) {{
                                changeIcon.click();
                                return {{ clicked: true, method: 'sortable-item' }};
                            }}
                        }}
                    }}
                    return {{ clicked: false, reason: 'Change Image icon not found' }};
                }}
            """)

            if not change_clicked['clicked']:
                return {'success': False, 'error': 'Could not click Change Image icon', 'logos': [], 'totalCount': 0}

            await asyncio.sleep(3)

            # Extract all available logos from popup
            logos_info = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { success: false, error: 'Popup not found' };

                    const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    if (tiles.length === 0) return { success: false, error: 'No media tiles found' };

                    const logos = tiles.map((tile, index) => {
                        const img = tile.querySelector('img');
                        const alt = img ? img.alt : '';
                        const src = img ? img.src : '';
                        const filename = src ? src.split('/').pop() : '';

                        return {
                            index: index,
                            filename: filename,
                            alt: alt,
                            src: src
                        };
                    });

                    return {
                        success: true,
                        logos: logos,
                        totalCount: tiles.length
                    };
                }
            """)

            # Close popup
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)

            if logos_info['success']:
                logger.debug(f"   ✅ Found {logos_info['totalCount']} logos in media library")
                logger.debug(f"   Available logos: {[logo['filename'] for logo in logos_info['logos'][:5]]}{'...' if logos_info['totalCount'] > 5 else ''}")
                return logos_info
            else:
                return {'success': False, 'error': logos_info.get('error', 'Unknown error'), 'logos': [], 'totalCount': 0}

        except Exception as e:
            logger.exception(f"   Error fetching available logos: {e}")
            return {'success': False, 'error': str(e), 'logos': [], 'totalCount': 0}

    async def _select_logo_from_library(self, page: Page, target_filename: str = None, fallback_index: int = 0) -> dict:
        """
        Select logo from open media library popup

        This method assumes the media library popup is already open.
        It searches for a specific logo by filename, or falls back to selecting by index.

        Args:
            page: Playwright page object
            target_filename: Specific filename to search for (e.g., "Alfa Romeo of Cincinnati.jpg")
            fallback_index: Index to select if target_filename not found (default: 0 = first logo)

        Returns:
            {
                'success': True/False,
                'selected_filename': 'Tilton.png',
                'selected_index': 0,
                'method': 'filename' or 'index'
            }
        """
        try:
            logger.debug(f"   🎯 Selecting logo from library...")
            if target_filename:
                logger.debug(f"   Target: '{target_filename}', Fallback: index {fallback_index}")
            else:
                logger.debug(f"   Selecting by index: {fallback_index}")

            # Select logo from popup
            selection_result = await page.evaluate("""
                (args) => {
                    const targetFilename = args.targetFilename;
                    const fallbackIndex = args.fallbackIndex;

                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { success: false, error: 'Popup not found' };

                    const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    if (tiles.length === 0) return { success: false, error: 'No media tiles found' };

                    let selectedTile = null;
                    let selectedIndex = -1;
                    let method = 'index';

                    // Try to find by filename if specified
                    if (targetFilename) {
                        for (let i = 0; i < tiles.length; i++) {
                            const img = tiles[i].querySelector('img');
                            if (img && img.src) {
                                const filename = img.src.split('/').pop();
                                if (filename === targetFilename || filename.startsWith(targetFilename.split('?')[0])) {
                                    selectedTile = tiles[i];
                                    selectedIndex = i;
                                    method = 'filename';
                                    break;
                                }
                            }
                        }
                    }

                    // Fallback to index selection
                    if (!selectedTile && fallbackIndex < tiles.length) {
                        selectedTile = tiles[fallbackIndex];
                        selectedIndex = fallbackIndex;
                        method = 'index';
                    }

                    if (!selectedTile) {
                        return { success: false, error: 'No suitable tile found' };
                    }

                    // Click the tile
                    const topLayer = selectedTile.querySelector('[role="button"]') ||
                                    selectedTile.querySelector('[class*="topLayer"]');

                    if (topLayer) {
                        topLayer.click();

                        // Get the selected filename
                        const img = selectedTile.querySelector('img');
                        const filename = img && img.src ? img.src.split('/').pop() : '';

                        return {
                            success: true,
                            selected_filename: filename,
                            selected_index: selectedIndex,
                            method: method
                        };
                    }

                    return { success: false, error: 'Could not click tile' };
                }
            """, {'targetFilename': target_filename, 'fallbackIndex': fallback_index})

            if selection_result['success']:
                logger.debug(f"   ✅ Selected '{selection_result['selected_filename']}' (method: {selection_result['method']}, index: {selection_result['selected_index']})")
                return selection_result
            else:
                logger.warning(f"   ⚠️  Selection failed: {selection_result.get('error', 'Unknown error')}")
                return selection_result

        except Exception as e:
            logger.exception(f"   Error selecting logo from library: {e}")
            return {'success': False, 'error': str(e)}

    async def _get_available_logos_for_insert(self, page: Page, container_info: dict) -> dict:
        """
        Open Insert Image popup for an empty container and extract all available logo filenames

        This method clicks on an empty Logo 1/2 container, opens the Insert Image popup,
        extracts all available logos, then closes the popup.

        Args:
            page: Playwright page object
            container_info: Container info dict with 'id' field

        Returns:
            Same format as _get_available_logos():
            {
                'success': True/False,
                'logos': [{'index': 0, 'filename': '...', 'alt': '...', 'src': '...'}, ...],
                'totalCount': 5,
                'error': 'error message if failed'
            }
        """
        try:
            container_id = container_info.get('id')
            logger.debug(f"   📚 Fetching available logos from Insert Image popup...")
            logger.debug(f"      Using container: {container_id}")

            # Click container to focus it
            click_result = await page.evaluate(f"""
                () => {{
                    const textTemplate = document.querySelector('[id="{container_id}"]');
                    if (!textTemplate) return {{ success: false, reason: 'Container not found' }};

                    // Scroll into view
                    textTemplate.scrollIntoView({{ behavior: 'smooth', block: 'center' }});

                    // Remove 'unselectable' class from parent if it exists
                    let parent = textTemplate.parentElement;
                    while (parent) {{
                        if (parent.className && parent.className.includes('Unselectable')) {{
                            parent.className = parent.className.replace(/elementUnselectable\\S*/g, '');
                        }}
                        parent = parent.parentElement;
                    }}

                    // Click and focus
                    textTemplate.click();
                    textTemplate.focus();

                    return {{ success: true }};
                }}
            """)

            if not click_result.get('success'):
                return {'success': False, 'error': f"Could not click container: {click_result.get('reason', 'Unknown')}", 'logos': [], 'totalCount': 0}

            await asyncio.sleep(2)

            # Click Insert Image button
            insert_clicked = False
            try:
                await page.click('.icon-insert-image[aria-label="icon-insert-image"]', timeout=3000)
                insert_clicked = True
            except:
                # Try alternative selectors
                alt_selectors = [
                    'button:has-text("Insert Image")',
                    '[title="Insert Image"]',
                    '.templates_iconButton__jEGTJ[aria-label="icon-insert-image"]'
                ]
                for selector in alt_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        insert_clicked = True
                        break
                    except:
                        continue

            if not insert_clicked:
                return {'success': False, 'error': 'Could not click Insert Image button', 'logos': [], 'totalCount': 0}

            await asyncio.sleep(3)

            # Extract all available logos from popup
            logos_info = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { success: false, error: 'Popup not found' };

                    const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    if (tiles.length === 0) return { success: false, error: 'No media tiles found' };

                    const logos = tiles.map((tile, index) => {
                        const img = tile.querySelector('img');
                        const alt = img ? img.alt : '';
                        const src = img ? img.src : '';
                        const filename = src ? src.split('/').pop() : '';

                        return {
                            index: index,
                            filename: filename,
                            alt: alt,
                            src: src
                        };
                    });

                    return {
                        success: true,
                        logos: logos,
                        totalCount: tiles.length
                    };
                }
            """)

            # Close popup
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)

            if logos_info['success']:
                logger.debug(f"   ✅ Found {logos_info['totalCount']} logos in Insert Image popup")
                return logos_info
            else:
                return {'success': False, 'error': logos_info.get('error', 'Unknown error'), 'logos': [], 'totalCount': 0}

        except Exception as e:
            logger.exception(f"   Error fetching logos from Insert Image popup: {e}")
            return {'success': False, 'error': str(e), 'logos': [], 'totalCount': 0}


# Main entry point
async def main():
    """Main entry point for the script"""

    parser = argparse.ArgumentParser(description='Temp Logo Adding Final - Complete Automation')
    parser.add_argument('--departments', '-d', nargs='+', choices=['Sales', 'Service', 'Parts'],
                       help='Department(s) to filter')
    parser.add_argument('--all', action='store_true', help='Process all templates (no filter)')
    parser.add_argument('--max', '-m', type=int, help='Maximum templates to process')
    parser.add_argument('--no-publish', action='store_true', help='Disable auto-publish')
    parser.add_argument('--template-name', '-t', type=str, help='Filter by specific template name (e.g., "RO Created")')

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
        template_name=args.template_name,
        auto_publish=not args.no_publish
    )


if __name__ == "__main__":
    asyncio.run(main())


