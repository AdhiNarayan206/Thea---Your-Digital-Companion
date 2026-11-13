"""Generate assets/thea.ico from the sprite (run once, or after art tweaks).

    python tools/make_icon.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from thea import rig  # noqa: E402
from thea.expressions import draw_face  # noqa: E402


def main():
    img = rig.render_body({"sway": 0.3})
    draw_face(img, "happy")
    base = Image.fromarray(img)

    canvas = Image.new("RGBA", (44, 44), (0, 0, 0, 0))
    canvas.paste(base, (2, 2), base)
    big = canvas.resize((256, 256), Image.NEAREST)

    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    big.save(
        out / "thea.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    big.save(out / "thea.png")
    print(f"wrote {out / 'thea.ico'} and {out / 'thea.png'}")


if __name__ == "__main__":
    main()
