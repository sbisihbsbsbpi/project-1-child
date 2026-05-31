#!/usr/bin/env python3
"""
Template Edit Page - Comprehensive Element Detector
Detects ALL elements on Tekion template edit page including media tiles with checkboxes
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
    print("🔍 TEMPLATE EDIT PAGE - COMPREHENSIVE DETECTION")
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
            print(f"   {url}\n")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5)  # Wait for page to fully load
            
            print("🔍 Deep scanning template edit page...\n")
            
            # Comprehensive detection
            page_data = await page.evaluate("""
                () => {
                    const data = {
                        timestamp: new Date().toISOString(),
                        page_url: window.location.href,
                        template_id: window.location.pathname.split('/').pop(),
                        
                        // Page structure
                        page_info: {
                            title: document.title,
                            ready_state: document.readyState
                        },
                        
                        // Header/toolbar elements
                        header: {
                            buttons: [],
                            inputs: [],
                            selects: []
                        },
                        
                        // Template content area
                        template_content: {
                            has_editor: false,
                            editor_type: null,
                            images: [],
                            logos: [],
                            media_tiles: []
                        },
                        
                        // Media library / Insert Files popup
                        media_library: {
                            popup_visible: false,
                            media_tiles_with_checkboxes: [],
                            total_checkboxes: 0
                        },
                        
                        // Sidebar/panels
                        sidebars: [],
                        
                        // All buttons on page
                        all_buttons: [],
                        
                        // All inputs on page
                        all_inputs: [],
                        
                        // All checkboxes
                        all_checkboxes: [],
                        
                        // Class name analysis
                        class_analysis: {
                            template_classes: [],
                            media_classes: [],
                            tile_classes: [],
                            checkbox_classes: [],
                            editor_classes: []
                        }
                    };
                    
                    // === HEADER ELEMENTS ===
                    const header = document.querySelector('header, [role="banner"], [class*="header"]');
                    if (header) {
                        header.querySelectorAll('button').forEach(btn => {
                            data.header.buttons.push({
                                text: btn.textContent.trim(),
                                disabled: btn.disabled,
                                classes: btn.className.substring(0, 100)
                            });
                        });
                        
                        header.querySelectorAll('input').forEach(input => {
                            data.header.inputs.push({
                                type: input.type,
                                placeholder: input.placeholder,
                                value: input.value.substring(0, 100),
                                name: input.name
                            });
                        });
                        
                        header.querySelectorAll('select').forEach(select => {
                            data.header.selects.push({
                                name: select.name,
                                value: select.value,
                                options: Array.from(select.options).map(o => o.text)
                            });
                        });
                    }
                    
                    // === ALL BUTTONS ===
                    document.querySelectorAll('button').forEach((btn, idx) => {
                        if (btn.offsetParent !== null) {
                            const text = btn.textContent.trim();
                            if (text && text.length < 100) {
                                data.all_buttons.push({
                                    index: idx + 1,
                                    text: text,
                                    disabled: btn.disabled,
                                    classes: btn.className.substring(0, 150),
                                    aria_label: btn.getAttribute('aria-label')
                                });
                            }
                        }
                    });
                    
                    // === ALL INPUTS ===
                    document.querySelectorAll('input').forEach((input, idx) => {
                        if (input.offsetParent !== null) {
                            data.all_inputs.push({
                                index: idx + 1,
                                type: input.type,
                                placeholder: input.placeholder || '',
                                value: input.value ? input.value.substring(0, 100) : '',
                                name: input.name || '',
                                id: input.id || '',
                                classes: input.className.substring(0, 150)
                            });
                        }
                    });
                    
                    // === ALL CHECKBOXES (THE IMPORTANT ONE!) ===
                    document.querySelectorAll('input[type="checkbox"]').forEach((checkbox, idx) => {
                        const wrapper = checkbox.closest('.ant-checkbox-wrapper, label');
                        const mediaTileWrapper = checkbox.closest('[class*="mediaTile"]');
                        const checkboxWrapper = checkbox.closest('[class*="checkboxWrapper"]');
                        
                        const checkboxData = {
                            index: idx + 1,
                            checked: checkbox.checked,
                            value: checkbox.value,
                            data_test: checkbox.getAttribute('data-test') || '',
                            data_test_id: checkbox.getAttribute('data-test-id') || '',
                            
                            // Parent info
                            wrapper_classes: wrapper?.className.substring(0, 200) || '',
                            checkbox_wrapper_classes: checkboxWrapper?.className.substring(0, 200) || '',
                            media_tile_classes: mediaTileWrapper?.className.substring(0, 200) || '',
                            
                            // HTML snippets
                            checkbox_html: checkbox.outerHTML.substring(0, 300),
                            wrapper_html: wrapper?.outerHTML.substring(0, 500) || '',
                            
                            // Special detection
                            is_media_tile_checkbox: checkboxWrapper?.className.includes('mediaTile_checkboxWrapper') || false,
                            has_flex_grow_parent: checkbox.closest('.d-flex.flex-grow-1.align-self-center') !== null
                        };
                        
                        data.all_checkboxes.push(checkboxData);
                        
                        // If this is a media tile checkbox, add to special list
                        if (checkboxData.is_media_tile_checkbox || checkboxData.has_flex_grow_parent) {
                            data.media_library.media_tiles_with_checkboxes.push(checkboxData);
                        }
                    });
                    
                    data.media_library.total_checkboxes = data.all_checkboxes.length;

                    // === IMAGES AND LOGOS ===
                    document.querySelectorAll('img').forEach((img, idx) => {
                        if (img.offsetParent !== null) {
                            const imgData = {
                                index: idx + 1,
                                src: img.src.substring(0, 200),
                                alt: img.alt,
                                width: img.width,
                                height: img.height,
                                classes: img.className.substring(0, 150),

                                // Check if it's in a media tile
                                in_media_tile: img.closest('[class*="mediaTile"]') !== null,

                                // Check for warning icon
                                is_warning_icon: img.className.includes('warning') ||
                                                img.src.includes('warning') ||
                                                img.alt.includes('warning'),

                                // Parent container info
                                parent_classes: img.parentElement?.className.substring(0, 150) || ''
                            };

                            data.template_content.images.push(imgData);

                            // Check if this looks like a logo
                            if (img.src.includes('logo') || img.alt.includes('logo') ||
                                img.src.includes('media') || imgData.in_media_tile) {
                                data.template_content.logos.push(imgData);
                            }
                        }
                    });

                    // === MEDIA TILES ===
                    const mediaTileSelectors = [
                        '[class*="mediaTile"]',
                        '[class*="media-tile"]',
                        '[class*="imageTile"]'
                    ];

                    mediaTileSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach((tile, idx) => {
                            if (tile.offsetParent !== null) {
                                const checkbox = tile.querySelector('input[type="checkbox"]');
                                const img = tile.querySelector('img');

                                data.template_content.media_tiles.push({
                                    index: idx + 1,
                                    selector: selector,
                                    classes: tile.className.substring(0, 200),
                                    has_checkbox: checkbox !== null,
                                    checkbox_checked: checkbox ? checkbox.checked : false,
                                    has_image: img !== null,
                                    image_src: img ? img.src.substring(0, 200) : null,
                                    html_snippet: tile.outerHTML.substring(0, 600)
                                });
                            }
                        });
                    });

                    // === EDITOR DETECTION ===
                    const editorSelectors = [
                        '.ql-editor',              // Quill
                        '.tox-edit-area',          // TinyMCE
                        '[contenteditable="true"]', // Generic
                        '.ProseMirror',            // ProseMirror
                        '.CodeMirror',             // CodeMirror
                        'iframe[class*="editor"]'  // iFrame editors
                    ];

                    editorSelectors.forEach(selector => {
                        const editor = document.querySelector(selector);
                        if (editor) {
                            data.template_content.has_editor = true;
                            data.template_content.editor_type = selector;
                        }
                    });

                    // === CLASS NAME ANALYSIS ===
                    const allElements = document.querySelectorAll('*');
                    const seenClasses = {
                        template: new Set(),
                        media: new Set(),
                        tile: new Set(),
                        checkbox: new Set(),
                        editor: new Set()
                    };

                    allElements.forEach(el => {
                        const className = el.className;
                        if (typeof className === 'string' && className.length > 0) {
                            if (className.includes('template') && !seenClasses.template.has(className)) {
                                seenClasses.template.add(className.substring(0, 150));
                            }
                            if (className.includes('media') && !seenClasses.media.has(className)) {
                                seenClasses.media.add(className.substring(0, 150));
                            }
                            if (className.includes('tile') && !seenClasses.tile.has(className)) {
                                seenClasses.tile.add(className.substring(0, 150));
                            }
                            if (className.includes('checkbox') && !seenClasses.checkbox.has(className)) {
                                seenClasses.checkbox.add(className.substring(0, 150));
                            }
                            if (className.includes('editor') && !seenClasses.editor.has(className)) {
                                seenClasses.editor.add(className.substring(0, 150));
                            }
                        }
                    });

                    data.class_analysis.template_classes = Array.from(seenClasses.template);
                    data.class_analysis.media_classes = Array.from(seenClasses.media);
                    data.class_analysis.tile_classes = Array.from(seenClasses.tile);
                    data.class_analysis.checkbox_classes = Array.from(seenClasses.checkbox);
                    data.class_analysis.editor_classes = Array.from(seenClasses.editor);

                    // === POPUPS/MODALS ===
                    const modals = document.querySelectorAll('[role="dialog"], .ant-modal, .modal');
                    data.media_library.popup_visible = modals.length > 0 &&
                        Array.from(modals).some(m => m.offsetParent !== null);

                    return data;
                }
            """)

            # Save to JSON
            filename = f"template_edit_page_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(page_data, f, indent=2)

            print(f"✅ Saved to: {filename}\n")

            # Print comprehensive summary
            print("=" * 100)
            print("📊 DETECTION RESULTS")
            print("=" * 100)

            print(f"\n📄 PAGE INFO:")
            print(f"   Title: {page_data['page_info']['title']}")
            print(f"   Template ID: {page_data['template_id']}")
            print(f"   Ready State: {page_data['page_info']['ready_state']}")

            print(f"\n🔘 BUTTONS DETECTED: {len(page_data['all_buttons'])}")
            for btn in page_data['all_buttons'][:20]:  # Show first 20
                status = "🔒" if btn['disabled'] else "✅"
                print(f"   {status} {btn['text']}")

            print(f"\n📝 INPUT FIELDS: {len(page_data['all_inputs'])}")
            for inp in page_data['all_inputs'][:15]:
                print(f"   Type: {inp['type']}, Placeholder: {inp['placeholder'][:40]}")

            print(f"\n\n☑️  CHECKBOXES DETECTED: {len(page_data['all_checkboxes'])}")
            print("=" * 100)
            for cb in page_data['all_checkboxes']:
                print(f"\n   Checkbox #{cb['index']}:")
                print(f"      Checked: {'✅' if cb['checked'] else '❌'}")
                if cb['is_media_tile_checkbox']:
                    print(f"      🎯 MEDIA TILE CHECKBOX! ⭐")
                if cb['has_flex_grow_parent']:
                    print(f"      🎯 HAS FLEX-GROW PARENT! ⭐")
                if cb['wrapper_classes']:
                    print(f"      Wrapper: {cb['wrapper_classes'][:80]}")
                if cb['checkbox_wrapper_classes']:
                    print(f"      Checkbox Wrapper: {cb['checkbox_wrapper_classes'][:80]}")
                if cb['data_test_id']:
                    print(f"      Data-test-id: {cb['data_test_id']}")

            if page_data['media_library']['media_tiles_with_checkboxes']:
                print(f"\n\n🎯 MEDIA TILE CHECKBOXES FOUND: {len(page_data['media_library']['media_tiles_with_checkboxes'])}")
                print("=" * 100)
                for cb in page_data['media_library']['media_tiles_with_checkboxes']:
                    print(f"\n   ⭐ Media Tile Checkbox #{cb['index']}:")
                    print(f"      Checked: {'✅' if cb['checked'] else '❌'}")
                    print(f"      Wrapper Classes: {cb['checkbox_wrapper_classes'][:80]}")

            print(f"\n\n🖼️  IMAGES: {len(page_data['template_content']['images'])}")
            print(f"   Logos: {len(page_data['template_content']['logos'])}")
            for logo in page_data['template_content']['logos'][:5]:
                print(f"      • {logo['src'][:80]}")

            print(f"\n🎨 MEDIA TILES: {len(page_data['template_content']['media_tiles'])}")
            for tile in page_data['template_content']['media_tiles']:
                print(f"   Tile #{tile['index']}: Checkbox={'✅' if tile['has_checkbox'] else '❌'}, Image={'✅' if tile['has_image'] else '❌'}")

            print(f"\n✏️  EDITOR:")
            print(f"   Has Editor: {'✅' if page_data['template_content']['has_editor'] else '❌'}")
            if page_data['template_content']['has_editor']:
                print(f"   Editor Type: {page_data['template_content']['editor_type']}")

            print(f"\n🔍 CLASS ANALYSIS:")
            print(f"   Template classes: {len(page_data['class_analysis']['template_classes'])}")
            print(f"   Media classes: {len(page_data['class_analysis']['media_classes'])}")
            print(f"   Tile classes: {len(page_data['class_analysis']['tile_classes'])}")
            print(f"   Checkbox classes: {len(page_data['class_analysis']['checkbox_classes'])}")
            print(f"   Editor classes: {len(page_data['class_analysis']['editor_classes'])}")

            if page_data['class_analysis']['media_classes']:
                print(f"\n   Media classes found:")
                for cls in page_data['class_analysis']['media_classes'][:10]:
                    print(f"      • {cls}")

            print("\n" + "=" * 100)
            print(f"✅ Complete data saved to: {filename}")
            print("=" * 100)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

