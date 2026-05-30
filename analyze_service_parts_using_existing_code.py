#!/usr/bin/env python3
"""
Analyze Service & Parts Templates Using EXISTING Working Code
Uses the proven API interception method from fetch_service_templates_complete.py
"""

import asyncio
import sys
import os
import json
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright
from smart_template_filter_builder import SmartTemplateFilterBuilder
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def fetch_department_templates(page, department_name):
    """
    Fetch templates using the EXISTING working method:
    - API interception
    - Direct API call with payload
    """
    
    logger.info(f"\n{'='*80}")
    logger.info(f"📥 FETCHING {department_name} TEMPLATES")
    logger.info(f"{'='*80}")
    
    # Method 1: Try direct API call (fastest)
    logger.info("\n🔍 Method 1: Direct API call...")
    
    builder = SmartTemplateFilterBuilder()
    payload = builder.build_grouped_payload(
        departments=[department_name],
        comm_types=["EMAIL", "TEXT", "CHAT"],
        status=["ACTIVE"],
        max_results=500
    )
    
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
        
        if templates:
            logger.info(f"  ✅ Found {len(templates)} templates via direct API")
            return templates
        
    except Exception as e:
        logger.warning(f"  ⚠️  Direct API failed: {e}")
    
    
    # Method 2: API Interception (fallback)
    logger.info("\n🔍 Method 2: API interception...")
    
    templates = []
    response_received = asyncio.Event()
    
    async def handle_response(response):
        nonlocal templates
        if '/api/templatestore/u/search' in response.url:
            try:
                data = await response.json()
                
                if 'data' in data and 'hits' in data['data']:
                    hits = data['data']['hits']
                    
                    if hits and len(hits) > 0:
                        # Filter for this department
                        dept_templates = [
                            h for h in hits 
                            if department_name in h.get('departments', [])
                        ]
                        
                        if dept_templates:
                            templates.extend(dept_templates)
                            logger.info(f"  ✅ Captured {len(dept_templates)} templates")
                            response_received.set()
            except:
                pass
    
    page.on('response', handle_response)
    
    # Reload to trigger API call
    logger.info("  Reloading page...")
    await page.reload(wait_until='domcontentloaded')
    
    try:
        await asyncio.wait_for(response_received.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("  ⚠️  Timeout waiting for API response")
    
    page.remove_listener('response', handle_response)
    
    return templates


async def create_analysis_table(templates, department_name):
    """Create DataFrame from templates (using existing format)"""
    
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
    logger.info("🔍 SERVICE & PARTS ANALYSIS - USING EXISTING WORKING CODE")
    logger.info("="*100)

    playwright = await async_playwright().start()

    try:
        # Connect to existing browser
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]

        # Find or create templates page
        page = None
        for p in context.pages:
            if 'templates/list' in p.url:
                page = p
                logger.info(f"✅ Found existing templates page")
                break

        if not page:
            logger.info("📄 Creating new templates page...")
            page = await context.new_page()
            await page.goto("https://preprodapp.tekioncloud.com/templates/list")
            await page.wait_for_load_state('networkidle')

        await page.bring_to_front()

        results = {}

        # ========================================================================
        # SERVICE DEPARTMENT
        # ========================================================================

        service_templates = await fetch_department_templates(page, "SERVICE")

        if service_templates:
            service_df = await create_analysis_table(service_templates, "SERVICE")
            results['SERVICE'] = {
                'templates': service_templates,
                'dataframe': service_df,
                'count': len(service_templates)
            }

            logger.info(f"\n✅ SERVICE: {len(service_templates)} templates")
            logger.info(f"   Email: {len(service_df[service_df['Communication Type'] == 'EMAIL'])}")
            logger.info(f"   Text: {len(service_df[service_df['Communication Type'] == 'TEXT'])}")
            logger.info(f"   Chat: {len(service_df[service_df['Communication Type'] == 'CHAT'])}")


        # ========================================================================
        # PARTS DEPARTMENT
        # ========================================================================

        parts_templates = await fetch_department_templates(page, "PARTS")

        if parts_templates:
            parts_df = await create_analysis_table(parts_templates, "PARTS")
            results['PARTS'] = {
                'templates': parts_templates,
                'dataframe': parts_df,
                'count': len(parts_templates)
            }

            logger.info(f"\n✅ PARTS: {len(parts_templates)} templates")
            logger.info(f"   Email: {len(parts_df[parts_df['Communication Type'] == 'EMAIL'])}")
            logger.info(f"   Text: {len(parts_df[parts_df['Communication Type'] == 'TEXT'])}")
            logger.info(f"   Chat: {len(parts_df[parts_df['Communication Type'] == 'CHAT'])}")


        # ========================================================================
        # SAVE RESULTS
        # ========================================================================

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"\n{'='*100}")
        logger.info("💾 SAVING FILES")
        logger.info(f"{'='*100}")

        for dept_name, dept_data in results.items():
            df = dept_data['dataframe']

            # CSV
            csv_file = f"{dept_name}_analysis_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            logger.info(f"✅ {dept_name} CSV: {csv_file}")

            # Excel
            excel_file = f"{dept_name}_analysis_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False)
            logger.info(f"✅ {dept_name} Excel: {excel_file}")

            # JSON
            json_file = f"{dept_name}_analysis_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(dept_data['templates'], f, indent=2)
            logger.info(f"✅ {dept_name} JSON: {json_file}")


        # Combined summary
        logger.info(f"\n{'='*100}")
        logger.info("📊 ANALYSIS COMPLETE!")
        logger.info(f"{'='*100}")
        logger.info(f"\nTotal templates analyzed: {sum(d['count'] for d in results.values())}")
        for dept_name, dept_data in results.items():
            logger.info(f"  {dept_name}: {dept_data['count']} templates")

    finally:
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())

