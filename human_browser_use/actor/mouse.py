"""HumanMouse - Mouse actor with human-like trajectories."""

import asyncio
import random
from typing import Literal

from browser_use.actor.mouse import Mouse

from human_browser_use.config import MouseConfig
from human_browser_use.behavior.mouse_trajectory import MouseTrajectory


class HumanMouse(Mouse):
    """Mouse with human-like movement trajectories.

    Extends the base Mouse class to move along realistic paths
    instead of teleporting to positions.
    """

    def __init__(self, *args, config: MouseConfig | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = config or MouseConfig()
        self._trajectory = MouseTrajectory(self._config)
        self._current_x: float = 0.0
        self._current_y: float = 0.0

    async def move(self, x: float, y: float, steps: int | None = None) -> None:
        """Move mouse along a human-like trajectory to (x, y)."""
        points = self._trajectory.generate(self._current_x, self._current_y, x, y)
        interval = 1.0 / self._config.move_frequency_hz

        for px, py in points:
            await super().move(px, py, steps=1)
            await asyncio.sleep(interval)

        self._current_x = x
        self._current_y = y

    async def click(
        self,
        x: float,
        y: float,
        button: Literal['left', 'right', 'middle'] = 'left',
        click_count: int = 1,
    ) -> None:
        """Click with human-like trajectory and variable press duration."""
        # Apply click offset
        dx, dy = random.gauss(0, self._config.click_offset_sigma), random.gauss(0, self._config.click_offset_sigma)
        target_x, target_y = x + dx, y + dy

        # Move to position with trajectory
        await self.move(target_x, target_y)

        # Press and release with variable duration
        await self.down(button, click_count)
        await asyncio.sleep(self._trajectory.get_press_duration())
        await self.up(button, click_count)

    async def scroll(
        self,
        x: float,
        y: float,
        delta_x: float,
        delta_y: float,
    ) -> None:
        """Scroll with mouse move to position first."""
        # Move to scroll position
        await self.move(x + random.uniform(-30, 30), y + random.uniform(-30, 30))
        await asyncio.sleep(random.uniform(0.05, 0.1))

        # Delegate to parent scroll
        await super().scroll(x, y, delta_x, delta_y)
