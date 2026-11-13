"""Pointer interpretation: tap, double-tap, drag and throw.

Kept free of Qt so the tap/drag rules can be unit tested.
"""

import math

from .physics import throw_velocity


class Pointer:
    DRAG_THRESHOLD = 7.0     # screen px of travel before it counts as a drag
    DOUBLE_WINDOW = 0.34     # seconds
    DOUBLE_DISTANCE = 26.0   # screen px

    def __init__(self):
        self.down = False
        self.dragging = False
        self.down_pos = (0.0, 0.0)
        self.down_time = 0.0
        self.samples = []
        self.last_tap_time = -10.0
        self.last_tap_pos = (0.0, 0.0)

    def press(self, pos, now):
        self.down = True
        self.dragging = False
        self.down_pos = pos
        self.down_time = now
        self.samples = [(pos, now)]

    def move(self, pos, now):
        if not self.down:
            return False
        self.samples.append((pos, now))
        if len(self.samples) > 40:
            self.samples = self.samples[-40:]
        if not self.dragging:
            dx = pos[0] - self.down_pos[0]
            dy = pos[1] - self.down_pos[1]
            if math.hypot(dx, dy) > self.DRAG_THRESHOLD:
                self.dragging = True
        return self.dragging

    def release(self, pos, now):
        if not self.down:
            return None
        self.samples.append((pos, now))
        was_dragging = self.dragging
        self.down = False
        self.dragging = False
        action = {"pos": pos, "held": now - self.down_time}

        if was_dragging:
            action["drag"] = throw_velocity(self.samples, now)
            return action

        dx = pos[0] - self.last_tap_pos[0]
        dy = pos[1] - self.last_tap_pos[1]
        double = (
            now - self.last_tap_time <= self.DOUBLE_WINDOW
            and math.hypot(dx, dy) <= self.DOUBLE_DISTANCE
        )
        if double:
            self.last_tap_time = -10.0
            action["double"] = True
        else:
            self.last_tap_time = now
            self.last_tap_pos = pos
            action["tap"] = True
        return action
