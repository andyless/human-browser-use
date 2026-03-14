"""HumanBrowserProfile - BrowserProfile with anti-detection Chrome flags."""

from browser_use.browser import BrowserProfile


# Additional Chrome flags for stealth
STEALTH_CHROME_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--disable-dev-shm-usage',
    '--disable-browser-side-navigation',
    '--disable-gpu-sandbox',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-networking',
    '--disable-client-side-phishing-detection',
    '--disable-hang-monitor',
    '--disable-ipc-flooding-protection',
    '--metrics-recording-only',
    '--no-service-autorun',
    '--password-store=basic',
    '--use-mock-keychain',
    '--export-tagged-pdf',
    '--disable-features=IsolateOrigins,site-per-process,TranslateUI',
    '--flag-switches-begin',
    '--flag-switches-end',
]


class HumanBrowserProfile(BrowserProfile):
    """BrowserProfile extended with anti-detection Chrome flags.

    Automatically adds stealth flags to the browser launch arguments
    to reduce automation detection surface.
    """

    def model_post_init(self, __context) -> None:
        """Add stealth args after initialization."""
        super().model_post_init(__context)

        # Add stealth args that aren't already present
        existing = set(self.args)
        for arg in STEALTH_CHROME_ARGS:
            if arg not in existing:
                self.args.append(arg)
