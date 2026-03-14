#!/usr/bin/env python3
"""CLI entry point for human-browser-use.

Wraps browser-use's CLI but starts our patched server (human_browser_use.cli.server)
so all browser interactions use HumanBrowserSession with human-like behavior.

Usage:
    hbu open https://example.com
    hbu click 0
    hbu type "hello world"
    hbu screenshot page.png
    hbu state
    hbu close
"""

import os
import subprocess
import sys

# Ensure localhost bypasses proxy (critical for CDP WebSocket)
os.environ.setdefault('no_proxy', 'localhost,127.0.0.1,::1')
os.environ.setdefault('NO_PROXY', 'localhost,127.0.0.1,::1')


def main():
    # Intercept browser-use's ensure_server() subprocess.Popen call
    # to start our patched server instead of the original.

    _original_popen = subprocess.Popen

    class _PatchedPopen(subprocess.Popen):
        def __init__(self, cmd, *args, **kwargs):
            if isinstance(cmd, list):
                cmd = [
                    'human_browser_use.cli.server'
                    if x == 'browser_use.skill_cli.server'
                    else x
                    for x in cmd
                ]
                # Ensure no_proxy is in the subprocess env
                env = kwargs.get('env') or os.environ.copy()
                env.setdefault('no_proxy', 'localhost,127.0.0.1,::1')
                env.setdefault('NO_PROXY', 'localhost,127.0.0.1,::1')
                kwargs['env'] = env
            super().__init__(cmd, *args, **kwargs)

    subprocess.Popen = _PatchedPopen
    try:
        from browser_use.skill_cli.main import main as _bu_main

        _bu_main()
    finally:
        subprocess.Popen = _original_popen


if __name__ == '__main__':
    main()
