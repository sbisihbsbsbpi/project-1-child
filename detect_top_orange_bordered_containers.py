#!/usr/bin/env python3
"""
Detect Top Orange-Bordered Logo Containers
===========================================

Finds the actual logo placeholders (orange-bordered boxes at top of template).

Target: https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def find_orange_bordered_logo_containers(page):
    """Find orange-bordered logo containers at top of template"""
    
    logger.info("\n" + "="*100)
    logger.info("🎯 FINDING ORANGE-BORDERED LOGO CONTAINERS")
    logger.info("="*100)
    
    result = await page.evaluate("""
        () => {
            const result = {
                logoContainers: [],
                allTopContainers: []
            };
            
            // Find all SortableItem containers
            const allSortables = Array.from(document.querySelectorAll('[class*="SortableItem"]'));
            
            // Find containers in the VERY TOP area (header with orange borders)
            const topContainers = allSortables.filter(item => {
                const rect = item.getBoundingClientRect();
                // VERY top of template (where orange boxes are in screenshot)
                // top < 100px, width around 150-300px, height around 40-80px
                return rect.top >= 30 && rect.top < 120 &&
                       rect.width >= 80 && rect.width <= 400 &&
                       rect.height >= 30 && rect.height <= 100;
            });
            
            // Sort by left position (left to right)
            topContainers.sort((a, b) => {
                const rectA = a.getBoundingClientRect();
                const rectB = b.getBoundingClientRect();
                return rectA.left - rectB.left;
            });
            
            // Analyze all top containers
            topContainers.forEach((container, idx) => {
                const rect = container.getBoundingClientRect();
                const hasImage = container.querySelector('img') !== null;
                const img = container.querySelector('img');
                const computedStyle = window.getComputedStyle(container);
                const parentStyle = window.getComputedStyle(container.parentElement);
                
                result.allTopContainers.push({
                    index: allSortables.indexOf(container) + 1,
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    hasImage: hasImage,
                    imageInfo: img ? {
                        src: img.src.substring(0, 80),
                        alt: img.alt,
                        width: img.width,
                        height: img.height
                    } : null,
                    style: {
                        border: computedStyle.border,
                        outline: computedStyle.outline,
                        backgroundColor: computedStyle.backgroundColor
                    },
                    parent: {
                        tagName: container.parentElement?.tagName,
                        border: parentStyle.border
                    },
                    className: container.className.substring(0, 100),
                    textContent: container.textContent.substring(0, 50).trim()
                });
            });
            
            // Filter for EMPTY containers (no image) in top area
            // These are the orange-bordered logo placeholders
            const emptyTopContainers = topContainers.filter(item => {
                const img = item.querySelector('img');
                const rect = item.getBoundingClientRect();
                const className = item.className;
                
                // Must be empty (no image)
                const isEmpty = img === null;
                
                // Must be content container
                const isContentContainer = className.includes('elementContainer');
                
                // Must have reasonable size (not too small like alignment borders)
                const reasonableSize = rect.width > 100 && rect.height > 30;
                
                // Must not be UI controls
                const notUIControl = !className.includes('removeBtn') && 
                                    !className.includes('dragHandle') &&
                                    !className.includes('hidden');
                
                // No text content
                const noText = item.textContent.trim().length === 0;
                
                return isEmpty && isContentContainer && reasonableSize && notUIControl && noText;
            });
            
            // Take first 2 logo containers (left to right)
            const logoContainers = emptyTopContainers.slice(0, 2);
            
            // Mark logo containers
            logoContainers.forEach((container, idx) => {
                const rect = container.getBoundingClientRect();
                
                result.logoContainers.push({
                    index: allSortables.indexOf(container) + 1,
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    parent: {
                        tagName: container.parentElement?.tagName
                    }
                });
                
                // Visual markers - VERY BRIGHT
                container.style.outline = '10px solid lime';
                container.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
                container.style.boxShadow = '0 0 20px lime';
                container.setAttribute('data-logo-placeholder', `logo-${idx + 1}`);
                
                // Add large text label
                const label = document.createElement('div');
                label.textContent = `🎯 LOGO ${idx + 1}`;
                label.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: lime; color: black; padding: 10px 20px; font-weight: bold; font-size: 18px; z-index: 99999; border: 3px solid black;';
                container.style.position = 'relative';
                container.appendChild(label);
            });
            
            return result;
        }
    """)

    return result


async def main():
    TARGET_URL = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48"

    logger.info("="*100)
    logger.info("🚀 FINDING ORANGE-BORDERED LOGO CONTAINERS (TOP AREA)")
    logger.info("="*100)
    logger.info(f"Target: {TARGET_URL}")
    logger.info("="*100)

    async with async_playwright() as playwright:
        try:
            # Connect to browser
            logger.info("\n🌐 Connecting to browser...")
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            logger.info("✅ Connected")

            # Find target tab
            target_page = None
            for page in context.pages:
                if TARGET_URL in page.url:
                    target_page = page
                    break

            if not target_page:
                logger.error("❌ Template tab not found!")
                return

            await target_page.bring_to_front()
            await asyncio.sleep(2)

            # Run detection
            detection = await find_orange_bordered_logo_containers(target_page)

            # Display results
            logger.info("\n" + "="*100)
            logger.info("📊 DETECTION RESULTS")
            logger.info("="*100)

            logger.info(f"\n📋 SUMMARY:")
            logger.info(f"   Total top containers: {len(detection['allTopContainers'])}")
            logger.info(f"   🎯 Logo containers found: {len(detection['logoContainers'])}")

            if detection['allTopContainers']:
                logger.info(f"\n📦 ALL TOP CONTAINERS ({len(detection['allTopContainers'])}):")
                logger.info("   " + "-"*90)
                for i, container in enumerate(detection['allTopContainers'], 1):
                    marker = "🎯" if not container['hasImage'] else "✅"
                    logger.info(f"\n   {marker} Container #{container['index']}:")
                    logger.info(f"      Position: top={container['position']['top']}px, left={container['position']['left']}px")
                    logger.info(f"      Size: {container['position']['width']}x{container['position']['height']}px")
                    logger.info(f"      Has Image: {container['hasImage']}")
                    if container['imageInfo']:
                        logger.info(f"      Image: {container['imageInfo']['width']}x{container['imageInfo']['height']}px - {container['imageInfo']['alt']}")
                    logger.info(f"      Text: '{container['textContent']}'")
                    logger.info(f"      Parent: <{container['parent']['tagName']}>")

            if detection['logoContainers']:
                logger.info(f"\n🎯 SELECTED LOGO CONTAINERS ({len(detection['logoContainers'])}):")
                logger.info("   " + "-"*90)
                for i, logo in enumerate(detection['logoContainers'], 1):
                    logger.info(f"\n   Logo #{i} - Container #{logo['index']}:")
                    logger.info(f"      Position: top={logo['position']['top']}px, left={logo['position']['left']}px")
                    logger.info(f"      Size: {logo['position']['width']}x{logo['position']['height']}px")
                    logger.info(f"      Marked: data-logo-placeholder='logo-{i}'")
            else:
                logger.warning("\n⚠️  NO empty logo containers found in top area!")

            logger.info("\n" + "="*100)
            logger.info("✅ DETECTION COMPLETE")
            logger.info("="*100)
            logger.info("🎨 Visual markers:")
            logger.info("   🟢 LIME outline + GREEN background + '🎯 LOGO 1/2' = Logo containers")
            logger.info("="*100)

        except Exception as e:
            logger.exception(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
