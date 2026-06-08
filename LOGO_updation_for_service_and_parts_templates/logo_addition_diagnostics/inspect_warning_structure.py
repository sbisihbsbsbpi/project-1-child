#!/usr/bin/env python3
"""
Inspect the structure of warning icons in Service History Recap PDF
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        page = await context.new_page()
        
        template_url = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6ea2"
        print(f"Opening: {template_url}")
        await page.goto(template_url, wait_until='domcontentloaded', timeout=15000)
        print("Waiting 10 seconds for template to fully render...")
        await asyncio.sleep(10)
        
        print("\n" + "="*80)
        print("ANALYZING WARNING ICON STRUCTURE")
        print("="*80)
        
        result = await page.evaluate("""
            () => {
                const findings = [];
                
                // Check OLD selector
                const oldWarnings = document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb');
                findings.push(`\\nOLD WARNING ICONS (.templates_Image_warningIcon__hCZHMuhEmb): ${oldWarnings.length}`);
                
                oldWarnings.forEach((icon, idx) => {
                    findings.push(`\\n  Warning ${idx + 1}:`);
                    findings.push(`    Classes: ${icon.className}`);
                    
                    // Check if inside SortableItem
                    const sortableItem = icon.closest('[class*="SortableItem"]');
                    findings.push(`    Inside SortableItem: ${sortableItem !== null}`);
                    
                    if (sortableItem) {
                        findings.push(`    SortableItem classes: ${sortableItem.className}`);
                        
                        // Check if SortableItem has an image
                        const img = sortableItem.querySelector('img');
                        findings.push(`    Has image: ${img !== null}`);
                        if (img) {
                            findings.push(`    Image src: ${img.src.substring(0, 80)}...`);
                        }
                        
                        // Check if in a table cell
                        const td = sortableItem.closest('td');
                        findings.push(`    Inside table cell: ${td !== null}`);
                        if (td) {
                            const tr = td.closest('tr');
                            const cells = tr ? tr.querySelectorAll('td') : [];
                            findings.push(`    Table has ${cells.length} cells`);
                        }
                    }
                });
                
                // Check NEW selector
                const newWarnings = document.querySelectorAll('.templates_errorWarningIconsWithPopover_warningIcon__fT9Rzb2vrs');
                findings.push(`\\n\\nNEW WARNING ICONS (.templates_errorWarningIconsWithPopover_warningIcon__fT9Rzb2vrs): ${newWarnings.length}`);
                
                newWarnings.forEach((icon, idx) => {
                    findings.push(`\\n  Warning ${idx + 1}:`);
                    findings.push(`    Classes: ${icon.className}`);
                    
                    const sortableItem = icon.closest('[class*="SortableItem"]');
                    findings.push(`    Inside SortableItem: ${sortableItem !== null}`);
                    
                    // This is likely the banner at the top
                    const container = icon.parentElement;
                    findings.push(`    Parent tag: ${container.tagName}`);
                    findings.push(`    Parent classes: ${container.className}`);
                });
                
                return findings.join('\\n');
            }
        """)
        
        print(result)
        print("="*80)
        
        await page.close()

if __name__ == "__main__":
    asyncio.run(main())
