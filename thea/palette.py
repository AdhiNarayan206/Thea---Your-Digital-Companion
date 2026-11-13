"""The whole visual vocabulary: four values, no colour.

The style brief is black and white with subtle grayscale shading, so the
palette is deliberately a closed set. Anything that needs "lighter" or
"darker" uses a dither pattern rather than a new value.
"""

import numpy as np

INK = (0, 0, 0)
PAPER = (255, 255, 255)
SHADE = (185, 185, 185)
DEEP = (105, 105, 105)

CLEAR = (0, 0, 0, 0)

# 50% checkerboard used for blush and contact shadow: a fifth "tone" that
# costs no new palette entry.
CHECKER = np.array([[0, 1], [1, 0]], dtype=bool)


def rgba(color):
    if len(color) == 4:
        return color
    return (color[0], color[1], color[2], 255)


def checker_mask(h, w):
    """Checkerboard of shape (h, w); True on the lit squares."""
    return CHECKER[np.arange(h)[:, None] % 2, np.arange(w)[None, :] % 2]
