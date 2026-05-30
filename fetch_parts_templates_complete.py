#!/usr/bin/env python3
"""
Automated PARTS Templates Table Generator
Switches to PARTS department and captures all templates
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
    logger.info("🚀 AUTOMATED PARTS TEMPLATES TABLE GENERATOR")
    logger.info("=" * 80)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Step 1: Open template list page
    logger.info("\n📂 Step 1: Opening template list page...")
    page = await context.new_page()
    await page.goto("https://preprodapp.tekioncloud.com/templates/list", wait_until='domcontentloaded', timeout=15000)
    await asyncio.sleep(3)
    logger.info("✅ Page loaded")
    
    # Step 2: Switch to PARTS department
    logger.info("\n🔄 Step 2: Switching to PARTS department...")
    
    # Use working Ant Design dropdown method
    switched = False
    
    try:
        # Click the dropdown trigger
        clicked = await page.evaluate("""
            () => {
                const trigger = document.querySelector('.ant-dropdown-trigger');
                if (trigger) {
                    trigger.click();
                    return true;
                }
                return false;
            }
        """)
        
        if clicked:
            logger.info("  Opened department dropdown")
            await asyncio.sleep(0.8)
            
            # Click on Parts option
            parts_selected = await page.evaluate("""
                () => {
                    const options = document.querySelectorAll('[class*="css-"][class*="-option"]');
                    const partsOption = Array.from(options).find(opt => 
                        opt.textContent.trim() === 'Parts' &&
                        opt.offsetParent !== null
                    );
                    
                    if (partsOption) {
                        partsOption.click();
                        return true;
                    }
                    return false;
                }
            """)
            
            if parts_selected:
                logger.info("  ✅ Selected PARTS department")
                switched = True
                await asyncio.sleep(1.5)
    except Exception as e:
        logger.info(f"  Error: {e}")
    
    if not switched:
        logger.info("  ⚠️  Could not auto-switch department")
        logger.info("  The page is open - please manually select PARTS department")
        logger.info("  Press Enter when ready...")
        input()
    
    # Step 3: Wait for templates to load
    logger.info("\n⏳ Step 3: Waiting for templates to load...")
    await asyncio.sleep(4)
    
    # Step 4: Capture templates via API interception
    logger.info("\n📥 Step 4: Capturing templates...")
    
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
                        existing_ids = {t.get('id') for t in templates}
                        new_templates = [h for h in hits if h.get('id') not in existing_ids]
                        
                        if new_templates:
                            templates.extend(new_templates)
                            logger.info(f"  ✅ Captured {len(new_templates)} templates")
                            response_received.set()
            except:
                pass
    
    page.on('response', handle_response)
    
    # Reload to trigger API call
    logger.info("  Reloading page...")
    await page.reload(wait_until='domcontentloaded')
    
    try:
        await asyncio.wait_for(response_received.wait(), timeout=15.0)
    except asyncio.TimeoutError:
        logger.warning("  Timeout waiting for API response")
    
    page.remove_listener('response', handle_response)
    
    if not templates:
        logger.error("\n❌ No templates captured!")
        await playwright.stop()
        return
    
    logger.info(f"\n✅ Successfully captured {len(templates)} PARTS templates!")
    
    # Step 5: Create table
    logger.info("\n📊 Step 5: Creating table...")
    
    table_data = []
    for t in templates:
        table_data.append({
            'Template ID': t.get('templateId') or t.get('id'),
            'MongoDB ID': t.get('id'),
            'Name': t.get('name'),
            'Departments': ', '.join(t.get('departments', [])),
            'Communication Type': t.get('purposeSubType'),
            'Status': t.get('status'),
            'Category': t.get('category', 'N/A'),
            'Visible on UI': t.get('visibleOnUI'),
            'Created Date': pd.to_datetime(t.get('createdTime'), unit='ms').strftime('%Y-%m-%d %H:%M:%S') if t.get('createdTime') else 'N/A',
            'Modified Date': pd.to_datetime(t.get('modifiedTime'), unit='ms').strftime('%Y-%m-%d %H:%M:%S') if t.get('modifiedTime') else 'N/A',
            'Description': t.get('description', ''),
            'Edit URL': f"https://preprodapp.tekioncloud.com/templates/edit/{t.get('templateId') or t.get('id')}"
        })

    df = pd.DataFrame(table_data)
    logger.info(f"✅ Table created: {len(df)} rows")

    # Step 6: Save files
    logger.info("\n💾 Step 6: Saving files...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_file = f"PARTS_templates_{timestamp}.csv"
    excel_file = f"PARTS_templates_{timestamp}.xlsx"
    json_file = f"PARTS_templates_{timestamp}.json"

    df.to_csv(csv_file, index=False)
    logger.info(f"✅ CSV: {csv_file}")

    df.to_excel(excel_file, index=False, engine='openpyxl')
    logger.info(f"✅ Excel: {excel_file}")

    with open(json_file, 'w') as f:
        json.dump(templates, f, indent=2)
    logger.info(f"✅ JSON: {json_file}")

    # Step 7: Generate HTML view
    logger.info("\n🎨 Step 7: Generating HTML view...")
    await generate_html_table(df, templates, timestamp)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📈 SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total PARTS templates: {len(df)}")

    comm_type_counts = df['Communication Type'].value_counts()
    logger.info(f"\n📧 By Communication Type:")
    for comm_type, count in comm_type_counts.items():
        logger.info(f"  {comm_type}: {count}")

    logger.info(f"\n📋 PARTS TEMPLATES:")
    logger.info("=" * 80)
    logger.info("\n" + df[['Name', 'Departments', 'Communication Type', 'Status']].to_string(index=False))

    logger.info("\n" + "=" * 80)
    logger.info("✅ COMPLETE! Files generated:")
    logger.info("=" * 80)
    logger.info(f"  📄 {csv_file}")
    logger.info(f"  📊 {excel_file}")
    logger.info(f"  📋 {json_file}")
    logger.info(f"  🌐 PARTS_templates_{timestamp}.html")

    logger.info("\n🎉 Opening HTML view in browser...")

    import subprocess
    subprocess.run(['open', f"PARTS_templates_{timestamp}.html"])

    await playwright.stop()


async def generate_html_table(df, templates, timestamp):
    """Generate beautiful HTML table"""

    html_file = f"PARTS_templates_{timestamp}.html"

    # Generate table rows
    rows_html = ""
    for _, row in df.iterrows():
        depts_badges = ' '.join([f'<span class="badge badge-dept">{d.strip()}</span>' for d in row['Departments'].split(',')])

        rows_html += f"""
                    <tr>
                        <td class="template-name">{row['Name']}</td>
                        <td class="template-id">{row['Template ID']}</td>
                        <td>{depts_badges}</td>
                        <td><span class="badge badge-email">{row['Communication Type']}</span></td>
                        <td><span class="badge badge-active">{row['Status']}</span></td>
                        <td class="date">{row['Created Date'][:16] if row['Created Date'] != 'N/A' else 'N/A'}</td>
                        <td class="date">{row['Modified Date'][:16] if row['Modified Date'] != 'N/A' else 'N/A'}</td>
                        <td><a href="{row['Edit URL']}" class="link-btn" target="_blank">Edit</a></td>
                    </tr>"""

    comm_type_counts = df['Communication Type'].value_counts()
    comm_type_summary = ' / '.join([f"{t}: {c}" for t, c in comm_type_counts.items()])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PARTS Department Templates</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; font-weight: 700; }}
        .header p {{ font-size: 1.1em; opacity: 0.9; }}
        .stats {{ display: flex; justify-content: space-around; padding: 20px; background: #f8f9fa; border-bottom: 2px solid #e9ecef; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #ff6b6b; }}
        .stat-label {{ color: #6c757d; font-size: 0.9em; margin-top: 5px; }}
        .search-box {{ padding: 20px; background: #f8f9fa; border-bottom: 2px solid #e9ecef; }}
        .search-box input {{ width: 100%; padding: 12px 20px; border: 2px solid #ff6b6b; border-radius: 25px; font-size: 16px; outline: none; }}
        .search-box input:focus {{ box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1); }}
        .table-wrapper {{ overflow-x: auto; padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        thead {{ background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); color: white; position: sticky; top: 0; z-index: 10; }}
        th {{ padding: 15px 12px; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 12px; }}
        td {{ padding: 12px; border-bottom: 1px solid #e9ecef; }}
        tr:hover {{ background-color: #f8f9fa; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
        .badge-active {{ background: #d4edda; color: #155724; }}
        .badge-email {{ background: #d1ecf1; color: #0c5460; }}
        .badge-dept {{ background: #ffe0e0; color: #8b0000; margin: 2px; }}
        .link-btn {{ display: inline-block; padding: 6px 12px; background: #ff6b6b; color: white; text-decoration: none; border-radius: 6px; font-size: 12px; transition: all 0.3s; }}
        .link-btn:hover {{ background: #ee5a6f; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
        .template-name {{ font-weight: 600; color: #2c3e50; }}
        .template-id {{ font-family: 'Courier New', monospace; font-size: 12px; color: #6c757d; }}
        .date {{ font-size: 12px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 PARTS Department Templates</h1>
            <p>Comprehensive Templates Table</p>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(df)}</div>
                <div class="stat-label">Total Templates</div>
            </div>
            <div class="stat">
                <div class="stat-value">{comm_type_summary}</div>
                <div class="stat-label">Communication Types</div>
            </div>
            <div class="stat">
                <div class="stat-value">ACTIVE</div>
                <div class="stat-label">Status</div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Search templates..." onkeyup="searchTable()">
        </div>

        <div class="table-wrapper">
            <table id="templatesTable">
                <thead>
                    <tr>
                        <th>Template Name</th>
                        <th>Template ID</th>
                        <th>Departments</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Modified</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
{rows_html}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function searchTable() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('templatesTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                const row = tr[i];
                const cells = row.getElementsByTagName('td');
                let found = false;

                for (let j = 0; j < cells.length; j++) {{
                    const cell = cells[j];
                    if (cell) {{
                        const textValue = cell.textContent || cell.innerText;
                        if (textValue.toUpperCase().indexOf(filter) > -1) {{
                            found = true;
                            break;
                        }}
                    }}
                }}

                row.style.display = found ? '' : 'none';
            }}
        }}
    </script>
</body>
</html>"""

    with open(html_file, 'w') as f:
        f.write(html_content)

    logger.info(f"✅ HTML: {html_file}")


if __name__ == "__main__":
    asyncio.run(main())
