from __future__ import annotations

import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

with redirect_stdout(open(os.devnull, 'w', encoding='utf-8')):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication
    from qfluentwidgets import setTheme, Theme


def _icon_path() -> Path:
    return Path(__file__).resolve().parent / "resources" / "icon.svg"


def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    icon_path = _icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    from .ui.main_window import MainWindow
    from .core.config import Config

    cfg = Config.instance()
    theme_val = cfg.get("theme", Theme.LIGHT.value)
    try:
        theme = Theme(theme_val)
    except (ValueError, TypeError):
        theme = Theme.LIGHT
    setTheme(theme)
    app.processEvents()

    window = MainWindow()
    from PySide6.QtCore import QTimer
    QTimer.singleShot(0, window.show)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
