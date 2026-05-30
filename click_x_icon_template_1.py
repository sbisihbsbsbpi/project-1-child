#!/usr/bin/env python3
"""
Click X icon on Template #1 to remove logo
Looking for X icon in top-right corner of container
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
    
    template_id = "CPRA_REQUEST_COMPLETION_DATA_DELETION_CLOSED_DOCUMENTS"
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        working_tab = None
        for p in context.pages:
            if 'tekioncloud.com/templates' in p.url:
                working_tab = p
                break
        
        if not working_tab:
            logger.error("❌ No Tekion tab found")
            return
        
        logger.info("✅ Using existing tab")
        
        # Navigate to template
        logger.info(f"\n🌐 Opening template: {template_id}")
        edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        await working_tab.goto(edit_url, wait_until='domcontentloaded', timeout=20000)
        
        logger.info("\n⏳ Waiting 17 seconds for template to fully load...")
        await asyncio.sleep(17)
        logger.info("✅ Template loaded")
        
        with open('logo_ignore_list.json') as f:
            ignore_list = json.load(f)
        
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 1: CHECK INITIAL STATE")
        logger.info("=" * 100)
        
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
        
        logger.info(f"\n🔘 Header Button:")
        logger.info(f"   Grayed: {initial_state['headerGrayed']}")
        logger.info(f"   Opacity: {initial_state['headerOpacity']}")
        
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 2: FIND LOGO CONTAINER AND MARK IT")
        logger.info("=" * 100)

        # Mark the container in JavaScript
        mark_result = await working_tab.evaluate("""
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

                // Find logo image
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

                if (!logoImg) return { success: false, error: 'Logo not found' };

                // Find the selectable container
                let container = logoImg.closest('[data-type]') ||
                               logoImg.closest('td[class]') ||
                               logoImg.closest('div[class*="element"]') ||
                               logoImg.parentElement;

                // Mark it with data attribute for Playwright to find
                container.setAttribute('data-selected-logo-container', 'true');

                // Highlight for visual feedback
                container.style.outline = '8px solid blue';
                logoImg.style.outline = '8px solid red';

                // Click to select
                container.click();

                const rect = container.getBoundingClientRect();

                return {
                    success: true,
                    container: {
                        tagName: container.tagName,
                        className: container.className || '',
                        dataType: container.getAttribute('data-type') || '',
                        position: {
                            top: Math.round(rect.top),
                            left: Math.round(rect.left),
                            right: Math.round(rect.right),
                            bottom: Math.round(rect.bottom)
                        },
                        size: {
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    }
                };
            }
        """, ignore_list['ignore_patterns'])

        if not mark_result['success']:
            logger.error(f"❌ {mark_result.get('error')}")
            return

        logger.info(f"\n✅ CONTAINER FOUND AND MARKED:")
        logger.info(f"   Tag: <{mark_result['container']['tagName']}>")
        logger.info(f"   Class: {mark_result['container']['className'][:100] if mark_result['container']['className'] else 'none'}")
        logger.info(f"   Data-type: {mark_result['container']['dataType'] or 'none'}")
        logger.info(f"   Position: top-left=({mark_result['container']['position']['top']}, {mark_result['container']['position']['left']})")
        logger.info(f"   Size: {mark_result['container']['size']['width']}x{mark_result['container']['size']['height']}")

        # Wait for UI to update
        await asyncio.sleep(0.5)

        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 3: FIND X ICON IN TOP-RIGHT CORNER")
        logger.info("=" * 100)

        # Search for X icon - BROADER SEARCH (anywhere on page)
        x_icon_result = await working_tab.evaluate("""
            () => {
                // Get ALL visible SVG and button elements on the page
                const allElements = document.querySelectorAll('svg, button, i, [role="button"], [class*="icon"], [class*="Icon"], [data-action]');

                // Get container bounds (the one we just marked)
                const container = document.querySelector('[data-selected-logo-container="true"]');
                if (!container) return { success: false, error: 'Container not found' };

                const containerRect = container.getBoundingClientRect();

                // Collect ALL visible elements with their info
                const allCandidates = [];

                for (const el of allElements) {
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);

                    // Only visible elements
                    if (rect.width > 0 && rect.height > 0 &&
                        style.display !== 'none' &&
                        parseFloat(style.opacity) > 0) {

                        allCandidates.push({
                            element: el,
                            tagName: el.tagName,
                            className: el.className || '',
                            id: el.id || '',
                            ariaLabel: el.getAttribute('aria-label') || '',
                            title: el.getAttribute('title') || '',
                            dataAction: el.getAttribute('data-action') || '',
                            innerHTML: el.innerHTML.substring(0, 100),
                            position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                            size: { width: Math.round(rect.width), height: Math.round(rect.height) },
                            distanceFromContainer: Math.sqrt(
                                Math.pow(rect.top - containerRect.top, 2) +
                                Math.pow(rect.left - containerRect.right, 2)
                            )
                        });
                    }
                }

                // Sort by distance from container's top-right corner
                allCandidates.sort((a, b) => a.distanceFromContainer - b.distanceFromContainer);

                // Take top 20 closest
                const closestCandidates = allCandidates.slice(0, 20);

                return {
                    success: true,
                    containerRect: {
                        top: Math.round(containerRect.top),
                        right: Math.round(containerRect.right),
                        bottom: Math.round(containerRect.bottom),
                        left: Math.round(containerRect.left)
                    },
                    totalFound: allCandidates.length,
                    candidates: closestCandidates.map(c => ({
                        tagName: c.tagName,
                        className: c.className,
                        id: c.id,
                        ariaLabel: c.ariaLabel,
                        title: c.title,
                        dataAction: c.dataAction,
                        innerHTML: c.innerHTML,
                        position: c.position,
                        size: c.size,
                        distance: Math.round(c.distanceFromContainer)
                    }))
                };
            }
        """)

        if not x_icon_result['success']:
            logger.error(f"❌ {x_icon_result.get('error')}")
            return

        logger.info(f"\n📍 Container Position:")
        logger.info(f"   Top-left: ({x_icon_result['containerRect']['top']}, {x_icon_result['containerRect']['left']})")
        logger.info(f"   Bottom-right: ({x_icon_result['containerRect']['bottom']}, {x_icon_result['containerRect']['right']})")

        logger.info(f"\n🔍 Total visible elements: {x_icon_result['totalFound']}")
        logger.info(f"🔍 Showing 20 CLOSEST to container top-right corner:")
        logger.info("")

        for idx, candidate in enumerate(x_icon_result['candidates'], 1):
            logger.info(f"  [{idx}] <{candidate['tagName']}> at ({candidate['position']['top']}, {candidate['position']['left']}) - distance: {candidate['distance']}px")
            if candidate['className']:
                logger.info(f"      Class: {candidate['className'][:80]}")
            if candidate['id']:
                logger.info(f"      ID: {candidate['id']}")
            if candidate['ariaLabel']:
                logger.info(f"      Aria-label: {candidate['ariaLabel']}")
            if candidate['title']:
                logger.info(f"      Title: {candidate['title']}")
            if candidate['dataAction']:
                logger.info(f"      Data-action: {candidate['dataAction']}")
            logger.info(f"      Size: {candidate['size']['width']}x{candidate['size']['height']}")
            if candidate['innerHTML']:
                logger.info(f"      HTML: {candidate['innerHTML'][:60]}...")
            logger.info("")

        # Look for X or close icon
        x_icon = None
        for idx, candidate in enumerate(x_icon_result['candidates']):
            className = candidate['className'].lower()
            ariaLabel = candidate['ariaLabel'].lower()
            title = candidate['title'].lower()
            innerHTML = candidate['innerHTML'].lower()
            dataAction = candidate['dataAction'].lower()

            # Check for X, close, delete, remove patterns
            all_text = className + ariaLabel + title + innerHTML + dataAction
            if any(keyword in all_text for keyword in ['close', 'cross', 'delete', 'remove', 'times', '×']):
                x_icon = idx
                logger.info(f"\n🎯 FOUND X ICON: Candidate [{idx + 1}]")
                logger.info(f"   Matched keyword in: {className[:50] if 'close' in className or 'cross' in className or 'delete' in className else ''}")
                break

        if x_icon is None and len(x_icon_result['candidates']) > 0:
            # If no specific match, ask user or try closest one
            logger.info(f"\n⚠️  No clear X icon found automatically")
            logger.info(f"💡 Please check the candidates above and identify which one is the X icon")
            logger.info(f"   Looking for small icons (16-32px) near the container's top-right")

            # Try to find small icons (likely toolbar icons)
            small_icons = [idx for idx, c in enumerate(x_icon_result['candidates'])
                          if c['size']['width'] <= 32 and c['size']['height'] <= 32 and c['distance'] < 200]

            if small_icons:
                x_icon = small_icons[0]
                logger.info(f"\n💡 Using first small icon close to container: Candidate [{x_icon + 1}]")

        if x_icon is None:
            logger.error("\n❌ No X icon found in top-right corner")
            # Take screenshot for debugging
            screenshot = f"no_x_icon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await working_tab.screenshot(path=screenshot, full_page=True)
            logger.info(f"📸 Debug screenshot: {screenshot}")
            return

        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 4: CLICK X ICON")
        logger.info("=" * 100)

        # Highlight the X icon and click it
        final_result = await working_tab.evaluate("""
            (iconIndex) => {
                const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

                // Re-find the candidates
                const container = document.querySelector('[data-selected-logo-container="true"]');
                if (!container) return { success: false, error: 'Container lost' };

                const containerRect = container.getBoundingClientRect();

                const allElements = document.querySelectorAll('svg, button, i, [role="button"], [class*="icon"], [class*="Icon"], [data-action]');
                const allCandidates = [];

                for (const el of allElements) {
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);

                    if (rect.width > 0 && rect.height > 0 &&
                        style.display !== 'none' &&
                        parseFloat(style.opacity) > 0) {

                        const distance = Math.sqrt(
                            Math.pow(rect.top - containerRect.top, 2) +
                            Math.pow(rect.left - containerRect.right, 2)
                        );

                        allCandidates.push({ element: el, distance: distance });
                    }
                }

                allCandidates.sort((a, b) => a.distance - b.distance);
                const candidatesInZone = allCandidates.slice(0, 20).map(c => c.element);

                if (iconIndex >= candidatesInZone.length) {
                    return { success: false, error: 'Icon index out of range' };
                }

                const xIcon = candidatesInZone[iconIndex];

                // Highlight it
                xIcon.style.outline = '6px solid lime';
                xIcon.style.boxShadow = '0 0 20px lime';
                xIcon.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';

                // Click it!
                xIcon.click();

                return { success: true, clicked: true };
            }
        """, x_icon)

        if not final_result['success']:
            logger.error(f"❌ {final_result.get('error')}")
            return

        logger.info("✅ X icon CLICKED!")
        logger.info("⏳ Waiting for deletion...")

        await asyncio.sleep(2)

        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 5: VERIFY RESULTS")
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

                // Check header button
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

        # Take final screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot = f"template_1_after_x_click_{timestamp}.png"
        await working_tab.screenshot(path=screenshot, full_page=True)
        logger.info(f"\n📸 Screenshot: {screenshot}")

        logger.info("\n" + "=" * 100)
        logger.info("✅ RESULTS")
        logger.info("=" * 100)

        if not final_state['logoStillExists']:
            logger.info("\n✅ Logo REMOVED!")
        else:
            logger.info("\n❌ Logo still exists")

        if initial_state['headerGrayed'] and not final_state['headerGrayed']:
            logger.info("✅ Header button is now ACTIVE!")
            logger.info("   → Entire header component was removed (Option B)")
        elif initial_state['headerGrayed'] and final_state['headerGrayed']:
            logger.info("⚠️  Header button still grayed")
            logger.info("   → Only logo image removed, header component remains (Option A)")

        logger.info("\n" + "=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
