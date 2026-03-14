"""Human-like browser automation extension for browser-use."""

from human_browser_use.config import HumanBehaviorConfig, MouseConfig, KeyboardConfig, ScrollConfig
from human_browser_use.session import HumanBrowserSession
from human_browser_use.profile import HumanBrowserProfile

__all__ = [
    "HumanBehaviorConfig",
    "MouseConfig",
    "KeyboardConfig",
    "ScrollConfig",
    "HumanBrowserSession",
    "HumanBrowserProfile",
]
