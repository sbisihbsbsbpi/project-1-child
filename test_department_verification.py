#!/usr/bin/env python3
"""
🧪 Department Verification Test
Tests the dynamic imageComponent detection + department verification logic
"""

import asyncio
import logging
from playwright.async_api import async_playwright
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_TEMPLATE_ID = "667f0befd4964026ee7b6ea2"
CDP_URL = "http://localhost:9223"


async def test_dynamic_detection_with_department_verification(page):
    """Test the new dynamic detection logic"""
    
    logger.info("\n" + "="*100)
    logger.info("🔍 TESTING DYNAMIC LOGO DETECTION + DEPARTMENT VERIFICATION")
    logger.info("="*100)
    
    # Import the detection logic from the production script
    result = await page.evaluate("""
        () => {
            const debug = [];
            
            // ============================================================================
            // DYNAMIC DETECTION: Find ALL imageComponent containers
            // ============================================================================
            debug.push('=== DYNAMIC LOGO DETECTION (imageComponent Pattern) ===');
            
            const allImageComponents = document.querySelectorAll('[class*="imageComponent"]');
            debug.push(`Found ${allImageComponents.length} imageComponent containers`);
            
            let logoIndex = 0;
            const detectedLogos = [];
            
            // Helper function to detect logo department
            function detectLogoDepartment(container, imageComp) {
                // Strategy 1: Check for department text near the logo
                const nearbyText = container.innerText || container.textContent || '';
                const upperText = nearbyText.toUpperCase();
                
                if (upperText.includes('SERVICE')) return 'Service';
                if (upperText.includes('SALES')) return 'Sales';
                if (upperText.includes('PARTS')) return 'Parts';
                
                // Strategy 2: Check parent containers for department indicators
                let parent = container.parentElement;
                let depth = 0;
                while (parent && depth < 5) {
                    const parentText = (parent.innerText || parent.textContent || '').toUpperCase();
                    if (parentText.includes('SERVICE') && parentText.length < 1000) return 'Service';
                    if (parentText.includes('SALES') && parentText.length < 1000) return 'Sales';
                    if (parentText.includes('PARTS') && parentText.length < 1000) return 'Parts';
                    parent = parent.parentElement;
                    depth++;
                }
                
                // Strategy 3: Check logo position (header vs body)
                const rect = container.getBoundingClientRect();
                const isHeader = rect.top < 600;
                
                if (isHeader) {
                    return 'header';
                }
                
                return 'unknown';
            }
            
            allImageComponents.forEach((imageComp, idx) => {
                const sortableItem = imageComp.closest('[class*="SortableItem"]');
                
                if (!sortableItem) {
                    debug.push(`  imageComponent #${idx + 1}: No SortableItem parent found`);
                    return;
                }
                
                // Check for image
                const img = imageComp.querySelector('img');
                const hasImage = img !== null;
                
                // Check for warning icon
                const warningSelectors = [
                    '.templates_errorWarningIconsWithPopover_warningIcon__fT9Rzb2vrs',
                    '.icon-alert1',
                    '[class*="errorWarningIconsWithPopover_warningIcon"]',
                    '.templates_Image_warningIcon__hCZHMuhEmb'
                ];
                
                let hasWarning = false;
                for (const selector of warningSelectors) {
                    if (imageComp.querySelector(selector)) {
                        hasWarning = true;
                        break;
                    }
                }
                
                // Only process logos with warnings or empty containers
                if (hasWarning || !hasImage) {
                    logoIndex++;
                    
                    // Detect department
                    const department = detectLogoDepartment(sortableItem, imageComp);
                    
                    // Get position
                    const rect = sortableItem.getBoundingClientRect();
                    
                    // Mark containers
                    sortableItem.setAttribute('data-logo-to-inspect', `warning-logo-${logoIndex}`);
                    sortableItem.setAttribute('data-logo-department', department || 'unknown');
                    imageComp.setAttribute('data-imagecomponent-target', `logo-${logoIndex}`);
                    
                    const logoData = {
                        index: logoIndex,
                        status: hasWarning ? 'WARNING' : 'EMPTY',
                        department: department || 'unknown',
                        position: {
                            top: Math.round(rect.top + window.scrollY),
                            left: Math.round(rect.left)
                        },
                        hasImage: hasImage,
                        hasWarning: hasWarning,
                        containerId: sortableItem.id || 'custom-container',
                        imageSrc: img ? img.src.substring(0, 80) : null
                    };
                    
                    detectedLogos.push(logoData);
                    
                    debug.push(`  Logo #${logoIndex}: ${logoData.status} - Department: ${department || 'UNKNOWN'} at ${logoData.position.top}px`);
                } else if (hasImage) {
                    debug.push(`  imageComponent #${idx + 1}: Has image, no warning (logo is correct)`);
                }
            });
            
            return {
                success: true,
                totalImageComponents: allImageComponents.length,
                logosDetected: detectedLogos.length,
                logos: detectedLogos,
                debug: debug
            };
        }
    """)
    
    return result


async def verify_department_matching(logos, template_departments):
    """Verify that department detection would prevent cross-department updates"""

    logger.info("\n" + "="*100)
    logger.info("🔒 DEPARTMENT VERIFICATION SIMULATION")
    logger.info("="*100)
    logger.info(f"Template Departments: {', '.join(template_departments)}")
    logger.info("")

    results = {
        'allowed': [],
        'blocked': [],
        'warnings': []
    }

    for logo in logos:
        logo_dept = logo['department']

        # Check if logo department matches template departments
        if logo_dept == 'header':
            # Header logos are shared - ALLOW
            decision = 'ALLOW'
            reason = 'Header logo (shared across all departments)'
            results['allowed'].append(logo)
        elif logo_dept == 'unknown':
            # Unknown department - ALLOW with warning
            decision = 'ALLOW (with warning)'
            reason = 'Could not detect logo department'
            results['warnings'].append(logo)
        elif logo_dept in template_departments:
            # Department matches - ALLOW
            decision = 'ALLOW'
            reason = f'Department match: {logo_dept}'
            results['allowed'].append(logo)
        else:
            # Department mismatch - BLOCK
            decision = 'BLOCK'
            reason = f'Department mismatch: Logo is {logo_dept}, Template is {", ".join(template_departments)}'
            results['blocked'].append(logo)

        logger.info(f"Logo #{logo['index']}: {logo['status']} at {logo['position']['top']}px")
        logger.info(f"   Department: {logo_dept}")
        logger.info(f"   Decision: {'✅' if decision.startswith('ALLOW') else '❌'} {decision}")
        logger.info(f"   Reason: {reason}")
        logger.info("")

    return results


async def highlight_logos_by_decision(page, logos, template_departments):
    """Highlight logos with colors based on department verification decision"""

    logger.info("\n" + "="*100)
    logger.info("🎨 HIGHLIGHTING LOGOS BY DECISION")
    logger.info("="*100)

    await page.evaluate("""
        (data) => {
            const { logos, templateDepartments } = data;

            logos.forEach(logo => {
                const container = document.querySelector(`[data-logo-to-inspect="warning-logo-${logo.index}"]`);
                if (!container) return;

                const logoDept = logo.department;
                let color, label;

                // Determine color based on department verification
                if (logoDept === 'header') {
                    color = 'green';
                    label = `✅ ALLOW: Header Logo`;
                } else if (logoDept === 'unknown') {
                    color = 'orange';
                    label = `⚠️ ALLOW: Unknown Dept`;
                } else if (templateDepartments.includes(logoDept)) {
                    color = 'blue';
                    label = `✅ ALLOW: ${logoDept} Match`;
                } else {
                    color = 'red';
                    label = `❌ BLOCK: ${logoDept} Mismatch`;
                }

                // Apply styling
                container.style.border = `5px solid ${color}`;
                container.style.backgroundColor = `rgba(${
                    color === 'red' ? '255, 0, 0' :
                    color === 'green' ? '0, 255, 0' :
                    color === 'blue' ? '0, 0, 255' : '255, 165, 0'
                }, 0.1)`;
                container.style.position = 'relative';

                // Add label
                const labelDiv = document.createElement('div');
                labelDiv.style.cssText = `
                    position: absolute;
                    top: -35px;
                    left: 0;
                    background: ${color};
                    color: white;
                    padding: 5px 10px;
                    font-weight: bold;
                    font-size: 12px;
                    z-index: 10000;
                    border-radius: 3px;
                    white-space: nowrap;
                `;
                labelDiv.textContent = label;
                container.insertBefore(labelDiv, container.firstChild);
            });
        }
    """, {'logos': logos, 'templateDepartments': template_departments})

    logger.info("✅ Logos highlighted in browser")
    logger.info("   - GREEN = Header logo (allowed)")
    logger.info("   - BLUE = Department match (allowed)")
    logger.info("   - ORANGE = Unknown department (allowed with warning)")
    logger.info("   - RED = Department mismatch (BLOCKED)")


async def main():
    """Main test execution"""

    logger.info("="*100)
    logger.info("🧪 DEPARTMENT VERIFICATION TEST")
    logger.info("="*100)
    logger.info(f"Test Template: {TEST_TEMPLATE_ID}")
    logger.info(f"CDP URL: {CDP_URL}")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*100)

    async with async_playwright() as p:
        try:
            # Connect to existing browser
            browser = await p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]
            page = context.pages[0]

            # Navigate to template
            logger.info("Opening template edit page...")
            edit_url = f"https://preprodapp.tekioncloud.com/templates/edit/{TEST_TEMPLATE_ID}"
            await page.goto(edit_url, wait_until='domcontentloaded', timeout=30000)

            # Wait for editor to load
            await page.wait_for_selector('[class*="SortableItem"]', timeout=15000)
            logger.info("✅ Template editor loaded")

            # Run detection
            detection_result = await test_dynamic_detection_with_department_verification(page)

            # Print debug info
            logger.info("\n" + "="*100)
            logger.info("📋 DETECTION DEBUG LOG")
            logger.info("="*100)
            for line in detection_result['debug']:
                logger.info(line)

            logger.info("\n" + "="*100)
            logger.info("📊 DETECTION SUMMARY")
            logger.info("="*100)
            logger.info(f"Total imageComponents found: {detection_result['totalImageComponents']}")
            logger.info(f"Logos requiring action: {detection_result['logosDetected']}")

            # Simulate template departments (Service in this case)
            template_departments = ['Service']

            # Verify department matching
            verification_results = await verify_department_matching(
                detection_result['logos'],
                template_departments
            )

            # Highlight logos
            await highlight_logos_by_decision(page, detection_result['logos'], template_departments)

            # Summary
            logger.info("\n" + "="*100)
            logger.info("📈 VERIFICATION SUMMARY")
            logger.info("="*100)
            logger.info(f"   ✅ Allowed: {len(verification_results['allowed'])}")
            logger.info(f"   ⚠️  Warnings: {len(verification_results['warnings'])}")
            logger.info(f"   ❌ Blocked: {len(verification_results['blocked'])}")

            # Wait for inspection
            logger.info("\n" + "="*100)
            logger.info("⏸️  Waiting 30 seconds for visual inspection...")
            logger.info("   Check the browser for color-coded logos!")
            logger.info("="*100)

            await asyncio.sleep(30)

            logger.info("\n" + "="*100)
            logger.info("✅ DEPARTMENT VERIFICATION TEST COMPLETE")
            logger.info("="*100)

        except Exception as e:
            logger.exception(f"❌ Fatal error during test execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())

