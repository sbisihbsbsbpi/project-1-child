#!/usr/bin/env python3
"""
Test the fix for duplicate logo insertion in RO Invoiced template
"""

import asyncio
import sys
sys.path.append('logo_addition_diagnostics')
from temp_logo_adding_FINAL import TempLogoAdditionFinalService

async def test_ro_invoiced():
    """Test that RO Invoiced doesn't get duplicate logos"""
    
    print("=" * 100)
    print("🧪 TESTING FIX: RO Invoiced Duplicate Logo Prevention")
    print("=" * 100)
    print()
    print("Template: RO Invoiced (SERVICE department)")
    print("Expected: Should NOT insert duplicate logos (Logo 1 and Logo 2 already exist)")
    print("Fix: Dynamic detection now populates globalLogoRowsWithContent")
    print()
    print("=" * 100)
    print()
    
    service = TempLogoAdditionFinalService()
    
    try:
        await service.run(
            departments=["Service"],
            logo_media_id="6a19132b6697f36de6236fb1",  # Tilton.png
            logo_width=200,
            cdp_url="http://localhost:9223",
            auto_publish=False,  # DON'T PUBLISH - just test
            base_url="https://preprodapp.tekioncloud.com",
            template_name="RO Invoiced",  # Only test this specific template
            max_templates=1
        )

        print()
        print("=" * 100)
        print("✅ TEST COMPLETE")
        print("=" * 100)
        print()
        print("CHECK THE RESULTS:")
        print("  1. Check the browser tab for RO Invoiced")
        print("  2. Should see CYAN/MAGENTA (existing logos) but NO new logos added")
        print("  3. Check logs for 'SYNCING DYNAMIC DETECTION TO GLOBAL STATE'")
        print("  4. Should see 'Logo 1' and 'Logo 2' added to global state")
        print("  5. Hardcoded detection should SKIP Logo 1 LEFT and Logo 2 LEFT")
        print()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ro_invoiced())
