from __future__ import annotations

import sys

from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication


class NotificationManager(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray: QSystemTrayIcon | None = None
        self._use_system_notify = False
        self._window_focused = True
        self._enabled = True

    def setup(self, window_icon: QIcon | None = None):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray = QSystemTrayIcon(self)
        if window_icon:
            self._tray.setIcon(window_icon)
        self._tray.setToolTip("RCSW - Remove CamScanner Watermark")

        menu = QMenu()
        show_action = menu.addAction("显示窗口")
        show_action.triggered.connect(self._show_window)
        menu.addSeparator()
        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(self._quit_app)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _show_window(self):
        w = self.parent()
        if w:
            w.show()
            w.raise_()
            w.activateWindow()

    def _quit_app(self):
        QApplication.instance().quit()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def set_use_system(self, enabled: bool):
        self._use_system_notify = enabled

    def set_window_focused(self, focused: bool):
        self._window_focused = focused

    def notify(self, title: str, message: str):
        if not self._enabled:
            return
        if self._use_system_notify and not self._window_focused:
            if self._tray and self._tray.supportsMessages():
                self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)
        # When window is focused or system notify disabled,
        # the caller (MainWindow) handles it via InfoBar.

    def close(self):
        if self._tray:
            self._tray.hide()

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
