"""HumanBrowserSession - BrowserSession with human-like behavior."""

import logging
from typing import Self

from browser_use.browser import BrowserSession

from human_browser_use.config import HumanBehaviorConfig
from human_browser_use.stealth.injection import StealthInjector

logger = logging.getLogger(__name__)


class HumanBrowserSession(BrowserSession):
    """BrowserSession extended with human-like behavior and stealth features.

    Key differences from BrowserSession:
    - Uses HumanActionWatchdog instead of DefaultActionWatchdog
    - Injects stealth JavaScript on every new document
    - Accepts HumanBehaviorConfig for fine-tuning behavior
    """

    # Store config and injector as class-level attributes since BrowserSession
    # uses Pydantic and we need to avoid field conflicts
    _human_config: HumanBehaviorConfig | None = None
    _stealth_injector: StealthInjector | None = None
    _stealth_script_id: str | None = None

    def __init__(self, human_config: HumanBehaviorConfig | None = None, **kwargs):
        """Initialize with optional human behavior config.

        Args:
            human_config: Configuration for human-like behavior. Uses defaults if None.
            **kwargs: All standard BrowserSession/BrowserProfile arguments.
        """
        super().__init__(**kwargs)
        # Store on instance via object.__setattr__ to bypass Pydantic
        object.__setattr__(self, '_human_config', human_config or HumanBehaviorConfig())
        object.__setattr__(self, '_stealth_injector', StealthInjector())
        object.__setattr__(self, '_stealth_script_id', None)

    async def connect(self, cdp_url: str | None = None) -> Self:
        """Connect to browser and inject stealth scripts."""
        result = await super().connect(cdp_url)

        config = object.__getattribute__(self, '_human_config')

        # Inject stealth scripts if enabled
        if config.enable_stealth:
            injector = object.__getattribute__(self, '_stealth_injector')
            try:
                script = injector.get_stealth_script()
                script_id = await self._cdp_add_init_script(script)
                object.__setattr__(self, '_stealth_script_id', script_id)
                logger.info('Stealth scripts injected successfully')

                # Also evaluate on current page immediately
                try:
                    cdp_session = await self.get_or_create_cdp_session()
                    await cdp_session.cdp_client.send.Runtime.evaluate(
                        params={'expression': script},
                        session_id=cdp_session.session_id,
                    )
                except Exception as e:
                    logger.debug(f'Failed to evaluate stealth on current page: {e}')
            except Exception as e:
                logger.warning(f'Failed to inject stealth scripts: {e}')

        return result

    async def attach_all_watchdogs(self) -> None:
        """Attach all watchdogs, replacing DefaultActionWatchdog with HumanActionWatchdog."""
        if self._watchdogs_attached:
            return

        # Import all watchdog classes
        from browser_use.browser.watchdogs.aboutblank_watchdog import AboutBlankWatchdog
        from browser_use.browser.watchdogs.captcha_watchdog import CaptchaWatchdog
        from browser_use.browser.watchdogs.dom_watchdog import DOMWatchdog
        from browser_use.browser.watchdogs.downloads_watchdog import DownloadsWatchdog
        from browser_use.browser.watchdogs.har_recording_watchdog import HarRecordingWatchdog
        from browser_use.browser.watchdogs.local_browser_watchdog import LocalBrowserWatchdog
        from browser_use.browser.watchdogs.permissions_watchdog import PermissionsWatchdog
        from browser_use.browser.watchdogs.popups_watchdog import PopupsWatchdog
        from browser_use.browser.watchdogs.recording_watchdog import RecordingWatchdog
        from browser_use.browser.watchdogs.screenshot_watchdog import ScreenshotWatchdog
        from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog
        from browser_use.browser.watchdogs.storage_state_watchdog import StorageStateWatchdog

        # Import our human action watchdog
        from human_browser_use.watchdogs.human_action_watchdog import HumanActionWatchdog

        # --- Same initialization order as BrowserSession ---

        # DownloadsWatchdog
        DownloadsWatchdog.model_rebuild()
        self._downloads_watchdog = DownloadsWatchdog(event_bus=self.event_bus, browser_session=self)
        self._downloads_watchdog.attach_to_session()

        # StorageStateWatchdog (conditional)
        should_enable_storage_state = (
            self.browser_profile.storage_state is not None or self.browser_profile.user_data_dir is not None
        )
        if should_enable_storage_state:
            StorageStateWatchdog.model_rebuild()
            self._storage_state_watchdog = StorageStateWatchdog(
                event_bus=self.event_bus,
                browser_session=self,
                auto_save_interval=60.0,
                save_on_change=False,
            )
            self._storage_state_watchdog.attach_to_session()

        # LocalBrowserWatchdog
        LocalBrowserWatchdog.model_rebuild()
        self._local_browser_watchdog = LocalBrowserWatchdog(event_bus=self.event_bus, browser_session=self)
        self._local_browser_watchdog.attach_to_session()

        # SecurityWatchdog
        SecurityWatchdog.model_rebuild()
        self._security_watchdog = SecurityWatchdog(event_bus=self.event_bus, browser_session=self)
        self._security_watchdog.attach_to_session()

        # AboutBlankWatchdog
        AboutBlankWatchdog.model_rebuild()
        self._aboutblank_watchdog = AboutBlankWatchdog(event_bus=self.event_bus, browser_session=self)
        self._aboutblank_watchdog.attach_to_session()

        # PopupsWatchdog
        PopupsWatchdog.model_rebuild()
        self._popups_watchdog = PopupsWatchdog(event_bus=self.event_bus, browser_session=self)
        self._popups_watchdog.attach_to_session()

        # PermissionsWatchdog
        PermissionsWatchdog.model_rebuild()
        self._permissions_watchdog = PermissionsWatchdog(event_bus=self.event_bus, browser_session=self)
        self._permissions_watchdog.attach_to_session()

        # >>> KEY CHANGE: Use HumanActionWatchdog instead of DefaultActionWatchdog <<<
        config = object.__getattribute__(self, '_human_config')
        HumanActionWatchdog.model_rebuild()
        self._default_action_watchdog = HumanActionWatchdog(
            event_bus=self.event_bus,
            browser_session=self,
            human_config=config,
        )
        self._default_action_watchdog.attach_to_session()

        # ScreenshotWatchdog
        ScreenshotWatchdog.model_rebuild()
        self._screenshot_watchdog = ScreenshotWatchdog(event_bus=self.event_bus, browser_session=self)
        self._screenshot_watchdog.attach_to_session()

        # DOMWatchdog
        DOMWatchdog.model_rebuild()
        self._dom_watchdog = DOMWatchdog(event_bus=self.event_bus, browser_session=self)
        self._dom_watchdog.attach_to_session()

        # RecordingWatchdog
        RecordingWatchdog.model_rebuild()
        self._recording_watchdog = RecordingWatchdog(event_bus=self.event_bus, browser_session=self)
        self._recording_watchdog.attach_to_session()

        # HarRecordingWatchdog (conditional)
        if self.browser_profile.record_har_path:
            HarRecordingWatchdog.model_rebuild()
            self._har_recording_watchdog = HarRecordingWatchdog(event_bus=self.event_bus, browser_session=self)
            self._har_recording_watchdog.attach_to_session()

        # CaptchaWatchdog (conditional)
        if self.browser_profile.captcha_solver:
            CaptchaWatchdog.model_rebuild()
            self._captcha_watchdog = CaptchaWatchdog(event_bus=self.event_bus, browser_session=self)
            self._captcha_watchdog.attach_to_session()

        self._watchdogs_attached = True
        logger.info('All watchdogs attached (with HumanActionWatchdog)')

    async def get_current_page(self):
        """Get the current page as a HumanPage (with human-like element interactions)."""
        target_info = await self.get_current_target_info()
        if not target_info:
            return None

        from human_browser_use.actor.page import HumanPage

        config = object.__getattribute__(self, '_human_config')
        return HumanPage(self, target_info['targetId'], human_config=config)

    async def get_pages(self):
        """Get all pages as HumanPage instances."""
        from human_browser_use.actor.page import HumanPage

        config = object.__getattribute__(self, '_human_config')
        page_targets = self.session_manager.get_all_page_targets() if self.session_manager else []
        return [HumanPage(self, target.target_id, human_config=config) for target in page_targets]
