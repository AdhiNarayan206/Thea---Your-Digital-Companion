"""Launch Thea.

    python run.py              desktop companion
    python run.py --preview    write contact sheets to out/ and exit
"""

import argparse
import sys
from pathlib import Path

_mutex = None


def _already_running():
    """A named mutex, so double-launching does not give you two Theas."""
    global _mutex
    import ctypes

    _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\TheaOverlay")
    return ctypes.windll.kernel32.GetLastError() == 183  # ERROR_ALREADY_EXISTS


def main():
    parser = argparse.ArgumentParser(description="Thea, a pixel companion")
    parser.add_argument("--preview", action="store_true", help="render contact sheets and exit")
    parser.add_argument("--scale", type=int, default=None, help="sprite pixel size (default 5)")
    args = parser.parse_args()

    if args.preview:
        from tools.preview import make

        make()
        return

    if _already_running():
        print("[thea] already running")
        return

    import ctypes

    try:
        # Sets the explicit Application User Model ID so Windows associates the taskbar icon with Thea rather than Python
        myappid = "thea.digitalpet.companion.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    from thea import config

    if args.scale:
        config.SCALE = max(2, args.scale)

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication, QIcon
    from PySide6.QtWidgets import QApplication

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)

    icon = Path(__file__).resolve().parent / "assets" / "thea.ico"
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))
    app.setQuitOnLastWindowClosed(False)

    from thea.window import Overlay

    overlay = Overlay()  # noqa: F841  (kept alive)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
