"""Configuration for human-like browser behavior."""

from pydantic import BaseModel, Field


class MouseConfig(BaseModel):
    """Mouse movement configuration."""

    # WindMouse parameters
    wind_gravity: float = Field(default=9.0, description="Gravity force pulling toward target")
    wind_force: float = Field(default=3.0, description="Wind force for random perturbation")
    wind_change_prob: float = Field(default=0.7, description="Probability of wind direction change")
    max_step: float = Field(default=10.0, description="Maximum step size per tick")

    # Bezier curve parameters
    bezier_control_points: int = Field(default=3, description="Number of random control points for Bezier curves")
    bezier_distance_threshold: float = Field(default=200.0, description="Distance threshold to switch from Bezier to WindMouse")

    # Overshoot
    overshoot_probability: float = Field(default=0.15, description="Probability of overshooting target")
    overshoot_distance_range: tuple[float, float] = Field(default=(5.0, 20.0), description="Min/max overshoot distance in px")

    # Jitter
    jitter_sigma: float = Field(default=0.5, description="Gaussian jitter sigma in px")

    # Timing
    move_frequency_hz: float = Field(default=125.0, description="Mouse event dispatch frequency")

    # Click
    click_offset_sigma: float = Field(default=3.0, description="Random click position offset sigma in px")
    press_duration_range: tuple[float, float] = Field(default=(0.05, 0.15), description="Mouse button press duration range in seconds")


class KeyboardConfig(BaseModel):
    """Keyboard dynamics configuration."""

    # Inter-key delay (lognormal distribution)
    delay_mu: float = Field(default=4.17, description="Lognormal mu for inter-key delay (exp(4.17)≈65ms)")
    delay_sigma: float = Field(default=0.3, description="Lognormal sigma for inter-key delay")

    # Bigram speedup/slowdown
    common_bigram_factor: float = Field(default=0.7, description="Speed factor for common letter pairs")
    shift_char_factor: float = Field(default=1.3, description="Speed factor for shifted characters")

    # Word boundary
    word_pause_range: tuple[float, float] = Field(default=(0.08, 0.16), description="Extra pause after space (seconds)")

    # Typo simulation
    typo_probability: float = Field(default=0.02, description="Probability of making a typo")
    typo_pause_range: tuple[float, float] = Field(default=(0.2, 0.4), description="Pause before correcting typo (seconds)")


class ScrollConfig(BaseModel):
    """Scroll dynamics configuration."""

    # Impulse phase
    impulse_count_range: tuple[int, int] = Field(default=(1, 3), description="Number of initial large scroll impulses")
    impulse_delta_range: tuple[int, int] = Field(default=(80, 200), description="Delta Y range for impulse events")

    # Inertia phase
    inertia_decay: float = Field(default=0.85, description="Velocity decay factor per frame")
    inertia_frame_interval: float = Field(default=0.016, description="Frame interval in seconds (~60fps)")
    inertia_stop_threshold: float = Field(default=2.0, description="Stop when velocity drops below this")

    # Correction
    correction_probability: float = Field(default=0.2, description="Probability of small correction scroll")
    correction_delta_range: tuple[int, int] = Field(default=(10, 30), description="Delta Y range for correction")


class TimingConfig(BaseModel):
    """Action timing configuration."""

    # Pre-action delay
    pre_action_delay_range: tuple[float, float] = Field(default=(0.1, 0.3), description="Delay before actions (seconds)")

    # Reading time per character
    reading_time_per_char: float = Field(default=0.03, description="Simulated reading time per character (seconds)")
    reading_time_max: float = Field(default=2.0, description="Maximum reading time (seconds)")


class HumanBehaviorConfig(BaseModel):
    """Master configuration for human-like browser behavior."""

    mouse: MouseConfig = Field(default_factory=MouseConfig)
    keyboard: KeyboardConfig = Field(default_factory=KeyboardConfig)
    scroll: ScrollConfig = Field(default_factory=ScrollConfig)
    timing: TimingConfig = Field(default_factory=TimingConfig)

    # Feature toggles
    enable_stealth: bool = Field(default=True, description="Enable stealth JS injection")
    enable_human_mouse: bool = Field(default=True, description="Enable human-like mouse movement")
    enable_human_keyboard: bool = Field(default=True, description="Enable human-like keyboard dynamics")
    enable_human_scroll: bool = Field(default=True, description="Enable human-like scrolling")
