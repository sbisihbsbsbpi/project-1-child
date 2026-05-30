#!/usr/bin/env python3
"""
Performance Test - Measure detection speed
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from playwright.async_api import async_playwright


async def main():
    print("⏱️  DETECTION PERFORMANCE TEST")
    print("=" * 60)
    
    async with async_playwright() as playwright:
        try:
            start_total = time.time()
            
            # Connect
            print("Connecting to browser...")
            start = time.time()
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
            print(f"✅ Connected in {time.time() - start:.2f}s")
            
            context = browser.contexts[0]
            page = await context.new_page()
            
            # Navigate
            print("Navigating to page...")
            start = time.time()
            await page.goto("https://preprodapp.tekioncloud.com/templates/list", 
                          wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)
            nav_time = time.time() - start
            print(f"✅ Page loaded in {nav_time:.2f}s")
            
            # Detect elements
            print("\nDetecting elements...")
            start = time.time()
            
            results = await page.evaluate("""
                () => {
                    const startTime = performance.now();
                    const detected = {
                        buttons: document.querySelectorAll('button').length,
                        divs: document.querySelectorAll('div').length,
                        inputs: document.querySelectorAll('input').length,
                        links: document.querySelectorAll('a').length,
                        tabs: document.querySelectorAll('[role="tab"]').length,
                        dropdowns: document.querySelectorAll('[role="combobox"]').length,
                        all_elements: document.querySelectorAll('*').length,
                        headings: document.querySelectorAll('h1,h2,h3,h4,h5,h6').length,
                        images: document.querySelectorAll('img').length,
                        containers: document.querySelectorAll('[class*="container"]').length
                    };
                    const endTime = performance.now();
                    detected.detection_time_ms = endTime - startTime;
                    return detected;
                }
            """)
            
            detection_time = time.time() - start
            
            print("\n" + "=" * 60)
            print("📊 RESULTS")
            print("=" * 60)
            print(f"\n⏱️  TIMING:")
            print(f"   Browser connect:    {time.time() - start_total - nav_time - detection_time:.2f}s")
            print(f"   Page navigation:    {nav_time:.2f}s")
            print(f"   Element detection:  {detection_time:.2f}s")
            print(f"   Browser eval time:  {results['detection_time_ms']:.2f}ms")
            print(f"   Total time:         {time.time() - start_total:.2f}s")
            
            print(f"\n🔍 ELEMENTS DETECTED:")
            print(f"   Total elements:     {results['all_elements']:,}")
            print(f"   DIV containers:     {results['divs']:,}")
            print(f"   Buttons:            {results['buttons']}")
            print(f"   Input fields:       {results['inputs']}")
            print(f"   Links:              {results['links']}")
            print(f"   Tabs:               {results['tabs']}")
            print(f"   Dropdowns:          {results['dropdowns']}")
            print(f"   Headings:           {results['headings']}")
            print(f"   Images:             {results['images']}")
            print(f"   Containers:         {results['containers']}")
            
            print("\n" + "=" * 60)
            print("✅ PERFORMANCE SUMMARY")
            print("=" * 60)
            print(f"Detection speed: ~{results['all_elements'] / detection_time:,.0f} elements/second")
            print(f"Browser eval:    {results['detection_time_ms']:.0f}ms (very fast!)")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
