#!/usr/bin/env python3
"""
Quick test script for RO Created template only
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logo_addition_diagnostics.temp_logo_adding_FINAL import TemplateLogoAutomation

async def main():
    """Test RO Created template only"""
    
    # Create automation instance
    automation = TemplateLogoAutomation(
        base_url="https://preprodapp.tekioncloud.com",
        cdp_url="http://localhost:9223",
        logo_media_id="6a19132b6697f36de6236fb1",
        logo_width="160px",
        auto_publish=False  # Keep tabs open for inspection
    )
    
    try:
        # Connect to browser
        print("🌐 Connecting to browser...")
        await automation.connect()
        
        # Navigate to templates list
        print("📍 Navigating to templates list...")
        await automation.page.goto("https://preprodapp.tekioncloud.com/templates/list")
        await automation.page.wait_for_load_state("networkidle", timeout=10000)
        
        # Apply filter for Service & Parts
        print("🎯 Applying Service & Parts filter...")
        await automation.apply_department_filter(["Service", "Parts"])
        
        # Get all templates
        templates = automation.templates
        print(f"\n✅ Found {len(templates)} total templates")
        
        # Find RO Created template
        ro_created = None
        for idx, template in enumerate(templates, 1):
            if template.get('name') == 'RO Created':
                ro_created = template
                print(f"\n🎯 Found 'RO Created' at position {idx}")
                print(f"   ID: {template.get('templateId')}")
                print(f"   Departments: {', '.join(template.get('departments', []))}")
                break
        
        if not ro_created:
            print("\n❌ 'RO Created' template not found!")
            return
        
        # Process just this template
        print(f"\n{'='*100}")
        print(f"📄 PROCESSING: RO Created")
        print(f"{'='*100}")
        
        await automation.process_template(ro_created, 1, 1)
        
        print(f"\n{'='*100}")
        print("✅ TEST COMPLETE")
        print(f"{'='*100}")
        print("\n📊 Check the logs for detailed detection results:")
        print(f"   Log file: {automation.logger.handlers[0].baseFilename if automation.logger.handlers else 'N/A'}")
        print("\n🔍 The browser tab is still open for inspection (--no-publish)")
        print("   Check the detection logic to see if:")
        print("   - Logo Table 2 & 3 were rejected as 'not logo tables'")
        print("   - Logo 1 LEFT was skipped (Logo 1 CENTER has logo)")
        print("   - Logo 4 LEFT was skipped (Logo 4 RIGHT has logo)")
        
        # Keep browser open for inspection
        print("\n⏸️  Browser will stay open. Press Ctrl+C when done inspecting...")
        await asyncio.sleep(999999)
        
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🧹 Cleaning up...")
        # Don't close browser - let user inspect
        # await automation.close()

if __name__ == '__main__':
    asyncio.run(main())
