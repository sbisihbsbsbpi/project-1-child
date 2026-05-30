#!/usr/bin/env python3
"""
Test Header Button Click and Analyze Popup
Complete workflow:
1. Check header button state
2. Click header button when active
3. Detect popup/modal appearance
4. Analyze popup elements (inputs, buttons, logos)
5. Report all findings
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def test_header_click_and_popup():
    """Complete test of header button click and popup analysis"""

    logger.info("=" * 100)
    logger.info("🧪 TEST: Header Button Click → Popup Detection → Element Analysis")
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
            return

        logger.info(f"✅ Using page: {working_tab.url[:80]}...")

        # ========================================================================
        # STEP 1: Check header button state
        # ========================================================================
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 1: Check Header Button State")
        logger.info("=" * 100)

        header_state = await working_tab.evaluate("""
            () => {
                const headerBtn = document.querySelector('#HEADER');

                if (!headerBtn) return { found: false, error: 'Header button not found' };

                const rect = headerBtn.getBoundingClientRect();
                const style = getComputedStyle(headerBtn);
                const hasDisabledClass = headerBtn.className.includes('disabledButton') ||
                                        headerBtn.className.includes('disabled');
                const opacity = parseFloat(style.opacity);
                const pointerEvents = style.pointerEvents;

                return {
                    found: true,
                    isActive: opacity === 1.0 && !hasDisabledClass && pointerEvents !== 'none',
                    opacity: opacity,
                    hasDisabledClass: hasDisabledClass,
                    pointerEvents: pointerEvents,
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    text: headerBtn.textContent || headerBtn.innerText || '',
                    className: headerBtn.className
                };
            }
        """)

        if not header_state['found']:
            logger.error(f"   ❌ {header_state.get('error')}")
            return

        logger.info(f"\n   🔘 Header Button Found:")
        logger.info(f"      Text: {header_state['text']}")
        logger.info(f"      Position: ({header_state['position']['top']}, {header_state['position']['left']})")
        logger.info(f"      Size: {header_state['position']['width']}x{header_state['position']['height']}")
        logger.info(f"      Opacity: {header_state['opacity']}")
        logger.info(f"      Active: {'🟢 YES' if header_state['isActive'] else '🔴 NO (grayed)'}")

        if not header_state['isActive']:
            logger.warning("\n   ⚠️  Header button is NOT active (grayed out)")
            logger.warning("      This means a header component already exists in the template")
            logger.warning("      You need to remove the existing header first")
            logger.info("\n   💡 To make header active: Remove existing header logo using X icon")
            return

        logger.info("\n   ✅ Header button is ACTIVE - ready to click!")

        # ========================================================================
        # STEP 2: Click header button
        # ========================================================================
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 2: Click Header Button")
        logger.info("=" * 100)

        click_result = await working_tab.evaluate("""
            () => {
                const headerBtn = document.querySelector('#HEADER');
                if (!headerBtn) return { success: false, error: 'Button disappeared' };

                headerBtn.click();
                return { success: true, clicked: true };
            }
        """)

        if not click_result['success']:
            logger.error(f"   ❌ {click_result.get('error')}")
            return

        logger.info("   ✅ Header button clicked!")
        logger.info("   ⏳ Waiting for popup to appear...")

        await asyncio.sleep(2)  # Wait for popup animation


        # ========================================================================
        # STEP 3: Detect popup/modal
        # ========================================================================
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 3: Detect Popup/Modal")
        logger.info("=" * 100)

        popup_info = await working_tab.evaluate("""
            () => {
                // Try multiple selectors to find the popup
                const selectors = [
                    '[role="dialog"]',
                    '.ant-modal',
                    '.ant-modal-wrap',
                    '[class*="modal"]',
                    '[class*="Modal"]',
                    '[class*="dialog"]',
                    '[class*="Dialog"]',
                    '[class*="popup"]',
                    '[class*="Popup"]'
                ];

                let popup = null;
                let usedSelector = '';

                for (const selector of selectors) {
                    const found = document.querySelector(selector);
                    if (found) {
                        const rect = found.getBoundingClientRect();
                        // Verify it's actually visible
                        if (rect.width > 0 && rect.height > 0) {
                            popup = found;
                            usedSelector = selector;
                            break;
                        }
                    }
                }

                if (!popup) return { found: false };

                const rect = popup.getBoundingClientRect();
                const style = getComputedStyle(popup);

                return {
                    found: true,
                    selector: usedSelector,
                    className: popup.className,
                    id: popup.id || '',
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    visible: rect.width > 0 && rect.height > 0,
                    opacity: parseFloat(style.opacity),
                    zIndex: style.zIndex
                };
            }
        """)

        if not popup_info['found']:
            logger.error("   ❌ Popup not found!")
            logger.info("   💡 Tried selectors: [role='dialog'], .ant-modal, [class*='modal'], etc.")
            return

        logger.info(f"\n   ✅ Popup detected!")
        logger.info(f"      Selector: {popup_info['selector']}")
        logger.info(f"      Position: ({popup_info['position']['top']}, {popup_info['position']['left']})")
        logger.info(f"      Size: {popup_info['position']['width']}x{popup_info['position']['height']}")
        logger.info(f"      Z-Index: {popup_info['zIndex']}")
        logger.info(f"      Opacity: {popup_info['opacity']}")

        # ========================================================================
        # STEP 4: Analyze popup elements
        # ========================================================================
        logger.info("\n" + "=" * 100)
        logger.info("📋 STEP 4: Analyze Popup Elements")
        logger.info("=" * 100)

        elements = await working_tab.evaluate(f"""
            () => {{
                const popup = document.querySelector('{popup_info['selector']}');
                if (!popup) return null;

                // Find title/header
                const title = popup.querySelector('[class*="title"]') ||
                             popup.querySelector('[class*="Title"]') ||
                             popup.querySelector('[class*="header"]') ||
                             popup.querySelector('h1, h2, h3, h4');

                // Find all inputs
                const inputs = Array.from(popup.querySelectorAll('input'));

                // Find all buttons
                const buttons = Array.from(popup.querySelectorAll('button'));

                // Find all labels
                const labels = Array.from(popup.querySelectorAll('label'));

                // Find all images
                const images = Array.from(popup.querySelectorAll('img'));

                // Find file upload (logo upload)
                const fileInputs = Array.from(popup.querySelectorAll('input[type="file"]'));

                // Find upload buttons/areas
                const uploadAreas = Array.from(popup.querySelectorAll('[class*="upload"]'));

                return {{
                    title: title ? title.textContent.trim() : '',
                    titleClass: title ? title.className : '',
                    inputs: inputs.map(i => ({{
                        type: i.type,
                        name: i.name || '',
                        id: i.id || '',
                        placeholder: i.placeholder || '',
                        value: i.value || '',
                        className: i.className,
                        accept: i.accept || ''
                    }})),
                    buttons: buttons.map(b => ({{
                        text: b.textContent.trim(),
                        className: b.className,
                        type: b.type || '',
                        disabled: b.disabled
                    }})),
                    labels: labels.map(l => ({{
                        text: l.textContent.trim(),
                        htmlFor: l.htmlFor || '',
                        className: l.className
                    }})),
                    images: images.map(img => ({{
                        src: img.src || '',
                        alt: img.alt || '',
                        className: img.className,
                        width: img.width,
                        height: img.height
                    }})),
                    fileInputs: fileInputs.length,
                    uploadAreas: uploadAreas.map(u => ({{
                        className: u.className,
                        text: u.textContent.trim().substring(0, 50)
                    }})),
                    hasLogoUpload: fileInputs.length > 0 || uploadAreas.length > 0
                }};
            }}
        """)

        if not elements:
            logger.error("   ❌ Failed to analyze popup elements")
            return

        logger.info(f"\n   📊 Popup Analysis Results:")
        logger.info(f"      Title: '{elements['title']}'")
        logger.info(f"      Total Inputs: {len(elements['inputs'])}")
        logger.info(f"      Total Buttons: {len(elements['buttons'])}")
        logger.info(f"      Total Labels: {len(elements['labels'])}")
        logger.info(f"      Total Images: {len(elements['images'])}")
        logger.info(f"      File Upload Fields: {elements['fileInputs']}")
        logger.info(f"      Upload Areas: {len(elements['uploadAreas'])}")
        logger.info(f"      Has Logo Upload: {'✅ YES' if elements['hasLogoUpload'] else '❌ NO'}")

        # Detailed breakdown
        logger.info("\n   🔘 Buttons:")
        for i, btn in enumerate(elements['buttons'], 1):
            status = "🔴 Disabled" if btn['disabled'] else "🟢 Enabled"
            logger.info(f"      {i}. '{btn['text']}' ({btn['type']}) {status}")

        logger.info("\n   📝 Input Fields:")
        for i, inp in enumerate(elements['inputs'], 1):
            if inp['type'] == 'file':
                logger.info(f"      {i}. 🎨 FILE UPLOAD (accept: {inp['accept'] or 'any'})")
            else:
                logger.info(f"      {i}. {inp['type'].upper()}: {inp['placeholder'] or inp['name'] or inp['id']}")

        logger.info("\n   🏷️  Labels:")
        for i, lbl in enumerate(elements['labels'], 1):
            logger.info(f"      {i}. '{lbl['text']}'")

        if elements['images']:
            logger.info("\n   🖼️  Images:")
            for i, img in enumerate(elements['images'], 1):
                logger.info(f"      {i}. {img['width']}x{img['height']} - {img['alt'] or 'No alt text'}")

        if elements['uploadAreas']:
            logger.info("\n   📤 Upload Areas:")
            for i, area in enumerate(elements['uploadAreas'], 1):
                logger.info(f"      {i}. {area['text']}")

        # ========================================================================
        # STEP 5: Summary and recommendations
        # ========================================================================
        logger.info("\n" + "=" * 100)
        logger.info("📊 SUMMARY & RECOMMENDATIONS")
        logger.info("=" * 100)

        logger.info(f"\n   ✅ Successfully detected popup after clicking HEADER button")
        logger.info(f"   ✅ Popup contains {len(elements['buttons'])} buttons")
        logger.info(f"   ✅ Popup contains {len(elements['inputs'])} input fields")

        if elements['hasLogoUpload']:
            logger.info(f"   ✅ Logo upload functionality detected!")
            logger.info(f"      → {elements['fileInputs']} file input(s)")
            logger.info(f"      → {len(elements['uploadAreas'])} upload area(s)")
        else:
            logger.warning(f"   ⚠️  No logo upload functionality detected")

        logger.info("\n   💡 Next Steps:")
        logger.info("      1. Identify the logo upload input/button")
        logger.info("      2. Test uploading a logo file")
        logger.info("      3. Detect success/error after upload")
        logger.info("      4. Verify logo appears in preview")

        logger.info("\n" + "=" * 100)
        logger.info("✅ TEST COMPLETE!")
        logger.info("=" * 100)


if __name__ == "__main__":
    asyncio.run(test_header_click_and_popup())

