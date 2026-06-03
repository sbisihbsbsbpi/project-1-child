#!/usr/bin/env python3
"""
🧪 Dynamic Detection + Click Change Image Icon Test
Tests the complete workflow: Detect → Hover → Click
"""

import asyncio
import logging
from playwright.async_api import async_playwright
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_TEMPLATE_ID = "667f0befd4964026ee7b6ea2"
CDP_URL = "http://localhost:9223"


async def detect_and_mark_logos(page):
    """Detect all logo containers using dynamic imageComponent pattern"""
    
    logger.info("\n" + "="*100)
    logger.info("🔍 STEP 1: DYNAMIC LOGO DETECTION")
    logger.info("="*100)
    
    result = await page.evaluate("""
        () => {
            const allImageComponents = document.querySelectorAll('[class*="imageComponent"]');
            const detectedLogos = [];
            
            allImageComponents.forEach((imageComp, idx) => {
                const sortableItem = imageComp.closest('[class*="SortableItem"]');
                
                if (!sortableItem) return;
                
                const img = imageComp.querySelector('img');
                const hasImage = img !== null;
                
                // Mark for testing (we'll test ALL imageComponents)
                sortableItem.setAttribute('data-logo-test', `logo-${idx + 1}`);
                imageComp.setAttribute('data-imagecomponent-target', `target-${idx + 1}`);
                
                const rect = sortableItem.getBoundingClientRect();
                
                detectedLogos.push({
                    index: idx + 1,
                    hasImage: hasImage,
                    position: {
                        top: Math.round(rect.top + window.scrollY),
                        left: Math.round(rect.left)
                    },
                    size: {
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }
                });
                
                // Highlight the imageComponent
                imageComp.style.outline = '3px solid blue';
                imageComp.style.backgroundColor = 'rgba(0, 0, 255, 0.05)';
            });
            
            return {
                total: allImageComponents.length,
                logos: detectedLogos
            };
        }
    """)
    
    logger.info(f"✅ Found {result['total']} imageComponent containers")
    for logo in result['logos']:
        logger.info(f"   Logo #{logo['index']}: {logo['position']['top']}px - Has Image: {logo['hasImage']}")
    
    return result


async def test_hover_and_click(page, logo_index):
    """Test hovering over imageComponent and clicking Change Image icon"""
    
    logger.info("\n" + "="*100)
    logger.info(f"🎯 STEP 2: TESTING LOGO #{logo_index}")
    logger.info("="*100)
    
    # Find the imageComponent target
    imagecomp_selector = f'[data-imagecomponent-target="target-{logo_index}"]'
    
    try:
        imagecomp = await page.wait_for_selector(imagecomp_selector, timeout=5000)
        
        if not imagecomp:
            logger.error(f"❌ Could not find imageComponent for logo #{logo_index}")
            return False
        
        logger.info(f"✅ Found imageComponent container")
        
        # Scroll into view
        await imagecomp.scroll_into_view_if_needed()
        await asyncio.sleep(0.5)
        
        # Hover over the imageComponent
        logger.info("🖱️  Hovering over imageComponent...")
        await imagecomp.hover(force=True)
        await asyncio.sleep(2)  # Wait longer for toolbar to appear
        
        # Check if toolbar appeared
        toolbar_visible = await page.evaluate("""
            () => {
                const toolbars = document.querySelectorAll('[class*="toolbar"]');
                for (const toolbar of toolbars) {
                    const style = window.getComputedStyle(toolbar);
                    if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                        return true;
                    }
                }
                return false;
            }
        """)
        
        if toolbar_visible:
            logger.info("✅ Toolbar appeared!")
        else:
            logger.warning("⚠️  Toolbar not visible yet, waiting...")
            await asyncio.sleep(1)
        
        # Try to find and click the Change Image icon using production logic
        logger.info("🔍 Looking for Change Image icon (using production selectors)...")

        # Use the same logic as production code
        click_result = await page.evaluate(f"""
            (logoIndex) => {{
                const imagecomp = document.querySelector('[data-imagecomponent-target="target-' + logoIndex + '"]');
                if (!imagecomp) return {{ success: false, reason: 'imageComponent not found', debug: [] }};

                const debug = [];
                debug.push('Found imageComponent');

                // Find the parent SortableItem where the toolbar appears
                const sortableItem = imagecomp.closest('[class*="SortableItem"]');
                if (!sortableItem) return {{ success: false, reason: 'SortableItem not found', debug }};

                debug.push('Found SortableItem');

                // Look for Change Image icon with production selectors
                const selectors = [
                    '[aria-label="icon-switch"]',
                    '[title="Change Image"]',
                    '[class*="Image_changeImage"]'
                ];

                let changeIcon = null;
                let usedSelector = null;

                // First try in SortableItem
                for (const selector of selectors) {{
                    changeIcon = sortableItem.querySelector(selector);
                    if (changeIcon) {{
                        usedSelector = selector + ' (in SortableItem)';
                        break;
                    }}
                }}

                // Then try in imageComponent
                if (!changeIcon) {{
                    for (const selector of selectors) {{
                        changeIcon = imagecomp.querySelector(selector);
                        if (changeIcon) {{
                            usedSelector = selector + ' (in imageComponent)';
                            break;
                        }}
                    }}
                }}

                if (!changeIcon) {{
                    // List all buttons in the area for debugging
                    const buttons = Array.from(sortableItem.querySelectorAll('button, [role="button"]'));
                    debug.push(`Found ${{buttons.length}} buttons in SortableItem:`);
                    buttons.forEach((btn, idx) => {{
                        const rect = btn.getBoundingClientRect();
                        debug.push(`  ${{idx + 1}}. aria-label: ${{btn.getAttribute('aria-label')}}, visible: ${{rect.width > 0}}`);
                    }});

                    return {{ success: false, reason: 'Change Image icon not found', debug }};
                }}

                debug.push(`Found icon with: ${{usedSelector}}`);

                // Click the icon
                changeIcon.click();
                debug.push('Clicked icon');

                return {{ success: true, selector: usedSelector, debug }};
            }}
        """, logo_index)

        logger.info("📋 Click Debug Info:")
        for line in click_result.get('debug', []):
            logger.info(f"   {line}")

        if not click_result['success']:
            logger.error(f"❌ Failed to click: {click_result.get('reason')}")
            return False

        logger.info(f"✅ Clicked Change Image icon using: {click_result.get('selector')}")
        await asyncio.sleep(2)

        # Check if popup opened
        popup_open = await page.evaluate("""
            () => {
                const modals = document.querySelectorAll('[class*="modal"], [class*="dialog"], [role="dialog"]');
                for (const modal of modals) {
                    const style = window.getComputedStyle(modal);
                    const rect = modal.getBoundingClientRect();
                    if (style.display !== 'none' && rect.width > 0) {
                        return true;
                    }
                }
                return false;
            }
        """)

        if popup_open:
            logger.info("✅ SUCCESS! Change Image popup opened!")
            return True
        else:
            logger.warning("⚠️  Click executed but popup not detected")
            return False
            
    except Exception as e:
        logger.exception(f"❌ Error during hover/click test: {e}")
        return False


async def main():
    """Main test execution"""

    logger.info("="*100)
    logger.info("🧪 DYNAMIC DETECTION + CHANGE IMAGE CLICK TEST")
    logger.info("="*100)
    logger.info(f"Test Template: {TEST_TEMPLATE_ID}")
    logger.info(f"CDP URL: {CDP_URL}")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*100)

    async with async_playwright() as p:
        try:
            # Connect to existing browser
            browser = await p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]
            page = context.pages[0]

            # Navigate to template
            logger.info("Opening template edit page...")
            edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{TEST_TEMPLATE_ID}"
            await page.goto(edit_url, wait_until='domcontentloaded', timeout=30000)

            # Wait for editor to load
            await page.wait_for_selector('[class*="SortableItem"]', timeout=15000)
            logger.info("✅ Template editor loaded")

            # Detect logos
            detection_result = await detect_and_mark_logos(page)

            if detection_result['total'] == 0:
                logger.error("❌ No imageComponents found!")
                return

            # Test each logo
            results = []
            for logo in detection_result['logos']:
                logger.info("\n" + "-"*100)
                result = await test_hover_and_click(page, logo['index'])
                results.append({
                    'logo': logo['index'],
                    'success': result
                })

                if result:
                    logger.info(f"✅ Logo #{logo['index']}: SUCCESS")

                    # Wait a moment for inspection
                    logger.info("⏸️  Waiting 5 seconds to inspect popup...")
                    await asyncio.sleep(5)

                    # Close popup if it opened
                    try:
                        # Try to close with Escape
                        await page.keyboard.press('Escape')
                        await asyncio.sleep(1)
                    except:
                        pass
                else:
                    logger.error(f"❌ Logo #{logo['index']}: FAILED")

                logger.info("-"*100)

            # Summary
            logger.info("\n" + "="*100)
            logger.info("📊 TEST SUMMARY")
            logger.info("="*100)

            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]

            logger.info(f"Total Logos Tested: {len(results)}")
            logger.info(f"✅ Successful: {len(successful)}")
            logger.info(f"❌ Failed: {len(failed)}")

            if successful:
                logger.info("\n✅ Successful Logos:")
                for r in successful:
                    logger.info(f"   - Logo #{r['logo']}")

            if failed:
                logger.info("\n❌ Failed Logos:")
                for r in failed:
                    logger.info(f"   - Logo #{r['logo']}")

            logger.info("\n" + "="*100)
            logger.info("✅ TEST COMPLETE")
            logger.info("="*100)

        except Exception as e:
            logger.exception(f"❌ Fatal error during test execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())

