#!/usr/bin/env python3
"""
Complete Flow: Template List → Edit → Popup → Radio Buttons → Insert Button
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
    logger.info("🚀 COMPLETE FLOW: LIST → EDIT → POPUP → RADIO BUTTONS")
    logger.info("=" * 100)
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        # STEP 1: Navigate to template list
        logger.info("\n" + "=" * 100)
        logger.info("STEP 1: Starting from Template List Page")
        logger.info("=" * 100)
        
        # Check if we have a list page already open
        pages = context.pages
        list_page = None
        
        for existing_page in pages:
            if '/templates/list' in existing_page.url:
                list_page = existing_page
                logger.info("✅ Found existing template list page")
                break
        
        if not list_page:
            logger.info("Opening template list page...")
            list_page = await context.new_page()
            await list_page.goto("https://preprodapp.tekioncloud.com/templates/list")
            await asyncio.sleep(4)
        
        logger.info(f"Current URL: {list_page.url}")
        
        # STEP 2: Click on a template to open editor
        logger.info("\n" + "=" * 100)
        logger.info("STEP 2: Opening Template Editor")
        logger.info("=" * 100)
        
        # We'll use the known template ID with warning logo
        template_id = "667f0befd4964026ee7b6ea2"  # Service History Recap PDF
        edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        
        # Check if template edit page is already open
        edit_page = None
        for existing_page in pages:
            if template_id in existing_page.url:
                edit_page = existing_page
                logger.info("✅ Template editor already open")
                break
        
        if not edit_page:
            logger.info(f"Opening template editor: {template_id}")
            edit_page = await context.new_page()
            await edit_page.goto(edit_url)
            await asyncio.sleep(20)  # Wait for template to load
            logger.info("✅ Template editor loaded")
        else:
            # Bring to front
            await edit_page.bring_to_front()
            logger.info("✅ Using existing template editor page")
        
        # STEP 3: Find logo with warning icon
        logger.info("\n" + "=" * 100)
        logger.info("STEP 3: Finding Logo with Warning Icon")
        logger.info("=" * 100)
        
        container_found = await edit_page.evaluate("""
            () => {
                const warningIcon = document.querySelector('.templates_Image_warningIcon__hCZHMuhEmb');
                if (!warningIcon) return false;
                
                const sortableItem = warningIcon.closest('[class*="SortableItem"]');
                if (sortableItem) {
                    sortableItem.setAttribute('data-logo-to-inspect', 'true');
                    
                    // Highlight it
                    sortableItem.style.outline = '5px solid orange';
                    sortableItem.style.backgroundColor = 'rgba(255, 165, 0, 0.2)';
                    
                    return true;
                }
                return false;
            }
        """)
        
        if not container_found:
            logger.error("❌ No logo with warning found!")
            logger.info("   Make sure the template has a broken/warning logo")
            return
        
        logger.info("✅ Found logo with warning (highlighted in ORANGE)")
        await asyncio.sleep(2)
        
        # STEP 4: Hover to reveal toolbar
        logger.info("\n" + "=" * 100)
        logger.info("STEP 4: Hovering to Reveal Toolbar")
        logger.info("=" * 100)
        
        container = await edit_page.query_selector('[data-logo-to-inspect="true"]')
        logger.info("Hovering over logo...")
        await container.hover(force=True)
        await asyncio.sleep(3)  # Wait for toolbar to appear
        
        logger.info("✅ Hovered - toolbar should be visible")
        
        # STEP 5: Click "Change Image" icon
        logger.info("\n" + "=" * 100)
        logger.info("STEP 5: Clicking 'Change Image' Icon")
        logger.info("=" * 100)
        
        # Check if popup is already open
        popup_already_open = await edit_page.evaluate("""
            () => {
                const popup = document.querySelector('[role="dialog"]') || document.querySelector('.ant-modal');
                return popup && popup.getBoundingClientRect().width > 0;
            }
        """)
        
        if popup_already_open:
            logger.info("✅ Popup already open!")
        else:
            change_clicked = await edit_page.evaluate("""
                () => {
                    const container = document.querySelector('[data-logo-to-inspect="true"]');
                    if (!container) return { clicked: false, reason: 'Container not found' };
                    
                    const changeIcon = container.querySelector('[aria-label="icon-switch"]') ||
                                      container.querySelector('[title="Change Image"]');
                    
                    if (changeIcon) {
                        changeIcon.click();
                        return { clicked: true };
                    }
                    
                    return { clicked: false, reason: 'Change Image icon not found in toolbar' };
                }
            """)
            
            if not change_clicked['clicked']:
                logger.error(f"❌ {change_clicked.get('reason', 'Unknown error')}")
                logger.info("\n💡 Tip: The Change Image icon only appears when hovering over the logo")
                return
            
            logger.info("✅ Clicked 'Change Image' icon")
            await asyncio.sleep(3)  # Wait for popup
        
        # STEP 6: Detect Radio Buttons in Popup
        logger.info("\n" + "=" * 100)
        logger.info("STEP 6: Detecting Radio Buttons in Popup")
        logger.info("=" * 100)
