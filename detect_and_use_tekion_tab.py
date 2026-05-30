#!/usr/bin/env python3
"""
Detect all open tabs and find the Tekion template tab
Then search for logos AND analyze Header option status in left panel
IMPROVED: Now includes detailed logo position and Header status detection
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def analyze_logo_and_header(page):
    """
    Analyze logo position and Header option status
    Returns: dict with logo info and header status
    """

    # Load ignore list
    with open('logo_ignore_list.json') as f:
        ignore_list = json.load(f)

    analysis = await page.evaluate("""
        (ignorePatterns) => {
            const results = {
                logo: null,
                headerOption: null,
                leftPanelElements: []
            };

            // Helper to check if ignored
            function isIgnored(el) {
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

            // Find actual template logo (in TD, from S3)
            const allImgs = document.querySelectorAll('img');
            for (const img of allImgs) {
                if (isIgnored(img)) continue;

                const src = img.src || '';
                if (src.includes('amazonaws.com') &&
                    src.includes('media_') &&
                    img.parentElement?.tagName === 'TD') {

                    const rect = img.getBoundingClientRect();
                    const parent = img.parentElement;
                    const table = img.closest('table');

                    // Determine section (header/body/footer)
                    let section = 'BODY';
                    const pageHeight = window.innerHeight;
                    if (rect.top < pageHeight * 0.2) {
                        section = 'HEADER_AREA';
                    } else if (rect.top > pageHeight * 0.8) {
                        section = 'FOOTER_AREA';
                    }

                    results.logo = {
                        src: src.substring(0, 150),
                        alt: img.alt || '',
                        displaySize: {
                            width: rect.width,
                            height: rect.height
                        },
                        naturalSize: {
                            width: img.naturalWidth,
                            height: img.naturalHeight
                        },
                        position: {
                            top: rect.top,
                            left: rect.left,
                            right: rect.right,
                            bottom: rect.bottom
                        },
                        section: section,
                        parent: {
                            tag: parent.tagName,
                            align: parent.align || '',
                            valign: parent.valign || ''
                        },
                        inTable: table !== null
                    };
                    break;
                }
            }

            // Search for Header option in left panel
            // Look in multiple ways: direct text, aria-label, icons, etc.
            const allElements = document.querySelectorAll('*');

            allElements.forEach(el => {
                const text = el.textContent?.trim() || '';
                const ariaLabel = el.getAttribute('aria-label') || '';
                const rect = el.getBoundingClientRect();

                // Left panel check (x < 300px)
                if (rect.left < 300 && rect.width > 0 && rect.width < 250) {

                    // Look for "Header" text or aria-label or class
                    const isHeaderElement = text === 'Header' ||
                                          text === 'HEADER' ||
                                          text.toLowerCase() === 'header' ||
                                          ariaLabel.toLowerCase().includes('header') ||
                                          el.className?.includes('icon-header');

                    if (isHeaderElement) {
                        const computedStyle = window.getComputedStyle(el);
                        const isDisabled = el.hasAttribute('disabled') ||
                                         el.getAttribute('aria-disabled') === 'true';
                        const isGrayed = computedStyle.opacity < 1 ||
                                       computedStyle.opacity === '0.5' ||
                                       computedStyle.color.includes('rgb(128') ||
                                       computedStyle.color.includes('rgb(192') ||
                                       computedStyle.color.includes('rgba(0, 0, 0, 0.25)') ||
                                       el.className?.includes('disabled') ||
                                       el.className?.includes('Disabled') ||
                                       el.className?.includes('gray');

                        const parentButton = el.closest('button, [role="button"], [class*="Button"], div[class*="button"]');

                        // Only set if not already found, or if this one looks more specific
                        if (!results.headerOption || text === 'Header') {
                            results.headerOption = {
                                text: text || ariaLabel,
                                tag: el.tagName,
                                id: el.id || '',
                                className: el.className?.substring(0, 80) || '',
                                ariaLabel: ariaLabel,
                                disabled: isDisabled,
                                grayed: isGrayed,
                                opacity: computedStyle.opacity,
                                color: computedStyle.color,
                                pointerEvents: computedStyle.pointerEvents,
                                position: {
                                    top: rect.top,
                                    left: rect.left
                                },
                                size: {
                                    width: rect.width,
                                    height: rect.height
                                },
                                visible: el.offsetParent !== null,
                                parentButton: parentButton ? {
                                    tag: parentButton.tagName,
                                    disabled: parentButton.disabled || parentButton.hasAttribute('disabled'),
                                    className: parentButton.className?.substring(0, 60) || '',
                                    opacity: window.getComputedStyle(parentButton).opacity,
                                    pointerEvents: window.getComputedStyle(parentButton).pointerEvents
                                } : null
                            };
                        }
                    }

                    // Collect left panel elements for context
                    if (text.length > 0 && text.length < 50) {
                        const computedStyle = window.getComputedStyle(el);
                        const isGrayed = computedStyle.opacity < 1;

                        results.leftPanelElements.push({
                            text: text.substring(0, 30),
                            position: rect.top,
                            grayed: isGrayed,
                            opacity: computedStyle.opacity
                        });
                    }
                }
            });

            return results;
        }
    """, ignore_list['ignore_patterns'])

    return analysis


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        print("=" * 100)
        print("🔍 DETECTING ALL OPEN TABS")
        print("=" * 100)
        
        all_pages = context.pages
        print(f"\nTotal tabs open: {len(all_pages)}\n")
        
        # List all tabs
        for i, p in enumerate(all_pages):
            print(f"{i+1}. {p.url}")
        
        # Find Tekion template tab
        tekion_page = None
        for p in all_pages:
            if 'tekioncloud.com/templates' in p.url:
                tekion_page = p
                break
        
        if not tekion_page:
            print("\n❌ No Tekion template tab found!")
            print("Please make sure you have a Tekion template page open.")
            return
        
        print("\n" + "=" * 100)
        print(f"✅ FOUND TEKION TEMPLATE TAB")
        print("=" * 100)
        print(f"\nURL: {tekion_page.url}")
        
        # Bring it to front
        await tekion_page.bring_to_front()
        print("✅ Switched to Tekion tab")
        
        # Wait a moment for it to be active
        await asyncio.sleep(2)

        print("\n" + "=" * 100)
        print("🔍 ANALYZING LOGO POSITION & HEADER OPTION")
        print("=" * 100)

        # Run improved analysis
        analysis = await analyze_logo_and_header(tekion_page)

        # Print Logo Analysis
        print("\n📍 LOGO POSITION ANALYSIS:")
        print("=" * 100)

        if analysis['logo']:
            logo = analysis['logo']
            print(f"\n✅ Template Logo Found:")
            print(f"   Source: {logo['src']}")
            print(f"\n   📏 Size:")
            print(f"      Display: {logo['displaySize']['width']:.0f} x {logo['displaySize']['height']:.0f} px")
            print(f"      Natural: {logo['naturalSize']['width']} x {logo['naturalSize']['height']} px")
            print(f"\n   📍 Position on Screen:")
            print(f"      Top: {logo['position']['top']:.0f}px")
            print(f"      Left: {logo['position']['left']:.0f}px")
            print(f"      Right: {logo['position']['right']:.0f}px")
            print(f"      Bottom: {logo['position']['bottom']:.0f}px")
            print(f"\n   🎯 Location:")
            print(f"      Section: {logo['section']} {'⭐' if logo['section'] == 'BODY' else ''}")
            print(f"      In Table: {logo['inTable']}")
            print(f"      Parent: <{logo['parent']['tag']}>")
            if logo['parent']['align']:
                print(f"      Alignment: {logo['parent']['align']}")
            if logo['parent']['valign']:
                print(f"      Vertical Align: {logo['parent']['valign']}")

            print(f"\n   💡 Analysis:")
            if logo['section'] == 'BODY':
                print(f"      ✅ Logo is in the TEMPLATE BODY (main content area)")
            elif logo['section'] == 'HEADER_AREA':
                print(f"      ⚠️  Logo is in the HEADER area (top 20% of page)")
            else:
                print(f"      ⚠️  Logo is in the FOOTER area (bottom 20% of page)")
        else:
            print("\n❌ No template logo found")

        # Print Header Option Analysis
        print("\n\n🎛️  HEADER OPTION STATUS:")
        print("=" * 100)

        if analysis['headerOption']:
            header = analysis['headerOption']
            print(f"\n✅ Header Option Found in Left Panel:")
            print(f"   Text: '{header['text']}'")
            print(f"   Tag: <{header['tag']}>")
            print(f"   ID: {header['id'] or 'N/A'}")
            print(f"   Class: {header['className'][:60] if header['className'] else 'N/A'}")

            print(f"\n   🎨 Visual State:")
            print(f"      Disabled: {header['disabled']} {'⚠️ YES' if header['disabled'] else '✅ No'}")
            print(f"      Grayed Out: {header['grayed']} {'⚠️ YES - GRAYED!' if header['grayed'] else '✅ Normal'}")
            print(f"      Opacity: {header['opacity']}")
            print(f"      Color: {header['color']}")

            print(f"\n   📍 Position:")
            print(f"      Top: {header['position']['top']:.0f}px")
            print(f"      Left: {header['position']['left']:.0f}px")
            print(f"      Size: {header['size']['width']:.0f}x{header['size']['height']:.0f}px")
            print(f"      Visible: {header['visible']}")

            if header['parentButton']:
                print(f"\n   🔘 Parent Button:")
                print(f"      Tag: <{header['parentButton']['tag']}>")
                print(f"      Disabled: {header['parentButton']['disabled']}")
                print(f"      Class: {header['parentButton']['className']}")

            # Summary
            print(f"\n   📊 Summary:")
            if header['grayed'] or header['disabled']:
                print(f"      ⚠️  Header option is GRAYED OUT / DISABLED")
                print(f"      This might indicate:")
                print(f"         - Header section already exists in template")
                print(f"         - Header insertion is not allowed in current context")
                print(f"         - User permissions restrict header editing")
            else:
                print(f"      ✅ Header option is ENABLED and available")
        else:
            print("\n⚠️  Header option not found in left panel")
            print("   Possible reasons:")
            print("   - Not visible in current view")
            print("   - Different element name")
            print("   - Panel not fully loaded")

        # Show some left panel context
        if analysis['leftPanelElements']:
            print(f"\n\n📋 LEFT PANEL ELEMENTS ({len(analysis['leftPanelElements'])} found):")
            print("=" * 100)

            # Sort by position
            sorted_elements = sorted(analysis['leftPanelElements'], key=lambda x: x['position'])

            for i, elem in enumerate(sorted_elements[:15], 1):
                grayed = "🔘 GRAYED" if elem['grayed'] else "✅"
                print(f"{i}. {grayed} {elem['text'][:30]} (top={elem['position']:.0f}px, opacity={elem['opacity']})")

        # Highlight logo
        if analysis['logo']:
            print("\n\n🎨 HIGHLIGHTING LOGO:")
            print("=" * 100)

            await tekion_page.evaluate("""
                () => {
                    const allImgs = document.querySelectorAll('img');

                    allImgs.forEach(img => {
                        const src = img.src || '';
                        if (src.includes('amazonaws.com') &&
                            src.includes('media_') &&
                            img.parentElement?.tagName === 'TD') {

                            img.style.border = '5px solid lime';
                            img.style.boxShadow = '0 0 20px rgba(0, 255, 0, 0.8)';
                            img.style.outline = '3px dashed yellow';
                            img.style.outlineOffset = '5px';
                        }
                    });
                }
            """)

            print("✅ Logo highlighted with lime border and yellow outline!")
            print("📸 Taking screenshot...")

            await tekion_page.screenshot(path='tekion_logo_highlighted.png', full_page=True)
            print("✅ Screenshot saved: tekion_logo_highlighted.png")

        print("\n" + "=" * 100)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
