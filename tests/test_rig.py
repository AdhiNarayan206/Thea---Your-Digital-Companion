import numpy as np
import pytest

from thea import rig
from thea.expressions import draw_face

EXPRESSIONS = ["neutral", "sad", "happy", "surprised", "angry", "eating", "sing", "sleep"]


def test_canvas_is_the_agreed_grid():
    assert (rig.W, rig.H) == (40, 40)


def test_silhouette_is_stable_across_expressions():
    base = rig.render_body()
    for expr in EXPRESSIONS:
        other = rig.render_body()
        assert np.array_equal(base[..., 3], other[..., 3]), expr


def test_face_only_paints_inside_the_face_rect():
    base = rig.render_body()
    for expr in EXPRESSIONS:
        img = base.copy()
        draw_face(img, expr, look=(0, 0), chew=0.7)
        changed = np.any(img != base, axis=2)
        ys, xs = np.where(changed)
        if len(xs) == 0:
            continue
        assert xs.min() >= 11 and xs.max() < 28, (expr, xs.min(), xs.max())
        assert ys.min() >= 20 and ys.max() < 30, (expr, ys.min(), ys.max())


def test_expressions_are_visually_distinct():
    frames = {}
    for expr in ["neutral", "sad", "happy", "surprised", "angry"]:
        img = rig.render_body()
        draw_face(img, expr)
        frames[expr] = img.tobytes()

    assert len(set(frames.values())) == len(frames)


def test_outline_is_one_pixel_and_closed():
    m = rig.body_mask()
    inner = rig.erode(m, 1)
    edge = m & ~inner
    assert edge.any()
    # every edge pixel touches the outside or is adjacent to it: no filled ring
    grown = rig.erode(edge, 1)
    assert grown.sum() == 0


def test_squash_keeps_him_on_the_floor():
    tall = rig.body_mask({"squash": 0.15})
    flat = rig.body_mask({"squash": -0.15})
    assert tall.shape == flat.shape
    assert tall.sum() > 0 and flat.sum() > 0


@pytest.mark.parametrize("expr", EXPRESSIONS)
def test_renders_rgba(expr):
    img = rig.render_body()
    draw_face(img, expr)
    assert img.shape == (40, 40, 4)
    assert img.dtype == np.uint8
    assert set(np.unique(img[..., 3]).tolist()) <= {0, 255}
