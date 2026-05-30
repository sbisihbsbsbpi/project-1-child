#!/usr/bin/env python3
"""
Network Monitor for Department Filter API Calls
Intercepts and analyzes the search API when filter changes
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright
from cdp_utils import get_or_navigate_to_page, print_cdp_info


async def monitor_network_and_change_filter():
    """
    Monitor network traffic while changing department filter
    Captures the search API call and response
    """
    
    print("=" * 100)
    print("🌐 NETWORK MONITOR - DEPARTMENT FILTER API ANALYSIS")
    print("=" * 100)
    print()
    
    # Storage for captured API calls
    api_calls = {
        'requests': [],
        'responses': [],
        'search_api_calls': []
    }
    
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
            
            # Set up network listeners BEFORE making changes
            print("🎯 Setting up network monitors...")
            print()
            
            # Request listener
            async def log_request(request):
                url = request.url
                
                # Only capture template search API
                if '/api/templatestore/u/search' in url:
                    print(f"📤 REQUEST: {request.method} {url}")
                    
                    # Try to get request body
                    try:
                        post_data = request.post_data
                        if post_data:
                            try:
                                post_json = json.loads(post_data)
                                print(f"   📦 Request Body:")
                                print(f"      {json.dumps(post_json, indent=6)}")
                            except:
                                print(f"   📦 Request Body (raw): {post_data[:500]}")
                    except:
                        pass
                    
                    api_calls['requests'].append({
                        'timestamp': datetime.now().isoformat(),
                        'method': request.method,
                        'url': url,
                        'headers': dict(request.headers),
                        'post_data': request.post_data
                    })
            
            # Response listener
            async def log_response(response):
                url = response.url
                
                # Only capture template search API
                if '/api/templatestore/u/search' in url:
                    print(f"\n📥 RESPONSE: {response.status} {url}")
                    
                    try:
                        # Get response body
                        body = await response.text()
                        
                        try:
                            body_json = json.loads(body)
                            
                            # Extract key information
                            if 'data' in body_json:
                                data = body_json['data']
                                
                                print(f"   ✅ Status: {response.status}")
                                print(f"   📊 Response Structure:")
                                print(f"      Total: {data.get('total', 'N/A')}")
                                print(f"      Hits: {len(data.get('hits', []))}")
                                print(f"      Page: {data.get('page', 'N/A')}")
                                print(f"      Size: {data.get('size', 'N/A')}")
                                
                                # Analyze templates
                                hits = data.get('hits', [])
                                if hits:
                                    print(f"\n   📋 Template Data (first 5):")
                                    
                                    for i, template in enumerate(hits[:5], 1):
                                        print(f"\n      {i}. {template.get('name', 'Unknown')}")
                                        print(f"         ID: {template.get('templateId', 'N/A')}")
                                        print(f"         Departments: {template.get('departments', [])}")
                                        print(f"         Type: {template.get('purposeSubType', 'N/A')}")
                                        print(f"         Status: {template.get('status', 'N/A')}")
                                        print(f"         Categories: {template.get('categories', [])}")
                                    
                                    # Department breakdown
                                    dept_counts = {}
                                    type_counts = {}
                                    
                                    for template in hits:
                                        depts = template.get('departments', [])
                                        for dept in depts:
                                            dept_counts[dept] = dept_counts.get(dept, 0) + 1
                                        
                                        t_type = template.get('purposeSubType', 'Unknown')
                                        type_counts[t_type] = type_counts.get(t_type, 0) + 1
                                    
                                    print(f"\n   📊 Department Breakdown:")
                                    for dept, count in sorted(dept_counts.items()):
                                        print(f"      {dept}: {count} templates")
                                    
                                    print(f"\n   📊 Type Breakdown:")
                                    for t_type, count in sorted(type_counts.items()):
                                        print(f"      {t_type}: {count} templates")
                            
                            # Store full response
                            api_calls['responses'].append({
                                'timestamp': datetime.now().isoformat(),
                                'status': response.status,
                                'url': url,
                                'body': body_json
                            })
                            
                            api_calls['search_api_calls'].append({
                                'timestamp': datetime.now().isoformat(),
                                'request': api_calls['requests'][-1] if api_calls['requests'] else None,
                                'response': body_json
                            })
                            
                        except json.JSONDecodeError:
                            print(f"   ⚠️  Response not JSON: {body[:200]}")
                    
                    except Exception as e:
                        print(f"   ❌ Error reading response: {e}")
            
            # Attach listeners
            page.on('request', log_request)
            page.on('response', log_response)
            
            print("✅ Network monitors active")
            print()
            print("=" * 100)
            print("STEP 1: CAPTURE CURRENT STATE (Service & Parts)")
            print("=" * 100)
            print()
            
            # Reload page to trigger initial API call
            print("🔄 Reloading page to capture current filter state...")
            await page.reload(wait_until='domcontentloaded')
            await asyncio.sleep(5)
            
            print()
            print("=" * 100)
            print("STEP 2: CHANGE TO SALES ONLY")
            print("=" * 100)
            print()
            
            # Change filter to Sales
            print("🖱️  Opening department dropdown...")
            await page.click('.ant-dropdown-trigger', timeout=5000)
            await asyncio.sleep(2)
            
            # Click on Sales checkbox (index 0)
            print("🖱️  Selecting Sales only...")
            clicked = await page.evaluate("""
                () => {
                    const checkboxes = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]');
                    if (checkboxes.length >= 3) {
                        // Uncheck Service (1) and Parts (2) if checked
                        if (checkboxes[1].checked) checkboxes[1].click();
                        if (checkboxes[2].checked) checkboxes[2].click();
                        // Check Sales (0) if not checked
                        if (!checkboxes[0].checked) checkboxes[0].click();
                        return true;
                    }
                    return false;
                }
            """)
            
            if clicked:
                print("   ✅ Changed to Sales")
            else:
                print("   ⚠️  Could not find checkboxes")
            
            await asyncio.sleep(1)
            
            # Close dropdown
            print("🖱️  Closing dropdown...")
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)
            
            # Wait for API call
            print("⏳ Waiting for API call...")
            await asyncio.sleep(10)
            
            print()
            print("=" * 100)
            print("STEP 3: CHANGE BACK TO SERVICE & PARTS")
            print("=" * 100)
            print()
            
            # Change back to Service & Parts
            print("🖱️  Opening department dropdown...")
            await page.click('.ant-dropdown-trigger', timeout=5000)
            await asyncio.sleep(2)
            
            print("🖱️  Selecting Service & Parts...")
            clicked = await page.evaluate("""
                () => {
                    const checkboxes = document.querySelectorAll('input[type="checkbox"][data-test*="departments"]');
                    if (checkboxes.length >= 3) {
                        // Uncheck Sales (0) if checked
                        if (checkboxes[0].checked) checkboxes[0].click();
                        // Check Service (1) and Parts (2)
                        if (!checkboxes[1].checked) checkboxes[1].click();
                        if (!checkboxes[2].checked) checkboxes[2].click();
                        return true;
                    }
                    return false;
                }
            """)
            
            if clicked:
                print("   ✅ Changed to Service & Parts")

            await asyncio.sleep(1)

            # Close dropdown
            print("🖱️  Closing dropdown...")
            await page.keyboard.press('Escape')
            await asyncio.sleep(1)

            # Wait for API call
            print("⏳ Waiting for API call...")
            await asyncio.sleep(10)

            # Remove listeners
            page.remove_all_listeners('request')
            page.remove_all_listeners('response')

            print()
            print("=" * 100)
            print("📊 API ANALYSIS SUMMARY")
            print("=" * 100)
            print()

            print(f"Total API Calls Captured: {len(api_calls['search_api_calls'])}")
            print()

            # Save results
            filename = f"api_monitor_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(api_calls, f, indent=2, default=str)

            print(f"💾 Full results saved to: {filename}")
            print()

            # Summary of each call
            for i, call in enumerate(api_calls['search_api_calls'], 1):
                print(f"Call {i}:")
                response = call.get('response', {})
                data = response.get('data', {})
                hits = data.get('hits', [])

                print(f"  Timestamp: {call.get('timestamp', 'N/A')}")
                print(f"  Templates: {len(hits)}")

                if hits:
                    # Department analysis
                    dept_counts = {}
                    for template in hits:
                        depts = template.get('departments', [])
                        for dept in depts:
                            dept_counts[dept] = dept_counts.get(dept, 0) + 1

                    print(f"  Departments: {dept_counts}")

                print()

            # Key learnings
            print("=" * 100)
            print("🎓 KEY LEARNINGS")
            print("=" * 100)
            print()

            if api_calls['search_api_calls']:
                print("✅ Successfully intercepted API calls!")
                print()
                print("📋 What we learned:")
                print("   1. API Endpoint: /api/templatestore/u/search")
                print("   2. Method: POST")
                print("   3. Request contains filter parameters")
                print("   4. Response contains full template data")
                print("   5. Each template has:")
                print("      - templateId")
                print("      - name")
                print("      - departments (array)")
                print("      - purposeSubType (EMAIL, SMS, etc.)")
                print("      - status")
                print("      - categories")
                print("      - metadata")
                print()
                print("💡 This means we can:")
                print("   ✅ Verify filter changes by comparing API responses")
                print("   ✅ Get exact template counts per department")
                print("   ✅ Analyze template distribution")
                print("   ✅ Bypass DOM parsing - use API data directly!")
                print()
            else:
                print("⚠️  No API calls captured. Possible reasons:")
                print("   - Filter didn't actually change")
                print("   - API call already happened before monitoring started")
                print("   - Page uses different API endpoint")

            print("=" * 100)

            return api_calls

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None


async def main():
    result = await monitor_network_and_change_filter()

    if result:
        print("\n✅ MONITORING COMPLETE")
        print(f"   Captured {len(result['search_api_calls'])} API calls")


if __name__ == "__main__":
    asyncio.run(main())

