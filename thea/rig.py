"""Thea's body, drawn procedurally on a 40x40 pixel grid.

The character is authored once, here. Every proportion in this module is a
closed-form number, so the face layer (thea/expressions.py) can change freely
without the body ever shifting. tests/test_rig.py asserts that.

Coordinates are pixel centres (x + 0.5, y + 0.5) so rotated ellipses sample
cleanly. The canvas is:
    y  0 .. 16   sprout (steam + two leaves)
    y 15 .. 34   round body
    y 36 .. 38   feet
    y 37 .. 39   dithered contact shadow
"""

import math

import numpy as np

from .palette import DEEP, INK, PAPER, SHADE, rgba

W = H = 40
CX = 20.0
BASE_Y = 37.0

BODY = dict(cx=20.0, cy=24.6, rx=11.7, ry=9.7)
FEET = [(-5.7, 36.1, 3.7, 2.1), (5.7, 36.1, 3.7, 2.1)]
HANDS = [(-13.2, 28.0, 2.8, 2.5), (13.2, 28.0, 2.8, 2.5)]
STEM = dict(cx=20.0, cy=12.4, rx=1.35, ry=4.1)
LEAVES = [
    # (offset x, offset y, angle degrees)  left leaf points up-left
    (-4.7, 8.7, 30.0),
    (4.7, 8.7, -30.0),
]


def _grid():
    ys, xs = np.mgrid[0:H, 0:W]
    return xs + 0.5, ys + 0.5


def ellipse(X, Y, cx, cy, rx, ry, deg=0.0):
    rad = math.radians(deg)
    ca, sa = math.cos(rad), math.sin(rad)
    dx, dy = X - cx, Y - cy
    u = dx * ca + dy * sa
    v = -dx * sa + dy * ca
    return (u / rx) ** 2 + (v / ry) ** 2 <= 1.0


def erode(mask, steps=1):
    """Shrink a boolean mask by `steps` 4-connected pixels."""
    out = mask.copy()
    for _ in range(steps):
        s = out.copy()
        s[1:, :] &= out[:-1, :]
        s[:-1, :] &= out[1:, :]
        s[:, 1:] &= out[:, :-1]
        s[:, :-1] &= out[:, 1:]
        out = s
    return out


def body_mask(pose=None):
    """Silhouette of Thea. Pose only squashes/leans the same shape."""
    p = pose or {}
    X, Y = _grid()

    squash = float(p.get("squash", 0.0))
    sy = max(0.55, 1.0 + squash)
    sx = 1.0 / math.sqrt(sy)
    Xb = (X - CX) / sx + CX
    Yb = BASE_Y - (BASE_Y - Y) / sy

    lean = float(p.get("tilt", 0.0))
    if lean:
        Xb = Xb - (BASE_Y - Yb) * lean

    sway = float(p.get("sway", 0.0))
    arm = float(p.get("arm", 0.0))

    m = ellipse(Xb, Yb, BODY["cx"], BODY["cy"], BODY["rx"], BODY["ry"])

    for dx, cy, rx, ry in HANDS:
        side = -1.0 if dx < 0 else 1.0
        m |= ellipse(Xb, Yb, CX + dx, cy + arm * side * -1.0, rx, ry)

    m |= ellipse(Xb, Yb, STEM["cx"] + sway * 0.55, STEM["cy"], STEM["rx"], STEM["ry"])

    for i, (dx, cy, deg) in enumerate(LEAVES):
        side = -1.0 if dx < 0 else 1.0
        m |= ellipse(
            Xb,
            Yb,
            CX + dx + sway * 0.5 * side,
            cy + abs(sway) * 0.18,
            5.1,
            2.45,
            deg + sway * 7.0 * side,
        )

    for dx, cy, rx, ry in FEET:
        m |= ellipse(X, Y, CX + dx, cy, rx, ry)

    return m


def shadow_mask(pose=None):
    X, Y = _grid()
    m = ellipse(X, Y, CX, 38.4, 10.6, 1.55)
    lit = ((np.arange(H)[:, None] + np.arange(W)[None, :]) % 2) == 0
    return m & lit


def _line_points(x0, y0, x1, y1):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        t = i / n
        yield int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t))


def render_body(pose=None):
    """Return an (H, W, 4) uint8 RGBA image with no face drawn."""
    pose = pose or {}
    img = np.zeros((H, W, 4), np.uint8)

    sh = shadow_mask()
    img[sh] = rgba(SHADE)

    m = body_mask(pose)
    inner = erode(m, 1)
    ring2 = inner & ~erode(inner, 1)

    img[inner] = rgba(PAPER)

    X, Y = _grid()
    img[ring2 & (X > CX) & (Y > 24.0)] = rgba(SHADE)

    # leaf veins: one inset stroke per leaf, the only interior line work
    for dx, cy, deg in LEAVES:
        side = -1.0 if dx < 0 else 1.0
        x0, y0 = CX + side * 1.6, 12.4
        x1, y1 = CX + dx * 1.35, cy + 0.2
        for x, y in _line_points(x0, y0, x1, y1):
            if 0 <= x < W and 0 <= y < H and m[y, x]:
                img[y, x] = rgba(DEEP)

    img[m & ~inner] = rgba(INK)
    return img
