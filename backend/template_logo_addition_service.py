"""
Template Logo Addition Service - INTEGRATED WITH FINAL VERSION
Handles bulk addition of custom logos to Tekion email templates

✅ FEATURES INTEGRATED FROM temp_logo_adding_FINAL.py:
   1. Department filtering (Service & Parts)
   2. API interception & template fetching
   3. 4-layer logo detection (warnings + empty containers + headers + table-based)
   4. Logo replacement (Change Image workflow)
   5. Logo insertion (Insert Image workflow)
   6. Center align & enlarge logos
   7. Auto-publish (2-click workflow)
   8. Sequential processing
   9. Excel reporting with comprehensive stats
   10. Enhanced detection logging
   11. Robust production-grade logging system ✨ NEW
"""

import asyncio
import logging
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import pandas as pd
import json
from playwright.async_api import Page, Browser, BrowserContext, Error as PlaywrightError

# ============================================================================
# ENHANCED LOGGING SYSTEM - FROM FINAL VERSION
# ============================================================================

class EnhancedLogger:
    """
    Enhanced logger with detailed tracking and file output
    FROM FINAL VERSION (Lines 48-209)
    """

    def __init__(self, log_file: str = None):
        """Initialize enhanced logger with file and console output"""

        # Create logs directory if it doesn't exist
        log_dir = Path("backend") / "logs"
        log_dir.mkdir(exist_ok=True, parents=True)

        # Generate log filename with timestamp
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"logo_automation_{timestamp}.log"
        else:
            log_file = log_dir / log_file

        self.log_file = log_file

        # Setup logger
        self.logger = logging.getLogger(f"EnhancedLogger_{id(self)}")
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

    def log_detection_detailed(self, template_name: str, detection_result: Dict):
        """Log detailed detection results to file"""

        entry = {
            'timestamp': datetime.now().isoformat(),
            'template': template_name,
            'warnings_count': detection_result.get('warningsCount', 0),
            'empty_containers_count': detection_result.get('emptyCount', 0),
            'header_containers_count': detection_result.get('headerCount', 0),
            'replace_count': detection_result.get('replaceCount', 0),
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
            for line in detection_result['debug'][:50]:  # First 50 lines
                self.debug(f"  {line}")
            self.debug("-" * 80)

        self.debug(f"SUMMARY:")
        self.debug(f"  Warnings detected: {entry['warnings_count']}")
        self.debug(f"  Logos to replace (table-based): {entry['replace_count']}")
        self.debug(f"  Empty Logo 1/2 containers: {entry['empty_containers_count']}")
        self.debug(f"  Empty header containers: {entry['header_containers_count']}")

        # Detailed container check results
        if 'containerCheckResults' in detection_result:
            self.debug("")
            self.debug("Logo 1/2 Container Check Results:")
            for check in detection_result['containerCheckResults']:
                self.debug(f"  {check['name']:15s} → found={check['found']}, "
                          f"hasImage={check.get('hasImage', False)}, "
                          f"isEmpty={check.get('isEmpty', False)}")

        # Detailed header check results
        if 'headerCheckResults' in detection_result:
            self.debug("")
            self.debug("Header Container Check Results:")
            for check in detection_result['headerCheckResults']:
                self.debug(f"  Position {check['position']} → "
                          f"hasContainer={check['hasContainer']}, "
                          f"hasImage={check['hasImage']}, "
                          f"isEmpty={check['isEmpty']}")

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

    def log_action_detailed(self, action: str, target: str, success: bool, details: str = ""):
        """Log action taken on a logo with detailed info"""

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
            filename = Path("backend") / "logs" / f"detection_log_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.detection_log, f, indent=2)

        self.info(f"📊 Detection log saved: {filename}")

logger = logging.getLogger(__name__)


class TemplateLogoAdditionService:
    """
    Service for adding custom logos to Tekion templates
    Integrated with all features from temp_logo_adding_FINAL.py
    ✨ NOW WITH ROBUST ENHANCED LOGGING
    """

    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.enhanced_loggers: Dict[str, EnhancedLogger] = {}  # Enhanced logger per job
        self.open_tabs: Dict[str, List] = {}  # Track open tabs per job (separate from job dict to avoid JSON serialization issues)
        logger.info("✨ Template Logo Addition Service initialized (FINAL VERSION + ROBUST LOGGING)")

    def create_job(self, job_id: str, base_url: str, max_rows: int = 200,
                   custom_limit: Optional[int] = None, keep_tabs_open: bool = True,
                   logo_media_id: str = None,
                   logo_width: int = 160,
                   departments: Optional[List[str]] = None,
                   auto_publish: bool = True) -> Dict[str, Any]:
        """Create a new logo addition job with all FINAL features + Enhanced Logging

        Args:
            logo_media_id: REQUIRED - Media ID of the store's logo (24-char hex string from Media Library)
        """

        # Validate required logo_media_id
        if not logo_media_id or logo_media_id.strip() == '':
            raise ValueError("logo_media_id is required. Please provide your store's logo Media ID from the Media Library.")

        # Enforce tabs behavior based on auto_publish setting
        # If auto_publish is disabled, force tabs to stay open for manual verification
        if not auto_publish:
            original_keep_tabs = keep_tabs_open
            keep_tabs_open = True
            if not original_keep_tabs:
                logger.info(f"⚠️  Auto-publish disabled: Forcing keep_tabs_open=True (was {original_keep_tabs})")

        # Initialize enhanced logger for this job
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"job_{job_id[:8]}_{timestamp}.log"
        enhanced_logger = EnhancedLogger(log_filename)
        self.enhanced_loggers[job_id] = enhanced_logger

        job = {
            "job_id": job_id,
            "base_url": base_url,
            "max_rows": max_rows,
            "custom_limit": custom_limit,
            "keep_tabs_open": keep_tabs_open,
            "logo_media_id": logo_media_id,
            "logo_width": logo_width,
            "departments": departments or ['Service', 'Parts'],  # NEW: Department filtering
            "auto_publish": auto_publish,  # NEW: Auto-publish feature
            "status": "pending",
            "start_time": datetime.now(),
            "logs": [],
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "published_count": 0,  # NEW: Track published templates
            "centered_count": 0,   # NEW: Track centered logos
            "enlarged_count": 0,   # NEW: Track enlarged logos
            "templates": [],
            "results": [],
            "detection_log": [],  # NEW: Detailed detection results
            "log_file": str(enhanced_logger.log_file)  # NEW: Enhanced log file path
        }

        self.jobs[job_id] = job
        self.open_tabs[job_id] = []  # Initialize tabs tracking for this job

        # Log job creation with enhanced logger
        enhanced_logger.info("🚀 NEW LOGO ADDITION JOB CREATED")
        enhanced_logger.info(f"Job ID: {job_id}")
        enhanced_logger.info(f"Base URL: {base_url}")
        enhanced_logger.info(f"Departments: {', '.join(job['departments'])}")
        enhanced_logger.info(f"Max Templates (API): {max_rows}")
        enhanced_logger.info(f"Custom Limit: {custom_limit if custom_limit else 'None (process all)'}")
        enhanced_logger.info(f"Logo Media ID: {logo_media_id}")
        enhanced_logger.info(f"Logo Width: {logo_width}px")
        enhanced_logger.info("")
        enhanced_logger.info(f"Auto-publish: {'✅ ENABLED (2-click workflow)' if auto_publish else '❌ DISABLED (manual verification required)'}")
        enhanced_logger.info(f"Keep tabs open: {'✅ YES' if keep_tabs_open else '❌ NO (close after processing)'}")
        if not auto_publish:
            enhanced_logger.info("📌 Note: Auto-publish disabled → Tabs FORCED to stay open for manual verification")

        # Also log to standard logger
        logger.info(f"✨ Created logo addition job: {job_id}")
        logger.info(f"   Enhanced log file: {enhanced_logger.log_file}")

        return job

    def add_log(self, job_id: str, message: str, level: str = "info"):
        """Add a log message to the job"""
        if job_id not in self.jobs:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "message": message,
            "level": level
        }

        self.jobs[job_id]["logs"].append(log_entry)

        # Also log to Python logger
        log_message = f"[{job_id[:8]}] {message}"
        if level == "error":
            logger.error(log_message)
        elif level == "warning":
            logger.warning(log_message)
        elif level == "success":
            logger.info(f"✅ {log_message}")
        else:
            logger.info(log_message)

    def log_detection(self, job_id: str, template_name: str, detection_result: Dict):
        """Log detailed detection results (from FINAL version) with Enhanced Logging"""
        if job_id not in self.jobs:
            return

        entry = {
            'timestamp': datetime.now().isoformat(),
            'template': template_name,
            'warnings_count': detection_result.get('warningsCount', 0),
            'empty_containers_count': detection_result.get('emptyCount', 0),
            'header_containers_count': detection_result.get('headerCount', 0),
            'replace_count': detection_result.get('replaceCount', 0),
            'empty_containers': detection_result.get('emptyContainers', []),
            'header_containers': detection_result.get('headerContainers', []),
            'logos_to_replace': detection_result.get('logosToReplace', [])
        }

        self.jobs[job_id]["detection_log"].append(entry)

        # Log summary to UI
        self.add_log(job_id, f"   📊 Detection: {entry['warnings_count']} warnings, "
                     f"{entry['replace_count']} to replace, {entry['empty_containers_count']} empty, "
                     f"{entry['header_containers_count']} headers", "info")

        # Log detailed detection to enhanced logger (file)
        if job_id in self.enhanced_loggers:
            self.enhanced_loggers[job_id].log_detection_detailed(template_name, detection_result)

    def log_action(self, job_id: str, action: str, target: str, success: bool, details: str = ""):
        """Log action taken on a logo (from FINAL version) with Enhanced Logging"""
        if job_id not in self.jobs:
            return

        status = "✅" if success else "❌"
        msg = f"   {status} [{action}] {target}"
        if details:
            msg += f" | {details}"

        level = "success" if success else "warning"
        self.add_log(job_id, msg, level)

        # Log detailed action to enhanced logger (file)
        if job_id in self.enhanced_loggers:
            self.enhanced_loggers[job_id].log_action_detailed(action, target, success, details)
    
    async def run_logo_addition(self, job_id: str, browser: Browser):
        """Main execution flow with FINAL version features integrated"""

        if job_id not in self.jobs:
            logger.error(f"Job {job_id} not found")
            return

        job = self.jobs[job_id]

        try:
            job["status"] = "running"
            self.add_log(job_id, "=" * 60, "info")
            self.add_log(job_id, "🚀 LOGO ADDITION - FINAL VERSION", "success")
            self.add_log(job_id, "=" * 60, "info")
            self.add_log(job_id, f"Departments: {', '.join(job['departments'])}", "info")
            self.add_log(job_id, f"Max Templates: {job['custom_limit'] or 'ALL'}", "info")
            self.add_log(job_id, f"Logo Width: {job['logo_width']}px", "info")
            self.add_log(job_id, f"Auto-Publish: {'✅ ENABLED' if job['auto_publish'] else '❌ DISABLED'}", "info")
            self.add_log(job_id, "=" * 60, "info")

            # Step 1: Connect to existing browser
            self.add_log(job_id, "\n🌐 Connecting to browser...", "info")
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            self.add_log(job_id, "✅ Connected to browser", "success")

            # Step 2: Navigate to templates list (detect existing tab or open new)
            self.add_log(job_id, "\n📍 STEP 1: NAVIGATING TO TEMPLATES LIST", "info")
            templates_url = f"{job['base_url']}/templates/list"

            # Check if templates list tab is already open
            page = None
            tab_was_reused = False
            for existing_page in context.pages:
                if templates_url in existing_page.url or '/templates/list' in existing_page.url:
                    page = existing_page
                    tab_was_reused = True
                    self.add_log(job_id, f"   ✅ Found existing templates list tab", "success")
                    self.add_log(job_id, f"   URL: {existing_page.url}", "info")
                    break

            # If not found, open new tab
            if not page:
                self.add_log(job_id, f"   Opening new tab: {templates_url}", "info")
                page = await context.new_page()
                await page.goto(templates_url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
                self.add_log(job_id, "   ✅ Templates page loaded", "success")
            else:
                # Found existing tab
                self.add_log(job_id, "   ℹ️  Using existing tab (will reload in filter step)", "info")

            # Step 3: Apply department filter and fetch templates
            # NOTE: Reload happens INSIDE _apply_filter_and_capture (AFTER listener is attached)
            self.add_log(job_id, "\n🎯 STEP 2: APPLYING DEPARTMENT FILTER", "info")
            self.add_log(job_id, f"   Filtering: {', '.join(job['departments'])}", "info")
            templates = await self._apply_filter_and_capture(job_id, page, job['departments'], job['base_url'])

            if not templates:
                self.add_log(job_id, "❌ No templates found after filtering", "error")
                job["status"] = "failed"
                # Only close tab if we created it
                if not tab_was_reused:
                    await page.close()
                return

            self.add_log(job_id, f"   ✅ Found {len(templates)} template(s)", "success")
            job["templates"] = templates

            # Apply custom limit if specified
            if job['custom_limit']:
                templates = templates[:job['custom_limit']]
                self.add_log(job_id, f"   📊 Limited to first {job['custom_limit']} templates", "info")

            # Step 4: Process each template
            self.add_log(job_id, "\n" + "=" * 60, "info")
            self.add_log(job_id, "📋 STEP 3: PROCESSING TEMPLATES", "info")
            self.add_log(job_id, "=" * 60, "info")

            for idx, template in enumerate(templates, 1):
                await self._process_template(job_id, context, template, idx, len(templates))

            # Close the filter page only if we created it (don't close if reused)
            if not tab_was_reused:
                await page.close()
                self.add_log(job_id, "\n🔒 Closed templates list tab (created by automation)", "info")
            else:
                self.add_log(job_id, "\n📂 Kept templates list tab open (was pre-existing)", "info")

            # Step 5: Generate report
            self.add_log(job_id, "\n" + "=" * 60, "info")
            self.add_log(job_id, "📊 STEP 4: GENERATING REPORT", "info")
            self.add_log(job_id, "=" * 60, "info")

            await self._generate_excel_report(job_id)

            # Final summary
            duration = (datetime.now() - job['start_time']).total_seconds()
            self.add_log(job_id, "\n" + "=" * 60, "info")
            self.add_log(job_id, "✅ AUTOMATION COMPLETE!", "success")
            self.add_log(job_id, "=" * 60, "info")
            self.add_log(job_id, f"Total Templates: {len(templates)}", "info")
            self.add_log(job_id, f"Processed: {job['processed']}", "info")
            self.add_log(job_id, f"Successful: {job['successful']}", "success")
            self.add_log(job_id, f"Failed: {job['failed']}", "error" if job['failed'] > 0 else "info")
            self.add_log(job_id, f"Published: {job['published_count']}", "info")
            self.add_log(job_id, f"Centered: {job['centered_count']}", "info")
            self.add_log(job_id, f"Enlarged: {job['enlarged_count']}", "info")
            self.add_log(job_id, f"Duration: {duration:.1f}s", "info")
            self.add_log(job_id, "=" * 60, "info")

            # Save enhanced detection log
            if job_id in self.enhanced_loggers:
                enhanced_logger = self.enhanced_loggers[job_id]
                enhanced_logger.save_detection_log()
                enhanced_logger.info("")
                enhanced_logger.info("=" * 100)
                enhanced_logger.info("✅ JOB COMPLETED SUCCESSFULLY")
                enhanced_logger.info("=" * 100)
                enhanced_logger.info(f"Total Templates: {len(templates)}")
                enhanced_logger.info(f"Processed: {job['processed']}")
                enhanced_logger.info(f"Successful: {job['successful']}")
                enhanced_logger.info(f"Failed: {job['failed']}")
                enhanced_logger.info(f"Published: {job['published_count']}")
                enhanced_logger.info(f"Centered: {job['centered_count']}")
                enhanced_logger.info(f"Enlarged: {job['enlarged_count']}")
                enhanced_logger.info(f"Duration: {duration:.1f}s")
                enhanced_logger.info("=" * 100)

            job["status"] = "completed"
            job["end_time"] = datetime.now()

        except Exception as e:
            logger.exception(f"Error in logo addition job {job_id}")
            self.add_log(job_id, f"❌ Fatal error: {str(e)}", "error")

            # Log error to enhanced logger
            if job_id in self.enhanced_loggers:
                enhanced_logger = self.enhanced_loggers[job_id]
                enhanced_logger.error("=" * 100)
                enhanced_logger.error("❌ JOB FAILED")
                enhanced_logger.error("=" * 100)
                enhanced_logger.exception(f"Fatal error: {str(e)}")

            job["status"] = "failed"
            job["error"] = str(e)

    async def _apply_filter_and_capture(self, job_id: str, page: Page,
                                         departments: List[str], base_url: str) -> List[Dict]:
        """
        Apply department filter and capture templates via API
        USES EXACT WORKING LOGIC from test_complete_logo_addition_flow.py
        CRITICAL: Listener attached BEFORE reload, filters by department
        """
        templates = []
        response_received = asyncio.Event()

        # Convert departments to uppercase for comparison (API uses uppercase)
        target_departments = {dept.upper() for dept in departments}

        async def handle_response(response):
            nonlocal templates
            if '/api/templatestore/u/search' in response.url:
                try:
                    data = await response.json()
                    if 'data' in data and 'hits' in data['data']:
                        hits = data['data']['hits']
                        if hits:
                            # Parse request to check which departments were requested
                            request_departments = set()
                            try:
                                import json
                                post_data = response.request.post_data
                                if post_data:
                                    request_data = json.loads(post_data)
                                    if 'filters' in request_data:
                                        for f in request_data['filters']:
                                            if f.get('field') == 'departments':
                                                request_departments = set(f.get('values', []))
                            except:
                                pass

                            # ONLY accept API response if departments match what we want
                            if request_departments == target_departments:
                                templates.clear()  # Clear any old data
                                templates.extend(hits)
                                self.add_log(job_id, f"   📥 Captured {len(hits)} templates from API ({', '.join(departments)})", "info")
                                response_received.set()
                            else:
                                # Log but ignore responses for other departments
                                dept_str = ', '.join(request_departments) if request_departments else 'default'
                                self.add_log(job_id, f"   📥 Ignoring API call for: {dept_str} ({len(hits)} templates)", "debug")
                except:
                    pass

        # CRITICAL: Attach listener BEFORE reload
        page.on('response', handle_response)

        # Reload page to get fresh state (AFTER listener is attached)
        self.add_log(job_id, "   🔄 Reloading page for fresh state...", "info")
        await page.reload(wait_until='domcontentloaded', timeout=15000)
        await asyncio.sleep(3)
        self.add_log(job_id, "      ✅ Page reloaded", "info")

        # Additional wait for filters to be ready (dropdown elements might load async)
        await asyncio.sleep(2)
        self.add_log(job_id, "      ⏳ Waiting for filters to be ready...", "debug")

        # Department mapping (same as working test)
        dept_map = {'Sales': 0, 'Service': 1, 'Parts': 2}

        try:
            # Open dropdown - use JavaScript to find and click the FIRST VISIBLE trigger
            self.add_log(job_id, "   1. Opening department dropdown...", "info")

            # Use JavaScript to click first visible .ant-dropdown-trigger (departments filter)
            dropdown_clicked = await page.evaluate("""
                () => {
                    const triggers = Array.from(document.querySelectorAll('.ant-dropdown-trigger'));
                    console.log(`Found ${triggers.length} dropdown triggers`);

                    // Find first visible trigger (departments should be first in the filters row)
                    for (const trigger of triggers) {
                        const rect = trigger.getBoundingClientRect();
                        const isVisible = rect.width > 0 && rect.height > 0 &&
                                         window.getComputedStyle(trigger).display !== 'none' &&
                                         window.getComputedStyle(trigger).visibility !== 'hidden';

                        if (isVisible) {
                            console.log('Found visible trigger, clicking...');
                            trigger.click();
                            return { clicked: true, index: triggers.indexOf(trigger) };
                        }
                    }

                    // If no visible triggers, try clicking first one anyway
                    if (triggers.length > 0) {
                        console.log('No visible triggers, clicking first one...');
                        triggers[0].click();
                        return { clicked: true, index: 0, fallback: true };
                    }

                    return { clicked: false };
                }
            """)

            if not dropdown_clicked.get('clicked'):
                self.add_log(job_id, "      ❌ No dropdown triggers found!", "error")
                return []

            if dropdown_clicked.get('fallback'):
                self.add_log(job_id, f"      ⚠️  Clicked trigger {dropdown_clicked.get('index')} (fallback - not visible)", "warning")
            else:
                self.add_log(job_id, f"      ✅ Clicked visible trigger {dropdown_clicked.get('index')}", "debug")

            await asyncio.sleep(1)
            self.add_log(job_id, "      ✅ Dropdown opened", "info")

            # Uncheck all first
            self.add_log(job_id, "   2. Unchecking all departments...", "info")
            for dept_name in ['Sales', 'Service', 'Parts']:
                await page.evaluate(f"""
                    () => {{
                        const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map[dept_name]}];
                        if (cb && cb.checked) cb.click();
                    }}
                """)
                await asyncio.sleep(0.3)
            self.add_log(job_id, "      ✅ All unchecked", "info")

            # Check selected departments
            self.add_log(job_id, f"   3. Checking: {', '.join(departments)}", "info")
            for dept_name in departments:
                if dept_name in dept_map:
                    await page.evaluate(f"""
                        () => {{
                            const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map[dept_name]}];
                            if (cb && !cb.checked) cb.click();
                        }}
                    """)
                    await asyncio.sleep(0.3)
                    self.add_log(job_id, f"      ✅ {dept_name} checked", "info")

            # Close dropdown
            self.add_log(job_id, "   4. Closing dropdown...", "info")
            await page.keyboard.press('Escape')
            await asyncio.sleep(2)
            self.add_log(job_id, "      ✅ Dropdown closed", "info")

            # Wait for API response
            self.add_log(job_id, "   5. Waiting for API response...", "info")
            try:
                await asyncio.wait_for(response_received.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                self.add_log(job_id, "   ⚠️  API response timeout", "warning")

            page.remove_listener('response', handle_response)

            self.add_log(job_id, f"   ✅ Filter applied: {len(templates)} templates captured", "success")

        except Exception as e:
            self.add_log(job_id, f"   ❌ Filter application failed: {e}", "error")
            page.remove_listener('response', handle_response)

        return templates

    async def _process_template(self, job_id: str, context, template: Dict,
                                idx: int, total: int):
        """
        Process single template with FULL FINAL VERSION integration
        Uses 4-layer detection and all manipulation methods
        """

        job = self.jobs[job_id]
        template_id = template.get('templateId') or template.get('id')
        template_name = template.get('name', 'Unknown')

        self.add_log(job_id, "", "info")
        self.add_log(job_id, "=" * 80, "info")
        self.add_log(job_id, f"📄 TEMPLATE [{idx}/{total}]: {template_name}", "info")
        self.add_log(job_id, f"   ID: {template_id}", "info")

        result = {
            "template_id": template_id,
            "template_name": template_name,
            "status": "pending",
            "logos_processed": 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            # STEP 1: Open template editor
            edit_url = f"{job['base_url']}/templates/edit/{template_id}"
            self.add_log(job_id, f"   🌐 Opening: {edit_url}", "info")

            page = await context.new_page()
            await page.goto(edit_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(5)

            # STEP 2: Detect all logos (4-layer detection)
            self.add_log(job_id, "   🔍 Running 4-layer logo detection...", "info")
            detection_result = await self._detect_logos(page)

            # Log detection results
            self.log_detection(job_id, template_name, detection_result)

            warnings_count = detection_result['warningsCount']
            empty_count = detection_result['emptyCount']
            header_count = detection_result.get('headerCount', 0)
            replace_count = detection_result.get('replaceCount', 0)

            if warnings_count == 0 and empty_count == 0 and header_count == 0 and replace_count == 0:
                self.add_log(job_id, "   ℹ️  No logos need processing - skipping", "info")
                self.add_log(job_id, "   📌 Tab kept open for inspection", "info")
                result["status"] = "skipped"
                result["reason"] = "No logos to process"
                job["processed"] += 1
                job["results"].append(result)
                # Don't close the tab - keep it open for inspection
                # Add to open_tabs list to prevent garbage collection
                self.open_tabs[job_id].append(page)
                # await page.close()
                return

            logos_processed = 0

            # STEP 3: Replace logos WITH warnings (wrong logos)
            if warnings_count > 0:
                self.add_log(job_id, f"\n   🔄 Replacing {warnings_count} logo(s) with warnings...", "info")
                for i in range(1, warnings_count + 1):
                    self.add_log(job_id, f"      Processing warning logo #{i}...", "info")
                    if await self._replace_logo(page, i, job['logo_media_id']):
                        self.log_action(job_id, "REPLACE", f"Warning logo #{i}", True)
                        await asyncio.sleep(2)

                        # Center the logo
                        if await self._center_logo(page, i):
                            self.log_action(job_id, "CENTER", f"Logo #{i}", True)
                            job['centered_count'] += 1

                        # Enlarge the logo
                        if await self._enlarge_logo(page, i, job['logo_media_id'], job['logo_width']):
                            self.log_action(job_id, "ENLARGE", f"Logo #{i}", True, f"to {job['logo_width']}px")
                            job['enlarged_count'] += 1

                        logos_processed += 1
                    else:
                        self.log_action(job_id, "REPLACE", f"Warning logo #{i}", False)

            # STEP 4: Replace logos WITHOUT warnings (table-based detection)
            if replace_count > 0:
                self.add_log(job_id, f"\n   🔄 Replacing {replace_count} logo(s) (table-based)...", "info")
                for i in range(1, replace_count + 1):
                    self.add_log(job_id, f"      Processing table logo #{i}...", "info")
                    if await self._replace_logo_without_warning(page, i, job['logo_media_id']):
                        self.log_action(job_id, "REPLACE_TABLE", f"Logo #{i}", True)
                        logos_processed += 1
                    else:
                        self.log_action(job_id, "REPLACE_TABLE", f"Logo #{i}", False)

            # STEP 5: Insert into empty containers
            if empty_count > 0:
                self.add_log(job_id, f"\n   ➕ Inserting into {empty_count} empty container(s)...", "info")
                for container_info in detection_result['emptyContainers']:
                    self.add_log(job_id, f"      Inserting into {container_info['name']}...", "info")
                    if await self._insert_logo_to_container(page, container_info, job['logo_media_id']):
                        self.log_action(job_id, "INSERT", container_info['name'], True)
                        logos_processed += 1
                    else:
                        self.log_action(job_id, "INSERT", container_info['name'], False)

            # STEP 5.5: Insert into header containers
            header_count = detection_result.get('headerCount', 0)
            if header_count > 0:
                self.add_log(job_id, f"\n   📋 Inserting into {header_count} header container(s)...", "info")
                for header_info in detection_result.get('headerContainers', []):
                    self.add_log(job_id, f"      Inserting into {header_info['name']}...", "info")
                    if await self._insert_logo_to_header(page, header_info, job['logo_media_id']):
                        self.log_action(job_id, "INSERT_HEADER", header_info['name'], True)
                        logos_processed += 1
                    else:
                        self.log_action(job_id, "INSERT_HEADER", header_info['name'], False)

            # STEP 6: Auto-publish if enabled
            published = False
            if logos_processed > 0 and job['auto_publish']:
                self.add_log(job_id, "\n   📤 Auto-publishing (2-click workflow)...", "info")
                if await self._publish_template(job_id, page, template_name):
                    published = True
                    job['published_count'] += 1
                    self.add_log(job_id, "   ✅ Template published!", "success")
                else:
                    self.add_log(job_id, "   ⚠️  Publish failed", "warning")
            elif logos_processed > 0 and not job['auto_publish']:
                self.add_log(job_id, "\n   ⏸️  Auto-publish DISABLED - Template NOT published", "warning")
                self.add_log(job_id, "   📌 Tab kept open for manual verification and publishing", "info")
            elif logos_processed == 0:
                self.add_log(job_id, "\n   ⏭️  No logos processed - skipping publish", "info")

            # Result summary
            if logos_processed > 0:
                result["status"] = "success"
                result["logos_processed"] = logos_processed
                result["published"] = published
                job["successful"] += 1
                self.add_log(job_id, f"   ✅ Successfully processed {logos_processed} logo(s)", "success")
            else:
                result["status"] = "partial"
                result["logos_processed"] = 0
                job["failed"] += 1
                self.add_log(job_id, "   ⚠️  No logos successfully processed", "warning")

            # Keep tab open or close based on settings
            if not job['keep_tabs_open']:
                await page.close()
                self.add_log(job_id, "   🔒 Tab closed (keep_tabs_open=False)", "info")
            else:
                # Add to open_tabs list to prevent garbage collection
                self.open_tabs[job_id].append(page)
                if job['auto_publish']:
                    self.add_log(job_id, "   📂 Tab kept open for verification (user preference)", "info")
                else:
                    self.add_log(job_id, "   📌 Tab kept open for MANUAL verification and publishing", "warning")

        except Exception as e:
            logger.exception(f"Error processing template {template_id}")
            self.add_log(job_id, f"   ❌ Error: {str(e)}", "error")
            result["status"] = "error"
            result["error"] = str(e)
            job["failed"] += 1

        job["processed"] += 1
        job["results"].append(result)

    # ============================================================================
    # FINAL VERSION - 4-LAYER LOGO DETECTION
    # ============================================================================

    async def _detect_logos(self, page: Page) -> Dict:
        """
        4-LAYER LOGO DETECTION - DYNAMIC VERSION (Fixed duplicate variable)
        Detects: warnings, empty Logo 1/2 containers, headers, table-based fallback
        Returns comprehensive detection results
        """

        return await page.evaluate("""
            () => {
                const debug = [];

                // LAYER 1: Find logos with warnings (wrong logos - need replacement)
                debug.push('=== LAYER 1: WARNING DETECTION ===');

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

                warnings.forEach((icon, idx) => {
                    const sortableItem = icon.closest('[class*="SortableItem"]');
                    if (sortableItem) {
                        sortableItem.setAttribute('data-logo-to-inspect', `warning-logo-${idx + 1}`);
                        debug.push(`  Warning ${idx + 1}: Marked sortableItem`);
                    }
                });

                // LAYER 2: DYNAMIC Logo 1/2 container detection (NEW - finds containers in any template)
                debug.push('\\n=== LAYER 2: DYNAMIC LOGO CONTAINER DETECTION ===');

                const emptyContainers = [];
                const containerCheckResults = [];

                // Strategy 1: Find logo containers in table structure
                debug.push('Strategy 1: Searching for logo tables...');
                const logoTableElements = Array.from(document.querySelectorAll('table'));
                let logoContainersFound = 0;

                logoTableElements.forEach((table, tableIdx) => {
                    const firstRow = table.querySelector('tr');
                    if (!firstRow) return;

                    const cells = Array.from(firstRow.querySelectorAll('td'));

                    // Logo tables have 4 OR 5 cells (some templates have 5)
                    // Structure: [empty] [empty] [LOGO] [empty] [empty] OR [empty] [LOGO] [empty] [EXTRA]
                    if (cells.length === 4 || cells.length === 5) {
                        const positions = cells.length === 4
                            ? ['LEFT', 'CENTER', 'RIGHT', 'EXTRA']
                            : ['FAR_LEFT', 'LEFT', 'CENTER', 'RIGHT', 'FAR_RIGHT'];

                        cells.forEach((cell, cellIdx) => {
                            // Skip the last column (always EXTRA or FAR_RIGHT)
                            if (cellIdx >= cells.length - 1) return;

                            const textTemplate = cell.querySelector('.TEXT_TEMPLATE[contenteditable="true"]');

                            if (textTemplate) {
                                const hasImage = textTemplate.querySelector('img') !== null;
                                const htmlLength = textTemplate.innerHTML.trim().length;
                                const isEmpty = !hasImage && htmlLength < 300;

                                const containerName = `Logo ${tableIdx + 1} ${positions[cellIdx]}`;

                                containerCheckResults.push({
                                    name: containerName,
                                    id: textTemplate.id,
                                    found: true,
                                    hasImage: hasImage,
                                    isEmpty: isEmpty,
                                    tableIndex: tableIdx,
                                    cellIndex: cellIdx
                                });

                                if (isEmpty) {
                                    logoContainersFound++;
                                    textTemplate.setAttribute('data-empty-container', `empty-${logoContainersFound}`);
                                    emptyContainers.push({
                                        index: logoContainersFound,
                                        id: textTemplate.id,
                                        name: containerName,
                                        type: 'logo_container',
                                        position: positions[cellIdx]
                                    });
                                    debug.push(`  Found empty: ${containerName} (ID: ${textTemplate.id.substring(0, 8)}...)`);
                                }
                            }
                        });
                    }
                });

                debug.push(`Strategy 1 result: Found ${logoContainersFound} empty logo containers in tables`);

                // Strategy 2: Fallback - Find all hidden TEXT_TEMPLATE elements (likely logo spots)
                if (logoContainersFound === 0) {
                    debug.push('Strategy 2: Searching for hidden TEXT_TEMPLATE elements...');

                    const allTextTemplates = Array.from(document.querySelectorAll('.TEXT_TEMPLATE[contenteditable="true"]'));

                    allTextTemplates.forEach((el, idx) => {
                        const rect = el.getBoundingClientRect();
                        const isHidden = rect.width === 0 || rect.height < 20;
                        const hasImage = el.querySelector('img') !== null;
                        const htmlLength = el.innerHTML.trim().length;
                        const isEmpty = !hasImage && htmlLength < 300;

                        if (isHidden && isEmpty) {
                            logoContainersFound++;
                            el.setAttribute('data-empty-container', `empty-${logoContainersFound}`);
                            emptyContainers.push({
                                index: logoContainersFound,
                                id: el.id,
                                name: `Hidden Container ${logoContainersFound}`,
                                type: 'hidden_template',
                                position: 'UNKNOWN'
                            });
                            debug.push(`  Found hidden empty container: ${el.id.substring(0, 8)}...`);
                        }
                    });

                    debug.push(`Strategy 2 result: Found ${logoContainersFound} hidden empty containers`);
                }

                // LAYER 3: Table-based Logo detection (fallback)
                debug.push('\\n=== LAYER 3: TABLE-BASED LOGO DETECTION ===');
                const allTables = Array.from(document.querySelectorAll('table'));
                const logoTables = [];
                const logosToReplace = [];

                allTables.forEach((table, tableIdx) => {
                    const firstRow = table.querySelector('tr');
                    if (!firstRow) return;

                    const cells = Array.from(firstRow.querySelectorAll('td'));

                    if (cells.length === 4) {
                        const tableInfo = { tableIndex: tableIdx, positions: [] };

                        cells.forEach((cell, cellIdx) => {
                            const imageComponent = cell.querySelector('.templates_Image_imageComponent__tqwK7j9G7t');
                            // Check for warning icons with multiple selectors
                            const hasWarning = cell.querySelector('.templates_errorWarningIconsWithPopover_warningIcon__fT9Rzb2vrs, .icon-alert1, [class*="errorWarningIconsWithPopover_warningIcon"], .templates_Image_warningIcon__hCZHMuhEmb') !== null;
                            const textTemplate = cell.querySelector('.TEXT_TEMPLATE[contenteditable="true"]');
                            const hasImage = imageComponent !== null;
                            const isEmpty = !hasImage && textTemplate !== null;

                            const alignment = cellIdx === 0 ? 'LEFT' :
                                            cellIdx === 1 ? 'CENTER' :
                                            cellIdx === 2 ? 'RIGHT' : 'EXTRA';

                            tableInfo.positions.push({
                                cellIndex: cellIdx,
                                alignment: alignment,
                                hasImage: hasImage,
                                hasWarning: hasWarning,
                                isEmpty: isEmpty,
                                imageComponent: imageComponent
                            });
                        });

                        const relevantPositions = tableInfo.positions.slice(0, 3);
                        const hasRelevantContent = relevantPositions.some(p => p.hasImage || p.isEmpty);

                        if (hasRelevantContent) {
                            logoTables.push(tableInfo);

                            // Mark logos WITH warnings for replacement
                            tableInfo.positions.forEach((pos) => {
                                if (pos.hasImage && pos.hasWarning && pos.imageComponent) {
                                    const replaceIdx = logosToReplace.length + 1;
                                    pos.imageComponent.setAttribute('data-logo-to-replace', `replace-logo-${replaceIdx}`);
                                    logosToReplace.push({
                                        index: replaceIdx,
                                        name: `Logo ${logoTables.length} ${pos.alignment}`,
                                        type: 'logo_with_warning_table_based'
                                    });
                                }
                            });
                        }
                    }
                });

                // LAYER 4: Header container detection
                debug.push('\\n=== LAYER 4: HEADER CONTAINER DETECTION ===');
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
                    logosToReplace: logosToReplace,
                    replaceCount: logosToReplace.length,
                    debug: debug
                };
            }
        """)

    # ============================================================================
    # FINAL VERSION - LOGO REPLACEMENT METHODS
    # ============================================================================

    async def _replace_logo(self, page: Page, logo_idx: int, logo_media_id: str) -> bool:
        """
        Replace logo with warning icon using Change Image workflow
        FROM FINAL (Lines 1108-1211) - EXACT SYNC
        """
        try:
            # Hover to reveal toolbar
            container = await page.query_selector(f'[data-logo-to-inspect="warning-logo-{logo_idx}"]')
            if not container:
                return False

            await container.hover(force=True)
            await asyncio.sleep(3)

            # Check if popup already open (CRITICAL - from FINAL)
            popup_open = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    return popup && popup.getBoundingClientRect().width > 0;
                }
            """)

            if not popup_open:
                # Click Change Image icon (only if popup not already open)
                change_clicked = await page.evaluate(f"""
                    () => {{
                        const container = document.querySelector('[data-logo-to-inspect="warning-logo-{logo_idx}"]');
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

            # Verify popup closed (CRITICAL - from FINAL)
            popup_closed = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    return !popup || popup.getBoundingClientRect().width === 0;
                }
            """)

            return popup_closed

        except Exception as e:
            logger.exception(f"Error replacing logo: {e}")
            return False

    async def _replace_logo_without_warning(self, page: Page, logo_idx: int, logo_media_id: str) -> bool:
        """
        Replace logo WITHOUT warning (table-based detection) using Change Image workflow
        FROM FINAL (Lines 1213-1340)
        """
        try:
            logger.debug(f"[REPLACE_TABLE] Looking for replace-logo-{logo_idx}")
            container = await page.query_selector(f'[data-logo-to-replace="replace-logo-{logo_idx}"]')
            if not container:
                logger.error(f"[REPLACE_TABLE] Container not found: replace-logo-{logo_idx}")
                return False

            img_element = await container.query_selector('img')
            if not img_element:
                logger.error(f"[REPLACE_TABLE] No img element in container")
                return False

            logger.debug(f"[REPLACE_TABLE] Hovering and clicking image...")
            # Hover and click image
            await img_element.hover(force=True)
            await asyncio.sleep(1.5)
            await img_element.click(force=True)
            await asyncio.sleep(2)

            # Try clicking 4th toolbar icon (replace icon)
            logger.debug(f"[REPLACE_TABLE] Clicking toolbar icon...")
            img_box = await img_element.bounding_box()
            if img_box:
                toolbar_icon_x = img_box['x'] + 140
                toolbar_icon_y = img_box['y'] - 30
                logger.debug(f"[REPLACE_TABLE] Toolbar position: ({toolbar_icon_x}, {toolbar_icon_y})")
                await page.mouse.click(toolbar_icon_x, toolbar_icon_y)
                await asyncio.sleep(2)
            else:
                logger.error(f"[REPLACE_TABLE] Could not get image bounding box")
                return False

            # Select Tilton.png (tile #1)
            logger.debug(f"[REPLACE_TABLE] Looking for media library popup...")
            selection = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) {
                        const allDialogs = document.querySelectorAll('[role="dialog"]');
                        const allModals = document.querySelectorAll('.ant-modal');
                        return {
                            success: false,
                            popup: false,
                            dialogCount: allDialogs.length,
                            modalCount: allModals.length
                        };
                    }

                    const tiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    if (tiles.length > 0) {
                        const topLayer = tiles[0].querySelector('[role="button"]') ||
                                        tiles[0].querySelector('[class*="topLayer"]');
                        if (topLayer) {
                            topLayer.click();
                            return { success: true, popup: true, tiles: tiles.length };
                        }
                        return { success: false, popup: true, tiles: tiles.length, noTopLayer: true };
                    }
                    return { success: false, popup: true, tiles: 0 };
                }
            """)

            if not selection.get('popup'):
                logger.error(f"[REPLACE_TABLE] Media library popup not found!")
                logger.debug(f"[REPLACE_TABLE] Dialogs: {selection.get('dialogCount', 0)}, Modals: {selection.get('modalCount', 0)}")
                return False

            if not selection['success']:
                logger.error(f"[REPLACE_TABLE] Failed to select tile")
                logger.debug(f"[REPLACE_TABLE] Tiles: {selection.get('tiles', 0)}, NoTopLayer: {selection.get('noTopLayer', False)}")
                return False

            logger.debug(f"[REPLACE_TABLE] Logo tile selected ({selection.get('tiles', 0)} tiles)")
            await asyncio.sleep(1.5)

            # Click INSERT
            logger.debug(f"[REPLACE_TABLE] Looking for Insert button...")
            insert_result = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { clicked: false, popup: false };

                    const buttons = Array.from(popup.querySelectorAll('button'));
                    const insertBtn = buttons.find(b => b.textContent.trim().toLowerCase().includes('insert'));

                    if (insertBtn && !insertBtn.disabled) {
                        insertBtn.click();
                        return { clicked: true, popup: true };
                    }

                    const allButtons = buttons.map(b => b.textContent.trim());
                    return { clicked: false, popup: true, buttons: allButtons };
                }
            """)

            if not insert_result['clicked']:
                logger.error(f"[REPLACE_TABLE] Failed to click Insert button")
                logger.debug(f"[REPLACE_TABLE] Buttons: {insert_result.get('buttons', [])}")
                return False

            logger.debug(f"[REPLACE_TABLE] Insert button clicked")
            return True

        except Exception as e:
            logger.error(f"[REPLACE_TABLE] Unexpected error: {e}")
            import traceback
            logger.error(f"[REPLACE_TABLE] Traceback: {traceback.format_exc()}")
            return False

    # ============================================================================
    # FINAL VERSION - LOGO MANIPULATION METHODS
    # ============================================================================

    async def _center_logo(self, page: Page, logo_idx: int) -> bool:
        """
        Center align a logo - FROM FINAL (Lines 1383-1417)
        """
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
        """
        Detect and enlarge logo to target width - FROM FINAL (Lines 1419-1502)
        """
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

    async def _center_logo_without_warning(self, page: Page, logo_idx: int) -> bool:
        """
        Center align a logo that was replaced (without warning icon)
        FROM FINAL (Lines 1361-1370) - CRITICAL MISSING METHOD
        """
        try:
            # For now, return True as placeholder
            # TODO: Implement center alignment logic for logos without warning icons
            logger.debug(f"Center alignment for logo {logo_idx} (no warning) - not yet implemented")
            return False
        except Exception as e:
            logger.error(f"Error in _center_logo_without_warning: {e}")
            return False

    async def _enlarge_logo_without_warning(self, page: Page, logo_idx: int, logo_media_id: str, logo_width: str) -> bool:
        """
        Enlarge a logo that was replaced (without warning icon)
        FROM FINAL (Lines 1372-1381) - CRITICAL MISSING METHOD
        """
        try:
            # For now, return True as placeholder
            # TODO: Implement enlarge logic for logos without warning icons
            logger.debug(f"Enlarge logo {logo_idx} to {logo_width} (no warning) - not yet implemented")
            return False
        except Exception as e:
            logger.error(f"Error in _enlarge_logo_without_warning: {e}")
            return False

    async def _insert_logo_to_container(self, page: Page, container_info: Dict, logo_media_id: str) -> bool:
        """
        Insert logo into empty Logo 1/2 container - FROM FINAL (Lines 1504-1590)
        """
        try:
            # Focus container
            target_selector = f'div.TEXT_TEMPLATE[id="{container_info["id"]}"][contenteditable="true"]'

            try:
                logger.debug(f"[INSERT] Waiting for container: {target_selector}")
                # Try to check if element exists first using evaluate
                exists = await page.evaluate(f"""
                    document.querySelector('{target_selector.replace("'", "\\'")}') !== null
                """)

                if not exists:
                    logger.error(f"[INSERT] Container not found in DOM: {target_selector}")
                    return False

                logger.debug(f"[INSERT] Container found in DOM")

                # FIXED: Use JavaScript click FIRST (works reliably even for hidden elements)
                # Force click fails for width=0 elements ("Element is outside of the viewport")
                try:
                    logger.debug(f"[INSERT] Using JavaScript click (works for hidden containers)...")
                    await page.evaluate(f"""
                        const el = document.querySelector('{target_selector.replace("'", "\\'")}');
                        el.click();
                        el.focus();
                    """)
                    logger.debug(f"[INSERT] JavaScript click + focus executed successfully")
                except Exception as click_err:
                    logger.error(f"[INSERT] JavaScript click failed: {click_err}")
                    # Fallback to force click
                    logger.debug(f"[INSERT] Trying force click as fallback...")
                    try:
                        await page.click(target_selector, force=True, timeout=5000)
                        logger.debug(f"[INSERT] Force click successful")
                    except Exception as force_err:
                        logger.error(f"[INSERT] Force click also failed: {force_err}")
                        return False

                # Wait for toolbar to appear
                logger.debug(f"[INSERT] Waiting 3 seconds for editor toolbar to appear...")
                await asyncio.sleep(3.0)
            except Exception as e:
                logger.error(f"[INSERT] Failed to click container: {e}")
                logger.debug(f"[INSERT] Selector: {target_selector}")
                return False

            # Click Insert Image button with comprehensive selector strategy
            try:
                logger.debug(f"[INSERT] Searching for Insert Image button with multiple strategies...")

                # FIXED: Find the editor toolbar button (bottom of page), not the catalog button
                btn_result = await page.evaluate("""
                    () => {
                        // Multiple selector strategies
                        const selectors = [
                            '.icon-insert-image[aria-label="icon-insert-image"]',
                            '.icon-insert-image',
                            '[class*="icon-insert-image"]',
                            '[class*="insert-image"]',
                            '[aria-label*="insert" i][aria-label*="image" i]',
                            '[aria-label*="insert-image" i]',
                            'button[aria-label*="insert" i]',
                            'span[class*="icon"][class*="insert"]',
                            'i[class*="icon-insert"]',
                            '[data-action="insert-image"]',
                            '[title*="Insert Image" i]',
                            '[title*="Insert" i][title*="Image" i]'
                        ];

                        // Find ALL matching buttons, then choose the one in editor toolbar (bottom area)
                        let allFoundButtons = [];

                        for (const selector of selectors) {
                            const buttons = Array.from(document.querySelectorAll(selector));
                            buttons.forEach(btn => {
                                const rect = btn.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    allFoundButtons.push({
                                        element: btn,
                                        selector: selector,
                                        rect: rect,
                                        top: rect.top,
                                        left: rect.left
                                    });
                                }
                            });
                        }

                        if (allFoundButtons.length === 0) {
                            // Get diagnostic info
                            const allToolbarBtns = Array.from(document.querySelectorAll('[aria-label*="icon"], [class*="icon-"]'));
                            const toolbarLabels = allToolbarBtns.map(b => ({
                                label: b.getAttribute('aria-label'),
                                class: b.className,
                                visible: b.getBoundingClientRect().width > 0
                            }));

                            return {
                                exists: false,
                                toolbarButtons: toolbarLabels.slice(0, 30),
                                triedSelectors: selectors
                            };
                        }

                        // CRITICAL FIX: Choose button closest to BOTTOM of page (editor toolbar)
                        // Editor toolbar typically appears at bottom (high Y coordinate)
                        // Catalog toolbar is at top (low Y coordinate)
                        allFoundButtons.sort((a, b) => b.top - a.top);

                        const chosenButton = allFoundButtons[0];

                        return {
                            exists: true,
                            selector: chosenButton.selector,
                            visible: true,
                            rect: chosenButton.rect,
                            totalFound: allFoundButtons.length,
                            allPositions: allFoundButtons.map(b => ({ top: b.top, left: b.left }))
                        };
                    }
                """)

                if not btn_result.get('exists'):
                    logger.error(f"[INSERT] Insert Image button NOT FOUND after trying {len(btn_result.get('triedSelectors', []))} selectors!")
                    logger.error(f"[INSERT] Available toolbar buttons ({len(btn_result.get('toolbarButtons', []))} found):")
                    for idx, btn in enumerate(btn_result.get('toolbarButtons', [])[:15], 1):
                        logger.error(f"  {idx}. {btn}")
                    return False

                logger.debug(f"[INSERT] ✅ Found {btn_result.get('totalFound', 1)} Insert Image button(s)")
                logger.debug(f"[INSERT] Chose button at: {btn_result.get('rect')}")
                logger.debug(f"[INSERT] All button positions: {btn_result.get('allPositions', [])}")
                logger.debug(f"[INSERT] Using selector: {btn_result.get('selector')}")

                # Click using the successful selector
                successful_selector = btn_result.get('selector')
                await page.click(successful_selector, timeout=5000)
                await asyncio.sleep(2.5)
                logger.debug(f"[INSERT] Insert Image button clicked successfully")
            except Exception as e:
                logger.error(f"[INSERT] Failed to click Insert Image button: {e}")
                return False

            # Select logo from media library
            logger.debug(f"[INSERT] Looking for media library popup...")
            selection = await page.evaluate("""
                async () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) {
                        const allDialogs = document.querySelectorAll('[role="dialog"]');
                        const allModals = document.querySelectorAll('.ant-modal');
                        return {
                            clicked: false,
                            popup: false,
                            dialogCount: allDialogs.length,
                            modalCount: allModals.length
                        };
                    }

                    const allTiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    if (allTiles.length === 0) {
                        const popupHTML = popup.innerHTML.substring(0, 500);
                        return {
                            clicked: false,
                            popup: true,
                            tiles: 0,
                            popupPreview: popupHTML
                        };
                    }

                    const tile = allTiles[0];
                    const topLayer = tile.querySelector('[class*="topLayer"]') ||
                                    tile.querySelector('[role="button"]');

                    if (topLayer) {
                        topLayer.click();
                        return { clicked: true, popup: true, tiles: allTiles.length };
                    }
                    return { clicked: false, popup: true, tiles: allTiles.length };
                }
            """)

            if not selection.get('popup'):
                logger.error(f"[INSERT] Media library popup not found!")
                logger.debug(f"[INSERT] Dialogs: {selection.get('dialogCount', 0)}, Modals: {selection.get('modalCount', 0)}")
                return False

            if not selection['clicked']:
                logger.error(f"[INSERT] Failed to select tile from media library")
                logger.debug(f"[INSERT] Tiles found: {selection.get('tiles', 0)}")
                if 'popupPreview' in selection:
                    logger.debug(f"[INSERT] Popup HTML: {selection['popupPreview'][:200]}...")
                return False

            logger.debug(f"[INSERT] Logo tile selected ({selection.get('tiles', 0)} tiles)")
            await asyncio.sleep(2)

            # Click INSERT
            logger.debug(f"[INSERT] Looking for Insert button...")
            insert_result = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { clicked: false, popup: false };

                    const buttons = Array.from(popup.querySelectorAll('button'));
                    const insertBtn = buttons.find(b => b.textContent.trim().toLowerCase().includes('insert'));

                    if (insertBtn && !insertBtn.disabled) {
                        insertBtn.click();
                        return { clicked: true, popup: true };
                    }

                    const allButtons = buttons.map(b => b.textContent.trim());
                    return { clicked: false, popup: true, buttons: allButtons };
                }
            """)

            if not insert_result['clicked']:
                logger.error(f"[INSERT] Failed to click Insert button")
                logger.debug(f"[INSERT] Buttons found: {insert_result.get('buttons', [])}")
                return False

            logger.debug(f"[INSERT] Insert button clicked")
            await asyncio.sleep(2)
            return True

        except Exception as e:
            logger.error(f"[INSERT] Unexpected error: {e}")
            import traceback
            logger.error(f"[INSERT] Traceback: {traceback.format_exc()}")
            return False

    async def _insert_logo_to_header(self, page: Page, header_info: Dict, logo_media_id: str) -> bool:
        """
        Insert logo into empty header container - FROM FINAL (Lines 1592-1691)
        """
        try:
            # Click the header container by position
            logger.debug(f"[INSERT_HEADER] Looking for header container at position {header_info['position']}")
            clicked = await page.evaluate(f"""
                () => {{
                    const headerContainer = document.querySelector('[data-header-container="header-{header_info['position']}"]');
                    if (!headerContainer) {{
                        // Debug: what header containers exist?
                        const allHeaders = Array.from(document.querySelectorAll('[data-header-container]'));
                        return {{
                            success: false,
                            found: false,
                            availableHeaders: allHeaders.map(h => h.getAttribute('data-header-container'))
                        }};
                    }}

                    const textTemplate = headerContainer.querySelector('.TEXT_TEMPLATE') ||
                                        headerContainer.querySelector('[contenteditable="true"]');

                    if (textTemplate) {{
                        textTemplate.click();
                        textTemplate.focus();
                        return {{ success: true, found: true }};
                    }}
                    return {{ success: false, found: true, noEditableElement: true }};
                }}
            """)

            if not clicked.get('found'):
                logger.error(f"[INSERT_HEADER] Header container not found at position {header_info['position']}")
                logger.debug(f"[INSERT_HEADER] Available headers: {clicked.get('availableHeaders', [])}")
                return False

            if not clicked['success']:
                logger.error(f"[INSERT_HEADER] Header found but no editable element")
                return False

            logger.debug(f"[INSERT_HEADER] Header container clicked")
            await asyncio.sleep(1.5)

            # Click Insert Image
            try:
                insert_btn_selector = '.icon-insert-image[aria-label="icon-insert-image"]'
                logger.debug(f"[INSERT_HEADER] Looking for Insert Image button: {insert_btn_selector}")

                btn_check = await page.evaluate("""
                    () => {
                        const btn = document.querySelector('.icon-insert-image[aria-label="icon-insert-image"]');
                        if (!btn) {
                            const allInsertBtns = Array.from(document.querySelectorAll('[aria-label*="insert"]'));
                            return {
                                exists: false,
                                alternatives: allInsertBtns.map(b => b.getAttribute('aria-label'))
                            };
                        }
                        return { exists: true };
                    }
                """)

                if not btn_check.get('exists'):
                    logger.error(f"[INSERT_HEADER] Insert Image button not found")
                    logger.debug(f"[INSERT_HEADER] Alternatives: {btn_check.get('alternatives', [])}")
                    return False

                await page.click(insert_btn_selector, timeout=5000)
                await asyncio.sleep(2.5)
                logger.debug(f"[INSERT_HEADER] Insert Image button clicked")
            except Exception as e:
                logger.error(f"[INSERT_HEADER] Failed to click Insert Image: {e}")
                return False

            # Select logo from media library
            logger.debug(f"[INSERT_HEADER] Looking for media library popup...")
            selection = await page.evaluate("""
                async () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) {
                        const allDialogs = document.querySelectorAll('[role="dialog"]');
                        const allModals = document.querySelectorAll('.ant-modal');
                        return {
                            clicked: false,
                            popup: false,
                            dialogCount: allDialogs.length,
                            modalCount: allModals.length
                        };
                    }

                    const allTiles = Array.from(popup.querySelectorAll('[class*="mediaTile"]'));
                    if (allTiles.length === 0) {
                        return {
                            clicked: false,
                            popup: true,
                            tiles: 0
                        };
                    }

                    const tile = allTiles[0];
                    const topLayer = tile.querySelector('[class*="topLayer"]') ||
                                    tile.querySelector('[role="button"]');

                    if (topLayer) {
                        topLayer.click();
                        return { clicked: true, popup: true, tiles: allTiles.length };
                    }
                    return { clicked: false, popup: true, tiles: allTiles.length };
                }
            """)

            if not selection.get('popup'):
                logger.error(f"[INSERT_HEADER] Media library popup not found!")
                logger.debug(f"[INSERT_HEADER] Dialogs: {selection.get('dialogCount', 0)}, Modals: {selection.get('modalCount', 0)}")
                return False

            if not selection['clicked']:
                logger.error(f"[INSERT_HEADER] Failed to select tile")
                logger.debug(f"[INSERT_HEADER] Tiles: {selection.get('tiles', 0)}")
                return False

            logger.debug(f"[INSERT_HEADER] Logo tile selected")
            await asyncio.sleep(2)

            # Click INSERT
            logger.debug(f"[INSERT_HEADER] Looking for Insert button...")
            insert_result = await page.evaluate("""
                () => {
                    const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                    if (!popup) return { clicked: false, popup: false };

                    const buttons = Array.from(popup.querySelectorAll('button'));
                    const insertBtn = buttons.find(b => b.textContent.trim().toLowerCase().includes('insert'));

                    if (insertBtn && !insertBtn.disabled) {
                        insertBtn.click();
                        return { clicked: true, popup: true };
                    }

                    const allButtons = buttons.map(b => b.textContent.trim());
                    return { clicked: false, popup: true, buttons: allButtons };
                }
            """)

            if not insert_result['clicked']:
                logger.error(f"[INSERT_HEADER] Failed to click Insert button")
                logger.debug(f"[INSERT_HEADER] Buttons: {insert_result.get('buttons', [])}")
                return False

            logger.debug(f"[INSERT_HEADER] Insert button clicked")
            await asyncio.sleep(2)
            return True

        except Exception as e:
            logger.error(f"[INSERT_HEADER] Unexpected error: {e}")
            import traceback
            logger.error(f"[INSERT_HEADER] Traceback: {traceback.format_exc()}")
            return False

    async def _add_logo_to_template(self, job_id: str, page: Page,
                                    logo_media_id: str, logo_width: int) -> bool:
        """Add logo to the template using Playwright automation"""

        try:
            # Click on the template editor area
            self.add_log(job_id, "   🖱️ Clicking editor area...", "info")
            await page.click('iframe[title*="Editor"], iframe[title*="editor"], .editor-iframe', timeout=5000)
            await asyncio.sleep(0.5)

            # Open image insertion menu
            self.add_log(job_id, "   🖼️ Opening image menu...", "info")
            await page.click('[aria-label*="Image"], button[title*="Image"]', timeout=5000)
            await asyncio.sleep(1)

            # Select the logo from media library
            self.add_log(job_id, f"   📂 Selecting logo (ID: {logo_media_id})...", "info")

            # Click on media library tab
            await page.click('text="Media Library"', timeout=5000)
            await asyncio.sleep(0.5)

            # Search for the specific media ID or select it
            media_selector = f'[data-media-id="{logo_media_id}"], img[src*="{logo_media_id}"]'
            await page.click(media_selector, timeout=5000)
            await asyncio.sleep(0.5)

            # Insert the image
            self.add_log(job_id, "   ➕ Inserting logo...", "info")
            await page.click('button:has-text("Insert"), button:has-text("Add")', timeout=5000)
            await asyncio.sleep(1)

            # Resize logo to specified width
            self.add_log(job_id, f"   📏 Resizing logo to {logo_width}px...", "info")
            await self._resize_image(page, logo_width)

            # Center the logo
            self.add_log(job_id, "   ⬅️➡️ Centering logo...", "info")
            await page.click('[aria-label*="Align center"], button[title*="Center"]', timeout=5000)
            await asyncio.sleep(0.5)

            return True

        except Exception as e:
            logger.error(f"Error adding logo: {e}")
            return False

    async def _resize_image(self, page: Page, width: int):
        """Resize the selected image to specified width"""
        try:
            # Try to find width input field
            width_input = page.locator('input[aria-label*="Width"], input[placeholder*="Width"]').first
            await width_input.fill(str(width))
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.warning(f"Could not resize image: {e}")

    async def _publish_template(self, job_id: str, page: Page, template_name: str = "") -> bool:
        """
        Publish template with 2-click workflow - FROM FINAL (Lines 1881-1975)
        Auto-publish feature with modal handling
        """
        try:
            self.add_log(job_id, "   📤 Step 1: Clicking PUBLISH...", "info")

            # Find visible publish button
            publish_btns = await page.query_selector_all('button:has-text("Publish")')

            main_publish = None
            for btn in publish_btns:
                try:
                    box = await btn.bounding_box()
                    if box and box['x'] > 100:  # Avoid hidden buttons
                        main_publish = btn
                        break
                except:
                    continue

            if not main_publish:
                self.add_log(job_id, "   ⚠️  Publish button not found", "warning")
                return False

            # CLICK #1
            await main_publish.click()
            self.add_log(job_id, "   ✅ Clicked PUBLISH (1st click)", "success")
            await asyncio.sleep(2.5)

            # Check if modal opened
            modal_open = await page.evaluate("""
                () => {
                    const modal = document.querySelector('.ant-modal');
                    return modal && modal.getBoundingClientRect().width > 0;
                }
            """)

            if not modal_open:
                self.add_log(job_id, "   ✅ No modal - auto-saved!", "success")
                return True

            # CLICK #2 in modal
            self.add_log(job_id, "   📋 Clicking modal PUBLISH (2nd click)...", "info")

            modal_publish = await page.query_selector('.ant-modal button:has-text("Publish")')

            if modal_publish:
                await modal_publish.click()
                self.add_log(job_id, "   ✅ Clicked modal PUBLISH (2nd click)", "success")
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
                    self.add_log(job_id, "   ✅ Clicked via JS (2nd click)", "success")
                else:
                    self.add_log(job_id, "   ⚠️  Could not click modal", "warning")
                    return False

            await asyncio.sleep(2.5)

            # Verify modal closed
            modal_closed = await page.evaluate("""
                () => {
                    const modal = document.querySelector('.ant-modal');
                    return !modal || modal.getBoundingClientRect().width === 0;
                }
            """)

            if modal_closed:
                self.add_log(job_id, "   ✅ Publish verified!", "success")
                return True
            else:
                self.add_log(job_id, "   ⚠️  Modal still open", "warning")
                return False

        except Exception as e:
            logger.exception(f"Publish error: {e}")
            self.add_log(job_id, f"   ❌ Publish error: {e}", "error")
            return False

    async def _generate_excel_report(self, job_id: str):
        """Generate Excel report of logo addition results"""

        job = self.jobs[job_id]

        try:
            self.add_log(job_id, "📊 Generating Excel report...", "info")

            df = pd.DataFrame(job['results'])

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logo_addition_report_{timestamp}.xlsx"
            filepath = Path("backend") / "output" / filename
            filepath.parent.mkdir(exist_ok=True)

            df.to_excel(filepath, index=False, engine='openpyxl')

            self.add_log(job_id, f"✅ Report saved: {filename}", "success")
            job["report_file"] = str(filepath)

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            self.add_log(job_id, f"⚠️ Report generation failed: {str(e)}", "warning")


# Global instance
template_logo_addition_service = TemplateLogoAdditionService()

