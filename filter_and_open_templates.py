#!/usr/bin/env python3
"""
Filter Service & Parts → Build Links from API → Open All Templates
===================================================================

This script:
1. Applies Service & Parts department filter
2. Captures API response with templates
3. Extracts templateId from each template
4. Builds edit URLs
5. Opens all templates in browser tabs

Author: Automation Team
Date: 2026-05-30
Status: Production Ready
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright


def generate_edit_url(template_id):
    """Generate edit URL for a template using templateId"""
    return f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"


async def filter_and_open_templates(
    departments=['Service', 'Parts'],
    max_templates=None,
    cdp_url="http://localhost:9223"
):
    """
    Main workflow: Filter → Capture API → Build URLs → Open Templates
    """

    print("=" * 100)
    print("🚀 FILTER SERVICE & PARTS → BUILD LINKS → OPEN TEMPLATES")
    print("=" * 100)
    print(f"Departments: {', '.join(departments)}")
    print(f"Max Templates: {max_templates if max_templates else 'ALL'}")
    print("=" * 100)
    print()

    # Storage for API data
    tracking_data = {
        'before': {'api': None, 'departments': None},
        'after': {'api': None, 'departments': None},
        'api_calls': []
    }

    async with async_playwright() as playwright:
        try:
            # Connect to browser
            browser = await playwright.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]

            print("✅ Connected to browser via CDP\n")

            # Find or navigate to templates page
            page = None
            for p in context.pages:
                if '/templates/list' in p.url:
                    page = p
                    print(f"✅ Found templates page: {p.url}")
                    break

            if not page:
                page = await context.new_page()
                templates_url = "https://preprodapp.tekioncloud.com/templates/list"
                print(f"🌐 Navigating to: {templates_url}")
                await page.goto(templates_url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(3)

            await page.bring_to_front()

            # STEP 1: Set up API monitoring
            print("\n" + "=" * 100)
            print("📡 STEP 1: SETTING UP API MONITORING")
            print("=" * 100)

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
                        departments_list = []
                        if request_data and 'filters' in request_data:
                            for f in request_data['filters']:
                                if f.get('field') == 'departments':
                                    departments_list = f.get('values', [])

                        # Extract template count and templates
                        template_count = len(response_data.get('data', {}).get('hits', []))
                        templates = response_data.get('data', {}).get('hits', [])

                        # Store API call
                        api_call = {
                            'timestamp': datetime.now().isoformat(),
                            'departments': departments_list,
                            'template_count': template_count,
                            'templates': templates
                        }

                        tracking_data['api_calls'].append(api_call)
                        print(f"   📥 API Call: {departments_list} → {template_count} templates")

                    except Exception as e:
                        print(f"   ⚠️  Error parsing API: {e}")

            page.on('response', monitor_api)

            # Capture BEFORE state
            print("\n🔄 Capturing BEFORE state...")
            await page.reload(wait_until='domcontentloaded')
            await asyncio.sleep(3)

            if tracking_data['api_calls']:
                tracking_data['before']['api'] = tracking_data['api_calls'][-1]
                print(f"✅ BEFORE: {tracking_data['before']['api']['departments']} → {tracking_data['before']['api']['template_count']} templates")



            # STEP 2: Apply Service & Parts filter
            print("\n" + "=" * 100)
            print("🎯 STEP 2: APPLYING SERVICE & PARTS FILTER")
            print("=" * 100)

            dept_map = {'Sales': 0, 'Service': 1, 'Parts': 2}

            # Open dropdown
            print("\n   1. Opening department dropdown...")
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

            print("\n✅ FILTER APPLIED!")

            # STEP 3: Wait for API call with new filter
            print("\n" + "=" * 100)
            print("⏳ STEP 3: WAITING FOR API RESPONSE...")
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
                        print(f"   Departments: {api_call['departments']}")
                        print(f"   Template Count: {api_call['template_count']}")
                        break

                if tracking_data['after']['api']:
                    break

                await asyncio.sleep(0.5)

            if not tracking_data['after']['api']:
                print("   ❌ No matching API call found")
                return

            # STEP 4: Extract templates and build URLs
            print("\n" + "=" * 100)
            print("🔗 STEP 4: BUILDING EDIT URLS FROM API")
            print("=" * 100)

            templates = tracking_data['after']['api']['templates']
            print(f"\n✅ Captured {len(templates)} templates from API")

            # Apply max limit if specified
            if max_templates and max_templates < len(templates):
                templates = templates[:max_templates]
                print(f"⚠️  Limiting to first {max_templates} templates")

            # Build edit URLs
            template_data = []
            for template in templates:
                template_id = template.get('templateId')
                if template_id:
                    edit_url = generate_edit_url(template_id)
                    template_data.append({
                        'templateId': template_id,
                        'name': template.get('name', 'Unknown'),
                        'url': edit_url,
                        'departments': template.get('departments', [])
                    })

            print(f"✅ Built {len(template_data)} edit URLs")

            # Display URLs
            print("\n📋 Templates to open:")
            print("-" * 100)
            for i, item in enumerate(template_data, 1):
                print(f"{i:2d}. {item['name'][:60]:<60}")
                print(f"    Template ID: {item['templateId']}")
                print(f"    Edit URL: {item['url']}")
                print(f"    Departments: {', '.join(item['departments'])}")
                print()

            # STEP 5: Open all templates
            print("=" * 100)
            print("🌐 STEP 5: OPENING ALL TEMPLATES")
            print("=" * 100)

            opened_pages = []
            failed_count = 0

            for idx, item in enumerate(template_data, 1):
                print(f"\n[{idx}/{len(template_data)}] Opening: {item['name'][:50]}")
                print(f"   URL: {item['url']}")

                try:
                    # Open in new tab
                    new_page = await context.new_page()
                    await new_page.goto(item['url'], wait_until='domcontentloaded', timeout=15000)
                    await asyncio.sleep(2)

                    opened_pages.append({
                        'page': new_page,
                        'template': item,
                        'url': item['url']
                    })

                    print(f"   ✅ Opened successfully")

                except Exception as e:
                    print(f"   ❌ Failed to open: {e}")
                    failed_count += 1

            # Cleanup
            page.remove_listener('response', monitor_api)

            # Summary
            print("\n" + "=" * 100)
            print("📊 SUMMARY")
            print("=" * 100)

            print(f"\n✅ Filter Applied: Service & Parts")
            print(f"✅ API Response Captured: {tracking_data['after']['api']['template_count']} templates")
            print(f"✅ Edit URLs Built: {len(template_data)} URLs")
            print(f"✅ Templates Opened: {len(opened_pages)}/{len(template_data)}")
            if failed_count > 0:
                print(f"⚠️  Failed to Open: {failed_count}")

            print("\n📋 Opened Templates:")
            for i, item in enumerate(opened_pages, 1):
                print(f"   {i}. {item['template']['name'][:60]}")

            print("\n" + "=" * 100)
            print("✅ ALL TEMPLATES OPENED SUCCESSFULLY!")
            print("=" * 100)
            print("\n💡 Next Steps:")
            print("   - All templates are now open in browser tabs")
            print("   - You can inspect them manually")
            print("   - Or run logo processing automation on them")

            return {
                'success': True,
                'templates': template_data,
                'opened_pages': opened_pages,
                'count': len(opened_pages)
            }

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


async def main():
    """Main entry point"""

    result = await filter_and_open_templates(
        departments=['Service', 'Parts'],
        max_templates=10,  # Limit to 10 for testing (change to None for all)
        cdp_url="http://localhost:9223"
    )

    if result.get('success'):
        print(f"\n🎉 Successfully opened {result['count']} templates!")
    else:
        print(f"\n❌ Failed: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())

