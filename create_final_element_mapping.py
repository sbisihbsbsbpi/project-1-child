#!/usr/bin/env python3
"""
Final Element Mapping - Creates a comprehensive JSON with all important elements
Based on user's requirements:
1. Department Filter
5. Drafts (0)
6. Archive (0)
8. New Template button
12. Dropdown Select50
13. Tab Email (11) - where 11 is the filtered results count
14. Tab Text (1)
17. Page heading / title
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
    print("🎯 CREATING FINAL ELEMENT MAPPING JSON")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            context = browser.contexts[0]
            page = await context.new_page()
            
            print("🌐 Loading page...")
            await page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                          wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(4)
            
            print("🔍 Mapping all important elements...\n")
            
            # Create comprehensive mapping
            element_mapping = await page.evaluate("""
                () => {
                    const mapping = {
                        metadata: {
                            page_url: window.location.href,
                            page_title: document.title,
                            timestamp: new Date().toISOString(),
                            description: "Complete element mapping for Tekion Templates page"
                        },
                        
                        important_elements: {}
                    };
                    
                    // Helper to extract clean text
                    function cleanText(text) {
                        return text.replace(/[^a-zA-Z0-9\\s()]/g, '').trim();
                    }
                    
                    // 1. DEPARTMENT FILTER
                    const deptFilter = document.querySelector('.ant-dropdown-trigger');
                    if (deptFilter) {
                        const fullText = deptFilter.textContent;
                        const cleanedText = cleanText(fullText) || fullText.split('}').pop().trim();
                        
                        mapping.important_elements["1_department_filter"] = {
                            element_number: 1,
                            type: "department_filter",
                            label: "Department Filter",
                            value: cleanedText,
                            full_text: fullText,
                            selector: ".ant-dropdown-trigger",
                            css_class: deptFilter.className,
                            is_interactive: true,
                            description: "Main department filter dropdown (Sales, Service, Parts, etc.)"
                        };
                    }
                    
                    // 2-4. SEARCH BOXES
                    let searchIndex = 2;
                    document.querySelectorAll('input[type="search"], input[placeholder*="Search" i]').forEach(input => {
                        mapping.important_elements[`${searchIndex}_search_box`] = {
                            element_number: searchIndex,
                            type: "search_input",
                            label: "Search Box",
                            placeholder: input.placeholder,
                            value: input.value,
                            selector: `input[placeholder="${input.placeholder}"]`,
                            css_class: input.className,
                            is_interactive: true,
                            description: `Search input field: "${input.placeholder}"`
                        };
                        searchIndex++;
                    });
                    
                    // 5-7. ACTION BUTTONS (Drafts, Archive, Actions)
                    let buttonIndex = 5;
                    document.querySelectorAll('button').forEach(btn => {
                        const text = btn.textContent.trim();
                        
                        if (text.includes('Draft')) {
                            const match = text.match(/Drafts?\\s*\\((\\d+)\\)/);
                            mapping.important_elements["5_drafts_button"] = {
                                element_number: 5,
                                type: "action_button",
                                label: "Drafts",
                                text: text,
                                count: match ? parseInt(match[1]) : 0,
                                disabled: btn.disabled,
                                css_class: btn.className,
                                is_interactive: true,
                                description: "Button to view draft templates"
                            };
                        } else if (text.includes('Archive')) {
                            const match = text.match(/Archive\\s*\\((\\d+)\\)/);
                            mapping.important_elements["6_archive_button"] = {
                                element_number: 6,
                                type: "action_button",
                                label: "Archive",
                                text: text,
                                count: match ? parseInt(match[1]) : 0,
                                disabled: btn.disabled,
                                css_class: btn.className,
                                is_interactive: true,
                                description: "Button to view archived templates"
                            };
                        } else if (text === 'Actions') {
                            mapping.important_elements["7_actions_button"] = {
                                element_number: 7,
                                type: "action_button",
                                label: "Actions",
                                text: text,
                                disabled: btn.disabled,
                                css_class: btn.className,
                                is_interactive: true,
                                description: "Actions dropdown menu button"
                            };
                        }
                    });
                    
                    // 8. NEW TEMPLATE BUTTON
                    document.querySelectorAll('button').forEach(btn => {
                        const text = btn.textContent.trim();
                        if (text.includes('New Template')) {
                            mapping.important_elements["8_new_template_button"] = {
                                element_number: 8,
                                type: "action_button",
                                label: "New Template",
                                text: text,
                                disabled: btn.disabled,
                                css_class: btn.className,
                                is_interactive: true,
                                description: "Primary button to create a new template"
                            };
                        }
                    });
                    
                    // 9-11. Reserved for other controls
                    
                    // 12. PAGE SIZE DROPDOWN (Select50)
                    const pageSizeDropdown = document.querySelector('[role="combobox"]');
                    if (pageSizeDropdown) {
                        mapping.important_elements["12_page_size_dropdown"] = {
                            element_number: 12,
                            type: "dropdown",
                            label: "Page Size Selector",
                            value: pageSizeDropdown.textContent.trim(),
                            aria_expanded: pageSizeDropdown.getAttribute('aria-expanded'),
                            css_class: pageSizeDropdown.className,
                            is_interactive: true,
                            description: "Dropdown to select number of items per page (e.g., Select50)"
                        };
                    }
                    
                    // 13-15. TABS (Email, Text, Live Chat)
                    let tabIndex = 13;
                    document.querySelectorAll('[role="tab"]').forEach(tab => {
                        const fullText = tab.textContent.trim();
                        const match = fullText.match(/(.+?)\\s*\\((\\d+)\\)/);
                        const label = match ? match[1] : fullText;
                        const count = match ? parseInt(match[2]) : 0;
                        const isActive = tab.getAttribute('aria-selected') === 'true';
                        
                        mapping.important_elements[`${tabIndex}_tab_${label.toLowerCase().replace(/\\s+/g, '_')}`] = {
                            element_number: tabIndex,
                            type: "tab",
                            label: label,
                            count: count,
                            full_text: fullText,
                            is_active: isActive,
                            aria_selected: isActive,
                            css_class: tab.className,
                            is_interactive: true,
                            description: `${label} tab showing ${count} filtered results`
                        };
                        tabIndex++;
                    });

                    // 16. Reserved

                    // 17. PAGE HEADING / TITLE
                    const pageHeadings = [];
                    ['h1', 'h2', 'h3', 'h4'].forEach(tag => {
                        document.querySelectorAll(tag).forEach(h => {
                            const text = h.textContent.trim();
                            if (text && text.length > 3 && text.length < 100 && h.offsetParent) {
                                pageHeadings.push({
                                    tag: tag,
                                    text: text,
                                    className: h.className
                                });
                            }
                        });
                    });

                    if (pageHeadings.length > 0) {
                        const mainHeading = pageHeadings[0];
                        mapping.important_elements["17_page_heading"] = {
                            element_number: 17,
                            type: "heading",
                            label: "Page Heading",
                            text: mainHeading.text,
                            tag: mainHeading.tag,
                            css_class: mainHeading.className,
                            is_interactive: false,
                            description: "Main page title/heading"
                        };
                    }

                    // 18+. TEMPLATE CARDS/TILES
                    let tileIndex = 18;

                    // Try multiple strategies to find template tiles
                    const templates = [];

                    // Strategy 1: Look for cards in grid/list containers
                    document.querySelectorAll('[class*="grid"], [class*="list"], [class*="container"]').forEach(container => {
                        if (container.offsetHeight > 200) {
                            Array.from(container.children).forEach((child, idx) => {
                                if (child.offsetHeight > 60 && child.offsetHeight < 600) {
                                    const heading = child.querySelector('h1, h2, h3, h4, h5, h6, [class*="title"], [class*="name"]');
                                    const title = heading?.textContent.trim();

                                    if (title && title.length > 3 && title.length < 150) {
                                        const buttons = [];
                                        child.querySelectorAll('button').forEach(b => {
                                            if (b.textContent.trim()) buttons.push(b.textContent.trim());
                                        });

                                        const exists = templates.some(t => t.title === title);
                                        if (!exists) {
                                            templates.push({
                                                title: title,
                                                height: child.offsetHeight,
                                                buttons: buttons,
                                                has_image: child.querySelector('img') !== null,
                                                css_class: child.className.substring(0, 80)
                                            });
                                        }
                                    }
                                }
                            });
                        }
                    });

                    // Add template cards to mapping
                    templates.forEach((template, idx) => {
                        mapping.important_elements[`${tileIndex + idx}_template_card`] = {
                            element_number: tileIndex + idx,
                            type: "template_card",
                            label: "Template Card",
                            title: template.title,
                            buttons: template.buttons,
                            has_image: template.has_image,
                            css_class: template.css_class,
                            is_interactive: true,
                            description: `Template tile: ${template.title}`
                        };
                    });

                    // ADDITIONAL DETECTIONS

                    // Pagination buttons
                    document.querySelectorAll('button').forEach(btn => {
                        const text = btn.textContent.trim().toLowerCase();
                        if (text === 'prev' || text === 'previous') {
                            mapping.important_elements["pagination_prev"] = {
                                type: "pagination_button",
                                label: "Previous Page",
                                text: btn.textContent.trim(),
                                disabled: btn.disabled,
                                css_class: btn.className,
                                is_interactive: true,
                                description: "Previous page button"
                            };
                        } else if (text === 'next') {
                            mapping.important_elements["pagination_next"] = {
                                type: "pagination_button",
                                label: "Next Page",
                                text: btn.textContent.trim(),
                                disabled: btn.disabled,
                                css_class: btn.className,
                                is_interactive: true,
                                description: "Next page button"
                            };
                        }
                    });

                    // Count total elements
                    mapping.summary = {
                        total_important_elements: Object.keys(mapping.important_elements).length,
                        filters: Object.keys(mapping.important_elements).filter(k => k.includes('filter')).length,
                        buttons: Object.keys(mapping.important_elements).filter(k => k.includes('button')).length,
                        tabs: Object.keys(mapping.important_elements).filter(k => k.includes('tab')).length,
                        dropdowns: Object.keys(mapping.important_elements).filter(k => k.includes('dropdown')).length,
                        template_cards: Object.keys(mapping.important_elements).filter(k => k.includes('template_card')).length
                    };

                    return mapping;
                }
            """)

            # Save JSON
            filename = f"final_element_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(element_mapping, f, indent=2)

            # Print beautiful report
            print("=" * 100)
            print("✅ FINAL ELEMENT MAPPING COMPLETE")
            print("=" * 100)

            print(f"\n📊 SUMMARY:")
            print(f"   Total Important Elements: {element_mapping['summary']['total_important_elements']}")
            print(f"   Filters: {element_mapping['summary']['filters']}")
            print(f"   Buttons: {element_mapping['summary']['buttons']}")
            print(f"   Tabs: {element_mapping['summary']['tabs']}")
            print(f"   Dropdowns: {element_mapping['summary']['dropdowns']}")
            print(f"   Template Cards: {element_mapping['summary']['template_cards']}")

            print(f"\n🎯 IMPORTANT ELEMENTS (User-specified):")
            print()

            # Sort by element number
            sorted_elements = sorted(
                [(k, v) for k, v in element_mapping['important_elements'].items() if 'element_number' in v],
                key=lambda x: x[1]['element_number']
            )

            for key, elem in sorted_elements:
                num = elem['element_number']
                label = elem['label']

                if elem['type'] == 'department_filter':
                    print(f"   {num}. 🎛️  {label}: {elem['value']}")

                elif elem['type'] == 'search_input':
                    print(f"   {num}. 🔍 {label}: \"{elem['placeholder']}\"")

                elif elem['type'] == 'action_button':
                    if 'count' in elem:
                        print(f"   {num}. 🔘 {label}: {elem['text']}")
                    else:
                        print(f"   {num}. 🔘 {label}")

                elif elem['type'] == 'dropdown':
                    print(f"   {num}. 📋 {label}: {elem['value']}")

                elif elem['type'] == 'tab':
                    active = "✓" if elem['is_active'] else " "
                    print(f"   {num}. 📑 {active} {label} ({elem['count']})")

                elif elem['type'] == 'heading':
                    print(f"   {num}. 📰 {label}: \"{elem['text']}\"")

                elif elem['type'] == 'template_card':
                    print(f"   {num}. 🎴 {label}: \"{elem['title']}\"")

            # Show pagination
            if 'pagination_prev' in element_mapping['important_elements']:
                print(f"\n📄 PAGINATION:")
                print(f"   ◀ Previous: (Disabled: {element_mapping['important_elements']['pagination_prev']['disabled']})")
                print(f"   ▶ Next: (Disabled: {element_mapping['important_elements']['pagination_next']['disabled']})")

            print("\n" + "=" * 100)
            print(f"💾 SAVED TO: {filename}")
            print("=" * 100)
            print()
            print("✨ This JSON contains:")
            print("   • All user-specified important elements (1, 5, 6, 8, 12, 13, 14, 17)")
            print("   • Additional detected elements (search boxes, pagination, etc.)")
            print("   • Complete metadata (selectors, CSS classes, interactive status)")
            print("   • Element descriptions and types")
            print()

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

