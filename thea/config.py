"""Tunable constants for Thea.

Every visual number that can change the character's shape lives in thea/rig.py.
This file only holds world, timing and behaviour settings.
"""

import os
from pathlib import Path

APP_NAME = "Thea"
APP_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME

# --- Render ---------------------------------------------------------------
SCALE = 5                  # 1 sprite pixel -> SCALE device pixels (200px tall)
TICK_MS = 16               # ~60 fps
POLL_MS = 8                # cursor polling / click-through check

# --- World ----------------------------------------------------------------
GRAVITY = 1500.0           # px / s^2
RUN_SPEED = 270.0          # px / s
RUN_TIMEOUT = 2.6          # seconds before he gives up chasing the cursor
RUN_ARRIVE = 26            # px: close enough to call it a catch
JUMP_VELOCITY = -560.0
THROW_DAMPING = 0.75
MAX_THROW = 1400.0
DRAG_ANGRY_AFTER = 4.0     # seconds of being held
FEED_ZONE = 0.16           # top fraction of the work area is the feeding shelf
EAT_SECONDS = 2.6
SING_SECONDS = 4.2

# --- Overlay --------------------------------------------------------------
# The overlay is a small window that follows Thea, made hit-transparent
# (WS_EX_TRANSPARENT) whenever the cursor is not on his silhouette. Clicks
# outside the body therefore reach whatever app is underneath.
FOLLOW_MARGIN = 90         # logical px of transparent padding around the sprite
FULLNESS_DECAY = 0.055     # points per second
JOY_DECAY = 0.04
ENERGY_DECAY = 0.03
SAVE_EVERY = 10.0
