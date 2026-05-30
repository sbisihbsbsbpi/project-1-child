#!/usr/bin/env python3
"""
Element Navigator - Highlights elements with RED border and provides Next/Prev navigation
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page


async def main():
    template_id = '667f0befd4964026ee7b6ea4'
    
    print("=" * 100)
    print("🔍 ELEMENT NAVIGATOR - Visual Highlighting with Navigation")
    print("=" * 100)
    print()
    
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            
            url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
            page = await get_or_navigate_to_page(browser, url, wait_for_load=True)
            
            print("✅ Template editor loaded")
            await asyncio.sleep(3)
            
            # Inject the navigator UI and logic
            print("🎨 Injecting visual navigator...")
            
            # Read the JavaScript code from a separate function to avoid escaping issues
            js_code = get_navigator_javascript()
            await page.evaluate(js_code)
            
            print("✅ Navigator injected!")
            print()
            print("=" * 100)
            print("✅ NAVIGATION READY!")
            print("=" * 100)
            print()
            print("Controls:")
            print("  • Click 'NEXT →' button (or press Right Arrow key)")
            print("  • Click '← PREV' button (or press Left Arrow key)")
            print("  • Click '✕ CLOSE' to remove navigator")
            print("  • DRAG the header to move the navigator panel")
            print()
            print("🎯 First element is now highlighted in RED!")
            print("💡 Navigator panel is in top-right corner (DRAGGABLE!)")
            print()
            print("Keeping navigator active... Press Ctrl+C to exit")
            print()
            
            # Keep running
            await asyncio.sleep(3600)
            
        except KeyboardInterrupt:
            print("\n✅ Exiting (navigator remains in browser)")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


def get_navigator_javascript():
    """Returns the JavaScript code for the navigator"""
    return """
        () => {
            // Remove existing
            const existing = document.getElementById('element-navigator');
            if (existing) existing.remove();
            const existingStyle = document.getElementById('highlight-styles');
            if (existingStyle) existingStyle.remove();
            
            // Inject styles
            const style = document.createElement('style');
            style.id = 'highlight-styles';
            style.textContent = '.element-highlight { outline: 5px solid red !important; outline-offset: 3px !important; box-shadow: 0 0 20px rgba(255, 0, 0, 0.5) !important; position: relative !important; z-index: 999998 !important; } .element-highlight::before { content: attr(data-element-label); position: absolute; top: -30px; left: 0; background: red; color: white; padding: 5px 10px; border-radius: 5px; font-size: 12px; font-weight: bold; z-index: 999999; white-space: nowrap; }';
            document.head.appendChild(style);
            
            // 🎯 STEP 1: Use WHOLE PAGE (we'll filter UI controls instead of limiting to content area)
            // This is more reliable since Tekion editor structure may vary
            const contentArea = document.body;

            // 🚫 STEP 2: Define what to BLOCK
            // Learning mode: Track patterns of blocked elements for future templates
            const uiControlTexts = ['back', 'settings', 'draft', 'publish', 'save', 'preview', 'send test', 'schedule', 'activate', 'deactivate'];
            const blockReasons = {}; // Track why each element was blocked

            function shouldBlockElement(el, rect, tempIndex) {
                // Block our own navigator
                if (el.closest('#element-navigator')) return true;

                // 📊 LEARNING: Track scrollbar patterns
                if (rect.width < 20 || rect.height < 20) {
                    blockReasons[tempIndex] = 'too_small_likely_scrollbar_or_icon';
                    return true;
                }

                // 📊 LEARNING: Track scrollbar class patterns
                const classes = el.className || '';
                if (classes.includes('scroll') || classes.includes('Scroll')) {
                    blockReasons[tempIndex] = 'scrollbar_class_detected';
                    return true;
                }

                // 📊 LEARNING: Track UI control button patterns
                if (el.tagName === 'BUTTON' || el.tagName === 'A' || el.role === 'button') {
                    const text = (el.textContent || el.innerText || el.title || el.ariaLabel || '').toLowerCase().trim();

                    // Check for "back" button
                    if (text.includes('back')) {
                        blockReasons[tempIndex] = 'back_button';
                        return true;
                    }
                    // Check for "settings" button
                    if (text.includes('settings') || text.includes('setting')) {
                        blockReasons[tempIndex] = 'settings_button';
                        return true;
                    }
                    // Check for "draft" button
                    if (text.includes('draft')) {
                        blockReasons[tempIndex] = 'draft_button';
                        return true;
                    }
                    // Check for "publish" button
                    if (text.includes('publish')) {
                        blockReasons[tempIndex] = 'publish_button';
                        return true;
                    }

                    // Check for other control texts
                    for (const controlText of uiControlTexts) {
                        if (text.includes(controlText)) {
                            blockReasons[tempIndex] = 'ui_control_button_' + controlText.replace(' ', '_');
                            return true;
                        }
                    }
                }

                // 📊 LEARNING: Track fixed UI chrome
                const computed = window.getComputedStyle(el);
                if (computed.position === 'fixed' && !contentArea.contains(el)) {
                    blockReasons[tempIndex] = 'fixed_position_ui_chrome';
                    return true;
                }

                // 📊 LEARNING: Track very large containers
                if (rect.width > window.innerWidth * 0.9 && rect.height > window.innerHeight * 0.5) {
                    blockReasons[tempIndex] = 'very_large_container';
                    return true;
                }

                return false;
            }

            // 🔍 STEP 3: Find all CONTENT elements only
            const allElements = [];
            const allElementsIncludingBlocked = []; // Track ALL for learning
            const selectors = [
                'img',
                'button',
                'a[href]',
                'svg',  // Add SVG (left panel icons might be SVGs)
                '[role="button"]',  // Add role=button
                '[class*="component"]',
                '[class*="resizable"]',
                '[class*="image"]',
                '[class*="icon"]',  // Add icon classes
                '[class*="Icon"]'   // Add Icon classes (capital I)
            ];
            const found = new Set();
            let tempIndex = 0;

            selectors.forEach(sel => {
                // Search ONLY within content area
                contentArea.querySelectorAll(sel).forEach(el => {
                    if (found.has(el)) return;

                    const rect = el.getBoundingClientRect();
                    found.add(el);
                    tempIndex++;

                    let type = el.tagName.toLowerCase();
                    let details = '';

                    if (type === 'img') {
                        const src = el.src || '';
                        const match = src.match(/([a-f0-9]{24})/);
                        if (match) {
                            details = ' (' + match[1].substring(0, 8) + '...)';
                        }
                        type = 'IMAGE' + details;
                    } else if (type === 'button') {
                        const btnText = (el.textContent || '').trim().substring(0, 20);
                        details = btnText ? ' "' + btnText + '"' : '';
                        type = 'BUTTON' + details;
                    } else if (type === 'a') {
                        const linkText = (el.textContent || '').trim().substring(0, 20);
                        details = linkText ? ' "' + linkText + '"' : '';
                        type = 'LINK' + details;
                    } else if (el.className.includes('resizable')) {
                        type = 'COMPONENT';
                    }

                    const elementData = {
                        el,
                        type,
                        rect: {
                            width: rect.width,
                            height: rect.height,
                            top: rect.top,
                            left: rect.left
                        },
                        originalIndex: tempIndex,
                        blocked: false,
                        blockReason: null
                    };

                    // Apply blocking rules
                    if (shouldBlockElement(el, rect, tempIndex)) {
                        elementData.blocked = true;
                        elementData.blockReason = blockReasons[tempIndex] || 'unknown';
                        allElementsIncludingBlocked.push(elementData);
                        return; // Don't add to navigation list
                    }

                    el.setAttribute('data-nav-index', allElements.length);
                    allElements.push(elementData);
                    allElementsIncludingBlocked.push(elementData);
                });
            });

            // Store learning data globally
            window.allElementsIncludingBlocked = allElementsIncludingBlocked;
            window.blockReasons = blockReasons;

            // Log learning data to console
            console.log('🔍 ELEMENT LEARNING DATA:');
            console.log('Total elements scanned:', allElementsIncludingBlocked.length);
            console.log('Elements shown:', allElements.length);
            console.log('Elements blocked:', allElementsIncludingBlocked.filter(e => e.blocked).length);
            console.log('Block reasons:', blockReasons);
            
            window.navElements = allElements;
            window.currentIndex = 0;
            
            // Create navigator UI
            const nav = document.createElement('div');
            nav.id = 'element-navigator';
            nav.innerHTML = '<div id="nav-container" style="position:fixed;top:20px;right:20px;background:rgba(0,0,0,0.9);color:white;padding:20px;border-radius:10px;z-index:999999;min-width:300px;box-shadow:0 4px 20px rgba(0,0,0,0.5);font-family:Arial;cursor:move"><h3 id="nav-header" style="margin:0 0 15px 0;color:#ff4444;font-size:18px;cursor:move;user-select:none">🔍 Element Navigator <span style="float:right;font-size:12px;color:#aaa">(drag me)</span></h3><div style="margin-bottom:15px;padding:10px;background:rgba(255,255,255,0.1);border-radius:5px"><div style="font-size:14px"><strong>Element <span id="curr-idx">1</span> of <span id="total-idx">' + allElements.length + '</span></strong></div><div id="el-info" style="font-size:12px;color:#aaa;margin-top:5px">Ready</div></div><div style="display:flex;gap:10px;margin-bottom:10px"><button id="prev-btn" style="flex:1;padding:12px;background:#ff4444;color:white;border:none;border-radius:5px;cursor:pointer;font-weight:bold;font-size:14px">← PREV</button><button id="next-btn" style="flex:1;padding:12px;background:#ff4444;color:white;border:none;border-radius:5px;cursor:pointer;font-weight:bold;font-size:14px">NEXT →</button></div><button id="close-nav" style="width:100%;padding:10px;background:#666;color:white;border:none;border-radius:5px;cursor:pointer;font-size:12px">✕ CLOSE</button><div style="margin-top:15px;font-size:11px;background:rgba(255,68,68,0.2);padding:10px;border-radius:5px"><strong>💡 Tip:</strong> Use arrow keys ← → to navigate</div></div>';
            document.body.appendChild(nav);

            // Make navigator draggable
            const container = document.getElementById('nav-container');
            const header = document.getElementById('nav-header');
            let isDragging = false;
            let currentX;
            let currentY;
            let initialX;
            let initialY;
            let xOffset = 0;
            let yOffset = 0;

            header.addEventListener('mousedown', dragStart);
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', dragEnd);

            function dragStart(e) {
                initialX = e.clientX - xOffset;
                initialY = e.clientY - yOffset;
                if (e.target === header || e.target.closest('#nav-header')) {
                    isDragging = true;
                }
            }

            function drag(e) {
                if (isDragging) {
                    e.preventDefault();
                    currentX = e.clientX - initialX;
                    currentY = e.clientY - initialY;
                    xOffset = currentX;
                    yOffset = currentY;
                    setTranslate(currentX, currentY, container);
                }
            }

            function dragEnd(e) {
                initialX = currentX;
                initialY = currentY;
                isDragging = false;
            }

            function setTranslate(xPos, yPos, el) {
                el.style.transform = 'translate3d(' + xPos + 'px, ' + yPos + 'px, 0)';
            }
            
            // Navigation functions
            function highlight(idx) {
                document.querySelectorAll('.element-highlight').forEach(el => {
                    el.classList.remove('element-highlight');
                    el.removeAttribute('data-element-label');
                });
                
                const item = window.navElements[idx];
                item.el.classList.add('element-highlight');
                item.el.setAttribute('data-element-label', '#' + (idx + 1) + ': ' + item.type);
                item.el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                document.getElementById('curr-idx').textContent = idx + 1;
                document.getElementById('el-info').innerHTML = '<strong>' + item.type + '</strong><br>Size: ' + Math.round(item.rect.width) + 'x' + Math.round(item.rect.height) + 'px<br>Position: ' + Math.round(item.rect.top) + 'px from top';
            }
            
            function next() {
                window.currentIndex = (window.currentIndex + 1) % window.navElements.length;
                highlight(window.currentIndex);
            }
            
            function prev() {
                window.currentIndex = (window.currentIndex - 1 + window.navElements.length) % window.navElements.length;
                highlight(window.currentIndex);
            }
            
            document.getElementById('next-btn').onclick = next;
            document.getElementById('prev-btn').onclick = prev;
            document.getElementById('close-nav').onclick = () => {
                nav.remove();
                style.remove();
                document.querySelectorAll('.element-highlight').forEach(el => {
                    el.classList.remove('element-highlight');
                    el.removeAttribute('data-nav-index');
                    el.removeAttribute('data-element-label');
                });
            };
            
            document.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowRight') {
                    next();
                    e.preventDefault();
                } else if (e.key === 'ArrowLeft') {
                    prev();
                    e.preventDefault();
                }
            });
            
            // Highlight first element
            if (allElements.length > 0) {
                highlight(0);
            }
        }
    """


if __name__ == "__main__":
    asyncio.run(main())
