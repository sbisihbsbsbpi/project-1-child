#!/usr/bin/env python3
"""
Fetch Service & Parts Templates - IMPROVED VERSION
Waits for results count to update after filtering
"""

import asyncio
import sys
import os
import json
import pandas as pd
from datetime import datetime
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def wait_for_results_to_load(page, department_name, previous_count=None, max_wait=15):
    """
    Wait for results count text to appear/update after filtering
    If previous_count is provided, wait until count CHANGES from that value
    Returns: (results_count, tab_count)
    """
    logger.info(f"   ⏳ Waiting for {department_name} results to load...")
    if previous_count:
        logger.info(f"   (Waiting for count to change from {previous_count}...)")

    start_time = asyncio.get_event_loop().time()
    last_seen_count = None
    stable_count = 0

    while (asyncio.get_event_loop().time() - start_time) < max_wait:
        # Check for results count text
        results_info = await page.evaluate("""
            () => {
                // Look for "X Result(s)" text
                const resultElements = document.querySelectorAll('[class*="filterResults"]');

                for (let el of resultElements) {
                    const text = el.textContent.trim();
                    const match = text.match(/(\\d+)\\s*Result/);
                    if (match) {
                        return {
                            count: parseInt(match[1]),
                            text: text
                        };
                    }
                }

                return null;
            }
        """)

        # Also check active tab count
        tab_info = await page.evaluate("""
            () => {
                const activeTab = document.querySelector('[role="tab"][aria-selected="true"]');
                if (activeTab) {
                    const text = activeTab.textContent.trim();
                    const match = text.match(/(\\w+)\\s*\\((\\d+)\\)/);
                    if (match) {
                        return {
                            tabName: match[1],
                            count: parseInt(match[2])
                        };
                    }
                }
                return null;
            }
        """)

        # If we have both results count and tab count
        if results_info and tab_info:
            current_count = tab_info['count']

            # If we're waiting for a change from previous count
            if previous_count is not None:
                if current_count != previous_count:
                    # Count changed - check if it's stable
                    if last_seen_count == current_count:
                        stable_count += 1
                        if stable_count >= 3:  # Stable for 3 iterations (1.5 seconds)
                            logger.info(f"   ✅ Results loaded: {results_info['count']} Result(s)")
                            logger.info(f"   ✅ Active tab: {tab_info['tabName']} ({tab_info['count']})")
                            return results_info['count'], tab_info['count']
                    else:
                        last_seen_count = current_count
                        stable_count = 1
                # else: still same as previous_count, keep waiting
            else:
                # No previous count - just check if stable
                if last_seen_count == current_count:
                    stable_count += 1
                    if stable_count >= 3:
                        logger.info(f"   ✅ Results loaded: {results_info['count']} Result(s)")
                        logger.info(f"   ✅ Active tab: {tab_info['tabName']} ({tab_info['count']})")
                        return results_info['count'], tab_info['count']
                else:
                    last_seen_count = current_count
                    stable_count = 1

        await asyncio.sleep(0.5)

    # Timeout - return what we have
    logger.warning(f"   ⚠️  Timeout waiting for results")
    if results_info and tab_info:
        logger.warning(f"   Last seen: {results_info['count']} Result(s), tab: {tab_info['count']}")
        return results_info['count'], tab_info['count']
    return None, None


async def switch_to_department(page, department_name, previous_count=None):
    """Switch to department and wait for data to load"""

    logger.info(f"\n🔄 Switching to {department_name} department...")

    try:
        # Click dropdown
        logger.info("   Opening department dropdown...")
        await page.click('.ant-dropdown-trigger', timeout=5000)
        await asyncio.sleep(1)

        # Select department
        selected = await page.evaluate(f"""
            async (dept) => {{
                // Find input
                const input = document.querySelector('input[id*="departments"]');
                if (!input) return false;

                // Focus and type
                input.focus();
                input.value = dept;

                // Trigger events
                const inputEvent = new Event('input', {{ bubbles: true }});
                input.dispatchEvent(inputEvent);

                // Wait for options
                await new Promise(r => setTimeout(r, 500));

                // Press Enter
                const enterEvent = new KeyboardEvent('keydown', {{
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    bubbles: true
                }});
                input.dispatchEvent(enterEvent);

                return true;
            }}
        """, department_name)

        if selected:
            logger.info(f"   ✅ Selected {department_name}")

            # Close dropdown
            await asyncio.sleep(1)
            await page.keyboard.press('Escape')
            await asyncio.sleep(2)  # Wait a bit longer for filter to apply

            # Wait for results to load (pass previous_count to detect changes)
            results_count, tab_count = await wait_for_results_to_load(page, department_name, previous_count)

            return True, results_count, tab_count
        else:
            logger.warning(f"   ⚠️  Could not select {department_name}")
            return False, None, None

    except Exception as e:
        logger.error(f"   ❌ Error switching to {department_name}: {e}")
        return False, None, None


async def fetch_templates_via_api(page, department_name, expected_count):
    """Fetch templates using DIRECT API call - NO page reload needed!"""

    logger.info("\n📥 Fetching templates via direct API call...")

    # Build API payload for this department
    payload = {
        "sort": [{"field": "modifiedTime", "order": "DESC"}],
        "filters": [
            {
                "field": "departments",
                "values": [department_name.upper()],
                "type": "terms"
            },
            {
                "field": "status",
                "values": ["ACTIVE"],
                "type": "terms"
            }
        ],
        "searchText": "",
        "groupBy": ["purposeSubType"],
        "includeFields": [],
        "searchableFields": ["name"],
        "excludeFields": ["body", "htmlBody", "subject", "htmlSubject", "preHeader", "languages"],
        "pageInfo": {"start": 0, "rows": 500}  # Get up to 500 templates
    }

    try:
        response = await page.evaluate("""
            async (payload) => {
                const response = await fetch('/api/templatestore/u/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                return await response.json();
            }
        """, payload)

        templates = []

        # Handle grouped response
        if 'data' in response and 'groups' in response.get('data', {}):
            groups = response['data']['groups']
            for group in groups:
                if 'hits' in group:
                    templates.extend(group['hits'])

        # Handle flat response
        elif 'data' in response and 'hits' in response.get('data', {}):
            templates = response['data']['hits']

        logger.info(f"   ✅ Fetched {len(templates)} templates via API")

        if len(templates) != expected_count:
            logger.warning(f"   ⚠️  Expected {expected_count} but got {len(templates)}")

        return templates

    except Exception as e:
        logger.error(f"   ❌ API call failed: {e}")
        return []


async def create_table(templates, department_name):
    """Create DataFrame from templates"""

    table_data = []
    for t in templates:
        table_data.append({
            'Template ID': t.get('templateId') or t.get('id'),
            'MongoDB ID': t.get('id'),
            'Name': t.get('name'),
            'Departments': ', '.join(sorted(t.get('departments', []))),
            'Communication Type': t.get('purposeSubType'),
            'Status': t.get('status'),
            'Category': t.get('category', 'N/A'),
            'Visible on UI': t.get('visibleOnUI'),
            'Created Date': pd.to_datetime(t.get('createdTime'), unit='ms').strftime('%Y-%m-%d %H:%M:%S') if t.get('createdTime') else 'N/A',
            'Modified Date': pd.to_datetime(t.get('modifiedTime'), unit='ms').strftime('%Y-%m-%d %H:%M:%S') if t.get('modifiedTime') else 'N/A',
            'Description': (t.get('description') or '')[:100],
            'Edit URL': f"https://preprodapp.tekioncloud.com/templates/edit/{t.get('templateId') or t.get('id')}"
        })

    df = pd.DataFrame(table_data)
    df = df.sort_values(['Communication Type', 'Name'])

    return df


async def main():
    logger.info("="*100)
    logger.info("🔍 SERVICE & PARTS ANALYSIS - USING EXISTING TAB ONLY")
    logger.info("="*100)

    playwright = await async_playwright().start()

    try:
        # Connect to existing browser via CDP
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]

        # USE EXISTING TAB - Don't create new one!
        page = None
        for p in context.pages:
            if 'templates/list' in p.url:
                page = p
                logger.info("✅ Using EXISTING templates tab")
                break

        if not page:
            logger.error("❌ No templates tab found! Please navigate to templates page manually.")
            logger.error("   Go to: https://preprodapp.tekioncloud.com/templates/list")
            await playwright.stop()
            return

        # Bring existing tab to front
        await page.bring_to_front()
        logger.info("✅ Using existing tab - NO new tabs created")

        results = {}
        previous_count = None  # Track count from previous department

        # ========================================================================
        # SERVICE DEPARTMENT
        # ========================================================================

        logger.info("\n" + "="*100)
        logger.info("📥 FETCHING SERVICE DEPARTMENT")
        logger.info("="*100)

        success, results_count, tab_count = await switch_to_department(page, "Service", previous_count)

        if success:
            logger.info(f"\n📊 Expected: {results_count} results, {tab_count} in active tab")

            # Fetch templates via direct API call
            service_templates = await fetch_templates_via_api(page, "SERVICE", tab_count)

            if service_templates:
                service_df = await create_table(service_templates, "SERVICE")
                results['SERVICE'] = {
                    'templates': service_templates,
                    'dataframe': service_df,
                    'count': len(service_templates),
                    'results_count': results_count,
                    'tab_count': tab_count
                }

                logger.info(f"\n✅ SERVICE: Captured {len(service_templates)} templates")
                logger.info(f"   Matches UI count: {'✅' if len(service_templates) == tab_count else '❌'}")

                # Track this count for next department
                previous_count = tab_count


        # ========================================================================
        # PARTS DEPARTMENT
        # ========================================================================

        logger.info("\n" + "="*100)
        logger.info("📥 FETCHING PARTS DEPARTMENT")
        logger.info("="*100)

        success, results_count, tab_count = await switch_to_department(page, "Parts", previous_count)

        if success:
            logger.info(f"\n📊 Expected: {results_count} results, {tab_count} in active tab")

            # Fetch templates via direct API call
            parts_templates = await fetch_templates_via_api(page, "PARTS", tab_count)

            if parts_templates:
                parts_df = await create_table(parts_templates, "PARTS")
                results['PARTS'] = {
                    'templates': parts_templates,
                    'dataframe': parts_df,
                    'count': len(parts_templates),
                    'results_count': results_count,
                    'tab_count': tab_count
                }

                logger.info(f"\n✅ PARTS: Captured {len(parts_templates)} templates")
                logger.info(f"   Matches UI count: {'✅' if len(parts_templates) == tab_count else '❌'}")


        # ========================================================================
        # SAVE & SUMMARY
        # ========================================================================

        if results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            logger.info(f"\n{'='*100}")
            logger.info("💾 SAVING FILES")
            logger.info(f"{'='*100}")

            for dept_name, dept_data in results.items():
                df = dept_data['dataframe']

                csv_file = f"{dept_name}_analyzed_{timestamp}.csv"
                df.to_csv(csv_file, index=False)
                logger.info(f"✅ {dept_name}: {csv_file}")

            logger.info(f"\n{'='*100}")
            logger.info("📊 FINAL SUMMARY")
            logger.info(f"{'='*100}")

            for dept_name, dept_data in results.items():
                logger.info(f"\n{dept_name}:")
                logger.info(f"  UI Results Count: {dept_data['results_count']}")
                logger.info(f"  Active Tab Count: {dept_data['tab_count']}")
                logger.info(f"  Templates Captured: {dept_data['count']}")
                logger.info(f"  Match: {'✅' if dept_data['count'] == dept_data['tab_count'] else '❌ MISMATCH!'}")

    finally:
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())

