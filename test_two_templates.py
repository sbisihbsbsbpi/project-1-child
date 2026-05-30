#!/usr/bin/env python3
"""
Test the updated removal logic on 2 templates:
1. Service History Recap PDF (667f0befd4964026ee7b6ea2) - 2 logos with warnings
2. CPRA_REQUEST_COMPLETION_DATA_CORRECTION - 1 logo (healthy)

This validates the loop-based removal fix.
"""

import asyncio
import sys
import os

# Add parent directory to path to import the updater
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parallel_logo_warning_updater import ParallelLogoUpdater

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def main():
    logger.info("="*100)
    logger.info("🧪 TESTING UPDATED REMOVAL LOGIC ON 2 TEMPLATES")
    logger.info("="*100)
    logger.info("\nTemplate 1: Service History Recap PDF (2 logos with warnings)")
    logger.info("Template 2: CPRA Data Correction (1 healthy logo)")
    logger.info("\nThis tests the new loop-based removal logic.\n")

    # Define test templates
    test_templates = [
        {
            'id': '667f0befd4964026ee7b6ea2',
            'name': 'Service History Recap PDF',
            'departments': ['Service']
        },
        {
            'id': 'CPRA_REQUEST_COMPLETION_DATA_CORRECTION',
            'name': 'Request Completion: Data Correction',
            'departments': ['Service']
        }
    ]

    updater = ParallelLogoUpdater()

    try:
        # Step 1: Connect to browser
        await updater.connect_to_browser()

        # Step 2: Navigate to template list
        if not await updater.navigate_to_template_list("https://preprodapp.tekioncloud.com"):
            logger.error("❌ Failed to navigate to template list")
            return 1

        # Step 3: Manually set templates (bypass API fetch)
        updater.templates = test_templates
        logger.info(f"\n✅ Loaded {len(test_templates)} templates for testing")

        # Step 4: Open template tabs
        opened_pages = await updater.open_template_tabs("https://preprodapp.tekioncloud.com")

        if not opened_pages:
            logger.error("❌ No tabs opened")
            return 1

        # Step 5: Process templates
        await updater.process_all_templates_parallel(opened_pages)

        # Step 6: Print results
        logger.info("\n" + "="*100)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("="*100)

        results = updater.results
        success_count = sum(1 for r in results if r['success'])

        for idx, result in enumerate(results, 1):
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            logger.info(f"\n[{idx}] {result['template_name']}")
            logger.info(f"    Status: {status}")
            logger.info(f"    Action: {result['action']}")
            logger.info(f"    Warnings: {result['warnings_detected']}")
            logger.info(f"    Logos: {len(result.get('logos', []))}")
            if result.get('message'):
                logger.info(f"    Message: {result['message']}")
            if result.get('error'):
                logger.info(f"    Error: {result['error']}")

        logger.info(f"\n{'='*100}")
        logger.info(f"🎯 FINAL SCORE: {success_count}/{len(results)} templates succeeded")
        logger.info(f"{'='*100}")

        if success_count == len(results):
            logger.info("\n🎉 ALL TESTS PASSED! ✅")
            logger.info("   - Service History Recap PDF: Fixed (removed both logos)")
            logger.info("   - CPRA template: Still working correctly")
            return 0
        else:
            logger.info("\n❌ SOME TESTS FAILED")
            for r in results:
                if not r['success']:
                    logger.info(f"   Failed: {r['template_name']} - {r.get('error', 'Unknown error')}")
            return 1

    except KeyboardInterrupt:
        logger.info("\n✋ Test interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
