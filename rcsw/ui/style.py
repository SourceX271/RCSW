from __future__ import annotations

from PySide6.QtGui import QColor
from qfluentwidgets import CardWidget, isDarkTheme

ACCENT = "#0078D4"
ACCENT_TRANSLUCENT = QColor(0, 120, 212, 100)

BODY_TEXT_STYLE = "font-size: 13px; line-height: 1.6;"
TIER_LABEL_STYLE = "font-size: 11px;"


def hint_color() -> str:
    return "#888888" if not isDarkTheme() else "#AAAAAA"


def dot_inactive_color() -> str:
    return "#CCC" if not isDarkTheme() else "#555555"


def body_text_color() -> str:
    return "#1A1A1A" if not isDarkTheme() else "#E0E0E0"


def meta_text_color() -> str:
    return "#888888" if not isDarkTheme() else "#999999"


def empty_label_style() -> str:
    base = (
        "font-size: 15px;"
        "padding: 32px;"
        "border-radius: 8px;"
    )
    if not isDarkTheme():
        return (
            "color: #888888;"
            + base
            + f"border: 2px dashed {ACCENT}44;"
            + "background: rgba(0,0,0,0.02);"
        )
    else:
        return (
            "color: #AAAAAA;"
            + base
            + f"border: 2px dashed {ACCENT}44;"
            + "background: rgba(255,255,255,0.03);"
        )

PANEL_BG = """
QWidget#filePanel,
QWidget#settingsPanel,
QWidget#softwareSettingsPanel,
QWidget#helpPanel,
QWidget#aboutPanel,
QWidget#filePanel QScrollArea,
QWidget#settingsPanel QScrollArea,
QWidget#softwareSettingsPanel QScrollArea,
QWidget#helpPanel QScrollArea,
QWidget#aboutPanel QScrollArea,
QWidget#filePanel QScrollArea > QWidget,
QWidget#settingsPanel QScrollArea > QWidget,
QWidget#softwareSettingsPanel QScrollArea > QWidget,
QWidget#helpPanel QScrollArea > QWidget,
QWidget#aboutPanel QScrollArea > QWidget,
QWidget#filePanel QListWidget,
QWidget#filePanel QListWidget > QWidget {
    background-color: transparent;
}
"""


class TransparentCard(CardWidget):

    def _normalBackgroundColor(self):
        return QColor(255, 255, 255, 60) if not isDarkTheme() \
          else QColor(0, 0, 0, 40)

    def _hoverBackgroundColor(self):
        return QColor(255, 255, 255, 90) if not isDarkTheme() \
          else QColor(0, 0, 0, 65)

    def _pressedBackgroundColor(self):
        return QColor(255, 255, 255, 40) if not isDarkTheme() \
          else QColor(0, 0, 0, 25)

