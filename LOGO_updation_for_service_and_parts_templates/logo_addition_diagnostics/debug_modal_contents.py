#!/usr/bin/env python3
"""
Debug Modal Contents - Inspect what's actually in the media library modal
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_modal():
    """Debug the modal contents"""
    
    print("="*100)
    print("🔍 DEBUG: Media Library Modal Contents")
    print("="*100)
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        pages = [p for p in context.pages if "/templates/edit/" in p.url]
        
        if not pages:
            print("❌ No template pages found")
            return
        
        page = pages[0]
        print(f"\n📄 Page: {page.url[:80]}")
        
        # Step 1: Find a logo container with data-learned-logo
        print("\n🔍 Finding logo container...")
        container_found = await page.query_selector('[data-learned-logo]')
        
        if not container_found:
            print("❌ No learned logo containers found")
            return
        
        print("✅ Found logo container")
        
        # Step 2: Hover on image parent
        print("\n🔍 Hovering on image parent...")
        img_parent = await page.evaluate_handle("""
            () => {
                const container = document.querySelector('[data-learned-logo]');
                if (!container) return null;
                const img = container.querySelector('img');
                return img ? img.parentElement : container;
            }
        """)
        
        if img_parent:
            await img_parent.as_element().hover(force=True)
            await page.wait_for_timeout(2000)
            print("✅ Hovered")
        
        # Step 3: Click the change icon
        print("\n🔍 Clicking change icon...")
        clicked = await page.evaluate("""
            () => {
                const container = document.querySelector('[data-learned-logo]');
                if (!container) return false;
                
                const changeIcon = container.querySelector('[aria-label="icon-switch"]') ||
                                  container.querySelector('[title="Change Image"]');
                
                if (changeIcon) {
                    changeIcon.click();
                    return true;
                }
                
                return false;
            }
        """)
        
        if not clicked:
            print("❌ Could not click change icon")
            return
        
        print("✅ Clicked change icon")
        await page.wait_for_timeout(3000)
        
        # Step 4: Inspect the modal
        print("\n📊 MODAL CONTENTS:")
        print("="*100)
        
        modal_info = await page.evaluate("""
            () => {
                const modal = document.querySelector('[role="dialog"], [class*="modal"], [class*="Modal"]');
                if (!modal) return { found: false };
                
                // Get all images in the modal
                const images = Array.from(modal.querySelectorAll('img'));
                
                return {
                    found: true,
                    imageCount: images.length,
                    images: images.map((img, idx) => ({
                        index: idx,
                        src: img.src,
                        alt: img.alt || '',
                        title: img.title || '',
                        className: img.className,
                        // Extract potential filenames from src
                        srcFilename: img.src.split('/').pop().split('?')[0],
                        // Parent info
                        parentTag: img.parentElement ? img.parentElement.tagName : '',
                        parentClass: img.parentElement ? img.parentElement.className : '',
                        // Check if it's clickable
                        isClickable: img.onclick !== null || img.style.cursor === 'pointer'
                    }))
                };
            }
        """)
        
        if not modal_info['found']:
            print("❌ Modal not found!")
            return
        
        print(f"✅ Modal found with {modal_info['imageCount']} images\n")
        
        for img in modal_info['images']:
            print(f"Image {img['index']}:")
            print(f"   src: {img['src'][:100]}{'...' if len(img['src']) > 100 else ''}")
            print(f"   srcFilename: {img['srcFilename']}")
            print(f"   alt: {img['alt']}")
            print(f"   title: {img['title']}")
            print(f"   className: {img['className'][:60] if img['className'] else '(none)'}")
            print(f"   parent: <{img['parentTag']}> (class: {img['parentClass'][:40] if img['parentClass'] else '(none)'})")
            print(f"   clickable: {img['isClickable']}")
            print()
        
        # Also check for buttons or other clickable elements
        print("\n🔍 Other clickable elements in modal:")
        print("="*100)
        
        clickables = await page.evaluate("""
            () => {
                const modal = document.querySelector('[role="dialog"], [class*="modal"], [class*="Modal"]');
                if (!modal) return [];
                
                const buttons = Array.from(modal.querySelectorAll('button, [role="button"], [class*="card"], [class*="Card"]'));
                
                return buttons.slice(0, 10).map((btn, idx) => ({
                    index: idx,
                    tag: btn.tagName,
                    text: btn.textContent.trim().substring(0, 50),
                    className: btn.className,
                    // Check if it contains an image
                    hasImage: btn.querySelector('img') !== null,
                    imageCount: btn.querySelectorAll('img').length
                }));
            }
        """)
        
        for elem in clickables:
            print(f"{elem['index']}. <{elem['tag']}> \"{elem['text']}\"")
            print(f"   class: {elem['className'][:60] if elem['className'] else '(none)'}")
            print(f"   images inside: {elem['imageCount']}")
            print()
        
        print("="*100)
        print("✅ Debug complete!")
        print("="*100)

if __name__ == "__main__":
    asyncio.run(debug_modal())
