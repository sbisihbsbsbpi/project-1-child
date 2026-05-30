#!/usr/bin/env python3
"""
Compare DOM architecture of 2 templates to understand logo container structures.

Template 1: Service History Recap PDF (667f0befd4964026ee7b6ea2) - 2 logos
Template 2: CPRA_REQUEST_COMPLETION_DATA_CORRECTION - 1 logo

This analysis reveals the EXACT DOM differentiator between:
- Header containers (single component with multiple logos)
- Separate logo images (individual elements)
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def analyze_template_architecture(page, template_id, template_name):
    """
    Deep DOM analysis to determine logo architecture.
    
    Returns architecture analysis including:
    - All logos detected
    - SortableItem containers for each logo
    - Container relationships (shared vs separate)
    - Header button state
    - Architecture classification
    """
    logger.info(f"\n{'='*100}")
    logger.info(f"🔍 ANALYZING: {template_name}")
    logger.info(f"   Template ID: {template_id}")
    logger.info(f"{'='*100}")
    
    # Navigate to template
    edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    await page.goto(edit_url, wait_until='domcontentloaded', timeout=20000)
    
    # Wait for full load
    logger.info("\n⏳ Waiting 15 seconds for template to fully load...")
    await asyncio.sleep(15)
    logger.info("✅ Template loaded")
    
    # Load ignore list
    with open('logo_ignore_list.json') as f:
        ignore_list = json.load(f)
    
    # Run deep analysis
    logger.info("\n🔍 Running deep DOM analysis...")
    
    result = await page.evaluate("""
        (ignorePatterns) => {
            const analysis = {
                templateName: null,
                logos: [],
                containers: [],
                sharedContainers: false,
                headerButtonState: null,
                architecture: 'UNKNOWN',
                rawData: {}
            };
            
            // Helper to check if element is ignored
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
            
            // Position zones
            const HEADER_THRESHOLD = 600;
            const BODY_THRESHOLD = 1200;
            
            function getLogoZone(rect) {
                if (rect.top < HEADER_THRESHOLD) return 'header';
                else if (rect.top < BODY_THRESHOLD) return 'body';
                else return 'footer';
            }
            
            // 1. CHECK HEADER BUTTON STATE
            const headerBtn = document.querySelector('#HEADER');
            if (headerBtn) {
                const opacity = parseFloat(getComputedStyle(headerBtn).opacity);
                const isGrayed = opacity < 1;
                analysis.headerButtonState = {
                    found: true,
                    opacity: opacity,
                    isGrayed: isGrayed,
                    state: isGrayed ? 'GRAYED' : 'ACTIVE'
                };
            } else {
                analysis.headerButtonState = { found: false };
            }
            
            // 2. DETECT ALL LOGOS AND THEIR CONTAINERS
            const allImgs = document.querySelectorAll('img');
            const containerMap = new Map(); // Track unique containers
            let containerCounter = 0;
            
            for (const img of allImgs) {
                if (isIgnored(img)) continue;
                
                const src = img.src || '';
                const rect = img.getBoundingClientRect();
                
                // Look for S3 dealer logos
                if (src.includes('amazonaws.com') && src.includes('media_')) {
                    const isReasonableSize = rect.width > 50 && rect.width < 500 &&
                                            rect.height > 20 && rect.height < 200;
                    
                    if (isReasonableSize && rect.top < BODY_THRESHOLD) {
                        const zone = getLogoZone(rect);
                        
                        // CRITICAL: Find SortableItem container
                        const sortableItem = img.closest('[class*="SortableItem"]');
                        
                        let containerInfo = null;
                        if (sortableItem) {
                            // Generate unique ID for this container
                            let containerId;
                            if (containerMap.has(sortableItem)) {
                                containerId = containerMap.get(sortableItem);
                            } else {
                                containerCounter++;
                                containerId = `CONTAINER_${containerCounter}`;
                                containerMap.set(sortableItem, containerId);
                            }
                            
                            containerInfo = {
                                id: containerId,
                                className: sortableItem.className || '',
                                tagName: sortableItem.tagName,
                                dataType: sortableItem.getAttribute('data-type') || '',
                                dataComponentKey: sortableItem.getAttribute('data-component-key') || '',
                                dataKey: sortableItem.getAttribute('data-key') || '',
                                id_attribute: sortableItem.id || '',
                                outerHTML: sortableItem.outerHTML.substring(0, 300)
                            };
                        }
                        
                        analysis.logos.push({
                            index: analysis.logos.length + 1,
                            zone: zone,
                            src: src.substring(0, 150),
                            coordinates: {
                                top: Math.round(rect.top),
                                left: Math.round(rect.left),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            },
                            container: containerInfo
                        });
                    }
                }
            }
            
            // 3. ANALYZE CONTAINER RELATIONSHIPS
            const uniqueContainers = new Set();
            analysis.logos.forEach(logo => {
                if (logo.container) {
                    uniqueContainers.add(logo.container.id);
                }
            });
            
            analysis.totalLogos = analysis.logos.length;
            analysis.totalContainers = uniqueContainers.size;
            analysis.sharedContainers = analysis.totalLogos > 1 && uniqueContainers.size === 1;
            
            // 4. CLASSIFY ARCHITECTURE
            if (analysis.totalLogos === 0) {
                analysis.architecture = 'NO_LOGOS';
            } else if (analysis.totalLogos === 1) {
                analysis.architecture = 'SINGLE_IMAGE';
            } else if (analysis.sharedContainers) {
                // Multiple logos in SAME container
                if (analysis.headerButtonState.isGrayed) {
                    analysis.architecture = 'HEADER_CONTAINER';
                } else {
                    analysis.architecture = 'SHARED_CONTAINER_UNKNOWN';
                }
            } else {
                // Multiple logos in DIFFERENT containers
                analysis.architecture = 'SEPARATE_IMAGES';
            }
            
            // 5. COLLECT CONTAINER DETAILS
            analysis.containers = Array.from(containerMap.values()).map(containerId => {
                const logosInContainer = analysis.logos.filter(l => l.container?.id === containerId);
                return {
                    id: containerId,
                    logoCount: logosInContainer.length,
                    logos: logosInContainer.map(l => `Logo #${l.index} (${l.zone})`)
                };
            });
            
            return analysis;
        }
    """, ignore_list['ignore_patterns'])
    
    return result


async def print_analysis(analysis, template_name):
    """Print formatted analysis results"""
    logger.info(f"\n{'='*100}")
    logger.info(f"📊 RESULTS: {template_name}")
    logger.info(f"{'='*100}")
    
    # Header button state
    if analysis['headerButtonState']['found']:
        state = analysis['headerButtonState']['state']
        opacity = analysis['headerButtonState']['opacity']
        emoji = '❌' if state == 'GRAYED' else '✅'
        logger.info(f"\n🔘 #HEADER Button:")
        logger.info(f"   State: {emoji} {state}")
        logger.info(f"   Opacity: {opacity}")
    else:
        logger.info(f"\n🔘 #HEADER Button: ⚠️  NOT FOUND")
    
    # Logo detection
    logger.info(f"\n📷 Logos Detected: {analysis['totalLogos']}")
    
    for logo in analysis['logos']:
        zone_emoji = '🔴' if logo['zone'] == 'header' else '🔵' if logo['zone'] == 'body' else '⚪'
        logger.info(f"\n   Logo #{logo['index']}: {zone_emoji} {logo['zone'].upper()} ZONE")
        logger.info(f"      Position: ({logo['coordinates']['top']}, {logo['coordinates']['left']})")
        logger.info(f"      Size: {logo['coordinates']['width']}×{logo['coordinates']['height']}px")
        logger.info(f"      URL: {logo['src'][:80]}...")
        
        if logo['container']:
            c = logo['container']
            logger.info(f"      📦 Container: {c['id']}")
            logger.info(f"         Tag: <{c['tagName']}>")
            logger.info(f"         Class: {c['className'][:60]}...")
            if c['dataType']:
                logger.info(f"         data-type: {c['dataType']}")
            if c['dataComponentKey']:
                logger.info(f"         data-component-key: {c['dataComponentKey']}")
            if c['dataKey']:
                logger.info(f"         data-key: {c['dataKey']}")
    
    # Container analysis
    logger.info(f"\n📦 Container Analysis:")
    logger.info(f"   Total unique containers: {analysis['totalContainers']}")
    logger.info(f"   Shared containers: {'✅ YES' if analysis['sharedContainers'] else '❌ NO'}")
    
    for container in analysis['containers']:
        logger.info(f"\n   {container['id']}:")
        logger.info(f"      Logos in this container: {container['logoCount']}")
        for logo_desc in container['logos']:
            logger.info(f"         - {logo_desc}")
    
    # Architecture classification
    logger.info(f"\n🏗️  ARCHITECTURE: {analysis['architecture']}")
    
    arch_explanations = {
        'NO_LOGOS': 'Template has no dealer logos',
        'SINGLE_IMAGE': 'Template has 1 logo in 1 container (standard image)',
        'HEADER_CONTAINER': '⭐ Multiple logos in SAME container + grayed button = Tekion HEADER COMPONENT',
        'SEPARATE_IMAGES': 'Multiple logos in DIFFERENT containers (individual images)',
        'SHARED_CONTAINER_UNKNOWN': 'Multiple logos in same container but button is active (unusual)'
    }
    
    explanation = arch_explanations.get(analysis['architecture'], 'Unknown architecture')
    logger.info(f"   {explanation}")


async def compare_architectures(arch1, arch2, name1, name2):
    """Compare two architecture analyses and highlight differences"""
    logger.info(f"\n{'='*100}")
    logger.info(f"🔀 COMPARATIVE ANALYSIS")
    logger.info(f"{'='*100}")
    
    logger.info(f"\n📊 Quick Comparison:")
    logger.info(f"\n{'Metric':<40} {'Template 1':<30} {'Template 2':<30}")
    logger.info(f"{'-'*100}")
    logger.info(f"{'Template Name':<40} {name1[:28]:<30} {name2[:28]:<30}")
    logger.info(f"{'Logo Count':<40} {arch1['totalLogos']:<30} {arch2['totalLogos']:<30}")
    logger.info(f"{'Container Count':<40} {arch1['totalContainers']:<30} {arch2['totalContainers']:<30}")
    logger.info(f"{'Shared Container':<40} {'YES' if arch1['sharedContainers'] else 'NO':<30} {'YES' if arch2['sharedContainers'] else 'NO':<30}")
    
    btn1 = arch1['headerButtonState']['state'] if arch1['headerButtonState']['found'] else 'N/A'
    btn2 = arch2['headerButtonState']['state'] if arch2['headerButtonState']['found'] else 'N/A'
    logger.info(f"{'#HEADER Button':<40} {btn1:<30} {btn2:<30}")
    logger.info(f"{'Architecture':<40} {arch1['architecture']:<30} {arch2['architecture']:<30}")
    
    # Key insights
    logger.info(f"\n🎯 KEY INSIGHTS:")
    
    if arch1['sharedContainers'] and arch1['headerButtonState'].get('isGrayed'):
        logger.info(f"\n   ⭐ Template 1 ({name1}):")
        logger.info(f"      - Has {arch1['totalLogos']} logos in the SAME container")
        logger.info(f"      - #HEADER button is GRAYED")
        logger.info(f"      - This is a TEKION HEADER COMPONENT")
        logger.info(f"      - Removal strategy: Remove ENTIRE header component (one X click)")
        logger.info(f"      - Re-add strategy: Cannot re-add (header already exists)")
    
    if not arch2['sharedContainers'] or arch2['totalLogos'] == 1:
        logger.info(f"\n   ⭐ Template 2 ({name2}):")
        logger.info(f"      - Has {arch2['totalLogos']} logo(s) in {arch2['totalContainers']} container(s)")
        logger.info(f"      - Each logo is a SEPARATE image element")
        logger.info(f"      - Removal strategy: Remove each logo individually")
        logger.info(f"      - Re-add strategy: Can add new header")
    
    logger.info(f"\n🔑 THE DIFFERENTIATOR:")
    logger.info(f"   ✅ Check if multiple logos share the SAME SortableItem container")
    logger.info(f"   ✅ Cross-verify with #HEADER button state (grayed vs active)")
    logger.info(f"   ✅ This determines: Header component vs Separate images")


async def main():
    logger.info("="*100)
    logger.info("🔍 TEMPLATE ARCHITECTURE COMPARISON ANALYSIS")
    logger.info("="*100)
    logger.info("\nThis analysis reveals the EXACT DOM differentiator between:")
    logger.info("  - Header containers (single component with multiple logos)")
    logger.info("  - Separate logo images (individual elements)")
    logger.info("")
    
    # Templates to compare
    template1 = {
        'id': '667f0befd4964026ee7b6ea2',
        'name': 'Service History Recap PDF'
    }
    
    template2 = {
        'id': 'CPRA_REQUEST_COMPLETION_DATA_CORRECTION',
        'name': 'Request Completion: Data Correction'
    }
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        # Find or create tab
        working_tab = None
        for p in context.pages:
            if 'tekioncloud.com/templates' in p.url:
                working_tab = p
                break
        
        if not working_tab:
            working_tab = await context.new_page()
        
        await working_tab.bring_to_front()
        
        # Analyze template 1
        arch1 = await analyze_template_architecture(working_tab, template1['id'], template1['name'])
        await print_analysis(arch1, template1['name'])
        
        # Analyze template 2
        arch2 = await analyze_template_architecture(working_tab, template2['id'], template2['name'])
        await print_analysis(arch2, template2['name'])
        
        # Compare
        await compare_architectures(arch1, arch2, template1['name'], template2['name'])
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'architecture_comparison_{timestamp}.json'
        
        results = {
            'timestamp': timestamp,
            'template1': {
                'id': template1['id'],
                'name': template1['name'],
                'analysis': arch1
            },
            'template2': {
                'id': template2['id'],
                'name': template2['name'],
                'analysis': arch2
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n{'='*100}")
        logger.info(f"💾 Results saved to: {filename}")
        logger.info(f"{'='*100}")


if __name__ == "__main__":
    asyncio.run(main())
