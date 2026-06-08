#!/usr/bin/env python3
"""
Detect the Nucar logo in Service History Recap PDF and find the "Change Image" workflow
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Connect to existing browser
        browser = await p.chromium.connect_over_cdp("http://localhost:9223")
        context = browser.contexts[0]
        page = await context.new_page()
        
        # Open Service History Recap PDF
        template_url = "https://preprodapp.tekioncloud.com/templates/edit/667f0befd4964026ee7b6ea2"
        print(f"Opening: {template_url}")
        await page.goto(template_url, wait_until='domcontentloaded', timeout=15000)
        await asyncio.sleep(5)
        
        print("\n" + "="*80)
        print("SEARCHING FOR NUCAR LOGO...")
        print("="*80)
        
        result = await page.evaluate("""
            () => {
                const findings = [];
                
                // Find all images
                const allImages = document.querySelectorAll('img');
                findings.push(`Total images on page: ${allImages.length}`);
                
                // Find images with "nucar" in src
                const nucarImages = [];
                allImages.forEach((img, idx) => {
                    if (img.src && img.src.toLowerCase().includes('nucar')) {
                        nucarImages.push({
                            index: idx,
                            src: img.src,
                            alt: img.alt,
                            className: img.className,
                            width: img.width,
                            height: img.height,
                            parentClass: img.parentElement ? img.parentElement.className : 'no parent'
                        });
                    }
                });
                
                findings.push(`\\nImages with 'nucar' in src: ${nucarImages.length}`);
                nucarImages.forEach((img, i) => {
                    findings.push(`\\n[${i+1}] Nucar Image:`);
                    findings.push(`  src: ${img.src}`);
                    findings.push(`  className: ${img.className}`);
                    findings.push(`  dimensions: ${img.width}x${img.height}`);
                    findings.push(`  parent class: ${img.parentClass}`);
                });
                
                return findings.join('\\n');
            }
        """)
        
        print(result)
        print("="*80)
        
        await page.close()

if __name__ == "__main__":
    asyncio.run(main())
