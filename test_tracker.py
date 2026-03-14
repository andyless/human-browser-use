"""Test: Use HumanBrowserSession to interact with the mouse tracker page.

Navigates to the local tracker page, performs mouse movements, clicks, and typing
so we can visually verify how human-like the automation looks.
"""

import asyncio
import logging
import os

# Fix: exclude localhost from proxy so CDP WebSocket works
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'

from human_browser_use import HumanBrowserSession, HumanBrowserProfile, HumanBehaviorConfig

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
# Only DEBUG for our module, INFO for others
logging.getLogger('human_browser_use').setLevel(logging.DEBUG)
logging.getLogger('BrowserSession').setLevel(logging.WARNING)
logging.getLogger('playwright').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def main():
    config = HumanBehaviorConfig()
    config.mouse.overshoot_probability = 0.3

    profile = HumanBrowserProfile(
        headless=False,
        window_size={'width': 1280, 'height': 900},
        disable_security=True,
    )

    session = HumanBrowserSession(
        human_config=config,
        browser_profile=profile,
    )

    try:
        logger.info('=== Starting browser session ===')
        await session.start()

        # Navigate to the local tracker page
        logger.info('=== Navigating to mouse tracker page ===')
        await session.navigate_to('http://127.0.0.1:8765/test_mouse_tracker.html')
        await asyncio.sleep(2)

        page = await session.get_current_page()

        # Check tracker state via JS before interactions
        stats_before = await page.evaluate('() => JSON.stringify({points: points.length, clicks: clicks.length, keys: keyEventCount})')
        logger.info(f'=== Tracker state BEFORE: {stats_before} ===')

        # Step 1: Click the search input
        logger.info('=== Step 1: Clicking search input ===')
        elements = await page.get_elements_by_css_selector('.search-input')
        if not elements:
            logger.error('Search input not found!')
            return

        search_input = elements[0]
        await search_input.click()
        await asyncio.sleep(0.5)

        # Check tracker state after click
        stats_after_click = await page.evaluate('() => JSON.stringify({points: points.length, clicks: clicks.length, keys: keyEventCount})')
        logger.info(f'=== Tracker state after click: {stats_after_click} ===')

        # Step 2: Type text with human-like keyboard dynamics
        logger.info('=== Step 2: Typing "human browser use" ===')
        await search_input.fill('human browser use', clear=True)
        await asyncio.sleep(1)

        # Check tracker state after typing
        stats_after_type = await page.evaluate('() => JSON.stringify({points: points.length, clicks: clicks.length, keys: keyEventCount})')
        logger.info(f'=== Tracker state after typing: {stats_after_type} ===')

        # Step 3: Click the "搜索一下" button
        logger.info('=== Step 3: Clicking search button ===')
        buttons = await page.get_elements_by_css_selector('.btn')
        if buttons:
            await buttons[0].click()
            await asyncio.sleep(1)

        # Step 4: Move to another area - click "手气不错" button
        logger.info('=== Step 4: Clicking second button ===')
        if len(buttons) > 1:
            await buttons[1].click()
            await asyncio.sleep(1)

        # Step 5: Click back on the search input and type more
        logger.info('=== Step 5: Clicking search input again ===')
        await search_input.click()
        await asyncio.sleep(0.3)
        await search_input.fill(' test 12345', clear=False)
        await asyncio.sleep(1)

        # Step 6: Click the logo area
        logger.info('=== Step 6: Clicking logo ===')
        logo = await page.get_elements_by_css_selector('.logo')
        if logo:
            await logo[0].click()
            await asyncio.sleep(1)

        # Final tracker state
        stats_final = await page.evaluate('() => JSON.stringify({points: points.length, clicks: clicks.length, keys: keyEventCount})')
        logger.info(f'=== Tracker state FINAL: {stats_final} ===')

        logger.info('=== Test complete! Browser stays open 30s for inspection ===')
        await asyncio.sleep(30)

    except Exception as e:
        logger.error(f'Error: {e}', exc_info=True)
    finally:
        logger.info('Closing browser session...')
        await session.reset()


if __name__ == '__main__':
    asyncio.run(main())
