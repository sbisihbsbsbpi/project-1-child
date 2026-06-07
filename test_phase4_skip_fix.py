#!/usr/bin/env python3
"""
Phase 4: Test fix for skipped templates
Tests templates that were skipped in Phase 3 despite having logos
"""
import asyncio
import sys
sys.path.append('logo_addition_diagnostics')
from temp_logo_adding_FINAL import TempLogoAdditionFinalService

async def test_template(template_id, template_name):
    """Test a single template"""
    print(f"\n{'='*100}")
    print(f"📄 Testing: {template_name}")
    print(f"   ID: {template_id}")
    print(f"{'='*100}")
    
    automation = TempLogoAdditionFinalService(
        logo_media_id="6a19132b6697f36de6236fb1",
        logo_width=200,
        cdp_url="http://localhost:9223",
        auto_publish=False,
        base_url="https://preprodapp.tekioncloud.com",
        departments=None,
        max_templates=None
    )
    
    try:
        await automation.start()
        
        # Process just this one template
        result = await automation._process_template({
            'id': template_id,
            'name': template_name,
            'departments': ['SERVICE']
        })
        
        print(f"\n   ✅ Test complete")
        return result
        
    finally:
        if automation.browser:
            await automation.browser.close()

async def main():
    """Test skipped templates"""
    print("="*100)
    print("🧪 PHASE 4: TESTING FIX FOR SKIPPED TEMPLATES")
    print("="*100)
    print("\nChanges tested:")
    print("  1. Check allDetectedLogosCount before deciding to skip")
    print("  2. Mark templates as DETECTED if dynamic detection found logos")
    print("\n")
    
    # Test templates that were skipped in Phase 3
    test_cases = [
        ("667f0befd4964026ee7b6e6e", "Consumer Scheduling OTP"),
        ("667f0befd4964026ee7b6e46", "RO Invoiced"),
        ("667f0befd4964026ee7b6ea8", "Bulk RO Download"),
    ]
    
    results = []
    for template_id, template_name in test_cases:
        try:
            result = await test_template(template_id, template_name)
            results.append({
                'name': template_name,
                'success': True,
                'result': result
            })
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({
                'name': template_name,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*100)
    print("📊 SUMMARY")
    print("="*100)
    print()
    
    success_count = sum(1 for r in results if r['success'])
    print(f"Templates tested: {success_count}/{len(test_cases)}")
    print()
    
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{status} {r['name']}")
    
    print("\n🎉 ALL TESTS COMPLETE!")

if __name__ == "__main__":
    asyncio.run(main())
