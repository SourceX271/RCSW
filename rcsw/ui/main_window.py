from __future__ import annotations

import os
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

from qfluentwidgets import (
    FluentWindow,
    NavigationItemPosition,
    InfoBar,
    InfoBarPosition,
    FluentIcon as FIF,
)

from .file_panel import FilePanel
from .settings_panel import SettingsPanel
from .software_settings_panel import SoftwareSettingsPanel
from .help_panel import HelpPanel
from .about_panel import AboutPanel
from ..core.worker import ProcessingWorker
from ..core.logger import get_logger
from ..core.config import Config

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

        self._init_navigation()
        self._connect_signals()

        self._apply_transparent_chain()

    def _init_navigation(self):
        self.addSubInterface(
            self._file_panel,
            FIF.DOCUMENT,
            "文件",
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self._settings_panel,
            FIF.PALETTE,
            "处理设置",
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self._software_settings_panel,
            FIF.DEVELOPER_TOOLS,
            "软件设置",
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self._help_panel,
            FIF.HELP,
            "帮助",
            position=NavigationItemPosition.BOTTOM,
        )
        self.addSubInterface(
            self._about_panel,
            FIF.INFO,
            "关于",
            position=NavigationItemPosition.BOTTOM,
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

    def _connect_signals(self):
        self._file_panel.process_requested.connect(self._on_start_process)
        self._file_panel.cancel_requested.connect(self._on_cancel)

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
        self._worker.start()

    def _on_progress(self, current: int, total: int, filename: str):
        self._file_panel.update_progress(current, total, filename)

    def _on_finished(self, success: list, errors: list, output_dir: str = ""):
        self._worker = None
        self._file_panel.set_processing(False)

        if success:
            parts = []
            for s in success[:5]:
                parts.append(f"{os.path.basename(s[0])} -> {os.path.basename(s[1])}")
            info = "\n".join(parts)
            if len(success) > 5:
                info += f"\n... 等 {len(success) - 5} 个文件"
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
            InfoBar.error(
                title=f"{len(errors)} 个文件处理失败",
                content=info,
                parent=self,
                position=InfoBarPosition.TOP,
                duration=8000,
            )

        if output_dir and self._software_settings_panel.open_folder_after:
            try:
                subprocess.run(["explorer", os.path.normpath(output_dir)], check=False)
            except Exception:
                pass

    def _on_cancel(self):
        if self._worker and not self._worker.isFinished():
            self._worker.requestInterruption()
            self._file_panel.update_status("正在取消...")

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            _log.info("Waiting for worker thread to finish...")
            self._file_panel.update_status("正在停止处理任务...")
            self._worker.requestInterruption()
            if not self._worker.wait(15000):
                _log.warning("Worker thread did not finish in time, terminating")
                self._worker.terminate()
        self._save_all_settings()
        super().closeEvent(event)

    def _save_all_settings(self):
        self._settings_panel.save_to_config()
        self._software_settings_panel.save_to_config()
        Config.instance().save()
