#!/usr/bin/env python3
"""
Template Editor Elements Detector
Detects contenteditable fields, sortable items, table cells, and all editable components
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
    print("📝 TEMPLATE EDITOR - EDITABLE ELEMENTS DETECTION")
    print("=" * 100)
    
    template_id = "667f0befd4964026ee7b6e48"
    url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print("✅ Connected to browser\n")
            
            context = browser.contexts[0]
            page = await context.new_page()
            
            print(f"🌐 Navigating to edit page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5)
            
            print("🔍 Detecting editable elements...\n")
            
            # Comprehensive detection
            editor_data = await page.evaluate("""
                () => {
                    const data = {
                        timestamp: new Date().toISOString(),
                        
                        // Contenteditable elements
                        contenteditable_elements: [],
                        
                        // TEXT_TEMPLATE elements
                        text_template_elements: [],
                        
                        // Sortable items
                        sortable_items: [],
                        
                        // Table structure
                        tables: {
                            total_tables: 0,
                            rows: [],
                            cells: []
                        },
                        
                        // All editable regions
                        all_editables: [],
                        
                        // Focus nodes
                        focus_nodes: [],
                        
                        // Container structure
                        element_containers: []
                    };
                    
                    // === 1. CONTENTEDITABLE ELEMENTS ===
                    document.querySelectorAll('[contenteditable="true"]').forEach((el, idx) => {
                        data.contenteditable_elements.push({
                            index: idx + 1,
                            id: el.id,
                            classes: el.className.substring(0, 150),
                            content: el.textContent.trim().substring(0, 100),
                            placeholder: el.getAttribute('placeholder') || '',
                            data_offset: el.getAttribute('data-offset'),
                            parent_id: el.parentElement?.id || '',
                            parent_classes: el.parentElement?.className.substring(0, 100) || '',
                            cursor_style: window.getComputedStyle(el).cursor,
                            height: window.getComputedStyle(el).height,
                            html_snippet: el.outerHTML.substring(0, 400)
                        });
                    });
                    
                    // === 2. TEXT_TEMPLATE CLASS ELEMENTS ===
                    document.querySelectorAll('.TEXT_TEMPLATE').forEach((el, idx) => {
                        data.text_template_elements.push({
                            index: idx + 1,
                            id: el.id,
                            classes: el.className,
                            is_focus_node: el.classList.contains('focus_node'),
                            contenteditable: el.getAttribute('contenteditable'),
                            placeholder: el.getAttribute('placeholder') || '',
                            content: el.textContent.trim().substring(0, 100),
                            data_offset: el.getAttribute('data_offset')
                        });
                    });
                    
                    // === 3. SORTABLE ITEMS ===
                    document.querySelectorAll('[class*="SortableItem"]').forEach((el, idx) => {
                        const container = el.querySelector('[class*="elementContainer"]');
                        const crossIcon = el.querySelector('.icon-cross');
                        const editableDiv = el.querySelector('[contenteditable="true"]');
                        
                        data.sortable_items.push({
                            index: idx + 1,
                            classes: el.className.substring(0, 150),
                            has_container: container !== null,
                            has_cross_icon: crossIcon !== null,
                            cross_icon_hidden: crossIcon?.classList.contains('hidden') || 
                                              crossIcon?.className.includes('hidden'),
                            has_editable: editableDiv !== null,
                            editable_id: editableDiv?.id || '',
                            content: editableDiv?.textContent.trim().substring(0, 100) || ''
                        });
                    });
                    
                    // === 4. TABLE STRUCTURE ===
                    const tables = document.querySelectorAll('table');
                    data.tables.total_tables = tables.length;
                    
                    tables.forEach((table, tableIdx) => {
                        const rows = table.querySelectorAll('tr');
                        
                        rows.forEach((row, rowIdx) => {
                            const cells = row.querySelectorAll('td, th');
                            const rowData = {
                                table_index: tableIdx + 1,
                                row_index: rowIdx + 1,
                                cell_count: cells.length,
                                cells: []
                            };
                            
                            cells.forEach((cell, cellIdx) => {
                                const editable = cell.querySelector('[contenteditable="true"]');
                                const sortableItem = cell.querySelector('[class*="SortableItem"]');
                                
                                const cellData = {
                                    cell_index: cellIdx + 1,
                                    has_editable: editable !== null,
                                    editable_id: editable?.id || '',
                                    editable_class: editable?.className.substring(0, 80) || '',
                                    has_sortable_item: sortableItem !== null,
                                    content: editable?.textContent.trim().substring(0, 100) || 
                                            cell.textContent.trim().substring(0, 100),
                                    cell_classes: cell.className.substring(0, 100)
                                };
                                
                                rowData.cells.push(cellData);
                                data.tables.cells.push(cellData);
                            });
                            
                            data.tables.rows.push(rowData);
                        });
                    });
                    
                    // === 5. FOCUS NODES ===
                    document.querySelectorAll('.focus_node').forEach((el, idx) => {
                        data.focus_nodes.push({
                            index: idx + 1,
                            id: el.id,
                            classes: el.className.substring(0, 100),
                            contenteditable: el.getAttribute('contenteditable'),
                            content: el.textContent.trim().substring(0, 100)
                        });
                    });
                    
                    // === 6. ELEMENT CONTAINERS ===
                    document.querySelectorAll('[class*="elementContainer"]').forEach((el, idx) => {
                        data.element_containers.push({
                            index: idx + 1,
                            classes: el.className.substring(0, 150),
                            children_count: el.children.length,
                            has_editable: el.querySelector('[contenteditable="true"]') !== null
                        });
                    });
                    
                    // === 7. ALL EDITABLES (ANY TYPE) ===
                    const editableSelectors = [
                        '[contenteditable="true"]',
                        'textarea',
                        'input[type="text"]',
                        '.editable',
                        '[class*="editable"]'
                    ];
                    
                    editableSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => {
                            const type = el.tagName.toLowerCase() === 'div' ? 'contenteditable' : el.tagName.toLowerCase();
                            data.all_editables.push({
                                type: type,
                                id: el.id || '',
                                classes: el.className.substring(0, 100),
                                value: el.value || el.textContent?.trim().substring(0, 100) || ''
                            });
                        });
                    });
                    
                    // Remove duplicates from all_editables
                    const seen = new Set();
                    data.all_editables = data.all_editables.filter(item => {
                        const key = `${item.type}-${item.id}-${item.classes}`;
                        if (seen.has(key)) return false;
                        seen.add(key);
                        return true;
                    });
                    
                    return data;
                }
            """)

            # Save to JSON
            filename = f"template_editor_elements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(editor_data, f, indent=2)

            print(f"✅ Saved to: {filename}\n")

            # Print comprehensive summary
            print("=" * 100)
            print("📊 EDITOR ELEMENTS DETECTION RESULTS")
            print("=" * 100)

            print(f"\n📝 CONTENTEDITABLE ELEMENTS: {len(editor_data['contenteditable_elements'])}")
            for el in editor_data['contenteditable_elements'][:10]:
                print(f"\n   Element #{el['index']}:")
                print(f"      ID: {el['id']}")
                print(f"      Classes: {el['classes'][:70]}")
                print(f"      Content: {el['content'][:60] if el['content'] else '(empty)'}")
                print(f"      Placeholder: {el['placeholder']}")
                print(f"      Cursor: {el['cursor_style']}")

            print(f"\n\n📋 TEXT_TEMPLATE ELEMENTS: {len(editor_data['text_template_elements'])}")
            for el in editor_data['text_template_elements'][:10]:
                focus = "✓ FOCUS" if el['is_focus_node'] else ""
                print(f"   #{el['index']}: ID={el['id'][:30]} {focus}")

            print(f"\n\n🔀 SORTABLE ITEMS: {len(editor_data['sortable_items'])}")
            for item in editor_data['sortable_items'][:10]:
                editable = "✅" if item['has_editable'] else "❌"
                cross = "🗙" if item['has_cross_icon'] else ""
                print(f"   Item #{item['index']}: Editable={editable} {cross}")
                if item['content']:
                    print(f"      Content: {item['content'][:50]}")

            print(f"\n\n📊 TABLE STRUCTURE:")
            print(f"   Total Tables: {editor_data['tables']['total_tables']}")
            print(f"   Total Rows: {len(editor_data['tables']['rows'])}")
            print(f"   Total Cells: {len(editor_data['tables']['cells'])}")

            if editor_data['tables']['rows']:
                print(f"\n   Table Layout:")
                for row in editor_data['tables']['rows'][:5]:
                    print(f"      Table {row['table_index']}, Row {row['row_index']}: {row['cell_count']} cells")
                    for cell in row['cells']:
                        editable = "✏️" if cell['has_editable'] else "  "
                        sortable = "🔀" if cell['has_sortable_item'] else "  "
                        print(f"         Cell {cell['cell_index']}: {editable} {sortable} ID={cell['editable_id'][:25]}")

            print(f"\n\n🎯 FOCUS NODES: {len(editor_data['focus_nodes'])}")
            for node in editor_data['focus_nodes'][:10]:
                print(f"   #{node['index']}: {node['id'][:40]}")

            print(f"\n\n📦 ELEMENT CONTAINERS: {len(editor_data['element_containers'])}")
            editable_containers = sum(1 for c in editor_data['element_containers'] if c['has_editable'])
            print(f"   Containers with editables: {editable_containers}")

            print(f"\n\n✏️ ALL EDITABLE ELEMENTS: {len(editor_data['all_editables'])}")
            by_type = {}
            for el in editor_data['all_editables']:
                by_type[el['type']] = by_type.get(el['type'], 0) + 1

            for etype, count in by_type.items():
                print(f"   {etype}: {count}")

            # Analysis
            print(f"\n\n🔍 STRUCTURE ANALYSIS:")
            print("=" * 100)

            print(f"\n📐 Template Structure Pattern:")
            print(f"   Each editable cell follows this structure:")
            print(f"   ")
            print(f"   <td>")
            print(f"     <div class='elementContainer'>")
            print(f"       <div class='sortableItemDisplayPadding'>")
            print(f"         <div class='elementUnselectable'>")
            print(f"           <div class='icon-cross hidden'>  <!-- Delete icon -->")
            print(f"           <div id='UUID' role='presentation'>")
            print(f"             <div style='width: 100%; height: auto;'>")
            print(f"               <div class='TEXT_TEMPLATE focus_node' ")
            print(f"                    id='UUID'")
            print(f"                    contenteditable='true'")
            print(f"                    placeholder=''")
            print(f"                    data-offset='0'>")
            print(f"                 [EDITABLE CONTENT HERE]")
            print(f"               </div>")
            print(f"             </div>")
            print(f"           </div>")
            print(f"         </div>")
            print(f"       </div>")
            print(f"     </div>")
            print(f"   </td>")

            print(f"\n\n📋 KEY IDENTIFIERS:")
            print(f"   ✅ Class: 'TEXT_TEMPLATE focus_node'")
            print(f"   ✅ Attribute: contenteditable='true'")
            print(f"   ✅ Attribute: data-offset='0'")
            print(f"   ✅ Each cell has unique UUID as ID")
            print(f"   ✅ Parent: SortableItem containers")
            print(f"   ✅ Delete icon: 'icon-cross' (hidden by default)")

            print("\n" + "=" * 100)
            print(f"✅ Complete data saved to: {filename}")
            print("=" * 100)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

