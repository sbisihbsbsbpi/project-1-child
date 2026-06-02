#!/usr/bin/env python3
"""
Find the correct CSS selector for warning icons in Service History Recap PDF template
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
        
        # Search for warning-related elements
        print("\n" + "="*80)
        print("SEARCHING FOR WARNING ICONS...")
        print("="*80)
        
        result = await page.evaluate("""
            () => {
                const findings = [];
                
                // 1. Check for old selector
                const oldSelector = document.querySelectorAll('.templates_Image_warningIcon__hCZHMuhEmb');
                findings.push(`Old selector (.templates_Image_warningIcon__hCZHMuhEmb): ${oldSelector.length} found`);
                
                // 2. Check for any element with 'warning' in class
                const anyWarning = document.querySelectorAll('[class*="warning" i], [class*="Warning" i]');
                findings.push(`Any warning class: ${anyWarning.length} found`);
                if (anyWarning.length > 0) {
                    Array.from(anyWarning).slice(0, 3).forEach((el, i) => {
                        findings.push(`  [${i+1}] Tag: ${el.tagName}, Classes: ${el.className}`);
                    });
                }
                
                // 3. Check for SVG icons with warning/alert
                const svgIcons = document.querySelectorAll('svg[class*="icon"], svg[aria-label*="warning" i]');
                findings.push(`SVG icons: ${svgIcons.length} found`);
                if (svgIcons.length > 0) {
                    Array.from(svgIcons).slice(0, 3).forEach((el, i) => {
                        findings.push(`  [${i+1}] Classes: ${el.className.baseVal || el.className}, aria-label: ${el.getAttribute('aria-label')}`);
                    });
                }
                
                // 4. Check for Ant Design alert/warning components
                const antWarning = document.querySelectorAll('.ant-alert, .ant-notification, [class*="alert"]');
                findings.push(`Ant Design warnings: ${antWarning.length} found`);
                
                // 5. Look for images with specific src patterns
                const images = document.querySelectorAll('img');
                const suspiciousImages = [];
                images.forEach(img => {
                    if (img.src && (img.src.includes('nucar') || img.src.includes('warning') || img.src.includes('error'))) {
                        suspiciousImages.push({
                            src: img.src,
                            classes: img.className,
                            parent: img.parentElement ? img.parentElement.className : 'no parent'
                        });
                    }
                });
                findings.push(`Images with nucar/warning: ${suspiciousImages.length} found`);
                if (suspiciousImages.length > 0) {
                    suspiciousImages.slice(0, 3).forEach((img, i) => {
                        findings.push(`  [${i+1}] src: ${img.src.substring(0, 100)}...`);
                        findings.push(`      classes: ${img.classes}`);
                        findings.push(`      parent: ${img.parent}`);
                    });
                }
                
                // 6. Check for all classes containing 'Image'
                const imageClasses = document.querySelectorAll('[class*="Image"]');
                findings.push(`Elements with 'Image' in class: ${imageClasses.length} found`);
                const uniqueClasses = new Set();
                imageClasses.forEach(el => {
                    const classList = el.className.split(' ');
                    classList.forEach(cls => {
                        if (cls.includes('Image')) uniqueClasses.add(cls);
                    });
                });
                findings.push(`  Unique Image classes: ${Array.from(uniqueClasses).join(', ')}`);
                
                return findings.join('\\n');
            }
        """)
        
        print(result)
        print("="*80)
        
        await page.close()

if __name__ == "__main__":
    asyncio.run(main())
