#!/usr/bin/env python3
"""
Complete Page Structure Detector
Detects EVERYTHING including template cards, titles, action buttons, etc.
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
    print("🔍 COMPLETE PAGE STRUCTURE DETECTION")
    print("=" * 100)
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            page = await context.new_page()
            
            print("🌐 Navigating to templates page...")
            await page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                          wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(4)
            
            print("🔍 Deep scanning page structure...\n")
            
            # Comprehensive detection
            page_structure = await page.evaluate("""
                () => {
                    const structure = {
                        page_title: document.title,
                        url: window.location.href,
                        
                        // 1. FILTERS & CONTROLS
                        filters: {
                            department_filter: null,
                            search_boxes: [],
                            page_size_selector: null
                        },
                        
                        // 2. TABS WITH COUNTS
                        tabs: [],
                        
                        // 3. ACTION BUTTONS (Top section)
                        action_buttons: {
                            drafts: null,
                            archive: null,
                            actions: null,
                            new_template: null,
                            other: []
                        },
                        
                        // 4. TEMPLATE CARDS/TILES
                        template_cards: [],
                        
                        // 5. TABLE/LIST VIEW
                        template_list: {
                            headers: [],
                            rows: [],
                            view_type: null
                        },
                        
                        // 6. PAGINATION
                        pagination: {
                            current_page: null,
                            total_items: null,
                            items_per_page: null,
                            prev_button: null,
                            next_button: null
                        },
                        
                        // 7. ALL VISIBLE TEXT ELEMENTS
                        page_sections: [],
                        
                        // 8. DOM STRUCTURE
                        dom_info: {
                            total_buttons: 0,
                            total_links: 0,
                            total_inputs: 0,
                            total_cards: 0,
                            main_containers: []
                        }
                    };
                    
                    // === 1. FILTERS ===
                    const deptFilter = document.querySelector('.ant-dropdown-trigger');
                    if (deptFilter) {
                        const cleanText = deptFilter.textContent.replace(/[^a-zA-Z0-9\\s]/g, '').trim();
                        structure.filters.department_filter = {
                            text: cleanText || deptFilter.textContent.split('}').pop().trim(),
                            selector: '.ant-dropdown-trigger',
                            full_text: deptFilter.textContent
                        };
                    }
                    
                    // Search boxes
                    document.querySelectorAll('input[type="search"], input[placeholder*="Search" i]').forEach(input => {
                        structure.filters.search_boxes.push({
                            placeholder: input.placeholder,
                            value: input.value,
                            type: input.type
                        });
                    });
                    
                    // Page size selector (Select50, etc.)
                    const pageSize = document.querySelector('[role="combobox"]');
                    if (pageSize) {
                        structure.filters.page_size_selector = {
                            text: pageSize.textContent.trim(),
                            aria_expanded: pageSize.getAttribute('aria-expanded')
                        };
                    }
                    
                    // === 2. TABS ===
                    document.querySelectorAll('[role="tab"]').forEach(tab => {
                        const text = tab.textContent.trim();
                        const match = text.match(/(.+?)\\s*\\((\\d+)\\)/);
                        structure.tabs.push({
                            label: match ? match[1] : text,
                            count: match ? parseInt(match[2]) : 0,
                            active: tab.getAttribute('aria-selected') === 'true',
                            full_text: text
                        });
                    });
                    
                    // === 3. ACTION BUTTONS ===
                    document.querySelectorAll('button').forEach(btn => {
                        const text = btn.textContent.trim();
                        
                        if (text.includes('Draft')) {
                            const match = text.match(/Drafts?\\s*\\((\\d+)\\)/);
                            structure.action_buttons.drafts = {
                                text: text,
                                count: match ? parseInt(match[1]) : 0
                            };
                        } else if (text.includes('Archive')) {
                            const match = text.match(/Archive\\s*\\((\\d+)\\)/);
                            structure.action_buttons.archive = {
                                text: text,
                                count: match ? parseInt(match[1]) : 0
                            };
                        } else if (text === 'Actions') {
                            structure.action_buttons.actions = {
                                text: text,
                                disabled: btn.disabled
                            };
                        } else if (text.includes('New Template')) {
                            structure.action_buttons.new_template = {
                                text: text,
                                disabled: btn.disabled
                            };
                        }
                    });
                    
                    // === 4. TEMPLATE CARDS/TILES ===
                    // Look for card containers
                    const cardSelectors = [
                        '[class*="card"]',
                        '[class*="tile"]',
                        '[class*="item"]',
                        '[class*="template"]'
                    ];
                    
                    cardSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(card => {
                            if (card.offsetParent && card.offsetHeight > 50) {
                                // Try to extract template info
                                const heading = card.querySelector('h1, h2, h3, h4, h5, h6');
                                const title = heading?.textContent.trim();
                                
                                if (title && title.length > 3 && title.length < 200) {
                                    const cardInfo = {
                                        title: title,
                                        selector: selector,
                                        classes: card.className.substring(0, 100),
                                        has_image: card.querySelector('img') !== null,
                                        buttons: [],
                                        badges: []
                                    };
                                    
                                    // Get buttons in card
                                    card.querySelectorAll('button').forEach(btn => {
                                        const btnText = btn.textContent.trim();
                                        if (btnText) cardInfo.buttons.push(btnText);
                                    });

                                    // Get badges/tags
                                    card.querySelectorAll('[class*="badge"], [class*="tag"]').forEach(badge => {
                                        const badgeText = badge.textContent.trim();
                                        if (badgeText) cardInfo.badges.push(badgeText);
                                    });

                                    // Check if already added
                                    const exists = structure.template_cards.some(c => c.title === title);
                                    if (!exists) {
                                        structure.template_cards.push(cardInfo);
                                    }
                                }
                            }
                        });
                    });

                    // === 5. TABLE/LIST HEADERS & ROWS ===
                    document.querySelectorAll('th').forEach(th => {
                        const text = th.textContent.trim();
                        if (text) structure.template_list.headers.push(text);
                    });

                    // Try to detect template rows
                    document.querySelectorAll('tr').forEach(tr => {
                        const cells = tr.querySelectorAll('td');
                        if (cells.length > 0) {
                            const rowData = [];
                            cells.forEach(cell => {
                                rowData.push(cell.textContent.trim());
                            });
                            if (rowData.some(d => d.length > 0)) {
                                structure.template_list.rows.push(rowData);
                            }
                        }
                    });

                    // === 6. PAGINATION ===
                    const paginationContainer = document.querySelector('[class*="pagination"]');
                    if (paginationContainer) {
                        const paginationText = paginationContainer.textContent;

                        // Look for patterns like "1-10 of 50"
                        const match = paginationText.match(/(\\d+)-(\\d+)\\s+of\\s+(\\d+)/);
                        if (match) {
                            structure.pagination.current_page = Math.ceil(parseInt(match[2]) / (parseInt(match[2]) - parseInt(match[1]) + 1));
                            structure.pagination.total_items = parseInt(match[3]);
                            structure.pagination.items_per_page = parseInt(match[2]) - parseInt(match[1]) + 1;
                        }
                    }

                    // Prev/Next buttons
                    document.querySelectorAll('button').forEach(btn => {
                        const text = btn.textContent.trim().toLowerCase();
                        if (text === 'prev' || text === 'previous') {
                            structure.pagination.prev_button = { text: btn.textContent.trim(), disabled: btn.disabled };
                        } else if (text === 'next') {
                            structure.pagination.next_button = { text: btn.textContent.trim(), disabled: btn.disabled };
                        }
                    });

                    // === 7. PAGE SECTIONS (Headings) ===
                    ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].forEach(tag => {
                        document.querySelectorAll(tag).forEach(h => {
                            const text = h.textContent.trim();
                            if (text && h.offsetParent) {
                                structure.page_sections.push({
                                    level: tag,
                                    text: text,
                                    className: h.className.substring(0, 50)
                                });
                            }
                        });
                    });

                    // === 8. DOM STATS ===
                    structure.dom_info.total_buttons = document.querySelectorAll('button').length;
                    structure.dom_info.total_links = document.querySelectorAll('a').length;
                    structure.dom_info.total_inputs = document.querySelectorAll('input').length;

                    // Find main containers
                    document.querySelectorAll('[class*="container"], [class*="wrapper"], main').forEach(container => {
                        if (container.offsetParent && container.offsetHeight > 100) {
                            structure.dom_info.main_containers.push({
                                tag: container.tagName,
                                classes: container.className.substring(0, 60),
                                children_count: container.children.length
                            });
                        }
                    });

                    return structure;
                }
            """)

            # Save JSON
            filename = f"complete_page_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(page_structure, f, indent=2)

            # Print detailed report
            print("=" * 100)
            print("📊 COMPLETE PAGE STRUCTURE REPORT")
            print("=" * 100)

            print(f"\n🌐 PAGE INFO:")
            print(f"   Title: {page_structure['page_title']}")
            print(f"   URL: {page_structure['url']}")

            print(f"\n🎛️ FILTERS & CONTROLS:")
            if page_structure['filters']['department_filter']:
                print(f"   1. Department Filter: {page_structure['filters']['department_filter']['text']}")

            for i, sb in enumerate(page_structure['filters']['search_boxes'], 2):
                print(f"   {i}. Search Box: \"{sb['placeholder']}\"")

            if page_structure['filters']['page_size_selector']:
                print(f"   12. Page Size Dropdown: {page_structure['filters']['page_size_selector']['text']}")

            print(f"\n📑 TABS:")
            for i, tab in enumerate(page_structure['tabs'], 1):
                active = "✓" if tab['active'] else " "
                print(f"   {active} 13-{i}. Tab: {tab['label']} ({tab['count']})")

            print(f"\n🔘 ACTION BUTTONS:")
            buttons_found = []
            if page_structure['action_buttons']['drafts']:
                print(f"   5. Drafts: {page_structure['action_buttons']['drafts']['text']}")
                buttons_found.append('Drafts')
            if page_structure['action_buttons']['archive']:
                print(f"   6. Archive: {page_structure['action_buttons']['archive']['text']}")
                buttons_found.append('Archive')
            if page_structure['action_buttons']['actions']:
                print(f"   7. Actions: {page_structure['action_buttons']['actions']['text']}")
            if page_structure['action_buttons']['new_template']:
                print(f"   8. New Template: {page_structure['action_buttons']['new_template']['text']}")

            print(f"\n📋 TEMPLATE CARDS/TILES: {len(page_structure['template_cards'])}")
            for i, card in enumerate(page_structure['template_cards'][:10], 1):
                print(f"   17-{i}. {card['title']}")
                if card['buttons']:
                    print(f"         Buttons: {', '.join(card['buttons'][:3])}")

            if len(page_structure['template_cards']) > 10:
                print(f"   ... and {len(page_structure['template_cards']) - 10} more cards")

            print(f"\n📄 TABLE/LIST VIEW:")
            if page_structure['template_list']['headers']:
                print(f"   Headers: {', '.join(page_structure['template_list']['headers'])}")
            print(f"   Rows: {len(page_structure['template_list']['rows'])}")

            print(f"\n📃 PAGINATION:")
            if page_structure['pagination']['total_items']:
                print(f"   Total Items: {page_structure['pagination']['total_items']}")
                print(f"   Items Per Page: {page_structure['pagination']['items_per_page']}")
            if page_structure['pagination']['prev_button']:
                print(f"   Prev Button: {page_structure['pagination']['prev_button']['text']} (Disabled: {page_structure['pagination']['prev_button']['disabled']})")
            if page_structure['pagination']['next_button']:
                print(f"   Next Button: {page_structure['pagination']['next_button']['text']} (Disabled: {page_structure['pagination']['next_button']['disabled']})")

            print(f"\n📰 PAGE SECTIONS (Headings): {len(page_structure['page_sections'])}")
            for section in page_structure['page_sections'][:15]:
                print(f"   {section['level'].upper()}: {section['text']}")

            print(f"\n📊 DOM STATISTICS:")
            print(f"   Total Buttons: {page_structure['dom_info']['total_buttons']}")
            print(f"   Total Links: {page_structure['dom_info']['total_links']}")
            print(f"   Total Inputs: {page_structure['dom_info']['total_inputs']}")
            print(f"   Main Containers: {len(page_structure['dom_info']['main_containers'])}")

            print("\n" + "=" * 100)
            print(f"✅ COMPLETE DATA SAVED TO: {filename}")
            print("=" * 100)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

