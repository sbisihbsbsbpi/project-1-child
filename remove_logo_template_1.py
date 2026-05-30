#!/usr/bin/env python3
"""
Remove logo from Template #1 by clicking X icon
Verifies:
1. Logo is removed
2. Header button becomes active (not grayed)
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def main():
    logger.info("=" * 100)
    logger.info("🗑️  REMOVE LOGO FROM TEMPLATE #1 - Click X Icon")
    logger.info("=" * 100)
    
    # Template #1 is the first CPRA template
    template_id = "CPRA_REQUEST_COMPLETION_DATA_DELETION_CLOSED_DOCUMENTS"
    template_name = "Request Completion: Data Deletion (Closed Documents)"
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        # Find Tekion tab
        working_tab = None
        for p in context.pages:
            if 'tekioncloud.com/templates' in p.url:
                working_tab = p
                logger.info("✅ Using existing tab")
                break
        
        if not working_tab:
            logger.error("❌ No Tekion tab found")
            return
        
        # Navigate to template #1
        logger.info(f"\n🌐 Opening template: {template_name}")
        logger.info(f"   ID: {template_id}")
        edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        await working_tab.goto(edit_url, wait_until='domcontentloaded', timeout=20000)
        
        # Wait for full load
        logger.info("\n⏳ Waiting 17 seconds for template to fully load...")
        await asyncio.sleep(17)
        logger.info("✅ Template loaded")
        
        # Load ignore list
        with open('logo_ignore_list.json') as f:
            ignore_list = json.load(f)
        
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 1: DETECT INITIAL STATE")
        logger.info("=" * 100)
        
        # Check initial state
        initial_state = await working_tab.evaluate("""
            () => {
                const headerBtn = document.querySelector('#HEADER');
                return {
                    headerGrayed: headerBtn ? (
                        headerBtn.classList.contains('templates_Button_disabledButton__5QXhWoXLh5') ||
                        parseFloat(getComputedStyle(headerBtn).opacity) < 1
                    ) : null,
                    headerOpacity: headerBtn ? parseFloat(getComputedStyle(headerBtn).opacity) : null
                };
            }
        """)
        
        logger.info(f"\n🔘 Header Button Initial State:")
        logger.info(f"   Grayed out: {initial_state['headerGrayed']}")
        logger.info(f"   Opacity: {initial_state['headerOpacity']}")
        
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 2: FIND LOGO AND HOVER TO REVEAL X ICON")
        logger.info("=" * 100)
        
        # Find logo, hover, and find X button
        result = await working_tab.evaluate("""
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
                
                // Find logo
                const allImgs = document.querySelectorAll('img');
                let logoImg = null;
                
                for (const img of allImgs) {
                    if (isIgnored(img)) continue;
                    
                    const src = img.src || '';
                    const rect = img.getBoundingClientRect();
                    
                    if (src.includes('amazonaws.com') && src.includes('media_')) {
                        const isReasonableSize = rect.width > 50 && rect.height > 20;
                        if (isReasonableSize && rect.top < 600) {
                            logoImg = img;
                            break;
                        }
                    }
                }
                
                if (!logoImg) {
                    return { success: false, error: 'Logo not found' };
                }
                
                // Highlight logo in red
                logoImg.style.outline = '8px solid red';
                logoImg.style.boxShadow = '0 0 20px red';
                
                const rect = logoImg.getBoundingClientRect();
                return {
                    success: true,
                    logo: {
                        position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                        size: { width: Math.round(rect.width), height: Math.round(rect.height) },
                        src: logoImg.src.substring(0, 120)
                    }
                };
            }
        """, ignore_list['ignore_patterns'])
        
        if not result['success']:
            logger.error(f"❌ {result.get('error', 'Unknown error')}")
            return
        
        logger.info(f"\n✅ LOGO FOUND:")
        logger.info(f"   Position: top={result['logo']['position']['top']}, left={result['logo']['position']['left']}")
        logger.info(f"   Size: {result['logo']['size']['width']}x{result['logo']['size']['height']}")
        logger.info(f"   Highlighted in RED")

        # Now hover and find X button
        logger.info("\n🖱️  HOVERING over logo to reveal X icon...")

        hover_result = await working_tab.evaluate("""
            async (ignorePatterns) => {
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

                const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

                // Find logo again
                const allImgs = document.querySelectorAll('img');
                let logoImg = null;

                for (const img of allImgs) {
                    if (isIgnored(img)) continue;
                    const src = img.src || '';
                    const rect = img.getBoundingClientRect();
                    if (src.includes('amazonaws.com') && src.includes('media_')) {
                        const isReasonableSize = rect.width > 50 && rect.height > 20;
                        if (isReasonableSize && rect.top < 600) {
                            logoImg = img;
                            break;
                        }
                    }
                }

                if (!logoImg) return { success: false, error: 'Logo not found on second pass' };

                // Get parent container
                let container = logoImg.closest('div') || logoImg.parentElement;
                if (!container) return { success: false, error: 'No parent container found' };

                // Simulate hover
                const rect = container.getBoundingClientRect();
                const mouseEvent = new MouseEvent('mouseenter', {
                    bubbles: true,
                    cancelable: true,
                    clientX: rect.left + rect.width / 2,
                    clientY: rect.top + rect.height / 2
                });
                container.dispatchEvent(mouseEvent);
                container.classList.add('hover', 'hovered');

                // Wait for X to appear
                await sleep(800);

                // Search for X/delete button with multiple selectors
                const deleteSelectors = [
                    '[class*="icon-cross"]',
                    '[class*="icon-close"]',
                    '[class*="icon-delete"]',
                    '[class*="icon-remove"]',
                    '[class*="delete"]',
                    '[class*="remove"]',
                    '[class*="close"]',
                    'button[aria-label*="delete" i]',
                    'button[aria-label*="remove" i]',
                    'button[aria-label*="close" i]',
                    '[data-action="delete"]',
                    '[data-action="remove"]',
                    'svg[class*="cross"]',
                    'svg[class*="close"]',
                    'i[class*="cross"]',
                    'i[class*="close"]',
                    'svg[class*="delete"]',
                    'svg[class*="remove"]'
                ];

                let deleteBtn = null;
                let matchedSelector = null;

                // Search in container
                for (const selector of deleteSelectors) {
                    deleteBtn = container.querySelector(selector);
                    if (deleteBtn) {
                        matchedSelector = selector;
                        break;
                    }
                }

                // Search in parent if not found
                if (!deleteBtn && container.parentElement) {
                    for (const selector of deleteSelectors) {
                        deleteBtn = container.parentElement.querySelector(selector);
                        if (deleteBtn) {
                            matchedSelector = selector + ' (in parent)';
                            break;
                        }
                    }
                }

                if (!deleteBtn) {
                    return {
                        success: false,
                        error: 'X button not found',
                        containerInfo: {
                            tagName: container.tagName,
                            className: container.className,
                            innerHTML: container.innerHTML.substring(0, 500)
                        }
                    };
                }

                // Highlight X button in green
                deleteBtn.style.outline = '6px solid lime';
                deleteBtn.style.boxShadow = '0 0 20px lime';
                deleteBtn.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';

                const btnRect = deleteBtn.getBoundingClientRect();

                return {
                    success: true,
                    deleteBtn: {
                        selector: matchedSelector,
                        position: { top: Math.round(btnRect.top), left: Math.round(btnRect.left) },
                        size: { width: Math.round(btnRect.width), height: Math.round(btnRect.height) },
                        tagName: deleteBtn.tagName
                    }
                };
            }
        """, ignore_list['ignore_patterns'])

        if not hover_result['success']:
            logger.error(f"\n❌ {hover_result.get('error', 'Unknown error')}")
            if 'containerInfo' in hover_result:
                logger.info(f"\n📦 Container Info:")
                logger.info(f"   Tag: {hover_result['containerInfo']['tagName']}")
                logger.info(f"   Class: {hover_result['containerInfo']['className']}")
                logger.info(f"   HTML: {hover_result['containerInfo']['innerHTML'][:200]}...")
            return

        logger.info(f"\n✅ X BUTTON FOUND:")
        logger.info(f"   Selector: {hover_result['deleteBtn']['selector']}")
        logger.info(f"   Position: top={hover_result['deleteBtn']['position']['top']}, left={hover_result['deleteBtn']['position']['left']}")
        logger.info(f"   Size: {hover_result['deleteBtn']['size']['width']}x{hover_result['deleteBtn']['size']['height']}")
        logger.info(f"   Tag: {hover_result['deleteBtn']['tagName']}")
        logger.info(f"   Highlighted in GREEN")

        # Take screenshot before clicking
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_before = f"template_1_before_delete_{timestamp}.png"
        await working_tab.screenshot(path=screenshot_before, full_page=True)
        logger.info(f"\n📸 Screenshot (before): {screenshot_before}")

        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 3: CLICK X ICON TO DELETE LOGO")
        logger.info("=" * 100)

        await asyncio.sleep(2)  # Let user see the highlights

        # Click the X button
        click_result = await working_tab.evaluate("""
            async (ignorePatterns) => {
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

                const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

                // Find logo and container again
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

                if (!logoImg) return { success: false, error: 'Logo disappeared before click' };

                let container = logoImg.closest('div') || logoImg.parentElement;

                const deleteSelectors = [
                    '[class*="icon-cross"]',
                    '[class*="icon-close"]',
                    '[class*="icon-delete"]',
                    '[class*="icon-remove"]',
                    '[class*="delete"]',
                    '[class*="remove"]',
                    '[class*="close"]',
                    'button[aria-label*="delete" i]',
                    'button[aria-label*="remove" i]',
                    'svg[class*="cross"]',
                    'svg[class*="close"]',
                    'svg[class*="delete"]'
                ];

                let deleteBtn = null;
                for (const selector of deleteSelectors) {
                    deleteBtn = container.querySelector(selector);
                    if (deleteBtn) break;
                }

                if (!deleteBtn && container.parentElement) {
                    for (const selector of deleteSelectors) {
                        deleteBtn = container.parentElement.querySelector(selector);
                        if (deleteBtn) break;
                    }
                }

                if (!deleteBtn) return { success: false, error: 'X button not found on click attempt' };

                // Click it!
                deleteBtn.click();
                deleteBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));

                await sleep(1000);  // Wait for deletion animation

                return { success: true, clicked: true };
            }
        """, ignore_list['ignore_patterns'])

        if not click_result['success']:
            logger.error(f"❌ {click_result.get('error', 'Click failed')}")
            return

        logger.info("✅ X button CLICKED!")
        logger.info("⏳ Waiting for deletion to complete...")

        await asyncio.sleep(2)

        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 4: VERIFY LOGO REMOVAL AND HEADER STATE")
        logger.info("=" * 100)

        # Check final state
        final_state = await working_tab.evaluate("""
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

                // Check if logo still exists
                const allImgs = document.querySelectorAll('img');
                let logoFound = false;

                for (const img of allImgs) {
                    if (isIgnored(img)) continue;
                    const src = img.src || '';
                    const rect = img.getBoundingClientRect();
                    if (src.includes('amazonaws.com') && src.includes('media_')) {
                        if (rect.width > 50 && rect.height > 20 && rect.top < 600) {
                            logoFound = true;
                            break;
                        }
                    }
                }

                // Check header button state
                const headerBtn = document.querySelector('#HEADER');
                const headerGrayed = headerBtn ? (
                    headerBtn.classList.contains('templates_Button_disabledButton__5QXhWoXLh5') ||
                    parseFloat(getComputedStyle(headerBtn).opacity) < 1
                ) : null;
                const headerOpacity = headerBtn ? parseFloat(getComputedStyle(headerBtn).opacity) : null;

                return {
                    logoStillExists: logoFound,
                    headerGrayed: headerGrayed,
                    headerOpacity: headerOpacity
                };
            }
        """, ignore_list['ignore_patterns'])

        logger.info(f"\n📊 FINAL STATE:")
        logger.info(f"   Logo still exists: {final_state['logoStillExists']}")
        logger.info(f"   Header button grayed: {final_state['headerGrayed']}")
        logger.info(f"   Header button opacity: {final_state['headerOpacity']}")

        # Take screenshot after
        screenshot_after = f"template_1_after_delete_{timestamp}.png"
        await working_tab.screenshot(path=screenshot_after, full_page=True)
        logger.info(f"\n📸 Screenshot (after): {screenshot_after}")

        logger.info("\n" + "=" * 100)
        logger.info("✅ VERIFICATION RESULTS")
        logger.info("=" * 100)

        if not final_state['logoStillExists']:
            logger.info("\n✅ Logo successfully REMOVED!")
        else:
            logger.info("\n❌ Logo still exists (removal failed)")

        if initial_state['headerGrayed'] and not final_state['headerGrayed']:
            logger.info("✅ Header button is now ACTIVE (was grayed, now enabled)!")
            logger.info("   This confirms the header component was removed.")
        elif initial_state['headerGrayed'] and final_state['headerGrayed']:
            logger.info("⚠️  Header button is still GRAYED (header component still exists)")
            logger.info("   This means only the logo image was removed, not the header.")
        elif not initial_state['headerGrayed']:
            logger.info("ℹ️  Header button was already active (unchanged)")

        logger.info("\n" + "=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
