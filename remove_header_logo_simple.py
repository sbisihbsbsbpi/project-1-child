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
        
        logger.info("\n📋 Step 3: Click X icon")
        
        # Try specific selector first, then generic patterns
        result = await working_tab.evaluate("""
            () => {
                // Try specific known selector first
                const removeBtn = document.querySelector('.templates_SortableItem_removeBtn__osvYZsTyqJ');
                if (removeBtn) {
                    removeBtn.click();
                    return { success: true, method: 'specific selector (.templates_SortableItem_removeBtn__)' };
                }

                // Try generic removeBtn pattern
                const genericRemove = document.querySelector('[class*="removeBtn"]');
                if (genericRemove) {
                    genericRemove.click();
                    return { success: true, method: 'generic removeBtn selector' };
                }

                return { success: false, error: 'X icon not found' };
            }
        """)

        if result['success']:
            logger.info(f"   ✅ X icon clicked! (Method: {result['method']})")

            await asyncio.sleep(1)

            # Verify logo is removed
            logo_check = await working_tab.evaluate("""
                () => {
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

                    return { logoStillPresent: headerLogoFound };
                }
            """)

            if logo_check['logoStillPresent']:
                logger.warning("   ⚠️  Logo still present after click")
                return False
            else:
                logger.info("\n" + "=" * 100)
                logger.info("🎉 SUCCESS! Header logo removed!")
                logger.info("=" * 100)
                return True
        else:
            logger.error(f"   ❌ {result.get('error', 'Unknown error')}")
            return False


if __name__ == "__main__":
    success = asyncio.run(remove_header_logo())
    exit(0 if success else 1)
