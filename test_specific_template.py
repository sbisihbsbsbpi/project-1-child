#!/usr/bin/env python3
"""
Test specific template with validation
"""

import asyncio
import sys
sys.path.insert(0, 'logo_addition_diagnostics')

from temp_logo_adding_FINAL import TempLogoAdditionFinalService

async def main():
    """Test specific template"""
    
    print("=" * 100)
    print("🧪 TESTING SPECIFIC TEMPLATE")
    print("=" * 100)
    print()
    print("Template ID: 6a0dc5fb62ae8d1a351df064")
    print("URL: https://preprodapp.tekioncloud.com/templates/edit/6a0dc5fb62ae8d1a351df064")
    print("Auto-Publish: DISABLED (testing mode)")
    print()
    print("=" * 100)
    print()
    
    service = TempLogoAdditionFinalService()
    
    # Manually set up a single template
    template = {
        'id': '6a0dc5fb62ae8d1a351df064',
        'name': 'Test Template',
        'departments': ['Service'],
        'dealershipName': 'Alfa Romeo of Cincinnati'
    }
    
    try:
        # Initialize browser connection
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Connect to existing Chrome instance
            browser = await p.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            
            # Create new page for this template
            page = await context.new_page()
            
            print(f"🌐 Opening template...")
            await page.goto(f"https://preprodapp.tekioncloud.com/templates/edit/{template['id']}", 
                          wait_until='domcontentloaded', timeout=30000)
            
            print(f"⏳ Waiting for template to load...")
            await asyncio.sleep(5)
            
            print(f"✅ Template loaded")
            print()
            print(f"🔍 Running logo detection and validation...")
            print()
            
            # Run detection
            detection_result = await service._detect_logos(page)
            
            # Print results
            print()
            print("=" * 100)
            print("📊 DETECTION RESULTS:")
            print("=" * 100)
            print(f"Warnings: {detection_result.get('warnings', 0)}")
            print(f"Empty containers: {detection_result.get('empty', 0)}")
            print(f"Headers: {detection_result.get('headers', 0)}")
            print(f"Replace count: {detection_result.get('replaceCount', 0)}")
            print(f"All detected logos: {detection_result.get('allDetectedLogosCount', 0)}")
            print()
            
            truly_dynamic = detection_result.get('trulyDynamic', {})
            detected_logos = truly_dynamic.get('detectedLogos', [])
            
            if detected_logos:
                print(f"Detected Logos ({len(detected_logos)}):")
                for idx, logo in enumerate(detected_logos, 1):
                    filename = logo.get('imageFilename', 'N/A')
                    src = logo.get('imageSrc', 'N/A')
                    print(f"  {idx}. Filename: {filename}")
                    print(f"     Src: {src[:100]}...")
                print()
            
            print("=" * 100)
            print("🔍 Template tab kept open for manual verification")
            print("=" * 100)
            print()
            print("CHECK:")
            print("  - Open Chrome browser")
            print("  - Look for the template tab")
            print("  - Check detected logos (colored borders)")
            print("  - Verify validation results in console output above")
            print()
            
            # Keep browser open
            print("Press Ctrl+C to close...")
            await asyncio.sleep(999999)
            
    except KeyboardInterrupt:
        print("\n\n✅ Test completed")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
