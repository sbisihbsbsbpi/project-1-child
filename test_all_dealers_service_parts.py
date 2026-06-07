#!/usr/bin/env python3
"""
Test logo automation on Service & Parts templates across all dealerships
With auto-publish disabled for testing
"""

import asyncio
import sys
sys.path.append('logo_addition_diagnostics')
from temp_logo_adding_FINAL import TempLogoAdditionFinalService

async def test_all_dealers():
    """Test logo automation on Service & Parts templates"""
    
    print("=" * 100)
    print("🧪 TESTING LOGO AUTOMATION - ALL DEALERSHIPS")
    print("=" * 100)
    print()
    print("Departments: Service & Parts")
    print("Auto-Publish: DISABLED (testing mode)")
    print("Max Templates: ALL (testing all templates)")
    print()
    print("=" * 100)
    print()
    
    service = TempLogoAdditionFinalService()
    
    try:
        await service.run(
            departments=["Service", "Parts"],
            logo_media_id="6a19132b6697f36de6236fb1",  # Tilton.png
            logo_width=200,
            cdp_url="http://localhost:9223",
            auto_publish=False,  # DON'T PUBLISH - just test
            base_url="https://preprodapp.tekioncloud.com"
            # No max_templates - process ALL templates
        )

        print()
        print("=" * 100)
        print("✅ TEST COMPLETE")
        print("=" * 100)
        print()
        print("CHECK THE RESULTS:")
        print("  1. Check browser tabs - should show processed templates")
        print("  2. Check logs/temp_logo_automation_*.log for details")
        print("  3. Check temp_logo_results_FINAL_*.xlsx for summary")
        print()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_all_dealers())
