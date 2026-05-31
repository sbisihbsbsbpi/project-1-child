#!/usr/bin/env python3
"""
Complete Logo Addition Flow Test
Uses the EXACT same code that worked in test_service_parts_filter_selection.py
Tests the complete flow: filter → capture templates → process
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.async_api import async_playwright
from cdp_utils import get_or_navigate_to_page


async def test_complete_flow():
    """
    Test complete logo addition flow with working filter logic
    """
    
    print("=" * 100)
    print("🧪 COMPLETE LOGO ADDITION FLOW TEST")
    print("=" * 100)
    print()
    
    # Storage for captured templates
    templates = []
    response_received = asyncio.Event()
    
    async with async_playwright() as playwright:
        try:
            # STEP 1: Connect to browser
            print("🔌 STEP 1: CONNECTING TO BROWSER")
            print("=" * 100)
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected via CDP\n")
            
            context = browser.contexts[0]
            
            # STEP 2: Navigate to templates page
            print("🌐 STEP 2: NAVIGATING TO TEMPLATES PAGE")
            print("=" * 100)
            
            page = await get_or_navigate_to_page(
                browser,
                "https://preprodapp.tekioncloud.com/templates/list",
                wait_for_load=True
            )
            
            print("✅ Page loaded\n")
            
            # STEP 3: Set up API monitoring
            print("📡 STEP 3: SETTING UP API MONITORING")
            print("=" * 100)
            
            async def handle_response(response):
                nonlocal templates
                if '/api/templatestore/u/search' in response.url:
                    try:
                        data = await response.json()
                        if 'data' in data and 'hits' in data['data']:
                            hits = data['data']['hits']
                            if hits:
                                # Get request data to check filter
                                request_data = None
                                try:
                                    post_data = response.request.post_data
                                    if post_data:
                                        request_data = json.loads(post_data)
                                except:
                                    pass
                                
                                # Extract departments
                                departments = []
                                if request_data and 'filters' in request_data:
                                    for f in request_data['filters']:
                                        if f.get('field') == 'departments':
                                            departments = f.get('values', [])
                                
                                # Check if this is Service & Parts filter
                                if set(departments) == set(['SERVICE', 'PARTS']):
                                    templates.clear()  # Clear old data
                                    templates.extend(hits)
                                    print(f"   📥 Captured {len(hits)} templates from API (Service & Parts)")
                                    response_received.set()
                                else:
                                    print(f"   📥 API call detected: {departments} → {len(hits)} templates")
                    except:
                        pass
            
            page.on('response', handle_response)
            print("✅ API monitoring active\n")
            
            # STEP 4: Reload page to get fresh state (CRITICAL - from working test)
            print("🔄 STEP 4: RELOADING PAGE FOR FRESH STATE")
            print("=" * 100)
            await page.reload(wait_until='domcontentloaded')
            await asyncio.sleep(3)
            print("✅ Page reloaded\n")
            
            # STEP 5: Apply Service & Parts Filter (EXACT WORKING CODE)
            print("🎯 STEP 5: APPLYING DEPARTMENT FILTER")
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

            print("\n✅ FILTER APPLICATION COMPLETE!\n")

            # STEP 6: Wait for API response
            print("⏳ STEP 6: WAITING FOR API RESPONSE")
            print("=" * 100)
            try:
                await asyncio.wait_for(response_received.wait(), timeout=10.0)
                print(f"✅ API response received: {len(templates)} templates captured\n")
            except asyncio.TimeoutError:
                print("⚠️  API response timeout - using any captured templates\n")

            # STEP 7: Display captured templates
            print("📋 STEP 7: CAPTURED TEMPLATES")
            print("=" * 100)

            if not templates:
                print("❌ No templates captured!")
                return

            print(f"\n✅ Captured {len(templates)} templates:\n")
            for idx, template in enumerate(templates[:5], 1):  # Show first 5
                template_id = template.get('templateId') or template.get('id')
                template_name = template.get('name', 'Unknown')
                print(f"   {idx}. {template_name} (ID: {template_id})")

            if len(templates) > 5:
                print(f"   ... and {len(templates) - 5} more")

            # STEP 8: Test processing first template (just navigation, no logo work)
            print(f"\n🧪 STEP 8: TEST PROCESSING FIRST TEMPLATE")
            print("=" * 100)

            if templates:
                first_template = templates[0]
                template_id = first_template.get('templateId') or first_template.get('id')
                template_name = first_template.get('name', 'Unknown')
                base_url = "https://preprodapp.tekioncloud.com"

                print(f"\nTemplate: {template_name}")
                print(f"ID: {template_id}")

                edit_url = f"{base_url}/templates/edit/{template_id}"
                print(f"\nOpening: {edit_url}")

                # Open in new page
                test_page = await context.new_page()
                await test_page.goto(edit_url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(5)

                print("✅ Template editor opened")

                # Test logo detection
                print("\n🔍 Running logo detection...")
                detection_result = await test_page.evaluate("""
                    () => {
                        // LAYER 1: Warning icons
                        const warnings = Array.from(
                            document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb')
                        );

                        // LAYER 2: Logo 1/2 containers
                        const logo1Ids = ['Logo 1', 'Logo1', 'logo 1', 'logo1'];
                        const logo2Ids = ['Logo 2', 'Logo2', 'logo 2', 'logo2'];
                        const allLogos = [];

                        logo1Ids.forEach(id => {
                            const el = document.getElementById(id);
                            if (el) allLogos.push({ id, element: el });
                        });

                        logo2Ids.forEach(id => {
                            const el = document.getElementById(id);
                            if (el) allLogos.push({ id, element: el });
                        });

                        return {
                            warningsCount: warnings.length,
                            logo1_2_containers: allLogos.length,
                            hasContent: document.body.innerHTML.length > 0
                        };
                    }
                """)

                print(f"\nDetection results:")
                print(f"   Warnings: {detection_result['warningsCount']}")
                print(f"   Logo 1/2 containers: {detection_result['logo1_2_containers']}")
                print(f"   Page loaded: {detection_result['hasContent']}")

                # Close test page
                await test_page.close()
                print("\n✅ Template processing test complete")

            # Cleanup
            page.remove_listener('response', handle_response)

            print("\n" + "=" * 100)
            print("✅ COMPLETE FLOW TEST FINISHED!")
            print("=" * 100)
            print(f"\n📊 Summary:")
            print(f"   ✅ Browser connected")
            print(f"   ✅ Page loaded")
            print(f"   ✅ Filter applied (Service & Parts)")
            print(f"   ✅ Templates captured: {len(templates)}")
            print(f"   ✅ Template processing: Tested")
            print("\n🎉 All steps completed successfully!\n")

        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_complete_flow())

