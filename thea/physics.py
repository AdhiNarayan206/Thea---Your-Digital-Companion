"""Pure motion helpers. No Qt, no state - easy to unit test."""

from . import config


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def approach(value, target, max_step):
    if value < target:
        return min(value + max_step, target)
    return max(value - max_step, target)


def edges(x, size, work_x, work_w, vx):
    """Keep him inside the work area; returns (x, vx, hit_edge)."""
    lo, hi = work_x, work_x + work_w - size
    if x < lo:
        return lo, abs(vx) * 0.35, True
    if x > hi:
        return hi, -abs(vx) * 0.35, True
    return x, vx, False


def throw_velocity(samples, now, window=0.12):
    """Average pointer velocity over the last `window` seconds of samples."""
    recent = [(p, t) for p, t in samples if now - t <= window]
    if len(recent) < 2:
        return 0.0, 0.0
    (x0, y0), t0 = recent[0]
    (x1, y1), t1 = recent[-1]
    dt = t1 - t0
    if dt <= 0.001:
        return 0.0, 0.0
    vx = clamp((x1 - x0) / dt, -config.MAX_THROW, config.MAX_THROW)
    vy = clamp((y1 - y0) / dt, -config.MAX_THROW, config.MAX_THROW)
    return vx, vy


def feed_zone(work_y, work_h):
    return work_y + int(work_h * config.FEED_ZONE)
