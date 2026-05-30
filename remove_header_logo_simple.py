#!/usr/bin/env python3
"""
Simple script to remove header logo using the proven working method.
Uses force hover + specific selector discovered on 2026-05-30.

Usage:
    python3 remove_header_logo_simple.py
    
Prerequisites:
    - Chrome browser running with CDP on localhost:9223
    - Template edit page already open
"""

import asyncio
import json
from playwright.async_api import async_playwright

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def remove_header_logo():
    """Remove header logo using proven working method"""
    
    logger.info("=" * 100)
    logger.info("🗑️  REMOVE HEADER LOGO - Simple Proven Method")
    logger.info("=" * 100)
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        # Find template edit page
        working_tab = None
        for page in context.pages:
            if '/templates/edit/' in page.url:
                working_tab = page
                break
        
        if not working_tab:
            logger.error("❌ No template edit page found!")
            logger.info("💡 Please open a template edit page first")
            return False
        
        logger.info(f"✅ Using page: {working_tab.url[:80]}...")
        
        # Load ignore list
        try:
            with open('logo_ignore_list.json') as f:
                ignore_list = json.load(f)
        except FileNotFoundError:
            logger.warning("⚠️  logo_ignore_list.json not found, using empty ignore list")
            ignore_list = {'ignore_patterns': {'ids': [], 'class_names': [], 'parent_selectors': []}}
        
        logger.info("\n📋 Step 1: Find logo and mark container")
        
        # Find logo and mark container
        container_info = await working_tab.evaluate("""
            (ignorePatterns) => {
                function isIgnored(el) {
                    if (!el) return true;
                    if (ignorePatterns.ids.includes(el.id)) return true;
                    const classes = el.className || '';
                    for (const pattern of ignorePatterns.class_names) {
                        if (classes.includes(pattern)) return true;
                    }
                    for (const parentSelector of ignorePatterns.parent_selectors) {
                        if (el.closest(parentSelector)) return true;
                    }
                    return false;
                }
                
                // Find header logo (S3 + media_ + top < 600px)
                const allImgs = document.querySelectorAll('img');
                let logoImg = null;
                
                for (const img of allImgs) {
                    if (isIgnored(img)) continue;
                    const src = img.src || '';
                    const rect = img.getBoundingClientRect();
                    if (src.includes('amazonaws.com') && src.includes('media_')) {
                        if (rect.width > 50 && rect.height > 20 && rect.top < 600) {
                            logoImg = img;
                            break;
                        }
                    }
                }
                
                if (!logoImg) return { found: false, error: 'Logo not found' };
                
                // Find container (TD or DIV)
                let container = logoImg.closest('td') || logoImg.closest('div') || logoImg.parentElement;
                container.setAttribute('data-logo-container-temp', 'true');
                container.style.outline = '3px solid red';  // Visual marker
                
                return { found: true, tagName: container.tagName };
            }
        """, ignore_list['ignore_patterns'])
        
        if not container_info['found']:
            logger.error(f"❌ {container_info.get('error', 'Unknown error')}")
            return False
        
        logger.info(f"   ✅ Logo found, container: <{container_info['tagName']}>")
        
        logger.info("\n📋 Step 2: Force hover on container")
        
        container = await working_tab.query_selector('[data-logo-container-temp="true"]')
        if not container:
            logger.error("   ❌ Container element not found")
            return False
        
        try:
            await container.hover(force=True, timeout=5000)
            logger.info("   ✅ Hover successful (forced)")
        except Exception as e:
            logger.warning(f"   ⚠️  Hover failed: {e}")
            logger.info("   🔄 Trying JavaScript hover...")
            await working_tab.evaluate("""
                () => {
                    const container = document.querySelector('[data-logo-container-temp="true"]');
                    if (container) {
                        container.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
                        container.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                    }
                }
            """)
            logger.info("   ✅ JavaScript hover dispatched")
        
        logger.info("   ⏳ Waiting 2 seconds for X icon to appear...")
        await asyncio.sleep(2)
        
        logger.info("\n📋 Step 3: Check initial header state")

        # Check header state BEFORE removal
        initial_header = await working_tab.evaluate("""
            () => {
                const headerBtn = document.querySelector('#HEADER');
                if (!headerBtn) return { found: false };

                const hasDisabledClass = headerBtn.className.includes('disabledButton') ||
                                        headerBtn.className.includes('disabled');
                const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                const pointerEvents = getComputedStyle(headerBtn).pointerEvents;

                return {
                    found: true,
                    grayed: hasDisabledClass || opacity < 1 || pointerEvents === 'none',
                    opacity: opacity
                };
            }
        """)

        if initial_header['found']:
            logger.info(f"   🔘 Header button before: {'🔴 Grayed (opacity {:.1f})'.format(initial_header['opacity']) if initial_header['grayed'] else '🟢 Active'}")

        logger.info("\n📋 Step 4: Click X icon (ONLY correct selector)")

        # ONLY use the proven correct selector - never click wrong elements!
        result = await working_tab.evaluate("""
            () => {
                // ONLY use the specific verified selector for header logo remove button
                // This prevents clicking wrong elements like popover close buttons
                const removeBtn = document.querySelector('.templates_SortableItem_removeBtn__osvYZsTyqJ');

                if (removeBtn) {
                    // Verify it's visible and within reasonable bounds
                    const rect = removeBtn.getBoundingClientRect();
                    const style = getComputedStyle(removeBtn);

                    if (rect.width > 0 && rect.height > 0 &&
                        parseFloat(style.opacity) > 0 &&
                        style.display !== 'none') {
                        removeBtn.click();
                        return {
                            success: true,
                            selector: '.templates_SortableItem_removeBtn__osvYZsTyqJ',
                            position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                            size: { width: Math.round(rect.width), height: Math.round(rect.height) }
                        };
                    }
                }

                // Try generic removeBtn ONLY if it's NOT a popover/workspace close button
                const genericBtns = document.querySelectorAll('[class*="removeBtn"]');
                for (const btn of genericBtns) {
                    const className = btn.className || '';
                    // Skip popover/workspace/notification close buttons
                    if (className.includes('popover') ||
                        className.includes('workspace') ||
                        className.includes('notification') ||
                        className.includes('Close')) {
                        continue;
                    }

                    const rect = btn.getBoundingClientRect();
                    const style = getComputedStyle(btn);

                    if (rect.width > 0 && rect.height > 0 &&
                        parseFloat(style.opacity) > 0 &&
                        style.display !== 'none') {
                        btn.click();
                        return {
                            success: true,
                            selector: '[class*="removeBtn"] (filtered)',
                            className: className
                        };
                    }
                }

                return { success: false, error: 'X icon not found or not visible' };
            }
        """)

        if result['success']:
            logger.info(f"   ✅ X icon clicked!")
            logger.info(f"      Selector: {result['selector']}")
            if result.get('position'):
                logger.info(f"      Position: ({result['position']['top']}, {result['position']['left']})")
                logger.info(f"      Size: {result['size']['width']}x{result['size']['height']}")

            logger.info("\n   ⏳ Waiting 2 seconds for removal to complete...")
            await asyncio.sleep(2)

            logger.info("\n📋 Step 5: Verify removal and header state change")

            # Check final state - both logo and header button
            final_state = await working_tab.evaluate("""
                () => {
                    // Check if logo still exists
                    const allImgs = document.querySelectorAll('img');
                    let headerLogoFound = false;

                    for (const img of allImgs) {
                        const src = img.src || '';
                        const rect = img.getBoundingClientRect();
                        if (src.includes('amazonaws.com') && src.includes('media_')) {
                            if (rect.width > 50 && rect.height > 20 && rect.top < 600) {
                                headerLogoFound = true;
                                break;
                            }
                        }
                    }

                    // Check header button state
                    const headerBtn = document.querySelector('#HEADER');
                    let headerState = { found: false };

                    if (headerBtn) {
                        const hasDisabledClass = headerBtn.className.includes('disabledButton') ||
                                                headerBtn.className.includes('disabled');
                        const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                        const pointerEvents = getComputedStyle(headerBtn).pointerEvents;

                        headerState = {
                            found: true,
                            grayed: hasDisabledClass || opacity < 1 || pointerEvents === 'none',
                            opacity: opacity
                        };
                    }

                    return {
                        logoStillPresent: headerLogoFound,
                        header: headerState
                    };
                }
            """)

            logger.info(f"\n   📊 Results:")
            logger.info(f"      Logo removed: {'❌ No (still present)' if final_state['logoStillPresent'] else '✅ Yes'}")

            if final_state['header']['found']:
                logger.info(f"      Header button after: {'🔴 Grayed (opacity {:.1f})'.format(final_state['header']['opacity']) if final_state['header']['grayed'] else '🟢 Active (opacity {:.1f})'.format(final_state['header']['opacity'])}")

                # Compare before and after
                if initial_header['found'] and initial_header['grayed'] and not final_state['header']['grayed']:
                    logger.info(f"\n   🎉 Header became ACTIVE! (was grayed, now enabled)")
                    logger.info(f"      → Entire header component removed")
                elif initial_header['found'] and initial_header['grayed'] and final_state['header']['grayed']:
                    logger.info(f"\n   ⚠️  Header still grayed (only logo removed)")

            if final_state['logoStillPresent']:
                logger.warning("\n❌ FAILED - Logo still present after click")
                return False
            else:
                logger.info("\n" + "=" * 100)
                logger.info("🎉 SUCCESS! Header logo removed!")
                if final_state['header']['found'] and not final_state['header']['grayed']:
                    logger.info("✅ Header button is now ACTIVE - header option available!")
                logger.info("=" * 100)
                return True
        else:
            logger.error(f"   ❌ {result.get('error', 'Unknown error')}")
            logger.error("   💡 Make sure you hover over the logo container first")
            return False


if __name__ == "__main__":
    success = asyncio.run(remove_header_logo())
    exit(0 if success else 1)
