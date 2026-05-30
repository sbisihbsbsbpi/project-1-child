#!/usr/bin/env python3
"""
Analyze Department Filter Behavior
Compares what templates appear for SALES vs SERVICE vs PARTS
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def main():
    print("=" * 80)
    print("🔍 ANALYZING DEPARTMENT FILTER BEHAVIOR")
    print("=" * 80)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Open fresh template list page
    page = await context.new_page()
    await page.goto("https://preprodapp.tekioncloud.com/templates/list", wait_until='domcontentloaded', timeout=15000)
    await asyncio.sleep(3)
    
    print("\n✅ Template list page loaded")
    
    # Function to capture templates
    async def capture_templates_for_department(dept_name):
        print(f"\n{'=' * 80}")
        print(f"📋 CAPTURING {dept_name} DEPARTMENT")
        print("=" * 80)
        
        templates = []
        response_received = asyncio.Event()
        
        async def handle_response(response):
            nonlocal templates
            if '/api/templatestore/u/search' in response.url:
                try:
                    data = await response.json()
                    
                    if 'data' in data and 'hits' in data['data']:
                        hits = data['data']['hits']
                        if hits and len(hits) > 0 and len(templates) == 0:
                            templates.extend(hits)
                            print(f"  ✅ Captured {len(hits)} templates")
                            response_received.set()
                except:
                    pass
        
        # Click on department filter
        try:
            # First, find the current department chip/filter
            current_dept = await page.evaluate("""
                () => {
                    const chips = Array.from(document.querySelectorAll('[class*="chip"], [class*="tag"], [class*="badge"]'));
                    const deptChip = chips.find(el => 
                        ['Sales', 'Service', 'Parts', 'General', 'Accounting'].includes(el.textContent.trim())
                    );
                    return deptChip ? deptChip.textContent.trim() : null;
                }
            """)
            
            print(f"  Current filter: {current_dept}")
            
            if current_dept and current_dept != dept_name:
                print(f"  Clicking on '{current_dept}' to open dropdown...")
                await page.click(f'text={current_dept}', timeout=3000)
                await asyncio.sleep(0.5)
                
                print(f"  Selecting '{dept_name}'...")
                await page.click(f'text={dept_name}', timeout=3000)
                await asyncio.sleep(1)
                print(f"  ✅ Switched to {dept_name}")
            else:
                print(f"  Already on {dept_name}")
        
        except Exception as e:
            print(f"  ⚠️  Could not switch department: {e}")
            print(f"  Proceeding with current filter...")
        
        # Set up listener
        page.on('response', handle_response)
        
        # Reload to trigger API
        print(f"  Reloading page...")
        await page.reload(wait_until='domcontentloaded')
        
        try:
            await asyncio.wait_for(response_received.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            print(f"  ⚠️  Timeout")
        
        page.remove_listener('response', handle_response)
        
        return templates
    
    # Capture for each department
    departments = ['Sales', 'Service', 'Parts']
    all_results = {}
    
    for dept in departments:
        templates = await capture_templates_for_department(dept)
        all_results[dept] = templates
    
    # Analysis
    print("\n" + "=" * 80)
    print("📊 ANALYSIS")
    print("=" * 80)
    
    for dept, templates in all_results.items():
        print(f"\n{dept} Department: {len(templates)} templates")
        
        if templates:
            # Count by department assignment
            dept_counts = {}
            for t in templates:
                depts_str = ', '.join(sorted(t.get('departments', [])))
                dept_counts[depts_str] = dept_counts.get(depts_str, 0) + 1
            
            print(f"  Department assignments:")
            for dept_combo, count in sorted(dept_counts.items()):
                print(f"    {dept_combo}: {count}")
            
            # Show first 5 template names
            print(f"  First 5 templates:")
            for t in templates[:5]:
                print(f"    - {t.get('name')}")
    
    # Compare templates between departments
    print("\n" + "=" * 80)
    print("🔍 COMPARISON")
    print("=" * 80)
    
    if 'Sales' in all_results and 'Service' in all_results:
        sales_ids = {t.get('id') for t in all_results['Sales']}
        service_ids = {t.get('id') for t in all_results['Service']}
        
        print(f"\nSales templates: {len(sales_ids)}")
        print(f"Service templates: {len(service_ids)}")
        print(f"Overlap: {len(sales_ids & service_ids)}")
        print(f"Sales only: {len(sales_ids - service_ids)}")
        print(f"Service only: {len(service_ids - sales_ids)}")
        
        if sales_ids == service_ids:
            print("\n⚠️  WARNING: Sales and Service show IDENTICAL templates!")
            print("    This means the department filter might not be working as expected,")
            print("    or all templates are multi-department.")
        else:
            print("\n✅ Sales and Service show DIFFERENT templates")
            
            # Show Service-only templates
            service_only = service_ids - sales_ids
            if service_only:
                print(f"\n📋 SERVICE-ONLY Templates ({len(service_only)}):")
                for t in all_results['Service']:
                    if t.get('id') in service_only:
                        print(f"  - {t.get('name')} (Depts: {', '.join(t.get('departments', []))})")
    
    # Save detailed comparison
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"department_comparison_{timestamp}.json"
    
    comparison = {
        'timestamp': timestamp,
        'departments': {}
    }
    
    for dept, templates in all_results.items():
        comparison['departments'][dept] = {
            'count': len(templates),
            'template_ids': [t.get('id') for t in templates],
            'templates': [{
                'id': t.get('id'),
                'templateId': t.get('templateId'),
                'name': t.get('name'),
                'departments': t.get('departments')
            } for t in templates]
        }
    
    with open(filename, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\n💾 Detailed comparison saved to: {filename}")
    
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
