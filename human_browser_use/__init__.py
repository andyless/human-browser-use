"""Human-like browser automation extension for browser-use."""

__all__ = [
    "HumanBehaviorConfig",
    "MouseConfig",
    "KeyboardConfig",
    "ScrollConfig",
    "HumanBrowserSession",
    "HumanBrowserProfile",
]

_LAZY_IMPORTS = {
    "HumanBehaviorConfig": "human_browser_use.config",
    "MouseConfig": "human_browser_use.config",
    "KeyboardConfig": "human_browser_use.config",
    "ScrollConfig": "human_browser_use.config",
    "HumanBrowserSession": "human_browser_use.session",
    "HumanBrowserProfile": "human_browser_use.profile",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        import importlib
        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    raise AttributeError(f"module 'human_browser_use' has no attribute {name!r}")
