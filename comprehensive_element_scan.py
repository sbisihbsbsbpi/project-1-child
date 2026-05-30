#!/usr/bin/env python3
"""
Comprehensive Element Scanner
Finds ALL elements in template beyond just logos
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page


def analyze_all_elements(body):
    """
    Analyze ALL elements in template body
    Returns categorized list of all components
    """
    elements = {
        'total_components': 0,
        'by_type': {},
        'images': [],
        'buttons': [],
        'text_blocks': [],
        'layouts': [],
        'separators': [],
        'footers': [],
        'other': []
    }
    
    if not isinstance(body, list):
        return elements
    
    elements['total_components'] = len(body)
    
    for idx, component in enumerate(body):
        comp_key = component.get('key', 'UNKNOWN')
        
        # Count by type
        if comp_key not in elements['by_type']:
            elements['by_type'][comp_key] = 0
        elements['by_type'][comp_key] += 1
        
        # Categorize
        comp_info = {
            'index': idx,
            'key': comp_key,
            'compId': component.get('compId')
        }
        
        if comp_key == 'INSERT_IMAGE':
            props = component.get('componentProps', {})
            media_id = props.get('selectedImage', {}).get('mediaId')
            comp_info['mediaId'] = media_id
            comp_info['width'] = props.get('imageDimensions', {}).get('width', 'auto')
            elements['images'].append(comp_info)
        
        elif comp_key == 'INSERT_BUTTON':
            props = component.get('componentProps', {})
            comp_info['hasMediaId'] = 'mediaId' in json.dumps(props)
            elements['buttons'].append(comp_info)
        
        elif comp_key == 'TEXT_TEMPLATE':
            props = component.get('componentProps', {})
            html = props.get('html', '')
            comp_info['hasContent'] = len(html.strip()) > 0
            comp_info['htmlLength'] = len(html)
            elements['text_blocks'].append(comp_info)
        
        elif comp_key == 'INSERT_LAYOUT':
            props = component.get('componentProps', {})
            columns = props.get('columns', [])
            comp_info['columnCount'] = len(columns)
            comp_info['hasImages'] = False
            
            # Check for images in layout
            for col in columns:
                for item in col.get('list', []):
                    if item.get('key') == 'INSERT_IMAGE':
                        comp_info['hasImages'] = True
                        break
            
            elements['layouts'].append(comp_info)
        
        elif 'SEPARATOR' in comp_key:
            elements['separators'].append(comp_info)
        
        elif 'FOOTER' in comp_key:
            props = component.get('componentProps', {})
            comp_info['footerId'] = props.get('id')
            elements['footers'].append(comp_info)
        
        else:
            elements['other'].append(comp_info)
    
    return elements


async def main():
    template_id = '667f0befd4964026ee7b6ea4'
    
    print("=" * 100)
    print("🔍 COMPREHENSIVE ELEMENT SCAN")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        
        url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        page = await get_or_navigate_to_page(browser, url, wait_for_load=True)
        
        print("✅ Template editor loaded")
        await asyncio.sleep(2)
        
        # Load body JSON
        with open('template_body_full.json', 'r') as f:
            body = json.load(f)
        
        elements = analyze_all_elements(body)
        
        print("=" * 100)
        print("📊 ELEMENT ANALYSIS RESULTS")
        print("=" * 100)
        print()
        
        print(f"Total Components: {elements['total_components']}")
        print()
        
        print("By Type:")
        for comp_type, count in sorted(elements['by_type'].items()):
            print(f"  • {comp_type}: {count}")
        print()
        
        print("=" * 100)
        print("📸 IMAGES (Direct INSERT_IMAGE components)")
        print("=" * 100)
        for img in elements['images']:
            print(f"  {img['index']}. Media ID: {img['mediaId']}")
            print(f"     Width: {img['width']}")
        print()
        
        print("=" * 100)
        print("🔘 BUTTONS")
        print("=" * 100)
        for btn in elements['buttons']:
            print(f"  {btn['index']}. {btn['key']}")
            print(f"     Has media reference: {btn.get('hasMediaId', False)}")
        print()
        
        print("=" * 100)
        print("📝 TEXT BLOCKS")
        print("=" * 100)
        for txt in elements['text_blocks']:
            print(f"  {txt['index']}. Has content: {txt['hasContent']}")
            print(f"     HTML length: {txt['htmlLength']} chars")
        print()
        
        print("=" * 100)
        print("📐 LAYOUTS")
        print("=" * 100)
        for layout in elements['layouts']:
            print(f"  {layout['index']}. Columns: {layout['columnCount']}")
            print(f"     Contains images: {layout['hasImages']}")
        print()
        
        print("=" * 100)
        print("➖ SEPARATORS")
        print("=" * 100)
        for sep in elements['separators']:
            print(f"  {sep['index']}. {sep['key']}")
        print()
        
        print("=" * 100)
        print("👣 FOOTERS")
        print("=" * 100)
        for footer in elements['footers']:
            print(f"  {footer['index']}. {footer['key']}")
            print(f"     Footer ID: {footer.get('footerId')}")
        print()
        
        # Save
        with open('comprehensive_element_scan.json', 'w') as f:
            json.dump(elements, f, indent=2)
        
        print("💾 Saved: comprehensive_element_scan.json")


if __name__ == "__main__":
    asyncio.run(main())
