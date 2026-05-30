"""
Behavioral randomization for human-like automation.

Extracted from screenshot_service.py (lines 2298-2344, 807-859)
Part of Week 4 refactoring.

Provides human-like behavioral simulation:
- Random mouse movements
- Realistic scrolling patterns
- Random delays
- Occasional clicks and keyboard inputs

Modern anti-bots analyze behavioral patterns to detect automation.

Sources: AgentQL Nov 2024, ScrapingAnt Sep 2024
"""

import asyncio
import random
import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def add_random_delay(min_seconds: float, max_seconds: float):
    """
    Add a random delay between actions.
    
    Simulates human think time and reading behavior.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


async def simulate_mouse_movement(page: Page):
    """
    Simulate realistic mouse movements.
    
    Moves the mouse to random positions on the page with delays between
    movements to simulate human-like cursor behavior.
    
    Args:
        page: Playwright page object
    """
    try:
        # Random number of movements (2-5)
        num_movements = random.randint(2, 5)
        
        for _ in range(num_movements):
            x = random.randint(100, 1200)
            y = random.randint(100, 800)
            await page.mouse.move(x, y)
            await add_random_delay(0.05, 0.15)
        
        logger.debug("   🖱️  Simulated realistic mouse movements")
    except Exception as e:
        logger.warning("   ⚠️  Mouse simulation failed: %s", e)


async def simulate_scrolling(page: Page):
    """
    Simulate realistic scrolling behavior.
    
    Performs random scroll actions with smooth behavior and delays to
    simulate reading and browsing patterns.
    
    Args:
        page: Playwright page object
    """
    try:
        # Random number of scroll actions
        num_scrolls = random.randint(2, 5)
        
        for _ in range(num_scrolls):
            # Random scroll amount (200-800px)
            scroll_amount = random.randint(200, 800)
            
            # Scroll down
            await page.evaluate(f'window.scrollBy(0, {scroll_amount})')
            
            # Random delay between scrolls (simulate reading)
            await add_random_delay(0.3, 1.0)
        
        # Scroll back to top
        await page.evaluate('window.scrollTo(0, 0)')
        await add_random_delay(0.2, 0.5)
        
        logger.debug("   📜 Simulated realistic scrolling")
    except Exception as e:
        logger.warning("   ⚠️  Scroll simulation failed: %s", e)


async def apply_behavioral_randomization(page: Page):
    """
    Apply comprehensive behavioral randomization.
    
    Simulates human-like behavior with mouse movements, scrolling, and
    timing delays. Includes occasional random clicks and keyboard inputs.
    
    Args:
        page: Playwright page object
        
    Example:
        page = await context.new_page()
        await page.goto("https://example.com")
        await apply_behavioral_randomization(page)
    """
    try:
        # Random mouse movements (2-5 movements)
        num_movements = random.randint(2, 5)
        for _ in range(num_movements):
            x = random.randint(100, 1200)
            y = random.randint(100, 800)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # Random scroll with smooth behavior
        scroll_amount = random.randint(100, 500)
        await page.evaluate(f"""
            window.scrollTo({{
                top: {scroll_amount},
                behavior: 'smooth'
            }});
        """)
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        # Occasionally click somewhere random (30% chance)
        if random.random() > 0.7:
            x = random.randint(200, 1000)
            y = random.randint(200, 700)
            try:
                await page.mouse.click(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
            except Exception:
                pass  # Ignore click errors (element may not be clickable)
        
        # Random typing simulation (20% chance)
        if random.random() > 0.8:
            await page.keyboard.press('Tab')
            await asyncio.sleep(random.uniform(0.1, 0.2))
        
        logger.debug("   🤖 Human-like behavior simulation applied")
    except Exception as e:
        # Don't fail if behavioral randomization fails
        logger.warning("   ⚠️  Behavioral randomization warning: %s", e)


__all__ = [
    "add_random_delay",
    "simulate_mouse_movement",
    "simulate_scrolling",
    "apply_behavioral_randomization",
]
