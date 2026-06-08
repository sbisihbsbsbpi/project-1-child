#!/usr/bin/env python3
"""
CDP Logo Validator (Simple) - Just validate logos, don't update
================================================================

This script:
1. Connects to existing browser tabs
2. Detects logos in each template
3. Reports validation status (placeholder vs real logos)
4. Logs everything in detail

Usage:
    python3 cdp_validator_simple.py --max 5
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from playwright.async_api import async_playwright
from pathlib import Path

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"cdp_validator_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Known placeholder logos
PLACEHOLDER_LOGOS = [
    'Screenshot_2022-02-10_at_5.25.15_PM.png',
    'example',
    'placeholder',
    'sample',
    'test',
    'default'
]

def is_placeholder(filename: str) -> bool:
    """Check if filename is a known placeholder"""
    filename_lower = filename.lower()
    return any(p in filename_lower for p in PLACEHOLDER_LOGOS)

async def validate_templates(cdp_url: str = "http://localhost:9223", max_templates: int = None):
    """Validate logos in all template tabs"""
    
    logger.info("="*100)
    logger.info("🚀 CDP LOGO VALIDATOR - Starting")
    logger.info(f"📁 Log file: {log_file}")
    logger.info("="*100)
    
    results = []
    
    async with async_playwright() as playwright:
        try:
            # Connect to browser
            logger.info(f"\n🌐 Connecting to browser at {cdp_url}...")
            browser = await playwright.chromium.connect_over_cdp(cdp_url)
            
            contexts = browser.contexts
            logger.info(f"✅ Connected! Found {len(contexts)} browser context(s)")
            
            if not contexts:
                logger.error("❌ No browser contexts found")
                return
            
            context = contexts[0]
            pages = context.pages
            
            # Filter template pages
            template_pages = [p for p in pages if "/templates/edit/" in p.url]
            logger.info(f"✅ Found {len(template_pages)} template editor tab(s)")
            
            if not template_pages:
                logger.error("❌ No template editor tabs found")
                return
            
            # Limit if requested
            if max_templates:
                template_pages = template_pages[:max_templates]
                logger.info(f"📊 Processing first {max_templates} template(s)")
            
            # Process each template
            for idx, page in enumerate(template_pages, 1):
                logger.info(f"\n{'='*100}")
                logger.info(f"📄 TAB {idx}/{len(template_pages)}: {page.url}")
                logger.info(f"{'='*100}")
                
                # Extract template info
                template_id = page.url.split('/')[-1]
                title = await page.title()
                logger.info(f"📝 Template: {title}")
                logger.info(f"🆔 ID: {template_id}")
                
                # Extract detected logos
                logos = await page.evaluate("""
                    () => {
                        const containers = document.querySelectorAll('[data-learned-logo]');
                        const detected = [];
                        
                        containers.forEach((container, idx) => {
                            const img = container.querySelector('img');
                            const outline = container.style.outline;
                            
                            const isGreen = outline.includes('lime') || outline.includes('green');
                            const isPink = outline.includes('pink') || outline.includes('hotpink');
                            const isRed = outline.includes('red');
                            
                            if (img && (isGreen || isRed || isPink)) {
                                detected.push({
                                    index: idx + 1,
                                    marker: container.getAttribute('data-learned-logo'),
                                    filename: img.src.split('/').pop().split('?')[0],
                                    src: img.src.substring(0, 80),
                                    alt: img.alt || '',
                                    borderColor: isGreen ? 'green' : isPink ? 'pink' : 'red',
                                    width: Math.round(img.getBoundingClientRect().width),
                                    height: Math.round(img.getBoundingClientRect().height)
                                });
                            }
                        });
                        
                        return detected;
                    }
                """)
                
                logger.info(f"\n📊 DETECTION RESULTS:")
                logger.info(f"   • Total logos detected: {len(logos)}")
                
                if not logos:
                    logger.warning(f"   ⚠️  No logos detected in this template")
                    results.append({
                        'tab': idx,
                        'template_id': template_id,
                        'logos_count': 0,
                        'status': 'no_logos'
                    })
                    continue
                
                # Analyze each logo
                green_logos = [l for l in logos if l['borderColor'] == 'green']
                pink_logos = [l for l in logos if l['borderColor'] == 'pink']
                red_logos = [l for l in logos if l['borderColor'] == 'red']
                
                logger.info(f"   • Green borders (dealer logos): {len(green_logos)}")
                logger.info(f"   • Pink borders (UI icons): {len(pink_logos)}")
                logger.info(f"   • Red borders (warnings): {len(red_logos)}")
                
                # Check for placeholders
                placeholders = []
                real_logos = []
                
                for logo in green_logos:
                    logger.info(f"\n   🎨 Logo {logo['index']}: {logo['filename']}")
                    logger.info(f"      • Size: {logo['width']}x{logo['height']}px")
                    logger.info(f"      • Border: {logo['borderColor']}")
                    
                    if is_placeholder(logo['filename']):
                        logger.warning(f"      ⚠️  PLACEHOLDER DETECTED!")
                        placeholders.append(logo)
                    else:
                        logger.info(f"      ✅ Real logo (not a placeholder)")
                        real_logos.append(logo)
                
                # Summary for this template
                logger.info(f"\n📝 SUMMARY:")
                logger.info(f"   • Real logos: {len(real_logos)}")
                logger.info(f"   • Placeholders: {len(placeholders)}")
                logger.info(f"   • UI icons: {len(pink_logos)}")
                logger.info(f"   • Warnings: {len(red_logos)}")
                
                status = 'valid' if len(placeholders) == 0 and len(red_logos) == 0 else 'needs_update'
                
                results.append({
                    'tab': idx,
                    'template_id': template_id,
                    'logos_count': len(green_logos),
                    'placeholders': len(placeholders),
                    'warnings': len(red_logos),
                    'status': status
                })
            
            # Final summary
            logger.info(f"\n{'='*100}")
            logger.info(f"📊 FINAL SUMMARY - {len(results)} template(s) processed")
            logger.info(f"{'='*100}")
            
            for result in results:
                status_icon = '✅' if result['status'] == 'valid' else '⚠️' if result['status'] == 'needs_update' else '❌'
                logger.info(f"{status_icon} Tab {result['tab']}: {result['status'].upper()} - {result['logos_count']} logos, {result.get('placeholders', 0)} placeholders")
            
            logger.info(f"\n📁 Full log: {log_file}")
            logger.info(f"{'='*100}")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate logos in existing browser tabs')
    parser.add_argument('--max', type=int, help='Maximum number of templates to process')
    parser.add_argument('--cdp-url', default='http://localhost:9223', help='CDP URL')
    
    args = parser.parse_args()
    
    asyncio.run(validate_templates(cdp_url=args.cdp_url, max_templates=args.max))
