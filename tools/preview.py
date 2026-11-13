"""Offscreen contact sheets: python run.py --preview

Renders every expression and pose at 8x into out/ so the look can be reviewed
without the desktop overlay running.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw  # noqa: E402

from thea import rig  # noqa: E402
from thea.expressions import draw_face  # noqa: E402

SCALE = 8
CELL = rig.W * SCALE
PAD = 14
LABEL_H = 20

EXPRESSIONS = ["neutral", "sad", "happy", "surprised", "angry", "eating", "sing", "sleep"]

POSES = [
    ("idle", {"sway": 0.4}, "neutral"),
    ("run lean", {"squash": 0.02, "tilt": 0.03, "arm": 0.8, "sway": 0.7}, "neutral"),
    ("jump", {"squash": 0.09, "arm": -0.9}, "surprised"),
    ("squash", {"squash": -0.12, "arm": 0.3}, "happy"),
    ("drag", {"squash": -0.06, "arm": 0.5, "sway": 0.5}, "surprised"),
    ("sleep", {"squash": 0.02, "sway": 0.2}, "sleep"),
]


def _cell(arr):
    img = Image.fromarray(arr)
    return img.resize((CELL, CELL), Image.NEAREST)


def _sheet(rows, cols, title):
    w = cols * CELL + (cols + 1) * PAD
    h = len(rows) * (CELL + LABEL_H) + (len(rows) + 1) * PAD + (LABEL_H if title else 0)
    sheet = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    y = PAD
    if title:
        draw.text((PAD, y), title, fill=(0, 0, 0))
        y += LABEL_H
    for ri, row in enumerate(rows):
        x = PAD
        for ci, (label, arr) in enumerate(row):
            if ci >= cols:
                break
            sheet.paste(_cell(arr), (x, y), _cell(arr))
            draw.text((x, y + CELL + 2), label, fill=(0, 0, 0))
            x += CELL + PAD
        y += CELL + LABEL_H + PAD
    return sheet


def _expression_row():
    row = []
    for name in EXPRESSIONS:
        img = rig.render_body({"sway": 0.35})
        draw_face(img, name, t=0.0, look=(0, 0), chew=0.7)
        row.append((name, img))
    return row[:4], row[4:]


def _pose_row():
    row = []
    for label, pose, expr in POSES:
        img = rig.render_body(pose)
        draw_face(img, expr, t=0.0, look=(0, 0), chew=0.5)
        row.append((label, img))
    return row[:3], row[3:]


def make(out_dir=None):
    out = Path(out_dir or "out")
    out.mkdir(parents=True, exist_ok=True)

    r1, r2 = _expression_row()
    sheet = _sheet([r1, r2], 4, "Thea - expressions (only the face changes)")
    sheet.save(out / "expressions.png")

    p1, p2 = _pose_row()
    sheet = _sheet([p1, p2], 3, "Thea - poses (body rig, 40x40 grid)")
    sheet.save(out / "poses.png")

    one = Image.new("RGB", (4 * (40 + 8), 48), (255, 255, 255))
    for i, name in enumerate(["neutral", "sad", "happy", "surprised"]):
        img = rig.render_body()
        draw_face(img, name, look=(0, 0), chew=0.6)
        one.paste(Image.fromarray(img), (i * 48 + 4, 4), Image.fromarray(img))
    one.resize((one.width * 4, one.height * 4), Image.NEAREST).save(out / "thea_1x.png")

    print(f"wrote {out / 'expressions.png'}")
    print(f"wrote {out / 'poses.png'}")
    print(f"wrote {out / 'thea_1x.png'}")


if __name__ == "__main__":
    make()
