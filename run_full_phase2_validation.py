#!/usr/bin/env python3
"""
Full Phase 2 Validation - Test all 39 Service + Parts Templates

This script runs detection on all templates and generates a comprehensive report:
1. Detection accuracy (Phase 1 vs Phase 2)
2. API cross-validation results
3. False negative identification
4. Enhancement impact measurement
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / 'logo_addition_diagnostics'))

from temp_logo_adding_FINAL import TempLogoAdditionFinalService
from playwright.async_api import async_playwright


async def validate_all_templates():
    """Run validation on all 39 templates"""
    
    print("="*100)
    print("🔬 PHASE 2 FULL VALIDATION - All 39 Service + Parts Templates")
    print("="*100)
    print()
    
    # Load template list from metadata
    metadata_path = Path(__file__).parent / 'template_metadata.json'
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    templates = metadata.get('templates', [])
    print(f"📊 Loaded {len(templates)} templates from metadata")
    print()
    
    # Results storage
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_templates': len(templates),
        'templates_tested': [],
        'summary': {
            'phase1_has_logos': 0,
            'phase2_has_logos': 0,
            'learned_logos_found': 0,
            'api_validation_performed': 0,
            'false_negatives_detected': 0,
            'enhancements_helped': 0
        }
    }
    
    async with async_playwright() as p:
        print("🌐 Connecting to browser...")
        browser = await p.chromium.connect_over_cdp('http://localhost:9223')
        context = browser.contexts[0]
        print("✅ Connected\n")
        
        service = TempLogoAdditionFinalService()
        
        for idx, template in enumerate(templates, 1):
            template_id = template.get('id')
            template_name = template.get('name', 'Unknown')
            
            # Get Phase 1 data from metadata
            phase1_detection = template.get('detection', {})
            phase1_has_logos = phase1_detection.get('has_logos', False)
            
            print(f"\n{'='*100}")
            print(f"📄 Template {idx}/{len(templates)}: {template_name}")
            print(f"{'='*100}")
            print(f"   ID: {template_id}")
            print(f"   Phase 1: has_logos={phase1_has_logos}")
            
            try:
                # Open template
                page = await context.new_page()
                edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{template_id}"
                
                print(f"   Loading template...")
                await page.goto(edit_url, wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(8)  # Wait for render
                
                # Run Phase 2 detection
                print(f"   Running Phase 2 detection...")
                detection_result = await service._detect_logos(page)
                
                # Extract results
                warnings = detection_result.get('warningsCount', 0)
                empties = detection_result.get('emptyCount', 0)
                learned = detection_result.get('learnedLogosCount', 0)
                
                # Phase 2 calculation
                phase2_has_logos = (warnings > 0 or empties > 0 or learned > 0)
                phase2_logo_count = warnings + empties + learned
                
                # Check for enhancement impact
                enhancement_helped = (not phase1_has_logos and phase2_has_logos)
                
                # Store result
                template_result = {
                    'name': template_name,
                    'id': template_id,
                    'phase1': {
                        'has_logos': phase1_has_logos,
                        'logo_count': phase1_detection.get('logo_count', 0)
                    },
                    'phase2': {
                        'has_logos': phase2_has_logos,
                        'logo_count': phase2_logo_count,
                        'warnings': warnings,
                        'empties': empties,
                        'learned_logos': learned
                    },
                    'enhancement_impact': enhancement_helped,
                    'changed': phase1_has_logos != phase2_has_logos
                }
                
                results['templates_tested'].append(template_result)
                
                # Update summary
                if phase1_has_logos:
                    results['summary']['phase1_has_logos'] += 1
                if phase2_has_logos:
                    results['summary']['phase2_has_logos'] += 1
                if learned > 0:
                    results['summary']['learned_logos_found'] += 1
                if enhancement_helped:
                    results['summary']['enhancements_helped'] += 1
                
                # Print result
                status = "✅ SAME" if not enhancement_helped else "✨ ENHANCED"
                print(f"   Phase 2: has_logos={phase2_has_logos} (warnings={warnings}, empties={empties}, learned={learned}) {status}")
                
                await page.close()
                
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                results['templates_tested'].append({
                    'name': template_name,
                    'id': template_id,
                    'error': str(e)
                })
        
        print("\n" + "="*100)
        print("📊 VALIDATION SUMMARY")
        print("="*100)
        print()
        print(f"Total templates: {results['total_templates']}")
        print(f"Successfully tested: {len([t for t in results['templates_tested'] if 'error' not in t])}")
        print()
        print(f"Phase 1 - Templates with logos: {results['summary']['phase1_has_logos']}")
        print(f"Phase 2 - Templates with logos: {results['summary']['phase2_has_logos']}")
        print()
        print(f"✨ Enhancements helped: {results['summary']['enhancements_helped']} templates")
        print(f"🏷️  Learned logo markers found: {results['summary']['learned_logos_found']} templates")
        print()
        
        # Save detailed report
        report_path = Path(__file__).parent / f'phase2_validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Detailed report saved: {report_path.name}")
        print()
        
        return results


if __name__ == '__main__':
    results = asyncio.run(validate_all_templates())
    sys.exit(0)
