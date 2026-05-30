#!/usr/bin/env python3
"""
Detect Grid Details - Deep analysis of the role="grid" structure
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("🔍 Deep Grid Structure Analysis\n")
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            
            page = None
            for p in context.pages:
                if '/templates/list' in p.url and '/edit/' not in p.url:
                    page = p
                    break
            
            if not page:
                page = context.pages[0]
                await page.goto("https://preprodapp.tekioncloud.com/templates/list")
                await asyncio.sleep(3)
            
            await page.bring_to_front()
            print(f"✅ Page: {page.url}\n")
            
            # Deep grid analysis
            print("📊 Analyzing role='grid' structure...\n")
            
            grid_structure = await page.evaluate("""
                () => {
                    const result = {
                        grid_container: null,
                        headers: [],
                        rows: [],
                        columns_count: 0,
                        rows_count: 0
                    };
                    
                    // Find the main grid
                    const grid = document.querySelector('[role="grid"]');
                    if (!grid) return result;
                    
                    result.grid_container = {
                        className: grid.className.substring(0, 100),
                        html: grid.outerHTML.substring(0, 500)
                    };
                    
                    // Find headers (columnheader role or first row)
                    const headers = grid.querySelectorAll('[role="columnheader"]');
                    if (headers.length > 0) {
                        headers.forEach((header, i) => {
                            result.headers.push({
                                index: i,
                                text: header.textContent.trim(),
                                ariaLabel: header.getAttribute('aria-label'),
                                className: header.className.substring(0, 80),
                                hasSort: header.querySelector('[class*="sort"]') !== null,
                                hasCheckbox: header.querySelector('input[type="checkbox"]') !== null
                            });
                        });
                    } else {
                        // Try to find headers in first row
                        const firstRow = grid.querySelector('[role="row"]');
                        if (firstRow) {
                            const cells = firstRow.querySelectorAll('[role="gridcell"], [role="columnheader"]');
                            cells.forEach((cell, i) => {
                                result.headers.push({
                                    index: i,
                                    text: cell.textContent.trim().substring(0, 50),
                                    className: cell.className.substring(0, 80),
                                    role: cell.getAttribute('role')
                                });
                            });
                        }
                    }
                    
                    result.columns_count = result.headers.length;
                    
                    // Find all rows
                    const rows = grid.querySelectorAll('[role="row"]');
                    result.rows_count = rows.length;
                    
                    // Get first 5 sample rows
                    rows.forEach((row, rowIndex) => {
                        if (rowIndex < 5) {
                            const cells = row.querySelectorAll('[role="gridcell"], [role="columnheader"]');
                            const rowData = {
                                index: rowIndex,
                                cells: [],
                                className: row.className.substring(0, 80),
                                hasCheckbox: row.querySelector('input[type="checkbox"]') !== null,
                                hasActions: row.querySelector('button, [class*="action"]') !== null
                            };
                            
                            cells.forEach((cell, cellIndex) => {
                                const text = cell.textContent.trim();
                                rowData.cells.push({
                                    index: cellIndex,
                                    text: text.substring(0, 80),
                                    role: cell.getAttribute('role'),
                                    hasCheckbox: cell.querySelector('input[type="checkbox"]') !== null,
                                    hasButton: cell.querySelector('button') !== null,
                                    hasLink: cell.querySelector('a') !== null,
                                    className: cell.className.substring(0, 60)
                                });
                            });
                            
                            result.rows.push(rowData);
                        }
                    });
                    
                    return result;
                }
            """)
            
            print("=" * 120)
            print("📋 GRID STRUCTURE")
            print("=" * 120)
            print()
            
            if grid_structure['grid_container']:
                print("✅ Grid Found!\n")
                print(f"📊 Columns: {grid_structure['columns_count']}")
                print(f"📝 Total Rows: {grid_structure['rows_count']}\n")
                
                # Show headers
                print("📋 Column Headers:")
                print("-" * 120)
                for header in grid_structure['headers']:
                    sort_icon = "↕️" if header.get('hasSort') else ""
                    checkbox_icon = "☑️" if header.get('hasCheckbox') else ""
                    text = header['text'] if header['text'] else "(empty)"
                    print(f"  [{header['index']}] {checkbox_icon}{sort_icon} {text}")
                    if header.get('ariaLabel'):
                        print(f"       Aria-Label: {header['ariaLabel']}")
                print()
                
                # Show sample rows
                print("📋 Sample Data Rows:")
                print("-" * 120)
                for row in grid_structure['rows']:
                    checkbox = "☑️" if row['hasCheckbox'] else "  "
                    actions = "⚙️" if row['hasActions'] else "  "
                    print(f"\nRow {row['index']}: {checkbox} {actions}")
                    
                    for cell in row['cells']:
                        cell_checkbox = "☑️" if cell['hasCheckbox'] else ""
                        cell_button = "🔘" if cell['hasButton'] else ""
                        cell_link = "🔗" if cell['hasLink'] else ""
                        icons = f"{cell_checkbox}{cell_button}{cell_link} " if any([cell_checkbox, cell_button, cell_link]) else ""
                        
                        text = cell['text'] if cell['text'] else "(empty)"
                        print(f"     [{cell['index']}] {icons}{text[:70]}")
                print()
                
            else:
                print("❌ No grid with role='grid' found\n")
            
            # Save detailed results
            filename = f"grid_structure_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(grid_structure, f, indent=2)
            
            print(f"💾 Detailed results saved to: {filename}")
            
            print("\n" + "=" * 120)
            print("✅ ANALYSIS COMPLETE")
            print("=" * 120)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
