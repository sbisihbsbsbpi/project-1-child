#!/usr/bin/env python3
"""
Detect Media Library Popup Contents
====================================

After clicking Insert Image, detect what's in the media library popup.
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TILTON_LOGO_ID = "6a19132b6697f36de6236fb1"


async def main():
    TARGET_URL = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48"
    
    logger.info("="*100)
    logger.info("🔍 DETECTING MEDIA LIBRARY POPUP")
    logger.info("="*100)
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            
            target_page = None
            for page in context.pages:
                if TARGET_URL in page.url:
                    target_page = page
                    break
            
            if not target_page:
                logger.error("❌ Template not found!")
                return
            
            await target_page.bring_to_front()
            await asyncio.sleep(2)
            
            # STEP 1: Select container
            logger.info("\n📍 Step 1: Selecting container...")
            await target_page.evaluate("""
                () => {
                    const tables = Array.from(document.querySelectorAll('table'));
                    for (const table of tables) {
                        const tds = Array.from(table.querySelector('tr')?.querySelectorAll('td') || []);
                        if (tds.length === 3) {
                            const container = tds[0].querySelector('[class*="elementContainer"]');
                            if (container) {
                                container.click();
                                return true;
                            }
                        }
                    }
                }
            """)
            await asyncio.sleep(1)
            logger.info("✅ Container selected")
            
            # STEP 2: Click Insert Image
            logger.info("\n🖼️  Step 2: Clicking Insert Image...")
            clicked = await target_page.evaluate("""
                () => {
                    const allElements = Array.from(document.querySelectorAll('*'));
                    
                    for (const el of allElements) {
                        const text = el.textContent?.trim() || '';
                        
                        if (text.toLowerCase() === 'insert image') {
                            if (el.offsetParent !== null) {
                                el.click();
                                return { clicked: true };
                            }
                        }
                    }
                    
                    return { clicked: false };
                }
            """)
            
            if not clicked['clicked']:
                logger.error("❌ Insert Image button not found!")
                return
            
            logger.info("✅ Clicked Insert Image")
            await asyncio.sleep(3)  # Wait for popup to open
            
            # STEP 3: Analyze media library popup
            logger.info("\n📂 Step 3: Analyzing media library popup...")
            
            popup_info = await target_page.evaluate(f"""
                () => {{
                    const result = {{
                        popupFound: false,
                        popupType: 'unknown',
                        images: [],
                        tiltonLogo: null,
                        allElements: []
                    }};
                    
                    // Check for popup/modal
                    const popup = document.querySelector('[role="dialog"]') || 
                                 document.querySelector('.ant-modal') ||
                                 document.querySelector('[class*="modal"]');
                    
                    if (popup) {{
                        result.popupFound = true;
                        const rect = popup.getBoundingClientRect();
                        result.popupType = popup.className.substring(0, 80);
                        
                        // Find all images in popup
                        const images = Array.from(popup.querySelectorAll('img'));
                        
                        images.forEach((img, idx) => {{
                            const imgRect = img.getBoundingClientRect();
                            const src = img.src || '';
                            const alt = img.alt || '';
                            
                            const imgInfo = {{
                                index: idx + 1,
                                src: src.substring(0, 100),
                                alt: alt,
                                width: Math.round(imgRect.width),
                                height: Math.round(imgRect.height),
                                hasTiltonId: src.includes('{TILTON_LOGO_ID}'),
                                parent: {{
                                    tagName: img.parentElement?.tagName,
                                    className: img.parentElement?.className.substring(0, 60)
                                }}
                            }};
                            
                            result.images.push(imgInfo);
                            
                            // Check if this is Tilton logo
                            if (src.includes('{TILTON_LOGO_ID}')) {{
                                result.tiltonLogo = imgInfo;
                                
                                // Highlight it
                                img.style.outline = '5px solid lime';
                                if (img.parentElement) {{
                                    img.parentElement.style.outline = '3px solid yellow';
                                }}
                            }}
                        }});
                        
                        // Get some other elements in popup for debugging
                        const buttons = Array.from(popup.querySelectorAll('button'));
                        result.allElements = buttons.slice(0, 5).map(btn => ({{
                            tagName: 'BUTTON',
                            text: btn.textContent.substring(0, 40),
                            className: btn.className.substring(0, 60)
                        }}));
                    }}
                    
                    return result;
                }}
            """)
            
            # Display results
            logger.info(f"\n📊 RESULTS:")
            logger.info(f"   Popup found: {popup_info['popupFound']}")
            
            if popup_info['popupFound']:
                logger.info(f"   Popup type: {popup_info['popupType']}")
                logger.info(f"   Total images: {len(popup_info['images'])}")
                logger.info(f"   Tilton logo found: {popup_info['tiltonLogo'] is not None}")
                
                if popup_info['tiltonLogo']:
                    logger.info(f"\n🎯 TILTON LOGO DETECTED:")
                    logo = popup_info['tiltonLogo']
                    logger.info(f"   Index: {logo['index']}")
                    logger.info(f"   Src: {logo['src']}")
                    logger.info(f"   Alt: {logo['alt']}")
                    logger.info(f"   Size: {logo['width']}x{logo['height']}px")
                    logger.info(f"   Parent: <{logo['parent']['tagName']}> {logo['parent']['className'][:40]}")
                    logger.info(f"\n   ✅ HIGHLIGHTED IN BROWSER WITH LIME OUTLINE!")
                
                if popup_info['images']:
                    logger.info(f"\n📸 ALL IMAGES IN POPUP (first 10):")
                    for img in popup_info['images'][:10]:
                        marker = "🎯" if img['hasTiltonId'] else "  "
                        logger.info(f"   {marker} {img['index']}. {img['width']}x{img['height']}px - {img['alt'][:40]}")
                        logger.info(f"       src: {img['src'][:80]}")
                
                if popup_info['allElements']:
                    logger.info(f"\n🔘 BUTTONS IN POPUP:")
                    for btn in popup_info['allElements']:
                        logger.info(f"   - {btn['text']}")
            else:
                logger.warning("⚠️  No popup/modal found! Media library may not have opened.")
            
            logger.info("\n" + "="*100)
            logger.info("✅ Detection complete! Check browser for highlighted Tilton logo.")
            logger.info("="*100)
            
        except Exception as e:
            logger.exception(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
