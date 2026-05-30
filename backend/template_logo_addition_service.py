"""
Template Logo Addition Service
Handles bulk addition of custom logos to Tekion email templates
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import pandas as pd
from playwright.async_api import Page, Browser, Error as PlaywrightError

logger = logging.getLogger(__name__)


class TemplateLogoAdditionService:
    """Service for adding custom logos to Tekion templates"""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        logger.info("✨ Template Logo Addition Service initialized")
    
    def create_job(self, job_id: str, base_url: str, max_rows: int = 200, 
                   custom_limit: Optional[int] = None, keep_tabs_open: bool = True,
                   logo_media_id: str = "6a19132b6697f36de6236fb1",
                   logo_width: int = 160) -> Dict[str, Any]:
        """Create a new logo addition job"""
        
        job = {
            "job_id": job_id,
            "base_url": base_url,
            "max_rows": max_rows,
            "custom_limit": custom_limit,
            "keep_tabs_open": keep_tabs_open,
            "logo_media_id": logo_media_id,  # Tilton.png media ID
            "logo_width": logo_width,
            "status": "pending",
            "start_time": datetime.now(),
            "logs": [],
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "templates": [],
            "results": []
        }
        
        self.jobs[job_id] = job
        logger.info(f"✨ Created logo addition job: {job_id}")
        logger.info(f"   Base URL: {base_url}")
        logger.info(f"   Max rows: {max_rows}")
        logger.info(f"   Custom limit: {custom_limit}")
        logger.info(f"   Keep tabs open: {keep_tabs_open}")
        logger.info(f"   Logo Media ID: {logo_media_id}")
        logger.info(f"   Logo Width: {logo_width}px")
        
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
    
    async def run_logo_addition(self, job_id: str, browser: Browser):
        """Main execution flow for adding logos"""
        
        if job_id not in self.jobs:
            logger.error(f"Job {job_id} not found")
            return
        
        job = self.jobs[job_id]
        
        try:
            job["status"] = "running"
            self.add_log(job_id, "🚀 Starting logo addition process...", "info")
            
            # Step 1: Connect to existing browser
            self.add_log(job_id, "🌐 Connecting to browser...", "info")
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            
            # Step 2: Navigate to templates list
            self.add_log(job_id, "📋 Opening templates list page...", "info")
            page = await context.new_page()
            templates_url = f"{job['base_url']}/templates/list"
            await page.goto(templates_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(3)
            self.add_log(job_id, "✅ Templates page loaded", "success")
            
            # Step 3: Fetch templates via API interception
            self.add_log(job_id, "🔍 Fetching templates from API...", "info")
            templates = await self._fetch_templates_via_api(job_id, page, job['max_rows'])
            
            if not templates:
                self.add_log(job_id, "❌ No templates found", "error")
                job["status"] = "failed"
                return
            
            self.add_log(job_id, f"✅ Found {len(templates)} templates", "success")
            job["templates"] = templates
            
            # Apply custom limit if specified
            templates_to_process = templates
            if job['custom_limit']:
                templates_to_process = templates[:job['custom_limit']]
                self.add_log(job_id, f"📊 Processing {len(templates_to_process)} templates (custom limit)", "info")
            
            # Step 4: Process each template
            self.add_log(job_id, "=" * 60, "info")
            self.add_log(job_id, f"🎨 Processing {len(templates_to_process)} templates for logo addition", "info")
            self.add_log(job_id, "=" * 60, "info")
            
            for idx, template in enumerate(templates_to_process, 1):
                await self._process_template(job_id, context, template, idx, len(templates_to_process))
            
            # Step 5: Generate report
            self.add_log(job_id, "", "info")
            self.add_log(job_id, "=" * 60, "info")
            self.add_log(job_id, "📊 LOGO ADDITION COMPLETE", "success")
            self.add_log(job_id, "=" * 60, "info")
            self.add_log(job_id, f"✅ Successful: {job['successful']}", "success")
            self.add_log(job_id, f"❌ Failed: {job['failed']}", "error" if job['failed'] > 0 else "info")
            self.add_log(job_id, f"📋 Total Processed: {job['processed']}", "info")
            
            await self._generate_excel_report(job_id)
            
            job["status"] = "completed"
            job["end_time"] = datetime.now()

        except Exception as e:
            logger.exception(f"Error in logo addition job {job_id}")
            self.add_log(job_id, f"❌ Fatal error: {str(e)}", "error")
            job["status"] = "failed"
            job["error"] = str(e)

    async def _fetch_templates_via_api(self, job_id: str, page: Page, max_rows: int) -> List[Dict]:
        """Fetch templates by intercepting API calls"""

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
                            self.add_log(job_id, f"📥 Captured {len(hits)} templates from API", "info")
                            response_received.set()
                except Exception as e:
                    logger.error(f"Error parsing API response: {e}")

        page.on('response', handle_response)

        # Reload page to trigger API call
        self.add_log(job_id, "🔄 Reloading page to fetch templates...", "info")
        await page.reload(wait_until='domcontentloaded')

        try:
            await asyncio.wait_for(response_received.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            self.add_log(job_id, "⚠️ API fetch timeout, retrying...", "warning")

        page.remove_listener('response', handle_response)

        return templates[:max_rows]

    async def _process_template(self, job_id: str, context, template: Dict,
                                idx: int, total: int):
        """Process a single template to add logo"""

        job = self.jobs[job_id]
        template_id = template.get('templateId') or template.get('id')
        template_name = template.get('name', 'Unknown')

        self.add_log(job_id, "", "info")
        self.add_log(job_id, f"📄 [{idx}/{total}] {template_name}", "info")
        self.add_log(job_id, f"   ID: {template_id}", "info")

        result = {
            "template_id": template_id,
            "template_name": template_name,
            "status": "pending",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            # Open template editor
            edit_url = f"{job['base_url']}/templates/edit/{template_id}"
            self.add_log(job_id, f"   🌐 Opening editor: {edit_url[:80]}...", "info")

            page = await context.new_page()
            await page.goto(edit_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)

            # Wait for editor to load
            self.add_log(job_id, "   ⏳ Waiting for editor to load...", "info")
            await asyncio.sleep(2)

            # Add logo to template
            self.add_log(job_id, f"   ✨ Adding logo (Media ID: {job['logo_media_id']})...", "info")
            success = await self._add_logo_to_template(job_id, page, job['logo_media_id'], job['logo_width'])

            if success:
                # Publish changes
                self.add_log(job_id, "   📤 Publishing changes...", "info")
                published = await self._publish_template(job_id, page)

                if published:
                    self.add_log(job_id, f"   ✅ Successfully added logo to {template_name}", "success")
                    result["status"] = "success"
                    job["successful"] += 1
                else:
                    self.add_log(job_id, f"   ⚠️ Logo added but publish failed for {template_name}", "warning")
                    result["status"] = "partial"
                    job["failed"] += 1
            else:
                self.add_log(job_id, f"   ❌ Failed to add logo to {template_name}", "error")
                result["status"] = "failed"
                job["failed"] += 1

            # Keep tab open or close
            if not job['keep_tabs_open']:
                await page.close()
            else:
                self.add_log(job_id, "   📌 Tab kept open for verification", "info")

        except Exception as e:
            logger.exception(f"Error processing template {template_id}")
            self.add_log(job_id, f"   ❌ Error: {str(e)}", "error")
            result["status"] = "error"
            result["error"] = str(e)
            job["failed"] += 1

        job["processed"] += 1
        job["results"].append(result)

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

    async def _publish_template(self, job_id: str, page: Page) -> bool:
        """Publish the template changes"""
        try:
            # Click Publish button
            await page.click('button:has-text("Publish"), button:has-text("Save")', timeout=5000)
            await asyncio.sleep(1)

            # Confirm if modal appears
            try:
                await page.click('button:has-text("Confirm"), button:has-text("Yes")', timeout=2000)
                await asyncio.sleep(1)
            except:
                pass  # No confirmation needed

            return True
        except Exception as e:
            logger.error(f"Error publishing template: {e}")
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

