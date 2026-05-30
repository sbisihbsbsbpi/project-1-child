#!/usr/bin/env python3
"""
Test script to detect and analyze the Change Image popup
Just opens popup and shows what's in it
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("=" * 100)
    logger.info("🔍 TESTING CHANGE IMAGE POPUP - DETECT & ANALYZE")
    logger.info("=" * 100)
    
    template_id = "667f0befd4964026ee7b6ea2"  # Service History Recap PDF
    url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    
    async with async_playwright() as playwright:
        # Connect to existing browser
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]

        # Get or create page
        pages = context.pages
        page = None
        for existing_page in pages:
            if template_id in existing_page.url:
                page = existing_page
                logger.info(f"✅ Found existing template page")
                break

        if not page:
            logger.info(f"Opening template: {url}")
            page = await context.new_page()
            await page.goto(url)
            await asyncio.sleep(20)  # Wait for load
        
        logger.info("\n" + "=" * 100)
        logger.info("STEP 1: Finding logo with warning")
        logger.info("=" * 100)
        
        # Find logo with warning
        container_found = await page.evaluate("""
            () => {
                const warningIcon = document.querySelector('.templates_Image_warningIcon__hCZHMuhEmb');
                if (!warningIcon) return false;
                
                const sortableItem = warningIcon.closest('[class*="SortableItem"]');
                if (sortableItem) {
                    sortableItem.setAttribute('data-logo-to-inspect', 'true');
                    return true;
                }
                return false;
            }
        """)
        
        if not container_found:
            logger.error("❌ No logo with warning found")
            return
        
        logger.info("✅ Found logo with warning")
        
        logger.info("\n" + "=" * 100)
        logger.info("STEP 2: Hovering to reveal toolbar")
        logger.info("=" * 100)
        
        container = await page.query_selector('[data-logo-to-inspect="true"]')
        await container.hover(force=True)
        await asyncio.sleep(2)
        logger.info("✅ Hovered")
        
        logger.info("\n" + "=" * 100)
        logger.info("STEP 3: Finding toolbar buttons")
        logger.info("=" * 100)

        # First, detect all buttons/icons in the toolbar
        toolbar_info = await page.evaluate("""
            () => {
                const container = document.querySelector('[data-logo-to-inspect="true"]');
                if (!container) return { found: false };

                // Find all clickable elements (buttons, icons, etc.)
                const buttons = Array.from(container.querySelectorAll('button, [role="button"], svg, [class*="btn"], [class*="icon"]'));

                return {
                    found: true,
                    buttonCount: buttons.length,
                    buttons: buttons.map((btn, idx) => ({
                        index: idx,
                        tagName: btn.tagName,
                        title: btn.getAttribute('title') || '',
                        ariaLabel: btn.getAttribute('aria-label') || '',
                        className: btn.className || '',
                        innerText: btn.innerText || ''
                    }))
                };
            }
        """)

        if toolbar_info['found']:
            logger.info(f"✅ Found {toolbar_info['buttonCount']} toolbar elements:")
            for btn in toolbar_info['buttons']:
                logger.info(f"   [{btn['index']}] {btn['tagName']}")
                if btn['title']:
                    logger.info(f"       Title: {btn['title']}")
                if btn['ariaLabel']:
                    logger.info(f"       Aria-Label: {btn['ariaLabel']}")
                if btn['className']:
                    logger.info(f"       Class: {btn['className'][:100]}")

        # Now try to click Change Image
        logger.info("\n   Attempting to click Change Image...")
        change_clicked = await page.evaluate("""
            () => {
                const container = document.querySelector('[data-logo-to-inspect="true"]');
                if (!container) return { clicked: false, reason: 'No container' };

                // Try multiple selectors
                const selectors = [
                    '[title="Change Image"]',
                    '[aria-label="icon-switch"]',
                    '[class*="switch"]',
                    'button[title*="Change"]',
                    'button[title*="Replace"]'
                ];

                for (const selector of selectors) {
                    const btn = container.querySelector(selector);
                    if (btn) {
                        btn.click();
                        return { clicked: true, selector: selector };
                    }
                }

                return { clicked: false, reason: 'No matching button found' };
            }
        """)

        if not change_clicked['clicked']:
            logger.error(f"❌ Change Image button not found: {change_clicked.get('reason', 'Unknown')}")
            logger.info("\n📝 Available buttons listed above. Update selectors if needed.")
            return

        logger.info(f"✅ Change Image clicked (using: {change_clicked['selector']})")

        await asyncio.sleep(3)
        
        logger.info("\n" + "=" * 100)
        logger.info("STEP 4: ANALYZING POPUP - DETECTING ALL LOGOS")
        logger.info("=" * 100)

        popup_info = await page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]');
                if (!popup) return { found: false };

                // Find all logo images in the popup
                const allImages = Array.from(popup.querySelectorAll('img'));

                const logos = allImages.map((img, idx) => {
                    const src = img.src || '';
                    const parent = img.closest('div[class*="item"], div[role="button"], div[class*="card"]');

                    // Check if this logo is selected/active
                    const isSelected = parent?.className?.includes('selected') ||
                                      parent?.className?.includes('active') ||
                                      parent?.getAttribute('aria-selected') === 'true' ||
                                      parent?.querySelector('[class*="check"]') !== null;

                    // Extract media ID from URL
                    const mediaIdMatch = src.match(/media_([a-f0-9]{24})/);
                    const mediaId = mediaIdMatch ? mediaIdMatch[1] : 'unknown';

                    return {
                        index: idx,
                        src: src.substring(0, 150),
                        mediaId: mediaId,
                        width: img.width,
                        height: img.height,
                        isSelected: isSelected,
                        parentClasses: parent?.className || 'no parent'
                    };
                });

                return {
                    found: true,
                    title: popup.querySelector('h2, h3, .ant-modal-title')?.innerText || 'No title',
                    totalLogos: logos.length,
                    logos: logos,
                    buttons: Array.from(popup.querySelectorAll('button')).map(b => b.innerText),
                    hasSearchBox: popup.querySelector('input[type="search"], input[placeholder*="search" i]') !== null
                };
            }
        """)

        if popup_info['found']:
            logger.info("✅ POPUP DETECTED!")
            logger.info(f"\n📋 POPUP DETAILS:")
            logger.info(f"   Title: {popup_info['title']}")
            logger.info(f"   Total Logos Found: {popup_info['totalLogos']}")
            logger.info(f"   Has Search Box: {popup_info['hasSearchBox']}")
            logger.info(f"   Buttons: {popup_info['buttons']}")

            logger.info(f"\n🖼️  LOGO DETAILS:")
            for logo in popup_info['logos']:
                selected_emoji = "✅ SELECTED" if logo['isSelected'] else "⭕ Available"
                logger.info(f"\n   Logo #{logo['index'] + 1}: {selected_emoji}")
                logger.info(f"      Media ID: {logo['mediaId']}")
                logger.info(f"      Size: {logo['width']}x{logo['height']}px")
                logger.info(f"      Selected: {logo['isSelected']}")
                logger.info(f"      Parent Classes: {logo['parentClasses'][:100]}")
                logger.info(f"      URL: {logo['src']}")

            # Find logos that are NOT selected (candidates for replacement)
            available_logos = [l for l in popup_info['logos'] if not l['isSelected']]
            logger.info(f"\n🎯 AVAILABLE LOGOS (not selected, no warnings):")
            logger.info(f"   Count: {len(available_logos)}")
            if available_logos:
                logger.info(f"\n   Recommended to use:")
                for logo in available_logos[:3]:  # Show first 3
                    logger.info(f"      - Media ID: {logo['mediaId']} ({logo['width']}x{logo['height']}px)")
        else:
            logger.error("❌ Popup not found")
        
        logger.info("\n" + "=" * 100)
        logger.info("✅ TEST COMPLETE - Popup analyzed")
        logger.info("=" * 100)
        logger.info("\n✅ Analysis complete. Browser remains open for inspection.")

if __name__ == "__main__":
    asyncio.run(main())
