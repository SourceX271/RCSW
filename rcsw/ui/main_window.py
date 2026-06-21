from __future__ import annotations

import os
import sys

from PySide6.QtCore import QSize, QRect, QEvent
from PySide6.QtGui import QPalette, QColor, QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from qfluentwidgets import (
    FluentWindow,
    NavigationItemPosition,
    InfoBar,
    InfoBarPosition,
    FluentIcon as FIF,
    isDarkTheme,
    qconfig,
)

from .file_panel import FilePanel
from .settings_panel import SettingsPanel
from .software_settings_panel import SoftwareSettingsPanel
from .help_panel import HelpPanel
from .about_panel import AboutPanel
from ..core.worker import ProcessingWorker
from ..core.logger import get_logger
from ..core.config import Config
from ..core.utils import open_in_system

from pathlib import Path

_log = get_logger("main_window")


class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()
        self.hide()
        self.resize(1100, 720)
        self.setMinimumSize(860, 600)
        self.setWindowTitle("RCSW - Remove CamScanner Watermark")

        self._file_panel = FilePanel()
        self._settings_panel = SettingsPanel()
        self._software_settings_panel = SoftwareSettingsPanel()
        self._help_panel = HelpPanel()
        self._about_panel = AboutPanel()

        self._worker: ProcessingWorker | None = None

        self._window_focused = True

        self._init_navigation()
        self._connect_signals()
        self._setup_tray()

        if sys.platform == "darwin":
            self.titleBar.hBoxLayout.setContentsMargins(8, 0, 0, 0)
            self.navigationInterface.panel.vBoxLayout.setContentsMargins(0, 28, 0, 5)

        self._apply_transparent_chain()
        self._apply_separators()
        qconfig.themeChangedFinished.connect(self._apply_separators)

    if sys.platform == "darwin":
        def systemTitleBarRect(self, size: QSize) -> QRect:
            return QRect(0, 0 if self.isFullScreen() else 8, 70, size.height())

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            self._window_focused = self.isActiveWindow()
        super().changeEvent(event)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if sys.platform == "darwin":
            self.titleBar.move(70, 0)
            self.titleBar.resize(self.width() - 70, self.titleBar.height())

    def _init_navigation(self):
        self.addSubInterface(
            self._file_panel,
            FIF.DOCUMENT,
            "文件",
            position=NavigationItemPosition.TOP,
            isTransparent=True,
        )
        self.addSubInterface(
            self._settings_panel,
            FIF.PALETTE,
            "处理设置",
            position=NavigationItemPosition.TOP,
            isTransparent=True,
        )
        self.addSubInterface(
            self._help_panel,
            FIF.HELP,
            "帮助",
            position=NavigationItemPosition.BOTTOM,
            isTransparent=True,
        )
        self.addSubInterface(
            self._about_panel,
            FIF.INFO,
            "关于",
            position=NavigationItemPosition.BOTTOM,
            isTransparent=True,
        )
        self.addSubInterface(
            self._software_settings_panel,
            FIF.SETTING,
            "软件设置",
            position=NavigationItemPosition.BOTTOM,
            isTransparent=True,
        )

    def _apply_transparent_chain(self):
        from PySide6.QtWidgets import QScrollArea

        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))

        view = self.stackedWidget.view
        view.setAutoFillBackground(False)
        view.setPalette(pal)

        for panel in [self._file_panel, self._settings_panel,
                      self._software_settings_panel, self._help_panel,
                      self._about_panel]:
            panel.setAutoFillBackground(False)
            panel.setPalette(pal)

            for scroll in panel.findChildren(QScrollArea):
                scroll.setAutoFillBackground(False)
                scroll.setPalette(pal)
                vp = scroll.viewport()
                vp.setAutoFillBackground(False)
                vp.setPalette(pal)

    def _apply_separators(self):
        dark = isDarkTheme()
        sep = "rgba(255,255,255,0.08)" if dark else "rgba(0,0,0,0.08)"

        self.navigationInterface.setObjectName("navInterface")
        self.navigationInterface.setStyleSheet(
            f"#navInterface {{ border-right: 1px solid {sep}; }}"
        )
        self.titleBar.setObjectName("titleBar")
        self.titleBar.setStyleSheet(
            f"#titleBar {{ border-bottom: 1px solid {sep}; }}"
        )

    def _connect_signals(self):
        self._file_panel.process_requested.connect(self._on_start_process)
        self._file_panel.cancel_requested.connect(self._on_cancel)

    def _setup_tray(self):
        icon_path = Path(__file__).resolve().parent.parent / "resources" / "icon.png"
        if not icon_path.exists():
            return

        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(QIcon(str(icon_path)))
        self._tray.setToolTip("RCSW - Remove CamScanner Watermark")

        menu = QMenu()
        show_action = menu.addAction("显示")
        show_action.triggered.connect(self._show_from_tray)
        menu.addSeparator()
        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(self._quit_from_tray)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_from_tray(self):
        self._tray.hide()
        self._save_all_settings()
        QApplication.quit()

    def _on_start_process(self):
        file_paths = self._file_panel.get_file_paths()
        if not file_paths:
            InfoBar.warning(
                title="提示",
                content="请先添加 PDF 文件",
                parent=self,
                position=InfoBarPosition.TOP,
            )
            self._file_panel.set_processing(False)
            return

        output_dir = self._settings_panel.output_dir
        if not output_dir:
            output_dir = self._software_settings_panel.default_output_dir
        if not output_dir:
            output_dir = os.path.dirname(file_paths[0])
        if not os.path.isdir(output_dir):
            InfoBar.warning(
                title="提示",
                content="请选择有效的输出目录",
                parent=self,
                position=InfoBarPosition.TOP,
            )
            self._file_panel.set_processing(False)
            return

        self._worker = ProcessingWorker()
        self._worker.configure(
            file_paths=file_paths,
            output_dir=output_dir,
            dpi=self._settings_panel.dpi,
            jpeg_quality=self._settings_panel.jpeg_quality,
            max_wm_size=self._settings_panel.max_wm_size,
            wm_mode=self._settings_panel.wm_mode,
            scale_mode=self._settings_panel.scale_mode,
            output_suffix=self._settings_panel.output_suffix,
            overwrite=self._software_settings_panel.overwrite_existing,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.file_started.connect(self._on_file_started)
        self._worker.file_progress.connect(self._on_file_progress)
        self._worker.file_finished.connect(self._on_file_done)
        self._worker.start()

    def _on_progress(self, current: int, total: int, filename: str):
        self._file_panel.update_progress(current, total, filename)

    def _on_file_started(self, index: int, filename: str, total_pages: int):
        pass

    def _on_file_progress(self, index: int, current_page: int, total_pages: int):
        self._file_panel.set_file_progress(index, current_page, total_pages)

    def _on_file_done(self, index: int, output_path: str):
        self._file_panel.set_file_done(index)

    def _on_finished(self, success: list, errors: list, output_dir: str = ""):
        self._worker = None
        self._file_panel.set_processing(False)
        use_system_notify = Config.instance().get("useSystemNotification", False)
        use_tray = use_system_notify and not self._window_focused and hasattr(self, '_tray')

        if success:
            parts = []
            for s in success[:5]:
                parts.append(f"{os.path.basename(s[0])} -> {os.path.basename(s[1])}")
            info = "\n".join(parts)
            if len(success) > 5:
                info += f"\n... 等 {len(success) - 5} 个文件"
            if use_tray:
                self._tray.showMessage(
                    f"成功处理 {len(success)} 个文件",
                    info.replace("\n", ", ")[:200],
                    QSystemTrayIcon.MessageIcon.Information,
                    5000,
                )
            InfoBar.success(
                title=f"成功处理 {len(success)} 个文件",
                content=info,
                parent=self,
                position=InfoBarPosition.TOP,
                duration=8000,
            )
        if errors:
            parts = []
            for e in errors[:3]:
                parts.append(f"{os.path.basename(e[0])}: {e[1][:60]}")
            info = "\n".join(parts)
            if use_tray:
                self._tray.showMessage(
                    f"{len(errors)} 个文件处理失败",
                    info.replace("\n", ", ")[:200],
                    QSystemTrayIcon.MessageIcon.Warning,
                    5000,
                )
            InfoBar.error(
                title=f"{len(errors)} 个文件处理失败",
                content=info,
                parent=self,
                position=InfoBarPosition.TOP,
                duration=8000,
            )

        if output_dir and self._software_settings_panel.open_folder_after:
            self._open_folder(output_dir)

    def _open_folder(self, path: str):
        try:
            open_in_system(path)
        except Exception:
            _log.warning("Failed to open folder: %s", path)

    def _on_cancel(self):
        if self._worker and not self._worker.isFinished():
            self._worker.requestInterruption()
            self._file_panel.update_status("正在取消...")

    def _shutdown_worker(self):
        if self._worker and self._worker.isRunning():
            _log.info("Waiting for worker thread to finish...")
            self._file_panel.update_status("正在停止处理任务...")
            try:
                self._worker.finished.disconnect(self._on_finished)
            except (TypeError, RuntimeError):
                pass
            self._worker.finished.connect(self._on_worker_shutdown)
            self._worker.requestInterruption()
            return False
        return True

    def _on_worker_shutdown(self, _success, _errors, _output_dir):
        self._worker = None
        self._finalize_close()

    def _finalize_close(self):
        self._save_all_settings()
        if hasattr(self, '_tray'):
            self._tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        minimize_to_tray = (
            hasattr(self, '_tray') and self._tray.isVisible()
            and Config.instance().get("minimizeToTray", False)
        )
        if minimize_to_tray:
            if self._worker and self._worker.isRunning():
                try:
                    self._worker.finished.disconnect(self._on_finished)
                except (TypeError, RuntimeError):
                    pass
                self._worker.finished.connect(
                    lambda *_: self.hide()
                )
                self._worker.requestInterruption()
            else:
                self.hide()
            self._save_all_settings()
            event.ignore()
            return

        if not self._shutdown_worker():
            event.ignore()
            return

        self._finalize_close()
        super().closeEvent(event)

    def _save_all_settings(self):
        self._settings_panel.save_to_config()
        self._software_settings_panel.save_to_config()
        Config.instance().save()
