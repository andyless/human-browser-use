"""HumanPage - Page actor that returns HumanElement instances."""

import asyncio
import random

from browser_use.actor.page import Page

from human_browser_use.config import HumanBehaviorConfig
from human_browser_use.behavior.timing import ActionTiming


class HumanPage(Page):
    """Page that returns HumanElement instances from element queries.

    All element retrieval methods return HumanElement instead of base Element,
    ensuring human-like behavior is used for all interactions.
    """

    def __init__(self, *args, human_config: HumanBehaviorConfig | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._human_config = human_config or HumanBehaviorConfig()
        self._timing = ActionTiming(self._human_config.timing)
        # Shared mouse position state - all elements from this page share it
        self._mouse_state = {'x': 0.0, 'y': 0.0}

    def _wrap_element(self, base_element):
        """Wrap a base Element as a HumanElement."""
        from human_browser_use.actor.element import HumanElement
        return HumanElement(
            self._browser_session,
            base_element._backend_node_id,
            base_element._session_id,
            human_config=self._human_config,
            mouse_state=self._mouse_state,
        )

    async def get_elements_by_css_selector(self, selector: str) -> list:
        """Get elements by CSS selector, returning HumanElement instances."""
        base_elements = await super().get_elements_by_css_selector(selector)
        return [self._wrap_element(el) for el in base_elements]

    async def get_element(self, backend_node_id: int):
        """Get a single element by backend node ID, returning HumanElement."""
        base_element = await super().get_element(backend_node_id)
        return self._wrap_element(base_element)

    async def goto(self, url: str) -> None:
        """Navigate to URL with pre-delay."""
        await asyncio.sleep(self._timing.get_pre_action_delay())
        await super().goto(url)

    async def press(self, key: str) -> None:
        """Press key with pre-delay."""
        await asyncio.sleep(random.uniform(0.05, 0.15))
        await super().press(key)
