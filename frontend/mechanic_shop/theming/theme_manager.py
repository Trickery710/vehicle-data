"""Dark/light theming via hand-rolled QPalette + QSS.

Deliberately not using a third-party theming library (e.g. qt-material):
this is an offline production tool where every extra dependency is
supply-chain surface, and full control over the palette avoids fighting an
opinionated library later when custom widgets appear (oscilloscope
captures, dashboard tiles, in later phases).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from shared.mechanic_shop_shared.constants import APP_NAME, APP_ORG_NAME

_QSS_DIR = Path(__file__).resolve().parent.parent / "resources" / "qss"

THEME_DARK = "dark"
THEME_LIGHT = "light"


def _dark_palette() -> QPalette:
    palette = QPalette()
    window = QColor(37, 39, 43)
    base = QColor(30, 32, 35)
    text = QColor(220, 222, 225)
    highlight = QColor(66, 133, 244)
    disabled_text = QColor(120, 122, 125)

    palette.setColor(QPalette.ColorRole.Window, window)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, window)
    palette.setColor(QPalette.ColorRole.ToolTipBase, window)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, window)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 80, 80))
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)
    return palette


class ThemeManager(QObject):
    theme_changed = Signal(str)

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self._app = app
        self._settings = QSettings(APP_ORG_NAME, APP_NAME)
        self._current = str(self._settings.value("theme", THEME_LIGHT))
        self._default_palette = QApplication.style().standardPalette()

    @property
    def current_theme(self) -> str:
        return self._current

    def apply_saved_theme(self) -> None:
        self.apply_dark() if self._current == THEME_DARK else self.apply_light()

    def apply_dark(self) -> None:
        self._app.setPalette(_dark_palette())
        self._app.setStyleSheet(_load_qss("dark.qss"))
        self._set_current(THEME_DARK)

    def apply_light(self) -> None:
        self._app.setPalette(self._default_palette)
        self._app.setStyleSheet(_load_qss("light.qss"))
        self._set_current(THEME_LIGHT)

    def toggle(self) -> None:
        self.apply_light() if self._current == THEME_DARK else self.apply_dark()

    def _set_current(self, theme: str) -> None:
        self._current = theme
        self._settings.setValue("theme", theme)
        self.theme_changed.emit(theme)


def _load_qss(filename: str) -> str:
    path = _QSS_DIR / filename
    return path.read_text() if path.exists() else ""
