"""Action timing utilities for human-like delays."""

import random
from human_browser_use.config import TimingConfig


class ActionTiming:
    """Provides human-like timing between browser actions."""

    def __init__(self, config: TimingConfig | None = None):
        self.config = config or TimingConfig()

    def get_pre_action_delay(self) -> float:
        """Get a random delay before performing an action."""
        return random.uniform(*self.config.pre_action_delay_range)

    def get_reading_time(self, text_length: int) -> float:
        """Estimate reading time based on text length."""
        cfg = self.config
        raw_time = text_length * cfg.reading_time_per_char
        return min(raw_time, cfg.reading_time_max)
