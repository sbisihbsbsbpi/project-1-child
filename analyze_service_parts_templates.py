#!/usr/bin/env python3
"""
Analyze Service & Parts Department Templates
Uses existing browser tab, filters departments, and analyzes grid data
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright


async def filter_department(page, department_name: str):
    """Filter to specific department using React-Select component"""
    print(f"\n🎯 Filtering to: {department_name}")

    try:
        # Click department dropdown to open it
        print("   Opening dropdown...")
        await page.click('.ant-dropdown-trigger', timeout=5000)
        await asyncio.sleep(1)

        # Use JavaScript to interact with React-Select
        print(f"   Selecting '{department_name}' via JavaScript...")
        selected = await page.evaluate(f"""
            async (deptName) => {{
                // Find the input
                const input = document.querySelector('input[id*="departments"]');
                if (!input) return false;

                // Focus and type
                input.focus();
                input.value = deptName;

                // Trigger React onChange event
                const event = new Event('input', {{ bubbles: true }});
                input.dispatchEvent(event);

                // Wait a bit for React to update
                await new Promise(r => setTimeout(r, 500));

                // Press Enter to select
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

        await asyncio.sleep(2)

        # Close dropdown
        await page.keyboard.press('Escape')
        await asyncio.sleep(2)

        print(f"   ✅ Selected {department_name}")
        return True

    except Exception as e:
        print(f"⚠️  Error filtering to {department_name}: {e}")
        return False


async def extract_grid_data(page):
    """Extract all template data from the grid/table"""
    print("\n📊 Extracting grid data...")

    # Wait for content to load
    await asyncio.sleep(3)

    grid_data = await page.evaluate("""
        () => {
            const data = {
                templates: [],
                grid_info: {},
                raw_elements: {},
                template_names: []
            };

            // Try to find table (tbody)
            const tbody = document.querySelector('tbody');
            const rows = tbody ? tbody.querySelectorAll('tr') : [];

            if (rows.length > 0) {
                data.grid_info.type = 'table';
                data.grid_info.total_rows = rows.length;

                // Extract headers from thead
                const headers = [];
                const thead = document.querySelector('thead');
                if (thead) {
                    thead.querySelectorAll('th').forEach(th => {
                        const text = th.textContent.trim();
                        if (text) headers.push(text);
                    });
                }
                data.grid_info.headers = headers;

                // Extract row data from tbody
                rows.forEach((row, i) => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length > 0) {
                        const rowData = {
                            row_index: i,
                            cells: [],
                            raw_data: {}
                        };

                        cells.forEach((cell, cellIdx) => {
                            const text = cell.textContent.trim();
                            rowData.cells.push(text);

                            // Map to header if available
                            if (headers[cellIdx]) {
                                rowData.raw_data[headers[cellIdx]] = text;
                            }
                        });

                        // Extract template name (usually first column)
                        if (rowData.cells.length > 0) {
                            data.template_names.push(rowData.cells[0]);
                        }

                        data.templates.push(rowData);
                    }
                });
            }

            // Try card/tile view if no table
            if (data.templates.length === 0) {
                const cards = document.querySelectorAll('[class*="card"], [class*="tile"], [class*="template"]');
                if (cards.length > 0) {
                    data.grid_info.type = 'cards';
                    data.grid_info.total_cards = cards.length;

                    cards.forEach((card, i) => {
                        const cardData = {
                            index: i,
                            title: card.querySelector('h1, h2, h3, h4, h5, h6')?.textContent.trim(),
                            text: card.textContent.substring(0, 200).trim()
                        };

                        if (cardData.title) {
                            data.template_names.push(cardData.title);
                        }

                        data.templates.push(cardData);
                    });
                }
            }

            // Get all visible text for analysis
            const allText = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.offsetParent !== null && el.children.length === 0) {
                    const text = el.textContent.trim();
                    if (text && text.length > 3 && text.length < 150) {
                        allText.push(text);
                    }
                }
            });

            data.raw_elements.all_text = [...new Set(allText)];

            // Get tab count
            const activeTab = document.querySelector('[role="tab"][aria-selected="true"]');
            if (activeTab) {
                const match = activeTab.textContent.match(/\\((\\d+)\\)/);
                data.grid_info.active_tab_count = match ? parseInt(match[1]) : null;
                data.grid_info.active_tab = activeTab.textContent.trim();
            }

            return data;
        }
    """)

    return grid_data


async def main():
    print("=" * 100)
    print("🔍 SERVICE & PARTS DEPARTMENT TEMPLATE ANALYSIS")
    print("=" * 100)
    
    async with async_playwright() as playwright:
        try:
            # Connect to existing browser
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to existing browser")
            
            # Get the active context and page
            context = browser.contexts[0]
            pages = context.pages
            
            # Find templates page or create new one
            templates_page = None
            for page in pages:
                url = page.url
                if 'templates/list' in url:
                    templates_page = page
                    print(f"✅ Found templates page: {url}")
                    break
            
            if not templates_page:
                print("📄 Creating new templates page...")
                templates_page = await context.new_page()
                await templates_page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                                         wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)
            
            # Bring page to front
            await templates_page.bring_to_front()
            
            all_results = {
                "timestamp": datetime.now().isoformat(),
                "url": templates_page.url,
                "departments": {}
            }
            
            
            # ========================================================================
            # ANALYZE SERVICE DEPARTMENT
            # ========================================================================
            
            print("\n" + "=" * 100)
            print("ANALYZING: SERVICE DEPARTMENT")
            print("=" * 100)
            
            success = await filter_department(templates_page, "Service")
            
            if success:
                await asyncio.sleep(3)
                service_data = await extract_grid_data(templates_page)
                all_results["departments"]["SERVICE"] = service_data
                
                print(f"\n📊 SERVICE Department Results:")
                print(f"   Grid Type: {service_data['grid_info'].get('type', 'Unknown')}")
                print(f"   Active Tab: {service_data['grid_info'].get('active_tab', 'N/A')}")
                print(f"   Tab Count: {service_data['grid_info'].get('active_tab_count', 'N/A')}")
                print(f"   Total Items: {len(service_data['templates'])}")
                
                if service_data['grid_info'].get('headers'):
                    print(f"   Headers: {', '.join(service_data['grid_info']['headers'])}")
                
                print(f"\n   Sample Templates:")
                for template in service_data['templates'][:5]:
                    if template.get('cells'):
                        print(f"     - {' | '.join(template['cells'][:3])}")
                    elif template.get('title'):
                        print(f"     - {template['title']}")
            
            
            # ========================================================================
            # ANALYZE PARTS DEPARTMENT
            # ========================================================================
            
            print("\n" + "=" * 100)
            print("ANALYZING: PARTS DEPARTMENT")
            print("=" * 100)
            
            success = await filter_department(templates_page, "Parts")
            
            if success:
                await asyncio.sleep(3)
                parts_data = await extract_grid_data(templates_page)
                all_results["departments"]["PARTS"] = parts_data
                
                print(f"\n📊 PARTS Department Results:")
                print(f"   Grid Type: {parts_data['grid_info'].get('type', 'Unknown')}")
                print(f"   Active Tab: {parts_data['grid_info'].get('active_tab', 'N/A')}")
                print(f"   Tab Count: {parts_data['grid_info'].get('active_tab_count', 'N/A')}")
                print(f"   Total Items: {len(parts_data['templates'])}")
                
                if parts_data['grid_info'].get('headers'):
                    print(f"   Headers: {', '.join(parts_data['grid_info']['headers'])}")
                
                print(f"\n   Sample Templates:")
                for template in parts_data['templates'][:5]:
                    if template.get('cells'):
                        print(f"     - {' | '.join(template['cells'][:3])}")
                    elif template.get('title'):
                        print(f"     - {template['title']}")
            
            
            # ========================================================================
            # SAVE RESULTS
            # ========================================================================
            
            filename = f"service_parts_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(all_results, f, indent=2)
            
            print("\n" + "=" * 100)
            print("📊 COMBINED ANALYSIS SUMMARY")
            print("=" * 100)
            
            for dept, data in all_results["departments"].items():
                print(f"\n{dept}:")
                print(f"  Templates: {len(data['templates'])}")
                print(f"  Tab Count: {data['grid_info'].get('active_tab_count', 'N/A')}")
                print(f"  Grid Type: {data['grid_info'].get('type', 'N/A')}")

            print(f"\n💾 Full results saved to: {filename}")

            # Detailed text analysis
            print("\n" + "=" * 100)
            print("📝 DETAILED TEXT ANALYSIS")
            print("=" * 100)

            for dept, data in all_results["departments"].items():
                print(f"\n{dept} - All Visible Text Elements:")
                texts = data['raw_elements'].get('all_text', [])[:30]
                for i, text in enumerate(texts, 1):
                    print(f"  {i}. {text}")

            print("\n" + "=" * 100)
            print("✅ ANALYSIS COMPLETE!")
            print("=" * 100)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

