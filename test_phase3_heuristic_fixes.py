#!/usr/bin/env python3
"""
Test Phase 3 Heuristic Fixes

Tests the two heuristic improvements:
1. Allow logos at top of page (rect.top >= 0 instead of > 100)
2. Lower score threshold (1 instead of 2)

Tests on 3 templates:
- First Time Email (CPRA - grayed header)
- Consumer Scheduling OTP (complex Service)
- RO Payment Link (medium Service with logo tables)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'logo_addition_diagnostics'))

from temp_logo_adding_FINAL import TempLogoAdditionFinalService
from playwright.async_api import async_playwright


async def test_template(template_id, template_name):
    """Test a single template"""
    print(f"\n{'='*100}")
    print(f"📄 Testing: {template_name}")
    print(f"   ID: {template_id}")
    print(f"{'='*100}")
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://localhost:9223')
        context = browser.contexts[0]
        page = await context.new_page()
        
        try:
            edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
            print(f"   Loading...")
            await page.goto(edit_url, wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(8)
            
            print(f"   Running detection...")
            service = TempLogoAdditionFinalService()
            detection_result = await service._detect_logos(page)
            
            # Extract results
            warnings = detection_result.get('warningsCount', 0)
            empties = detection_result.get('emptyCount', 0)
            learned = detection_result.get('learnedLogosCount', 0)
            logo_tables = detection_result.get('logoTablesCount', 0)
            all_detected = detection_result.get('allDetectedLogosCount', 0)  # NEW field

            # Check dynamic detection
            dynamic = detection_result.get('trulyDynamic', {})
            dynamic_enabled = dynamic.get('enabled', False)
            dynamic_logos = len(dynamic.get('detectedLogos', []))

            # Calculate has_logos (Phase 3 logic)
            has_logos = (warnings > 0 or empties > 0 or learned > 0 or all_detected > 0)
            total_count = max(warnings + empties + learned, all_detected)
            
            print(f"\n   📊 DETECTION RESULTS:")
            print(f"      warnings: {warnings}")
            print(f"      empties: {empties}")
            print(f"      learned: {learned}")
            print(f"      logo_tables: {logo_tables}")
            print(f"      allDetectedLogosCount: {all_detected} ✨ NEW")
            print(f"      dynamic_enabled: {dynamic_enabled}")
            print(f"      dynamic_logos: {dynamic_logos}")
            print(f"\n      ✨ PHASE 3: has_logos = {has_logos}, count = {total_count}")
            
            if has_logos:
                print(f"\n   ✅ SUCCESS: Template now detected!")
            else:
                print(f"\n   ❌ STILL FAILING: No logos detected")
            
            await page.close()
            
            return {
                'name': template_name,
                'has_logos': has_logos,
                'count': total_count,
                'warnings': warnings,
                'empties': empties,
                'learned': learned,
                'all_detected': all_detected,
                'dynamic_enabled': dynamic_enabled,
                'dynamic_logos': dynamic_logos
            }
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            await page.close()
            return {'name': template_name, 'error': str(e)}


async def main():
    print("="*100)
    print("🧪 PHASE 3 HEURISTIC FIXES TEST")
    print("="*100)
    print("\nChanges tested:")
    print("  1. Allow logos at top of page (rect.top >= 0 instead of > 100)")
    print("  2. Lower score threshold (>= 1 instead of >= 2)")
    print()
    
    tests = [
        ('CPRA_FIRST_TIME', 'First Time Email'),
        ('667f0befd4964026ee7b6e6e', 'Consumer Scheduling OTP'),
        ('667f0befd4964026ee7b6ea4', 'RO Payment Link'),
    ]
    
    results = []
    for template_id, template_name in tests:
        result = await test_template(template_id, template_name)
        results.append(result)
    
    print("\n" + "="*100)
    print("📊 SUMMARY")
    print("="*100)
    
    success_count = sum(1 for r in results if r.get('has_logos', False))
    total = len([r for r in results if 'error' not in r])
    
    print(f"\nTemplates detected: {success_count}/{total}")
    print()
    
    for r in results:
        if 'error' not in r:
            status = "✅" if r.get('has_logos') else "❌"
            print(f"{status} {r['name']}: count={r.get('count', 0)} " +
                  f"(w={r.get('warnings', 0)}, e={r.get('empties', 0)}, " +
                  f"l={r.get('learned', 0)}, a={r.get('all_detected', 0)}, d={r.get('dynamic_logos', 0)})")
    
    print()
    if success_count == total:
        print("🎉 ALL TESTS PASSED!")
    elif success_count > 0:
        print(f"⚠️  {success_count}/{total} tests passed")
    else:
        print("❌ ALL TESTS FAILED - Need different approach")


if __name__ == '__main__':
    asyncio.run(main())
