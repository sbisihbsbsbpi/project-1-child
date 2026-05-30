#!/usr/bin/env python3
"""
COMPLETE END-TO-END WORKFLOW TEST
1. Check if logo exists
2. Click X icon to remove header
3. Detect header button status change (grayed → active)
4. Click active header button
5. Detect popup appearance
6. Analyze popup elements
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def full_workflow_test():
    """Complete end-to-end test"""

    logger.info("=" * 100)
    logger.info("🔄 COMPLETE END-TO-END WORKFLOW TEST")
    logger.info("=" * 100)
    logger.info("Steps:")
    logger.info("  1. Check if logo exists")
    logger.info("  2. Click X icon to remove header")
    logger.info("  3. Detect header button status change")
    logger.info("  4. Click active header button")
    logger.info("  5. Detect popup appearance")
    logger.info("  6. Analyze popup elements")
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
            return

        logger.info(f"\n✅ Using page: {working_tab.url[:80]}...")

        # ====================================================================
        # STEP 1: Check if header exists and get initial state
        # ====================================================================
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 1: Check Initial State")
        logger.info("=" * 100)

        initial_state = await working_tab.evaluate("""
            () => {
                const headerBtn = document.querySelector('#HEADER');
                if (!headerBtn) return { error: 'Header button not found' };

                const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                const grayed = opacity < 1;

                // Check if there's a header component (with or without logo)
                const sortableItems = document.querySelectorAll('[class*="SortableItem"]');
                let hasHeaderComponent = false;

                // If header button is grayed, header component exists
                if (grayed) {
                    hasHeaderComponent = true;
                }

                return {
                    headerBtn: {
                        opacity: opacity,
                        grayed: grayed,
                        clickable: !grayed
                    },
                    hasHeaderComponent: hasHeaderComponent,
                    sortableItemsCount: sortableItems.length
                };
            }
        """)

        if 'error' in initial_state:
            logger.error(f"   ❌ {initial_state['error']}")
            return

        logger.info(f"\n   📊 Initial State:")
        logger.info(f"      Header Button Opacity: {initial_state['headerBtn']['opacity']}")
        logger.info(f"      Header Button Grayed: {initial_state['headerBtn']['grayed']}")
        logger.info(f"      Header Component Exists: {initial_state['hasHeaderComponent']}")

        # ====================================================================
        # STEP 2: Remove header component if it exists
        # ====================================================================
        if initial_state['hasHeaderComponent']:
            logger.info("\n" + "=" * 100)
            logger.info("📋 STEP 2: Remove Header Component")
            logger.info("=" * 100)
            logger.info("\n   🎯 Header component exists - removing it...")

            # Try to find and click X icon using proven method
            remove_result = await working_tab.evaluate("""
                async () => {
                    // Try specific selector first
                    const removeBtn = document.querySelector('.templates_SortableItem_removeBtn__osvYZsTyqJ');

                    if (!removeBtn) {
                        return { success: false, error: 'Remove button not found' };
                    }

                    // Find container
                    const container = removeBtn.closest('td') || removeBtn.closest('[class*="SortableItem"]');
                    if (!container) {
                        return { success: false, error: 'Container not found' };
                    }

                    // Force hover
                    container.dispatchEvent(new MouseEvent('mouseenter', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    }));

                    // Wait for icon to appear
                    await new Promise(resolve => setTimeout(resolve, 500));

                    // Click remove button
                    removeBtn.click();

                    return { success: true };
                }
            """)

            if not remove_result['success']:
                logger.error(f"   ❌ {remove_result.get('error')}")
                logger.info("\n   💡 Header might not have a remove button (no logo)")
                logger.info("   💡 Try manually removing header or use different template")
                return

            logger.info("   ✅ X icon clicked!")

        # ====================================================================
        # STEP 3: Detect header button state change
        # ====================================================================
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 3: Detect Header Button State Change")
        logger.info("=" * 100)

        final_header_state = await working_tab.evaluate("""
            () => {
                const headerBtn = document.querySelector('#HEADER');
                if (!headerBtn) return { error: 'Header button not found' };

                const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                const grayed = opacity < 1;

                return {
                    opacity: opacity,
                    grayed: grayed,
                    clickable: !grayed
                };
            }
        """)

        logger.info(f"\n   📊 Header Button State Change:")
        logger.info(f"      BEFORE: opacity {initial_state['headerBtn']['opacity']} ({'grayed' if initial_state['headerBtn']['grayed'] else 'active'})")
        logger.info(f"      AFTER:  opacity {final_header_state['opacity']} ({'grayed' if final_header_state['grayed'] else 'active'})")

        if initial_state['headerBtn']['grayed'] and not final_header_state['grayed']:
            logger.info(f"\n   🎉 SUCCESS! Header button became ACTIVE!")
            logger.info(f"      → Changed from opacity {initial_state['headerBtn']['opacity']} to {final_header_state['opacity']}")
            logger.info(f"      → Entire header component removed")
            logger.info(f"      → Header option now available")
        elif final_header_state['grayed']:
            logger.warning(f"\n   ⚠️  Header button still GRAYED")
            logger.warning(f"      → Removal might not have worked")
            logger.warning(f"      → Cannot proceed to click header")
            return

        # ====================================================================
        # STEP 4: Click active header button
        # ====================================================================
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 4: Click Active Header Button")
        logger.info("=" * 100)

        if not final_header_state['clickable']:
            logger.error("   ❌ Header button not clickable - stopping")
            return

        logger.info("   ✅ Header button is active - clicking...")

        click_result = await working_tab.evaluate("""
            () => {
                const headerBtn = document.querySelector('#HEADER');
                if (!headerBtn) return { success: false, error: 'Button not found' };

                headerBtn.click();
                return { success: true };
            }
        """)

        if not click_result['success']:
            logger.error(f"   ❌ {click_result.get('error')}")
            return

        logger.info("   ✅ Header button clicked!")
        logger.info("   ⏳ Waiting for popup to appear...")

        await asyncio.sleep(2)

        # ====================================================================
        # STEP 5: Detect popup appearance
        # ====================================================================
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 5: Detect Popup/Modal")
        logger.info("=" * 100)

        popup_info = await working_tab.evaluate("""
            () => {
                const selectors = [
                    '[role="dialog"]',
                    '.ant-modal',
                    '.ant-modal-wrap',
                    '[class*="modal"]',
                    '[class*="Modal"]',
                    '[class*="dialog"]',
                    '[class*="popup"]'
                ];

                for (const sel of selectors) {
                    const elem = document.querySelector(sel);
                    if (elem) {
                        const rect = elem.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            return {
                                found: true,
                                selector: sel,
                                className: elem.className,
                                position: {
                                    top: Math.round(rect.top),
                                    left: Math.round(rect.left),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                },
                                opacity: parseFloat(getComputedStyle(elem).opacity)
                            };
                        }
                    }
                }

                return { found: false };
            }
        """)

        if not popup_info['found']:
            logger.error("   ❌ Popup not detected!")
            logger.info("   💡 Tried: [role='dialog'], .ant-modal, [class*='modal'], etc.")
            return

        logger.info(f"\n   ✅ Popup detected!")
        logger.info(f"      Selector: {popup_info['selector']}")
        logger.info(f"      Position: ({popup_info['position']['top']}, {popup_info['position']['left']})")
        logger.info(f"      Size: {popup_info['position']['width']}x{popup_info['position']['height']}")
        logger.info(f"      Opacity: {popup_info['opacity']}")

        # ====================================================================
        # STEP 6: Analyze popup elements
        # ====================================================================
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 6: Analyze Popup Elements")
        logger.info("=" * 100)

        elements = await working_tab.evaluate(f"""
            () => {{
                const popup = document.querySelector('{popup_info['selector']}');
                if (!popup) return null;

                const title = popup.querySelector('[class*="title"]') ||
                             popup.querySelector('h1, h2, h3');
                const inputs = Array.from(popup.querySelectorAll('input'));
                const buttons = Array.from(popup.querySelectorAll('button'));
                const labels = Array.from(popup.querySelectorAll('label'));
                const images = Array.from(popup.querySelectorAll('img'));
                const fileInputs = Array.from(popup.querySelectorAll('input[type="file"]'));
                const uploadAreas = Array.from(popup.querySelectorAll('[class*="upload"]'));

                return {{
                    title: title ? title.textContent.trim() : '',
                    inputs: inputs.map(i => ({{
                        type: i.type,
                        name: i.name || '',
                        placeholder: i.placeholder || '',
                        accept: i.accept || ''
                    }})),
                    buttons: buttons.map(b => ({{
                        text: b.textContent.trim(),
                        type: b.type || '',
                        disabled: b.disabled
                    }})),
                    labels: labels.map(l => l.textContent.trim()),
                    images: images.length,
                    fileInputs: fileInputs.length,
                    uploadAreas: uploadAreas.length,
                    hasLogoUpload: fileInputs.length > 0 || uploadAreas.length > 0
                }};
            }}
        """)

        if not elements:
            logger.error("   ❌ Failed to analyze popup")
            return

        logger.info(f"\n   📊 Popup Analysis:")
        logger.info(f"      Title: '{elements['title']}'")
        logger.info(f"      Buttons: {len(elements['buttons'])}")
        logger.info(f"      Inputs: {len(elements['inputs'])}")
        logger.info(f"      Labels: {len(elements['labels'])}")
        logger.info(f"      Images: {elements['images']}")
        logger.info(f"      File Uploads: {elements['fileInputs']}")
        logger.info(f"      Upload Areas: {elements['uploadAreas']}")
        logger.info(f"      Has Logo Upload: {'✅ YES' if elements['hasLogoUpload'] else '❌ NO'}")

        logger.info(f"\n   🔘 Buttons:")
        for i, btn in enumerate(elements['buttons'], 1):
            status = "🔴 Disabled" if btn['disabled'] else "🟢 Enabled"
            logger.info(f"      {i}. '{btn['text']}' ({btn['type']}) {status}")

        logger.info(f"\n   📝 Inputs:")
        for i, inp in enumerate(elements['inputs'], 1):
            if inp['type'] == 'file':
                logger.info(f"      {i}. 🎨 FILE UPLOAD (accept: {inp['accept'] or 'any'})")
            else:
                logger.info(f"      {i}. {inp['type'].upper()}: {inp['placeholder'] or inp['name']}")

        # ====================================================================
        # FINAL SUMMARY
        # ====================================================================
        logger.info("\n" + "=" * 100)
        logger.info("🎉 WORKFLOW COMPLETE!")
        logger.info("=" * 100)
        logger.info("\n   ✅ Step 1: Checked initial state")
        logger.info("   ✅ Step 2: Removed header component")
        logger.info("   ✅ Step 3: Detected header button became active")
        logger.info("   ✅ Step 4: Clicked active header button")
        logger.info("   ✅ Step 5: Detected popup appearance")
        logger.info("   ✅ Step 6: Analyzed popup elements")
        logger.info("\n   📊 Results:")
        logger.info(f"      - Popup title: '{elements['title']}'")
        logger.info(f"      - Total buttons: {len(elements['buttons'])}")
        logger.info(f"      - Total inputs: {len(elements['inputs'])}")
        logger.info(f"      - Logo upload available: {'✅ YES' if elements['hasLogoUpload'] else '❌ NO'}")
        logger.info("\n" + "=" * 100)


if __name__ == "__main__":
    asyncio.run(full_workflow_test())
