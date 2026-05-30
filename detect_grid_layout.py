#!/usr/bin/env python3
"""
Detect Grid Layout on Templates Page
Analyzing table structure, columns, rows, and data
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("🔍 Detecting Grid Layout on Templates Page\n")
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            
            # Find templates page
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
            
            # Detect grid/table structure
            print("📊 Analyzing grid layout...\n")
            
            grid_info = await page.evaluate("""
                () => {
                    const info = {
                        table_found: false,
                        grid_found: false,
                        columns: [],
                        rows: [],
                        sample_rows: [],
                        checkboxes: false,
                        actions_column: false
                    };
                    
                    // Look for table element
                    const table = document.querySelector('table');
                    if (table) {
                        info.table_found = true;
                        
                        // Get column headers
                        const headers = table.querySelectorAll('thead th, thead td');
                        headers.forEach((header, i) => {
                            const text = header.textContent.trim();
                            const ariaLabel = header.getAttribute('aria-label');
                            const classes = header.className;
                            
                            info.columns.push({
                                index: i,
                                text: text,
                                ariaLabel: ariaLabel,
                                className: classes.substring(0, 80),
                                hasCheckbox: header.querySelector('input[type="checkbox"]') !== null,
                                hasSortIcon: header.querySelector('[class*="sort"]') !== null
                            });
                        });
                        
                        // Get row count
                        const rows = table.querySelectorAll('tbody tr');
                        info.rows.push({
                            total_rows: rows.length
                        });
                        
                        // Get first 3 sample rows
                        rows.forEach((row, rowIndex) => {
                            if (rowIndex < 3) {
                                const cells = row.querySelectorAll('td');
                                const rowData = {
                                    row_index: rowIndex,
                                    cells: []
                                };
                                
                                cells.forEach((cell, cellIndex) => {
                                    rowData.cells.push({
                                        index: cellIndex,
                                        text: cell.textContent.trim().substring(0, 100),
                                        hasCheckbox: cell.querySelector('input[type="checkbox"]') !== null,
                                        hasButton: cell.querySelector('button') !== null,
                                        hasLink: cell.querySelector('a') !== null,
                                        className: cell.className.substring(0, 80)
                                    });
                                });
                                
                                info.sample_rows.push(rowData);
                            }
                        });
                        
                        // Check for checkboxes
                        info.checkboxes = table.querySelector('input[type="checkbox"]') !== null;
                        
                        // Check for actions column
                        info.actions_column = table.querySelector('td button, td [class*="action"]') !== null;
                    }
                    
                    // Look for grid/data-grid elements
                    const gridElements = document.querySelectorAll('[class*="grid"], [class*="table"], [role="grid"]');
                    if (gridElements.length > 0) {
                        info.grid_found = true;
                        info.grid_elements = [];
                        
                        gridElements.forEach((grid, i) => {
                            info.grid_elements.push({
                                index: i,
                                tag: grid.tagName,
                                role: grid.getAttribute('role'),
                                className: grid.className.substring(0, 100)
                            });
                        });
                    }
                    
                    return info;
                }
            """)
            
            print("=" * 100)
            print("📋 GRID LAYOUT DETECTION RESULTS")
            print("=" * 100)
            print()
            
            if grid_info['table_found']:
                print("✅ Table Found!\n")
                
                # Show columns
                print(f"📊 Columns ({len(grid_info['columns'])}):")
                for col in grid_info['columns']:
                    checkbox_icon = "☑️" if col['hasCheckbox'] else ""
                    sort_icon = "↕️" if col['hasSortIcon'] else ""
                    text = col['text'] if col['text'] else "(empty)"
                    print(f"   {col['index']}. {checkbox_icon}{sort_icon} {text}")
                    if col['ariaLabel']:
                        print(f"      Aria-Label: {col['ariaLabel']}")
                print()
                
                # Show row count
                if grid_info['rows']:
                    print(f"📝 Total Rows: {grid_info['rows'][0]['total_rows']}\n")
                
                # Show sample rows
                print(f"📋 Sample Rows (first 3):\n")
                for sample in grid_info['sample_rows']:
                    print(f"Row {sample['row_index']}:")
                    for cell in sample['cells']:
                        checkbox = "☑️" if cell['hasCheckbox'] else ""
                        button = "🔘" if cell['hasButton'] else ""
                        link = "🔗" if cell['hasLink'] else ""
                        icons = f"{checkbox}{button}{link} " if (checkbox or button or link) else ""
                        text = cell['text'] if cell['text'] else "(empty)"
                        print(f"   [{cell['index']}] {icons}{text[:60]}")
                    print()
                
                print(f"☑️  Has Checkboxes: {grid_info['checkboxes']}")
                print(f"⚙️  Has Actions: {grid_info['actions_column']}")
                print()
            
            if grid_info['grid_found']:
                print(f"\n✅ Grid Elements Found: {len(grid_info.get('grid_elements', []))}\n")
                for grid in grid_info.get('grid_elements', []):
                    print(f"   {grid['index']}. {grid['tag']} (role={grid['role']})")
            
            # Take screenshot
            screenshot_file = f"grid_layout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_file, full_page=True)
            print(f"\n📸 Screenshot: {screenshot_file}\n")
            
            # Save results
            filename = f"grid_layout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(grid_info, f, indent=2)
            
            print(f"💾 Results saved to: {filename}")
            
            print("\n" + "=" * 100)
            print("✅ DETECTION COMPLETE")
            print("=" * 100)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
