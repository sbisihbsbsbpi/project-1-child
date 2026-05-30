"""
Canvas and WebGL fingerprint randomization.

Extracted from screenshot_service.py (lines 2054-2172)
Part of Week 4 refactoring.

Provides fingerprint randomization for:
- Canvas rendering (toDataURL, toBlob, getImageData)
- WebGL parameters (vendor, renderer, extensions)

This is the #1 detection method used by anti-bots in 2024-2025.

Sources: ScrapingAnt Oct 2024, Reddit r/webscraping Dec 2024
"""

import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def apply_canvas_webgl_randomization(page: Page):
    """
    Apply canvas and WebGL fingerprint randomization.
    
    Injects noise into canvas and WebGL rendering to prevent fingerprinting.
    This makes each browser session appear unique while maintaining realistic
    values.
    
    Techniques:
    - Adds random noise to canvas pixel data
    - Randomizes WebGL vendor and renderer strings
    - Varies WebGL extension list
    
    Args:
        page: Playwright page object
        
    Example:
        page = await context.new_page()
        await apply_canvas_webgl_randomization(page)
    """
    await page.add_init_script("""
        // ========================================
        // Canvas Fingerprint Randomization
        // ========================================
        (function() {
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

            // Add random noise to canvas data
            const addNoise = (imageData) => {
                const data = imageData.data;
                const noise = Math.random() * 10 - 5; // Random noise between -5 and 5

                // Add noise to random pixels (10% of pixels)
                for (let i = 0; i < data.length; i += 40) {
                    data[i] = Math.min(255, Math.max(0, data[i] + noise));
                }
                return imageData;
            };

            // Override toDataURL
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                const context = this.getContext('2d');
                if (context) {
                    try {
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        addNoise(imageData);
                        context.putImageData(imageData, 0, 0);
                    } catch (e) {
                        // Ignore errors (e.g., tainted canvas)
                    }
                }
                return originalToDataURL.apply(this, arguments);
            };

            // Override toBlob
            HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {
                const context = this.getContext('2d');
                if (context) {
                    try {
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        addNoise(imageData);
                        context.putImageData(imageData, 0, 0);
                    } catch (e) {
                        // Ignore errors
                    }
                }
                return originalToBlob.apply(this, arguments);
            };

            // Override getImageData
            CanvasRenderingContext2D.prototype.getImageData = function() {
                const imageData = originalGetImageData.apply(this, arguments);
                return addNoise(imageData);
            };
        })();

        // ========================================
        // WebGL Fingerprint Randomization
        // ========================================
        (function() {
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            const getParameterWebGL2 = WebGL2RenderingContext.prototype.getParameter;

            // Randomize WebGL parameters
            const randomizeParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    const vendors = ['Intel Inc.', 'Google Inc.', 'NVIDIA Corporation', 'AMD'];
                    return vendors[Math.floor(Math.random() * vendors.length)];
                }

                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    const renderers = [
                        'Intel Iris OpenGL Engine',
                        'ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.1)',
                        'ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0)',
                        'AMD Radeon Pro 5500M OpenGL Engine'
                    ];
                    return renderers[Math.floor(Math.random() * renderers.length)];
                }

                return getParameter.apply(this, arguments);
            };

            // Override for WebGL 1.0
            WebGLRenderingContext.prototype.getParameter = randomizeParameter;

            // Override for WebGL 2.0
            WebGL2RenderingContext.prototype.getParameter = randomizeParameter;

            // Randomize WebGL extensions
            const getSupportedExtensions = WebGLRenderingContext.prototype.getSupportedExtensions;
            WebGLRenderingContext.prototype.getSupportedExtensions = function() {
                const extensions = getSupportedExtensions.apply(this, arguments);
                // Randomly remove 1-2 extensions to vary fingerprint
                if (extensions && extensions.length > 5) {
                    const toRemove = Math.floor(Math.random() * 2) + 1;
                    for (let i = 0; i < toRemove; i++) {
                        const idx = Math.floor(Math.random() * extensions.length);
                        extensions.splice(idx, 1);
                    }
                }
                return extensions;
            };
        })();
    """)
    logger.debug("   🎨 Canvas & WebGL fingerprint randomization applied")


__all__ = ["apply_canvas_webgl_randomization"]
