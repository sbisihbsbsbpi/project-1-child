#!/usr/bin/env python3
"""
Test Guardrail: One Logo Per Row
=================================

Verifies that the guardrail prevents multiple logos from being processed
in the same logo row (Logo 1, Logo 2, etc.)

Date: June 2, 2026
"""

import asyncio
import sys
import os

# Add the logo_addition_diagnostics directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logo_addition_diagnostics'))

from temp_logo_adding_FINAL import TempLogoAdditionFinalService, logger

async def main():
    """Test the guardrail on a single template"""
    
    logger.info("=" * 100)
    logger.info("🛡️  GUARDRAIL TEST - ONE LOGO PER ROW")
    logger.info("=" * 100)
    logger.info("")
    logger.info("Testing on: Service History Recap PDF")
    logger.info("Expected behavior:")
    logger.info("  - Logo 1 has warning → Replace Logo 1")
    logger.info("  - Logo 2 LEFT empty → Insert into Logo 2 LEFT")
    logger.info("  - Logo 2 CENTER empty → ⏭️ SKIP (Logo 2 already has logo)")
    logger.info("")
    logger.info("=" * 100)
    logger.info("")
    
    service = TempLogoAdditionFinalService()
    
    # Test on a single template that we know has multiple empty containers
    await service.run(
        departments=['Service'],
        max_templates=1,  # Just test on first template
        logo_media_id="6a19132b6697f36de6236fb1",
        logo_width=160,
        auto_publish=False,
        cdp_url="http://localhost:9223",
        base_url="https://preprodapp.tekioncloud.com"
    )
    
    logger.info("")
    logger.info("=" * 100)
    logger.info("✅ GUARDRAIL TEST COMPLETE")
    logger.info("=" * 100)
    logger.info("")
    logger.info("📋 Review the logs above:")
    logger.info("   1. Check for '⏭️ Skipping' messages")
    logger.info("   2. Verify only 1 logo processed per logo row")
    logger.info("   3. Confirm 'GUARDRAIL: Only 1 logo per logo row allowed' messages")
    logger.info("")
    logger.info("🌐 Check the browser tab:")
    logger.info("   - Logo 1 should have 1 logo")
    logger.info("   - Logo 2 should have 1 logo (not 2 or 3)")
    logger.info("")

if __name__ == "__main__":
    asyncio.run(main())
