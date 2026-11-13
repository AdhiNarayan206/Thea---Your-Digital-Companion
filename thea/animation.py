"""Thea's state machine, physics and rendering glue."""

import math
import random

import numpy as np

from . import config, rig
from .expressions import draw_face
from .physics import approach, clamp, edges, feed_zone


class Thea:
    def __init__(self, work, stats, particles, audio, scale=None):
        self.work = tuple(work)  # (x, y, w, h) in screen pixels
        self.scale = float(scale or config.SCALE)
        self.size = rig.W * self.scale
        self.stats = stats
        self.particles = particles
        self.audio = audio

        self.x = float(self.work[0] + (self.work[2] - self.size) / 2)
        self.y = float(self.floor())
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.state = "idle"
        self.state_t = 0.0
        self.t = 0.0
        self.squash = 0.0
        self.cursor = (0, 0)
        self.look = (0, 0)

        self.surprised_t = 0.0
        self.angry_t = 0.0
        self.drag_time = 0.0
        self.run_target = None
        self.run_until = 0.0
        self.idle_t = 0.0

        self.blink_in = random.uniform(2.0, 4.0)
        self.blink_t = 0.0

        self._dust_t = 0.0
        self._emit_t = 0.0
        self._hitmask = self._build_hitmask()
        self.shelf_y = feed_zone(self.work[1], self.work[3])

    # -- geometry ---------------------------------------------------------
    def floor(self):
        return self.work[1] + self.work[3] - rig.H * self.scale

    def rect(self):
        return (
            int(round(self.x)),
            int(round(self.y)),
            self.size,
            self.size,
        )

    def center(self):
        return self.x + self.size / 2, self.y + self.size / 2

    def _build_hitmask(self):
        m = rig.body_mask()
        for sq in (-0.12, 0.08):
            m |= rig.body_mask({"squash": sq})
        # Dilate mask by 2 pixels so small scales remain easy to click/hover
        grow = m.copy()
        for _ in range(2):
            grow[1:, :] |= grow[:-1, :]
            grow[:-1, :] |= grow[1:, :]
            grow[:, 1:] |= grow[:, :-1]
            grow[:, :-1] |= grow[:, 1:]
        return grow

    def hit(self, px, py):
        lx = int(round((px - self.x) / self.scale))
        ly = int(round((py - self.y) / self.scale))
        if not (0 <= lx < rig.W and 0 <= ly < rig.H):
            # Generous bounding box margin at small sizes (padding = 6px)
            pad = max(4.0, 10.0 - self.scale)
            if (self.x - pad) <= px <= (self.x + self.size + pad) and (self.y - pad) <= py <= (self.y + self.size + pad):
                return True
            return False
        return bool(self._hitmask[ly, lx])

    def bowl_pos(self):
        return (
            self.x + self.size * 0.74,
            self.y + self.size * 0.84,
        )

    # -- mood -------------------------------------------------------------
    def expression(self):
        if self.state == "eat":
            return "eating"
        if self.state == "sing":
            return "sing"
        if self.state == "sleep":
            return "sleep"
        if self.state == "happy":
            return "happy"
        if self.state == "drag":
            return "surprised"
        if self.surprised_t > 0:
            return "surprised"
        if self.angry_t > 0:
            return "angry"
        if self.stats.fullness < 25:
            return "sad"
        return "neutral"

    def blinking(self):
        return self.blink_t > 0 and self.state not in ("sleep", "happy", "eat", "sing")

    # -- actions ----------------------------------------------------------
    def interact(self, cursor):
        """Space pressed while hovering Thea."""
        if self.state == "sleep":
            self.wake()
            return
        if self.state in ("eat", "sing"):
            return
        if self.state == "drag":
            return

        cx = self.x + self.size / 2
        if abs(cursor[0] - cx) < self.size * 0.5:
            side = 1.0 if cursor[0] >= cx else -1.0
            target = cursor[0] + side * self.size * 2.2
        else:
            target = cursor[0]

        self.run_target = target
        self.run_until = self.t + config.RUN_TIMEOUT
        self.state = "run"
        self.state_t = 0.0
        self.idle_t = 0.0
        self.audio.blip(760, 0.05, 0.16)

    def tap(self):
        if self.state == "sleep":
            self.wake()
            return
        if self.state in ("eat", "sing", "drag"):
            return
        self.vy = config.JUMP_VELOCITY
        self.state = "jump"
        self.state_t = 0.0
        self.squash = 0.10
        self.audio.blip(660, 0.06, 0.18)

    def double_tap(self):
        if self.state == "drag":
            return
        self.state = "happy"
        self.state_t = 0.0
        self.squash = 0.0
        self.stats.cheer(8)
        self.particles.spawn("heart", *self._head(), n=4, spread=self.size * 0.10, vy=-40)
        self.audio.chime()

    def begin_drag(self):
        self.state = "drag"
        self.state_t = 0.0
        self.drag_time = 0.0
        self.vx = self.vy = 0.0
        self.particles.clear()
        self.audio.blip(520, 0.05, 0.14)

    def drag_to(self, px, py):
        self.x = px - self.size / 2
        self.y = py - self.size * 0.45
        self.x = clamp(self.x, self.work[0], self.work[0] + self.work[2] - self.size)
        self.y = clamp(self.y, self.work[1], self.floor())
        self.drag_time += 1.0 / 60.0

    def release(self, vx, vy, held=None):
        self.vx = vx * config.THROW_DAMPING
        self.vy = vy * config.THROW_DAMPING
        held = self.drag_time if held is None else held
        if held > config.DRAG_ANGRY_AFTER:
            self.angry_t = 2.4
        elif held < 0.35:
            self.vx *= 0.5
            self.vy = min(self.vy, 0)
        self.state = "fall"
        self.state_t = 0.0

    def start_eat(self, x=None, y=None, on_shelf=False):
        if x is not None:
            self.x = clamp(
                x - self.size / 2, self.work[0], self.work[0] + self.work[2] - self.size
            )
        if on_shelf:
            self.y = float(max(self.work[1] + 4, self.shelf_y))
        else:
            self.y = float(self.floor())
        self.state = "eat"
        self.state_t = 0.0
        self.vx = self.vy = 0.0
        self.stats.feed()
        self.particles.spawn("crumb", *self._mouth_point(), n=3, spread=self.size * 0.05)

    def sing(self):
        if self.state == "drag":
            return
        if self.state == "sleep":
            self.wake()
        self.state = "sing"
        self.state_t = 0.0
        self.vx = self.vy = 0.0
        self.audio.sing()

    def sleep(self):
        if self.state == "drag":
            return
        self.state = "sleep"
        self.state_t = 0.0
        self.vx = self.vy = 0.0
        self.audio.stop()

    def wake(self):
        if self.state == "sleep":
            self.state = "idle"
            self.state_t = 0.0
            self.surprised_t = 0.5
            self.particles.spawn("bang", *self._head(), n=2, spread=self.size * 0.1, vy=-30)

    def toggle_sleep(self):
        if self.state == "sleep":
            self.wake()
        else:
            self.sleep()

    # -- helpers ----------------------------------------------------------
    def _head(self):
        return (self.x + self.size * 0.5, self.y + self.size * 0.22)

    def _mouth_point(self):
        return (self.x + self.size * 0.5, self.y + self.size * 0.70)

    def _feet(self):
        return (self.x + self.size * 0.5, self.y + self.size * 0.92)

    def _look_for_face(self):
        cx = self.x + self.size / 2
        dx = self.cursor[0] - cx
        dy = self.cursor[1] - (self.y + self.size * 0.55)
        lx = 0 if abs(dx) < self.size * 0.12 else (1 if dx > 0 else -1)
        ly = 0 if abs(dy) < self.size * 0.35 else (-1 if dy < 0 else 1)
        if self.facing < 0:
            lx = -lx
        return (lx, ly)

    def _pose(self):
        t = self.t
        state = self.state
        squash = self.squash
        arm = 0.0
        sway = math.sin(t * 1.6) * 0.40
        tilt = 0.0

        if state == "run":
            squash += math.sin(t * 15.0) * 0.022
            arm = math.sin(t * 15.0) * 0.9
            sway = math.sin(t * 6.0) * 0.8
            tilt = 0.03 * self.facing
        elif state == "happy":
            squash += math.sin(t * 11.0) * 0.05
            arm = 0.9
            sway = math.sin(t * 5.0) * 0.9
        elif state == "idle":
            squash += math.sin(t * 2.2) * 0.014
            sway = math.sin(t * 1.5) * 0.45
        elif state == "sleep":
            squash += math.sin(t * 1.05) * 0.02
            sway = math.sin(t * 1.1) * 0.25
        elif state == "drag":
            squash = -0.06
            arm = math.sin(t * 9.0) * 0.5
            sway = math.sin(t * 7.0) * 0.5

        return {"squash": squash, "tilt": tilt, "sway": sway, "arm": arm}

    # -- frame ------------------------------------------------------------
    def update(self, dt, cursor):
        dt = min(dt, 0.05)
        self.t += dt
        self.state_t += dt
        self.cursor = cursor
        self.stats.decay(dt)

        self.surprised_t = max(0.0, self.surprised_t - dt)
        self.angry_t = max(0.0, self.angry_t - dt)
        self.squash = approach(self.squash, 0.0, 0.85 * dt)

        self.blink_in -= dt
        if self.blink_in <= 0:
            self.blink_t = 0.13
            self.blink_in = random.uniform(2.4, 5.8)
        self.blink_t = max(0.0, self.blink_t - dt)

        if self.state in ("idle", "run"):
            self.idle_t += dt
            if self.state == "idle" and self.idle_t > 150 and self.stats.energy < 45:
                self.sleep()
        else:
            self.idle_t = 0.0

        if self.state == "run":
            cx = self.x + self.size / 2
            if self.run_target is None or self.t > self.run_until:
                self.state = "idle"
                self.state_t = 0.0
            else:
                direction = 1.0 if self.run_target > cx else -1.0
                if abs(self.run_target - cx) <= config.RUN_ARRIVE:
                    self._arrive()
                else:
                    self.facing = 1 if direction > 0 else -1
                    self.vx = direction * config.RUN_SPEED
                    self.x += self.vx * dt
                    self.x, _, hit = edges(
                        self.x, self.size, self.work[0], self.work[2], self.vx
                    )
                    if hit:
                        self.state = "idle"
                        self.state_t = 0.0
                        self.vx = 0.0
                    self._dust_t -= dt
                    if self._dust_t <= 0:
                        self._dust_t = 0.12
                        fx, fy = self._feet()
                        self.particles.spawn(
                            "dust",
                            fx - self.facing * self.size * 0.16,
                            fy,
                            n=2,
                            spread=self.size * 0.04,
                            vy=-20,
                            life=0.45,
                        )

        elif self.state in ("jump", "fall"):
            self.vy += config.GRAVITY * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.x, self.vx, _ = edges(
                self.x, self.size, self.work[0], self.work[2], self.vx
            )
            ground = self.floor()
            if self.y >= ground:
                impact = self.vy
                self.y = float(ground)
                self.vy = 0.0
                self.vx = 0.0
                self.state = "idle"
                self.state_t = 0.0
                self.squash = -min(0.22, abs(impact) / 5200.0)
                if impact > 500:
                    fx, fy = self._feet()
                    self.particles.spawn(
                        "dust", fx, fy, n=6, spread=self.size * 0.18, vy=-40, life=0.5
                    )

        elif self.state == "happy":
            self._emit_t -= dt
            if self._emit_t <= 0:
                self._emit_t = 0.22
                self.particles.spawn(
                    "heart", *self._head(), n=1, spread=self.size * 0.12, vy=-45, life=1.2
                )
            self.facing = 1 if self.cursor[0] >= self.x + self.size / 2 else -1
            if self.state_t > 1.9:
                self.state = "idle"
                self.state_t = 0.0

        elif self.state == "eat":
            self._emit_t -= dt
            if self._emit_t <= 0:
                self._emit_t = 0.34
                bx, by = self.bowl_pos()
                self.particles.spawn(
                    "crumb", bx, by - self.size * 0.04, n=2,
                    spread=self.size * 0.05, vy=-30, life=0.6
                )
            if self.state_t > config.EAT_SECONDS:
                self.state = "fall"
                self.state_t = 0.0
                self.vy = 40.0
                self.stats.cheer(4)

        elif self.state == "sing":
            self._emit_t -= dt
            if self._emit_t <= 0:
                self._emit_t = 0.30
                hx, hy = self._head()
                self.particles.spawn(
                    "note",
                    hx + self.size * random.uniform(0.12, 0.30),
                    hy,
                    n=1,
                    spread=self.size * 0.05,
                    vy=-55,
                    life=1.5,
                )
            if self.state_t > config.SING_SECONDS:
                self.state = "idle"
                self.state_t = 0.0
                self.stats.sing()

        elif self.state == "sleep":
            self.stats.rest(dt)
            self._emit_t -= dt
            if self._emit_t <= 0:
                self._emit_t = 0.85
                hx, hy = self._head()
                self.particles.spawn(
                    "zzz", hx + self.size * 0.20, hy, n=1,
                    spread=self.size * 0.06, vy=-28, life=2.0
                )

        elif self.state == "idle":
            target = 1 if self.cursor[0] >= self.x + self.size / 2 else -1
            if abs(self.cursor[0] - (self.x + self.size / 2)) > self.size * 0.15:
                self.facing = target

        if self.surprised_t > 0 and self.state != "drag":
            self._emit_t -= dt
            if self._emit_t <= 0:
                self._emit_t = 0.45
                hx, hy = self._head()
                self.particles.spawn(
                    "bang", hx + self.size * 0.18, hy - self.size * 0.05,
                    n=1, spread=self.size * 0.05, vy=-35, life=0.8
                )

        if self.expression() == "angry" and self.state != "sleep":
            self._emit_t -= dt
            if self._emit_t <= 0:
                self._emit_t = 0.5
                hx, hy = self._head()
                self.particles.spawn(
                    "steam", hx + self.size * 0.16, hy - self.size * 0.12,
                    n=1, spread=self.size * 0.04, vy=-45, life=1.0
                )

        if self.expression() == "sad" and self.state in ("idle", "run"):
            self._emit_t -= dt
            if self._emit_t <= 0:
                self._emit_t = 1.6
                self.particles.spawn(
                    "tear",
                    self.x + self.size * 0.36,
                    self.y + self.size * 0.63,
                    n=1, spread=0, vy=10, life=1.1, jitter=0.2
                )

        self.particles.update(dt)

    def _arrive(self):
        self.state = "jump"
        self.state_t = 0.0
        self.vy = -300.0
        self.vx = 0.0
        self.facing = 1 if self.run_target >= self.x + self.size / 2 else -1
        self.stats.cheer(1.5)
        self.particles.spawn("sparkle", *self._head(), n=3, spread=self.size * 0.1, vy=-30)
        self.audio.blip(880, 0.06, 0.14)

    def render(self):
        img = rig.render_body(self._pose())
        expr = self.expression()
        chew = (math.sin(self.t * 9.0) + 1.0) / 2.0
        draw_face(
            img,
            expr,
            t=self.t,
            look=self._look_for_face() if expr not in ("sleep", "happy") else (0, 0),
            blink=self.blinking(),
            chew=chew,
        )
        if self.facing < 0:
            img = img[:, ::-1, :]
        return np.ascontiguousarray(img)
