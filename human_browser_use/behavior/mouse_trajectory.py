"""Mouse trajectory generation with smooth Bezier curves and realistic speed.

Real human mouse movement:
- One continuous smooth arc (not two phases)
- Fast in the middle, slow at start and especially at the end
- Final approach: cursor drifts in slowly, tiny imprecision from hand settling
- NOT random wobble — just naturally less precise at low speed
"""

import math
import random
from human_browser_use.config import MouseConfig


class MouseTrajectory:
    """Generates human-like mouse movement trajectories."""

    def __init__(self, config: MouseConfig | None = None):
        self.config = config or MouseConfig()

    def generate_with_timing(self, start_x: float, start_y: float, end_x: float, end_y: float) -> list[tuple[float, float, float]]:
        """Generate trajectory with per-point delay.

        Single continuous curve with variable speed:
        - Ramp up quickly
        - Very fast cruise (2.5x average)
        - Gradual deceleration, getting very slow at the end
        """
        distance = math.hypot(end_x - start_x, end_y - start_y)
        if distance < 1:
            return [(end_x, end_y, 0.005)]

        # Generate smooth path
        dense_path = self._smooth_bezier(start_x, start_y, end_x, end_y)
        arc = self._compute_arc(dense_path)
        total_arc = arc[-1] or 1.0

        # Total duration: fast for long moves
        total_duration = 0.05 + 0.07 * math.log2(1 + distance / 20)
        total_duration *= random.uniform(0.85, 1.15)

        # Resample with speed profile
        result = []
        event_interval = 1.0 / 125.0
        arc_pos = 0.0

        while arc_pos < total_arc:
            t = arc_pos / total_arc

            # Speed profile: fast cruise + deep decel at end
            if t < 0.05:
                # Ramp up
                s = t / 0.05
                speed_mult = 0.3 + 2.2 * s * s
            elif t < 0.75:
                # Fast cruise
                speed_mult = 2.3 + 0.2 * math.sin(t * 8.0)
            else:
                # Deep deceleration: 2.5x → 0.3x over last 25%
                s = (t - 0.75) / 0.25
                # Smooth cubic ease-out decel
                speed_mult = 2.5 * (1 - s) ** 2 + 0.3 * s

            base_speed = total_arc / total_duration
            advance = base_speed * speed_mult * event_interval
            advance *= random.uniform(0.93, 1.07)
            arc_pos = min(arc_pos + advance, total_arc)

            px, py = self._interp_arc(dense_path, arc, arc_pos)

            # At low speed (end), the hand naturally drifts a tiny bit
            # This is NOT wobble — just sub-pixel imprecision
            if t > 0.85:
                drift = (t - 0.85) / 0.15  # 0→1
                # Very small: 0.3-1.5px perpendicular drift
                sigma = 0.3 + drift * 1.2
                px += random.gauss(0, sigma)
                py += random.gauss(0, sigma)

            delay = event_interval / max(speed_mult, 0.2)
            delay *= random.uniform(0.92, 1.08)
            result.append((px, py, delay))

            if arc_pos >= total_arc:
                break

        # Overshoot (post-move correction)
        overshoot_prob = self.config.overshoot_probability
        if distance > 300:
            overshoot_prob = min(0.55, overshoot_prob + 0.15)
        if random.random() < overshoot_prob and distance > 40:
            result.extend(self._overshoot_correction(end_x, end_y, distance))

        # Ensure exact endpoint
        if result:
            result[-1] = (end_x, end_y, result[-1][2])

        return result

    def _overshoot_correction(self, end_x, end_y, distance):
        """Small overshoot then drift back."""
        min_os, max_os = self.config.overshoot_distance_range
        os_dist = random.uniform(min_os, max_os)
        if distance > 300:
            os_dist *= 1.3

        # Overshoot direction: roughly continues approach
        angle = random.uniform(0, 2 * math.pi)
        osx = end_x + math.cos(angle) * os_dist
        osy = end_y + math.sin(angle) * os_dist

        points = [(osx, osy, random.uniform(0.012, 0.025))]

        # Drift back slowly (3-5 points, decelerating)
        steps = random.randint(3, 5)
        for i in range(1, steps + 1):
            t = i / steps
            # Ease-out drift
            t_ease = 1 - (1 - t) ** 2
            bx = osx + (end_x - osx) * t_ease
            by = osy + (end_y - osy) * t_ease
            # Tiny natural drift
            bx += random.gauss(0, 0.5 * (1 - t))
            by += random.gauss(0, 0.5 * (1 - t))
            points.append((bx, by, random.uniform(0.015, 0.035)))

        return points

    def generate(self, start_x: float, start_y: float, end_x: float, end_y: float) -> list[tuple[float, float]]:
        """Generate trajectory (positions only)."""
        return [(p[0], p[1]) for p in self.generate_with_timing(start_x, start_y, end_x, end_y)]

    def _smooth_bezier(self, start_x, start_y, end_x, end_y):
        """Dense smooth Bezier path."""
        distance = math.hypot(end_x - start_x, end_y - start_y)
        angle = math.atan2(end_y - start_y, end_x - start_x)
        perp = angle + math.pi / 2

        control_points = [(start_x, start_y)]
        for i in range(2):
            t = (i + 1) / 3
            cx = start_x + t * (end_x - start_x)
            cy = start_y + t * (end_y - start_y)
            max_off = min(distance * 0.06, 30)
            cx += random.gauss(0, max_off) * math.cos(perp)
            cy += random.gauss(0, max_off) * math.sin(perp)
            control_points.append((cx, cy))
        control_points.append((end_x, end_y))

        num_pts = max(30, int(distance))
        points = []
        for i in range(num_pts + 1):
            t = i / num_pts
            pts = list(control_points)
            while len(pts) > 1:
                pts = [((1 - t) * pts[j][0] + t * pts[j + 1][0],
                        (1 - t) * pts[j][1] + t * pts[j + 1][1])
                       for j in range(len(pts) - 1)]
            points.append(pts[0])
        return points

    @staticmethod
    def _compute_arc(path):
        arc = [0.0]
        for i in range(1, len(path)):
            arc.append(arc[-1] + math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]))
        return arc

    @staticmethod
    def _interp_arc(path, arc, target_arc):
        if target_arc <= 0:
            return path[0]
        if target_arc >= arc[-1]:
            return path[-1]
        lo, hi = 0, len(arc) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if arc[mid] <= target_arc:
                lo = mid
            else:
                hi = mid
        seg_len = arc[hi] - arc[lo]
        if seg_len < 1e-9:
            return path[lo]
        frac = (target_arc - arc[lo]) / seg_len
        return (path[lo][0] + frac * (path[hi][0] - path[lo][0]),
                path[lo][1] + frac * (path[hi][1] - path[lo][1]))

    def get_click_offset(self, element_width, element_height):
        sigma = self.config.click_offset_sigma
        max_dx = element_width / 2 * 0.7
        max_dy = element_height / 2 * 0.7
        return (max(-max_dx, min(max_dx, random.gauss(0, sigma))),
                max(-max_dy, min(max_dy, random.gauss(0, sigma))))

    def get_press_duration(self):
        return random.uniform(*self.config.press_duration_range)
