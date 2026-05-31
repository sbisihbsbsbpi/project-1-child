#!/usr/bin/env python3
"""
Inspect Media Library Popup Structure
======================================

Opens the media library and analyzes the structure of the Tilton logo tile
to find the correct element to click for selection.
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
    logger.info("🔍 INSPECTING MEDIA LIBRARY STRUCTURE")
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
            
            # STEP 1: Select container and click Insert Image
            logger.info("\n📍 Step 1: Opening media library...")
            await target_page.evaluate("""
                () => {
                    // Click inside first empty container
                    const tables = Array.from(document.querySelectorAll('table'));
                    for (const table of tables) {
                        const tds = Array.from(table.querySelector('tr')?.querySelectorAll('td') || []);
                        if (tds.length === 3) {
                            const editableDiv = tds[0].querySelector('.TEXT_TEMPLATE') || 
                                               tds[0].querySelector('[contenteditable="true"]');
                            if (editableDiv) {
                                editableDiv.click();
                                return true;
                            }
                        }
                    }
                }
            """)
            await asyncio.sleep(1)
            
            # Click Insert Image button
            await target_page.evaluate("""
                () => {
                    const insertBtn = document.querySelector('[aria-label="icon-insert-image"]');
                    if (insertBtn) {
                        const clickable = insertBtn.closest('button') || insertBtn.parentElement || insertBtn;
                        clickable.click();
                    }
                }
            """)
            await asyncio.sleep(3)
            
            logger.info("✅ Media library opened")
            
            # STEP 2: Inspect the Tilton logo tile structure
            logger.info("\n🔍 Step 2: Analyzing Tilton logo tile structure...")
            
            tile_structure = await target_page.evaluate(f"""
                () => {{
                    const images = Array.from(document.querySelectorAll('img'));
                    
                    for (const img of images) {{
                        const src = img.src || '';
                        
                        if (src.includes('{TILTON_LOGO_ID}')) {{
                            const tile = img.closest('[class*="mediaTile"]') ||
                                        img.closest('[class*="tile"]') ||
                                        img.closest('[class*="media"]');
                            
                            if (!tile) {{
                                return {{ found: false, reason: 'No parent tile found' }};
                            }}
                            
                            // Analyze tile structure
                            const result = {{
                                found: true,
                                tileHTML: tile.outerHTML.substring(0, 1000),
                                tileClasses: tile.className,
                                children: []
                            }};
                            
                            // Get all direct children
                            Array.from(tile.children).forEach((child, idx) => {{
                                result.children.push({{
                                    index: idx,
                                    tagName: child.tagName,
                                    className: child.className.substring(0, 80),
                                    role: child.getAttribute('role') || 'none',
                                    hasClick: child.onclick !== null || child.getAttribute('onclick') !== null,
                                    innerHTML: child.innerHTML.substring(0, 200)
                                }});
                            }});
                            
                            // Look for radio buttons
                            const radios = Array.from(tile.querySelectorAll('input[type="radio"]'));
                            result.radioButtons = radios.map(r => ({{
                                id: r.id,
                                checked: r.checked,
                                name: r.name,
                                visible: r.offsetParent !== null
                            }}));
                            
                            // Look for checkboxes
                            const checks = Array.from(tile.querySelectorAll('input[type="checkbox"]'));
                            result.checkboxes = checks.map(c => ({{
                                id: c.id,
                                checked: c.checked,
                                visible: c.offsetParent !== null
                            }}));
                            
                            // Highlight the tile
                            tile.style.outline = '5px solid red';
                            img.style.outline = '3px solid lime';
                            
                            return result;
                        }}
                    }}
                    
                    return {{ found: false, reason: 'Tilton logo not found' }};
                }}
            """)
            
            if not tile_structure['found']:
                logger.error(f"❌ {tile_structure.get('reason')}")
                return
            
            # Display results
            logger.info("\n📊 TILE STRUCTURE:")
            logger.info(f"   Tile Classes: {tile_structure['tileClasses']}")
            logger.info(f"\n   Children ({len(tile_structure['children'])}):")
            for child in tile_structure['children']:
                logger.info(f"      [{child['index']}] <{child['tagName']}> {child['className'][:50]}")
                logger.info(f"          Role: {child['role']} | HasClick: {child['hasClick']}")
            
            if tile_structure['radioButtons']:
                logger.info(f"\n   📻 Radio Buttons ({len(tile_structure['radioButtons'])}):")
                for radio in tile_structure['radioButtons']:
                    checked = "🔴 CHECKED" if radio['checked'] else "⭕ UNCHECKED"
                    visible = "👁️ VISIBLE" if radio['visible'] else "🚫 HIDDEN"
                    logger.info(f"      {checked} {visible} - ID: {radio['id']}")
            else:
                logger.info("\n   ⚠️  No radio buttons found")
            
            if tile_structure['checkboxes']:
                logger.info(f"\n   ☑️  Checkboxes ({len(tile_structure['checkboxes'])}):")
                for checkbox in tile_structure['checkboxes']:
                    checked = "✅ CHECKED" if checkbox['checked'] else "☐ UNCHECKED"
                    visible = "👁️ VISIBLE" if checkbox['visible'] else "🚫 HIDDEN"
                    logger.info(f"      {checked} {visible} - ID: {checkbox['id']}")
            else:
                logger.info("\n   ⚠️  No checkboxes found")
            
            logger.info("\n✅ Tile highlighted in RED in browser - inspect it to see the structure!")
            
        except Exception as e:
            logger.exception(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
