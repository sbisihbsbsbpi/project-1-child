#!/usr/bin/env python3
"""
Deep Analysis of First Template
Uses all detection levels without AI
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page


async def analyze_template_deep():
    """
    Comprehensive analysis of the first template
    """

    # Load template info
    with open('first_template_info.json', 'r') as f:
        template_info = json.load(f)

    print("=" * 100)
    print("🔬 DEEP TEMPLATE ANALYSIS - LEVEL 1, 2, 3 DETECTION")
    print("=" * 100)
    print(f"Template: {template_info['name']}")
    print(f"ID: {template_info['templateId']}")
    print(f"URL: {template_info['edit_url']}")
    print("=" * 100)
    print()

    analysis_result = {
        'template_info': template_info,
        'timestamp': datetime.now().isoformat(),
        'detection_levels': {}
    }

    async with async_playwright() as playwright:
        try:
            # Connect to existing browser
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to CDP")

            # Navigate to template
            page = await get_or_navigate_to_page(
                browser,
                template_info['edit_url'],
                wait_for_load=True
            )

            print("✅ Template editor loaded")
            print()

            # Wait for editor to fully load
            await asyncio.sleep(3)

            # ========================================
            # LEVEL 1: ESSENTIAL DETECTION (JSON API)
            # ========================================
            print("=" * 100)
            print("📊 LEVEL 1: ESSENTIAL DETECTION (API/JSON Parsing)")
            print("=" * 100)
            print()

            level1_result = await detect_level1_api(page, template_info['templateId'])
            analysis_result['detection_levels']['level1'] = level1_result

            print_level1_results(level1_result)

            # ========================================
            # LEVEL 2: IMPORTANT DETECTION (DOM + Heuristics)
            # ========================================
            print()
            print("=" * 100)
            print("🔍 LEVEL 2: IMPORTANT DETECTION (DOM Analysis + Heuristics)")
            print("=" * 100)
            print()

            level2_result = await detect_level2_dom(page)
            analysis_result['detection_levels']['level2'] = level2_result

            print_level2_results(level2_result)

            # ========================================
            # LEVEL 3: NICE TO HAVE (Advanced Patterns)
            # ========================================
            print()
            print("=" * 100)
            print("🎯 LEVEL 3: NICE TO HAVE (Container & Position Analysis)")
            print("=" * 100)
            print()

            level3_result = await detect_level3_advanced(page)
            analysis_result['detection_levels']['level3'] = level3_result

            print_level3_results(level3_result)

            # ========================================
            # LEVEL 4: VISUAL PLACEMENT (Email Preview Analysis)
            # ========================================
            print()
            print("=" * 100)
            print("📧 LEVEL 4: VISUAL PLACEMENT (Email Preview Analysis)")
            print("=" * 100)
            print()

            level4_result = await detect_level4_visual_preview(page, template_info['templateId'])
            analysis_result['detection_levels']['level4_visual_placement'] = level4_result

            print_level4_results(level4_result)

            # ========================================
            # MERGE AND ANALYZE
            # ========================================
            print()
            print("=" * 100)
            print("🧩 MERGED ANALYSIS")
            print("=" * 100)
            print()

            merged = merge_detection_results(level1_result, level2_result, level3_result)
            analysis_result['merged_results'] = merged

            print_merged_results(merged)

            # Save complete analysis
            filename = f"template_analysis_{template_info['templateId']}.json"
            with open(filename, 'w') as f:
                json.dump(analysis_result, f, indent=2, default=str)

            print()
            print("=" * 100)
            print(f"💾 Complete analysis saved to: {filename}")
            print("=" * 100)

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def _detect_thumbnail_visual_placement(template_data):
    """
    Analyze where the thumbnail logo appears visually
    by examining the template body structure
    """
    placement_info = {
        'found_in_preview': False,
        'position': 'unknown',
        'rendering_method': 'unknown',
        'details': []
    }

    # Check body for any thumbnail references
    body_json = template_data.get('body')
    if body_json:
        try:
            if isinstance(body_json, str):
                body = json.loads(body_json)
            else:
                body = body_json

            # Look for footer components (typical placement)
            for idx, component in enumerate(body):
                comp_key = component.get('key', '')
                comp_html = component.get('componentProps', {}).get('html', '')

                # Check if thumbnail is used in footer
                if 'FOOTER' in comp_key.upper():
                    if '{{THUMBNAIL_URL}}' in comp_html or 'thumbnail' in comp_html.lower():
                        placement_info['found_in_preview'] = True
                        placement_info['position'] = 'footer'
                        placement_info['rendering_method'] = 'template_variable'
                        placement_info['details'].append(f'Found in {comp_key} component at index {idx}')

                # Check for any thumbnail references
                if '{{THUMBNAIL_URL}}' in comp_html:
                    placement_info['found_in_preview'] = True
                    placement_info['rendering_method'] = 'template_variable'
                    placement_info['details'].append(f'{{{{THUMBNAIL_URL}}}} used in {comp_key}')

        except Exception as e:
            placement_info['details'].append(f'Error parsing body: {e}')

    # If not found in body, it might be auto-injected by the email rendering system
    if not placement_info['found_in_preview']:
        placement_info['rendering_method'] = 'auto_injected_by_system'
        placement_info['position'] = 'likely_footer'
        placement_info['details'].append('Not found in body HTML - probably auto-injected at email render time')

    return placement_info


async def detect_level1_api(page, template_id):
    """
    Level 1: Essential Detection - API/JSON parsing
    - thumbnail.mediaId
    - INSERT_HEADER components
    - Known media ID matching
    """
    print("Fetching template data from API...")

    result = {
        'thumbnail_logo': None,
        'header_logos': [],
        'image_components': [],
        'known_media_ids_found': [],
        'total_logos': 0
    }

    # Known logo media IDs
    known_logos = {
        '6a0c6722864813539e4da7ae': 'Nucar Logo (Old)',
        '6a19132b6697f36de6236fb1': 'Tilton Logo (New)',
        '6a191313710089188b66521e': 'Tilton Branding Logo'
    }

    # Try to get template data from page evaluation
    template_data_str = await page.evaluate("""
        () => {
            // Try multiple ways to get template data

            // Method 1: Check if data is in window/global
            if (window.templateData) return JSON.stringify(window.templateData);

            // Method 2: Check React state
            const rootDiv = document.querySelector('[data-reactroot]') ||
                           document.querySelector('#root') ||
                           document.querySelector('[id^="app"]');

            if (rootDiv && rootDiv._reactRootContainer) {
                try {
                    const fiber = rootDiv._reactRootContainer._internalRoot.current;
                    // Try to find template data in React fiber
                    return JSON.stringify({found: 'react', data: null});
                } catch (e) {}
            }

            // Method 3: Return null, we'll fetch via API
            return null;
        }
    """)

    # For now, analyze what we can see in the DOM
    # We'll trigger a reload to capture the API call

    template_data = None
    response_captured = asyncio.Event()

    async def handle_response(response):
        nonlocal template_data
        if '/api/templatestore/u/fetch' in response.url:
            try:
                data = await response.json()
                if 'data' in data:
                    template_data = data['data']
                    response_captured.set()
            except:
                pass

    page.on('response', handle_response)

    # Reload page to capture API
    print("   Reloading to capture template API data...")
    await page.reload(wait_until='domcontentloaded')

    # Wait for response
    try:
        await asyncio.wait_for(response_captured.wait(), timeout=10)
        print("   ✅ Template data captured from API")
    except:
        print("   ⚠️  Could not capture API data, using DOM analysis only")

    page.remove_listener('response', handle_response)

    # Analyze template data if we got it
    if template_data:
        # Check 1: Thumbnail
        if template_data.get('thumbnail', {}).get('mediaId'):
            media_id = template_data['thumbnail']['mediaId']

            # NEW: Try to determine visual placement by parsing body
            visual_placement = await _detect_thumbnail_visual_placement(template_data)

            result['thumbnail_logo'] = {
                'location': 'thumbnail',
                'mediaId': media_id,
                'name': template_data['thumbnail'].get('name'),
                'visualPlacement': visual_placement,
                'updateMethod': 'direct_field_replacement',
                'confidence': 100,
                'isKnownLogo': media_id in known_logos,
                'logoName': known_logos.get(media_id, 'Unknown')
            }
            result['total_logos'] += 1

            if media_id in known_logos:
                result['known_media_ids_found'].append(media_id)

        # Check 2: Parse body JSON
        body_json = template_data.get('body')
        if body_json:
            try:
                if isinstance(body_json, str):
                    body = json.loads(body_json)
                else:
                    body = body_json

                for idx, component in enumerate(body):
                    # Check INSERT_HEADER
                    if component.get('key') == 'INSERT_HEADER':
                        html = component.get('componentProps', {}).get('html', '')
                        # Find media URLs
                        import re
                        media_matches = re.findall(r'{{MEDIA_URL_([a-f0-9]{24})}}', html)

                        for media_id in media_matches:
                            result['header_logos'].append({
                                'location': 'body.INSERT_HEADER',
                                'componentIndex': idx,
                                'mediaId': media_id,
                                'updateMethod': 'regex_replace_in_html',
                                'confidence': 95,
                                'isKnownLogo': media_id in known_logos,
                                'logoName': known_logos.get(media_id, 'Unknown')
                            })
                            result['total_logos'] += 1

                            if media_id in known_logos:
                                result['known_media_ids_found'].append(media_id)

                    # Check INSERT_IMAGE
                    elif component.get('key') == 'INSERT_IMAGE':
                        props = component.get('componentProps', {})
                        media_id = props.get('mediaId')

                        if media_id:
                            result['image_components'].append({
                                'location': 'body.INSERT_IMAGE',
                                'componentIndex': idx,
                                'mediaId': media_id,
                                'fileName': props.get('fileName'),
                                'width': props.get('width'),
                                'height': props.get('height'),
                                'updateMethod': 'component_field_replacement',
                                'confidence': 80,
                                'isKnownLogo': media_id in known_logos,
                                'logoName': known_logos.get(media_id, 'Unknown')
                            })

                            if media_id in known_logos:
                                result['total_logos'] += 1
                                result['known_media_ids_found'].append(media_id)

            except Exception as e:
                print(f"   ⚠️  Error parsing body JSON: {e}")

    result['api_data_available'] = template_data is not None
    result['known_media_ids_found'] = list(set(result['known_media_ids_found']))

    return result



async def detect_level2_dom(page):
    """
    Level 2: Important Detection - DOM + Heuristics
    - File name analysis
    - Alt text keywords
    - Size/aspect ratio heuristics
    """
    print("Analyzing DOM for images with logo characteristics...")

    images_data = await page.evaluate("""
        () => {
            const images = Array.from(document.querySelectorAll('img'));

            return images.map((img, idx) => {
                const rect = img.getBoundingClientRect();
                const src = img.src || '';
                const alt = img.alt || '';

                // Extract media ID
                const mediaIdMatch = src.match(/([a-f0-9]{24})/);
                const mediaId = mediaIdMatch ? mediaIdMatch[1] : null;

                // Get file name from src
                const urlParts = src.split('/');
                const fileName = urlParts[urlParts.length - 1];

                return {
                    index: idx,
                    mediaId: mediaId,
                    src: src,
                    alt: alt,
                    fileName: fileName,
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    visible: rect.width > 0 && rect.height > 0
                };
            }).filter(img => {
                // Must be visible and reasonable size
                if (!img.visible || img.width < 20 || img.height < 10) return false;

                // BLOCK: UI icons and embedded SVGs
                const altLower = img.alt.toLowerCase();
                const isUIIcon =
                    img.src.startsWith('data:image/svg') ||  // Inline SVG
                    (img.width < 40 && img.height < 40) ||   // Too small (icon sized)
                    altLower.includes('icon') ||
                    altLower.includes('guide') ||
                    altLower.includes('help') ||
                    altLower.includes('menu') ||
                    altLower.includes('button');

                return !isUIIcon;  // Only return if NOT a UI icon
            });
        }
    """)

    result = {
        'total_images': len(images_data),
        'all_images_raw': images_data,  # Save ALL images with src URLs
        'logo_candidates': [],
        'detection_signals': []
    }

    known_logos = ['6a0c6722864813539e4da7ae', '6a19132b6697f36de6236fb1', '6a191313710089188b66521e']

    # Track different URL patterns we encounter
    url_patterns = {
        'has_24_char_hex': 0,
        'cdn_url': 0,
        'data_url': 0,
        'relative_url': 0,
        'other': 0
    }

    for img in images_data:
        confidence = 0
        reasons = []

        # Analyze URL pattern
        src = img.get('src', '')
        if src.startswith('data:'):
            url_patterns['data_url'] += 1
        elif img['mediaId']:
            url_patterns['has_24_char_hex'] += 1
        elif src.startswith('http'):
            url_patterns['cdn_url'] += 1
        elif src.startswith('/'):
            url_patterns['relative_url'] += 1
        else:
            url_patterns['other'] += 1

        # Signal 1: Known media ID (+40 points)
        if img['mediaId'] and img['mediaId'] in known_logos:
            confidence += 40
            reasons.append('known_media_id')

        # Signal 2: File name contains "logo" (+30 points)
        file_name_lower = img['fileName'].lower()
        if 'logo' in file_name_lower or 'brand' in file_name_lower:
            confidence += 30
            reasons.append('filename_logo_keyword')

        # Signal 3: Alt text contains logo keywords (+20 points)
        alt_lower = img['alt'].lower()
        if 'logo' in alt_lower or 'dealership' in alt_lower or 'brand' in alt_lower:
            confidence += 20
            reasons.append('alt_text_logo_keyword')

        # Signal 4: Typical logo size (+20 points)
        # UI icons already blocked at extraction level
        is_logo_sized = (60 < img['width'] < 300) and (20 < img['height'] < 150)
        if is_logo_sized:
            confidence += 20
            reasons.append('typical_logo_size')

        # Signal 5: Logo aspect ratio (+15 points)
        aspect_ratio = img['width'] / img['height'] if img['height'] > 0 else 0
        if 1.5 < aspect_ratio < 8:
            confidence += 15
            reasons.append('logo_aspect_ratio')

        # Add to candidates if confidence >= 50
        if confidence >= 50:
            result['logo_candidates'].append({
                **img,
                'confidence': confidence,
                'reasons': reasons,
                'aspectRatio': round(aspect_ratio, 2)
            })

        # Track detection signals for analysis
        if reasons:
            result['detection_signals'].append({
                'image_index': img['index'],
                'signals': reasons,
                'confidence': confidence
            })

    result['url_patterns'] = url_patterns
    return result


async def detect_level3_advanced(page):
    """
    Level 3: Nice to Have - Advanced pattern detection
    - Container class analysis
    - Position-based detection
    - DOM hierarchy patterns
    """
    print("Analyzing container patterns and positions...")

    advanced_data = await page.evaluate("""
        () => {
            const images = Array.from(document.querySelectorAll('img'));
            const viewportHeight = window.innerHeight;
            const viewportWidth = window.innerWidth;

            return images.map((img, idx) => {
                const rect = img.getBoundingClientRect();
                const src = img.src || '';
                const alt = img.alt || '';

                // Skip invisible or tiny
                if (rect.width < 20 || rect.height < 10) return null;

                // BLOCK: UI icons and embedded SVGs
                const altLower = alt.toLowerCase();
                const isUIIcon =
                    src.startsWith('data:image/svg') ||
                    (rect.width < 40 && rect.height < 40) ||
                    altLower.includes('icon') ||
                    altLower.includes('guide') ||
                    altLower.includes('help') ||
                    altLower.includes('menu') ||
                    altLower.includes('button');

                if (isUIIcon) return null;

                // Extract media ID
                const mediaIdMatch = src.match(/([a-f0-9]{24})/);
                const mediaId = mediaIdMatch ? mediaIdMatch[1] : null;

                // Get container classes (up to 5 levels)
                let container = img.parentElement;
                let containerClasses = [];
                let containerIds = [];
                let depth = 0;

                while (container && depth < 5) {
                    if (container.className) {
                        containerClasses.push(container.className);
                    }
                    if (container.id) {
                        containerIds.push(container.id);
                    }
                    container = container.parentElement;
                    depth++;
                }

                // Position analysis
                const verticalPos = rect.top < viewportHeight * 0.3 ? 'top' :
                                   rect.top > viewportHeight * 0.7 ? 'bottom' : 'middle';
                const horizontalPos = rect.left < viewportWidth * 0.3 ? 'left' :
                                     rect.left > viewportWidth * 0.7 ? 'right' : 'center';

                return {
                    index: idx,
                    src: src,
                    mediaId: mediaId,
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        vertical: verticalPos,
                        horizontal: horizontalPos,
                        location: verticalPos + '-' + horizontalPos
                    },
                    containerClasses: containerClasses,
                    containerIds: containerIds
                };
            }).filter(img => img !== null);
        }
    """)

    result = {
        'all_images_raw': advanced_data,  # Save ALL images with full data
        'position_based': [],
        'container_based': [],
        'combined_signals': []
    }

    logo_container_keywords = ['logo', 'footer', 'branding', 'powered', 'dealer', 'header']
    logo_positions = ['bottom-right', 'bottom-center', 'bottom-left', 'top-center', 'top-left', 'top-right']

    for img in advanced_data:
        confidence = 0
        reasons = []

        # Signal 1: Position (+15 points)
        if img['position']['location'] in logo_positions:
            confidence += 15
            reasons.append(f"position_{img['position']['location']}")

        # Signal 2: Container classes (+15 points)
        container_classes_str = ' '.join(img['containerClasses']).lower()
        has_logo_container = any(keyword in container_classes_str for keyword in logo_container_keywords)

        if has_logo_container:
            confidence += 15
            reasons.append('logo_container_class')

        # Signal 3: Size check (already done in Level 2, but count here for completeness)
        is_reasonable_size = (50 < img['width'] < 300) and (15 < img['height'] < 150)
        if is_reasonable_size:
            confidence += 10
            reasons.append('reasonable_size')

        if confidence > 0:
            result['combined_signals'].append({
                'image_index': img['index'],
                'mediaId': img['mediaId'],
                'position': img['position']['location'],
                'confidence': confidence,
                'reasons': reasons
            })

    return result



async def detect_level4_visual_preview(page, template_id):
    """
    Level 4: Visual Placement - Check email preview to see WHERE logo appears
    """
    print("Checking email preview/rendered output for logo placement...")

    result = {
        'preview_available': False,
        'logos_in_preview': [],
        'iframe_found': False,
        'page_elements': {}
    }

    # First, scan the page for editor elements
    try:
        page_scan = await page.evaluate("""
            () => {
                return {
                    all_iframes: Array.from(document.querySelectorAll('iframe')).map(f => ({
                        id: f.id,
                        title: f.title,
                        src: f.src ? f.src.substring(0, 100) : '',
                        className: f.className
                    })),
                    buttons: Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()).slice(0, 20),
                    has_editor: !!document.querySelector('[contenteditable="true"]'),
                    editor_classes: Array.from(document.querySelectorAll('[class*="editor"]')).map(e => e.className).slice(0, 5)
                };
            }
        """)
        result['page_elements'] = page_scan
        print(f"   📊 Page scan: {len(page_scan.get('all_iframes', []))} iframes, {len(page_scan.get('buttons', []))} buttons")
    except Exception as e:
        print(f"   ⚠️  Error scanning page: {e}")

    try:
        # First, try to click Preview/Test button if it exists
        preview_button_selectors = [
            'button:has-text("Preview")',
            'button:has-text("Test")',
            '[aria-label*="Preview"]',
            '[data-testid*="preview"]'
        ]

        preview_clicked = False
        for selector in preview_button_selectors:
            try:
                preview_btn = await page.wait_for_selector(selector, timeout=1000)
                if preview_btn:
                    print(f"   📋 Found preview button: {selector}")
                    await preview_btn.click()
                    preview_clicked = True
                    await asyncio.sleep(3)  # Wait longer for modal/preview to load

                    # Check what appeared after clicking
                    post_click_scan = await page.evaluate("""
                        () => {
                            return {
                                iframes: Array.from(document.querySelectorAll('iframe')).length,
                                modals: Array.from(document.querySelectorAll('[role="dialog"], .modal, [class*="modal"]')).length,
                                new_windows: window.frames.length
                            };
                        }
                    """)
                    print(f"      After click: {post_click_scan['iframes']} iframes, {post_click_scan['modals']} modals")
                    break
            except:
                continue

        # Look for preview content in modals or main page
        # First check for modals/dialogs
        modal_selectors = [
            '[role="dialog"]',
            '.modal[style*="display: block"]',
            '[class*="Modal"][class*="visible"]',
            '[class*="modal"][class*="show"]'
        ]

        preview_container = None
        for selector in modal_selectors:
            try:
                modal = await page.wait_for_selector(selector, timeout=1000)
                if modal:
                    print(f"   ✅ Found modal: {selector}")
                    preview_container = modal
                    break
            except:
                continue

        # Look for preview iframe inside modal or in page
        # Common iframe selectors in email builders
        iframe_selectors = [
            'iframe[title*="preview"]',
            'iframe[title*="Preview"]',
            'iframe#preview',
            'iframe.preview',
            'iframe[src*="preview"]',
            '[role="dialog"] iframe',  # iframe inside modal
            'iframe'  # Try any iframe as last resort
        ]

        iframe = None
        for selector in iframe_selectors:
            try:
                iframe = await page.wait_for_selector(selector, timeout=2000)
                if iframe:
                    result['iframe_found'] = True
                    print(f"   ✅ Found preview iframe: {selector}")
                    break
            except:
                continue

        if iframe:
            # Get the iframe content
            frame = await iframe.content_frame()
            if frame:
                result['preview_available'] = True

                # Analyze all images in the preview
                preview_images = await frame.evaluate("""
                    () => {
                        const images = Array.from(document.querySelectorAll('img'));
                        const viewportHeight = document.documentElement.scrollHeight;

                        return images.map((img, idx) => {
                            const rect = img.getBoundingClientRect();
                            const src = img.src || '';
                            const alt = img.alt || '';

                            // Extract media ID
                            const mediaIdMatch = src.match(/([a-f0-9]{24})/);
                            const mediaId = mediaIdMatch ? mediaIdMatch[1] : null;

                            // Determine position
                            const distanceFromTop = rect.top;
                            const distanceFromBottom = viewportHeight - rect.bottom;

                            let position = 'middle';
                            if (distanceFromTop < 200) position = 'header/top';
                            else if (distanceFromBottom < 200) position = 'footer/bottom';

                            return {
                                index: idx,
                                mediaId: mediaId,
                                src: src.substring(0, 100),
                                alt: alt,
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                top: Math.round(rect.top),
                                bottom: Math.round(rect.bottom),
                                position: position,
                                distanceFromTop: Math.round(distanceFromTop),
                                distanceFromBottom: Math.round(distanceFromBottom)
                            };
                        }).filter(img => img.width > 40 && img.height > 15);
                    }
                """)

                result['logos_in_preview'] = preview_images
        else:
            # No iframe, but maybe there's HTML preview directly in the modal
            print("   ⚠️  No preview iframe found, checking for direct HTML preview...")

            if preview_container:
                # Look for images in the modal itself
                modal_images = await page.evaluate("""
                    (selector) => {
                        const modal = document.querySelector(selector);
                        if (!modal) return [];

                        const images = Array.from(modal.querySelectorAll('img'));
                        return images.map((img, idx) => {
                            const rect = img.getBoundingClientRect();
                            const src = img.src || '';
                            const alt = img.alt || '';
                            const mediaIdMatch = src.match(/([a-f0-9]{24})/);
                            const mediaId = mediaIdMatch ? mediaIdMatch[1] : null;

                            return {
                                index: idx,
                                mediaId: mediaId,
                                src: src.substring(0, 100),
                                alt: alt,
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                position: 'in_modal'
                            };
                        }).filter(img => img.width > 40 && img.height > 15);
                    }
                """, modal_selectors[0] if preview_container else '[role="dialog"]')

                if modal_images:
                    result['preview_available'] = True
                    result['logos_in_preview'] = modal_images
                    print(f"   ✅ Found {len(modal_images)} images in modal HTML")

            if not result['preview_available']:
                print("   ⚠️  No preview content found")

    except Exception as e:
        print(f"   ⚠️  Error analyzing preview: {e}")
        result['error'] = str(e)

    return result


def merge_detection_results(level1, level2, level3):
    """Merge all detection levels and create final logo list"""

    merged_logos = {}

    # Add Level 1 results (highest confidence)
    if level1.get('thumbnail_logo'):
        logo = level1['thumbnail_logo']
        merged_logos['thumbnail'] = {
            **logo,
            'detection_levels': ['level1_api'],
            'final_confidence': logo['confidence']
        }

    for logo in level1.get('header_logos', []):
        key = f"header_{logo['mediaId']}"
        merged_logos[key] = {
            **logo,
            'detection_levels': ['level1_api'],
            'final_confidence': logo['confidence']
        }

    # Add Level 2 results and boost confidence if already detected
    for candidate in level2.get('logo_candidates', []):
        media_id = candidate.get('mediaId')
        if media_id:
            # Check if already detected in Level 1
            existing = None
            for key, logo in merged_logos.items():
                if logo.get('mediaId') == media_id:
                    existing = key
                    break

            if existing:
                # Boost confidence
                merged_logos[existing]['detection_levels'].append('level2_dom')
                merged_logos[existing]['final_confidence'] = min(
                    merged_logos[existing]['final_confidence'] + 20,
                    100
                )
                merged_logos[existing]['level2_signals'] = candidate['reasons']
            else:
                # New detection
                merged_logos[f"dom_{media_id}"] = {
                    'location': 'dom_image',
                    'mediaId': media_id,
                    'detection_levels': ['level2_dom'],
                    'final_confidence': candidate['confidence'],
                    'level2_signals': candidate['reasons'],
                    'updateMethod': 'ui_automation'
                }

    # Add Level 3 signals
    for signal in level3.get('combined_signals', []):
        media_id = signal.get('mediaId')
        if media_id:
            # Find in existing
            for key, logo in merged_logos.items():
                if logo.get('mediaId') == media_id:
                    if 'level3' not in logo['detection_levels']:
                        logo['detection_levels'].append('level3_advanced')
                        logo['final_confidence'] = min(logo['final_confidence'] + 10, 100)
                    logo['level3_signals'] = signal['reasons']

    return {
        'total_unique_logos': len(merged_logos),
        'logos': merged_logos,
        'highest_confidence': max([l['final_confidence'] for l in merged_logos.values()]) if merged_logos else 0
    }


def print_level1_results(result):
    """Print Level 1 detection results"""
    print(f"API Data Available: {'✅ YES' if result['api_data_available'] else '❌ NO'}")
    print(f"Total Logos Found: {result['total_logos']}")
    print()

    if result['thumbnail_logo']:
        logo = result['thumbnail_logo']
        print(f"✅ THUMBNAIL LOGO:")
        print(f"   Media ID: {logo['mediaId']}")
        print(f"   Name: {logo['name']}")
        print(f"   Logo: {logo['logoName']}")
        print(f"   Confidence: {logo['confidence']}%")
        print(f"   Update Method: {logo['updateMethod']}")

        # Print visual placement info
        if 'visualPlacement' in logo:
            vp = logo['visualPlacement']
            print(f"   📍 Visual Placement:")
            print(f"      Position: {vp.get('position', 'unknown')}")
            print(f"      Rendering: {vp.get('rendering_method', 'unknown')}")
            if vp.get('details'):
                for detail in vp['details']:
                    print(f"      • {detail}")
        print()

    if result['header_logos']:
        print(f"✅ HEADER LOGOS ({len(result['header_logos'])}):")
        for i, logo in enumerate(result['header_logos'], 1):
            print(f"   {i}. Media ID: {logo['mediaId']}")
            print(f"      Logo: {logo['logoName']}")
            print(f"      Confidence: {logo['confidence']}%")
        print()

    if result['image_components']:
        print(f"📦 IMAGE COMPONENTS ({len(result['image_components'])}):")
        for i, img in enumerate(result['image_components'], 1):
            print(f"   {i}. Media ID: {img['mediaId']}")
            print(f"      File: {img['fileName']}")
            print(f"      Size: {img['width']}x{img['height']}")
            print(f"      Logo: {img['logoName']}")
        print()

    if result['known_media_ids_found']:
        print(f"🎯 Known Logos Detected: {', '.join(result['known_media_ids_found'])}")


def print_level2_results(result):
    """Print Level 2 detection results"""
    print(f"Total Images Found: {result['total_images']}")
    print(f"Logo Candidates (≥50% confidence): {len(result['logo_candidates'])}")
    print()

    # Print URL pattern analysis
    if result.get('url_patterns'):
        print("📊 URL Pattern Analysis:")
        for pattern, count in result['url_patterns'].items():
            if count > 0:
                print(f"   • {pattern}: {count}")
        print()

    # Print ALL images found (raw data)
    if result.get('all_images_raw'):
        print("=" * 80)
        print("🔍 ALL IMAGES IN DOM (Raw Data):")
        print("=" * 80)
        for i, img in enumerate(result['all_images_raw'], 1):
            print(f"\n   Image #{i} (index {img['index']}):")
            print(f"      📸 SRC: {img['src'][:100]}..." if len(img['src']) > 100 else f"      📸 SRC: {img['src']}")
            print(f"      🏷️  Alt: {img['alt'] or '(empty)'}")
            print(f"      📁 Filename: {img['fileName']}")
            print(f"      🆔 Media ID: {img['mediaId'] or '❌ NOT FOUND'}")
            print(f"      📏 Size: {img['width']}x{img['height']}")
        print()
        print("=" * 80)
        print()

    if result['logo_candidates']:
        print("Logo Candidates:")
        for i, candidate in enumerate(result['logo_candidates'], 1):
            print(f"\n   {i}. Image #{candidate['index']}")
            print(f"      Media ID: {candidate['mediaId']}")
            print(f"      Size: {candidate['width']}x{candidate['height']}")
            print(f"      Aspect Ratio: {candidate['aspectRatio']}")
            print(f"      Confidence: {candidate['confidence']}%")
            print(f"      Signals: {', '.join(candidate['reasons'])}")


def print_level3_results(result):
    """Print Level 3 detection results"""
    print(f"Images with Advanced Signals: {len(result['combined_signals'])}")
    print()

    if result['combined_signals']:
        print("Advanced Detection Signals:")
        for i, signal in enumerate(result['combined_signals'], 1):
            print(f"\n   {i}. Image #{signal['image_index']}")
            print(f"      Media ID: {signal['mediaId']}")
            print(f"      Position: {signal['position']}")
            print(f"      Confidence: {signal['confidence']}%")
            print(f"      Signals: {', '.join(signal['reasons'])}")


def print_level4_results(result):
    """Print Level 4 visual placement results"""
    print(f"Preview Available: {'✅ YES' if result['preview_available'] else '❌ NO'}")
    print(f"Preview Iframe Found: {'✅ YES' if result['iframe_found'] else '❌ NO'}")
    print()

    if result.get('logos_in_preview'):
        print(f"Images Found in Email Preview: {len(result['logos_in_preview'])}")
        print()
        for i, img in enumerate(result['logos_in_preview'], 1):
            print(f"   {i}. 📍 {img['position'].upper()}")
            print(f"      Media ID: {img['mediaId'] or '❌ NOT FOUND'}")
            print(f"      Size: {img['width']}x{img['height']}")
            print(f"      Distance from top: {img['distanceFromTop']}px")
            print(f"      Distance from bottom: {img['distanceFromBottom']}px")
            print(f"      Alt: {img['alt'] or '(empty)'}")
            print()


def print_merged_results(merged):
    """Print merged detection results"""
    print(f"Total Unique Logos: {merged['total_unique_logos']}")
    print(f"Highest Confidence: {merged['highest_confidence']}%")
    print()

    if merged['logos']:
        print("FINAL LOGO DETECTIONS:")
        print()
        for key, logo in merged['logos'].items():
            print(f"   🎯 {key.upper()}")
            print(f"      Media ID: {logo.get('mediaId', 'N/A')}")
            print(f"      Location: {logo.get('location')}")
            print(f"      Final Confidence: {logo.get('final_confidence')}%")
            print(f"      Detected By: {', '.join(logo.get('detection_levels', []))}")
            print(f"      Update Method: {logo.get('updateMethod')}")
            if 'level2_signals' in logo:
                print(f"      Level 2 Signals: {', '.join(logo['level2_signals'])}")
            if 'level3_signals' in logo:
                print(f"      Level 3 Signals: {', '.join(logo['level3_signals'])}")
            print()


if __name__ == "__main__":
    asyncio.run(analyze_template_deep())

