#!/usr/bin/env python3
"""
TEST VERSION - Parallel Tab Logo Warning Updater
Uses hardcoded template IDs for testing
"""

import asyncio
import json
import logging
from datetime import datetime
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


async def test_parallel_updater():
    """Test with known template IDs"""
    
    logger.info("=" * 100)
    logger.info("🧪 TEST: PARALLEL TAB LOGO WARNING UPDATER")
    logger.info("=" * 100)
    
    # Test templates - including the one with warnings we found
    test_templates = [
        {
            'id': '667f0befd4964026ee7b6ea2',  # This one has warnings!
            'name': 'Service History Recap (WITH WARNINGS)'
        },
        {
            'id': '667f0c5fd4964026ee7b6ecf',  # CPRA template
            'name': 'CPRA Request Completion'
        },
        {
            'id': '667f0befd4964026ee7b6ea4',  # Another template
            'name': 'Service Appointment Confirmation'
        }
    ]
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    logger.info(f"✅ Connected! Found {len(context.pages)} open tab(s)\n")
    
    # Step 1: Open all template tabs
    logger.info("=" * 100)
    logger.info(f"🌐 OPENING {len(test_templates)} TEMPLATE TABS")
    logger.info("=" * 100)
    
    opened_pages = []
    
    for idx, template in enumerate(test_templates, 1):
        try:
            template_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template['id']}"
            logger.info(f"[{idx}/{len(test_templates)}] Opening: {template['name']}")
            logger.info(f"  URL: {template_url}")
            
            new_page = await context.new_page()
            await new_page.goto(template_url, wait_until='domcontentloaded', timeout=60000)
            
            opened_pages.append({
                'page': new_page,
                'template': template,
                'url': template_url
            })
            
            logger.info(f"  ✅ Opened\n")
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}\n")
    
    logger.info(f"✅ Opened {len(opened_pages)}/{len(test_templates)} tabs\n")
    
    # Step 2: Wait for first template to load and test detection
    if opened_pages:
        logger.info("=" * 100)
        logger.info("🔍 TESTING DETECTION ON FIRST TEMPLATE")
        logger.info("=" * 100)
        
        page = opened_pages[0]['page']
        template = opened_pages[0]['template']
        
        logger.info(f"\nTemplate: {template['name']}")
        logger.info("⏳ Waiting for template to load (17 seconds)...")
        
        # Wait for template to load
        try:
            await page.wait_for_selector('text=/Image|Video|Button/', timeout=15000)
            await asyncio.sleep(17)  # Full load wait
            logger.info("✅ Template loaded\n")
        except:
            logger.warning("⚠️  Timeout, continuing anyway\n")
        
        # Load ignore list
        with open('logo_ignore_list.json') as f:
            ignore_list = json.load(f)
        
        # Detect warnings and logo
        logger.info("🔍 Running detection...")
        result = await page.evaluate("""
            (ignorePatterns) => {
                const analysis = {
                    hasWarnings: false,
                    warningCount: 0,
                    warnings: [],
                    hasLogo: false,
                    logoPosition: null,
                    logoDetails: null,
                    headerButtonGrayed: false
                };
                
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
                
                // 1. DETECT WARNING ICONS
                const warningIcons = document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb');
                
                for (const icon of warningIcons) {
                    const parent = icon.closest('[class*="SortableItem"]');
                    const img = parent ? parent.querySelector('img') : null;
                    
                    if (img && !isIgnored(img)) {
                        const rect = icon.getBoundingClientRect();
                        analysis.warnings.push({
                            position: { x: Math.round(rect.left), y: Math.round(rect.top) },
                            imageSrc: img.src.substring(0, 100)
                        });
                    }
                }
                
                analysis.hasWarnings = analysis.warnings.length > 0;
                analysis.warningCount = analysis.warnings.length;
                
                // 2. DETECT LOGO
                const HEADER_THRESHOLD = 600;
                const allImgs = document.querySelectorAll('img');
                
                for (const img of allImgs) {
                    if (isIgnored(img)) continue;
                    
                    const src = img.src || '';
                    const rect = img.getBoundingClientRect();
                    
                    if (src.includes('amazonaws.com') && src.includes('media_')) {
                        const isReasonableSize = rect.width > 50 && rect.width < 500 &&
                                                rect.height > 20 && rect.height < 200;
                        
                        if (isReasonableSize && rect.top < HEADER_THRESHOLD) {
                            analysis.hasLogo = true;
                            analysis.logoPosition = 'header';
                            analysis.logoDetails = {
                                src: src.substring(0, 150),
                                size: { width: Math.round(rect.width), height: Math.round(rect.height) }
                            };
                            break;
                        }
                    }
                }

                // 3. CHECK HEADER BUTTON
                const headerBtn = document.querySelector('#HEADER');
                if (headerBtn) {
                    const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                    analysis.headerButtonGrayed = opacity < 1;
                }

                return analysis;
            }
        """, ignore_list['ignore_patterns'])

        # Display results
        logger.info("\n" + "=" * 100)
        logger.info("📊 DETECTION RESULTS")
        logger.info("=" * 100)
        logger.info(f"\n✅ Warnings detected: {result['warningCount']}")
        logger.info(f"✅ Logo exists: {result['hasLogo']}")
        logger.info(f"✅ Header button grayed: {result['headerButtonGrayed']}")

        if result['warnings']:
            logger.info(f"\n⚠️  Warning details:")
            for i, warning in enumerate(result['warnings'], 1):
                logger.info(f"   {i}. Position: ({warning['position']['x']}, {warning['position']['y']})")
                logger.info(f"      Image: {warning['imageSrc']}...")

        if result['hasLogo']:
            logger.info(f"\n🎨 Logo details:")
            logger.info(f"   Position: {result['logoPosition']}")
            logger.info(f"   Size: {result['logoDetails']['size']['width']}x{result['logoDetails']['size']['height']}")
            logger.info(f"   Src: {result['logoDetails']['src']}...")

        # Decide action
        has_warnings = result['hasWarnings']
        has_logo = result['hasLogo']

        if not has_warnings and has_logo:
            action = 'SKIP'
        elif has_warnings and has_logo:
            action = 'UPDATE_REMOVE_READD'
        else:
            action = 'UPDATE_ADD_NEW'

        logger.info(f"\n📋 DECISION: {action}")

        if action == 'SKIP':
            logger.info("   ⏭️  No update needed - template is good")
        elif action == 'UPDATE_REMOVE_READD':
            logger.info("   🔄 Need to remove and re-add logo")
        else:
            logger.info("   ➕ Need to add new logo")

    # Summary
    logger.info("\n" + "=" * 100)
    logger.info("✅ TEST COMPLETE")
    logger.info("=" * 100)
    logger.info(f"\n📊 Summary:")
    logger.info(f"   Templates opened: {len(opened_pages)}")
    logger.info(f"   Detection tested on: {opened_pages[0]['template']['name'] if opened_pages else 'None'}")
    logger.info("\n⚠️  Tabs kept open for manual verification")
    logger.info("   Review each tab to see the templates")
    logger.info("   Press Ctrl+C to exit")
    logger.info("=" * 100)

    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("\n✋ Exiting...")


if __name__ == "__main__":
    asyncio.run(test_parallel_updater())
