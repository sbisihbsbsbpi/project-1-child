#!/usr/bin/env python3
"""
Smart Logo Detector - Dynamic Detection System
Uses multiple detection strategies with fallbacks
"""

import asyncio
from playwright.async_api import Page
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SmartLogoDetector:
    """
    Intelligent logo detection using multiple strategies:
    1. Media ID matching (primary)
    2. Position-based detection (secondary)
    3. Size-based detection (tertiary)
    4. Container pattern matching (fallback)
    """
    
    def __init__(self):
        # Known logo media IDs (can be extended)
        self.known_logos = {
            '6a0c6722864813539e4da7ae': {
                'name': 'Nucar Logo',
                'type': 'old',
                'common_size': '80x21',
                'common_location': 'bottom-right'
            },
            '6a19132b6697f36de6236fb1': {
                'name': 'Tilton Logo',
                'type': 'new',
                'common_size': '228x138',
                'common_location': 'variable'
            }
        }
        
        # Detection strategies
        self.strategies = [
            self._detect_by_media_id,
            self._detect_by_position,
            self._detect_by_size_and_aspect,
            self._detect_by_container_pattern
        ]
    
    async def detect_logos(self, page: Page) -> Dict:
        """
        Run all detection strategies and return comprehensive results
        """
        logger.info("🔍 Running smart logo detection...")
        
        # Get all image data from page
        image_data = await self._extract_image_data(page)
        
        logger.info(f"Found {len(image_data)} images in template")
        
        results = {
            'total_images': len(image_data),
            'detected_logos': [],
            'detection_methods': [],
            'confidence_scores': {}
        }
        
        # Run each detection strategy
        for strategy in self.strategies:
            strategy_result = await strategy(image_data)
            
            if strategy_result['found']:
                results['detected_logos'].extend(strategy_result['logos'])
                results['detection_methods'].append(strategy_result['method'])
                logger.info(f"✅ {strategy_result['method']}: Found {len(strategy_result['logos'])} logo(s)")
        
        # Deduplicate logos (same image detected by multiple strategies)
        results['detected_logos'] = self._deduplicate_logos(results['detected_logos'])
        
        logger.info(f"Total unique logos detected: {len(results['detected_logos'])}")
        
        return results
    
    async def _extract_image_data(self, page: Page) -> List[Dict]:
        """Extract comprehensive image data from page"""
        
        return await page.evaluate("""
            () => {
                const images = Array.from(document.querySelectorAll('img'));
                
                return images.map((img, idx) => {
                    const rect = img.getBoundingClientRect();
                    const src = img.src || '';
                    
                    // Extract media ID
                    const mediaIdMatch = src.match(/([a-f0-9]{24})/);
                    const mediaId = mediaIdMatch ? mediaIdMatch[1] : null;
                    
                    // Get container info
                    let container = img.parentElement;
                    let containerClasses = [];
                    let depth = 0;
                    
                    while (container && depth < 5) {
                        const classes = container.className || '';
                        if (classes) {
                            containerClasses.push(classes);
                        }
                        container = container.parentElement;
                        depth++;
                    }
                    
                    // Position analysis
                    const viewportHeight = window.innerHeight;
                    const viewportWidth = window.innerWidth;
                    
                    const verticalPos = rect.top < viewportHeight * 0.3 ? 'top' :
                                       rect.top > viewportHeight * 0.7 ? 'bottom' : 'middle';
                    const horizontalPos = rect.left < viewportWidth * 0.3 ? 'left' :
                                         rect.left > viewportWidth * 0.7 ? 'right' : 'center';
                    
                    return {
                        index: idx,
                        mediaId: mediaId,
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        aspectRatio: rect.width / rect.height,
                        position: {
                            top: Math.round(rect.top),
                            left: Math.round(rect.left),
                            vertical: verticalPos,
                            horizontal: horizontalPos,
                            location: verticalPos + '-' + horizontalPos
                        },
                        alt: img.alt || '',
                        src: src,
                        containerClasses: containerClasses,
                        visible: rect.width > 0 && rect.height > 0
                    };
                }).filter(img => img.visible && img.width >= 20 && img.height >= 10);
            }
        """)
    
    async def _detect_by_media_id(self, image_data: List[Dict]) -> Dict:
        """Strategy 1: Detect by known media IDs"""
        
        found_logos = []
        
        for img in image_data:
            media_id = img.get('mediaId')
            if media_id and media_id in self.known_logos:
                logo_info = self.known_logos[media_id]
                found_logos.append({
                    **img,
                    'logo_name': logo_info['name'],
                    'logo_type': logo_info['type'],
                    'confidence': 100,  # Highest confidence
                    'detection_method': 'media_id'
                })
        
        return {
            'found': len(found_logos) > 0,
            'logos': found_logos,
            'method': 'Media ID Matching'
        }
    
    async def _detect_by_position(self, image_data: List[Dict]) -> Dict:
        """Strategy 2: Detect by typical logo positions"""
        
        found_logos = []
        
        # Logos typically at: bottom-right, bottom-center, bottom-left
        logo_positions = ['bottom-right', 'bottom-center', 'bottom-left']
        
        for img in image_data:
            location = img['position']['location']
            
            if location in logo_positions:
                # Additional checks: size and aspect ratio
                width = img['width']
                height = img['height']
                aspect_ratio = img['aspectRatio']
                
                # Typical logo characteristics
                is_logo_sized = (50 < width < 300) and (15 < height < 150)
                is_logo_aspect = 1.5 < aspect_ratio < 8
                
                if is_logo_sized and is_logo_aspect:
                    found_logos.append({
                        **img,
                        'confidence': 75,  # Medium-high confidence
                        'detection_method': 'position_based'
                    })
        
        return {
            'found': len(found_logos) > 0,
            'logos': found_logos,
            'method': 'Position-Based Detection'
        }

    async def _detect_by_size_and_aspect(self, image_data: List[Dict]) -> Dict:
        """Strategy 3: Detect by size and aspect ratio patterns"""

        found_logos = []

        # Common logo sizes and aspect ratios
        logo_patterns = [
            {'width_range': (60, 100), 'height_range': (15, 30), 'aspect_range': (2.5, 4.5)},  # Typical horizontal logo
            {'width_range': (150, 250), 'height_range': (50, 100), 'aspect_range': (2.0, 4.0)},  # Larger logos
            {'width_range': (200, 300), 'height_range': (50, 150), 'aspect_range': (1.5, 6.0)}   # Variable logos
        ]

        for img in image_data:
            width = img['width']
            height = img['height']
            aspect = img['aspectRatio']

            for pattern in logo_patterns:
                w_min, w_max = pattern['width_range']
                h_min, h_max = pattern['height_range']
                a_min, a_max = pattern['aspect_range']

                if (w_min <= width <= w_max and
                    h_min <= height <= h_max and
                    a_min <= aspect <= a_max):

                    found_logos.append({
                        **img,
                        'confidence': 60,  # Medium confidence
                        'detection_method': 'size_aspect_pattern'
                    })
                    break

        return {
            'found': len(found_logos) > 0,
            'logos': found_logos,
            'method': 'Size/Aspect Ratio Pattern'
        }

    async def _detect_by_container_pattern(self, image_data: List[Dict]) -> Dict:
        """Strategy 4: Detect by container class patterns"""

        found_logos = []

        # Common container patterns for logos
        logo_container_keywords = [
            'logo', 'footer', 'branding', 'powered', 'dealer',
            'resizable', 'imageComponent', 'elementContainer'
        ]

        for img in image_data:
            container_classes_str = ' '.join(img.get('containerClasses', [])).lower()

            # Check for logo-related keywords in containers
            has_logo_container = any(keyword in container_classes_str for keyword in logo_container_keywords)

            # Check position (logos usually at bottom)
            is_bottom = img['position']['vertical'] == 'bottom'

            # Check size
            is_reasonable_size = (50 < img['width'] < 300) and (15 < img['height'] < 150)

            if has_logo_container and is_bottom and is_reasonable_size:
                found_logos.append({
                    **img,
                    'confidence': 50,  # Lower confidence
                    'detection_method': 'container_pattern'
                })

        return {
            'found': len(found_logos) > 0,
            'logos': found_logos,
            'method': 'Container Pattern Matching'
        }

    def _deduplicate_logos(self, logos: List[Dict]) -> List[Dict]:
        """Remove duplicate detections, keeping highest confidence"""

        # Group by index (same image)
        by_index = {}
        for logo in logos:
            idx = logo['index']
            if idx not in by_index:
                by_index[idx] = []
            by_index[idx].append(logo)

        # Keep highest confidence detection for each image
        deduplicated = []
        for idx, detections in by_index.items():
            best = max(detections, key=lambda x: x.get('confidence', 0))
            deduplicated.append(best)

        return deduplicated

    def get_replacement_target(self, detected_logos: List[Dict], target_media_id: str) -> Optional[Dict]:
        """Get the specific logo to replace based on media ID"""

        for logo in detected_logos:
            if logo.get('mediaId') == target_media_id:
                return logo

        return None

    def log_detection_summary(self, results: Dict):
        """Log a summary of detection results"""

        logger.info("=" * 80)
        logger.info("🔍 SMART DETECTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total images analyzed: {results['total_images']}")
        logger.info(f"Logos detected: {len(results['detected_logos'])}")
        logger.info(f"Detection methods used: {', '.join(results['detection_methods'])}")
        logger.info("")

        for idx, logo in enumerate(results['detected_logos'], 1):
            logger.info(f"Logo {idx}:")
            logger.info(f"  Size: {logo['width']}x{logo['height']}")
            logger.info(f"  Position: {logo['position']['location']}")
            logger.info(f"  Media ID: {logo.get('mediaId', 'Unknown')}")
            logger.info(f"  Confidence: {logo.get('confidence', 0)}%")
            logger.info(f"  Method: {logo.get('detection_method', 'unknown')}")
            logger.info("")


async def test_smart_detector():
    """Test the smart detector on current page"""
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9223")
    context = browser.contexts[0]

    # Test on first template tab
    for page in context.pages:
        if 'templates/edit' in page.url:
            detector = SmartLogoDetector()
            results = await detector.detect_logos(page)
            detector.log_detection_summary(results)
            break

    await playwright.stop()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    asyncio.run(test_smart_detector())
