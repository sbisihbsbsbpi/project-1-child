#!/usr/bin/env python3
"""
Detect Empty Logo Containers - Temporary Analysis Script
=========================================================

Analyzes template to detect empty logo containers (placeholders without images)

Target: https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def detect_empty_containers(page):
    """Detect all types of logo containers"""
    
    logger.info("\n" + "="*100)
    logger.info("🔍 DETECTING EMPTY LOGO CONTAINERS")
    logger.info("="*100)
    
    # Run comprehensive detection
    detection_result = await page.evaluate("""
        () => {
            const result = {
                timestamp: new Date().toISOString(),
                
                // Type 1: Containers with warning icons (existing logos)
                containersWithWarnings: [],
                
                // Type 2: Containers with images but NO warnings (correct logos)
                containersWithCorrectLogos: [],
                
                // Type 3: Empty containers (placeholders, no images)
                emptyContainers: [],
                
                // Type 4: All SortableItem containers (for debugging)
                allSortableItems: [],
                
                // Summary
                summary: {}
            };
            
            // Find all SortableItem containers
            const allSortables = Array.from(document.querySelectorAll('[class*="SortableItem"]'));
            
            result.allSortableItems = allSortables.map((item, idx) => {
                const hasImage = item.querySelector('img') !== null;
                const hasWarning = item.querySelector('.templates_Image_warningIcon__hCZHMuhEmb') !== null;
                const img = item.querySelector('img');
                
                return {
                    index: idx + 1,
                    hasImage: hasImage,
                    hasWarning: hasWarning,
                    imageSrc: img ? img.src.substring(0, 100) : 'NO IMAGE',
                    imageAlt: img ? img.alt : 'NO IMAGE',
                    innerHTML: item.innerHTML.substring(0, 200),
                    textContent: item.textContent.substring(0, 150).trim(),
                    classNames: item.className.substring(0, 150)
                };
            });
            
            // Categorize containers
            allSortables.forEach((item, idx) => {
                const hasImage = item.querySelector('img') !== null;
                const hasWarning = item.querySelector('.templates_Image_warningIcon__hCZHMuhEmb') !== null;
                const img = item.querySelector('img');
                
                if (hasWarning) {
                    // Type 1: Has warning icon (logo exists but wrong)
                    result.containersWithWarnings.push({
                        index: idx + 1,
                        imageSrc: img ? img.src.substring(0, 100) : 'unknown',
                        imageAlt: img ? img.alt : 'unknown'
                    });
                    
                    // Mark for processing
                    item.setAttribute('data-logo-with-warning', `warning-${idx + 1}`);
                    
                } else if (hasImage) {
                    // Type 2: Has image but no warning (correct logo)
                    result.containersWithCorrectLogos.push({
                        index: idx + 1,
                        imageSrc: img.src.substring(0, 100),
                        imageAlt: img.alt,
                        width: img.width,
                        height: img.height
                    });
                    
                    // Mark for identification
                    item.setAttribute('data-logo-correct', `correct-${idx + 1}`);
                    
                } else {
                    // Type 3: No image = EMPTY CONTAINER
                    result.emptyContainers.push({
                        index: idx + 1,
                        textContent: item.textContent.substring(0, 100).trim(),
                        innerHTML: item.innerHTML.substring(0, 200),
                        classNames: item.className.substring(0, 150)
                    });
                    
                    // Mark for processing
                    item.setAttribute('data-empty-logo-container', `empty-${idx + 1}`);
                    item.style.outline = '3px solid orange';  // Visual marker
                }
            });
            
            // Generate summary
            result.summary = {
                totalSortableItems: allSortables.length,
                withWarnings: result.containersWithWarnings.length,
                withCorrectLogos: result.containersWithCorrectLogos.length,
                emptyContainers: result.emptyContainers.length
            };
            
            return result;
        }
    """)
    
    return detection_result


async def main():
    """Main detection workflow"""
    
    TARGET_URL = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48"
    
    logger.info("="*100)
    logger.info("🚀 EMPTY LOGO CONTAINER DETECTION")
    logger.info("="*100)
    logger.info(f"Target: {TARGET_URL}")
    logger.info("="*100)
    
    async with async_playwright() as playwright:
        try:
            # Connect to browser
            logger.info("\n🌐 Connecting to browser via CDP...")
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            logger.info("✅ Connected to browser")

            # Find the target template tab
            logger.info(f"\n🔍 Looking for target template tab...")
            target_page = None

            for page in context.pages:
                if TARGET_URL in page.url:
                    target_page = page
                    logger.info(f"✅ Found target tab: {page.url}")
                    break

            if not target_page:
                logger.error(f"❌ Target template not found!")
                logger.info(f"💡 Please open this URL in your browser: {TARGET_URL}")
                return

            # Bring page to front
            await target_page.bring_to_front()
            await asyncio.sleep(2)

            # Run detection
            detection = await detect_empty_containers(target_page)

            # Display results
            logger.info("\n" + "="*100)
            logger.info("📊 DETECTION RESULTS")
            logger.info("="*100)

            summary = detection['summary']
            logger.info(f"\n📋 SUMMARY:")
            logger.info(f"   Total SortableItem containers: {summary['totalSortableItems']}")
            logger.info(f"   ⚠️  With warnings (wrong logos): {summary['withWarnings']}")
            logger.info(f"   ✅ With correct logos: {summary['withCorrectLogos']}")
            logger.info(f"   📦 Empty containers: {summary['emptyContainers']}")

            # Show containers with warnings
            if detection['containersWithWarnings']:
                logger.info(f"\n⚠️  CONTAINERS WITH WARNINGS ({len(detection['containersWithWarnings'])}):")
                for container in detection['containersWithWarnings']:
                    logger.info(f"   #{container['index']}: {container['imageAlt']} - {container['imageSrc'][:80]}")

            # Show correct logos
            if detection['containersWithCorrectLogos']:
                logger.info(f"\n✅ CONTAINERS WITH CORRECT LOGOS ({len(detection['containersWithCorrectLogos'])}):")
                for container in detection['containersWithCorrectLogos']:
                    logger.info(f"   #{container['index']}: {container['width']}x{container['height']}px - {container['imageAlt']}")

            # Show empty containers (MAIN FOCUS)
            if detection['emptyContainers']:
                logger.info(f"\n📦 EMPTY LOGO CONTAINERS ({len(detection['emptyContainers'])}):")
                logger.info("   " + "-"*90)
                for container in detection['emptyContainers']:
                    logger.info(f"\n   Container #{container['index']}:")
                    logger.info(f"      Text: {container['textContent']}")
                    logger.info(f"      Classes: {container['classNames']}")
                    logger.info(f"      HTML Preview: {container['innerHTML'][:100]}...")
                logger.info("\n   " + "-"*90)
                logger.info(f"   🎯 Empty containers have been marked with ORANGE outline in browser")

            # Show all containers for debugging
            logger.info(f"\n🔧 ALL SORTABLE ITEMS ({len(detection['allSortableItems'])}):")
            logger.info("   " + "-"*90)
            for item in detection['allSortableItems']:
                status = "⚠️ WARNING" if item['hasWarning'] else ("✅ CORRECT" if item['hasImage'] else "📦 EMPTY")
                logger.info(f"   #{item['index']}: {status}")
                logger.info(f"      Has Image: {item['hasImage']}, Has Warning: {item['hasWarning']}")
                logger.info(f"      Image: {item['imageSrc'][:80]}")
                logger.info(f"      Text: {item['textContent'][:100]}")
                logger.info("")

            logger.info("\n" + "="*100)
            logger.info("✅ DETECTION COMPLETE")
            logger.info("="*100)
            logger.info("💡 Check your browser - empty containers are outlined in ORANGE")
            logger.info("="*100)

        except Exception as e:
            logger.exception(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
