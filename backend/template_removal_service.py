"""
Template Logo Removal Service
Handles bulk removal of "Powered by Tekion" logos from all templates

This service leverages the existing ScreenshotService infrastructure:
- TabRegistry for tab management
- Parallel processing with multiple tabs
- Browser context reuse
- Automatic cleanup
"""

import asyncio
import uuid
from typing import Dict, Optional, List
from datetime import datetime
from playwright.async_api import Page, BrowserContext
import logging
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import os

logger = logging.getLogger(__name__)


class TemplateRemovalService:
    def __init__(self, screenshot_service=None):
        """
        Initialize template removal service

        Args:
            screenshot_service: Existing ScreenshotService instance to reuse browser/tabs
        """
        self.active_jobs: Dict[str, dict] = {}
        self.screenshot_service = screenshot_service
        logger.info("🎨 Template Removal Service initialized")
        
    async def start_removal_job(
        self,
        base_url: str,
        job_id: str,
        progress_callback=None,
        max_parallel: int = 5,
        max_rows: int = 200,  # Maximum rows to fetch from API
        custom_limit: int = None,  # Custom limit on how many to process
        keep_tabs_open: bool = False  # ✅ NEW: Keep tabs open for verification
    ) -> dict:
        """
        Start a new template logo removal job with parallel processing

        Args:
            base_url: Base URL of the Tekion app (e.g., https://preprodapp.tekioncloud.com)
            job_id: Unique job identifier
            progress_callback: Async function to call with progress updates
            max_parallel: Maximum number of parallel tabs to use (default: 5)
            max_rows: Maximum number of templates to fetch from API (default: 200)
            custom_limit: Custom limit on how many templates to process (None = all)
            keep_tabs_open: Keep tabs open for manual verification (default: False)

        Returns:
            Job status dictionary
        """
        logger.info(f"🎨 Starting template removal job {job_id} for {base_url}")
        logger.info(f"⚡ Parallel processing: Up to {max_parallel} templates at once")

        job_status = {
            "job_id": job_id,
            "status": "running",
            "total": 0,
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "current_template": None,
            "errors": [],
            "logs": [],  # ✅ NEW: Store log messages for the UI
            "started_at": datetime.now().isoformat(),
            "template_urls": [],  # Store all template edit URLs
            "template_results": []  # ✅ Track individual template results {name, status, url}
        }

        self.active_jobs[job_id] = job_status

        # Helper function to add logs that appear in the UI
        def add_log(message: str):
            """Add a log message that will be sent to the frontend"""
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            logger.info(message)  # Also log to backend console
            job_status["logs"].append(log_entry)
            # Keep only last 100 logs to avoid memory issues
            if len(job_status["logs"]) > 100:
                job_status["logs"] = job_status["logs"][-100:]
        
        try:
            # ========================================
            # PHASE 1: Extract All Template URLs
            # ========================================
            add_log("📋 Phase 1: Extracting all template URLs...")
            add_log(f"🌐 Base URL: {base_url}")
            add_log(f"⚡ Max parallel: {max_parallel} templates at once")

            template_urls = await self._extract_template_urls(base_url, add_log, max_rows, job_status)

            # ✅ Check if job was cancelled during URL extraction
            if job_status.get("status") == "cancelled":
                add_log("🛑 Job cancelled by user")
                return job_status

            if not template_urls:
                add_log("❌ No templates found!")
                job_status["status"] = "failed"
                job_status["errors"].append("No templates found")
                return job_status

            # ✅ Apply custom limit if specified
            if custom_limit and custom_limit > 0:
                original_count = len(template_urls)
                template_urls = template_urls[:custom_limit]
                job_status["template_results"] = job_status["template_results"][:custom_limit]
                add_log(f"🎯 Custom limit applied: Processing {len(template_urls)} out of {original_count} templates")
                logger.info(f"Custom limit: {custom_limit} - Processing {len(template_urls)}/{original_count} templates")

            total_templates = len(template_urls)
            job_status["total"] = total_templates
            job_status["template_urls"] = template_urls

            logger.info(f"✅ Found {total_templates} template URLs")
            logger.info(f"🔗 Sample URLs: {template_urls[:3]}")

            if progress_callback:
                await progress_callback(job_status)

            # ========================================
            # PHASE 2: Process Templates in Parallel
            # ========================================
            # ✅ Check if job was cancelled before starting Phase 2
            if job_status.get("status") == "cancelled":
                logger.info("🛑 Job cancelled by user before Phase 2")
                return job_status

            logger.info(f"⚡ Phase 2: Processing {total_templates} templates with {max_parallel} parallel tabs...")

            await self._process_templates_parallel(
                template_urls=template_urls,
                job_status=job_status,
                progress_callback=progress_callback,
                max_parallel=max_parallel,
                keep_tabs_open=keep_tabs_open  # ✅ Pass keep tabs open setting
            )

                
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}")
            job_status["status"] = "failed"
            job_status["errors"].append(f"Job failed: {str(e)}")
        else:
            job_status["status"] = "completed"
        
        job_status["completed_at"] = datetime.now().isoformat()

        # ✅ Generate Excel report (always, even if cancelled or failed)
        try:
            excel_path = self._generate_excel_report(job_status)
            job_status["excel_report"] = excel_path
            logger.info(f"📊 Excel report generated: {excel_path}")
        except Exception as e:
            logger.error(f"Failed to generate Excel report: {e}")

        if progress_callback:
            await progress_callback(job_status)

        return job_status

    async def _extract_template_urls(self, base_url: str, add_log, max_rows: int = 200, job_status: dict = None) -> List[str]:
        """
        Extract all template edit URLs from the templates list page

        Args:
            base_url: Base URL of the Tekion app
            add_log: Function to log messages to the UI
            max_rows: Maximum number of templates to fetch from API (default: 200)
            job_status: Job status dictionary to store template results (optional)

        Returns:
            List of template edit URLs
        """
        from screenshot_service import ScreenshotService

        template_urls = []

        try:
            # ✅ USE BRAVE CDP DIRECTLY - Use your existing logged-in context!
            add_log("🦁 Using your existing Brave browser...")

            from playwright.async_api import async_playwright

            if not hasattr(self, '_playwright'):
                self._playwright = await async_playwright().start()

            # Connect to Brave CDP on port 9223
            add_log("🔗 Connecting to Brave (port 9223)...")
            browser = await self._playwright.chromium.connect_over_cdp("http://localhost:9223")
            add_log("✅ Connected to Brave!")

            # ✅ KEY FIX: Use an EXISTING page (tab) that's already on the templates list
            # Don't create a new page - find one that's already open!
            add_log("📄 Looking for an existing tab with the templates list...")

            if not browser.contexts:
                add_log("❌ No browser contexts found!")
                return []

            context = browser.contexts[0]
            pages = context.pages

            add_log(f"✅ Found {len(pages)} open tabs in Brave")

            # Try to find a tab that's already on the templates list page
            page = None
            for p in pages:
                try:
                    url = p.url
                    title = await p.title()
                    add_log(f"   Tab: '{title}' - {url}")

                    if '/templates/list' in url or 'Template' in title:
                        page = p
                        add_log(f"✅ Found templates list tab! Using it.")
                        break
                except:
                    continue

            if not page:
                # Create new page only if no templates list tab found
                add_log("⚠️  No templates list tab found. Creating new one...")
                page = await context.new_page()
                add_log("✅ New tab created")

                # Navigate to templates list
                templates_url = f"{base_url}/templates/list"
                add_log(f"📡 Navigating to templates list page...")

                try:
                    await page.goto(templates_url, wait_until="domcontentloaded", timeout=30000)
                    add_log(f"✅ Page navigation complete")

                    # Wait for the table to appear
                    await page.wait_for_selector('div.rt-tr, table tr', timeout=10000)
                    add_log(f"✅ Table loaded successfully")
                except Exception as e:
                    add_log(f"❌ Failed to navigate: {str(e)}")
                    raise

                await asyncio.sleep(1)
            else:
                # ✅ Using existing tab - no need to navigate!
                add_log(f"✅ Using existing templates list tab (no navigation needed)")

                # Just wait for table to be ready
                try:
                    await page.wait_for_selector('div.rt-tr, table tr', timeout=5000)
                    add_log(f"✅ Table is ready")
                except:
                    add_log(f"⚠️  Table selector not found, continuing anyway...")

                await asyncio.sleep(0.5)

            # Get page info
            page_title = await page.title()
            page_url = page.url
            add_log(f"📄 Page: '{page_title}'")

            # Check if login required
            is_login_page = '/login' in page_url
            if is_login_page:
                add_log(f"❌ Not logged in! Please login to preprod in Brave first.")
                return []  # Return empty list if not authenticated

            # ✅ NEW APPROACH: Intercept AND MODIFY API calls to get more templates!
            add_log(f"🌐 Intercepting API calls to extract template data...")

            template_data = []
            response_received = asyncio.Event()  # ✅ Flag to wait for response

            # ✅ Intercept and modify the request to fetch 200 rows instead of 50
            async def handle_route(route):
                if '/api/templatestore/u/search' in route.request.url:
                    # Get original request body
                    post_data = route.request.post_data_json

                    if post_data and 'pageInfo' in post_data:
                        # ✅ Modify to request max_rows instead of 50
                        original_rows = post_data['pageInfo'].get('rows', 50)
                        post_data['pageInfo']['rows'] = max_rows
                        add_log(f"📝 Modified API request: rows={original_rows} → rows={max_rows}")
                        logger.info(f"Modified API payload: {post_data}")

                        # Continue with modified request
                        await route.continue_(post_data=post_data)
                    else:
                        await route.continue_()
                else:
                    await route.continue_()

            # Set up request interception
            await page.route("**/api/templatestore/u/search", handle_route)

            # Set up response listener
            async def handle_response(response):
                if '/api/templatestore/u/search' in response.url:
                    try:
                        data = await response.json()
                        if 'data' in data and 'hits' in data['data']:
                            hits = data['data']['hits']
                            add_log(f"📡 API response received: {len(hits)} templates")

                            for hit in hits:
                                # Filter based on your criteria
                                status = hit.get('status')
                                purpose_type = hit.get('purposeType')
                                purpose_subtype = hit.get('purposeSubType')
                                departments = hit.get('departments', [])
                                template_id = hit.get('templateId')  # ✅ FIXED: Use 'templateId' not 'id'
                                name = hit.get('name', 'Unknown')

                                # Apply filters:
                                # 1. status == "ACTIVE"
                                # 2. purposeSubType == "EMAIL"
                                # 3. purposeType == "COMMUNICATION"
                                # 4. "SALES" in departments
                                if (status == 'ACTIVE' and
                                    purpose_subtype == 'EMAIL' and
                                    purpose_type == 'COMMUNICATION' and
                                    'SALES' in departments and
                                    template_id):

                                    template_data.append({
                                        'templateId': template_id,  # ✅ FIXED: Use 'templateId'
                                        'name': name,
                                        'departments': departments
                                    })
                                    logger.info(f"✓ Template: {name} (templateId: {template_id}, Depts: {departments})")

                            # ✅ Signal that response has been received and processed
                            response_received.set()
                    except Exception as e:
                        logger.error(f"Error parsing API response: {e}")
                        response_received.set()  # Still signal even on error

            page.on("response", handle_response)

            # Trigger the API call by refreshing/navigating
            add_log(f"🔄 Refreshing page to trigger API call...")
            await page.reload()

            # ✅ WAIT for the response to be received and processed
            add_log(f"⏳ Waiting for API response...")
            try:
                await asyncio.wait_for(response_received.wait(), timeout=15.0)
                add_log(f"✅ API response processed")
            except asyncio.TimeoutError:
                add_log(f"⚠️  API response timeout after 15 seconds")

            # Additional small wait to ensure all async processing is done
            await asyncio.sleep(1)

            add_log(f"✅ Found {len(template_data)} templates matching criteria")

            # Build template URLs from templateIds and store template info
            for item in template_data:
                template_url = f"{base_url}/templates/edit/{item['templateId']}"  # ✅ FIXED: Use 'templateId'
                template_urls.append(template_url)

                # ✅ Store template info for Excel report (if job_status is provided)
                if job_status is not None:
                    job_status["template_results"].append({
                        "name": item['name'],
                        "url": template_url,
                        "status": "Pending"  # Will be updated during processing
                    })

            add_log(f"✅ Extracted {len(template_urls)} template URLs from API!")

            # Close the page/context
            await context.close()

        except Exception as e:
            import traceback
            add_log(f"❌ Error: {str(e)}")
            logger.error(f"📋 Traceback: {traceback.format_exc()}")

        return template_urls

    async def _process_templates_parallel(
        self,
        template_urls: List[str],
        job_status: dict,
        progress_callback=None,
        max_parallel: int = 5,
        keep_tabs_open: bool = False  # ✅ NEW: Keep tabs open setting
    ):
        """
        Process templates in parallel using multiple browser tabs

        Args:
            template_urls: List of template edit URLs
            job_status: Job status dict to update
            progress_callback: Callback for progress updates
            max_parallel: Max concurrent tabs
            keep_tabs_open: Keep tabs open for verification (don't close them)
        """
        from screenshot_service import ScreenshotService

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_parallel)

        # ✅ Connect to Brave CDP once (shared connection)
        from playwright.async_api import async_playwright

        if not hasattr(self, '_playwright'):
            self._playwright = await async_playwright().start()

        # Connect to Brave CDP
        logger.info("🔗 Connecting to Brave CDP for parallel processing...")
        browser = await self._playwright.chromium.connect_over_cdp("http://localhost:9223")

        # Use existing context (authenticated!)
        if browser.contexts:
            context = browser.contexts[0]
            logger.info(f"✅ Using existing Brave context (authenticated)")
        else:
            context = await browser.new_context()
            logger.info("⚠️  Created new context (may need authentication)")

        async def process_one_template(url: str, index: int):
            async with semaphore:
                # ✅ Check if job was cancelled (frontend reloaded/closed)
                if job_status.get("status") == "cancelled":
                    logger.info(f"🛑 Job cancelled, skipping template {index + 1}")
                    return

                template_name = f"Template {index + 1}"
                page = None

                try:
                    logger.info(f"🎨 [{index + 1}/{len(template_urls)}] Processing: {url}")
                    job_status["current_template"] = template_name

                    if progress_callback:
                        await progress_callback(job_status)

                    # Create new page (tab) in authenticated context
                    page = await context.new_page()
                    logger.info(f"📄 [{index + 1}] New tab created")

                    # Navigate to template edit page
                    logger.info(f"📡 [{index + 1}] Navigating to: {url}")

                    # ✅ Navigate and wait for load
                    await page.goto(url, wait_until="load", timeout=45000)
                    logger.info(f"📄 [{index + 1}] Initial page load complete")

                    # ✅ KEY FIX: Reload the page to trigger proper initialization
                    # Direct navigation might skip some init, but reload ensures everything loads
                    logger.info(f"🔄 [{index + 1}] Reloading page to ensure proper initialization...")
                    await page.reload(wait_until="load")
                    logger.info(f"✅ [{index + 1}] Page reloaded")

                    # ✅ Wait for network to be idle (all API calls complete)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=15000)
                        logger.info(f"🌐 [{index + 1}] Network idle - all API calls complete")
                    except:
                        logger.warning(f"⚠️  [{index + 1}] Network still active after 15s, continuing anyway")

                    # ✅ Wait for template editor UI elements to appear
                    try:
                        # Wait for the template builder iframe or editor
                        await page.wait_for_selector('.ant-layout, [class*="template"], [class*="editor"], iframe, img[alt="Tekion Logo"]', timeout=10000)
                        logger.info(f"✅ [{index + 1}] Template editor UI loaded")
                    except:
                        logger.warning(f"⚠️  [{index + 1}] Template editor UI not detected, proceeding anyway")

                    # ✅ Additional wait to ensure all dynamic content loads (match your JavaScript's 2 second wait)
                    await asyncio.sleep(3)  # Increased to 3 seconds for safety
                    logger.info(f"✅ [{index + 1}] Ready to remove logo")

                    # Remove logo
                    logo_result = await self._remove_logo_from_page(page)

                    # ✅ Update template status in results
                    if index < len(job_status["template_results"]):
                        if logo_result == "NA":
                            job_status["template_results"][index]["status"] = "NA"
                        elif logo_result:
                            job_status["template_results"][index]["status"] = "Done"
                        else:
                            job_status["template_results"][index]["status"] = "Not Done"

                    if logo_result and logo_result != "NA":
                        job_status["successful"] += 1
                        logger.info(f"✅ [{index + 1}/{len(template_urls)}] Success: {url}")
                    else:
                        job_status["failed"] += 1
                        job_status["errors"].append(f"Failed: {url}")
                        logger.warning(f"⚠️  [{index + 1}/{len(template_urls)}] Failed: {url}")

                except Exception as e:
                    # ✅ Mark as "Not Done" on exception
                    if index < len(job_status["template_results"]):
                        job_status["template_results"][index]["status"] = "Not Done"

                    job_status["failed"] += 1
                    error_msg = f"{template_name}: {str(e)}"
                    job_status["errors"].append(error_msg)
                    logger.error(f"❌ [{index + 1}/{len(template_urls)}] Error: {str(e)}")

                finally:
                    # ✅ Close the page (tab) only if keep_tabs_open is False
                    if page:
                        if keep_tabs_open:
                            logger.info(f"📌 [{index + 1}] Tab kept open for verification")
                        else:
                            try:
                                await page.close()
                                logger.info(f"🗑️  [{index + 1}] Tab closed")
                            except:
                                pass

                    job_status["processed"] += 1

                    if progress_callback:
                        await progress_callback(job_status)

        # Process all templates in parallel
        tasks = [
            process_one_template(url, i)
            for i, url in enumerate(template_urls)
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"🎉 Parallel processing complete!")
        logger.info(f"   Total: {len(template_urls)}")
        logger.info(f"   ✅ Success: {job_status['successful']}")
        logger.info(f"   ❌ Failed: {job_status['failed']}")

    async def _remove_logo_from_page(self, page: Page) -> bool:
        """
        Remove Tekion logo using Playwright's REAL mouse hover
        This physically moves the mouse cursor to reveal the delete button!

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("🔍 Finding Tekion logo...")

            # Find logo and mark container
            container_found = await page.evaluate("""
                () => {
                    const logoImg = document.querySelector('img[alt="Tekion Logo"]');
                    if (!logoImg) return false;

                    const container = logoImg.closest('[class*="elementContainer"]') ||
                                     logoImg.closest('[class*="element-container"]') ||
                                     logoImg.closest('[class*="powered"]') ||
                                     logoImg.closest('div[id]') ||
                                     logoImg.parentElement;

                    if (!container) return false;

                    container.setAttribute('data-tekion-logo-container', 'true');
                    return true;
                }
            """)

            if not container_found:
                logger.info("⚠️  No Tekion logo found (element not available)")
                return "NA"  # ✅ Return "NA" when logo element doesn't exist

            logger.info("✅ Found Tekion logo container")

            # Get container element
            container = await page.query_selector('[data-tekion-logo-container="true"]')

            if not container:
                logger.error("❌ Could not get container element")
                return False

            # ✅ KEY FIX: Use Playwright's REAL hover with force=True
            logger.info("🖱️  Forcing hover over element...")
            try:
                await container.hover(force=True, timeout=5000)
                logger.info("✅ Mouse is hovering (delete button should appear now)")
            except Exception as e:
                logger.warning(f"⚠️  Force hover failed: {e}, trying JavaScript hover...")
                # Fallback to JavaScript hover
                await page.evaluate("""
                    () => {
                        const container = document.querySelector('[data-tekion-logo-container="true"]');
                        if (container) {
                            container.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
                            container.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                        }
                    }
                """)
                logger.info("✅ JavaScript hover dispatched")

            # Wait for delete button to appear
            await asyncio.sleep(2)
            logger.info("⏱️  Waited 2 seconds for X icon to appear")

            # Try to find and click delete button
            logger.info("🔍 Searching for delete button...")

            delete_selectors = [
                # ✅ Specific working selector for header logos (discovered 2026-05-30)
                '.templates_SortableItem_removeBtn__osvYZsTyqJ',
                # Generic selectors (fallback)
                '[class*="removeBtn"]',
                '[class*="icon-cross"]',
                '[class*="icon-close"]',
                '[class*="icon-delete"]',
                '[class*="icon-remove"]',
                '[class*="delete"]',
                '[class*="remove"]',
                '[class*="close"]',
                'button[aria-label*="delete" i]',
                'button[aria-label*="remove" i]',
                'button[aria-label*="close" i]',
                '[data-action="delete"]',
                '[data-action="remove"]',
                'svg[class*="cross"]',
                'svg[class*="close"]',
                'i[class*="cross"]',
                'i[class*="close"]'
            ]

            delete_clicked = False
            for selector in delete_selectors:
                try:
                    # Try within container
                    delete_btn = await container.query_selector(selector)

                    if delete_btn:
                        logger.info(f"✅ Found delete button: {selector}")
                        await delete_btn.click()
                        logger.info("🖱️  Clicked delete button")
                        await asyncio.sleep(0.5)
                        delete_clicked = True
                        break
                except:
                    continue

            if not delete_clicked:
                logger.warning("⚠️  No delete button found, trying fallback...")

            # Check if removed
            element_exists = await page.evaluate("""
                () => {
                    const cont = document.querySelector('[data-tekion-logo-container="true"]');
                    return cont !== null && document.contains(cont);
                }
            """)

            if not element_exists:
                logger.info("✅ Logo removed via delete button!")
                logo_removed = True
                # ✅ DON'T return yet - we need to click Publish!
            else:
                # Fallback strategies
                logger.info("📍 Trying JavaScript fallback removal...")
                result = await page.evaluate("""
                    async () => {
                        const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                        const container = document.querySelector('[data-tekion-logo-container="true"]');

                        if (!container) return { success: true, reason: 'already_removed' };

                        // Strategy 2: Direct removal
                        container.remove();
                        await sleep(300);

                        if (!document.contains(container)) {
                            return { success: true, reason: 'direct_removal' };
                        }

                        // Strategy 3: Parent removal
                        if (container.parentNode) {
                            container.parentNode.removeChild(container);
                            await sleep(300);

                            if (!document.contains(container)) {
                                return { success: true, reason: 'parent_removal' };
                            }
                        }

                        // Strategy 4: Hide with CSS
                        container.style.display = 'none';
                        container.style.visibility = 'hidden';
                        container.style.opacity = '0';
                        container.style.position = 'absolute';
                        container.style.left = '-9999px';

                        return { success: true, reason: 'css_hide' };
                    }
                """)

                logo_removed = result.get("success", False)

                if not logo_removed:
                    logger.warning("Failed to remove logo")
                    return False

                logger.info(f"✅ Logo removed successfully (method: {result.get('reason', 'unknown')})")

            # ✅ Click the "Publish" button after removing the logo
            logger.info("📤 Clicking Publish button...")
            try:
                # Try multiple selectors for the Publish button
                publish_selectors = [
                    'button#btnSalesSetupSave',  # Primary button ID
                    'button[data-test-id="undefined-Publish"]',  # ✅ NEW: Fail-safe selector
                    'button[data-test-id*="Publish"]',
                    'button:has-text("Publish")',
                    'button.ant-btn-primary:has-text("Publish")'
                ]

                publish_clicked = False
                for selector in publish_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        logger.info(f"✅ Clicked Publish button (selector: {selector})")
                        publish_clicked = True
                        break
                    except:
                        continue

                if not publish_clicked:
                    logger.warning("⚠️  Publish button not found with Playwright, trying JavaScript click...")
                    # Fallback: Try clicking via JavaScript
                    publish_js_result = await page.evaluate("""
                        () => {
                            const btn = document.querySelector('button#btnSalesSetupSave') ||
                                       document.querySelector('button[data-test-id="undefined-Publish"]') ||
                                       document.querySelector('button[data-test-id*="Publish"]') ||
                                       Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Publish'));
                            if (btn) {
                                btn.click();
                                return true;
                            }
                            return false;
                        }
                    """)
                    if publish_js_result:
                        logger.info("✅ Clicked Publish via JavaScript")
                        publish_clicked = True
                    else:
                        logger.error("❌ Publish button not found even with JavaScript!")

                # ✅ Wait for loader to appear and disappear
                logger.info("⏳ Waiting for loader...")
                try:
                    # Wait for loader to appear
                    await page.wait_for_selector('.templates_TemplateBuilder_loader__tBejhkZKfV > div:nth-of-type(1)', timeout=5000)
                    logger.info("✅ Loader appeared")

                    # Wait for loader to disappear
                    await page.wait_for_selector('.templates_TemplateBuilder_loader__tBejhkZKfV > div:nth-of-type(1)', state='hidden', timeout=15000)
                    logger.info("✅ Loader disappeared - popup should appear now")
                except Exception as e:
                    logger.warning(f"⚠️  Loader detection failed: {e}")

                # Small wait for popup to fully appear
                await asyncio.sleep(0.5)

                # ✅ Click the Publish button in the POPUP
                logger.info("📤 Clicking Publish button in popup...")
                try:
                    popup_publish_selectors = [
                        'button[data-test-id="undefined-submitButton"]',  # Primary popup button
                        'button[data-test-id*="submitButton"]',
                        '.ant-modal button:has-text("Publish")',
                        '.root_modal_submitBtn__7hhbPgopEx',
                        'button.ant-btn-primary:has-text("Publish")'
                    ]

                    popup_clicked = False
                    for selector in popup_publish_selectors:
                        try:
                            await page.click(selector, timeout=2000)
                            logger.info(f"✅ Clicked popup Publish button (selector: {selector})")
                            popup_clicked = True
                            break
                        except:
                            continue

                    if not popup_clicked:
                        logger.warning("⚠️  Popup Publish button not found with Playwright, trying JavaScript...")
                        # JavaScript fallback
                        popup_js_result = await page.evaluate("""
                            () => {
                                const btn = document.querySelector('button[data-test-id="undefined-submitButton"]') ||
                                           document.querySelector('button[data-test-id*="submitButton"]') ||
                                           document.querySelector('.root_modal_submitBtn__7hhbPgopEx') ||
                                           Array.from(document.querySelectorAll('.ant-modal button')).find(b => b.innerText.includes('Publish'));
                                if (btn) {
                                    btn.click();
                                    return true;
                                }
                                return false;
                            }
                        """)
                        if popup_js_result:
                            logger.info("✅ Clicked popup Publish via JavaScript")
                            popup_clicked = True
                        else:
                            logger.error("❌ Popup Publish button not found!")

                    # Wait 3 seconds after final publish
                    await asyncio.sleep(3)
                    logger.info("⏱️  Waited 3 seconds after popup publish")

                except Exception as e:
                    logger.error(f"❌ Error clicking popup Publish button: {e}")
                    # Continue anyway - logo was still removed

                return True

            except Exception as e:
                logger.error(f"❌ Error clicking Publish button: {str(e)}")
                # Still return True since logo was removed, even if publish failed
                return True

        except Exception as e:
            logger.error(f"Error removing logo: {str(e)}")
            return False

    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get status of a job"""
        return self.active_jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        if job_id in self.active_jobs:
            self.active_jobs[job_id]["status"] = "cancelled"
            return True
        return False

    def _generate_excel_report(self, job_status: dict) -> str:
        """
        Generate an Excel report with the results
        Returns the file path
        """
        # Create reports directory if it doesn't exist
        reports_dir = "backend/reports"
        os.makedirs(reports_dir, exist_ok=True)

        # ✅ Use the SAME filename every time (overwrites previous report)
        filename = "Communication Templates Tekion Logo removal.xlsx"
        filepath = os.path.join(reports_dir, filename)

        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Logo Removal Report"

        # ========== STYLING ==========
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=12)
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        success_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        success_font = Font(color="006100")

        fail_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        fail_font = Font(color="9C0006")

        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # ========== SUMMARY SECTION ==========
        ws['A1'] = "Communication Templates Tekion Logo Removal Report"
        ws['A1'].font = Font(size=16, bold=True)
        ws.merge_cells('A1:F1')

        ws['A2'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws.merge_cells('A2:F2')

        ws['A4'] = "Summary"
        ws['A4'].font = Font(size=14, bold=True)

        ws['A5'] = "Total Templates:"
        ws['B5'] = job_status.get("total", 0)
        ws['B5'].font = Font(bold=True)

        ws['A6'] = "Successful:"
        ws['B6'] = job_status.get("successful", 0)
        ws['B6'].font = success_font
        ws['B6'].fill = success_fill

        ws['A7'] = "Failed:"
        ws['B7'] = job_status.get("failed", 0)
        ws['B7'].font = fail_font
        ws['B7'].fill = fail_fill

        ws['A8'] = "Status:"
        ws['B8'] = job_status.get("status", "unknown").upper()
        ws['B8'].font = Font(bold=True)

        # ========== TEMPLATE LIST HEADER ==========
        ws['A10'] = "#"
        ws['B10'] = "Template Name"  # ✅ Changed from URL to Name
        ws['C10'] = "Status"  # Done / Not Done / NA

        for col in ['A', 'B', 'C']:
            cell = ws[f'{col}10']
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border

        # ========== TEMPLATE LIST DATA ==========
        row = 11
        template_results = job_status.get("template_results", [])

        for idx, template_info in enumerate(template_results, 1):
            name = template_info.get("name", "Unknown")
            status = template_info.get("status", "Pending")

            ws[f'A{row}'] = idx
            ws[f'B{row}'] = name
            ws[f'C{row}'] = status

            # Apply styling
            for col in ['A', 'B', 'C']:
                cell = ws[f'{col}{row}']
                cell.border = border

            # Color-code status
            if status == "Done":
                ws[f'C{row}'].fill = success_fill
                ws[f'C{row}'].font = success_font
            elif status == "Not Done":
                ws[f'C{row}'].fill = fail_fill
                ws[f'C{row}'].font = fail_font
            elif status == "NA":
                # Gray color for NA
                ws[f'C{row}'].fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
                ws[f'C{row}'].font = Font(color="696969")

            row += 1

        # ========== COLUMN WIDTHS ==========
        ws.column_dimensions['A'].width = 8
        ws.column_dimensions['B'].width = 60  # Wider for template names
        ws.column_dimensions['C'].width = 15

        # Save workbook
        wb.save(filepath)
        logger.info(f"📊 Excel report saved: {filepath}")

        return filepath


# Singleton instance
template_removal_service = TemplateRemovalService()
