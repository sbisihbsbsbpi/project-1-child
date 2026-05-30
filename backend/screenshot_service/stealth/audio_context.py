"""
Audio Context fingerprint randomization.

Extracted from screenshot_service.py (lines 2242-2296)
Part of Week 4 refactoring.

Provides audio API fingerprint randomization by:
- Adding noise to oscillator frequencies
- Randomizing dynamics compressor parameters

Some websites use audio context for fingerprinting.

Sources: Medium Aug 2024, ArXiv Feb 2025
"""

import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def apply_audio_context_randomization(page: Page):
    """
    Apply audio context fingerprint randomization.
    
    Randomizes audio API fingerprints by adding noise to oscillator frequencies
    and compressor parameters. This prevents audio-based fingerprinting while
    maintaining realistic audio API behavior.
    
    Techniques:
    - Adds random frequency offset to oscillators (-10 to +10 Hz)
    - Randomizes dynamics compressor threshold, knee, and ratio
    
    Args:
        page: Playwright page object
        
    Example:
        page = await context.new_page()
        await apply_audio_context_randomization(page)
    """
    await page.add_init_script("""
        // ========================================
        // Audio Context Randomization
        // ========================================
        (function() {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;

            const originalCreateOscillator = AudioContext.prototype.createOscillator;
            const originalCreateDynamicsCompressor = AudioContext.prototype.createDynamicsCompressor;

            // Randomize oscillator
            AudioContext.prototype.createOscillator = function() {
                const oscillator = originalCreateOscillator.apply(this, arguments);
                const originalStart = oscillator.start;

                oscillator.start = function() {
                    // Add random frequency offset (-10 to +10 Hz)
                    const offset = Math.random() * 20 - 10;
                    oscillator.frequency.value += offset;
                    return originalStart.apply(this, arguments);
                };

                return oscillator;
            };

            // Randomize dynamics compressor
            AudioContext.prototype.createDynamicsCompressor = function() {
                const compressor = originalCreateDynamicsCompressor.apply(this, arguments);

                // Add slight randomization to compressor parameters
                if (compressor.threshold) {
                    compressor.threshold.value += Math.random() * 2 - 1;
                }
                if (compressor.knee) {
                    compressor.knee.value += Math.random() * 2 - 1;
                }
                if (compressor.ratio) {
                    compressor.ratio.value += Math.random() * 0.5 - 0.25;
                }

                return compressor;
            };
        })();
    """)
    logger.debug("   🔊 Audio context randomization applied")


__all__ = ["apply_audio_context_randomization"]
