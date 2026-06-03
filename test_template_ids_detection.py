#!/usr/bin/env python3
"""
Comprehensive test: Template count + Template ID detection

This test verifies:
1. Correct template count (39-40 vs 129)
2. Template IDs are being captured from API
3. Template structure and required fields
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logo_addition_diagnostics.temp_logo_adding_FINAL import TempLogoAdditionFinalService, logger

async def test_template_ids_and_count():
    """Test template count and ID detection"""
    
    print("=" * 100)
    print("🧪 COMPREHENSIVE TEST: Template Count + ID Detection")
    print("=" * 100)
    print()
    print("This test verifies:")
    print("  1. ✅ Correct template count (39-40 expected)")
    print("  2. ✅ Template IDs are captured from API")
    print("  3. ✅ Template structure has required fields")
    print()
    print("=" * 100)
    print()
    
    service = TempLogoAdditionFinalService()
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            page = await context.new_page()
            
            # Navigate to templates list
            url = "https://preprodapp.tekioncloud.com/templates/list"
            logger.info(f"📍 Navigating to: {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)
            
            # Apply filter using the service method
            logger.info("\n🎯 Applying Service & Parts filter...")
            templates = await service._apply_filter_and_capture(
                page=page,
                departments=['Service', 'Parts'],
                base_url="https://preprodapp.tekioncloud.com"
            )
            
            # Get UI count for comparison
            ui_count = await page.evaluate("""
                () => {
                    const resultsElement = document.querySelector('[data-test="undefined-resultsCount"]') ||
                                          document.querySelector('[class*="filterResults_container"]');
                    return resultsElement ? resultsElement.textContent : 'Not found';
                }
            """)
            
            print()
            print("=" * 100)
            print("📊 STEP 1: TEMPLATE COUNT VERIFICATION")
            print("=" * 100)
            print()
            print(f"   UI Count: {ui_count}")
            print(f"   API Captured: {len(templates)} templates")
            print()
            
            if len(templates) >= 39 and len(templates) <= 41:
                print("   ✅ Template count is CORRECT (within expected range 39-41)")
                count_status = "PASS"
            else:
                print(f"   ❌ Template count is WRONG (expected 39-41, got {len(templates)})")
                count_status = "FAIL"
            
            print()
            print("=" * 100)
            print("📊 STEP 2: TEMPLATE ID DETECTION")
            print("=" * 100)
            print()
            
            if not templates:
                print("   ❌ No templates captured! Cannot verify IDs.")
                id_status = "FAIL"
            else:
                # Check template structure
                print(f"   Analyzing {len(templates)} templates...")
                print()
                
                templates_with_id = 0
                templates_without_id = 0
                id_field_name = None
                
                # Check what ID field is used
                sample_template = templates[0]
                print("   Sample template structure (first template):")
                print(f"      Keys available: {list(sample_template.keys())[:10]}...")
                print()
                
                # Check for template ID fields
                possible_id_fields = ['templateId', 'id', '_id', 'template_id']
                for field in possible_id_fields:
                    if field in sample_template:
                        id_field_name = field
                        print(f"   ✅ Found ID field: '{id_field_name}'")
                        print(f"      Value: {sample_template[id_field_name]}")
                        break
                
                if not id_field_name:
                    print("   ⚠️  No standard ID field found. Checking all keys...")
                    # Show all keys to help identify the ID field
                    print(f"      All keys in first template:")
                    for key, value in list(sample_template.items())[:15]:
                        print(f"         - {key}: {value}")
                
                print()
                
                # Count templates with IDs
                for template in templates:
                    if id_field_name and id_field_name in template and template[id_field_name]:
                        templates_with_id += 1
                    else:
                        templates_without_id += 1
                
                print(f"   Templates with IDs: {templates_with_id}")
                print(f"   Templates without IDs: {templates_without_id}")
                print()
                
                if templates_with_id == len(templates):
                    print("   ✅ ALL templates have IDs!")
                    id_status = "PASS"
                elif templates_with_id > 0:
                    print(f"   ⚠️  Only {templates_with_id}/{len(templates)} templates have IDs")
                    id_status = "PARTIAL"
                else:
                    print("   ❌ NO templates have IDs!")
                    id_status = "FAIL"

            print()
            print("=" * 100)
            print("📊 STEP 3: TEMPLATE DETAILS (First 5)")
            print("=" * 100)
            print()

            for idx, template in enumerate(templates[:5], 1):
                name = template.get('name', 'Unknown')
                template_id = template.get(id_field_name if id_field_name else 'templateId', 'No ID')
                depts = template.get('departments', [])

                print(f"   {idx}. {name}")
                print(f"      Template ID: {template_id}")
                print(f"      Departments: {', '.join(depts) if depts else 'None'}")
                print()

            if len(templates) > 5:
                print(f"   ... and {len(templates) - 5} more templates")

            print()
            print("=" * 100)
            print("📊 STEP 4: EDIT URL GENERATION TEST")
            print("=" * 100)
            print()

            if id_field_name and templates:
                base_url = "https://preprodapp.tekioncloud.com"
                print("   Testing edit URL generation for first 3 templates:")
                print()

                for idx, template in enumerate(templates[:3], 1):
                    template_id = template.get(id_field_name, 'NO_ID')
                    name = template.get('name', 'Unknown')
                    edit_url = f"{base_url}/templates/edit/{template_id}"

                    print(f"   {idx}. {name}")
                    print(f"      ID: {template_id}")
                    print(f"      URL: {edit_url}")
                    print()

                url_status = "PASS"
            else:
                print("   ❌ Cannot generate URLs - no ID field found")
                url_status = "FAIL"

            print()
            print("=" * 100)
            print("📊 FINAL VERDICT")
            print("=" * 100)
            print()
            print(f"   Template Count: {count_status}")
            print(f"   Template IDs:   {id_status}")
            print(f"   URL Generation: {url_status}")
            print()

            overall = "PASS" if all(s == "PASS" for s in [count_status, id_status, url_status]) else "FAIL"

            if overall == "PASS":
                print("   🎉 ALL TESTS PASSED! ✅")
                print()
                print("   Summary:")
                print(f"      • Captured {len(templates)} templates (correct!)")
                print(f"      • All templates have IDs (field: {id_field_name})")
                print("      • Can generate edit URLs")
                print("      • Ready for logo processing!")
            else:
                print("   ⚠️  SOME TESTS FAILED")
                print()
                print("   Issues:")
                if count_status == "FAIL":
                    print(f"      • Wrong template count: {len(templates)}")
                if id_status in ["FAIL", "PARTIAL"]:
                    print(f"      • Template ID detection: {id_status}")
                if url_status == "FAIL":
                    print("      • Cannot generate edit URLs")

            print()
            print("=" * 100)
            print()

            # Save detailed results to file
            results = {
                'timestamp': logger.start_time.isoformat() if hasattr(logger, 'start_time') else 'unknown',
                'template_count': len(templates),
                'ui_count': ui_count,
                'id_field_name': id_field_name,
                'templates_with_id': templates_with_id,
                'templates_without_id': templates_without_id,
                'count_status': count_status,
                'id_status': id_status,
                'url_status': url_status,
                'overall': overall,
                'sample_templates': [
                    {
                        'name': t.get('name'),
                        'id': t.get(id_field_name if id_field_name else 'templateId'),
                        'departments': t.get('departments')
                    }
                    for t in templates[:10]
                ]
            }

            results_file = 'test_results_template_ids.json'
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)

            print(f"📄 Detailed results saved to: {results_file}")
            print()
            print("Tab kept open for inspection. Press Ctrl+C to exit.")

            try:
                await asyncio.sleep(3600)
            except KeyboardInterrupt:
                print("\n✋ Test stopped by user")

    except Exception as e:
        logger.exception(f"❌ Test failed: {e}")
        print()
        print("=" * 100)
        print("🎯 VERDICT: ERROR")
        print("=" * 100)


if __name__ == "__main__":
    asyncio.run(test_template_ids_and_count())
