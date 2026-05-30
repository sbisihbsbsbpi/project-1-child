#!/usr/bin/env python3
"""
Smart Template Analysis - Build Dynamic Logo Detection
Analyzes all open templates to create intelligent detection patterns
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def analyze_all_templates():
    print("=" * 80)
    print("🔍 ANALYZING ALL TEMPLATE STRUCTURES FOR SMART DETECTION")
    print("=" * 80)
    print()
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]
    
    # Find all template edit tabs
    template_pages = []
    for page in context.pages:
        url = page.url
        if 'templates/edit' in url and 'templates/list' not in url:
            title = await page.title()
            template_pages.append({
                'page': page,
                'url': url,
                'title': title
            })
    
    print(f"Found {len(template_pages)} template tabs to analyze")
    print()
    
    all_analysis = []
    
    for idx, template_info in enumerate(template_pages, 1):
        page = template_info['page']
        title = template_info['title']
        
        print(f"[{idx}/{len(template_pages)}] Analyzing: {title[:60]}")
        
        # Deep analysis of the template structure
        analysis = await page.evaluate("""
            () => {
                const result = {
                    templateName: document.title,
                    images: [],
                    imageLocations: {},
                    containerTypes: {},
                    logoPatterns: []
                };
                
                // Analyze all images
                const images = Array.from(document.querySelectorAll('img'));
                
                images.forEach((img, idx) => {
                    const rect = img.getBoundingClientRect();
                    const src = img.src || '';
                    
                    // Skip tiny images (icons, etc.)
                    if (rect.width < 20 || rect.height < 10) return;
                    
                    // Extract media ID from URL
                    const mediaIdMatch = src.match(/([a-f0-9]{24})/);
                    const mediaId = mediaIdMatch ? mediaIdMatch[1] : null;
                    
                    // Analyze container hierarchy
                    let container = img.parentElement;
                    let containerChain = [];
                    let depth = 0;
                    
                    while (container && depth < 10) {
                        const classes = container.className || '';
                        const id = container.id || '';
                        
                        containerChain.push({
                            tag: container.tagName,
                            classes: classes.substring(0, 100),
                            id: id,
                            hasResizable: classes.includes('resizable'),
                            hasImageComponent: classes.includes('imageComponent') || classes.includes('image-component'),
                            hasElementContainer: classes.includes('elementContainer') || classes.includes('element-container')
                        });
                        
                        container = container.parentElement;
                        depth++;
                    }
                    
                    // Determine position in template
                    const viewportHeight = window.innerHeight;
                    const viewportWidth = window.innerWidth;
                    
                    let location = 'middle';
                    if (rect.top < viewportHeight * 0.3) location = 'top';
                    else if (rect.top > viewportHeight * 0.7) location = 'bottom';
                    
                    let horizontalPosition = 'center';
                    if (rect.left < viewportWidth * 0.3) horizontalPosition = 'left';
                    else if (rect.left > viewportWidth * 0.7) horizontalPosition = 'right';
                    
                    const position = location + '-' + horizontalPosition;
                    
                    // Check if it's likely a logo
                    const aspectRatio = rect.width / rect.height;
                    const isLogoSized = (
                        (rect.width > 50 && rect.width < 300) &&
                        (rect.height > 15 && rect.height < 150) &&
                        (aspectRatio > 1.5 && aspectRatio < 8)
                    );
                    
                    // Check for common logo keywords in surrounding text
                    const parent = img.closest('div, td, section');
                    const surroundingText = parent ? (parent.innerText || '').toLowerCase() : '';
                    const hasLogoKeywords = surroundingText.includes('logo') || 
                                           surroundingText.includes('powered by') ||
                                           surroundingText.includes('dealer');
                    
                    const imageInfo = {
                        index: idx,
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        aspectRatio: Math.round(aspectRatio * 100) / 100,
                        position: {
                            top: Math.round(rect.top),
                            left: Math.round(rect.left),
                            location: position
                        },
                        mediaId: mediaId,
                        alt: img.alt || '',
                        containerChain: containerChain,
                        isLogoSized: isLogoSized,
                        hasLogoKeywords: hasLogoKeywords,
                        likelyLogo: isLogoSized && (hasLogoKeywords || position.includes('bottom'))
                    };
                    
                    result.images.push(imageInfo);
                    
                    // Track location patterns
                    if (!result.imageLocations[position]) {
                        result.imageLocations[position] = 0;
                    }
                    result.imageLocations[position]++;
                });
                
                // Identify likely logo patterns
                result.images.forEach(img => {
                    if (img.likelyLogo) {
                        result.logoPatterns.push({
                            mediaId: img.mediaId,
                            size: img.width + 'x' + img.height,
                            location: img.position.location,
                            containerSignature: img.containerChain.map(c => c.classes).join(' > ')
                        });
                    }
                });
                
                return result;
            }
        """)
        
        all_analysis.append({
            'template': title,
            'url': template_info['url'],
            'analysis': analysis
        })

        # Print summary for this template
        print(f"  Total images: {len(analysis['images'])}")

        likely_logos = [img for img in analysis['images'] if img['likelyLogo']]
        if likely_logos:
            print(f"  Likely logos: {len(likely_logos)}")
            for logo in likely_logos:
                print(f"    - {logo['width']}x{logo['height']} at {logo['position']['location']} (Media ID: {logo['mediaId']})")
        else:
            print(f"  Likely logos: 0")

        print()

    # Save detailed analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'template_analysis_{timestamp}.json'
    with open(filename, 'w') as f:
        json.dump(all_analysis, f, indent=2)

    print("=" * 80)
    print("📊 PATTERN ANALYSIS SUMMARY")
    print("=" * 80)
    print()

    # Aggregate patterns
    all_media_ids = {}
    location_patterns = {}
    size_patterns = {}

    for template_data in all_analysis:
        for img in template_data['analysis']['images']:
            if img['likelyLogo']:
                # Track media IDs
                media_id = img['mediaId']
                if media_id:
                    if media_id not in all_media_ids:
                        all_media_ids[media_id] = []
                    all_media_ids[media_id].append(template_data['template'])

                # Track locations
                loc = img['position']['location']
                if loc not in location_patterns:
                    location_patterns[loc] = 0
                location_patterns[loc] += 1

                # Track sizes
                size = f"{img['width']}x{img['height']}"
                if size not in size_patterns:
                    size_patterns[size] = 0
                size_patterns[size] += 1

    print("🔍 COMMON LOGO MEDIA IDs:")
    for media_id, templates in sorted(all_media_ids.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {media_id}: Found in {len(templates)} template(s)")
        for t in templates[:3]:
            print(f"    - {t[:60]}")

    print()
    print("📍 COMMON LOGO LOCATIONS:")
    for loc, count in sorted(location_patterns.items(), key=lambda x: x[1], reverse=True):
        print(f"  {loc}: {count} logo(s)")

    print()
    print("📏 COMMON LOGO SIZES:")
    for size, count in sorted(size_patterns.items(), key=lambda x: x[1], reverse=True):
        print(f"  {size}: {count} logo(s)")

    print()
    print(f"💾 Detailed analysis saved to: {filename}")
    print()

    # Generate smart detection rules
    print("=" * 80)
    print("🧠 GENERATING SMART DETECTION RULES")
    print("=" * 80)
    print()

    detection_rules = {
        'timestamp': timestamp,
        'templates_analyzed': len(all_analysis),
        'media_id_patterns': [],
        'location_patterns': location_patterns,
        'size_patterns': size_patterns,
        'detection_strategies': []
    }

    # Strategy 1: Media ID based detection
    for media_id, templates in all_media_ids.items():
        detection_rules['media_id_patterns'].append({
            'media_id': media_id,
            'frequency': len(templates),
            'templates': templates
        })

    # Strategy 2: Position-based detection
    if location_patterns:
        most_common_location = max(location_patterns.items(), key=lambda x: x[1])
        detection_rules['detection_strategies'].append({
            'type': 'position_based',
            'most_common_location': most_common_location[0],
            'frequency': most_common_location[1],
            'description': f"Logos most commonly found at: {most_common_location[0]}"
        })

    # Strategy 3: Size-based detection
    if size_patterns:
        most_common_size = max(size_patterns.items(), key=lambda x: x[1])
        detection_rules['detection_strategies'].append({
            'type': 'size_based',
            'most_common_size': most_common_size[0],
            'frequency': most_common_size[1],
            'description': f"Logos most commonly sized: {most_common_size[0]}"
        })

    # Save detection rules
    rules_filename = f'smart_detection_rules_{timestamp}.json'
    with open(rules_filename, 'w') as f:
        json.dump(detection_rules, f, indent=2)

    print(f"✅ Smart detection rules saved to: {rules_filename}")
    print()

    # Print recommended detection approach
    print("💡 RECOMMENDED DETECTION APPROACH:")
    print()
    if all_media_ids:
        print("1. PRIMARY: Media ID Based Detection")
        print("   - Most reliable method")
        for media_id, templates in list(all_media_ids.items())[:3]:
            print(f"   - Media ID {media_id}: {len(templates)} occurrences")

    if location_patterns:
        most_common_loc = max(location_patterns.items(), key=lambda x: x[1])
        print()
        print(f"2. SECONDARY: Position Based Detection ({most_common_loc[0]})")
        print(f"   - {most_common_loc[1]} logos found at this position")

    if size_patterns:
        most_common_sz = max(size_patterns.items(), key=lambda x: x[1])
        print()
        print(f"3. TERTIARY: Size Based Detection ({most_common_sz[0]})")
        print(f"   - {most_common_sz[1]} logos with this size")

    print()

    await playwright.stop()

    return all_analysis, detection_rules


if __name__ == "__main__":
    analysis, rules = asyncio.run(analyze_all_templates())
