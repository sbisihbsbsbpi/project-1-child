#!/usr/bin/env python3
"""
Test the logo addition + department filter integration
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'automation'))

from logo_addition_from_filter import add_logos_to_filtered_templates


async def main():
    print("=" * 100)
    print("🧪 TESTING LOGO ADDITION + DEPARTMENT FILTER INTEGRATION")
    print("=" * 100)
    print()
    
    print("⚠️  This test will add logos to 2 templates in Service & Parts departments")
    print()
    
    result = await add_logos_to_filtered_templates(
        departments=['Service', 'Parts'],
        logo_media_id="6a19132b6697f36de6236fb1",
        logo_width=160,
        max_templates=2,  # Just 2 templates for testing
        keep_tabs_open=False
    )
    
    print()
    print("=" * 100)
    print("📊 TEST RESULTS")
    print("=" * 100)
    
    if result.get('success'):
        print(f"✅ SUCCESS!")
        print(f"   Job ID: {result.get('job_id')}")
        print(f"   Departments: {', '.join(result.get('departments', []))}")
        print(f"   Templates found: {result.get('templates_found')}")
        print(f"   Templates processed: {result.get('templates_processed')}")
        print(f"   Successful: {result.get('successful')}")
        print(f"   Failed: {result.get('failed')}")
        print()
        
        if result.get('results'):
            print("Detailed results:")
            for r in result['results']:
                status = "✅" if r['success'] else "❌"
                print(f"  {status} {r['name']}")
    else:
        print(f"❌ FAILED: {result.get('error')}")
    
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
