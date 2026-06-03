#!/usr/bin/env python3
"""
🔍 Dynamic Logo Container Pattern Detection Test
Analyzes sub-container structures to find patterns for logo detection
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


async def analyze_logo_patterns(page):
    """Comprehensive pattern analysis for logo containers"""
    
    logger.info("\n" + "="*100)
    logger.info("🔍 ANALYZING LOGO CONTAINER PATTERNS")
    logger.info("="*100)
    
    result = await page.evaluate("""
        () => {
            const patterns = {
                timestamp: new Date().toISOString(),
                
                // All detection strategies
                strategies: {
                    warningIcons: [],
                    emptyImageComponents: [],
                    allImageComponents: [],
                    positionBased: [],
                    sizeBased: [],
                    s3MediaUrls: [],
                    sortableItems: []
                },
                
                // Sub-container analysis
                subContainerPatterns: [],
                
                // Summary
                summary: {}
            };
            
            // STRATEGY 1: Warning Icon Detection
            const warnings = document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb');
            warnings.forEach((icon, idx) => {
                const sortable = icon.closest('[class*="SortableItem"]');
                const imageComponent = icon.closest('[class*="imageComponent"]');
                const resizable = icon.closest('[class*="resizable"]');
                
                if (sortable) {
                    const rect = sortable.getBoundingClientRect();
                    const img = sortable.querySelector('img');
                    
                    patterns.strategies.warningIcons.push({
                        index: idx + 1,
                        method: 'warning-icon',
                        position: {
                            top: Math.round(rect.top + window.scrollY),
                            left: Math.round(rect.left)
                        },
                        size: {
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        hasImage: img !== null,
                        imageSrc: img ? img.src.substring(0, 100) : null,
                        containers: {
                            sortable: sortable.className.substring(0, 100),
                            imageComponent: imageComponent ? imageComponent.className.substring(0, 100) : null,
                            resizable: resizable ? resizable.className.substring(0, 100) : null
                        },
                        containerId: sortable.id || 'no-id'
                    });
                }
            });
            
            // STRATEGY 2: All imageComponent Containers
            const allImageComponents = document.querySelectorAll('[class*="imageComponent"]');
            allImageComponents.forEach((comp, idx) => {
                const sortable = comp.closest('[class*="SortableItem"]');
                const rect = comp.getBoundingClientRect();
                const img = comp.querySelector('img');
                const hasWarning = comp.querySelector('.templates_Image_warningIcon__hCZHMuhEmb') !== null;
                
                patterns.strategies.allImageComponents.push({
                    index: idx + 1,
                    method: 'imageComponent',
                    position: {
                        top: Math.round(rect.top + window.scrollY),
                        left: Math.round(rect.left)
                    },
                    size: {
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    hasImage: img !== null,
                    hasWarning: hasWarning,
                    isEmpty: img === null,
                    imageSrc: img ? img.src.substring(0, 100) : null,
                    className: comp.className.substring(0, 100),
                    parentId: sortable ? sortable.id : 'no-parent-id'
                });
            });
            
            // STRATEGY 3: Empty imageComponent Containers
            const emptyImageComponents = Array.from(allImageComponents).filter(comp => {
                return comp.querySelector('img') === null;
            });
            
            emptyImageComponents.forEach((comp, idx) => {
                const rect = comp.getBoundingClientRect();
                patterns.strategies.emptyImageComponents.push({
                    index: idx + 1,
                    method: 'empty-imageComponent',
                    position: {
                        top: Math.round(rect.top + window.scrollY),
                        left: Math.round(rect.left)
                    },
                    size: {
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    },
                    className: comp.className.substring(0, 100),
                    innerHTML: comp.innerHTML.substring(0, 150)
                });
            });
            
            // STRATEGY 4: Position-based (all images in header/top/bottom)
            const HEADER_THRESHOLD = 600;
            const allImages = document.querySelectorAll('img');
            
            allImages.forEach((img, idx) => {
                const src = img.src || '';
                const rect = img.getBoundingClientRect();
                
                // Look for S3 media URLs
                if (src.includes('amazonaws.com') && src.includes('media_')) {
                    const isReasonableSize = 
                        rect.width > 50 && rect.width < 500 &&
                        rect.height > 20 && rect.height < 200;
                    
                    if (isReasonableSize) {
                        const sortable = img.closest('[class*="SortableItem"]');
                        const imageComponent = img.closest('[class*="imageComponent"]');
                        
                        patterns.strategies.positionBased.push({
                            index: idx + 1,
                            method: 'position-based',
                            region: rect.top < HEADER_THRESHOLD ? 'header' : 'body',
                            position: {
                                top: Math.round(rect.top + window.scrollY),
                                left: Math.round(rect.left)
                            },
                            size: {
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            },
                            src: src.substring(0, 100),
                            containers: {
                                sortable: sortable ? sortable.className.substring(0, 80) : null,
                                imageComponent: imageComponent ? imageComponent.className.substring(0, 80) : null
                            }
                        });
                    }
                }
            });

            // STRATEGY 5: Size-based Detection (logo-sized images)
            allImages.forEach((img, idx) => {
                const rect = img.getBoundingClientRect();
                const aspectRatio = rect.width / rect.height;

                const isLogoSize = (50 < rect.width && rect.width < 300) &&
                                  (20 < rect.height && rect.height < 150);
                const isLogoAspectRatio = aspectRatio > 1.2 && aspectRatio < 8;
                const isNotSystemIcon = rect.width > 50;

                if (isLogoSize && isLogoAspectRatio && isNotSystemIcon) {
                    const sortable = img.closest('[class*="SortableItem"]');
                    const imageComponent = img.closest('[class*="imageComponent"]');

                    patterns.strategies.sizeBased.push({
                        index: idx + 1,
                        method: 'size-based',
                        position: {
                            top: Math.round(rect.top + window.scrollY),
                            left: Math.round(rect.left)
                        },
                        size: {
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            aspectRatio: Math.round(aspectRatio * 100) / 100
                        },
                        src: img.src.substring(0, 100),
                        containers: {
                            sortable: sortable ? sortable.id || 'no-id' : null,
                            imageComponent: imageComponent !== null
                        }
                    });
                }
            });

            // STRATEGY 6: All SortableItems Analysis
            const allSortables = document.querySelectorAll('[class*="SortableItem"]');
            allSortables.forEach((sortable, idx) => {
                const hasImage = sortable.querySelector('img') !== null;
                const hasWarning = sortable.querySelector('.templates_Image_warningIcon__hCZHMuhEmb') !== null;
                const imageComponent = sortable.querySelector('[class*="imageComponent"]');
                const rect = sortable.getBoundingClientRect();

                // Only include if it has imageComponent (potential logo container)
                if (imageComponent) {
                    const img = sortable.querySelector('img');

                    patterns.strategies.sortableItems.push({
                        index: idx + 1,
                        method: 'sortable-item',
                        hasImage: hasImage,
                        hasWarning: hasWarning,
                        hasImageComponent: true,
                        isEmpty: !hasImage,
                        position: {
                            top: Math.round(rect.top + window.scrollY),
                            left: Math.round(rect.left)
                        },
                        size: {
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        containerId: sortable.id || 'custom-container',
                        imageSrc: img ? img.src.substring(0, 100) : null
                    });
                }
            });

            // SUB-CONTAINER DEEP ANALYSIS
            const logoContainers = new Set();

            // Collect all detected logo containers from all strategies
            [...patterns.strategies.warningIcons,
             ...patterns.strategies.allImageComponents,
             ...patterns.strategies.positionBased,
             ...patterns.strategies.sizeBased,
             ...patterns.strategies.sortableItems
            ].forEach(item => {
                if (item.containerId && item.containerId !== 'no-id' && item.containerId !== 'no-parent-id') {
                    const container = document.getElementById(item.containerId);
                    if (container) logoContainers.add(container);
                }
            });

            // Analyze sub-container structure for each logo container
            logoContainers.forEach((container, idx) => {
                const analysis = {
                    containerIndex: idx + 1,
                    containerId: container.id,
                    subContainers: []
                };

                // Find all nested elements
                const children = container.querySelectorAll('*');
                const subContainerTypes = new Set();

                children.forEach(child => {
                    const classes = child.className || '';

                    // Extract meaningful class patterns
                    if (typeof classes === 'string') {
                        const classNames = classes.split(' ').filter(c => c.length > 0);
                        classNames.forEach(cls => {
                            if (cls.includes('imageComponent') ||
                                cls.includes('resizable') ||
                                cls.includes('Image') ||
                                cls.includes('container') ||
                                cls.includes('wrapper')) {
                                subContainerTypes.add(cls);
                            }
                        });
                    }
                });

                // Get direct children structure
                const directChildren = Array.from(container.children);
                analysis.subContainers = directChildren.map(child => {
                    return {
                        tagName: child.tagName,
                        className: child.className ? child.className.substring(0, 100) : '',
                        hasImageComponent: child.querySelector('[class*="imageComponent"]') !== null,
                        hasImage: child.querySelector('img') !== null,
                        childCount: child.children.length
                    };
                });

                analysis.allSubContainerClasses = Array.from(subContainerTypes);
                analysis.depth = getMaxDepth(container);

                patterns.subContainerPatterns.push(analysis);
            });

            // Helper function to get max depth
            function getMaxDepth(element) {
                let maxDepth = 0;

                function traverse(el, depth) {
                    if (depth > maxDepth) maxDepth = depth;
                    Array.from(el.children).forEach(child => {
                        traverse(child, depth + 1);
                    });
                }

                traverse(element, 0);
                return maxDepth;
            }

            // Summary
            patterns.summary = {
                warningIcons: patterns.strategies.warningIcons.length,
                allImageComponents: patterns.strategies.allImageComponents.length,
                emptyImageComponents: patterns.strategies.emptyImageComponents.length,
                positionBased: patterns.strategies.positionBased.length,
                sizeBased: patterns.strategies.sizeBased.length,
                sortableItems: patterns.strategies.sortableItems.length,
                uniqueContainers: logoContainers.size
            };

            return patterns;
        }
    """)

    return result


async def highlight_detected_containers(page, patterns):
    """Highlight all detected containers with different colors"""

    logger.info("\n" + "="*100)
    logger.info("🎨 HIGHLIGHTING DETECTED CONTAINERS")
    logger.info("="*100)

    await page.evaluate("""
        (patterns) => {
            // Color scheme for different strategies
            const colors = {
                warningIcons: 'red',
                allImageComponents: 'blue',
                emptyImageComponents: 'orange',
                positionBased: 'green',
                sizeBased: 'purple',
                sortableItems: 'pink'
            };

            let highlightCount = 0;

            // Highlight warning icon containers
            patterns.strategies.warningIcons.forEach((item, idx) => {
                const selector = `[data-logo-to-inspect="warning-logo-${idx + 1}"]`;
                const container = document.querySelector(selector);
                if (container) {
                    container.style.border = '5px solid red';
                    container.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';

                    const label = document.createElement('div');
                    label.style.cssText = `
                        position: absolute;
                        top: -30px;
                        left: 0;
                        background: red;
                        color: white;
                        padding: 5px 10px;
                        font-weight: bold;
                        font-size: 12px;
                        z-index: 10000;
                        border-radius: 3px;
                    `;
                    label.textContent = `WARNING #${idx + 1}`;
                    container.style.position = 'relative';
                    container.insertBefore(label, container.firstChild);
                    highlightCount++;
                }
            });

            // Highlight all imageComponents
            const allImageComps = document.querySelectorAll('[class*="imageComponent"]');
            allImageComps.forEach((comp, idx) => {
                const hasWarning = comp.querySelector('.templates_Image_warningIcon__hCZHMuhEmb');
                if (!hasWarning) {  // Don't double-highlight warning containers
                    comp.style.outline = '2px dashed blue';
                    highlightCount++;
                }
            });

            // Highlight empty imageComponents
            patterns.strategies.emptyImageComponents.forEach((item, idx) => {
                const allComps = document.querySelectorAll('[class*="imageComponent"]');
                if (allComps[item.index - 1]) {
                    allComps[item.index - 1].style.border = '3px solid orange';
                    allComps[item.index - 1].style.backgroundColor = 'rgba(255, 165, 0, 0.1)';
                }
            });

            return highlightCount;
        }
    """, patterns)

    logger.info("✅ Containers highlighted in browser")


async def print_analysis_results(patterns):
    """Print comprehensive analysis results"""

    logger.info("\n" + "="*100)
    logger.info("📊 DETECTION STRATEGY RESULTS")
    logger.info("="*100)

    # Strategy 1: Warning Icons
    logger.info(f"\n🔴 STRATEGY 1: Warning Icons ({len(patterns['strategies']['warningIcons'])} found)")
    logger.info("-" * 100)
    for item in patterns['strategies']['warningIcons']:
        logger.info(f"   #{item['index']}: Position {item['position']['top']}px")
        logger.info(f"      Container ID: {item['containerId']}")
        logger.info(f"      Has Image: {item['hasImage']}")
        if item['containers']['imageComponent']:
            logger.info(f"      ✅ imageComponent: {item['containers']['imageComponent'][:50]}...")

    # Strategy 2: All imageComponents
    logger.info(f"\n🔵 STRATEGY 2: All imageComponents ({len(patterns['strategies']['allImageComponents'])} found)")
    logger.info("-" * 100)
    for item in patterns['strategies']['allImageComponents']:
        status = "⚠️  WARNING" if item['hasWarning'] else ("📷 HAS IMAGE" if item['hasImage'] else "🔲 EMPTY")
        logger.info(f"   #{item['index']}: {status} at {item['position']['top']}px")
        logger.info(f"      Parent ID: {item['parentId']}")

    # Strategy 3: Empty imageComponents
    logger.info(f"\n🟠 STRATEGY 3: Empty imageComponents ({len(patterns['strategies']['emptyImageComponents'])} found)")
    logger.info("-" * 100)
    for item in patterns['strategies']['emptyImageComponents']:
        logger.info(f"   #{item['index']}: Position {item['position']['top']}px")
        logger.info(f"      Size: {item['size']['width']}x{item['size']['height']}px")

    # Strategy 4: Position-based
    logger.info(f"\n🟢 STRATEGY 4: Position-based ({len(patterns['strategies']['positionBased'])} found)")
    logger.info("-" * 100)
    for item in patterns['strategies']['positionBased']:
        logger.info(f"   #{item['index']}: Region={item['region']}, Position {item['position']['top']}px")
        logger.info(f"      Size: {item['size']['width']}x{item['size']['height']}px")

    # Strategy 5: Size-based
    logger.info(f"\n🟣 STRATEGY 5: Size-based ({len(patterns['strategies']['sizeBased'])} found)")
    logger.info("-" * 100)
    for item in patterns['strategies']['sizeBased']:
        logger.info(f"   #{item['index']}: {item['size']['width']}x{item['size']['height']}px (AR: {item['size']['aspectRatio']})")
        logger.info(f"      Container ID: {item['containers']['sortable']}")

    # Strategy 6: SortableItems
    logger.info(f"\n🩷 STRATEGY 6: SortableItems with imageComponent ({len(patterns['strategies']['sortableItems'])} found)")
    logger.info("-" * 100)
    for item in patterns['strategies']['sortableItems']:
        status = "⚠️  WARNING" if item['hasWarning'] else ("📷 IMAGE" if item['hasImage'] else "🔲 EMPTY")
        logger.info(f"   #{item['index']}: {status} at {item['position']['top']}px")
        logger.info(f"      Container ID: {item['containerId']}")

    # Sub-container patterns
    logger.info("\n" + "="*100)
    logger.info("🔬 SUB-CONTAINER PATTERN ANALYSIS")
    logger.info("="*100)

    for pattern in patterns['subContainerPatterns']:
        logger.info(f"\n📦 Container #{pattern['containerIndex']}: {pattern['containerId']}")
        logger.info(f"   Max Depth: {pattern['depth']} levels")
        logger.info(f"   Sub-container Classes Found:")
        for cls in pattern['allSubContainerClasses']:
            logger.info(f"      - {cls}")

        logger.info(f"   Direct Children ({len(pattern['subContainers'])}):")
        for i, child in enumerate(pattern['subContainers']):
            logger.info(f"      {i+1}. <{child['tagName']}> - {child['className'][:50] if child['className'] else 'no-class'}")
            logger.info(f"         Has imageComponent: {child['hasImageComponent']}, Has Image: {child['hasImage']}")

    # Summary
    logger.info("\n" + "="*100)
    logger.info("📈 SUMMARY")
    logger.info("="*100)
    summary = patterns['summary']
    logger.info(f"   Warning Icons: {summary['warningIcons']}")
    logger.info(f"   All imageComponents: {summary['allImageComponents']}")
    logger.info(f"   Empty imageComponents: {summary['emptyImageComponents']}")
    logger.info(f"   Position-based: {summary['positionBased']}")
    logger.info(f"   Size-based: {summary['sizeBased']}")
    logger.info(f"   SortableItems: {summary['sortableItems']}")
    logger.info(f"   Unique Containers: {summary['uniqueContainers']}")


async def main():
    """Main test execution"""

    logger.info("="*100)
    logger.info("🧪 DYNAMIC LOGO PATTERN DETECTION TEST")
    logger.info("="*100)
    logger.info(f"Test Template: {TEST_TEMPLATE_ID}")
    logger.info(f"CDP URL: {CDP_URL}")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*100)

    async with async_playwright() as p:
        try:
            # Connect to existing browser
            browser = await p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]
            page = context.pages[0]

            # Navigate to template
            logger.info("Opening template edit page...")
            edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{TEST_TEMPLATE_ID}"
            await page.goto(edit_url, wait_until='domcontentloaded', timeout=30000)

            # Wait for editor to load
            await page.wait_for_selector('[class*="SortableItem"]', timeout=15000)
            logger.info("✅ Template editor loaded")

            # Run pattern analysis
            patterns = await analyze_logo_patterns(page)

            # Highlight containers
            await highlight_detected_containers(page, patterns)

            # Print results
            await print_analysis_results(patterns)

            # Wait for inspection
            logger.info("\n" + "="*100)
            logger.info("⏸️  Waiting 45 seconds for visual inspection...")
            logger.info("   - RED borders = Warning icons")
            logger.info("   - BLUE outlines = imageComponents")
            logger.info("   - ORANGE borders = Empty imageComponents")
            logger.info("="*100)

            await asyncio.sleep(45)

            logger.info("\n" + "="*100)
            logger.info("✅ PATTERN DETECTION COMPLETE")
            logger.info("="*100)

        except Exception as e:
            logger.exception(f"❌ Fatal error during test execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())

