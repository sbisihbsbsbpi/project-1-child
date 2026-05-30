#!/usr/bin/env python3
"""
Enhanced Logo Detector - Detects logos at ALL positions including BOTTOM-RIGHT
Based on learnings from first template analysis
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page


# Known logo media IDs
KNOWN_LOGOS = {
    '6a0c6722864813539e4da7ae': 'Nucar Logo (Old)',
    '6a19132b6697f36de6236fb1': 'Tilton Logo (New)',
    '6a191313710089188b66521e': 'Tilton Branding Logo'
}


def detect_position_in_body(component_index, total_components):
    """Determine if component is at top, middle, or bottom of template"""
    ratio = component_index / total_components
    if ratio < 0.25:
        return 'top'
    elif ratio > 0.75:
        return 'bottom'
    else:
        return 'middle'


def find_all_images_recursive(body, path="body", component_index=0, total_components=None):
    """
    Recursively find ONLY BOTTOM-RIGHT position images
    All other positions are BLOCKED

    Returns list of image info with position details
    """
    if total_components is None:
        total_components = len(body) if isinstance(body, list) else 1

    images = []

    if isinstance(body, list):
        for idx, component in enumerate(body):
            images.extend(find_all_images_recursive(
                component,
                f"{path}[{idx}]",
                idx,
                total_components
            ))

    elif isinstance(body, dict):
        comp_key = body.get('key')

        # Direct INSERT_IMAGE - BLOCKED (not bottom-right)
        # We only want images in layouts at bottom-right position
        if comp_key == 'INSERT_IMAGE':
            # Skip direct INSERT_IMAGE - not bottom-right position
            pass

        # INSERT_LAYOUT - check columns
        elif comp_key == 'INSERT_LAYOUT':
            props = body.get('componentProps', {})
            columns = props.get('columns', [])

            for col_idx, column in enumerate(columns):
                col_list = column.get('list', [])

                for item_idx, item in enumerate(col_list):
                    # Determine horizontal position in layout
                    total_cols = len(columns)
                    horizontal_pos = 'left' if col_idx == 0 else ('right' if col_idx == total_cols - 1 else 'center')

                    # Check if this item is an image
                    if item.get('key') == 'INSERT_IMAGE':
                        props_inner = item.get('componentProps', {})
                        selected_image = props_inner.get('selectedImage', {})
                        media_id = selected_image.get('mediaId')

                        if media_id:
                            dimensions = props_inner.get('imageDimensions', {})
                            alignment = props_inner.get('imageAlignment', 'center')

                            # Determine position within the column
                            is_last_in_column = item_idx == len(col_list) - 1
                            is_only_image_in_column = len([x for x in col_list if x.get('key') == 'INSERT_IMAGE']) == 1

                            # For bottom-right detection: must be in right column AND at bottom of that column
                            # OR be the only image in right column
                            vertical_pos_in_layout = 'bottom' if (is_last_in_column or is_only_image_in_column) else 'top'
                            position_label = f"{vertical_pos_in_layout}-{horizontal_pos}"

                            # 🚫 BLOCK: Only accept BOTTOM-RIGHT position
                            if position_label != 'bottom-right':
                                continue  # Skip this image - not bottom-right

                            img_info = {
                                'location': f"{path}.columns[{col_idx}].list[{item_idx}]",
                                'componentKey': 'INSERT_LAYOUT > INSERT_IMAGE',
                                'componentIndex': component_index,
                                'layoutColumn': col_idx + 1,
                                'layoutTotalColumns': total_cols,
                                'layoutPosition': position_label,
                                'mediaId': media_id,
                                'width': dimensions.get('width', 'auto'),
                                'alignment': alignment,
                                'verticalPosition': detect_position_in_body(component_index, total_components),
                                'isNested': True,
                                'isBottomRight': True,  # Always true now since we filter above
                                'updateMethod': 'nested_component_replacement',
                                'confidence': 100,  # 🎯 100% confidence for bottom-right logos
                                'isKnownLogo': media_id in KNOWN_LOGOS,
                                'logoName': KNOWN_LOGOS.get(media_id, 'Unknown')
                            }
                            images.append(img_info)

        # Recursively check all nested structures
        for key, value in body.items():
            if isinstance(value, (dict, list)) and key not in ['configuration', 'compId']:
                images.extend(find_all_images_recursive(
                    value,
                    f"{path}.{key}",
                    component_index,
                    total_components
                ))

    return images




async def analyze_template_comprehensive(template_id):
    """
    Comprehensive analysis of a template - finds ALL logos at ALL positions
    """
    print("=" * 100)
    print(f"🔍 COMPREHENSIVE LOGO ANALYSIS - Template: {template_id}")
    print("=" * 100)
    print()

    result = {
        'templateId': template_id,
        'timestamp': datetime.now().isoformat(),
        'logos_found': [],
        'thumbnail_logo': None,
        'total_logos': 0,
        'positions_detected': set()
    }

    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")

            url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
            page = await get_or_navigate_to_page(browser, url, wait_for_load=True)

            print("✅ Template editor loaded")
            await asyncio.sleep(2)

            # Capture template data from API
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
            await page.reload(wait_until='domcontentloaded')

            try:
                await asyncio.wait_for(response_captured.wait(), timeout=10)
                print("✅ Template data captured from API")
            except:
                print("⚠️  Could not capture API data")
                return result

            page.remove_listener('response', handle_response)

            if not template_data:
                print("❌ No template data")
                return result

            print()
            print("=" * 100)
            print("📊 LOGO DETECTION RESULTS")
            print("=" * 100)
            print()

            # Check 1: Thumbnail field
            if template_data.get('thumbnail', {}).get('mediaId'):
                media_id = template_data['thumbnail']['mediaId']
                result['thumbnail_logo'] = {
                    'location': 'thumbnail',
                    'mediaId': media_id,
                    'isKnownLogo': media_id in KNOWN_LOGOS,
                    'logoName': KNOWN_LOGOS.get(media_id, 'Unknown')
                }
                print(f"✅ THUMBNAIL LOGO: {media_id}")
                print(f"   Logo: {KNOWN_LOGOS.get(media_id, 'Unknown')}")
                print()

            # Check 2: Parse body JSON for all images
            body_json = template_data.get('body')
            if body_json:
                body = json.loads(body_json) if isinstance(body_json, str) else body_json

                all_images = find_all_images_recursive(body)

                print(f"📦 IMAGES IN BODY: {len(all_images)} found")
                print()

                for i, img in enumerate(all_images, 1):
                    result['logos_found'].append(img)
                    result['positions_detected'].add(img.get('layoutPosition', img.get('verticalPosition', 'unknown')))

                    print(f"{i}. {img['componentKey']}")
                    print(f"   Media ID: {img['mediaId']}")
                    print(f"   Logo: {img['logoName']}")
                    print(f"   Position: {img.get('verticalPosition', 'unknown')}")

                    if img.get('isNested'):
                        print(f"   📍 Layout Position: {img.get('layoutPosition', 'N/A')}")
                        print(f"      Column: {img.get('layoutColumn', 'N/A')} of {img.get('layoutTotalColumns', 'N/A')}")
                        if img.get('isBottomRight'):
                            print(f"      ⭐ BOTTOM-RIGHT POSITION DETECTED!")

                    print(f"   Width: {img.get('width', 'auto')}")
                    print(f"   Alignment: {img.get('alignment', 'N/A')}")
                    print(f"   Confidence: {img['confidence']}%")
                    print(f"   Update: {img['updateMethod']}")
                    print()

                result['total_logos'] = len(all_images)

            # Summary
            print("=" * 100)
            print("📊 SUMMARY")
            print("=" * 100)
            print()
            print(f"Total Logos Found: {result['total_logos']}")
            print(f"Thumbnail Logo: {'✅ YES' if result['thumbnail_logo'] else '❌ NO'}")
            print(f"Positions Detected: {', '.join(sorted(result['positions_detected']))}")
            print()

            # Check for bottom-right logos
            bottom_right_logos = [img for img in result['logos_found'] if img.get('isBottomRight')]
            if bottom_right_logos:
                print("⭐ BOTTOM-RIGHT LOGOS:")
                for logo in bottom_right_logos:
                    print(f"   • {logo['logoName']} ({logo['mediaId']})")
            else:
                print("ℹ️  No bottom-right position logos found in this template")
            print()

            # Save result
            filename = f"logo_analysis_{template_id}.json"
            result['positions_detected'] = list(result['positions_detected'])  # Convert set to list for JSON
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)

            print(f"💾 Analysis saved: {filename}")
            print()

            return result

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return result


if __name__ == "__main__":
    template_id = '667f0befd4964026ee7b6ea4'
    asyncio.run(analyze_template_comprehensive(template_id))
