"""Faces.

Hard rule from the brief: only the face and its emotion indicators may change.
This module therefore paints strictly inside the 12x8 face rect (x 13..26,
y 20..29). It never touches the silhouette, sprout, hands, feet or the palette.

Expressions: neutral, sad, happy, surprised, angry, plus two transient faces
that are part of daily life: eating and sleeping.
"""

from .palette import DEEP, INK, PAPER, SHADE, rgba

FACE_X0, FACE_X1 = 11, 28
FACE_Y0, FACE_Y1 = 20, 30

EYE_Y = 22
EYE_L = 15          # left eye left edge (3 wide)
EYE_R = 22          # right eye left edge
MOUTH_Y = 27


def _px(img, x, y, color):
    if FACE_X0 <= x < FACE_X1 and FACE_Y0 <= y < FACE_Y1:
        img[y, x] = rgba(color)


def _rect(img, x, y, w, h, color):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            _px(img, xx, yy, color)


def _dither(img, x, y, w, h, color):
    for yy in range(h):
        for xx in range(w):
            if (xx + yy) % 2 == 0:
                _px(img, x + xx, y + yy, color)


def _open_eye(img, x, y, w=3, h=4, look=(0, 0)):
    lx, ly = look
    x += lx
    y += ly
    _rect(img, x, y, w, h, INK)
    _px(img, x, y + 1, PAPER)


def _closed_up(img, x, y, look=(0, 0)):
    """Happy ^ eye."""
    lx, ly = look
    x += lx
    y += ly
    _px(img, x, y + 2, INK)
    _px(img, x + 1, y + 1, INK)
    _px(img, x + 2, y + 2, INK)


def _closed_line(img, x, y, look=(0, 0)):
    lx, ly = look
    _rect(img, x + lx, y + 3 + ly, 3, 1, INK)


def _mouth(img, kind, chew=0.0):
    if kind == "flat":
        _rect(img, 19, MOUTH_Y, 2, 1, INK)
    elif kind == "small":
        _rect(img, 18, MOUTH_Y, 3, 1, INK)
    elif kind == "frown_sad":
        _px(img, 18, MOUTH_Y + 1, INK)
        _px(img, 19, MOUTH_Y, INK)
        _px(img, 20, MOUTH_Y, INK)
        _px(img, 21, MOUTH_Y + 1, INK)
    elif kind == "frown_angry":
        _px(img, 18, MOUTH_Y, INK)
        _px(img, 19, MOUTH_Y + 1, INK)
        _px(img, 20, MOUTH_Y, INK)
    elif kind == "happy":
        _rect(img, 18, MOUTH_Y, 4, 2, INK)
        _px(img, 19, MOUTH_Y + 1, PAPER)
        _px(img, 20, MOUTH_Y + 1, PAPER)
    elif kind == "surprised":
        _rect(img, 19, MOUTH_Y, 2, 2, INK)
    elif kind == "sleep":
        _rect(img, 19, MOUTH_Y, 2, 1, INK)
    elif kind == "eating":
        h = 2 + (1 if chew > 0.45 else 0)
        _rect(img, 18, MOUTH_Y - 1, 3, h, INK)
        _px(img, 19, MOUTH_Y + h - 1, DEEP)
    elif kind == "sing":
        h = 2 + (1 if chew > 0.35 else 0)
        _rect(img, 19, MOUTH_Y - 1, 2, h, INK)


def draw_face(img, expr="neutral", t=0.0, look=(0, 0), blink=False, chew=0.0):
    lx = max(-1, min(1, int(look[0])))
    ly = max(-1, min(1, int(look[1])))
    look = (lx, ly)

    if expr == "happy":
        for x in (EYE_L, EYE_R):
            _closed_up(img, x, EYE_Y + 1, look)
        _mouth(img, "happy")
        for x in (12, 25):
            _dither(img, x, 26, 3, 2, SHADE)
        return

    if expr == "surprised":
        for x, w in ((EYE_L - 1, 4), (EYE_R - 1, 4)):
            _rect(img, x + lx, EYE_Y - 1 + ly, w, 4, INK)
            _px(img, x + lx + 1, EYE_Y + ly, PAPER)
        _mouth(img, "surprised")
        return

    if expr == "sad":
        for x, outer in ((EYE_L, -1), (EYE_R, 1)):
            _rect(img, x + lx, EYE_Y + 1 + ly, 3, 3, INK)
            _px(img, x + lx, EYE_Y + 2 + ly, PAPER)
            _px(img, x + lx + (2 if outer > 0 else 0), EYE_Y + ly, INK)
        _px(img, 14, 26, INK)
        _px(img, 14, 27, INK)
        _mouth(img, "frown_sad")
        return

    if expr == "angry":
        for x in (EYE_L, EYE_R):
            _rect(img, x + lx, EYE_Y + 1 + ly, 3, 3, INK)
            _px(img, x + lx, EYE_Y + 2 + ly, PAPER)
        for (bx, by) in ((14, 21), (15, 21), (16, 22)):
            _px(img, bx + lx, by + ly, INK)
        for (bx, by) in ((25, 21), (24, 21), (23, 22)):
            _px(img, bx + lx, by + ly, INK)
        _mouth(img, "frown_angry")
        return

    if expr == "eating":
        for x in (EYE_L, EYE_R):
            _closed_up(img, x, EYE_Y + 1, look)
        _mouth(img, "eating", chew)
        return

    if expr == "sing":
        for x in (EYE_L, EYE_R):
            _closed_up(img, x, EYE_Y + 1, look)
        _mouth(img, "sing", chew)
        return

    if expr == "sleep":
        for x in (EYE_L, EYE_R):
            _closed_line(img, x, EYE_Y, look)
        _mouth(img, "sleep")
        return

    # neutral
    for x in (EYE_L, EYE_R):
        if blink:
            _closed_line(img, x, EYE_Y, look)
        else:
            _open_eye(img, x, EYE_Y, look=look)
    _mouth(img, "flat")
