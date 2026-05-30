#!/usr/bin/env python3
"""
Smart Department Filter with API-Based Verification
Uses API monitoring to verify filter changes (much faster and more reliable!)
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright
from cdp_utils import get_or_navigate_to_page, print_cdp_info


async def change_filter_with_api_verification(
    departments_to_select=['Service', 'Parts'],
    departments_to_unselect=['Sales']
):
    """
    Change department filter and verify using API monitoring
    """
    
    print("=" * 100)
    print("🚀 SMART FILTER WITH API VERIFICATION")
    print("=" * 100)
    print(f"Target: {', '.join(departments_to_select)}")
    print("=" * 100)
    print()
    
    # Storage for API data
    api_data = {
        'before': None,
        'after': None,
        'all_requests': [],
        'all_responses': []
    }
    
    captured_before = asyncio.Event()
    captured_after = asyncio.Event()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected via CDP\n")
            
            page = await get_or_navigate_to_page(
                browser,
                "https://preprodapp.tekioncloud.com/templates/list",
                wait_for_load=True
            )
            
            # Set up API monitoring
            print("📡 Setting up API monitors...")
            
            async def monitor_response(response):
                if '/api/templatestore/u/search' in response.url:
                    try:
                        body = await response.json()
                        
                        # Get the request that triggered this
                        request_data = None
                        try:
                            request_text = response.request.post_data
                            if request_text:
                                request_data = json.loads(request_text)
                        except:
                            pass
                        
                        # Extract department filter from request
                        departments_in_request = []
                        if request_data and 'filters' in request_data:
                            for f in request_data['filters']:
                                if f.get('field') == 'departments':
                                    departments_in_request = f.get('values', [])
                        
                        # Store the data
                        api_call_data = {
                            'timestamp': datetime.now().isoformat(),
                            'request': request_data,
                            'response': body,
                            'departments': departments_in_request,
                            'template_count': len(body.get('data', {}).get('hits', [])),
                            'templates': body.get('data', {}).get('hits', [])
                        }
                        
                        api_data['all_responses'].append(api_call_data)
                        
                        # Capture BEFORE state (first significant response)
                        if not api_data['before'] and api_call_data['template_count'] > 0:
                            api_data['before'] = api_call_data
                            print(f"📊 BEFORE: {departments_in_request} → {api_call_data['template_count']} templates")
                            captured_before.set()
                        
                    except Exception as e:
                        pass
            
            page.on('response', monitor_response)
            
            # Reload to capture initial state
            print("🔄 Capturing BEFORE state...")
            await page.reload(wait_until='domcontentloaded')
            
            try:
                await asyncio.wait_for(captured_before.wait(), timeout=10)
            except:
                print("⚠️  No initial API call captured")
            
            await asyncio.sleep(2)
            print()
            
            # Change the filter
            print("=" * 100)
            print("🖱️  CHANGING FILTER")
            print("=" * 100)
            print()
            
            # Map department names to indices
            dept_map = {'Sales': 0, 'Service': 1, 'Parts': 2}
            
            print("Opening dropdown...")
            await page.click('.ant-dropdown-trigger', timeout=5000)
            await asyncio.sleep(2)
            
            print(f"Unchecking: {', '.join(departments_to_unselect)}")
            for dept in departments_to_unselect:
                idx = dept_map.get(dept)
                if idx is not None:
                    await page.evaluate(f"""
                        () => {{
                            const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{idx}];
                            if (cb && cb.checked) cb.click();
                        }}
                    """)
                    await asyncio.sleep(0.3)
            
            print(f"Checking: {', '.join(departments_to_select)}")
            for dept in departments_to_select:
                idx = dept_map.get(dept)
                if idx is not None:
                    await page.evaluate(f"""
                        () => {{
                            const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{idx}];
                            if (cb && !cb.checked) cb.click();
                        }}
                    """)
                    await asyncio.sleep(0.3)
            
            print("Closing dropdown...")
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)
            print()
            
            # Wait for new API call
            print("⏳ Waiting for API call...")
            
            # Monitor for new response with different departments
            start_time = asyncio.get_event_loop().time()
            timeout = 15
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                # Check if we got a new API call with different departments
                for response_data in reversed(api_data['all_responses']):
                    depts = set(response_data['departments'])
                    expected_depts = set([d.upper() for d in departments_to_select])
                    
                    if depts == expected_depts and response_data != api_data['before']:
                        api_data['after'] = response_data
                        print(f"📊 AFTER: {response_data['departments']} → {response_data['template_count']} templates")
                        captured_after.set()
                        break
                
                if captured_after.is_set():
                    break
                
                await asyncio.sleep(0.5)
            
            if not captured_after.is_set():
                print("⚠️  No new API call captured after filter change")
            
            print()
            
            # Remove listener
            try:
                page.remove_listener('response', monitor_response)
            except:
                pass
            
            # Analyze and compare
            print("=" * 100)
            print("📊 API-BASED VERIFICATION RESULTS")
            print("=" * 100)
            print()
            
            if api_data['before'] and api_data['after']:
                before = api_data['before']
                after = api_data['after']
                
                print(f"1️⃣  DEPARTMENT FILTER:")
                print(f"   Before: {', '.join(before['departments'])}")
                print(f"   After:  {', '.join(after['departments'])}")
                print(f"   Status: {'✅ CHANGED' if before['departments'] != after['departments'] else '❌ NO CHANGE'}")
                print()
                
                print(f"2️⃣  TEMPLATE COUNT:")
                print(f"   Before: {before['template_count']} templates")
                print(f"   After:  {after['template_count']} templates")
                delta = after['template_count'] - before['template_count']
                delta_str = f"+{delta}" if delta > 0 else str(delta)
                print(f"   Delta:  {delta_str}")
                print(f"   Status: {'✅ CHANGED' if delta != 0 else '⚠️  NO CHANGE'}")
                print()
                
                print(f"3️⃣  TEMPLATE COMPARISON:")
                before_ids = set(t['templateId'] for t in before['templates'])
                after_ids = set(t['templateId'] for t in after['templates'])
                
                added = after_ids - before_ids
                removed = before_ids - after_ids
                same = before_ids & after_ids
                
                print(f"   Same:    {len(same)} templates")
                print(f"   Added:   {len(added)} templates")
                print(f"   Removed: {len(removed)} templates")
                print()
                
                if added:
                    print(f"   📝 Sample Added Templates:")
                    for tid in list(added)[:5]:
                        template = next((t for t in after['templates'] if t['templateId'] == tid), None)
                        if template:
                            print(f"      • {template['name']}")
                print()
                
                # Department analysis
                print(f"4️⃣  DEPARTMENT DISTRIBUTION (AFTER):")
                dept_counts = {}
                for template in after['templates']:
                    for dept in template.get('departments', []):
                        dept_counts[dept] = dept_counts.get(dept, 0) + 1
                
                for dept, count in sorted(dept_counts.items()):
                    print(f"   {dept}: {count} templates")
                print()
                
                # Overall verification
                filter_changed = before['departments'] != after['departments']
                data_changed = delta != 0 or len(added) > 0 or len(removed) > 0
                
                print(f"5️⃣  OVERALL VERIFICATION:")
                print(f"   Filter Changed:  {'✅ YES' if filter_changed else '❌ NO'}")
                print(f"   Data Changed:    {'✅ YES' if data_changed else '❌ NO'}")
                print()
                
                if filter_changed and data_changed:
                    print("🎉 SUCCESS: Filter change successfully affected data!")
                elif filter_changed and not data_changed:
                    print("⚠️  Filter changed but data stayed the same")
                else:
                    print("❌ Filter did not change")
            else:
                print("⚠️  Could not capture both BEFORE and AFTER states")
            
            print()
            print("=" * 100)
            
            # Save results
            filename = f"api_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(api_data, f, indent=2, default=str)
            
            print(f"💾 Full results saved to: {filename}")
            print()
            
            return api_data
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None


async def main():
    result = await change_filter_with_api_verification(
        departments_to_select=['Service', 'Parts'],
        departments_to_unselect=['Sales']
    )
    
    if result:
        print("=" * 100)
        print("✅ COMPLETE")
        print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
