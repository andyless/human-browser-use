"""Scroll dynamics with impulse-inertia physics model."""

import random
from human_browser_use.config import ScrollConfig


class ScrollDynamics:
    """Generates human-like scroll event sequences."""

    def __init__(self, config: ScrollConfig | None = None):
        self.config = config or ScrollConfig()

    def generate_scroll_events(self, total_pixels: int) -> list[dict]:
        """Generate a sequence of scroll events to achieve the target scroll distance.

        Returns list of dicts with keys:
            - delta_y: int, the scroll delta for this event
            - delay: float, delay in seconds before this event
        """
        if total_pixels == 0:
            return []

        cfg = self.config
        direction = 1 if total_pixels > 0 else -1
        remaining = abs(total_pixels)
        events = []

        # Phase 1: Impulse - large initial scroll events
        num_impulses = random.randint(*cfg.impulse_count_range)
        impulse_total = 0

        for i in range(num_impulses):
            if impulse_total >= remaining:
                break
            delta = random.randint(*cfg.impulse_delta_range)
            delta = min(delta, remaining - impulse_total)
            if delta <= 0:
                break
            impulse_total += delta
            events.append({
                'delta_y': delta * direction,
                'delay': random.uniform(0.01, 0.04) if i > 0 else 0.0,
            })

        # Phase 2: Inertia - decaying velocity
        velocity = float(events[-1]['delta_y']) if events else float(remaining * direction)
        velocity = abs(velocity)

        while velocity > cfg.inertia_stop_threshold and impulse_total < remaining:
            velocity *= cfg.inertia_decay
            delta = int(round(velocity))
            if delta < 1:
                break
            delta = min(delta, remaining - impulse_total)
            if delta <= 0:
                break
            impulse_total += delta
            events.append({
                'delta_y': delta * direction,
                'delay': cfg.inertia_frame_interval,
            })

        # Phase 3: Correction (optional)
        scrolled = sum(abs(e['delta_y']) for e in events)
        undershoot = remaining - scrolled

        if undershoot > 0:
            # Always correct remaining distance
            events.append({
                'delta_y': undershoot * direction,
                'delay': random.uniform(0.05, 0.15),
            })
        elif random.random() < cfg.correction_probability and scrolled > remaining:
            # Small correction in opposite direction
            correction = random.randint(*cfg.correction_delta_range)
            correction = min(correction, scrolled - remaining)
            if correction > 0:
                events.append({
                    'delta_y': -correction * direction,
                    'delay': random.uniform(0.1, 0.25),
                })

        return events
