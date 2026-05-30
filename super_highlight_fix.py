#!/usr/bin/env python3
"""
Super Highlight Fix - Make highlighting IMPOSSIBLE to miss
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from cdp_utils import get_or_navigate_to_page


async def main():
    template_id = '667f0befd4964026ee7b6ea4'
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
        
        url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
        page = await get_or_navigate_to_page(browser, url, wait_for_load=True)
        
        print("🔧 Applying SUPER HIGHLIGHT...")
        
        # Apply ultra-visible highlighting
        await page.evaluate("""
            () => {
                // Remove old styles
                const oldStyle = document.getElementById('highlight-styles');
                if (oldStyle) oldStyle.remove();
                
                // Create ULTRA-VISIBLE highlight
                const style = document.createElement('style');
                style.id = 'highlight-styles';
                style.textContent = `
                    @keyframes pulse-red {
                        0%, 100% { box-shadow: 0 0 20px 10px rgba(255, 0, 0, 0.8); }
                        50% { box-shadow: 0 0 40px 20px rgba(255, 0, 0, 1); }
                    }
                    
                    .element-highlight {
                        outline: 10px solid #FF0000 !important;
                        outline-offset: 5px !important;
                        background-color: rgba(255, 0, 0, 0.15) !important;
                        position: relative !important;
                        z-index: 2147483647 !important;
                        animation: pulse-red 1.5s infinite !important;
                        box-shadow: 0 0 30px 15px rgba(255, 0, 0, 0.9) !important;
                    }
                    
                    .element-highlight::before {
                        content: attr(data-element-label);
                        position: absolute;
                        top: -45px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: linear-gradient(135deg, #FF0000 0%, #CC0000 100%);
                        color: white;
                        padding: 12px 20px;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        z-index: 2147483647;
                        white-space: nowrap;
                        box-shadow: 0 5px 20px rgba(0,0,0,0.6);
                        border: 3px solid white;
                        font-family: Arial, sans-serif;
                    }
                    
                    .element-highlight::after {
                        content: '';
                        position: absolute;
                        top: -8px;
                        left: -8px;
                        right: -8px;
                        bottom: -8px;
                        border: 4px dashed #FFFF00;
                        pointer-events: none;
                        z-index: 2147483646;
                        animation: spin 3s linear infinite;
                    }
                    
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    
                    /* Force visibility */
                    .element-highlight {
                        opacity: 1 !important;
                        visibility: visible !important;
                        display: block !important;
                    }
                `;
                document.head.appendChild(style);
                
                // Force re-highlight current element
                if (window.currentIndex !== undefined && window.navElements) {
                    const current = window.navElements[window.currentIndex];
                    if (current) {
                        current.el.classList.remove('element-highlight');
                        setTimeout(() => {
                            current.el.classList.add('element-highlight');
                            current.el.setAttribute('data-element-label', '#' + (window.currentIndex + 1) + ': ' + current.type);
                        }, 100);
                    }
                }
                
                console.log('✅ SUPER HIGHLIGHT ACTIVATED!');
                console.log('Features:');
                console.log('  - 10px RED outline');
                console.log('  - Pulsing red glow animation');
                console.log('  - Red background tint');
                console.log('  - Spinning yellow dashed border');
                console.log('  - Large centered label with gradient');
                console.log('  - Maximum z-index (always on top)');
            }
        """)
        
        print("=" * 100)
        print("✅ SUPER HIGHLIGHT ACTIVATED!")
        print("=" * 100)
        print()
        print("Features:")
        print("  🔴 10px THICK red outline")
        print("  💥 PULSING red glow animation")
        print("  🎨 Red background tint")
        print("  🌀 SPINNING yellow dashed border")
        print("  🏷️  LARGE label with gradient background")
        print("  ⬆️  Maximum z-index (always on top)")
        print()
        print("The current element should now be IMPOSSIBLE to miss!")
        print("Navigate using NEXT/PREV buttons - each element will PULSE and GLOW!")
        print()


if __name__ == "__main__":
    asyncio.run(main())
