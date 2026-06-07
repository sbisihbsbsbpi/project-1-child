#!/usr/bin/env python3
"""
Highlight Logo Containers vs Non-Logo Elements
==============================================
GREEN = Real logo containers (keep)
RED = Non-logo elements (filter out)
"""

import asyncio
from playwright.async_api import async_playwright

async def highlight_elements():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        
        if not context.pages:
            page = await context.new_page()
        else:
            page = context.pages[0]

        # Navigate to template if not already there
        current_url = page.url
        template_url = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6e48"

        if 'templates/edit' not in current_url:
            print(f"📍 Navigating to template...")
            await page.goto(template_url)
            await page.wait_for_timeout(5000)
        else:
            print(f"📍 Already on template page, waiting for content...")
            await page.wait_for_timeout(2000)

        print("🎨 Highlighting logo containers vs non-logo elements...")
        print("=" * 80)
        
        # Apply highlighting
        result = await page.evaluate("""
            () => {
                const results = {
                    logoContainers: [],
                    nonLogoElements: [],
                    totalTables: 0,
                    debugInfo: []
                };

                // Find ALL tables with 4 or 5 columns
                const allTables = Array.from(document.querySelectorAll('table'));
                results.totalTables = allTables.length;
                
                allTables.forEach((table, idx) => {
                    const firstRow = table.querySelector('tr');
                    if (!firstRow) return;
                    
                    const cells = Array.from(firstRow.querySelectorAll('td'));
                    
                    if (cells.length === 4 || cells.length === 5) {
                        // Check if this is a LOGO container or NON-LOGO element
                        
                        // RED FLAGS (Non-Logo):
                        const hasDynamicLinks = table.querySelector('.dynamic_tag_link') !== null;
                        const hasViewSurvey = table.textContent.includes('View Survey');
                        const hasGetDirections = table.textContent.includes('Get Directions');
                        const hasCallUs = table.textContent.includes('Call us') || table.textContent.includes('Call Us');
                        const hasIconButton = table.querySelector('[class*="iconButton"]') !== null;
                        
                        // Check if cells have logo-related content
                        const hasImageComponent = table.querySelector('.templates_Image_imageComponent__tqwK7j9G7t') !== null;
                        const hasTextTemplate = table.querySelector('.TEXT_TEMPLATE[contenteditable="true"]') !== null;
                        
                        const isNonLogo = hasDynamicLinks || hasViewSurvey || hasGetDirections || hasCallUs || hasIconButton;
                        const isLogoContainer = !isNonLogo && (hasImageComponent || hasTextTemplate);
                        
                        if (isLogoContainer) {
                            // ✅ GREEN = Logo container
                            table.style.outline = '8px solid lime';
                            table.style.backgroundColor = 'rgba(0, 255, 0, 0.2)';
                            table.style.boxShadow = '0 0 30px lime';
                            
                            // Add label
                            const label = document.createElement('div');
                            label.style.cssText = `
                                position: absolute;
                                top: -35px;
                                left: 0;
                                background: lime;
                                color: black;
                                padding: 8px 16px;
                                font-size: 14px;
                                font-weight: bold;
                                border: 3px solid black;
                                z-index: 999999;
                                font-family: monospace;
                            `;
                            label.textContent = `✅ LOGO CONTAINER #${results.logoContainers.length + 1}`;
                            table.style.position = 'relative';
                            table.appendChild(label);
                            
                            results.logoContainers.push({
                                index: idx,
                                columns: cells.length,
                                hasImageComponent: hasImageComponent,
                                hasTextTemplate: hasTextTemplate
                            });
                            
                        } else if (isNonLogo) {
                            // ❌ RED = Non-logo element
                            table.style.outline = '8px solid red';
                            table.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
                            table.style.boxShadow = '0 0 30px red';
                            
                            // Add label with reason
                            let reason = '';
                            if (hasDynamicLinks) reason = 'Dynamic Links';
                            else if (hasViewSurvey) reason = 'View Survey';
                            else if (hasGetDirections) reason = 'Get Directions';
                            else if (hasCallUs) reason = 'Call Us';
                            else if (hasIconButton) reason = 'Icon Button';
                            
                            const label = document.createElement('div');
                            label.style.cssText = `
                                position: absolute;
                                top: -35px;
                                left: 0;
                                background: red;
                                color: white;
                                padding: 8px 16px;
                                font-size: 14px;
                                font-weight: bold;
                                border: 3px solid black;
                                z-index: 999999;
                                font-family: monospace;
                            `;
                            label.textContent = `❌ FILTERED: ${reason}`;
                            table.style.position = 'relative';
                            table.appendChild(label);
                            
                            results.nonLogoElements.push({
                                index: idx,
                                columns: cells.length,
                                reason: reason
                            });
                        }
                    }
                });
                
                // Add legend
                const legend = document.createElement('div');
                legend.style.cssText = `
                    position: fixed;
                    top: 80px;
                    right: 20px;
                    background: white;
                    border: 4px solid black;
                    border-radius: 8px;
                    padding: 20px;
                    z-index: 9999999;
                    font-family: monospace;
                    font-size: 14px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                `;
                legend.innerHTML = `
                    <div style="font-weight: bold; margin-bottom: 12px; font-size: 18px; text-align: center;">
                        🎯 LOGO DETECTION
                    </div>
                    <div style="margin: 10px 0; padding: 10px; background: rgba(0,255,0,0.2); border-left: 6px solid lime;">
                        <strong>✅ GREEN</strong> = Logo Container<br>
                        <span style="font-size: 12px;">Keep for processing</span>
                    </div>
                    <div style="margin: 10px 0; padding: 10px; background: rgba(255,0,0,0.2); border-left: 6px solid red;">
                        <strong>❌ RED</strong> = Filtered Out<br>
                        <span style="font-size: 12px;">Not a logo container</span>
                    </div>
                    <div style="margin-top: 15px; padding-top: 12px; border-top: 2px solid #ccc; font-size: 13px;">
                        <strong>Results:</strong><br>
                        ✅ Logo Containers: ${results.logoContainers.length}<br>
                        ❌ Filtered: ${results.nonLogoElements.length}
                    </div>
                `;
                document.body.appendChild(legend);
                
                return results;
            }
        """)
        
        print(f"✅ Highlighting complete!\n")
        print(f"📊 Results:")
        print(f"   Total tables found: {result.get('totalTables', 0)}")
        print(f"   ✅ Logo Containers: {len(result['logoContainers'])}")
        print(f"   ❌ Filtered Out: {len(result['nonLogoElements'])}")
        print()
        
        if result['logoContainers']:
            print("✅ LOGO CONTAINERS (GREEN):")
            for i, container in enumerate(result['logoContainers'], 1):
                print(f"   {i}. Table {container['index']} - {container['columns']} columns")
                print(f"      Image Component: {container['hasImageComponent']}")
                print(f"      Text Template: {container['hasTextTemplate']}")
        
        print()
        
        if result['nonLogoElements']:
            print("❌ FILTERED OUT (RED):")
            for i, element in enumerate(result['nonLogoElements'], 1):
                print(f"   {i}. Table {element['index']} - {element['columns']} columns - Reason: {element['reason']}")
        
        print()
        print("🎨 Check the browser to see the visual highlights!")
        print("   GREEN = Logo containers to process")
        print("   RED = Elements to filter out")

if __name__ == "__main__":
    asyncio.run(highlight_elements())
