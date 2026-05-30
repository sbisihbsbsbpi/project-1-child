#!/usr/bin/env python3
"""
Generate SERVICE Department Templates Table
Uses the smart filter builder to fetch SERVICE templates directly
"""

import asyncio
from playwright.async_api import async_playwright
from smart_template_filter_builder import SmartTemplateFilterBuilder
import pandas as pd
from datetime import datetime
import json

async def main():
    print("=" * 80)
    print("📋 FETCHING SERVICE DEPARTMENT TEMPLATES")
    print("=" * 80)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Create new page
    page = await context.new_page()
    await page.goto("https://preprodapp.tekioncloud.com/templates/list")
    await page.wait_for_load_state('networkidle')
    
    print("✅ Template list page loaded")
    
    # Build SERVICE department payload
    builder = SmartTemplateFilterBuilder()
    payload = builder.build_grouped_payload(
        departments=["SERVICE"],
        comm_types=["EMAIL", "TEXT", "CHAT"],
        status=["ACTIVE"],
        max_results=500
    )
    
    print("\n🔍 Fetching SERVICE templates via API...")
    
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
        
        if not templates:
            print("❌ No templates found for SERVICE department")
            await playwright.stop()
            return
        
        print(f"✅ Found {len(templates)} SERVICE templates")
        
        # Create table
        print("\n📊 Creating table...")
        
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
        df = df.sort_values(['Communication Type', 'Name'])
        
        # Save files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_file = f"templates_SERVICE_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        print(f"\n✅ CSV: {csv_file}")
        
        excel_file = f"templates_SERVICE_{timestamp}.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='SERVICE Templates')
            worksheet = writer.sheets['SERVICE Templates']
            for idx, col in enumerate(df.columns):
                max_len = min(max(df[col].astype(str).apply(len).max(), len(col)) + 2, 50)
                worksheet.column_dimensions[chr(65 + idx)].width = max_len
        print(f"✅ Excel: {excel_file}")
        
        json_file = f"templates_SERVICE_{timestamp}.json"
        df.to_json(json_file, orient='records', indent=2)
        print(f"✅ JSON: {json_file}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📈 SUMMARY")
        print("=" * 80)
        print(f"Total SERVICE templates: {len(df)}")
        
        print(f"\n📧 By Communication Type:")
        for comm_type, count in df['Communication Type'].value_counts().items():
            print(f"  {comm_type}: {count}")
        
        print(f"\n📋 ALL SERVICE TEMPLATES:")
        print("=" * 80)
        print(df[['Name', 'Departments', 'Communication Type']].to_string(index=False))
        
        print(f"\n✅ Files saved successfully!")
        
        # Also save the raw templates for HTML generation
        with open(f'service_templates_raw_{timestamp}.json', 'w') as f:
            json.dump(templates, f, indent=2)
        
        print(f"\n💡 Next: Generate HTML table with:")
        print(f"   python3 generate_html_table.py templates_SERVICE_{timestamp}.csv")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
