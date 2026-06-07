#!/usr/bin/env python3
"""
Phase 5: Test fix for Customer Pay Closed template
Verifies that empty containers with wrapper divs are correctly detected as empty
"""
import asyncio
import sys
sys.path.append('logo_addition_diagnostics')
from temp_logo_adding_FINAL import TempLogoAdditionFinalService

async def test_customer_pay_closed():
    """Test the Customer Pay Closed template detection"""
    
    print("="*100)
    print("🧪 PHASE 5: TESTING CUSTOMER PAY CLOSED TEMPLATE")
    print("="*100)
    print()
    print("Template: Customer Pay Closed")
    print("ID: 667f0befd4964026ee7b6e48")
    print("URL: https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48")
    print()
    print("EXPECTED BEHAVIOR:")
    print("  ✅ Top-left container should be detected as EMPTY")
    print("  ✅ Bottom-right container should be detected as HAS IMAGE")
    print("  ✅ Logo should be inserted into top-left container")
    print()
    print("PHASE 5 FIXES TESTED:")
    print("  1. Check for actual <img> tag (not just wrapper div)")
    print("  2. Verify image visibility (display, visibility, opacity)")
    print("  3. Enhanced logging shows all table cells with wrapper/image status")
    print("  4. Dynamic pattern learning shows learned patterns")
    print()
    print("="*100)
    print()
    
    service = TempLogoAdditionFinalService()
    
    try:
        await service.run(
            departments=["Service"],
            template_name="Customer Pay Closed",  # Filter by name
            logo_media_id="6a19132b6697f36de6236fb1",
            logo_width=200,
            cdp_url="http://localhost:9223",
            auto_publish=False,
            base_url="https://preprodapp.tekioncloud.com"
        )

        print()
        print("="*100)
        print("✅ TEST COMPLETE")
        print("="*100)
        print()
        print("CHECK THE LOGS FOR:")
        print("  1. Table cell detection showing 'has-wrapper' vs 'no-wrapper'")
        print("  2. Table cell detection showing 'img.src=...' vs 'no-img'")
        print("  3. Learned patterns with scores and occurrences")
        print("  4. Whether LEFT container was correctly detected as empty")
        print("  5. Whether logo was inserted into LEFT container")
        print()
        print("LOG FILE: logs/temp_logo_automation_*.log")
        print("Look for: '✨ Found logo table' and cell detection details")
        print()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_customer_pay_closed())
