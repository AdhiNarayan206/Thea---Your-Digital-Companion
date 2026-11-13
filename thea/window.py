"""The desktop window: transparent, always on top, click-through elsewhere.

Overlay strategy: a small window that follows Thea rather than one fullscreen
sheet. Outside the window nothing exists, so other apps are never covered; and
inside it the window is made hit-transparent (WS_EX_TRANSPARENT) unless the
cursor is actually on his body. That gives per-pixel click-through with none of
the fullscreen-overlay fragility.
"""

import ctypes
import os
import time
import traceback
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QWidget

from . import config, rig
from .animation import Thea
from .audio import Chiptune
from .expressions import draw_face
from .input import Pointer
from .menu import build_menu
from .particles import Particles
from .stats import Stats
from tools.keyhook import SpaceHook

WS_EX_TRANSPARENT = 0x00000020
GWL_EXSTYLE = -20

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
_user32.GetWindowLongW.restype = ctypes.c_long
_user32.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
_user32.SetWindowLongW.restype = ctypes.c_long


class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.APP_NAME)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)

        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        self.work = (geo.x(), geo.y(), geo.width(), geo.height())

        dpr = screen.devicePixelRatio() or 1.0
        self.dpr = dpr
        # config.SCALE is device pixels per sprite pixel; Qt paints in logical
        # units, so divide by the ratio to keep Thea the same physical size on
        # every screen and every pixel exactly square.
        scale = config.SCALE / dpr
        self.scale = scale

        self.stats = Stats()
        self.particles = Particles()
        self.audio = Chiptune()
        self.thea = Thea(self.work, self.stats, self.particles, self.audio, scale=scale)
        self.pointer = Pointer()

        self.margin = config.FOLLOW_MARGIN
        self.setFixedSize(int(self.thea.size) + self.margin * 2, int(self.thea.size) + self.margin * 2)

        self._dashboard = None
        self._last_pos = None
        self._clickthrough = None
        self._over = False
        self._save_acc = 0.0
        self._frame = self.thea.render()
        self._qimg = self._to_qimage(self._frame)

        self._follow()
        self.show()

        self.tray = QSystemTrayIcon(self._make_icon(), self)
        self.tray.setToolTip(config.APP_NAME)
        self.tray.setContextMenu(self._tray_menu())
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

        self.hook = SpaceHook(self.hit_physical)
        self.hook_ok = self.hook.install()
        if not self.hook_ok:
            print(f"[thea] global space hook unavailable ({self.hook.error}); "
                  "Space works when the overlay is focused")

        self.clock = QElapsedTimer()
        self.clock.start()
        self.tick = QTimer(self)
        self.tick.setTimerType(Qt.PreciseTimer)
        self.tick.setInterval(config.TICK_MS)
        self.tick.timeout.connect(self._on_tick)
        self.tick.start()

        self.poll = QTimer(self)
        self.poll.setInterval(config.POLL_MS)
        self.poll.timeout.connect(self._on_poll)
        self.poll.start()

        self._set_clickthrough(True)
        self.audio.blip(880, 0.08, 0.18)
        print(
            f"[thea] ready work={self.work} dpr={dpr:.2f} scale={scale:.3f} "
            f"size={self.thea.size:.1f} window={self.geometry().getRect()}"
        )

        if os.environ.get("THEA_SELFTEST"):
            self._saved_cursor = QCursor.pos()
            QTimer.singleShot(1200, self._selftest_hover)

    # -- selftest ---------------------------------------------------------
    _user32 = ctypes.windll.user32

    def _selftest_hover(self):
        cx = int((self.thea.x + self.thea.size / 2) * self.dpr)
        cy = int((self.thea.y + self.thea.size / 2) * self.dpr)
        ok = self._user32.SetCursorPos(cx, cy)
        print(f"[selftest] SetCursorPos({cx},{cy}) -> {ok}")
        QTimer.singleShot(320, self._selftest_press)

    def _selftest_press(self):
        g = QCursor.pos()
        from tools.keyhook import cursor_pos

        print(
            f"[selftest] cursor=({g.x()},{g.y()}) raw={cursor_pos()} "
            f"pet=({self.thea.x:.0f},{self.thea.y:.0f}) size={self.thea.size:.1f} "
            f"over={self.thea.hit(g.x(), g.y())} "
            f"hook_hit={self.hit_physical(g.x() * self.dpr, g.y() * self.dpr)} "
            f"clickthrough={self._clickthrough} "
            f"exstyle=0x{self._exstyle() & 0xFFFFFFFF:08x}"
        )
        VK_SPACE, KEYUP = 0x20, 0x0002
        self._user32.keybd_event(VK_SPACE, 0, 0, 0)
        self._user32.keybd_event(VK_SPACE, 0, KEYUP, 0)
        QTimer.singleShot(300, self._selftest_report)

    def _selftest_report(self):
        print(
            f"[selftest] after space: state={self.thea.state} "
            f"expression={self.thea.expression()} hook={self.hook_ok}"
        )
        arr = self._frame
        print(
            f"[selftest] frame opaque_px={(arr[..., 3] > 0).sum()} "
            f"pos=({self.thea.x:.0f},{self.thea.y:.0f}) size={self.thea.size:.1f} "
            f"dpr={self.scale and (config.SCALE / self.scale):.2f}"
        )
        print(f"[selftest] tray={self.tray.isVisible()} geometry={self.geometry().getRect()}")
        self._user32.SetCursorPos(
            int(self._saved_cursor.x() * self.dpr), int(self._saved_cursor.y() * self.dpr)
        )
        QTimer.singleShot(250, self._selftest_away)

    def _selftest_away(self):
        style = self._exstyle()
        g = QCursor.pos()
        print(
            f"[selftest] cursor away: clickthrough={self._clickthrough} "
            f"transparent_bit={bool(style & WS_EX_TRANSPARENT)} "
            f"still_over={self.thea.hit(g.x(), g.y())}"
        )
        self.quit()

    # -- helpers ----------------------------------------------------------
    def _to_qimage(self, arr):
        h, w = arr.shape[:2]
        return QImage(arr.data, w, h, arr.strides[0], QImage.Format_RGBA8888).copy()

    def hit_physical(self, px, py):
        """Hook coordinates are physical pixels; Thea works in logical units."""
        return self.thea.hit(px / self.dpr, py / self.dpr)

    def _follow(self):
        wx = int(round(self.thea.x - self.margin))
        wy = int(round(self.thea.y - self.margin))
        if (wx, wy) != self._last_pos:
            self._last_pos = (wx, wy)
            self.move(wx, wy)

    def _set_clickthrough(self, on):
        if self._clickthrough == on:
            return
        self._clickthrough = on
        try:
            hwnd = int(self.winId())
            style = _user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if on:
                style |= WS_EX_TRANSPARENT
            else:
                style &= ~WS_EX_TRANSPARENT
            _user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            traceback.print_exc()

    def _exstyle(self):
        return _user32.GetWindowLongW(int(self.winId()), GWL_EXSTYLE)

    def _make_icon(self):
        """Prefer the multi-size .ico so the tray matches the app icon."""
        ico = Path(__file__).resolve().parents[1] / "assets" / "thea.ico"
        if ico.exists():
            return QIcon(str(ico))
        arr = rig.render_body()
        draw_face(arr, "happy", look=(0, 0))
        img = self._to_qimage(arr)
        pm = QPixmap.fromImage(img).scaled(32, 32, Qt.KeepAspectRatio, Qt.FastTransformation)
        return QIcon(pm)

    def _tray_menu(self):
        from .menu import PixelMenu

        menu = PixelMenu(self)
        menu.addAction("Feed Thea", self.feed)
        menu.addAction("Sing a song", self.sing)
        menu.addAction("Play", self.play)
        menu.addAction("Sleep / wake", self.toggle_sleep)
        menu.addSeparator()
        menu.addAction("Quit", self.quit)
        return menu

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_menu(QCursor.pos())

    # -- frame loop -------------------------------------------------------
    def _on_tick(self):
        try:
            dt = self.clock.restart() / 1000.0
            if dt <= 0:
                dt = 0.016
            cursor = QCursor.pos()
            self.thea.update(dt, (cursor.x(), cursor.y()))
            self._frame = self.thea.render()
            self._qimg = self._to_qimage(self._frame)
            self._follow()
            self.update()

            self._save_acc += dt
            if self._save_acc >= config.SAVE_EVERY:
                self._save_acc = 0.0
                self.stats.save()
        except Exception:
            traceback.print_exc()

    def _on_poll(self):
        try:
            g = QCursor.pos()
            over = self.thea.hit(g.x(), g.y())
            if self.pointer.down:
                over = True
            if over != self._over:
                self._over = over
                self._set_clickthrough(not over)
            if self.hook and self.hook.pressed:
                self.hook.pressed = False
                if self.thea.hit(g.x(), g.y()):
                    self.thea.interact((g.x(), g.y()))
        except Exception:
            traceback.print_exc()

    # -- painting ---------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        origin = self.pos()
        p.translate(-origin.x(), -origin.y())

        r = QRect(
            int(round(self.thea.x)),
            int(round(self.thea.y)),
            int(round(self.thea.size)),
            int(round(self.thea.size)),
        )
        p.drawImage(r, self._qimg)
        self.particles.draw(p, self.scale)

        if self.thea.state == "eat":
            self._draw_bowl(p)
        if self.pointer.dragging and QCursor.pos().y() < self.thea.shelf_y:
            self._draw_shelf(p)
        p.end()

    def _cell(self, p, x, y, w, h, color):
        s = self.scale
        p.fillRect(
            QRect(int(round(x)), int(round(y)), int(round(w * s)), int(round(h * s))),
            QColor(*color),
        )

    def _draw_bowl(self, p):
        bx, by = self.thea.bowl_pos()
        ink, paper, shade = (0, 0, 0), (255, 255, 255), (185, 185, 185)
        self._cell(p, bx, by, 6, 1, ink)
        self._cell(p, bx, by + 1, 1, 2, ink)
        self._cell(p, bx + 5, by + 1, 1, 2, ink)
        self._cell(p, bx + 1, by + 1, 4, 1, shade)
        self._cell(p, bx + 1, by + 2, 4, 1, paper)

    def _draw_shelf(self, p):
        y = self.thea.shelf_y
        x0 = self.pos().x()
        s = max(1, int(round(self.scale)))
        for x in range(x0, x0 + self.width(), s * 4):
            p.fillRect(QRect(x, y, s * 2, s), QColor(0, 0, 0))

    # -- input ------------------------------------------------------------
    def mousePressEvent(self, event):
        g = event.globalPosition().toPoint()
        if event.button() == Qt.RightButton:
            self.show_menu(g)
            event.accept()
            return
        if event.button() == Qt.LeftButton and self.thea.hit(g.x(), g.y()):
            self.pointer.press((g.x(), g.y()), time.monotonic())
            event.accept()

    def mouseMoveEvent(self, event):
        if not self.pointer.down:
            return
        g = event.globalPosition().toPoint()
        started = self.pointer.move((g.x(), g.y()), time.monotonic())
        if started:
            if self.thea.state != "drag":
                self.thea.begin_drag()
            self.thea.drag_to(g.x(), g.y())
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or not self.pointer.down:
            return
        g = event.globalPosition().toPoint()
        action = self.pointer.release((g.x(), g.y()), time.monotonic())
        event.accept()
        if not action:
            return
        if "drag" in action:
            if g.y() < self.thea.shelf_y:
                self.thea.start_eat(g.x(), g.y(), on_shelf=True)
                self.audio.blip(720, 0.08, 0.16)
            else:
                self.thea.release(*action["drag"], held=action["held"])
        elif action.get("double"):
            self.thea.double_tap()
        elif action.get("tap"):
            self.thea.tap()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Space:
            self.thea.interact((QCursor.pos().x(), QCursor.pos().y()))
        else:
            super().keyPressEvent(event)

    # -- commands ---------------------------------------------------------
    def show_menu(self, pos):
        menu = build_menu(self, self.thea, self.stats)
        menu.exec(pos)

    def feed(self):
        self.thea.start_eat(self.thea.x + self.thea.size * 0.1,
                            self.thea.floor(), on_shelf=False)

    def sing(self):
        self.thea.sing()

    def play(self):
        self.thea.double_tap()

    def toggle_sleep(self):
        self.thea.toggle_sleep()

    def show_dashboard(self):
        if self._dashboard is None:
            from .dashboard import DashboardWindow
            self._dashboard = DashboardWindow(self)
        self._dashboard.show()
        self._dashboard.raise_()
        self._dashboard.activateWindow()

    def show_stats(self):
        self.show_dashboard()

    def quit(self):
        try:
            if self.hook:
                self.hook.uninstall()
            self.stats.save()
            self.audio.stop()
            self.tray.hide()
        finally:
            QApplication.quit()

    def closeEvent(self, event):
        self.quit()
        super().closeEvent(event)
