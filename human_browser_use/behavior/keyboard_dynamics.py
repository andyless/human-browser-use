"""Keyboard dynamics simulation with realistic timing and typo simulation."""

import math
import random
from human_browser_use.config import KeyboardConfig

# Common bigrams that are faster to type
COMMON_BIGRAMS = {
    'th', 'he', 'in', 'er', 'an', 'on', 'en', 'at', 'es', 'ed',
    'or', 'ti', 'st', 'ar', 'nd', 'to', 'nt', 'is', 'of', 'it',
    'al', 'as', 'ha', 'et', 'se', 'ou', 'te', 're', 'hi', 'ea',
    'io', 'le', 'no', 'ri', 'ni', 'ra', 'el', 'ma', 'ec', 'ta',
}

# Nearby keys on QWERTY for typo simulation
NEARBY_KEYS = {
    'q': 'was', 'w': 'qesa', 'e': 'wrsd', 'r': 'etdf', 't': 'ryfg',
    'y': 'tugh', 'u': 'yijh', 'i': 'uokj', 'o': 'iplk', 'p': 'ol',
    'a': 'qwsz', 's': 'awedxz', 'd': 'serfcx', 'f': 'drtgvc',
    'g': 'ftyhbv', 'h': 'gyujnb', 'j': 'huiknm', 'k': 'jiolm',
    'l': 'kop', 'z': 'asx', 'x': 'zsdc', 'c': 'xdfv',
    'v': 'cfgb', 'b': 'vghn', 'n': 'bhjm', 'm': 'njk',
}


class KeyboardDynamics:
    """Simulates human keyboard typing dynamics."""

    def __init__(self, config: KeyboardConfig | None = None):
        self.config = config or KeyboardConfig()
        self._prev_char: str | None = None

    def get_inter_key_delay(self, current_char: str) -> float:
        """Get delay before typing the current character.

        Uses lognormal distribution with adjustments for bigrams,
        shift characters, and word boundaries.
        """
        cfg = self.config

        # Base delay from lognormal distribution
        delay = random.lognormvariate(cfg.delay_mu, cfg.delay_sigma) / 1000.0  # Convert ms to seconds
        # Clamp to reasonable range
        delay = max(0.02, min(0.5, delay))

        # Bigram speedup
        if self._prev_char and (self._prev_char + current_char).lower() in COMMON_BIGRAMS:
            delay *= cfg.common_bigram_factor

        # Shift character slowdown
        if current_char.isupper() or current_char in '!@#$%^&*()_+{}|:"<>?~':
            delay *= cfg.shift_char_factor

        # Word boundary pause
        if self._prev_char == ' ':
            delay += random.uniform(*cfg.word_pause_range)

        self._prev_char = current_char
        return delay

    def should_make_typo(self) -> bool:
        """Check if a typo should be made at this position."""
        return random.random() < self.config.typo_probability

    def get_typo_char(self, intended_char: str) -> str | None:
        """Get a nearby key for typo simulation.

        Returns None if no suitable nearby key found.
        """
        nearby = NEARBY_KEYS.get(intended_char.lower())
        if not nearby:
            return None
        typo = random.choice(nearby)
        # Preserve case
        if intended_char.isupper():
            typo = typo.upper()
        return typo

    def get_typo_pause(self) -> float:
        """Get the pause duration before correcting a typo (recognition delay)."""
        return random.uniform(*self.config.typo_pause_range)

    def reset(self):
        """Reset state for a new typing session."""
        self._prev_char = None
