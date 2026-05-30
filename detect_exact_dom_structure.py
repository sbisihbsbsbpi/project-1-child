#!/usr/bin/env python3
"""
Exact DOM Structure Detector
Captures the EXACT HTML structure with all attributes, classes, and text
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
    print("🔬 EXACT DOM STRUCTURE DETECTION")
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
            
            print("🔍 Extracting exact DOM structures...\n")
            
            # Extract precise DOM details
            dom_structures = await page.evaluate("""
                () => {
                    const structures = {
                        timestamp: new Date().toISOString(),
                        page_url: window.location.href,
                        elements: {}
                    };
                    
                    // Helper to get element info with EXACT structure
                    function getElementDetails(element, name) {
                        if (!element) return null;
                        
                        // Get all text nodes (excluding style tags)
                        const getCleanText = (el) => {
                            let text = '';
                            el.childNodes.forEach(node => {
                                if (node.nodeType === 3) { // Text node
                                    text += node.textContent;
                                } else if (node.nodeType === 1 && node.tagName !== 'STYLE') {
                                    text += getCleanText(node);
                                }
                            });
                            return text.trim();
                        };
                        
                        return {
                            name: name,
                            html: element.outerHTML.substring(0, 1000),
                            tag: element.tagName,
                            id: element.id,
                            className: element.className,
                            attributes: Array.from(element.attributes).map(attr => ({
                                name: attr.name,
                                value: attr.value
                            })),
                            text_content: element.textContent.trim(),
                            clean_text: getCleanText(element),
                            inner_text: element.innerText,
                            children_count: element.children.length,
                            children: Array.from(element.children).slice(0, 5).map(child => ({
                                tag: child.tagName,
                                id: child.id,
                                className: child.className,
                                text: child.textContent.trim().substring(0, 100)
                            })),
                            data_attributes: Array.from(element.attributes)
                                .filter(attr => attr.name.startsWith('data-'))
                                .map(attr => ({ name: attr.name, value: attr.value }))
                        };
                    }
                    
                    // 1. DEPARTMENT FILTER - Exact structure
                    const deptFilter = document.querySelector('.ant-dropdown-trigger');
                    structures.elements['1_department_filter'] = getElementDetails(deptFilter, 'Department Filter');
                    
                    // Find the inner div with id="departments"
                    if (deptFilter) {
                        const deptDiv = deptFilter.querySelector('#departments');
                        structures.elements['1a_department_inner'] = getElementDetails(deptDiv, 'Department Inner Div');
                        
                        // Find the ellipsis div
                        const ellipsisDiv = deptFilter.querySelector('[id^="antd-pro-ellipsis"]');
                        structures.elements['1b_department_ellipsis'] = getElementDetails(ellipsisDiv, 'Department Ellipsis');
                    }
                    
                    // 2. SEARCH BOXES
                    let searchIdx = 2;
                    document.querySelectorAll('input[type="search"], input[placeholder*="Search" i]').forEach(input => {
                        structures.elements[`${searchIdx}_search_input`] = getElementDetails(input, `Search Box ${searchIdx - 1}`);
                        searchIdx++;
                    });
                    
                    // 5. DRAFTS BUTTON
                    document.querySelectorAll('button').forEach(btn => {
                        const text = btn.textContent.trim();
                        if (text.includes('Draft')) {
                            structures.elements['5_drafts_button'] = getElementDetails(btn, 'Drafts Button');
                        } else if (text.includes('Archive')) {
                            structures.elements['6_archive_button'] = getElementDetails(btn, 'Archive Button');
                        } else if (text === 'Actions') {
                            structures.elements['7_actions_button'] = getElementDetails(btn, 'Actions Button');
                        } else if (text.includes('New Template')) {
                            structures.elements['8_new_template_button'] = getElementDetails(btn, 'New Template Button');
                        }
                    });
                    
                    // 12. PAGE SIZE DROPDOWN
                    const pageSizeDropdown = document.querySelector('[role="combobox"]');
                    structures.elements['12_page_size_dropdown'] = getElementDetails(pageSizeDropdown, 'Page Size Dropdown');
                    
                    // 13-15. TABS
                    let tabIdx = 13;
                    document.querySelectorAll('[role="tab"]').forEach(tab => {
                        structures.elements[`${tabIdx}_tab`] = getElementDetails(tab, `Tab ${tabIdx - 12}`);
                        tabIdx++;
                    });
                    
                    // 17. PAGE HEADING
                    const heading = document.querySelector('h1, h2, h3, h4');
                    if (heading) {
                        structures.elements['17_page_heading'] = getElementDetails(heading, 'Page Heading');
                    }
                    
                    // Find "Communication Templates" text
                    document.querySelectorAll('*').forEach(el => {
                        const text = el.textContent.trim();
                        if (text === 'Communication Templates' && el.children.length === 0) {
                            structures.elements['17_communication_templates_text'] = getElementDetails(el, 'Communication Templates Title');
                        }
                    });
                    
                    return structures;
                }
            """)
            
            # Save JSON
            filename = f"exact_dom_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(dom_structures, f, indent=2)
            
            # Print summary
            print("=" * 100)
            print("✅ EXACT DOM STRUCTURES EXTRACTED")
            print("=" * 100)
            
            for key, elem in sorted(dom_structures['elements'].items()):
                if elem:
                    print(f"\n{'='*100}")
                    print(f"🔍 {elem['name']}")
                    print(f"{'='*100}")
                    print(f"Tag: {elem['tag']}")
                    print(f"ID: {elem['id']}")
                    print(f"Class: {elem['className'][:100]}...")
                    print(f"Clean Text: {elem['clean_text']}")
                    print(f"Inner Text: {elem.get('inner_text', 'N/A')}")
                    
                    if elem['data_attributes']:
                        print(f"Data Attributes:")
                        for attr in elem['data_attributes']:
                            print(f"  - {attr['name']}: {attr['value']}")
                    
                    if elem['children']:
                        print(f"Children ({elem['children_count']}):")
                        for child in elem['children'][:3]:
                            print(f"  - <{child['tag']}> id=\"{child['id']}\" class=\"{child['className'][:40]}...\"")
                    
                    print(f"\nHTML Preview:")
                    print(elem['html'][:300] + "...")
            
            print("\n" + "=" * 100)
            print(f"💾 SAVED TO: {filename}")
            print("=" * 100)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
