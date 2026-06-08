#!/usr/bin/env python3
"""
Debug Hover Target - Find the correct element to hover for logo controls
"""

import asyncio
from playwright.async_api import async_playwright

async def find_hover_target():
    """Find the correct element to hover to show logo controls"""
    
    print("="*100)
    print("🔍 DEBUG: Finding Correct Hover Target")
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
        
        # Get the full DOM structure around the logo
        print("\n🔍 Analyzing DOM structure around logo...")
        
        structure = await page.evaluate("""
            () => {
                const container = document.querySelector('[data-learned-logo]');
                if (!container) return null;
                
                const img = container.querySelector('img');
                if (!img) return null;
                
                // Walk up the DOM tree and collect parent info
                const parents = [];
                let current = container;
                let depth = 0;
                
                while (current && depth < 10) {
                    const info = {
                        depth: depth,
                        tagName: current.tagName,
                        className: current.className || '',
                        id: current.id || '',
                        hasHoverClass: current.className.toLowerCase().includes('hover') || 
                                      current.className.toLowerCase().includes('image'),
                        dataAttributes: Array.from(current.attributes)
                            .filter(attr => attr.name.startsWith('data-'))
                            .map(attr => `${attr.name}="${attr.value}"`)
                    };
                    
                    parents.push(info);
                    current = current.parentElement;
                    depth++;
                }
                
                return {
                    containerTag: container.tagName,
                    containerClass: container.className,
                    imgSrc: img.src.substring(0, 80),
                    parents: parents
                };
            }
        """)
        
        if not structure:
            print("❌ No logo structure found")
            return
        
        print(f"\nLogo Container: <{structure['containerTag']} class='{structure['containerClass']}'>")
        print(f"Image: {structure['imgSrc']}")
        print(f"\n📊 Parent hierarchy (from logo container upwards):")
        
        for parent in structure['parents']:
            indent = "  " * parent['depth']
            tag = parent['tagName']
            cls = parent['className'][:60] if parent['className'] else '(no class)'
            data_attrs = ', '.join(parent['dataAttributes'][:3]) if parent['dataAttributes'] else '(no data attrs)'
            
            print(f"{indent}↑ <{tag}> class='{cls}'")
            if parent['dataAttributes']:
                print(f"{indent}   data: {data_attrs}")
        
        # Now try hovering at different levels
        print(f"\n🔍 Testing hover at different DOM levels...")
        
        # Test 1: Hover on the container itself
        print(f"\n1️⃣ Hovering on [data-learned-logo] container...")
        await page.hover('[data-learned-logo]')
        await page.wait_for_timeout(1000)
        
        buttons1 = await page.evaluate("""
            () => {
                return Array.from(document.querySelectorAll('button'))
                    .filter(btn => btn.offsetParent !== null)
                    .map(btn => btn.textContent.trim())
                    .filter(text => text.includes('Change') || text.includes('Edit') || text.includes('Replace'));
            }
        """)
        print(f"   Buttons visible: {buttons1 if buttons1 else 'None'}")
        
        # Test 2: Hover on parent wrapper (if it exists)
        print(f"\n2️⃣ Hovering on parent of [data-learned-logo]...")
        await page.evaluate("""
            () => {
                const container = document.querySelector('[data-learned-logo]');
                if (container && container.parentElement) {
                    const parent = container.parentElement;
                    parent.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                    parent.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
                }
            }
        """)
        await page.wait_for_timeout(1000)
        
        buttons2 = await page.evaluate("""
            () => {
                return Array.from(document.querySelectorAll('button'))
                    .filter(btn => btn.offsetParent !== null)
                    .map(btn => btn.textContent.trim())
                    .filter(text => text.includes('Change') || text.includes('Edit') || text.includes('Replace'));
            }
        """)
        print(f"   Buttons visible: {buttons2 if buttons2 else 'None'}")
        
        # Test 3: Look for SortableItem wrapper
        print(f"\n3️⃣ Looking for SortableItem wrapper...")
        sortable_info = await page.evaluate("""
            () => {
                const container = document.querySelector('[data-learned-logo]');
                if (!container) return null;
                
                // Find closest SortableItem
                let current = container;
                while (current) {
                    if (current.className && current.className.includes('SortableItem')) {
                        return {
                            found: true,
                            className: current.className,
                            tagName: current.tagName
                        };
                    }
                    current = current.parentElement;
                }
                
                return { found: false };
            }
        """)
        
        if sortable_info and sortable_info['found']:
            print(f"   ✅ Found SortableItem: <{sortable_info['tagName']} class='{sortable_info['className'][:60]}'>")
            print(f"   → Trying to hover on SortableItem...")
            
            await page.evaluate("""
                () => {
                    const container = document.querySelector('[data-learned-logo]');
                    let current = container;
                    while (current) {
                        if (current.className && current.className.includes('SortableItem')) {
                            current.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                            current.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
                            break;
                        }
                        current = current.parentElement;
                    }
                }
            """)
            await page.wait_for_timeout(1000)
            
            buttons3 = await page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('button'))
                        .filter(btn => btn.offsetParent !== null)
                        .map(btn => btn.textContent.trim())
                        .filter(text => text.includes('Change') || text.includes('Edit') || text.includes('Replace'));
                }
            """)
            print(f"   Buttons visible: {buttons3 if buttons3 else 'None'}")
        else:
            print(f"   ❌ No SortableItem wrapper found")
        
        # Test 4: Check if template is in edit mode
        print(f"\n4️⃣ Checking template editor state...")
        editor_state = await page.evaluate("""
            () => {
                // Check for draft/published status
                const draftButton = document.querySelector('button:has-text("Save As Draft")');
                const publishButton = document.querySelector('button:has-text("Publish")');
                
                return {
                    hasDraftButton: draftButton !== null,
                    hasPublishButton: publishButton !== null,
                    draftVisible: draftButton ? draftButton.offsetParent !== null : false,
                    publishVisible: publishButton ? publishButton.offsetParent !== null : false
                };
            }
        """)
        
        print(f"   Draft button: {editor_state['hasDraftButton']} (visible: {editor_state['draftVisible']})")
        print(f"   Publish button: {editor_state['hasPublishButton']} (visible: {editor_state['publishVisible']})")
        
        if not editor_state['draftVisible']:
            print(f"   ⚠️  Template might be in PUBLISHED state (controls disabled)")
        
        print("\n" + "="*100)
        print("✅ Debug complete!")
        print("="*100)

if __name__ == "__main__":
    asyncio.run(find_hover_target())
