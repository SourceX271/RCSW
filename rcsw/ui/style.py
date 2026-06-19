from __future__ import annotations

ACCENT = "#0078D4"

BODY_TEXT_STYLE = "font-size: 13px; line-height: 1.6;"
HINT_COLOR = "#888888"
DOT_INACTIVE_COLOR = "#CCC"
TIER_LABEL_STYLE = "font-size: 11px;"

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
QWidget#aboutPanel QScrollArea > QWidget {
    background-color: transparent;
}
"""

