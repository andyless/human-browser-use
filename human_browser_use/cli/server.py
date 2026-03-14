"""Session server that uses HumanBrowserSession instead of BrowserSession.

This module patches browser-use's session creation to inject human-like behavior,
then delegates to the original server. All CLI commands (click, type, scroll, etc.)
automatically get human-like mouse trajectories, typing dynamics, and stealth.
"""

import os

# Ensure localhost bypasses proxy (critical for CDP WebSocket)
os.environ.setdefault('no_proxy', 'localhost,127.0.0.1,::1')
os.environ.setdefault('NO_PROXY', 'localhost,127.0.0.1,::1')

import browser_use.skill_cli.sessions as _sessions

from human_browser_use import HumanBehaviorConfig, HumanBrowserProfile, HumanBrowserSession

_original_create = _sessions.create_browser_session


async def _create_human_session(mode: str, headed: bool, profile: str | None):
    """Create HumanBrowserSession with stealth and human-like behavior."""
    config = HumanBehaviorConfig()

    if mode == 'chromium':
        return HumanBrowserSession(
            human_config=config,
            browser_profile=HumanBrowserProfile(headless=not headed),
        )

    elif mode == 'real':
        from browser_use.skill_cli.utils import find_chrome_executable, get_chrome_profile_path

        chrome_path = find_chrome_executable()
        if not chrome_path:
            raise RuntimeError('Could not find Chrome executable.')

        user_data_dir = get_chrome_profile_path(None)
        profile_directory = profile or 'Default'

        return HumanBrowserSession(
            human_config=config,
            executable_path=chrome_path,
            user_data_dir=user_data_dir,
            profile_directory=profile_directory,
            headless=not headed,
        )

    else:
        # remote / unknown — fall back to original
        return await _original_create(mode, headed, profile)


# Patch before server starts
_sessions.create_browser_session = _create_human_session


def main():
    from browser_use.skill_cli.server import main as _server_main

    _server_main()


if __name__ == '__main__':
    main()
