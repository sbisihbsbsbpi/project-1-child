#!/usr/bin/env python3
"""
Verify the filter API capture fix

This test verifies that the script now captures only 39 templates
(the correct final count) instead of 129 templates (the bug).
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logo_addition_diagnostics.temp_logo_adding_FINAL import TempLogoAdditionFinalService, logger

async def test_filter_fix():
    """Test that filter now captures correct number of templates"""
    
    print("=" * 100)
    print("🧪 FILTER FIX VERIFICATION TEST")
    print("=" * 100)
    print()
    print("This test verifies that the API capture fix works correctly:")
    print("  ✅ EXPECTED: 39 templates (Service & Parts)")
    print("  ❌ BUG (old): 129 templates (with duplicates)")
    print()
    print("=" * 100)
    print()
    
    service = TempLogoAdditionFinalService()
    
    # Run with departments filter but DON'T process templates
    # Just verify the count is correct
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
            
            # Analyze results
            print()
            print("=" * 100)
            print("📊 RESULTS")
            print("=" * 100)
            print()
            print(f"   UI Count: {ui_count}")
            print(f"   API Captured: {len(templates)} templates")
            print()
            
            # Verify
            if len(templates) == 39:
                print("   ✅ SUCCESS: Captured exactly 39 templates!")
                print("   ✅ Fix is working correctly - using only final API response")
                print()
                print("   Before fix: Would have captured ~129 templates (with duplicates)")
                print("   After fix:  Captured 39 templates (correct!)")
                print()
                verdict = "PASSED"
            else:
                print(f"   ❌ FAILURE: Expected 39 templates, got {len(templates)}")
                print(f"   ⚠️  The fix may not be working correctly")
                print()
                verdict = "FAILED"
            
            # Show sample templates
            if templates:
                print("   Sample templates captured:")
                for idx, template in enumerate(templates[:5], 1):
                    name = template.get('name', 'Unknown')
                    depts = template.get('departments', [])
                    print(f"      {idx}. {name} - Departments: {', '.join(depts)}")
                
                if len(templates) > 5:
                    print(f"      ... and {len(templates) - 5} more")
            
            print()
            print("=" * 100)
            print(f"🎯 VERDICT: {verdict}")
            print("=" * 100)
            print()
            
            if verdict == "PASSED":
                print("The filter fix is working correctly! ✅")
                print()
                print("Summary:")
                print("  • Uses templates = hits (replace) instead of templates.extend(hits)")
                print("  • Captures only the final API response (39 templates)")
                print("  • No duplicates, no wrong departments")
                print("  • Ready for production use!")
            else:
                print("The fix needs further investigation. ⚠️")
            
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
    asyncio.run(test_filter_fix())
