#!/usr/bin/env python3
"""
DOM Analysis Bot Deployment
Deploys intelligent bots into the DOM to analyze everything deeply
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("=" * 100)
    print("🤖 DEPLOYING DOM ANALYSIS BOTS")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser via CDP")

            # Use existing tab instead of creating new one
            context = browser.contexts[0]
            pages = context.pages

            # Find the templates page or use the first available page
            page = None
            for p in pages:
                if 'templates/list' in p.url:
                    page = p
                    print(f"✅ Found existing templates page: {p.url}")
                    break

            if not page:
                # Use first available page
                page = pages[0] if pages else await context.new_page()
                print(f"📄 Using existing tab: {page.url}")

                # Only navigate if we're not already on the templates page
                if 'templates/list' not in page.url:
                    print("🌐 Navigating to templates page...")
                    await page.goto("https://preprodapp.tekioncloud.com/templates/list",
                                  wait_until='domcontentloaded', timeout=15000)
                    await asyncio.sleep(3)
            else:
                # Just refresh to ensure we have fresh data
                print("🔄 Using existing templates page (no navigation needed)")
                await asyncio.sleep(1)
            
            print("🤖 Deploying DOM analysis bots into the page...")
            print()
            
            # Deploy the bot - this JavaScript will run IN the page and analyze everything
            analysis_results = await page.evaluate("""
                () => {
                    console.log('🤖 DOM Analysis Bot deployed!');
                    
                    const analysis = {
                        timestamp: new Date().toISOString(),
                        url: window.location.href,
                        
                        // BOT 1: Grid/Layout Bot
                        layout: {
                            grids: [],
                            containers: [],
                            flex_containers: []
                        },
                        
                        // BOT 2: Filter Bot
                        filters: {
                            department: null,
                            dropdowns: [],
                            search_fields: [],
                            checkboxes: []
                        },
                        
                        // BOT 3: Navigation Bot  
                        navigation: {
                            tabs: [],
                            buttons: [],
                            links: []
                        },
                        
                        // BOT 4: Content Bot
                        content: {
                            template_cards: [],
                            table_data: [],
                            headings: []
                        },
                        
                        // BOT 5: Interactive Elements Bot
                        interactive: {
                            clickable: [],
                            editable: [],
                            hoverable: []
                        },
                        
                        // BOT 6: Data Extraction Bot
                        data: {
                            counts: [],
                            status_badges: [],
                            metadata: []
                        }
                    };
                    
                    // ========================================
                    // BOT 1: GRID/LAYOUT BOT
                    // ========================================
                    console.log('🤖 Bot 1: Scanning grids and layouts...');
                    
                    // Find all grid containers
                    document.querySelectorAll('*').forEach((el, index) => {
                        const style = window.getComputedStyle(el);
                        
                        // CSS Grid detection
                        if (style.display === 'grid') {
                            analysis.layout.grids.push({
                                index: analysis.layout.grids.length + 1,
                                tag: el.tagName,
                                class: el.className.substring(0, 100),
                                columns: style.gridTemplateColumns,
                                rows: style.gridTemplateRows,
                                gap: style.gap,
                                children_count: el.children.length,
                                visible_children: Array.from(el.children).filter(c => c.offsetParent !== null).length
                            });
                        }
                        
                        // Flexbox detection
                        if (style.display === 'flex' && el.children.length > 2) {
                            analysis.layout.flex_containers.push({
                                index: analysis.layout.flex_containers.length + 1,
                                tag: el.tagName,
                                class: el.className.substring(0, 100),
                                direction: style.flexDirection,
                                wrap: style.flexWrap,
                                justify: style.justifyContent,
                                align: style.alignItems,
                                children: el.children.length
                            });
                        }
                        
                        // Main containers (high-level layout)
                        const className = typeof el.className === 'string' ? el.className : '';
                        if (className.includes('container') ||
                            className.includes('wrapper') ||
                            className.includes('main')) {
                            if (el.offsetParent && el.offsetHeight > 100) {
                                analysis.layout.containers.push({
                                    class: className.substring(0, 80),
                                    tag: el.tagName,
                                    width: el.offsetWidth,
                                    height: el.offsetHeight
                                });
                            }
                        }
                    });
                    
                    // ========================================
                    // BOT 2: FILTER BOT
                    // ========================================
                    console.log('🤖 Bot 2: Scanning filters and controls...');
                    
                    // Department filter (Ant Design dropdown)
                    const deptFilter = document.querySelector('.ant-dropdown-trigger');
                    if (deptFilter) {
                        const text = deptFilter.textContent.trim();
                        // Clean up the CSS injection text
                        const cleanText = text.split('{')[0].split('}').pop().trim();
                        analysis.filters.department = {
                            text: cleanText || 'Sales',
                            selector: '.ant-dropdown-trigger',
                            visible: deptFilter.offsetParent !== null,
                            bbox: deptFilter.getBoundingClientRect()
                        };
                    }
                    
                    // All dropdowns
                    document.querySelectorAll('[role="combobox"]').forEach((dd, i) => {
                        analysis.filters.dropdowns.push({
                            index: i + 1,
                            text: dd.textContent.trim(),
                            expanded: dd.getAttribute('aria-expanded') === 'true',
                            bbox: dd.getBoundingClientRect()
                        });
                    });
                    
                    // Search fields
                    document.querySelectorAll('input[type="search"], input[placeholder*="Search" i]').forEach((input, i) => {
                        analysis.filters.search_fields.push({
                            index: i + 1,
                            placeholder: input.placeholder,
                            value: input.value,
                            name: input.name,
                            bbox: input.getBoundingClientRect()
                        });
                    });
                    
                    // Checkboxes
                    document.querySelectorAll('input[type="checkbox"]').forEach((cb, i) => {
                        const label = cb.nextElementSibling?.textContent?.trim() ||
                                     cb.parentElement?.textContent?.trim() ||
                                     'Checkbox ' + (i + 1);
                        analysis.filters.checkboxes.push({
                            index: i + 1,
                            label: label.substring(0, 50),
                            checked: cb.checked,
                            disabled: cb.disabled,
                            visible: cb.offsetParent !== null
                        });
                    });

                    // ========================================
                    // BOT 3: NAVIGATION BOT
                    // ========================================
                    console.log('🤖 Bot 3: Scanning navigation elements...');

                    // Tabs with counts
                    document.querySelectorAll('[role="tab"]').forEach((tab, i) => {
                        const text = tab.textContent.trim();
                        const match = text.match(/(.+?)\\s*\\((\\d+)\\)/);
                        analysis.navigation.tabs.push({
                            index: i + 1,
                            label: match ? match[1] : text,
                            count: match ? parseInt(match[2]) : null,
                            active: tab.getAttribute('aria-selected') === 'true',
                            full_text: text,
                            bbox: tab.getBoundingClientRect()
                        });
                    });

                    // Important buttons
                    document.querySelectorAll('button').forEach((btn, i) => {
                        if (btn.offsetParent === null) return; // Skip hidden

                        const text = btn.textContent.trim();
                        if (!text) return;

                        // Categorize button
                        let category = 'other';
                        if (text.toLowerCase().includes('draft')) category = 'drafts';
                        else if (text.toLowerCase().includes('archive')) category = 'archive';
                        else if (text.toLowerCase().includes('template')) category = 'template';
                        else if (text.toLowerCase().includes('action')) category = 'actions';
                        else if (text.toLowerCase().includes('prev')) category = 'pagination';
                        else if (text.toLowerCase().includes('next')) category = 'pagination';

                        const countMatch = text.match(/\\((\\d+)\\)/);

                        analysis.navigation.buttons.push({
                            index: i + 1,
                            text: text,
                            category: category,
                            count: countMatch ? parseInt(countMatch[1]) : null,
                            disabled: btn.disabled,
                            bbox: btn.getBoundingClientRect()
                        });
                    });

                    // Links
                    document.querySelectorAll('a[href]').forEach((link, i) => {
                        if (link.offsetParent === null) return;
                        const text = link.textContent.trim();
                        if (text && text.length < 100) {
                            analysis.navigation.links.push({
                                index: i + 1,
                                text: text,
                                href: link.href.substring(0, 150),
                                bbox: link.getBoundingClientRect()
                            });
                        }
                    });

                    // ========================================
                    // BOT 4: CONTENT BOT
                    // ========================================
                    console.log('🤖 Bot 4: Scanning content and template cards...');

                    // All headings
                    ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(tag => {
                        document.querySelectorAll(tag).forEach((h, i) => {
                            const text = h.textContent.trim();
                            if (text && h.offsetParent !== null && text.length < 200) {
                                analysis.content.headings.push({
                                    tag: tag,
                                    text: text,
                                    level: parseInt(tag[1]),
                                    bbox: h.getBoundingClientRect()
                                });
                            }
                        });
                    });

                    // Template cards - deep scan
                    // Look for cards/tiles that contain template information
                    const cardContainers = document.querySelectorAll('[class*="card"], [class*="tile"], [class*="item"]');
                    cardContainers.forEach((card, i) => {
                        if (card.offsetParent === null || card.offsetHeight < 50) return;

                        // Extract template title
                        const heading = card.querySelector('h1, h2, h3, h4, h5, h6, [class*="title"], [class*="name"]');
                        const title = heading?.textContent.trim();

                        if (title && title.length > 3 && title.length < 200) {
                            const cardData = {
                                index: analysis.content.template_cards.length + 1,
                                title: title,
                                class: card.className.substring(0, 80),
                                has_image: card.querySelector('img') !== null,
                                badges: [],
                                buttons: [],
                                metadata: []
                            };

                            // Extract badges/tags
                            card.querySelectorAll('[class*="badge"], [class*="tag"], [class*="label"]').forEach(badge => {
                                const badgeText = badge.textContent.trim();
                                if (badgeText && badgeText.length < 50) {
                                    cardData.badges.push(badgeText);
                                }
                            });

                            // Extract buttons in card
                            card.querySelectorAll('button').forEach(btn => {
                                const btnText = btn.textContent.trim();
                                if (btnText && btnText.length < 50) {
                                    cardData.buttons.push(btnText);
                                }
                            });

                            // Extract any metadata (dates, authors, etc.)
                            const metaElements = card.querySelectorAll('[class*="meta"], [class*="info"], [class*="date"]');
                            metaElements.forEach(meta => {
                                const metaText = meta.textContent.trim();
                                if (metaText && metaText.length < 100) {
                                    cardData.metadata.push(metaText);
                                }
                            });

                            analysis.content.template_cards.push(cardData);
                        }
                    });

                    // Table data (if templates are in table format)
                    const tables = document.querySelectorAll('table');
                    tables.forEach((table, i) => {
                        const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
                        const rows = [];

                        table.querySelectorAll('tbody tr').forEach((tr, rowIndex) => {
                            const cells = Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim());
                            if (cells.length > 0) {
                                rows.push({
                                    index: rowIndex + 1,
                                    cells: cells
                                });
                            }
                        });

                        if (headers.length > 0 || rows.length > 0) {
                            analysis.content.table_data.push({
                                index: i + 1,
                                headers: headers,
                                row_count: rows.length,
                                sample_rows: rows.slice(0, 5) // First 5 rows
                            });
                        }
                    });

                    // ========================================
                    // BOT 5: INTERACTIVE ELEMENTS BOT
                    // ========================================
                    console.log('🤖 Bot 5: Scanning interactive elements...');

                    // All clickable elements
                    const clickableSelectors = [
                        'button',
                        'a[href]',
                        '[role="button"]',
                        '[onclick]',
                        '[class*="clickable"]'
                    ];

                    clickableSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => {
                            if (el.offsetParent !== null) {
                                const text = el.textContent.trim().substring(0, 50);
                                if (text) {
                                    analysis.interactive.clickable.push({
                                        type: el.tagName,
                                        text: text,
                                        selector: selector
                                    });
                                }
                            }
                        });
                    });

                    // Editable elements
                    document.querySelectorAll('input, textarea, [contenteditable="true"]').forEach(el => {
                        if (el.offsetParent !== null) {
                            analysis.interactive.editable.push({
                                type: el.tagName,
                                inputType: el.type || 'textarea',
                                placeholder: el.placeholder || '',
                                name: el.name || ''
                            });
                        }
                    });

                    // ========================================
                    // BOT 6: DATA EXTRACTION BOT
                    // ========================================
                    console.log('🤖 Bot 6: Extracting data and counts...');

                    // Find all elements with counts in parentheses
                    document.querySelectorAll('*').forEach(el => {
                        if (el.children.length === 0 && el.offsetParent !== null) {
                            const text = el.textContent.trim();
                            const match = text.match(/^(.+?)\\s*\\((\\d+)\\)$/);
                            if (match && text.length < 50) {
                                analysis.data.counts.push({
                                    label: match[1],
                                    count: parseInt(match[2]),
                                    full_text: text,
                                    tag: el.tagName
                                });
                            }
                        }
                    });

                    // Status badges
                    const badgeSelectors = [
                        '[class*="badge"]',
                        '[class*="status"]',
                        '[class*="tag"]',
                        '[class*="chip"]'
                    ];

                    badgeSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(badge => {
                            const text = badge.textContent.trim();
                            if (text && text.length < 30 && badge.offsetParent !== null) {
                                analysis.data.status_badges.push({
                                    text: text,
                                    class: badge.className.substring(0, 60)
                                });
                            }
                        });
                    });

                    console.log('✅ All bots completed analysis!');
                    console.log('📊 Results:', {
                        grids: analysis.layout.grids.length,
                        flex_containers: analysis.layout.flex_containers.length,
                        filters: Object.keys(analysis.filters).length,
                        tabs: analysis.navigation.tabs.length,
                        buttons: analysis.navigation.buttons.length,
                        template_cards: analysis.content.template_cards.length,
                        headings: analysis.content.headings.length
                    });

                    return analysis;
                }
            """)

            # Save results
            filename = f"dom_bot_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(analysis_results, f, indent=2)

            print("=" * 100)
            print("📊 BOT ANALYSIS COMPLETE")
            print("=" * 100)
            print()

            # Print summary
            print("🤖 BOT 1 - LAYOUT:")
            print(f"   CSS Grids: {len(analysis_results['layout']['grids'])}")
            print(f"   Flex Containers: {len(analysis_results['layout']['flex_containers'])}")
            print(f"   Main Containers: {len(analysis_results['layout']['containers'])}")

            print("\n🤖 BOT 2 - FILTERS:")
            dept = analysis_results['filters'].get('department')
            if dept:
                print(f"   Department: {dept['text']}")
            print(f"   Dropdowns: {len(analysis_results['filters']['dropdowns'])}")
            print(f"   Search Fields: {len(analysis_results['filters']['search_fields'])}")
            print(f"   Checkboxes: {len(analysis_results['filters']['checkboxes'])}")

            print("\n🤖 BOT 3 - NAVIGATION:")
            print(f"   Tabs: {len(analysis_results['navigation']['tabs'])}")
            for tab in analysis_results['navigation']['tabs']:
                active = "✓" if tab['active'] else " "
                count = f" ({tab['count']})" if tab['count'] else ""
                print(f"     [{active}] {tab['label']}{count}")

            print(f"\n   Important Buttons:")
            for btn in analysis_results['navigation']['buttons']:
                if btn['category'] != 'other':
                    count = f" ({btn['count']})" if btn['count'] else ""
                    print(f"     {btn['category'].upper()}: {btn['text']}{count}")

            print(f"\n🤖 BOT 4 - CONTENT:")
            print(f"   Template Cards: {len(analysis_results['content']['template_cards'])}")
            print(f"   Headings: {len(analysis_results['content']['headings'])}")
            print(f"   Tables: {len(analysis_results['content']['table_data'])}")

            if analysis_results['content']['template_cards']:
                print(f"\n   Sample Template Cards:")
                for card in analysis_results['content']['template_cards'][:5]:
                    print(f"     • {card['title']}")

            print(f"\n🤖 BOT 5 - INTERACTIVE:")
            print(f"   Clickable: {len(analysis_results['interactive']['clickable'])}")
            print(f"   Editable: {len(analysis_results['interactive']['editable'])}")

            print(f"\n🤖 BOT 6 - DATA:")
            print(f"   Counts Found: {len(analysis_results['data']['counts'])}")
            print(f"   Status Badges: {len(analysis_results['data']['status_badges'])}")

            if analysis_results['data']['counts']:
                print(f"\n   Detected Counts:")
                for count in analysis_results['data']['counts'][:10]:
                    print(f"     {count['label']}: {count['count']}")

            print()
            print("=" * 100)
            print(f"💾 Full results saved to: {filename}")
            print("=" * 100)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

