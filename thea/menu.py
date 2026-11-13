"""The right-click / tray menu, styled as a 1-bit popup."""

from PySide6.QtWidgets import QMenu

STYLE = """
QMenu {
    background-color: #ffffff;
    color: #000000;
    border: 2px solid #000000;
    padding: 4px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
    font-weight: bold;
}
QMenu::item {
    padding: 5px 26px 5px 14px;
}
QMenu::item:selected {
    background-color: #000000;
    color: #ffffff;
}
QMenu::item:disabled {
    color: #696969;
}
QMenu::separator {
    height: 2px;
    background: #000000;
    margin: 4px 8px;
}
"""


class PixelMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLE)


def build_menu(parent, thea, stats):
    menu = PixelMenu(parent)
    happy = stats.joy >= 50
    header = menu.addAction(
        f"{'happy' if happy else 'down'}   food {int(stats.fullness)}   joy {int(stats.joy)}   energy {int(stats.energy)}"
    )
    header.setEnabled(False)
    menu.addSeparator()

    menu.addAction("Feed Thea", parent.feed)
    menu.addAction("Sing a song", parent.sing)
    menu.addAction("Play", parent.play)
    menu.addAction("Numbers", parent.show_stats)
    menu.addAction(
        "Wake up" if thea.state == "sleep" else "Go to sleep",
        parent.toggle_sleep,
    )
    menu.addSeparator()
    menu.addAction("Quit", parent.quit)
    return menu
