from __future__ import annotations

import os
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path

with open(os.devnull, 'w', encoding='utf-8') as devnull:
    with redirect_stdout(devnull):
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication
        from qfluentwidgets import setTheme, Theme

from .core.logger import get_logger, set_console_enabled

_log = get_logger("app")


def _exception_hook(exc_type, exc_value, exc_tb):
    _log.critical("未捕获的异常", exc_info=(exc_type, exc_value, exc_tb))
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _exception_hook


def _icon_path() -> Path:
    return Path(__file__).resolve().parent / "resources" / "icon.svg"


def main():
    from .core.config import Config
    cfg = Config.instance()
    console_enabled = cfg.get("consoleLogEnabled", False)
    if not isinstance(console_enabled, bool):
        console_enabled = False
    set_console_enabled(console_enabled)

    _log.info("RCSW 启动")
    _log.info("Python %s | PySide6 %s", sys.version.split()[0], Qt.__module__)

    app = QApplication(sys.argv)
    if sys.platform == "win32":
        app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    icon_path = _icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    from .ui.main_window import MainWindow

    _log.info("配置文件: %s", cfg.path)

    theme_val = cfg.get("theme", Theme.LIGHT.value)
    try:
        theme = Theme(theme_val)
    except (ValueError, TypeError):
        theme = Theme.LIGHT
    setTheme(theme)
    _log.info("主题: %s", theme_val)
    app.processEvents()

    window = MainWindow()
    from PySide6.QtCore import QTimer
    QTimer.singleShot(0, window.show)

    exit_code = app.exec()
    _log.info("RCSW 退出 (code=%d)", exit_code)
    sys.exit(exit_code)
