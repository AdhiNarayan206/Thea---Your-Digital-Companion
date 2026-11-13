"""1-bit Retro Pixel Dashboard for Thea."""

import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTabWidget,
    QSlider,
    QCheckBox,
    QGroupBox,
    QGridLayout,
    QFrame,
)

from . import config

DASHBOARD_STYLE = """
QWidget {
    background-color: #ffffff;
    color: #000000;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
}

QTabWidget::pane {
    border: 2px solid #000000;
    background: #ffffff;
    top: -2px;
}

QTabBar::tab {
    background: #ffffff;
    color: #000000;
    border: 2px solid #000000;
    padding: 6px 14px;
    margin-right: 2px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background: #000000;
    color: #ffffff;
}

QGroupBox {
    border: 2px solid #000000;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    background: #ffffff;
}

QPushButton {
    background-color: #ffffff;
    color: #000000;
    border: 2px solid #000000;
    padding: 6px 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #b9b9b9;
}

QPushButton:pressed {
    background-color: #000000;
    color: #ffffff;
}

QProgressBar {
    border: 2px solid #000000;
    text-align: center;
    background: #ffffff;
    color: #000000;
    font-weight: bold;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #000000;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #ffffff;
    border: 2px solid #000000;
}

QSlider::handle:horizontal {
    background: #000000;
    border: 1px solid #000000;
    width: 14px;
    margin: -5px 0;
}

QCheckBox {
    spacing: 8px;
    font-weight: bold;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 2px solid #000000;
    background: #ffffff;
}

QCheckBox::indicator:checked {
    background: #000000;
}
"""


class DashboardWindow(QWidget):
    """The retro 1-bit dashboard control center for Thea."""

    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.thea = overlay.thea
        self.stats = overlay.stats

        self.setWindowTitle("Thea // Control Center")
        self.resize(440, 380)
        self.setStyleSheet(DASHBOARD_STYLE)

        icon_path = Path(__file__).resolve().parent.parent / "assets" / "thea.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Header banner
        header = QLabel("[ THEA :: DIGITAL PET COMPANION ]")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px; background: #000000; color: #ffffff;")
        main_layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self._build_status_tab()
        self._build_actions_tab()
        self._build_milestones_tab()
        self._build_settings_tab()
        self._build_inspector_tab()

        # Update loop (200ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(200)

        self.refresh_data()

    def closeEvent(self, event):
        # Hide instead of quit so user can reopen from menu/tray
        self.hide()
        event.ignore()

    # -- Tabs -------------------------------------------------------------
    def _build_status_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        box = QGroupBox("LIVE NEEDS")
        box_layout = QVBoxLayout(box)

        # Mood summary
        self.lbl_mood = QLabel("Mood: Neutral")
        self.lbl_mood.setStyleSheet("font-size: 13px; font-weight: bold; margin-bottom: 4px;")
        box_layout.addWidget(self.lbl_mood)

        # Fullness
        box_layout.addWidget(QLabel("Fullness / Satiety:"))
        self.bar_fullness = QProgressBar()
        self.bar_fullness.setRange(0, 100)
        box_layout.addWidget(self.bar_fullness)

        # Joy
        box_layout.addWidget(QLabel("Joy / Happiness:"))
        self.bar_joy = QProgressBar()
        self.bar_joy.setRange(0, 100)
        box_layout.addWidget(self.bar_joy)

        # Energy
        box_layout.addWidget(QLabel("Energy / Stamina:"))
        self.bar_energy = QProgressBar()
        self.bar_energy.setRange(0, 100)
        box_layout.addWidget(self.bar_energy)

        layout.addWidget(box)

        quick_row = QHBoxLayout()
        btn_quick_feed = QPushButton("Feed")
        btn_quick_feed.clicked.connect(self.overlay.feed)
        btn_quick_play = QPushButton("Play")
        btn_quick_play.clicked.connect(self.overlay.play)
        quick_row.addWidget(btn_quick_feed)
        quick_row.addWidget(btn_quick_play)
        layout.addLayout(quick_row)

        self.tabs.addTab(tab, "Status")

    def _build_actions_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        box = QGroupBox("INTERACTIONS")
        grid = QGridLayout(box)
        grid.setSpacing(10)

        btn_feed = QPushButton("Feed (Snack)")
        btn_feed.clicked.connect(self.overlay.feed)
        grid.addWidget(btn_feed, 0, 0)

        btn_play = QPushButton("Play (Double-Tap)")
        btn_play.clicked.connect(self.overlay.play)
        grid.addWidget(btn_play, 0, 1)

        btn_sing = QPushButton("Sing a Song")
        btn_sing.clicked.connect(self.overlay.sing)
        grid.addWidget(btn_sing, 1, 0)

        self.btn_sleep = QPushButton("Toggle Sleep")
        self.btn_sleep.clicked.connect(self.overlay.toggle_sleep)
        grid.addWidget(self.btn_sleep, 1, 1)

        btn_hop = QPushButton("Hop")
        btn_hop.clicked.connect(lambda: self.thea.tap())
        grid.addWidget(btn_hop, 2, 0)

        btn_save = QPushButton("Save State Now")
        btn_save.clicked.connect(self._manual_save)
        grid.addWidget(btn_save, 2, 1)

        layout.addWidget(box)

        self.lbl_action_status = QLabel("Ready")
        self.lbl_action_status.setStyleSheet("color: #696969; font-style: italic;")
        layout.addWidget(self.lbl_action_status)

        layout.addStretch()
        self.tabs.addTab(tab, "Actions")

    def _manual_save(self):
        saved = self.stats.save()
        if saved:
            self.lbl_action_status.setText(f"Saved state at {datetime.now().strftime('%H:%M:%S')}")
        else:
            self.lbl_action_status.setText("Failed to save state")

    def _build_milestones_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        box = QGroupBox("LIFETIME METRICS")
        grid = QGridLayout(box)
        grid.setSpacing(8)

        grid.addWidget(QLabel("Born At:"), 0, 0)
        self.lbl_born = QLabel("--")
        grid.addWidget(self.lbl_born, 0, 1)

        grid.addWidget(QLabel("Age:"), 1, 0)
        self.lbl_age = QLabel("--")
        grid.addWidget(self.lbl_age, 1, 1)

        grid.addWidget(QLabel("Total Meals Eaten:"), 2, 0)
        self.lbl_fed_count = QLabel("0")
        grid.addWidget(self.lbl_fed_count, 2, 1)

        grid.addWidget(QLabel("State File:"), 3, 0)
        lbl_file = QLabel(str(config.APP_DIR / "state.json"))
        lbl_file.setWordWrap(True)
        lbl_file.setStyleSheet("color: #696969; font-size: 11px;")
        grid.addWidget(lbl_file, 3, 1)

        layout.addWidget(box)
        layout.addStretch()
        self.tabs.addTab(tab, "Milestones")

    def _build_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        box = QGroupBox("PREFERENCES")
        grid = QGridLayout(box)
        grid.setSpacing(10)

        # Scale slider
        grid.addWidget(QLabel("Sprite Scale:"), 0, 0)
        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setRange(2, 10)
        self.slider_scale.setValue(int(config.SCALE))
        self.slider_scale.valueChanged.connect(self._change_scale)
        grid.addWidget(self.slider_scale, 0, 1)

        self.lbl_scale_val = QLabel(f"{int(config.SCALE)}x ({int(40 * config.SCALE)}px)")
        grid.addWidget(self.lbl_scale_val, 0, 2)

        # Sound toggle
        self.chk_sound = QCheckBox("Enable Chiptune Voice")
        self.chk_sound.setChecked(bool(getattr(self.overlay.audio, "enabled", True)))
        self.chk_sound.toggled.connect(self._toggle_sound)
        grid.addWidget(self.chk_sound, 1, 0, 1, 3)

        layout.addWidget(box)
        layout.addStretch()
        self.tabs.addTab(tab, "Settings")

    def _change_scale(self, val):
        config.SCALE = val
        self.lbl_scale_val.setText(f"{val}x ({val * 40}px)")
        self.overlay.scale = val / self.overlay.dpr
        self.thea.size = 40 * self.overlay.scale
        self.thea.shelf_y = int(self.thea.screen_h * config.SHELF_TOP_FRAC)
        self.overlay.setFixedSize(
            int(self.thea.size) + self.overlay.margin * 2,
            int(self.thea.size) + self.overlay.margin * 2
        )
        self.overlay._update_mask()

    def _toggle_sound(self, checked):
        self.overlay.audio.enabled = checked
        if not checked:
            self.overlay.audio.stop()

    def _build_inspector_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        box = QGroupBox("PHYSICS & RIG TELEMETRY")
        grid = QGridLayout(box)
        grid.setSpacing(8)

        grid.addWidget(QLabel("Current State:"), 0, 0)
        self.lbl_thea_state = QLabel("--")
        self.lbl_thea_state.setStyleSheet("font-weight: bold;")
        grid.addWidget(self.lbl_thea_state, 0, 1)

        grid.addWidget(QLabel("Position (X, Y):"), 1, 0)
        self.lbl_pos = QLabel("--")
        grid.addWidget(self.lbl_pos, 1, 1)

        grid.addWidget(QLabel("Velocity (vx, vy):"), 2, 0)
        self.lbl_vel = QLabel("--")
        grid.addWidget(self.lbl_vel, 2, 1)

        grid.addWidget(QLabel("Active Expression:"), 3, 0)
        self.lbl_expression = QLabel("--")
        grid.addWidget(self.lbl_expression, 3, 1)

        grid.addWidget(QLabel("Facing Direction:"), 4, 0)
        self.lbl_facing = QLabel("--")
        grid.addWidget(self.lbl_facing, 4, 1)

        grid.addWidget(QLabel("Active Particles:"), 5, 0)
        self.lbl_particles = QLabel("0")
        grid.addWidget(self.lbl_particles, 5, 1)

        layout.addWidget(box)
        layout.addStretch()
        self.tabs.addTab(tab, "Inspector")

    # -- Refresh Loop -----------------------------------------------------
    def refresh_data(self):
        # 1. Needs
        f = int(self.stats.fullness)
        j = int(self.stats.joy)
        e = int(self.stats.energy)

        self.bar_fullness.setValue(f)
        self.bar_joy.setValue(j)
        self.bar_energy.setValue(e)

        mood = self.stats.mood()
        self.lbl_mood.setText(f"Mood: {mood.upper()} (Joy: {j}%)")

        # 2. Button texts
        if self.thea.state == "sleep":
            self.btn_sleep.setText("Wake Up")
        else:
            self.btn_sleep.setText("Put to Sleep")

        # 3. Milestones
        if self.stats.born_at:
            self.lbl_born.setText(str(self.stats.born_at)[:19])
            try:
                born_dt = datetime.fromisoformat(self.stats.born_at)
                diff = datetime.now() - born_dt
                days = diff.days
                hours = diff.seconds // 3600
                mins = (diff.seconds % 3600) // 60
                self.lbl_age.setText(f"{days}d {hours}h {mins}m")
            except Exception:
                self.lbl_age.setText("Active")
        else:
            self.lbl_born.setText("Just now")
            self.lbl_age.setText("0d 0h 0m")

        self.lbl_fed_count.setText(str(self.stats.fed))

        # 4. Inspector Telemetry
        self.lbl_thea_state.setText(str(self.thea.state))
        self.lbl_pos.setText(f"X: {int(self.thea.x)}, Y: {int(self.thea.y)}")
        self.lbl_vel.setText(f"vx: {self.thea.vx:.1f}, vy: {self.thea.vy:.1f}")
        self.lbl_expression.setText(str(self.thea.expression))
        self.lbl_facing.setText("Right (+1)" if self.thea.facing > 0 else "Left (-1)")
        self.lbl_particles.setText(str(len(self.overlay.particles.items)))

