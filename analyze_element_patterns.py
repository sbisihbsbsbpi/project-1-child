#!/usr/bin/env python3
"""
Analyze Element Patterns - Extract learning data and compare with user specifications
"""

import asyncio
import sys
import os
import json
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page


async def main():
    template_id = '667f0befd4964026ee7b6ea4'
    
    print("=" * 100)
    print("🔍 ANALYZING ELEMENT PATTERNS & LEARNING DATA")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        
        url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        page = await get_or_navigate_to_page(browser, url, wait_for_load=True)
        
        print("✅ Template editor loaded")
        await asyncio.sleep(2)
        
        # Get learning data
        result = await page.evaluate("""
            () => {
                if (!window.allElementsIncludingBlocked) {
                    return { error: 'Navigator not loaded yet' };
                }
                
                return {
                    totalScanned: window.allElementsIncludingBlocked.length,
                    totalShown: window.navElements.length,
                    totalBlocked: window.allElementsIncludingBlocked.filter(e => e.blocked).length,
                    elements: window.allElementsIncludingBlocked.map(e => ({
                        index: e.originalIndex,
                        type: e.type,
                        width: Math.round(e.rect.width),
                        height: Math.round(e.rect.height),
                        blocked: e.blocked,
                        blockReason: e.blockReason,
                        position: {
                            top: Math.round(e.rect.top),
                            left: Math.round(e.rect.left)
                        }
                    })),
                    blockReasons: window.blockReasons
                };
            }
        """)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            print("Wait a few seconds for navigator to load, then run again.")
            return
        
        print(f"Total elements scanned: {result['totalScanned']}")
        print(f"Elements shown (not blocked): {result['totalShown']}")
        print(f"Elements blocked: {result['totalBlocked']}")
        print()
        
        print("=" * 100)
        print("📋 ALL ELEMENTS (Showing Blocked Status)")
        print("=" * 100)
        print()
        
        # User specified blocks
        user_ignore = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 19]
        user_keep = [10, 18, 20]
        
        for el in result['elements']:
            idx = el['index']
            status = "🚫 BLOCKED" if el['blocked'] else "✅ SHOWN"
            
            # Check against user specifications
            user_spec = ""
            if idx in user_ignore:
                user_spec = " [USER: IGNORE]"
            elif idx in user_keep:
                if idx == 20:
                    user_spec = " [USER: BOTTOM-RIGHT LOGO ⭐]"
                else:
                    user_spec = " [USER: KEEP]"
            
            print(f"Element #{idx}: {el['type']} - {status}{user_spec}")
            print(f"  Size: {el['width']}x{el['height']}px")
            if el['blocked']:
                print(f"  Reason: {el['blockReason']}")
            print()
        
        print("=" * 100)
        print("🎯 PATTERN ANALYSIS")
        print("=" * 100)
        print()
        
        # Analyze patterns of blocked vs user-specified
        auto_blocked = [e['index'] for e in result['elements'] if e['blocked']]
        correctly_blocked = [i for i in auto_blocked if i in user_ignore]
        incorrectly_blocked = [i for i in auto_blocked if i not in user_ignore]
        missed_blocks = [i for i in user_ignore if i not in auto_blocked]
        
        print(f"✅ Correctly auto-blocked: {len(correctly_blocked)}/{len(user_ignore)}")
        if correctly_blocked:
            print(f"   Elements: {correctly_blocked}")
        print()
        
        print(f"❌ Incorrectly blocked (should keep): {len(incorrectly_blocked)}")
        if incorrectly_blocked:
            print(f"   Elements: {incorrectly_blocked}")
            for idx in incorrectly_blocked:
                el = next((e for e in result['elements'] if e['index'] == idx), None)
                if el:
                    print(f"   - #{idx}: {el['type']} (reason: {el['blockReason']})")
        print()
        
        print(f"⚠️  Missed blocks (should block): {len(missed_blocks)}")
        if missed_blocks:
            print(f"   Elements: {missed_blocks}")
            for idx in missed_blocks:
                el = next((e for e in result['elements'] if e['index'] == idx), None)
                if el:
                    print(f"   - #{idx}: {el['type']}")
        print()
        
        # Extract patterns from correctly blocked
        print("=" * 100)
        print("📊 LEARNED PATTERNS (from correctly blocked elements)")
        print("=" * 100)
        print()
        
        for idx in correctly_blocked:
            el = next((e for e in result['elements'] if e['index'] == idx), None)
            if el:
                print(f"Element #{idx}: {el['type']}")
                print(f"  Reason: {el['blockReason']}")
                print(f"  Size: {el['width']}x{el['height']}px")
                print()
        
        # Save analysis
        with open('element_pattern_analysis.json', 'w') as f:
            json.dump({
                'template_id': template_id,
                'total_scanned': result['totalScanned'],
                'user_specifications': {
                    'ignore': user_ignore,
                    'keep': user_keep
                },
                'auto_blocking_accuracy': {
                    'correctly_blocked': correctly_blocked,
                    'incorrectly_blocked': incorrectly_blocked,
                    'missed_blocks': missed_blocks,
                    'accuracy': f"{len(correctly_blocked)}/{len(user_ignore)}"
                },
                'all_elements': result['elements']
            }, f, indent=2)
        
        print("💾 Analysis saved: element_pattern_analysis.json")


if __name__ == "__main__":
    asyncio.run(main())
