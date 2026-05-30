#!/usr/bin/env python3
"""
Smart Department Filter with Data Verification
Changes department filter and analyzes page data before/after to verify the change worked
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'automation'))

from playwright.async_api import async_playwright
from cdp_utils import get_or_navigate_to_page, print_cdp_info


async def analyze_page_data(page, label=""):
    """
    Deep analysis of page data to detect what templates are shown
    
    Returns:
        dict: Analysis of current page state
    """
    
    print(f"🔍 Analyzing page data {label}...")
    
    data = await page.evaluate("""
        () => {
            const analysis = {
                timestamp: new Date().toISOString(),
                
                // Tab counts
                tabs: [],
                
                // Template cards/rows
                templates: [],
                
                // Table data
                table_info: {
                    headers: [],
                    row_count: 0,
                    visible_rows: []
                },
                
                // Department badges/tags visible
                department_badges: [],
                
                // Current filter state
                current_filter: null
            };
            
            // 1. Get tab counts
            document.querySelectorAll('[role="tab"]').forEach(tab => {
                const text = tab.textContent.trim();
                const match = text.match(/(.+?)\\s*\\((\\d+)\\)/);
                analysis.tabs.push({
                    label: match ? match[1] : text,
                    count: match ? parseInt(match[2]) : 0,
                    active: tab.getAttribute('aria-selected') === 'true'
                });
            });
            
            // 2. Get current filter selection
            const trigger = document.querySelector('.ant-dropdown-trigger');
            if (trigger) {
                analysis.current_filter = trigger.textContent.trim().split('\\n').filter(t => t.length > 0);
            }
            
            // 3. Scan for table rows (ReactTable structure)
            const table = document.querySelector('.ReactTable');
            if (table) {
                // Get headers
                table.querySelectorAll('.rt-thead .rt-th').forEach(th => {
                    const text = th.textContent.trim();
                    if (text && text !== '-sort' && text !== '-filters') {
                        analysis.table_info.headers.push(text);
                    }
                });
                
                // Get visible rows
                const rows = table.querySelectorAll('.rt-tbody .rt-tr-group');
                analysis.table_info.row_count = rows.length;
                
                rows.forEach((row, idx) => {
                    if (idx < 10) { // First 10 rows
                        const cells = row.querySelectorAll('.rt-td');
                        const rowData = [];
                        
                        cells.forEach(cell => {
                            const text = cell.textContent.trim();
                            if (text) {
                                rowData.push(text.substring(0, 100));
                            }
                        });
                        
                        if (rowData.length > 0) {
                            analysis.table_info.visible_rows.push(rowData);
                        }
                    }
                });
            }
            
            // 4. Look for department badges/tags in the content
            const badgeSelectors = [
                '[class*="badge"]',
                '[class*="tag"]',
                '[class*="department"]',
                '[class*="dept"]'
            ];
            
            badgeSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(badge => {
                    const text = badge.textContent.trim();
                    if (text && text.length < 30 && badge.offsetParent !== null) {
                        const lower = text.toLowerCase();
                        if (lower.includes('sales') || lower.includes('service') || lower.includes('parts')) {
                            analysis.department_badges.push(text);
                        }
                    }
                });
            });
            
            // 5. Extract template names from visible content
            const templateNameSelectors = [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                '[class*="title"]',
                '[class*="name"]',
                '.rt-td:first-child' // First column often has template name
            ];
            
            templateNameSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    const text = el.textContent.trim();
                    if (text && 
                        text.length > 5 && 
                        text.length < 150 &&
                        el.offsetParent !== null &&
                        !text.includes('\\n') &&
                        !text.includes('(')) {
                        
                        // Avoid duplicates
                        if (!analysis.templates.includes(text)) {
                            analysis.templates.push(text);
                        }
                    }
                });
            });
            
            return analysis;
        }
    """)
    
    # Print summary
    print(f"\n   📊 Tab Counts:")
    for tab in data['tabs']:
        active = "✓" if tab['active'] else " "
        print(f"      [{active}] {tab['label']}: {tab['count']}")
    
    print(f"\n   🎛️  Current Filter: {', '.join(data['current_filter']) if data['current_filter'] else 'None'}")
    print(f"\n   📋 Table Info:")
    print(f"      Headers: {len(data['table_info']['headers'])}")
    print(f"      Rows: {data['table_info']['row_count']}")
    
    if data['table_info']['visible_rows']:
        print(f"\n   📄 Sample Rows (first 3):")
        for i, row in enumerate(data['table_info']['visible_rows'][:3], 1):
            print(f"      {i}. {' | '.join(row[:3])}")  # First 3 columns
    
    if data['department_badges']:
        print(f"\n   🏷️  Department Badges: {', '.join(set(data['department_badges'][:10]))}")
    
    print(f"\n   📝 Templates Found: {len(data['templates'])}")
    if data['templates']:
        print(f"      Sample: {', '.join(data['templates'][:5])}")
    
    print()
    
    return data


async def compare_page_data(before, after):
    """
    Compare page data before and after filter change
    
    Returns:
        dict: Comparison results with verification status
    """
    
    print("=" * 100)
    print("📊 DATA COMPARISON & VERIFICATION")
    print("=" * 100)
    print()
    
    comparison = {
        'filter_changed': False,
        'data_changed': False,
        'tab_counts_changed': False,
        'table_changed': False,
        'details': {}
    }
    
    # 1. Compare filters
    before_filter = set(before['current_filter']) if before['current_filter'] else set()
    after_filter = set(after['current_filter']) if after['current_filter'] else set()
    
    comparison['filter_changed'] = before_filter != after_filter
    comparison['details']['filter'] = {
        'before': sorted(before_filter),
        'after': sorted(after_filter),
        'changed': comparison['filter_changed']
    }
    
    print(f"1️⃣  FILTER CHANGE:")
    print(f"   Before: {', '.join(sorted(before_filter))}")
    print(f"   After:  {', '.join(sorted(after_filter))}")
    print(f"   Status: {'✅ CHANGED' if comparison['filter_changed'] else '❌ NO CHANGE'}")
    print()
    
    # 2. Compare tab counts
    tab_changes = []
    for i, (b_tab, a_tab) in enumerate(zip(before['tabs'], after['tabs'])):
        if b_tab['count'] != a_tab['count']:
            tab_changes.append({
                'tab': b_tab['label'],
                'before': b_tab['count'],
                'after': a_tab['count'],
                'delta': a_tab['count'] - b_tab['count']
            })
    
    comparison['tab_counts_changed'] = len(tab_changes) > 0
    comparison['details']['tab_changes'] = tab_changes
    
    print(f"2️⃣  TAB COUNT CHANGES:")
    if tab_changes:
        for change in tab_changes:
            delta_str = f"+{change['delta']}" if change['delta'] > 0 else str(change['delta'])
            print(f"   {change['tab']}: {change['before']} → {change['after']} ({delta_str})")
        print(f"   Status: ✅ CHANGED")
    else:
        print(f"   Status: ⚠️  NO CHANGE")
    print()
    
    # 3. Compare table row count
    before_rows = before['table_info']['row_count']
    after_rows = after['table_info']['row_count']
    
    comparison['table_changed'] = before_rows != after_rows
    comparison['details']['table'] = {
        'before_rows': before_rows,
        'after_rows': after_rows,
        'delta': after_rows - before_rows
    }
    
    print(f"3️⃣  TABLE ROW COUNT:")
    print(f"   Before: {before_rows} rows")
    print(f"   After:  {after_rows} rows")
    delta_str = f"+{after_rows - before_rows}" if after_rows > before_rows else str(after_rows - before_rows)
    print(f"   Delta:  {delta_str}")
    print(f"   Status: {'✅ CHANGED' if comparison['table_changed'] else '⚠️  NO CHANGE'}")
    print()

    # 4. Overall verification
    comparison['data_changed'] = (
        comparison['tab_counts_changed'] or
        comparison['table_changed']
    )

    print(f"4️⃣  OVERALL VERIFICATION:")
    print(f"   Filter Updated:     {'✅ YES' if comparison['filter_changed'] else '❌ NO'}")
    print(f"   Data Changed:       {'✅ YES' if comparison['data_changed'] else '❌ NO'}")
    print()

    if comparison['filter_changed'] and comparison['data_changed']:
        print("🎉 SUCCESS: Filter change successfully triggered data update!")
    elif comparison['filter_changed'] and not comparison['data_changed']:
        print("⚠️  WARNING: Filter changed but data did not update. Possible issues:")
        print("   - Page may need more time to reload")
        print("   - API call may have failed")
        print("   - All departments may have same data")
    else:
        print("❌ FAILURE: Filter did not change properly")

    print()
    print("=" * 100)

    return comparison


async def change_department_with_verification(
    departments_to_select=['Service', 'Parts'],
    departments_to_unselect=['Sales'],
    wait_seconds=20
):
    """
    Change department filter and verify data actually changed
    """

    print("=" * 100)
    print("🎯 SMART DEPARTMENT FILTER WITH VERIFICATION")
    print("=" * 100)
    print(f"To Select: {', '.join(departments_to_select)}")
    print(f"To Unselect: {', '.join(departments_to_unselect)}")
    print("=" * 100)
    print()

    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser via CDP")
            print_cdp_info(browser)
            print()

            page = await get_or_navigate_to_page(
                browser,
                "https://preprodapp.tekioncloud.com/templates/list",
                wait_for_load=True
            )

            # ============================================
            # STEP 1: ANALYZE BEFORE
            # ============================================
            print("=" * 100)
            print("STEP 1: ANALYZE PAGE BEFORE FILTER CHANGE")
            print("=" * 100)

            before_data = await analyze_page_data(page, "(BEFORE)")

            # ============================================
            # STEP 2: CHANGE FILTER
            # ============================================
            print("=" * 100)
            print("STEP 2: CHANGING DEPARTMENT FILTER")
            print("=" * 100)
            print()

            # Open dropdown
            print("🖱️  Opening department dropdown...")
            await page.click('.ant-dropdown-trigger', timeout=5000)
            await asyncio.sleep(2)
            print("   ✅ Opened\n")

            # Detect checkboxes
            print("📋 Detecting department checkboxes...")
            checkboxes = await page.evaluate("""
                () => {
                    const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                    if (!dropdown) return [];

                    const boxes = [];
                    const labels = dropdown.querySelectorAll('label');

                    labels.forEach((label, index) => {
                        const checkbox = label.querySelector('input[type="checkbox"]');
                        const text = label.textContent.trim();

                        if (checkbox && text) {
                            boxes.push({
                                index: index,
                                text: text,
                                checked: checkbox.checked
                            });
                        }
                    });

                    return boxes;
                }
            """)

            print(f"   Found {len(checkboxes)} checkboxes:")
            for cb in checkboxes:
                status = "☑" if cb['checked'] else "☐"
                print(f"   {status} [{cb['index']}] {cb['text']}")
            print()

            # Click checkboxes to change selection
            print("🖱️  Changing department selection...")

            for dept in departments_to_unselect:
                checkbox = next((cb for cb in checkboxes if dept.lower() in cb['text'].lower() and cb['checked']), None)
                if checkbox:
                    print(f"   Unchecking {dept} (checkbox {checkbox['index']})...")
                    await page.evaluate(f"""
                        () => {{
                            const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                            const labels = dropdown.querySelectorAll('label');
                            labels[{checkbox['index']}].click();
                        }}
                    """)
                    await asyncio.sleep(0.5)

            for dept in departments_to_select:
                checkbox = next((cb for cb in checkboxes if dept.lower() in cb['text'].lower() and not cb['checked']), None)
                if checkbox:
                    print(f"   Checking {dept} (checkbox {checkbox['index']})...")
                    await page.evaluate(f"""
                        () => {{
                            const dropdown = document.querySelector('.ant-dropdown:not([style*="display: none"])');
                            const labels = dropdown.querySelectorAll('label');
                            labels[{checkbox['index']}].click();
                        }}
                    """)
                    await asyncio.sleep(0.5)

            print()

            # Close dropdown
            print("🖱️  Closing dropdown...")
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)
            print("   ✅ Closed\n")

            # Wait for page to update
            print(f"⏳ Waiting {wait_seconds} seconds for page to update...")
            for i in range(0, wait_seconds, 5):
                remaining = wait_seconds - i
                print(f"   [{i:2d}s] Waiting... ({remaining}s remaining)")
                await asyncio.sleep(5)
            print()

            # ============================================
            # STEP 3: ANALYZE AFTER
            # ============================================
            print("=" * 100)
            print("STEP 3: ANALYZE PAGE AFTER FILTER CHANGE")
            print("=" * 100)

            after_data = await analyze_page_data(page, "(AFTER)")

            # ============================================
            # STEP 4: COMPARE & VERIFY
            # ============================================
            comparison = await compare_page_data(before_data, after_data)

            # ============================================
            # STEP 5: SAVE RESULTS
            # ============================================
            import json
            result = {
                'timestamp': datetime.now().isoformat(),
                'departments_selected': departments_to_select,
                'departments_unselected': departments_to_unselect,
                'before': before_data,
                'after': after_data,
                'comparison': comparison
            }

            filename = f"filter_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)

            print(f"💾 Full results saved to: {filename}")
            print()

            return result

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None


async def main():
    result = await change_department_with_verification(
        departments_to_select=['Service', 'Parts'],
        departments_to_unselect=['Sales'],
        wait_seconds=20
    )

    if result:
        print("=" * 100)
        print("✅ AUTOMATION COMPLETE")
        print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())

