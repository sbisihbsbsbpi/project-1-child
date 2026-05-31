#!/usr/bin/env python3
"""
Detect Exact 2 Logo Containers - Refined Detection
===================================================

Filters out alignment holders and finds exactly 2 logo placeholders.

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


async def find_exact_2_logo_containers(page):
    """Find exactly 2 logo containers (excluding alignment holders)"""
    
    logger.info("\n" + "="*100)
    logger.info("🎯 FINDING EXACT 2 LOGO CONTAINERS")
    logger.info("="*100)
    
    result = await page.evaluate("""
        () => {
            const result = {
                logoContainers: [],
                allCandidates: []
            };
            
            // Find all SortableItem containers
            const allSortables = Array.from(document.querySelectorAll('[class*="SortableItem"]'));
            
            // Find empty containers in header area
            const candidates = allSortables.filter(item => {
                const img = item.querySelector('img');
                if (img !== null) return false; // Has image, skip
                
                const rect = item.getBoundingClientRect();
                const className = item.className;
                const textContent = item.textContent.trim();
                
                // Criteria for logo placeholder candidate:
                // 1. In header area (top < 500)
                const inHeaderArea = rect.top < 500 && rect.top > 250;
                
                // 2. Reasonable size for logo
                const reasonableSize = rect.width > 50 && rect.width < 400 && 
                                      rect.height > 20 && rect.height < 200;
                
                // 3. Is content container
                const isContentContainer = className.includes('elementContainer');
                
                // 4. No text content (not alignment holder text)
                const isEmpty = textContent.length === 0;
                
                // 5. NOT UI controls
                const notUIControl = !className.includes('removeBtn') && 
                                    !className.includes('dragHandle') &&
                                    !className.includes('hidden');
                
                return inHeaderArea && reasonableSize && isContentContainer && 
                       isEmpty && notUIControl;
            });
            
            // Store all candidates for analysis
            candidates.forEach((container, idx) => {
                const rect = container.getBoundingClientRect();
                const parentRect = container.parentElement?.getBoundingClientRect();
                const containerClassName = container.className;

                result.allCandidates.push({
                    index: allSortables.indexOf(container) + 1,
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    parent: {
                        tagName: container.parentElement?.tagName,
                        className: container.parentElement?.className.substring(0, 100),
                        width: Math.round(parentRect?.width || 0),
                        colspan: container.parentElement?.colSpan || 1
                    },
                    siblings: {
                        before: Array.from(container.parentElement?.children || []).indexOf(container),
                        total: container.parentElement?.children.length || 0
                    },
                    className: containerClassName.substring(0, 100)
                });
            });
            
            // Sort by position (left to right) to get first 2
            const sortedCandidates = candidates.sort((a, b) => {
                const rectA = a.getBoundingClientRect();
                const rectB = b.getBoundingClientRect();
                return rectA.left - rectB.left;
            });
            
            // Take the first 2 as logo containers (leftmost = logo placeholders)
            // The 3rd one (rightmost) is likely the alignment holder
            const logoContainers = sortedCandidates.slice(0, 2);
            
            // Mark the 2 logo containers
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
                        tagName: container.parentElement?.tagName,
                        className: container.parentElement?.className.substring(0, 100)
                    }
                });
                
                // Visual markers - BRIGHT colors
                container.style.outline = '5px solid red';
                container.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
                container.style.border = '3px dashed yellow';
                container.setAttribute('data-logo-placeholder', `logo-placeholder-${idx + 1}`);
                
                // Add text label
                const label = document.createElement('div');
                label.textContent = `LOGO ${idx + 1}`;
                label.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: red; color: white; padding: 5px 10px; font-weight: bold; font-size: 14px; z-index: 9999;';
                container.style.position = 'relative';
                container.appendChild(label);
            });
            
            // Mark the 3rd one (alignment holder) if exists
            if (sortedCandidates.length > 2) {
                const alignmentHolder = sortedCandidates[2];
                alignmentHolder.style.outline = '3px solid blue';
                alignmentHolder.style.backgroundColor = 'rgba(0, 0, 255, 0.1)';
                
                const label = document.createElement('div');
                label.textContent = 'ALIGNMENT';
                label.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: blue; color: white; padding: 5px; font-size: 12px; z-index: 9999;';
                alignmentHolder.style.position = 'relative';
                alignmentHolder.appendChild(label);
            }
            
            return result;
        }
    """)
    
    return result


async def main():
    TARGET_URL = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48"
    
    logger.info("="*100)
    logger.info("🚀 FINDING EXACT 2 LOGO CONTAINERS")
    logger.info("="*100)
    logger.info(f"Target: {TARGET_URL}")
    logger.info("="*100)

    async with async_playwright() as playwright:
        try:
            # Connect to browser
            logger.info("\n🌐 Connecting to browser via CDP...")
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            logger.info("✅ Connected")

            # Find target tab
            logger.info(f"\n🔍 Looking for target template tab...")
            target_page = None

            for page in context.pages:
                if TARGET_URL in page.url:
                    target_page = page
                    logger.info(f"✅ Found target tab")
                    break

            if not target_page:
                logger.error(f"❌ Target template not found!")
                logger.info(f"💡 Please open: {TARGET_URL}")
                return

            # Bring to front
            await target_page.bring_to_front()
            await asyncio.sleep(2)

            # Run detection
            detection = await find_exact_2_logo_containers(target_page)

            # Display results
            logger.info("\n" + "="*100)
            logger.info("📊 DETECTION RESULTS")
            logger.info("="*100)

            logger.info(f"\n📋 SUMMARY:")
            logger.info(f"   Total candidates found: {len(detection['allCandidates'])}")
            logger.info(f"   🎯 Logo containers selected: {len(detection['logoContainers'])}")

            if detection['allCandidates']:
                logger.info(f"\n📦 ALL CANDIDATES ({len(detection['allCandidates'])}):")
                logger.info("   " + "-"*90)
                for i, candidate in enumerate(detection['allCandidates'], 1):
                    marker = "🎯 LOGO" if i <= 2 else "🔵 ALIGNMENT"
                    logger.info(f"\n   {marker} - Container #{candidate['index']}:")
                    logger.info(f"      Position: top={candidate['position']['top']}px, left={candidate['position']['left']}px")
                    logger.info(f"      Size: {candidate['position']['width']}x{candidate['position']['height']}px")
                    logger.info(f"      Parent: <{candidate['parent']['tagName']}> colspan={candidate['parent']['colspan']}")
                    logger.info(f"      Siblings: {candidate['siblings']['before']} of {candidate['siblings']['total']}")

            if detection['logoContainers']:
                logger.info(f"\n🎯 SELECTED LOGO CONTAINERS ({len(detection['logoContainers'])}):")
                logger.info("   " + "-"*90)
                for i, logo in enumerate(detection['logoContainers'], 1):
                    logger.info(f"\n   Logo #{i} - Container #{logo['index']}:")
                    logger.info(f"      Position: top={logo['position']['top']}px, left={logo['position']['left']}px")
                    logger.info(f"      Size: {logo['position']['width']}x{logo['position']['height']}px")
                    logger.info(f"      Parent: <{logo['parent']['tagName']}>")
                    logger.info(f"      Marked with: data-logo-placeholder='logo-placeholder-{i}'")

            logger.info("\n" + "="*100)
            logger.info("✅ DETECTION COMPLETE")
            logger.info("="*100)
            logger.info("🎨 Visual markers in browser:")
            logger.info("   🔴 RED outline + RED background + 'LOGO 1' / 'LOGO 2' label = Logo containers")
            logger.info("   🔵 BLUE outline + 'ALIGNMENT' label = Alignment holder (ignored)")
            logger.info("="*100)

        except Exception as e:
            logger.exception(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
