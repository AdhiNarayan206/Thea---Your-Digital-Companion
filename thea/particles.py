"""Emotion indicators and small effects.

Indicators live outside the silhouette on purpose: sadness gets a falling tear,
surprise a "!", anger steam, sleep z's, happiness hearts. That keeps the body
untouched by emotion, as the brief requires.
"""

import random

INK = (0, 0, 0)
SHADE = (185, 185, 185)
DEEP = (105, 105, 105)

GLYPHS = {
    # 1 px = 1 logical sprite pixel, scaled up at draw time
    "heart": [".#.#.", "#####", "#####", ".###.", "..#.."],
    "sparkle": ["..#..", ".###.", "#####", ".###.", "..#.."],
    "note": ["..##.", "..#..", "..#..", "###..", "###.."],
    "bang": ["#", "#", "#", "."],
    "tear": ["#", "#"],
    "steam": ["##", "##"],
    "crumb": ["#"],
    "dust": ["#"],
    "zzz": ["###", "..#", ".#.", "###"],
    "drop": ["##", "##"],
}

COLORS = {
    "heart": INK,
    "sparkle": INK,
    "note": INK,
    "bang": INK,
    "tear": DEEP,
    "steam": SHADE,
    "crumb": DEEP,
    "dust": SHADE,
    "zzz": INK,
    "drop": SHADE,
}

FLOATERS = {"heart", "sparkle", "note", "bang", "steam", "zzz"}


class Particle:
    __slots__ = ("kind", "x", "y", "vx", "vy", "life", "max_life")

    def __init__(self, kind, x, y, vx, vy, life):
        self.kind = kind
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life


class Particles:
    def __init__(self, limit=220):
        self.items = []
        self.limit = limit

    def spawn(self, kind, x, y, n=1, spread=4.0, vx=0.0, vy=0.0, life=1.0, jitter=1.0):
        for _ in range(n):
            if len(self.items) >= self.limit:
                return
            self.items.append(
                Particle(
                    kind,
                    x + random.uniform(-spread, spread),
                    y + random.uniform(-spread, spread),
                    vx + random.uniform(-25, 25) * jitter,
                    vy + random.uniform(-20, 20) * jitter,
                    life * random.uniform(0.7, 1.25),
                )
            )

    def update(self, dt):
        alive = []
        for p in self.items:
            p.life -= dt
            if p.life <= 0:
                continue
            p.x += p.vx * dt
            p.y += p.vy * dt
            if p.kind in FLOATERS:
                p.vy -= 26 * dt
                p.vx *= 1.0 - 0.7 * dt
                p.vy *= 1.0 - 0.2 * dt
            else:
                p.vy += 620 * dt
            alive.append(p)
        self.items = alive

    def clear(self):
        self.items.clear()

    def bounds(self):
        if not self.items:
            return None
        x0 = min(p.x for p in self.items)
        y0 = min(p.y for p in self.items)
        x1 = max(p.x for p in self.items)
        y1 = max(p.y for p in self.items)
        return x0, y0, x1, y1

    def draw(self, painter, scale, origin=(0, 0)):
        from PySide6.QtCore import QRect
        from PySide6.QtGui import QColor

        ox, oy = origin
        for p in self.items:
            if p.life < 0.3 and int(p.life * 22) % 2 == 0:
                continue
            glyph = GLYPHS.get(p.kind)
            if not glyph:
                continue
            color = QColor(*COLORS[p.kind])
            gx = round((p.x - ox) / scale) * scale + ox
            gy = round((p.y - oy) / scale) * scale + oy
            for row, line in enumerate(glyph):
                for col, ch in enumerate(line):
                    if ch == "#":
                        painter.fillRect(
                            QRect(gx + col * scale, gy + row * scale, scale, scale), color
                        )
