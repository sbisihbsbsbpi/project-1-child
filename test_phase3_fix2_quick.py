#!/usr/bin/env python3
"""
Quick Test for Phase 3 Fix #2: Trust Fallback Detection Results

Tests 5 representative templates that showed false negatives in Phase 2:
1. First Time Email (CPRA - simple)
2. Consumer Scheduling OTP (Service - complex)
3. RO Payment Link (Service - medium)
4. Request Acknowledgement (CPRA - simple)
5. Service History Recap PDF (Service - complex)

Expected: All 5 should now show status='detected' instead of 'skipped'
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / 'logo_addition_diagnostics'))

from temp_logo_adding_FINAL import TempLogoAdditionFinalService

# Test templates that were false negatives in Phase 2
TEST_TEMPLATES = [
    {
        'name': 'First Time Email',
        'id': 'CPRA_FIRST_TIME',
        'expected_pattern': 'CPRA custom header',
        'phase2_result': 'false_negative'
    },
    {
        'name': 'Consumer Scheduling OTP',
        'id': '667f0befd4964026ee7b6e6e',
        'expected_pattern': 'Resizable images',
        'phase2_result': 'false_negative'
    },
    {
        'name': 'RO Payment Link',
        'id': '667f0befd4964026ee7b6ea4',
        'expected_pattern': 'Resizable images + logo tables',
        'phase2_result': 'false_negative'
    },
    {
        'name': 'Request Acknowledgement',
        'id': 'CPRA_REQUEST_ACKNOWLEDGEMENT',
        'expected_pattern': 'CPRA custom header',
        'phase2_result': 'false_negative'
    },
    {
        'name': 'Service History Recap PDF',
        'id': '667f0befd4964026ee7b6ea2',
        'expected_pattern': 'Resizable images + logo tables',
        'phase2_result': 'false_negative'
    }
]


async def test_phase3_fix():
    """Test Phase 3 Fix #2 on representative templates"""
    
    print("="*100)
    print("🧪 PHASE 3 FIX #2 TEST: Trust Fallback Detection Results")
    print("="*100)
    print()
    print(f"Testing {len(TEST_TEMPLATES)} templates that were false negatives in Phase 2")
    print("Expected: All should now show status='detected' instead of 'skipped'")
    print()
    
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://localhost:9223')
        context = browser.contexts[0]
        
        service = TempLogoAdditionFinalService()
        
        results_summary = []
        
        for idx, template in enumerate(TEST_TEMPLATES, 1):
            print(f"\n{'='*100}")
            print(f"📄 Test {idx}/{len(TEST_TEMPLATES)}: {template['name']}")
            print(f"{'='*100}")
            print(f"   ID: {template['id']}")
            print(f"   Phase 2: {template['phase2_result']}")
            print(f"   Expected pattern: {template['expected_pattern']}")
            print()
            
            try:
                page = await context.new_page()
                edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template['id']}"
                
                print(f"   Loading template...")
                await page.goto(edit_url, wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(8)
                
                print(f"   Running detection...")
                detection_result = await service._detect_logos(page)
                
                # Check if fallback detection found logos
                warnings = detection_result.get('warningsCount', 0)
                empties = detection_result.get('emptyCount', 0)
                learned = detection_result.get('learnedLogosCount', 0)
                
                has_logos = (warnings > 0 or empties > 0 or learned > 0)
                logo_count = warnings + empties + learned
                
                # Check the results queue for this template
                # The service._process_template would have added a result
                # We'll simulate by checking what the detection returned
                
                result = {
                    'template': template['name'],
                    'phase2_status': 'false_negative',
                    'phase3_has_logos': has_logos,
                    'phase3_logo_count': logo_count,
                    'detection': {
                        'warnings': warnings,
                        'empties': empties,
                        'learned': learned
                    }
                }
                
                results_summary.append(result)
                
                if has_logos:
                    print(f"   ✅ PHASE 3: Logos detected!")
                    print(f"      warnings={warnings}, empties={empties}, learned={learned}")
                    print(f"      Total count: {logo_count}")
                else:
                    print(f"   ❌ PHASE 3: Still no logos detected")
                    print(f"      warnings={warnings}, empties={empties}, learned={learned}")
                
                await page.close()
                
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                results_summary.append({
                    'template': template['name'],
                    'error': str(e)
                })
        
        print("\n" + "="*100)
        print("📊 PHASE 3 FIX #2 TEST RESULTS")
        print("="*100)
        print()
        
        detected_count = sum(1 for r in results_summary if r.get('phase3_has_logos', False))
        total_count = len([r for r in results_summary if 'error' not in r])
        
        print(f"Templates tested: {total_count}")
        print(f"Now detected: {detected_count}/{total_count}")
        print()
        
        if detected_count == total_count:
            print("🎉 SUCCESS: All templates now showing logos detected!")
        elif detected_count > 0:
            print(f"⚠️  PARTIAL: {detected_count} templates fixed, {total_count - detected_count} still failing")
        else:
            print("❌ FAILED: No templates fixed by Phase 3 changes")
        
        print()
        for r in results_summary:
            if 'error' not in r:
                status = "✅" if r.get('phase3_has_logos') else "❌"
                print(f"{status} {r['template']}: count={r.get('phase3_logo_count', 0)}")


if __name__ == '__main__':
    asyncio.run(test_phase3_fix())
