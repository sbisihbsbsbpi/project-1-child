#!/usr/bin/env python3
"""
COMPREHENSIVE LOGO/HEADER WARNING & REPLACEMENT WORKFLOW
=========================================================

Complete workflow for detecting and replacing logos/headers with warnings.

CRITICAL FINDINGS (2026-05-30):
================================

1. WARNING DETECTION:
   - Warning class: .templates_Image_warningIcon__hCZHMuhEmb
   - Appears as overlay on images with issues
   - Hover → Shows popover with warning message
   - Examples:
     * "This image resolution exceeds 1920x1920px"
     * Wrong dealer logo
     * File size issues
     * Format issues

2. WARNING CAUSE DOESN'T MATTER:
   - Regardless of WHY there's a warning (wrong logo, resolution, etc.)
   - The FIX PROCESS IS THE SAME: Remove → Re-add
   - No "edit" or "replace" option exists in Tekion

3. LOGO/HEADER REPLACEMENT WORKFLOW:
   Remove existing:
     → Hover over logo/header container
     → Click X (remove button)
   
   Add new:
     → Click HEADER or DEALER_LOGO button
     → Select template / upload logo
     → Insert

4. BUTTON STATES:
   - HEADER button: opacity 0.3 (grayed) = exists, 1.0 (active) = none
   - DEALER_LOGO button: opacity 0.3 (grayed) = exists, 1.0 (active) = none
   - Both can exist in same template

5. "INSERT HEADER" POPUP WORKFLOW:
   - Click #HEADER → Adds "+ Add Header" placeholder
   - Click "+ Add Header" → Opens template selection popup
   - Select template (radio button) → Enables Insert button
   - Click Insert → Header added to template

Complete workflow:
1. Detect warning icons on logos/headers
2. Analyze warning message (hover)
3. Remove problematic logo/header (X icon)
4. Verify button becomes active
5. Click appropriate button (HEADER or DEALER_LOGO)
6. Add new logo/header
7. Verify warning is gone

Usage:
    python3 comprehensive_logo_warning_workflow.py
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def detect_warnings():
    """Step 1: Detect all warning icons on images"""
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        working_tab = None
        for page in context.pages:
            if '/templates/edit/' in page.url:
                working_tab = page
                break
        
        if not working_tab:
            logger.error("❌ No template page found")
            return None
        
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: DETECT WARNING ICONS")
        logger.info("=" * 80)
        
        warnings = await working_tab.evaluate("""
            () => {
                const warningIcons = document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb');
                const warnings = [];
                
                for (const icon of warningIcons) {
                    const parent = icon.closest('[class*="SortableItem"]');
                    const img = parent ? parent.querySelector('img') : null;
                    
                    if (img) {
                        const rect = icon.getBoundingClientRect();
                        warnings.push({
                            imageSrc: img.src,
                            imageSize: { width: img.width, height: img.height },
                            imageAlt: img.alt || '',
                            position: { x: Math.round(rect.left), y: Math.round(rect.top) },
                            hasRemoveBtn: parent.querySelector('[class*="removeBtn"]') !== null
                        });
                    }
                }
                
                return warnings;
            }
        """)
        
        logger.info(f"\n✅ Found {len(warnings)} image(s) with warning icons")
        for i, warning in enumerate(warnings, 1):
            logger.info(f"\n   {i}. Image:")
            logger.info(f"      Size: {warning['imageSize']['width']}x{warning['imageSize']['height']}")
            logger.info(f"      Src: {warning['imageSrc'][:80]}...")
            logger.info(f"      Position: ({warning['position']['x']}, {warning['position']['y']})")
            logger.info(f"      Has Remove Button: {warning['hasRemoveBtn']}")
        
        return warnings


async def analyze_warning_message():
    """Step 2: Get warning message by hovering over warning icon"""
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        working_tab = None
        for page in context.pages:
            if '/templates/edit/' in page.url:
                working_tab = page
                break
        
        if not working_tab:
            return None

        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: ANALYZE WARNING MESSAGE")
        logger.info("=" * 80)

        message = await working_tab.evaluate("""
            async () => {
                const warningIcon = document.querySelector('.templates_Image_warningIcon__hCZHMuhEmb');
                if (!warningIcon) return { found: false };

                // Hover to trigger popover
                warningIcon.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                warningIcon.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));

                await new Promise(resolve => setTimeout(resolve, 500));

                const popover = document.querySelector('.ant-popover');

                return {
                    found: true,
                    hasPopover: popover !== null,
                    message: popover ? popover.textContent.trim() : null
                };
            }
        """)

        if message['found'] and message['hasPopover']:
            logger.info(f"\n✅ Warning message:")
            logger.info(f"   {message['message']}")
        else:
            logger.info("\n⚠️  No warning message found")

        return message


async def check_button_states():
    """Step 3: Check HEADER and DEALER_LOGO button states"""
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]

        working_tab = None
        for page in context.pages:
            if '/templates/edit/' in page.url:
                working_tab = page
                break

        if not working_tab:
            return None

        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: CHECK BUTTON STATES")
        logger.info("=" * 80)

        states = await working_tab.evaluate("""
            () => {
                const headerBtn = document.querySelector('#HEADER');
                const dealerLogoBtn = document.querySelector('#DEALER_LOGO');

                return {
                    header: headerBtn ? {
                        opacity: parseFloat(getComputedStyle(headerBtn).opacity),
                        status: parseFloat(getComputedStyle(headerBtn).opacity) < 1 ? 'GRAYED' : 'ACTIVE'
                    } : null,
                    dealerLogo: dealerLogoBtn ? {
                        opacity: parseFloat(getComputedStyle(dealerLogoBtn).opacity),
                        status: parseFloat(getComputedStyle(dealerLogoBtn).opacity) < 1 ? 'GRAYED' : 'ACTIVE'
                    } : null
                };
            }
        """)

        logger.info(f"\n📊 Button States:")
        if states['header']:
            logger.info(f"   HEADER: {states['header']['status']} (opacity: {states['header']['opacity']})")
        if states['dealerLogo']:
            logger.info(f"   DEALER_LOGO: {states['dealerLogo']['status']} (opacity: {states['dealerLogo']['opacity']})")

        return states


async def run_complete_workflow():
    """Run complete workflow: Detect → Analyze → Report"""
    logger.info("\n" + "=" * 100)
    logger.info("🎯 COMPREHENSIVE LOGO/HEADER WARNING & REPLACEMENT WORKFLOW")
    logger.info("=" * 100)

    # Step 1: Detect warnings
    warnings = await detect_warnings()

    # Step 2: Analyze warning message
    if warnings and len(warnings) > 0:
        message = await analyze_warning_message()

    # Step 3: Check button states
    states = await check_button_states()

    # Summary
    logger.info("\n" + "=" * 100)
    logger.info("📊 WORKFLOW SUMMARY")
    logger.info("=" * 100)

    logger.info(f"\n✅ Images with warnings: {len(warnings) if warnings else 0}")
    logger.info(f"✅ Button states analyzed: {bool(states)}")

    logger.info("\n💡 NEXT STEPS TO FIX WARNINGS:")
    logger.info("   1. Hover over logo/header container")
    logger.info("   2. Click X (remove button) to remove")
    logger.info("   3. Verify button becomes ACTIVE (opacity 1.0)")
    logger.info("   4. Click HEADER or DEALER_LOGO button")
    logger.info("   5. Add new logo/header")
    logger.info("   6. Verify warning is gone")

    logger.info("\n" + "=" * 100)
    logger.info("✅ WORKFLOW ANALYSIS COMPLETE")
    logger.info("=" * 100)


if __name__ == "__main__":
    asyncio.run(run_complete_workflow())
