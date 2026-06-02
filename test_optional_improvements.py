#!/usr/bin/env python3
"""
Test script for optional improvements to temp_logo_adding_FINAL.py

Tests the newly implemented functions:
1. _center_logo_without_warning
2. _enlarge_logo_without_warning

These functions handle centering and enlarging logos that were detected
via table-based detection without warning icons.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logo_addition_diagnostics.temp_logo_adding_FINAL import TempLogoAdditionFinalService

async def main():
    """Test the optional improvements on a single template"""
    
    service = TempLogoAdditionFinalService()
    
    print("=" * 100)
    print("🧪 TESTING OPTIONAL IMPROVEMENTS")
    print("=" * 100)
    print()
    print("Testing newly implemented functions:")
    print("  1. ✅ _center_logo_without_warning")
    print("  2. ✅ _enlarge_logo_without_warning")
    print()
    print("Test template: Service History Recap PDF (has logos without warnings)")
    print("Expected behavior:")
    print("  - Logos with warnings → Replace + Center + Enlarge")
    print("  - Logos without warnings → Replace + Center + Enlarge (NEW!)")
    print()
    print("=" * 100)
    print()
    
    # Run on 1 Service template to test the improvements
    await service.run(
        departments=['Service'],
        max_templates=1,
        logo_media_id="6a19132b6697f36de6236fb1",
        logo_width=160,
        auto_publish=False,  # Don't publish, just test the functions
        cdp_url="http://localhost:9223",
        base_url="https://preprodapp.tekioncloud.com"
    )
    
    print()
    print("=" * 100)
    print("✅ TEST COMPLETE")
    print("=" * 100)
    print()
    print("Check the logs for:")
    print("  - 'Successfully centered logo X' messages")
    print("  - 'Successfully enlarged logo X to Ypx' messages")
    print()
    print("These indicate the optional improvements are working!")
    print()

if __name__ == "__main__":
    asyncio.run(main())
