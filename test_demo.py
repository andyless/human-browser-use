"""Test demo: Use HumanBrowserSession to open Baidu, search for 'bing', click the result.

No LLM required - manually orchestrates browser actions via the session API
to demonstrate human-like mouse trajectories, keyboard dynamics, and scrolling.
"""

import asyncio
import logging
import os

# Fix: exclude localhost from proxy so CDP WebSocket works
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'

from human_browser_use import HumanBrowserSession, HumanBrowserProfile, HumanBehaviorConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


async def main():
    # Config with slightly exaggerated params for visible effect
    config = HumanBehaviorConfig()
    config.mouse.overshoot_probability = 0.3  # More overshoots so we can see them

    # Profile with stealth flags + proxy for Chrome to access internet
    profile = HumanBrowserProfile(
        headless=False,
        window_size={'width': 1280, 'height': 900},
        proxy={'server': 'http://127.0.0.1:7897'},
        disable_security=True,
    )

    session = HumanBrowserSession(
        human_config=config,
        browser_profile=profile,
    )

    try:
        # Start browser
        logger.info('=== Starting browser session ===')
        await session.start()
        logger.info('Browser session started successfully!')

        # Navigate to Baidu
        logger.info('=== Navigating to baidu.com ===')
        await session.navigate_to('https://www.baidu.com')
        await asyncio.sleep(2)

        # Get current page
        page = await session.get_current_page()

        # Find search input by CSS selector
        logger.info('=== Finding search input #kw ===')
        elements = await page.get_elements_by_css_selector('#kw')
        if not elements:
            logger.error('Search input #kw not found!')
            return

        search_input = elements[0]
        logger.info('Found search input')

        # Click the search input (human-like trajectory via watchdog)
        logger.info('=== Clicking search input (human-like trajectory) ===')
        await search_input.click()
        await asyncio.sleep(0.5)

        # Type "bing" with human-like keyboard dynamics
        logger.info('=== Typing "bing" (human-like dynamics) ===')
        await search_input.fill('bing', clear=True)
        await asyncio.sleep(1)

        # Press Enter to search
        logger.info('=== Pressing Enter to search ===')
        await page.press('Enter')
        await asyncio.sleep(3)

        # Check URL
        url = await page.get_url()
        logger.info(f'=== Search results loaded: {url} ===')

        # Find the first link in search results and click it
        logger.info('=== Looking for Bing link in search results ===')
        results = await page.get_elements_by_css_selector('.c-container h3 a, .result h3 a')

        clicked = False
        for elem in results[:5]:
            try:
                info = await elem.get_basic_info()
                text = info.get('text', '') or info.get('innerText', '')
                logger.info(f'  Result: {text[:80]}')
                if 'bing' in text.lower() or '必应' in text:
                    logger.info('=== Clicking Bing link (human-like trajectory) ===')
                    await elem.click()
                    clicked = True
                    break
            except Exception as e:
                logger.debug(f'  Skip element: {e}')
                continue

        if not clicked and results:
            logger.info('=== Clicking first result ===')
            await results[0].click()

        await asyncio.sleep(3)

        # Check all open tabs
        logger.info('=== Final state ===')
        pages = await session.get_pages()
        for p in pages:
            try:
                u = await p.get_url()
                t = await p.get_title()
                logger.info(f'  Tab: {t} ({u})')
            except Exception:
                pass

        logger.info('=== Test complete! Browser stays open 15s for inspection ===')
        await asyncio.sleep(15)

    except Exception as e:
        logger.error(f'Error: {e}', exc_info=True)
    finally:
        logger.info('Closing browser session...')
        await session.reset()


if __name__ == '__main__':
    asyncio.run(main())
