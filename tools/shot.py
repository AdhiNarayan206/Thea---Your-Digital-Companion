"""Dev helper: grab the primary screen to out/<name>.png (for visual QA)."""

import sys
from pathlib import Path

from PIL import ImageGrab


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "shot.png"
    path = Path("out") / name
    path.parent.mkdir(parents=True, exist_ok=True)
    img = ImageGrab.grab()
    img.save(path)
    print(f"{img.size[0]}x{img.size[1]} -> {path}")


if __name__ == "__main__":
    main()
