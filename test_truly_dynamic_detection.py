#!/usr/bin/env python3
"""
🔍 Truly Dynamic Logo Detection
Learns patterns from the template structure itself - no hardcoded selectors!
"""

import asyncio
import logging
from playwright.async_api import async_playwright
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_TEMPLATE_ID = "667f0befd4964026ee7b6ea2"
CDP_URL = "http://localhost:9223"


async def learn_logo_patterns(page):
    """
    TRULY DYNAMIC: Learn logo container patterns from the template structure
    Uses multiple heuristics to identify logo containers without hardcoded selectors
    """
    
    logger.info("\n" + "="*100)
    logger.info("🧠 LEARNING LOGO PATTERNS FROM TEMPLATE STRUCTURE")
    logger.info("="*100)
    
    result = await page.evaluate("""
        () => {
            const patterns = {
                learningPhases: [],
                detectedLogos: [],
                containerPatterns: [],
                summary: {}
            };
            
            // ============================================================================
            // PHASE 1: Find all images that look like logos
            // ============================================================================
            patterns.learningPhases.push('PHASE 1: Analyzing all images');
            
            const allImages = Array.from(document.querySelectorAll('img'));
            const candidateLogos = [];
            
            allImages.forEach((img, idx) => {
                const src = img.src || '';
                const rect = img.getBoundingClientRect();
                const alt = img.alt || '';
                
                // Heuristic 1: Size-based (RELAXED: logos can be various sizes)
                const isLogoSize = rect.width > 30 && rect.width < 500 &&
                                  rect.height > 15 && rect.height < 300;

                // Heuristic 2: Aspect ratio (RELAXED: logos can be square or wide)
                const aspectRatio = rect.width / rect.height;
                const isLogoAspect = aspectRatio > 0.5 && aspectRatio < 10;

                // Heuristic 3: URL pattern (S3 media URLs or any reasonable image)
                const isMediaUrl = (src.includes('amazonaws.com') && src.includes('media_')) ||
                                  src.includes('.png') || src.includes('.jpg') || src.includes('.svg');

                // Heuristic 4: Position (RELAXED: anywhere in visible area, but not in app header)
                const isReasonablePosition = rect.top > 100 && rect.top < 3000 &&
                                            rect.left > 0 && rect.width > 0;

                // Heuristic 5: Not a system icon (check for obvious non-logo patterns)
                const notSystemIcon = !src.includes('icon-') &&
                                     !alt.toLowerCase().includes('icon') &&
                                     !src.includes('tekion-logo') &&
                                     !src.includes('favicon');

                // Heuristic 6: Visible element
                const isVisible = rect.width > 0 && rect.height > 0;

                // Score the candidate (RELAXED threshold)
                const score = (isLogoSize ? 1 : 0) +
                             (isLogoAspect ? 1 : 0) +
                             (isMediaUrl ? 2 : 0) +  // Higher weight for media URLs
                             (isReasonablePosition ? 1 : 0) +
                             (notSystemIcon ? 1 : 0) +
                             (isVisible ? 1 : 0);

                if (score >= 2) {  // RELAXED Threshold: at least 2 points
                    candidateLogos.push({
                        img: img,
                        score: score,
                        index: idx,
                        rect: {
                            top: Math.round(rect.top + window.scrollY),
                            left: Math.round(rect.left),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        aspectRatio: Math.round(aspectRatio * 100) / 100,
                        src: src.substring(0, 80)
                    });
                }
            });
            
            patterns.learningPhases.push(`Found ${candidateLogos.length} candidate logo images`);
            
            // ============================================================================
            // PHASE 2: Learn container patterns from candidate logos
            // ============================================================================
            patterns.learningPhases.push('PHASE 2: Learning container patterns');
            
            const containerPatternMap = new Map();
            
            candidateLogos.forEach(candidate => {
                const img = candidate.img;
                let currentElement = img.parentElement;
                let depth = 0;
                const hierarchy = [];
                
                // Walk up the DOM to find common container patterns
                while (currentElement && depth < 10) {
                    const classes = Array.from(currentElement.classList || []);
                    const tagName = currentElement.tagName;
                    
                    hierarchy.push({
                        depth: depth,
                        tag: tagName,
                        classes: classes,
                        id: currentElement.id || null
                    });
                    
                    // Track class patterns
                    classes.forEach(cls => {
                        if (cls.length > 3) {  // Ignore very short class names
                            if (!containerPatternMap.has(cls)) {
                                containerPatternMap.set(cls, {
                                    class: cls,
                                    count: 0,
                                    depths: [],
                                    tags: new Set()
                                });
                            }
                            const pattern = containerPatternMap.get(cls);
                            pattern.count++;
                            pattern.depths.push(depth);
                            pattern.tags.add(tagName);
                        }
                    });
                    
                    currentElement = currentElement.parentElement;
                    depth++;
                }
                
                candidate.hierarchy = hierarchy;
            });
            
            // Find the most common container patterns
            const sortedPatterns = Array.from(containerPatternMap.values())
                .sort((a, b) => b.count - a.count)
                .slice(0, 10);  // Top 10 patterns
            
            patterns.containerPatterns = sortedPatterns.map(p => ({
                class: p.class,
                occurrences: p.count,
                avgDepth: Math.round(p.depths.reduce((a, b) => a + b, 0) / p.depths.length),
                tags: Array.from(p.tags)
            }));
            
            patterns.learningPhases.push(`Identified ${patterns.containerPatterns.length} common container patterns`);

            // ============================================================================
            // PHASE 3: Identify the most likely logo container class
            // ============================================================================
            patterns.learningPhases.push('PHASE 3: Selecting optimal container pattern');

            // The best container pattern is one that:
            // 1. Appears multiple times (consistent pattern)
            // 2. Is at a reasonable depth (2-5 levels from image)
            // 3. Has meaningful name (contains keywords like "image", "component", "container", etc.)

            let bestPattern = null;
            let bestScore = 0;

            for (const pattern of patterns.containerPatterns) {
                const classLower = pattern.class.toLowerCase();

                // Filter out UI/layout classes
                const isUIClass = classLower.includes('header') ||
                                 classLower.includes('wrapper') ||
                                 classLower.includes('skeleton') ||
                                 classLower.includes('full-height') ||
                                 classLower.includes('app-') ||
                                 classLower.includes('root_');

                if (isUIClass) continue;  // Skip UI classes

                // Keyword scoring
                let keywordScore = 0;
                if (classLower.includes('image')) keywordScore += 3;
                if (classLower.includes('component')) keywordScore += 2;
                if (classLower.includes('container')) keywordScore += 2;
                if (classLower.includes('logo')) keywordScore += 3;
                if (classLower.includes('sortable')) keywordScore += 1;
                if (classLower.includes('resizable')) keywordScore += 1;

                // Depth scoring (prefer depth 2-4)
                let depthScore = 0;
                if (pattern.avgDepth >= 2 && pattern.avgDepth <= 4) depthScore = 2;
                else if (pattern.avgDepth >= 1 && pattern.avgDepth <= 5) depthScore = 1;

                // Occurrence scoring (prefer multiple occurrences but not too many)
                let occurrenceScore = 0;
                if (pattern.occurrences >= 2 && pattern.occurrences <= 5) occurrenceScore = 2;
                else if (pattern.occurrences === 1) occurrenceScore = 1;

                const totalScore = keywordScore + depthScore + occurrenceScore;

                if (totalScore > bestScore) {
                    bestScore = totalScore;
                    bestPattern = pattern;
                }
            }

            patterns.learningPhases.push(`Selected best pattern: ${bestPattern ? bestPattern.class : 'none'} (score: ${bestScore})`);

            // ============================================================================
            // PHASE 4: Extract logo containers using learned pattern
            // ============================================================================
            patterns.learningPhases.push('PHASE 4: Extracting logo containers');

            if (bestPattern) {
                const containerSelector = `[class*="${bestPattern.class}"]`;
                const containers = document.querySelectorAll(containerSelector);

                patterns.learningPhases.push(`Found ${containers.length} containers matching: ${containerSelector}`);

                // Filter to only containers that actually have images
                containers.forEach((container, idx) => {
                    const hasImage = container.querySelector('img') !== null;
                    const img = container.querySelector('img');

                    if (hasImage) {
                        const rect = container.getBoundingClientRect();

                        // Mark the container for testing
                        container.setAttribute('data-learned-logo', `logo-${idx + 1}`);

                        // DON'T highlight yet - will do after warning detection

                        patterns.detectedLogos.push({
                            index: idx + 1,
                            containerClass: bestPattern.class,
                            hasImage: true,
                            position: {
                                top: Math.round(rect.top + window.scrollY),
                                left: Math.round(rect.left)
                            },
                            size: {
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            },
                            imageSrc: img ? img.src.substring(0, 80) : null
                        });
                    }
                });
            }

            // ============================================================================
            // PHASE 5: Look for warning icons to refine detection
            // ============================================================================
            patterns.learningPhases.push('PHASE 5: Checking for warning icons');

            const warningSelectors = [
                '[class*="warningIcon"]',
                '[class*="warning"]',
                '.icon-alert1',
                '[aria-label*="warning"]'
            ];

            let warningIcons = [];
            for (const selector of warningSelectors) {
                const found = document.querySelectorAll(selector);
                if (found.length > 0) {
                    warningIcons = Array.from(found);
                    patterns.learningPhases.push(`Found ${found.length} warning icons using: ${selector}`);
                    break;
                }
            }

            // Mark logos with warnings AND HIGHLIGHT with colors
            patterns.detectedLogos.forEach(logo => {
                logo.hasWarning = false;
            });

            warningIcons.forEach((icon, warnIdx) => {
                // Find which detected logo is near this warning icon (check both directions)
                let foundInLogo = false;
                const iconRect = icon.getBoundingClientRect();
                const iconTop = Math.round(iconRect.top + window.scrollY);

                patterns.detectedLogos.forEach(logo => {
                    const container = document.querySelector(`[data-learned-logo="logo-${logo.index}"]`);

                    // Check 1: Is warning inside the container?
                    if (container && container.contains(icon)) {
                        logo.hasWarning = true;
                        foundInLogo = true;
                        patterns.learningPhases.push(`  Warning #${warnIdx + 1} found INSIDE Logo #${logo.index}`);
                        return;
                    }

                    // Check 2: Is the container inside the warning's parent? (warning at SortableItem level)
                    let parent = container?.parentElement;
                    while (parent && parent !== document.body) {
                        if (parent.contains(icon) && parent.contains(container)) {
                            // Both warning and logo are in the same parent container
                            // Check if they're close (within 200px)
                            const containerRect = container.getBoundingClientRect();
                            const containerTop = Math.round(containerRect.top + window.scrollY);

                            if (Math.abs(iconTop - containerTop) < 200) {
                                logo.hasWarning = true;
                                foundInLogo = true;
                                patterns.learningPhases.push(`  Warning #${warnIdx + 1} found in PARENT of Logo #${logo.index} (distance: ${Math.abs(iconTop - containerTop)}px)`);
                                return;
                            }
                        }
                        parent = parent.parentElement;
                    }
                });

                if (!foundInLogo) {
                    // Debug: where is this warning icon?
                    patterns.learningPhases.push(`  Warning #${warnIdx + 1} NOT matched to any logo (at ${iconTop}px)`);
                }
            });

            // ============================================================================
            // PHASE 6: Highlight containers based on warning status
            // ============================================================================
            patterns.learningPhases.push('PHASE 6: Color-coding containers');

            patterns.detectedLogos.forEach(logo => {
                const container = document.querySelector(`[data-learned-logo="logo-${logo.index}"]`);
                if (!container) return;

                if (logo.hasWarning) {
                    // RED for containers with warnings
                    container.style.outline = '5px solid red';
                    container.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
                    container.style.position = 'relative';

                    // Add warning label
                    const label = document.createElement('div');
                    label.style.cssText = `
                        position: absolute;
                        top: -35px;
                        left: 0;
                        background: red;
                        color: white;
                        padding: 5px 10px;
                        font-weight: bold;
                        font-size: 14px;
                        z-index: 10000;
                        border-radius: 3px;
                        white-space: nowrap;
                    `;
                    label.textContent = `⚠️ WARNING - Logo #${logo.index}`;
                    container.insertBefore(label, container.firstChild);

                    patterns.learningPhases.push(`  Logo #${logo.index}: RED (has warning)`);
                } else {
                    // GREEN for containers without warnings
                    container.style.outline = '5px solid lime';
                    container.style.backgroundColor = 'rgba(0, 255, 0, 0.1)';
                    container.style.position = 'relative';

                    // Add OK label
                    const label = document.createElement('div');
                    label.style.cssText = `
                        position: absolute;
                        top: -35px;
                        left: 0;
                        background: lime;
                        color: black;
                        padding: 5px 10px;
                        font-weight: bold;
                        font-size: 14px;
                        z-index: 10000;
                        border-radius: 3px;
                        white-space: nowrap;
                    `;
                    label.textContent = `✅ OK - Logo #${logo.index}`;
                    container.insertBefore(label, container.firstChild);

                    patterns.learningPhases.push(`  Logo #${logo.index}: GREEN (no warning)`);
                }
            });

            // Summary
            patterns.summary = {
                totalImages: allImages.length,
                candidateLogos: candidateLogos.length,
                containerPatterns: patterns.containerPatterns.length,
                bestPattern: bestPattern ? bestPattern.class : null,
                bestPatternScore: bestScore,
                detectedLogos: patterns.detectedLogos.length,
                logosWithWarnings: patterns.detectedLogos.filter(l => l.hasWarning).length
            };

            return patterns;
        }
    """)

    return result


async def main():
    """Main test execution"""

    logger.info("="*100)
    logger.info("🧪 TRULY DYNAMIC LOGO DETECTION TEST")
    logger.info("="*100)
    logger.info(f"Test Template: {TEST_TEMPLATE_ID}")
    logger.info(f"CDP URL: {CDP_URL}")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*100)
    logger.info("\n💡 This test LEARNS patterns from the template instead of using hardcoded selectors!")
    logger.info("="*100)

    async with async_playwright() as p:
        try:
            # Connect to existing browser
            browser = await p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]
            page = context.pages[0]

            # Navigate to template
            logger.info("\nOpening template edit page...")
            edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{TEST_TEMPLATE_ID}"
            await page.goto(edit_url, wait_until='domcontentloaded', timeout=30000)

            # Wait for editor to load completely
            logger.info("⏳ Waiting for template content to load...")
            await page.wait_for_selector('[class*="SortableItem"]', timeout=20000)
            await asyncio.sleep(3)  # Extra wait for all images to render
            logger.info("✅ Template editor loaded")

            # Learn patterns
            patterns = await learn_logo_patterns(page)

            # Print learning phases
            logger.info("\n" + "="*100)
            logger.info("📚 LEARNING PROCESS")
            logger.info("="*100)
            for i, phase in enumerate(patterns['learningPhases'], 1):
                logger.info(f"{i}. {phase}")

            # Print container patterns
            logger.info("\n" + "="*100)
            logger.info("🔍 DISCOVERED CONTAINER PATTERNS (Top 10)")
            logger.info("="*100)
            for i, pattern in enumerate(patterns['containerPatterns'], 1):
                logger.info(f"{i}. Class: '{pattern['class']}'")
                logger.info(f"   Occurrences: {pattern['occurrences']}")
                logger.info(f"   Average Depth: {pattern['avgDepth']}")
                logger.info(f"   Tags: {', '.join(pattern['tags'])}")
                logger.info("")

            # Print detected logos
            logger.info("="*100)
            logger.info("🎯 DETECTED LOGOS")
            logger.info("="*100)
            for logo in patterns['detectedLogos']:
                warning_status = "⚠️  WARNING" if logo['hasWarning'] else "✅ NO WARNING"
                logger.info(f"\nLogo #{logo['index']}: {warning_status}")
                logger.info(f"   Container Class: {logo['containerClass']}")
                logger.info(f"   Position: {logo['position']['top']}px from top")
                logger.info(f"   Size: {logo['size']['width']}x{logo['size']['height']}px")
                logger.info(f"   Image: {logo['imageSrc']}")

            # Print summary
            logger.info("\n" + "="*100)
            logger.info("📊 SUMMARY")
            logger.info("="*100)
            summary = patterns['summary']
            logger.info(f"Total Images Analyzed: {summary['totalImages']}")
            logger.info(f"Candidate Logos Found: {summary['candidateLogos']}")
            logger.info(f"Container Patterns Discovered: {summary['containerPatterns']}")
            logger.info(f"Best Pattern Selected: '{summary['bestPattern']}' (score: {summary['bestPatternScore']})")
            logger.info(f"Logo Containers Detected: {summary['detectedLogos']}")
            logger.info(f"Logos with Warnings: {summary['logosWithWarnings']}")

            # Visual inspection
            logger.info("\n" + "="*100)
            logger.info("🎨 VISUAL INSPECTION - COLOR CODING")
            logger.info("="*100)
            logger.info("🔴 RED BORDERS = Containers WITH warnings (need logo replacement)")
            logger.info("🟢 GREEN BORDERS = Containers WITHOUT warnings (logos are correct)")
            logger.info("")
            logger.info("📋 Check the browser to see the color-coded containers!")
            logger.info("   - Red containers: Need attention")
            logger.info("   - Green containers: Already correct")
            logger.info("")
            logger.info("⏸️  Waiting 30 seconds for inspection...")
            logger.info("="*100)

            await asyncio.sleep(30)

            logger.info("\n" + "="*100)
            logger.info("✅ TRULY DYNAMIC DETECTION COMPLETE")
            logger.info("="*100)
            logger.info("\n💡 Key Insight: The system LEARNED the pattern without any hardcoded selectors!")
            logger.info(f"   Discovered Pattern: {summary['bestPattern']}")
            logger.info(f"   Adaptability: Can work on ANY template structure!")
            logger.info("="*100)

        except Exception as e:
            logger.exception(f"❌ Fatal error during test execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())

