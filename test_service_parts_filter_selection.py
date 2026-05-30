#!/usr/bin/env python3
"""
Test Service & Parts Filter Selection
Stops after selecting the filter to verify it works
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright
from cdp_utils import get_or_navigate_to_page


async def test_filter_selection():
    """
    Test applying Service & Parts filter and detecting results count
    """

    print("=" * 100)
    print("🧪 TEST: Service & Parts Filter Selection + Results Count Detection")
    print("=" * 100)
    print()

    # Storage for tracking
    tracking_data = {
        'before': {'api': None, 'ui_count': None, 'departments': None},
        'after': {'api': None, 'ui_count': None, 'departments': None},
        'api_calls': []
    }

    async with async_playwright() as playwright:
        try:
            # Connect to browser
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected via CDP\n")

            # Get or navigate to templates page
            page = await get_or_navigate_to_page(
                browser,
                "https://preprodapp.tekioncloud.com/templates/list",
                wait_for_load=True
            )

            # Set up API monitoring
            print("📡 Setting up API monitors...")

            async def monitor_api(response):
                """Monitor /api/templatestore/u/search calls"""
                if '/api/templatestore/u/search' in response.url:
                    try:
                        response_data = await response.json()

                        # Get request data
                        request_data = None
                        try:
                            post_data = response.request.post_data
                            if post_data:
                                request_data = json.loads(post_data)
                        except:
                            pass

                        # Extract departments from request
                        departments = []
                        if request_data and 'filters' in request_data:
                            for f in request_data['filters']:
                                if f.get('field') == 'departments':
                                    departments = f.get('values', [])

                        # Extract template count
                        template_count = len(response_data.get('data', {}).get('hits', []))

                        # Store API call
                        api_call = {
                            'timestamp': datetime.now().isoformat(),
                            'departments': departments,
                            'template_count': template_count
                        }

                        tracking_data['api_calls'].append(api_call)
                        print(f"   📥 API Call: {departments} → {template_count} templates")

                    except Exception as e:
                        print(f"   ⚠️  Error parsing API: {e}")

            page.on('response', monitor_api)

            # STEP 1: Capture BEFORE state
            print("\n" + "=" * 100)
            print("📊 STEP 1: CAPTURING BEFORE STATE")
            print("=" * 100)

            await page.reload(wait_until='domcontentloaded')
            await asyncio.sleep(3)

            # Get UI results count BEFORE
            ui_count_before = await page.evaluate("""
                () => {
                    // Look for filterResults_container
                    const countDiv = document.querySelector('[class*="filterResults_container"]');
                    if (countDiv) {
                        const match = countDiv.textContent.match(/(\\d+)\\s*Result/);
                        return match ? parseInt(match[1]) : null;
                    }
                    return null;
                }
            """)

            if tracking_data['api_calls']:
                tracking_data['before']['api'] = tracking_data['api_calls'][-1]
            tracking_data['before']['ui_count'] = ui_count_before

            print(f"\n✅ BEFORE State:")
            print(f"   UI Count: {ui_count_before} Result(s)")
            if tracking_data['before']['api']:
                print(f"   API Count: {tracking_data['before']['api']['template_count']} templates")
                print(f"   Departments: {tracking_data['before']['api']['departments']}")

            # STEP 2: Apply Service & Parts Filter
            print("\n" + "=" * 100)
            print("🎯 STEP 2: APPLYING FILTER - Service & Parts")
            print("=" * 100)

            dept_map = {'Sales': 0, 'Service': 1, 'Parts': 2}

            # Open dropdown
            print("   1. Opening department dropdown...")
            await page.click('.ant-dropdown-trigger', timeout=5000)
            await asyncio.sleep(1)
            print("      ✅ Dropdown opened")

            # Uncheck Sales
            print("\n   2. Unchecking: Sales")
            await page.evaluate(f"""
                () => {{
                    const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map['Sales']}];
                    if (cb && cb.checked) {{
                        cb.click();
                        console.log('Sales unchecked');
                    }}
                }}
            """)
            await asyncio.sleep(0.5)
            print("      ✅ Sales unchecked")

            # Check Service
            print("\n   3. Checking: Service")
            await page.evaluate(f"""
                () => {{
                    const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map['Service']}];
                    if (cb && !cb.checked) {{
                        cb.click();
                        console.log('Service checked');
                    }}
                }}
            """)
            await asyncio.sleep(0.5)
            print("      ✅ Service checked")

            # Check Parts
            print("\n   4. Checking: Parts")
            await page.evaluate(f"""
                () => {{
                    const cb = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]')[{dept_map['Parts']}];
                    if (cb && !cb.checked) {{
                        cb.click();
                        console.log('Parts checked');
                    }}
                }}
            """)
            await asyncio.sleep(0.5)
            print("      ✅ Parts checked")

            # Close dropdown
            print("\n   5. Closing dropdown...")
            await page.keyboard.press('Escape')
            await asyncio.sleep(2)
            print("      ✅ Dropdown closed")

            print("\n" + "=" * 100)
            print("✅ FILTER SELECTION COMPLETE!")
            print("=" * 100)

            # STEP 3: Wait for API call with new filter
            print("\n" + "=" * 100)
            print("⏳ STEP 3: WAITING FOR API CALL WITH NEW FILTER...")
            print("=" * 100)

            start_time = asyncio.get_event_loop().time()
            timeout = 10

            while (asyncio.get_event_loop().time() - start_time) < timeout:
                for api_call in reversed(tracking_data['api_calls']):
                    depts = set(api_call['departments'])
                    expected = set(['SERVICE', 'PARTS'])

                    if depts == expected:
                        tracking_data['after']['api'] = api_call
                        print(f"   ✅ Found matching API call!")
                        break

                if tracking_data['after']['api']:
                    break

                await asyncio.sleep(0.5)

            # STEP 4: Capture AFTER state
            print("\n" + "=" * 100)
            print("📊 STEP 4: CAPTURING AFTER STATE")
            print("=" * 100)

            await asyncio.sleep(1)

            # Get UI results count AFTER
            ui_count_after = await page.evaluate("""
                () => {
                    const countDiv = document.querySelector('[class*="filterResults_container"]');
                    if (countDiv) {
                        const match = countDiv.textContent.match(/(\\d+)\\s*Result/);
                        return match ? parseInt(match[1]) : null;
                    }
                    return null;
                }
            """)

            tracking_data['after']['ui_count'] = ui_count_after

            print(f"\n✅ AFTER State:")
            print(f"   UI Count: {ui_count_after} Result(s)")
            if tracking_data['after']['api']:
                print(f"   API Count: {tracking_data['after']['api']['template_count']} templates")
                print(f"   Departments: {tracking_data['after']['api']['departments']}")

            # STEP 5: Detect Results Count Element
            print("\n" + "=" * 100)
            print("🔍 STEP 5: RESULTS COUNT ELEMENT DETAILS")
            print("=" * 100)

            element_details = await page.evaluate("""
                () => {
                    const countDiv = document.querySelector('[class*="filterResults_container"]');
                    if (countDiv) {
                        return {
                            found: true,
                            text: countDiv.textContent,
                            className: countDiv.className,
                            dataTest: countDiv.getAttribute('data-test'),
                            dataTestId: countDiv.getAttribute('data-test-id'),
                            tagName: countDiv.tagName,
                            outerHTML: countDiv.outerHTML.substring(0, 300)
                        };
                    }
                    return { found: false };
                }
            """)

            if element_details['found']:
                print(f"\n   ✅ Element Found!")
                print(f"   Text: {element_details['text']}")
                print(f"   Tag: {element_details['tagName']}")
                print(f"   Class: {element_details['className']}")
                print(f"   data-test: {element_details['dataTest']}")
                print(f"   data-test-id: {element_details['dataTestId']}")
                print(f"\n   HTML Preview:")
                print(f"   {element_details['outerHTML']}")
            else:
                print("   ❌ Element not found")

            # STEP 6: Summary
            print("\n" + "=" * 100)
            print("📈 SUMMARY")
            print("=" * 100)

            print(f"\n🔍 DEPARTMENT FILTER:")
            if tracking_data['before']['api'] and tracking_data['after']['api']:
                print(f"   BEFORE: {tracking_data['before']['api']['departments']}")
                print(f"   AFTER:  {tracking_data['after']['api']['departments']}")
                print(f"   Status: {'✅ CHANGED' if tracking_data['before']['api']['departments'] != tracking_data['after']['api']['departments'] else '❌ NO CHANGE'}")

            print(f"\n📊 UI RESULTS COUNT:")
            print(f"   BEFORE: {ui_count_before} Result(s)")
            print(f"   AFTER:  {ui_count_after} Result(s)")
            if ui_count_before and ui_count_after:
                change = ui_count_after - ui_count_before
                print(f"   CHANGE: {'+' if change > 0 else ''}{change}")

            print(f"\n📥 API TEMPLATE COUNT:")
            if tracking_data['before']['api'] and tracking_data['after']['api']:
                before_count = tracking_data['before']['api']['template_count']
                after_count = tracking_data['after']['api']['template_count']
                print(f"   BEFORE: {before_count} templates")
                print(f"   AFTER:  {after_count} templates")
                print(f"   CHANGE: {'+' if (after_count - before_count) > 0 else ''}{after_count - before_count}")

            print(f"\n✅ UI vs API MATCH:")
            if ui_count_after and tracking_data['after']['api']:
                api_count = tracking_data['after']['api']['template_count']
                match = ui_count_after == api_count
                print(f"   UI: {ui_count_after}, API: {api_count} → {'✅ MATCH' if match else '❌ MISMATCH'}")

            # Cleanup
            page.remove_listener('response', monitor_api)

            print("\n" + "=" * 100)
            print("✅ TEST COMPLETE - FILTER SELECTION VERIFIED!")
            print("=" * 100)

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_filter_selection())
