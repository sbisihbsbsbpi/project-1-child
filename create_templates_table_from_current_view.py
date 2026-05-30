#!/usr/bin/env python3
"""
Create Templates Table from Current View
Captures whatever templates are currently displayed and creates a table
Then you can manually change the department filter and run again to add more
"""

import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def main():
    logger.info("=" * 80)
    logger.info("📋 CAPTURING TEMPLATES FROM CURRENT VIEW")
    logger.info("=" * 80)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Find template list page
    template_page = None
    for page in context.pages:
        if 'templates/list' in page.url:
            template_page = page
            break
    
    if not template_page:
        logger.error("❌ Template list page not found")
        return
    
    logger.info(f"✅ Found template list page: {template_page.url}")
    
    # Method: Intercept the API response
    templates = []
    response_received = asyncio.Event()
    
    async def handle_response(response):
        nonlocal templates
        if '/api/templatestore/u/search' in response.url:
            try:
                data = await response.json()

                # Check if this response has actual template data
                if 'data' in data and 'hits' in data['data']:
                    hits = data['data']['hits']

                    # Only add if there are actual hits (not empty list)
                    if hits and len(hits) > 0:
                        # Avoid duplicates
                        existing_ids = {t.get('id') for t in templates}
                        new_templates = [h for h in hits if h.get('id') not in existing_ids]

                        if new_templates:
                            templates.extend(new_templates)
                            logger.info(f"  ✅ Captured {len(new_templates)} templates from API response")
                            response_received.set()
            except Exception as e:
                pass  # Ignore errors from non-search responses
    
    # Listen for responses
    template_page.on('response', handle_response)
    
    # Reload to trigger API
    logger.info("🔄 Reloading page to capture current filter...")
    await template_page.reload()
    
    # Wait for response
    try:
        await asyncio.wait_for(response_received.wait(), timeout=15.0)
    except asyncio.TimeoutError:
        logger.warning("⚠️  Timeout - no templates captured")
    
    # Remove listener
    template_page.remove_listener('response', handle_response)
    
    if not templates:
        logger.error("❌ No templates captured")
        logger.info("\nTIP: Make sure the template list is showing templates")
        logger.info("     Then run this script again")
        await playwright.stop()
        return
    
    logger.info(f"✅ Captured {len(templates)} templates")
    
    # Create table
    logger.info("\n" + "=" * 80)
    logger.info("📊 CREATING TABLE")
    logger.info("=" * 80)
    
    table_data = []
    for template in templates:
        row = {
            'Template ID': template.get('templateId') or template.get('id'),
            'MongoDB ID': template.get('id'),
            'Name': template.get('name', 'Unknown'),
            'Departments': ', '.join(template.get('departments', [])),
            'Communication Type': template.get('purposeSubType', 'N/A'),
            'Status': template.get('status', 'N/A'),
            'Category': template.get('category', 'N/A'),
            'Visible on UI': template.get('visibleOnUI', False),
            'Created Date': pd.to_datetime(template.get('createdTime'), unit='ms').strftime('%Y-%m-%d %H:%M:%S') if template.get('createdTime') else 'N/A',
            'Modified Date': pd.to_datetime(template.get('modifiedTime'), unit='ms').strftime('%Y-%m-%d %H:%M:%S') if template.get('modifiedTime') else 'N/A',
            'Description': (template.get('description') or '')[:100],
            'Edit URL': f"https://preprodapp.tekioncloud.com/templates/edit/{template.get('templateId') or template.get('id')}"
        }
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    df = df.sort_values(['Departments', 'Communication Type', 'Name'])
    
    logger.info(f"✅ Table created: {len(df)} rows × {len(df.columns)} columns")
    
    # Save files
    logger.info("\n" + "=" * 80)
    logger.info("💾 SAVING FILES")
    logger.info("=" * 80)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV
    csv_file = f"templates_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    logger.info(f"✅ CSV: {csv_file}")
    
    # Excel
    excel_file = f"templates_{timestamp}.xlsx"
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Templates')
        worksheet = writer.sheets['Templates']
        for idx, col in enumerate(df.columns):
            max_len = min(max(df[col].astype(str).apply(len).max(), len(col)) + 2, 50)
            worksheet.column_dimensions[chr(65 + idx)].width = max_len
    logger.info(f"✅ Excel: {excel_file}")
    
    # JSON
    json_file = f"templates_{timestamp}.json"
    df.to_json(json_file, orient='records', indent=2)
    logger.info(f"✅ JSON: {json_file}")
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("📈 SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total templates: {len(df)}")
    
    logger.info(f"\n📧 By Communication Type:")
    for comm_type, count in df['Communication Type'].value_counts().items():
        logger.info(f"  {comm_type}: {count}")
    
    logger.info(f"\n🏢 Departments represented:")
    all_depts = set()
    for depts in df['Departments']:
        all_depts.update([d.strip() for d in depts.split(',')])
    for dept in sorted(all_depts):
        logger.info(f"  {dept}")
    
    # Show table
    logger.info("\n" + "=" * 80)
    logger.info("📋 ALL TEMPLATES")
    logger.info("=" * 80)
    print("\n" + df[['Name', 'Departments', 'Communication Type', 'Status']].to_string(index=False))
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ DONE!")
    logger.info("=" * 80)
    logger.info("\nTIP: To add more templates:")
    logger.info("  1. Go to the template list page in your browser")
    logger.info("  2. Change the department filter (e.g., from SALES to SERVICE)")
    logger.info("  3. Run this script again")
    logger.info("  4. Combine the CSV files afterward")
    
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())
