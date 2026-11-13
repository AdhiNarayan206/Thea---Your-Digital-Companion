"""Mood numbers and persistence."""

import json

from . import config


def _clamp(v):
    return 0.0 if v < 0 else 100.0 if v > 100 else v


class Stats:
    def __init__(self):
        self.fullness = 82.0
        self.joy = 74.0
        self.energy = 88.0
        self.fed = 0
        self.born_at = None
        self.load()

    # -- persistence ------------------------------------------------------
    def load(self):
        try:
            path = config.APP_DIR / "state.json"
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return
        self.fullness = _clamp(float(data.get("fullness", self.fullness)))
        self.joy = _clamp(float(data.get("joy", self.joy)))
        self.energy = _clamp(float(data.get("energy", self.energy)))
        self.fed = int(data.get("fed", 0))
        self.born_at = data.get("born_at")

    def save(self):
        try:
            config.APP_DIR.mkdir(parents=True, exist_ok=True)
            (config.APP_DIR / "state.json").write_text(
                json.dumps(
                    {
                        "fullness": round(self.fullness, 2),
                        "joy": round(self.joy, 2),
                        "energy": round(self.energy, 2),
                        "fed": self.fed,
                        "born_at": self.born_at,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            return True
        except Exception:
            return False

    # -- change -----------------------------------------------------------
    def decay(self, dt):
        self.fullness = _clamp(self.fullness - config.FULLNESS_DECAY * dt)
        self.joy = _clamp(self.joy - config.JOY_DECAY * dt)
        self.energy = _clamp(self.energy - config.ENERGY_DECAY * dt)

    def feed(self):
        self.fullness = _clamp(self.fullness + 34)
        self.joy = _clamp(self.joy + 6)
        self.fed += 1

    def cheer(self, amount=7.0):
        self.joy = _clamp(self.joy + amount)
        self.energy = _clamp(self.energy - 1.5)

    def sing(self):
        self.joy = _clamp(self.joy + 9)
        self.energy = _clamp(self.energy - 4)

    def rest(self, dt):
        self.energy = _clamp(self.energy + 2.2 * dt)
        self.fullness = _clamp(self.fullness - config.FULLNESS_DECAY * 0.35 * dt)

    def mood(self):
        if self.fullness < 25:
            return "hungry"
        if self.energy < 18:
            return "tired"
        if self.joy > 88:
            return "delighted"
        return "ok"
