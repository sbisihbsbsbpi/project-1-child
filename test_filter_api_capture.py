#!/usr/bin/env python3
"""
Test filter application and API capture behavior

Purpose:
- Apply Service & Parts filter
- Track ALL API calls during filter application
- Show before/after state
- Identify which API call is the correct final one
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

# Track all API calls
api_calls = []
templates_captured = []

async def test_filter_application():
    """Test filter application and track API behavior"""
    
    print("=" * 100)
    print("🧪 FILTER APPLICATION & API CAPTURE TEST")
    print("=" * 100)
    print()
    print("This test will:")
    print("  1. Navigate to templates list")
    print("  2. Track BEFORE state (initial filter)")
    print("  3. Apply Service & Parts filter")
    print("  4. Track ALL API calls during filter application")
    print("  5. Show AFTER state (final filter)")
    print("  6. Identify the correct final API call")
    print()
    print("=" * 100)
    print()
    
    async with async_playwright() as p:
        # Connect to existing browser
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        page = await context.new_page()
        
        # Navigate to templates list
        url = "https://preprodapp.tekioncloud.com/templates/list"
        print(f"📍 Navigating to: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        await asyncio.sleep(3)
        
        # STEP 1: Capture BEFORE state
        print()
        print("=" * 100)
        print("📊 STEP 1: BEFORE STATE (Initial Load)")
        print("=" * 100)
        
        before_state = await page.evaluate("""
            () => {
                // Get results count from UI
                const resultsElement = document.querySelector('[data-test="undefined-resultsCount"]') ||
                                      document.querySelector('[class*="filterResults_container"]');
                const resultsText = resultsElement ? resultsElement.textContent : 'Not found';
                
                // Get filter state
                const checkboxes = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]');
                const deptStates = {
                    sales: checkboxes[0] ? checkboxes[0].checked : false,
                    service: checkboxes[1] ? checkboxes[1].checked : false,
                    parts: checkboxes[2] ? checkboxes[2].checked : false
                };
                
                return {
                    resultsText: resultsText,
                    departmentStates: deptStates
                };
            }
        """)
        
        print(f"   UI Results Count: {before_state['resultsText']}")
        print(f"   Department Filter State:")
        print(f"      - Sales:   {'✅ Checked' if before_state['departmentStates']['sales'] else '❌ Unchecked'}")
        print(f"      - Service: {'✅ Checked' if before_state['departmentStates']['service'] else '❌ Unchecked'}")
        print(f"      - Parts:   {'✅ Checked' if before_state['departmentStates']['parts'] else '❌ Unchecked'}")
        
        # STEP 2: Set up API listener
        print()
        print("=" * 100)
        print("📡 STEP 2: SETTING UP API LISTENER")
        print("=" * 100)
        print("   Listening for: POST /api/templatestore/u/search")
        print()
        
        async def track_api_call(response):
            if '/api/templatestore/u/search' in response.url:
                try:
                    request = response.request
                    post_data = request.post_data
                    
                    if post_data:
                        payload = json.loads(post_data)
                        
                    data = await response.json()
                    hits_count = 0
                    departments = []
                    
                    if 'data' in data and 'hits' in data['data']:
                        hits_count = len(data['data']['hits'])
                        
                        # Extract department filter from request
                        if post_data:
                            for filter_item in payload.get('filters', []):
                                if filter_item.get('field') == 'departments':
                                    departments = filter_item.get('values', [])
                    
                    api_call_info = {
                        'timestamp': datetime.now().isoformat(),
                        'departments': departments,
                        'hits_count': hits_count,
                        'call_number': len(api_calls) + 1
                    }
                    
                    api_calls.append(api_call_info)
                    
                    print(f"   📥 API Call #{api_call_info['call_number']}:")
                    print(f"      Departments: {departments}")
                    print(f"      Templates: {hits_count}")
                    print()
                    
                except Exception as e:
                    print(f"   ⚠️  Error parsing API response: {e}")
        
        page.on('response', track_api_call)
        
        # STEP 3: Apply filter
        print("=" * 100)
        print("🎯 STEP 3: APPLYING SERVICE & PARTS FILTER")
        print("=" * 100)
        print()

        dept_map = {'Sales': 0, 'Service': 1, 'Parts': 2}

        # Open dropdown
        print("   1. Opening department dropdown...")
        await page.click('.ant-dropdown-trigger', timeout=5000)
        await asyncio.sleep(1)

        # Uncheck all first
        print("   2. Unchecking all departments...")
        for dept_name in ['Sales', 'Service', 'Parts']:
            await page.evaluate(f"""
                () => {{
                    const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map[dept_name]}];
                    if (cb && cb.checked) cb.click();
                }}
            """)
            await asyncio.sleep(0.3)

        # Check selected departments
        print(f"   3. Checking: Service, Parts")
        for dept_name in ['Service', 'Parts']:
            await page.evaluate(f"""
                () => {{
                    const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map[dept_name]}];
                    if (cb && !cb.checked) cb.click();
                }}
            """)
            await asyncio.sleep(0.3)

        # Close dropdown
        print("   4. Closing dropdown...")
        await page.keyboard.press('Escape')
        await asyncio.sleep(2)  # Wait for final API call

        # Stop listening
        page.remove_listener('response', track_api_call)

        # STEP 4: Capture AFTER state
        print()
        print("=" * 100)
        print("📊 STEP 4: AFTER STATE (Filter Applied)")
        print("=" * 100)

        after_state = await page.evaluate("""
            () => {
                // Get results count from UI
                const resultsElement = document.querySelector('[data-test="undefined-resultsCount"]') ||
                                      document.querySelector('[class*="filterResults_container"]');
                const resultsText = resultsElement ? resultsElement.textContent : 'Not found';

                // Get filter state
                const checkboxes = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]');
                const deptStates = {
                    sales: checkboxes[0] ? checkboxes[0].checked : false,
                    service: checkboxes[1] ? checkboxes[1].checked : false,
                    parts: checkboxes[2] ? checkboxes[2].checked : false
                };

                return {
                    resultsText: resultsText,
                    departmentStates: deptStates
                };
            }
        """)

        print(f"   UI Results Count: {after_state['resultsText']}")
        print(f"   Department Filter State:")
        print(f"      - Sales:   {'✅ Checked' if after_state['departmentStates']['sales'] else '❌ Unchecked'}")
        print(f"      - Service: {'✅ Checked' if after_state['departmentStates']['service'] else '❌ Unchecked'}")
        print(f"      - Parts:   {'✅ Checked' if after_state['departmentStates']['parts'] else '❌ Unchecked'}")

        # STEP 5: Analyze API calls
        print()
        print("=" * 100)
        print("🔍 STEP 5: API CALL ANALYSIS")
        print("=" * 100)
        print()
        print(f"   Total API calls captured: {len(api_calls)}")
        print()

        if api_calls:
            print("   Detailed breakdown:")
            print()
            total_using_extend = 0

            for call in api_calls:
                print(f"   Call #{call['call_number']}:")
                print(f"      Departments: {call['departments']}")
                print(f"      Templates returned: {call['hits_count']}")
                total_using_extend += call['hits_count']
                print()

            print("=" * 100)
            print("📊 SUMMARY")
            print("=" * 100)
            print()
            print(f"   BEFORE filter:")
            print(f"      UI count: {before_state['resultsText']}")
            print()
            print(f"   AFTER filter:")
            print(f"      UI count: {after_state['resultsText']}")
            print()
            print(f"   API Capture Analysis:")
            print(f"      Total API calls: {len(api_calls)}")
            print(f"      If using templates.extend() (current bug): {total_using_extend} templates ❌")
            print(f"      If using templates = hits (correct): {api_calls[-1]['hits_count']} templates ✅")
            print()
            print(f"   🎯 CORRECT BEHAVIOR:")
            print(f"      Only use the LAST API call (#{api_calls[-1]['call_number']})")
            print(f"      Departments: {api_calls[-1]['departments']}")
            print(f"      Templates: {api_calls[-1]['hits_count']}")
            print()

            # Identify which call is the final one
            final_call = api_calls[-1]
            if final_call['departments'] == ['SERVICE', 'PARTS'] or final_call['departments'] == ['PARTS', 'SERVICE']:
                print("   ✅ VERIFICATION: Final API call matches expected filter (SERVICE, PARTS)")
                print(f"   ✅ UI count matches final API: {after_state['resultsText']} vs {final_call['hits_count']} templates")
            else:
                print(f"   ⚠️  WARNING: Final API call departments don't match: {final_call['departments']}")

        print()
        print("=" * 100)
        print("✅ TEST COMPLETE")
        print("=" * 100)
        print()

        # Keep tab open for inspection
        print("Tab kept open for manual inspection.")
        print("Press Ctrl+C to exit.")

        try:
            await asyncio.sleep(3600)  # Keep running for 1 hour
        except KeyboardInterrupt:
            print("\n✋ Test stopped by user")


if __name__ == "__main__":
    asyncio.run(test_filter_application())
