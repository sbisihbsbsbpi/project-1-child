#!/usr/bin/env python3
"""
Test Phase 2 Enhancements on Consumer Scheduling OTP Template

This script tests the enhanced logo detection on the template that previously
showed a false negative (Consumer Scheduling OTP).

Expected Results (Phase 2):
- Should detect logo via data-learned-logo="logo-7" marker
- Should report: has_logos=true, logo_count=1, learned_logos_count=1
- API cross-validation should confirm: false_negative=false

Before Phase 2:
- has_logos: false ❌
- logo_count: 0 ❌
- learned_logos_count: 0

After Phase 2:
- has_logos: true ✅
- logo_count: 1 ✅
- learned_logos_count: 1 ✅
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / 'logo_addition_diagnostics'))

from temp_logo_adding_FINAL import TempLogoAdditionFinalService
from playwright.async_api import async_playwright


async def test_consumer_scheduling_otp():
    """Test Phase 2 detection on Consumer Scheduling OTP template"""
    
    print("="*100)
    print("🧪 PHASE 2 TEST: Consumer Scheduling OTP Template")
    print("="*100)
    print()
    
    # Template details from metadata
    TEMPLATE_ID = "667f0befd4964026ee7b6ea8"  # Consumer Scheduling OTP ID from metadata
    TEMPLATE_NAME = "Consumer Scheduling OTP"
    
    # Expected API data (from TEMPLATE_LOGO_UPDATE_ANALYSIS.md)
    EXPECTED_THUMBNAIL_MEDIA_ID = "6a1920d16697f36de6236fc9"
    
    print(f"📄 Testing Template: {TEMPLATE_NAME}")
    print(f"   ID: {TEMPLATE_ID}")
    print(f"   Expected mediaId: {EXPECTED_THUMBNAIL_MEDIA_ID}")
    print()
    
    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.connect_over_cdp('http://localhost:9223')
        context = browser.contexts[0]
        
        print("✅ Connected to existing browser session")
        print()
        
        # Create page and navigate
        page = await context.new_page()
        edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{TEMPLATE_ID}"
        
        print(f"📂 Loading template editor...")
        print(f"   URL: {edit_url}")
        await page.goto(edit_url, wait_until='domcontentloaded', timeout=20000)
        await asyncio.sleep(10)  # Wait for full render
        
        print("✅ Template loaded")
        print()
        
        # Run detection
        print("🔍 Running Phase 2 Enhanced Detection...")
        print("-" * 100)
        
        # Create service instance just to access _detect_logos
        service = TempLogoAdditionFinalService()
        detection_result = await service._detect_logos(page)
        
        print()
        print("="*100)
        print("📊 DETECTION RESULTS")
        print("="*100)
        print()
        
        # Extract key metrics
        warnings_count = detection_result.get('warningsCount', 0)
        empty_count = detection_result.get('emptyCount', 0)
        learned_logos = detection_result.get('learnedLogosCount', 0)
        logo_tables = detection_result.get('logoTablesCount', 0)
        
        # Calculate has_logos (Phase 2 logic)
        has_logos = (warnings_count > 0 or empty_count > 0 or learned_logos > 0)
        logo_count = warnings_count + empty_count + learned_logos
        
        # Print results
        print("🎯 Core Detection:")
        print(f"   • Logo tables found: {logo_tables}")
        print(f"   • Warnings (logos to replace): {warnings_count}")
        print(f"   • Empty containers: {empty_count}")
        print(f"   • Learned logos (Phase 2): {learned_logos} {'✨' if learned_logos > 0 else ''}")
        print()
        
        print("📈 Calculated Results:")
        print(f"   • has_logos: {has_logos} {'✅' if has_logos else '❌'}")
        print(f"   • logo_count: {logo_count}")
        print()
        
        # Show learned logo details
        if learned_logos > 0:
            truly_dynamic = detection_result.get('trulyDynamic', {})
            learned_markers = truly_dynamic.get('learnedLogoMarkers', [])
            
            print("✨ Phase 2 Enhancement #1: Learned Logo Markers")
            for i, marker in enumerate(learned_markers, 1):
                print(f"   Logo {i}:")
                print(f"      • Marker: {marker.get('marker', 'N/A')}")
                print(f"      • Size: {marker.get('rect', {}).get('width', 0)}x{marker.get('rect', {}).get('height', 0)}px")
                print(f"      • Position: top={marker.get('rect', {}).get('top', 0)}px")
                print(f"      • Detection Method: {marker.get('detectionMethod', 'N/A')}")
            print()
        
        # Show enhanced features
        enhanced = detection_result.get('enhancedFeatures', {})
        if enhanced:
            print("📊 Template Complexity (Phase 1):")
            print(f"   • Sortable items: {enhanced.get('sortableItemCount', 0)}")
            print(f"   • Total tables: {enhanced.get('totalTableCount', 0)}")
            print(f"   • Non-logo tables: {enhanced.get('nonLogoTableCount', 0)}")
            print(f"   • Has buttons: {enhanced.get('hasButtons', False)}")
            print(f"   • Dynamic tags: {enhanced.get('dynamicTagCount', 0)}")
            print()
        
        # Verdict
        print("="*100)
        print("🎯 PHASE 2 TEST VERDICT")
        print("="*100)
        print()
        
        if has_logos and learned_logos > 0:
            print("✅ SUCCESS! Phase 2 Enhancement #1 Working Correctly")
            print(f"   • Detected {learned_logos} logo(s) via data-learned-logo markers")
            print("   • False negative RESOLVED")
            print("   • Consumer Scheduling OTP now correctly identified as having a logo")
        elif has_logos and (warnings_count > 0 or empty_count > 0):
            print("⚠️  PARTIAL: Detection found logos via other methods")
            print(f"   • Warnings: {warnings_count}, Empties: {empty_count}")
            print("   • But data-learned-logo markers not found")
        else:
            print("❌ FAILED: Still showing false negative")
            print("   • No logos detected by any method")
            print("   • Phase 2 enhancements may need debugging")
        
        print()
        
        # Close page
        await page.close()
        
        return {
            'has_logos': has_logos,
            'logo_count': logo_count,
            'learned_logos': learned_logos,
            'success': has_logos and learned_logos > 0
        }


if __name__ == '__main__':
    result = asyncio.run(test_consumer_scheduling_otp())
    sys.exit(0 if result['success'] else 1)
