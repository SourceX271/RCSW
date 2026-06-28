from __future__ import annotations

import os
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path

# 修复 qframelesswindow 在 Python 3.14 上的递归 bug
_win_ver = sys.getwindowsversion() if sys.platform == "win32" else None
_is_win10 = _win_ver and _win_ver.major >= 10
_is_win11 = _win_ver and _win_ver.major >= 10 and _win_ver.build >= 22000

with open(os.devnull, 'w', encoding='utf-8') as devnull:
    with redirect_stdout(devnull):
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication

        if sys.platform == "win32":
            import qframelesswindow.utils.win32_utils as _wu
            _wu.isGreaterEqualWin10 = lambda: _is_win10
            _wu.isGreaterEqualWin11 = lambda: _is_win11

        from qfluentwidgets import setTheme, Theme

from .core.logger import get_logger, set_console_enabled
from .core.utils import resource_path

_log = get_logger("app")


def _exception_hook(exc_type, exc_value, exc_tb):
    _log.critical("未捕获的异常", exc_info=(exc_type, exc_value, exc_tb))
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _exception_hook


def _icon_path() -> Path:
    if sys.platform == "darwin":
        candidates = ("icon.icns", "icon.png")
    else:
        candidates = ("icon.ico", "icon.png", "icon.svg")
    for name in candidates:
        p = resource_path(name)
        if p.exists():
            return p
    return resource_path("icon.png")


def create_application() -> QApplication:
    from .core.config import Config
    cfg = Config.instance()

    app = QApplication(sys.argv)
    if sys.platform == "win32":
        app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    icon_path = _icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    theme_val = cfg.get("theme", Theme.LIGHT.value)
    try:
        theme = Theme(theme_val)
    except (ValueError, TypeError):
        theme = Theme.LIGHT
    setTheme(theme)

    return app


def main():
    from .core.config import Config
    cfg = Config.instance()
    console_enabled = cfg.get("consoleLogEnabled", False)
    if not isinstance(console_enabled, bool):
        console_enabled = False
    set_console_enabled(console_enabled)

    _log.info("RCSW 启动")
    _log.info("Python %s | PySide6 %s", sys.version.split()[0], Qt.__module__)

    app = create_application()

    from .ui.main_window import MainWindow

    _log.info("配置文件: %s", cfg.path)
    _log.info("主题: %s", cfg.get("theme", Theme.LIGHT.value))
    app.processEvents()

    window = MainWindow()
    from PySide6.QtCore import QTimer
    QTimer.singleShot(0, window.show)

    exit_code = app.exec()
    _log.info("RCSW 退出 (code=%d)", exit_code)
    sys.exit(exit_code)
