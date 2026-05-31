#!/usr/bin/env python3
"""
Detect Logo Placeholders by Position - Smart Detection
=======================================================

Uses position-based heuristics to find ACTUAL logo placeholders
by comparing with known working logo container positions.

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


async def analyze_containers_by_position(page):
    """Analyze containers by their position and characteristics"""
    
    logger.info("\n" + "="*100)
    logger.info("🎯 SMART LOGO PLACEHOLDER DETECTION")
    logger.info("="*100)
    
    # Run comprehensive position-based analysis
    analysis_result = await page.evaluate("""
        () => {
            const result = {
                timestamp: new Date().toISOString(),
                
                // Step 1: Analyze existing correct logos to learn the pattern
                existingLogos: [],
                
                // Step 2: Find empty containers matching the pattern
                logoPlaceholders: [],
                
                // Step 3: All empty containers for comparison
                allEmptyContainers: [],
                
                // Summary
                summary: {}
            };
            
            // Find all SortableItem containers
            const allSortables = Array.from(document.querySelectorAll('[class*="SortableItem"]'));
            
            // ============================================================
            // STEP 1: Analyze EXISTING correct logos to learn the pattern
            // ============================================================
            const existingLogoContainers = allSortables.filter(item => {
                const img = item.querySelector('img');
                if (!img) return false;
                
                // Look for logos in header area (top of template)
                // Skip small icons (< 50px) and Tekion logo
                const src = img.src || '';
                const alt = img.alt || '';
                const rect = item.getBoundingClientRect();
                
                // Header logos are typically:
                // - In top area (y < 800)
                // - Width > 50px
                // - Not system icons (no "icon-" in src)
                // - Not Tekion logo
                
                const isHeaderArea = rect.top < 800;
                const isReasonableSize = rect.width > 50 && rect.height > 20;
                const notSystemIcon = !src.includes('icon-') && !alt.toLowerCase().includes('icon');
                const notTekionLogo = !src.includes('tekion-logo');
                const notAmenityIcon = !src.includes('/TV.') && !src.includes('/Wifi.') && 
                                      !src.includes('/Water.') && !src.includes('/Coffee.');
                
                return isHeaderArea && isReasonableSize && notSystemIcon && 
                       notTekionLogo && notAmenityIcon;
            });
            
            // Extract characteristics of existing logo containers
            existingLogoContainers.forEach((container, idx) => {
                const img = container.querySelector('img');
                const rect = container.getBoundingClientRect();
                const parentRect = container.parentElement?.getBoundingClientRect();
                
                result.existingLogos.push({
                    index: allSortables.indexOf(container) + 1,
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        right: Math.round(rect.right),
                        bottom: Math.round(rect.bottom),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    parent: {
                        className: container.parentElement?.className.substring(0, 100),
                        tagName: container.parentElement?.tagName
                    },
                    image: {
                        src: img.src.substring(0, 100),
                        alt: img.alt,
                        width: img.width,
                        height: img.height
                    },
                    siblings: {
                        before: Array.from(container.parentElement?.children || [])
                            .indexOf(container),
                        total: container.parentElement?.children.length || 0
                    }
                });
                
                // Mark for visualization
                container.style.outline = '3px solid lime';
                container.setAttribute('data-existing-logo', `logo-${idx + 1}`);
            });
            
            // ============================================================
            // STEP 2: Find EMPTY containers matching the pattern
            // ============================================================
            
            // Calculate reference positions from existing logos
            const avgTop = result.existingLogos.length > 0
                ? result.existingLogos.reduce((sum, l) => sum + l.position.top, 0) / result.existingLogos.length
                : 300;
            const avgHeight = result.existingLogos.length > 0
                ? result.existingLogos.reduce((sum, l) => sum + l.position.height, 0) / result.existingLogos.length
                : 100;

            // Find empty containers
            const emptyContainers = allSortables.filter(item => {
                const img = item.querySelector('img');
                return img === null;
            });
            
            result.allEmptyContainers = emptyContainers.map((item, idx) => {
                const rect = item.getBoundingClientRect();
                return {
                    index: allSortables.indexOf(item) + 1,
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    textContent: item.textContent.substring(0, 80).trim(),
                    className: item.className.substring(0, 100)
                };
            });
            
            // Filter for logo placeholders based on learned pattern
            const logoPlaceholders = emptyContainers.filter(item => {
                const rect = item.getBoundingClientRect();
                const textContent = item.textContent.trim();
                const className = item.className;

                // Criteria for logo placeholder:
                // 1. In header area (similar top position as existing logos ± 200px)
                const similarTopPosition = Math.abs(rect.top - avgTop) < 200;

                // 2. Similar or reasonable size for logo
                const reasonableSize = rect.width > 50 && rect.height > 20 &&
                                      rect.width < 600 && rect.height < 400;

                // 3. NOT a UI control (no text content or very specific classes)
                const notUIControl = !className.includes('removeBtn') &&
                                    !className.includes('dragHandle') &&
                                    !className.includes('hidden');

                // 4. NOT CSS or script content
                const notCode = !textContent.includes('.layout__') &&
                               !textContent.includes('color:') &&
                               !textContent.includes('{') &&
                               !textContent.includes('BUILDER_APP');

                // 5. Either empty or has minimal text (like placeholder text)
                const minimalText = textContent.length < 50;

                // 6. Has elementContainer class (actual content containers)
                const isContentContainer = className.includes('elementContainer');

                return similarTopPosition && reasonableSize && notUIControl &&
                       notCode && minimalText && isContentContainer;
            });

            // Mark logo placeholders
            logoPlaceholders.forEach((container, idx) => {
                const rect = container.getBoundingClientRect();

                result.logoPlaceholders.push({
                    index: allSortables.indexOf(container) + 1,
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    textContent: container.textContent.substring(0, 80).trim(),
                    className: container.className.substring(0, 100),
                    parent: {
                        className: container.parentElement?.className.substring(0, 100),
                        tagName: container.parentElement?.tagName
                    }
                });

                // Visual marker
                container.style.outline = '5px solid red';
                container.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
                container.setAttribute('data-logo-placeholder', `placeholder-${idx + 1}`);
            });

            // Summary
            result.summary = {
                totalSortableItems: allSortables.length,
                existingLogos: result.existingLogos.length,
                totalEmptyContainers: emptyContainers.length,
                logoPlaceholders: result.logoPlaceholders.length,
                referencePosition: {
                    avgTop: Math.round(avgTop),
                    avgHeight: Math.round(avgHeight)
                }
            };

            return result;
        }
    """)

    return analysis_result


async def main():
    """Main detection workflow"""

    TARGET_URL = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48"

    logger.info("="*100)
    logger.info("🚀 SMART LOGO PLACEHOLDER DETECTION BY POSITION")
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

            # Run analysis
            analysis = await analyze_containers_by_position(target_page)

            # Display results
            logger.info("\n" + "="*100)
            logger.info("📊 ANALYSIS RESULTS")
            logger.info("="*100)

            summary = analysis['summary']
            logger.info(f"\n📋 SUMMARY:")
            logger.info(f"   Total SortableItem containers: {summary['totalSortableItems']}")
            logger.info(f"   ✅ Existing logos found: {summary['existingLogos']}")
            logger.info(f"   📦 Total empty containers: {summary['totalEmptyContainers']}")
            logger.info(f"   🎯 Logo placeholders detected: {summary['logoPlaceholders']}")
            logger.info(f"   📍 Reference position: top={summary['referencePosition']['avgTop']}px, height={summary['referencePosition']['avgHeight']}px")

            # Show existing logos pattern
            if analysis['existingLogos']:
                logger.info(f"\n✅ EXISTING LOGOS ({len(analysis['existingLogos'])}): [LIME outline]")
                logger.info("   " + "-"*90)
                for logo in analysis['existingLogos']:
                    logger.info(f"\n   Container #{logo['index']}:")
                    logger.info(f"      Position: top={logo['position']['top']}px, left={logo['position']['left']}px")
                    logger.info(f"      Size: {logo['position']['width']}x{logo['position']['height']}px")
                    logger.info(f"      Image: {logo['image']['width']}x{logo['image']['height']}px - {logo['image']['alt']}")
                    logger.info(f"      Parent: <{logo['parent']['tagName']}> {logo['parent']['className'][:60]}")

            # Show detected logo placeholders
            if analysis['logoPlaceholders']:
                logger.info(f"\n🎯 LOGO PLACEHOLDERS DETECTED ({len(analysis['logoPlaceholders'])}): [RED outline + RED background]")
                logger.info("   " + "-"*90)
                for placeholder in analysis['logoPlaceholders']:
                    logger.info(f"\n   Container #{placeholder['index']}:")
                    logger.info(f"      Position: top={placeholder['position']['top']}px, left={placeholder['position']['left']}px")
                    logger.info(f"      Size: {placeholder['position']['width']}x{placeholder['position']['height']}px")
                    logger.info(f"      Text: {placeholder['textContent'][:60] if placeholder['textContent'] else '(empty)'}")
                    logger.info(f"      Class: {placeholder['className'][:80]}")
                    logger.info(f"      Parent: <{placeholder['parent']['tagName']}> {placeholder['parent']['className'][:60]}")
            else:
                logger.info(f"\n⚠️  NO logo placeholders detected matching the pattern")
                logger.info(f"   This could mean:")
                logger.info(f"   1. All logo containers already have images")
                logger.info(f"   2. Empty placeholders don't match expected pattern")
                logger.info(f"   3. Need to adjust detection criteria")

            # Show sample of other empty containers for comparison
            if analysis['allEmptyContainers']:
                logger.info(f"\n📦 SAMPLE OF OTHER EMPTY CONTAINERS (first 5):")
                logger.info("   " + "-"*90)
                for container in analysis['allEmptyContainers'][:5]:
                    logger.info(f"   #{container['index']}: top={container['position']['top']}px, {container['position']['width']}x{container['position']['height']}px")
                    logger.info(f"      Text: {container['textContent'][:60] if container['textContent'] else '(empty)'}")

            logger.info("\n" + "="*100)
            logger.info("✅ ANALYSIS COMPLETE")
            logger.info("="*100)
            logger.info("🎨 Visual markers:")
            logger.info("   LIME outline = Existing logos (reference pattern)")
            logger.info("   RED outline + RED background = Detected logo placeholders")
            logger.info("="*100)

        except Exception as e:
            logger.exception(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
