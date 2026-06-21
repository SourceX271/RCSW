from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
)
from qfluentwidgets import (
    StrongBodyLabel,
    BodyLabel,
    CheckBox,
    ComboBox,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PushButton,
    ScrollArea,
    setTheme,
    Theme,
)

from ..core.config import Config
from .style import PANEL_BG, TransparentCard
from ..core.logger import get_log_path, set_console_enabled, is_console_enabled
import shutil
import sys as _sys


class SoftwareSettingsPanel(QWidget):

    _theme_combo: ComboBox
    _output_dir: LineEdit
    _suffix_edit: LineEdit
    _overwrite_cb: CheckBox
    _open_folder_cb: CheckBox
    _minimize_tray_cb: CheckBox

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("softwareSettingsPanel")
        self._cfg = Config.instance()
        self._setup_ui()
        self._connect_signals()
        self.load()

    def _setup_ui(self):
        self.setStyleSheet(PANEL_BG)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        title = StrongBodyLabel("软件设置")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        root = QWidget()
        root.setAutoFillBackground(False)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 8, 0, 0)
        root_layout.setSpacing(16)

        c1 = TransparentCard()
        c1_layout = QVBoxLayout(c1)
        c1_layout.setContentsMargins(16, 12, 16, 16)
        c1_layout.setSpacing(14)
        c1_layout.addWidget(StrongBodyLabel("通用"))

        theme_row = QHBoxLayout()
        theme_row.setSpacing(12)
        theme_label = BodyLabel("主题")
        theme_label.setFixedWidth(150)
        theme_row.addWidget(theme_label)
        self._theme_combo = ComboBox()
        self._theme_combo.addItem("浅色", userData=Theme.LIGHT)
        self._theme_combo.addItem("深色", userData=Theme.DARK)
        self._theme_combo.addItem("跟随系统", userData=Theme.AUTO)
        theme_row.addWidget(self._theme_combo, 1)
        c1_layout.addLayout(theme_row)

        self._minimize_tray_cb = CheckBox("关闭窗口时最小化到系统托盘")
        c1_layout.addWidget(self._minimize_tray_cb)

        self._system_notify_cb = CheckBox("窗口失焦时使用系统通知")
        c1_layout.addWidget(self._system_notify_cb)

        self._taskbar_cb = CheckBox("任务栏显示处理进度")
        if _sys.platform != "win32":
            self._taskbar_cb.setEnabled(False)
            self._taskbar_cb.setToolTip(
                "macOS 不支持任务栏进度显示" if _sys.platform == "darwin"
                else "Linux 不支持任务栏进度显示"
            )
        c1_layout.addWidget(self._taskbar_cb)

        root_layout.addWidget(c1)

        c3 = TransparentCard()
        c3_layout = QVBoxLayout(c3)
        c3_layout.setContentsMargins(16, 12, 16, 16)
        c3_layout.setSpacing(14)
        c3_layout.addWidget(StrongBodyLabel("输出"))

        c3_layout.addLayout(self._make_output_dir_row())

        c3_layout.addLayout(self._make_line_row("输出文件名后缀", "_RCSW"))

        self._overwrite_cb = CheckBox("覆盖已有同名文件")
        c3_layout.addWidget(self._overwrite_cb)

        self._open_folder_cb = CheckBox("处理完成后打开输出文件夹")
        c3_layout.addWidget(self._open_folder_cb)

        root_layout.addWidget(c3)

        ui_card = TransparentCard()
        ui_layout = QVBoxLayout(ui_card)
        ui_layout.setContentsMargins(16, 12, 16, 16)
        ui_layout.setSpacing(14)
        ui_layout.addWidget(StrongBodyLabel("界面与行为"))

        silent_row = QHBoxLayout()
        silent_row.setSpacing(12)
        silent_label = BodyLabel("双击PDF处理模式")
        silent_label.setFixedWidth(150)
        silent_row.addWidget(silent_label)
        self._silent_mode_combo = ComboBox()
        self._silent_mode_combo.addItem("迷你窗口", userData="mini")
        self._silent_mode_combo.addItem("无窗口", userData="headless")
        self._silent_mode_combo.setCurrentIndex(0)
        silent_row.addWidget(self._silent_mode_combo, 1)
        ui_layout.addLayout(silent_row)

        progress_style_row = QHBoxLayout()
        progress_style_row.setSpacing(12)
        ps_label = BodyLabel("文件进度显示")
        ps_label.setFixedWidth(150)
        progress_style_row.addWidget(ps_label)
        self._file_progress_combo = ComboBox()
        self._file_progress_combo.addItem("进度条", userData="bar")
        self._file_progress_combo.addItem("百分比", userData="percent")
        self._file_progress_combo.addItem("两者", userData="both")
        self._file_progress_combo.setCurrentIndex(0)
        progress_style_row.addWidget(self._file_progress_combo, 1)
        ui_layout.addLayout(progress_style_row)

        root_layout.addWidget(ui_card)

        c4 = TransparentCard()
        c4_layout = QVBoxLayout(c4)
        c4_layout.setContentsMargins(16, 12, 16, 16)
        c4_layout.setSpacing(14)
        c4_layout.addWidget(StrongBodyLabel("日志"))

        self._log_enable_cb = CheckBox("在终端中输出日志")
        self._log_enable_cb.setChecked(False)
        self._log_enable_cb.stateChanged.connect(self._on_log_toggle)
        c4_layout.addWidget(self._log_enable_cb)

        log_export_row = QHBoxLayout()
        log_export_row.setSpacing(8)
        log_path = str(get_log_path())
        log_label = BodyLabel(log_path if len(log_path) < 50 else "..." + log_path[-47:])
        log_label.setProperty("hint", True)
        log_label.setWordWrap(False)
        log_export_row.addWidget(log_label, 1)
        export_btn = PushButton("导出日志")
        export_btn.clicked.connect(self._on_export_log)
        log_export_row.addWidget(export_btn)
        c4_layout.addLayout(log_export_row)

        root_layout.addWidget(c4)

        c5 = TransparentCard()
        c5_layout = QVBoxLayout(c5)
        c5_layout.setContentsMargins(16, 12, 16, 16)
        c5_layout.setSpacing(14)
        c5_layout.addWidget(StrongBodyLabel("数据管理"))

        data_btn_row = QHBoxLayout()
        data_btn_row.setSpacing(8)

        clear_cache_btn = PushButton("清除缓存")
        clear_cache_btn.clicked.connect(self._on_clear_cache)
        data_btn_row.addWidget(clear_cache_btn)

        reset_btn = PushButton("重置设置")
        reset_btn.setStyleSheet(
            "PushButton { color: #E74C3C; }"
            "PushButton:hover { color: #C0392B; }"
        )
        reset_btn.clicked.connect(self._on_reset_settings)
        data_btn_row.addWidget(reset_btn)

        data_btn_row.addStretch()
        c5_layout.addLayout(data_btn_row)
        root_layout.addWidget(c5)

        root_layout.addStretch()

        scroll.setWidget(root)
        scroll.enableTransparentBackground()
        layout.addWidget(scroll, 1)

    def _make_output_dir_row(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = BodyLabel("默认输出目录")
        lbl.setFixedWidth(150)
        row.addWidget(lbl)

        self._output_dir = LineEdit()
        self._output_dir.setPlaceholderText("留空则使用源文件所在目录")
        row.addWidget(self._output_dir, 1)

        btn = PushButton("浏览")
        btn.clicked.connect(self._on_browse_output)
        row.addWidget(btn)

        src_btn = PushButton("源文件目录")
        src_btn.clicked.connect(lambda: self._output_dir.setText(""))
        row.addWidget(src_btn)
        return row

    def _make_line_row(self, label: str, default: str):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = BodyLabel(label)
        lbl.setFixedWidth(150)
        row.addWidget(lbl)

        self._suffix_edit = LineEdit()
        self._suffix_edit.setText(default)
        row.addWidget(self._suffix_edit, 1)
        return row

    def _on_theme_changed(self):
        theme = self._theme_combo.currentData()
        setTheme(theme)
        self._cfg.set("theme", theme.value if isinstance(theme, Theme) else Theme.LIGHT.value)

    def _on_browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择默认输出目录")
        if path:
            self._output_dir.setText(path)

    def _on_log_toggle(self, state):
        set_console_enabled(bool(state))
        self._cfg.set("consoleLogEnabled", bool(state))

    def _on_export_log(self):
        src = str(get_log_path())
        path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "rcsw.log", "日志文件 (*.log);;所有文件 (*)"
        )
        if path:
            try:
                shutil.copy2(src, path)
            except Exception:
                pass

    def _on_clear_cache(self):
        reply = QMessageBox.question(
            self, "清除缓存",
            "确定要清除缓存吗？\n这将删除日志文件和临时数据。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            log_file = get_log_path()
            if log_file.exists():
                log_file.unlink()
            for i in range(1, 4):
                roll = log_file.with_suffix(f".log.{i}")
                if roll.exists():
                    roll.unlink()
        except Exception:
            pass
        InfoBar.success(
            title="已清除", content="缓存数据已清除",
            parent=self.window(), position=InfoBarPosition.TOP, duration=3000,
        )

    def _on_reset_settings(self):
        reply = QMessageBox.warning(
            self, "重置设置",
            "确定要重置所有设置吗？\n所有自定义设置将恢复为默认值，此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._cfg.clear_all()
        self.load()
        InfoBar.success(
            title="已重置", content="所有设置已恢复为默认值",
            parent=self.window(), position=InfoBarPosition.TOP, duration=3000,
        )

    @property
    def default_output_dir(self) -> str:
        return self._output_dir.text()

    @property
    def output_suffix(self) -> str:
        return self._suffix_edit.text() or "_RCSW"

    @property
    def overwrite_existing(self) -> bool:
        return self._overwrite_cb.isChecked()

    @property
    def open_folder_after(self) -> bool:
        return self._open_folder_cb.isChecked()

    @property
    def minimize_to_tray(self) -> bool:
        return self._minimize_tray_cb.isChecked()

    def _connect_signals(self):
        c = self._cfg
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self._output_dir.textChanged.connect(lambda t: c.set("defaultOutputDir", t))
        self._suffix_edit.textChanged.connect(lambda t: c.set("defaultOutputSuffix", t))
        self._overwrite_cb.stateChanged.connect(lambda v: c.set("overwriteExisting", bool(v)))
        self._open_folder_cb.stateChanged.connect(lambda v: c.set("openFolderAfter", bool(v)))
        self._minimize_tray_cb.stateChanged.connect(lambda v: c.set("minimizeToTray", bool(v)))
        self._system_notify_cb.stateChanged.connect(lambda v: c.set("useSystemNotification", bool(v)))
        self._taskbar_cb.stateChanged.connect(lambda v: c.set("showTaskbarProgress", bool(v)))
        self._silent_mode_combo.currentIndexChanged.connect(lambda: c.set("silentMode", self._silent_mode_combo.currentData()))
        self._file_progress_combo.currentIndexChanged.connect(lambda: c.set("fileProgressStyle", self._file_progress_combo.currentData()))

    def save_to_config(self):
        c = self._cfg
        theme = self._theme_combo.currentData()
        c.set("theme", theme.value if isinstance(theme, Theme) else Theme.LIGHT.value)
        c.set("defaultOutputDir", self.default_output_dir)
        c.set("defaultOutputSuffix", self.output_suffix)
        c.set("overwriteExisting", self.overwrite_existing)
        c.set("openFolderAfter", self.open_folder_after)
        c.set("minimizeToTray", self.minimize_to_tray)
        c.set("consoleLogEnabled", self._log_enable_cb.isChecked())
        c.set("useSystemNotification", self._system_notify_cb.isChecked())
        c.set("showTaskbarProgress", self._taskbar_cb.isChecked())
        c.set("silentMode", self._silent_mode_combo.currentData())
        c.set("fileProgressStyle", self._file_progress_combo.currentData())

    def load(self):
        c = self._cfg

        self._theme_combo.blockSignals(True)
        self._output_dir.blockSignals(True)
        self._suffix_edit.blockSignals(True)
        self._overwrite_cb.blockSignals(True)
        self._open_folder_cb.blockSignals(True)
        self._minimize_tray_cb.blockSignals(True)
        self._log_enable_cb.blockSignals(True)
        self._system_notify_cb.blockSignals(True)
        self._taskbar_cb.blockSignals(True)
        self._silent_mode_combo.blockSignals(True)
        self._file_progress_combo.blockSignals(True)

        theme_val = c.get("theme", Theme.LIGHT.value)
        for i in range(self._theme_combo.count()):
            d = self._theme_combo.itemData(i)
            if d.value == theme_val:
                self._theme_combo.setCurrentIndex(i)
                break

        self._output_dir.setText(c.get("defaultOutputDir", ""))
        self._suffix_edit.setText(c.get("defaultOutputSuffix", "_RCSW"))
        self._overwrite_cb.setChecked(bool(c.get("overwriteExisting", False)))
        self._open_folder_cb.setChecked(bool(c.get("openFolderAfter", False)))
        self._minimize_tray_cb.setChecked(bool(c.get("minimizeToTray", False)))

        log_enabled = c.get("consoleLogEnabled", False)
        if not isinstance(log_enabled, bool):
            log_enabled = False
        self._log_enable_cb.setChecked(log_enabled)
        set_console_enabled(log_enabled)

        self._system_notify_cb.setChecked(bool(c.get("useSystemNotification", False)))
        self._taskbar_cb.setChecked(bool(c.get("showTaskbarProgress", True)))
        silent_mode = c.get("silentMode", "mini")
        for i in range(self._silent_mode_combo.count()):
            if self._silent_mode_combo.itemData(i) == silent_mode:
                self._silent_mode_combo.setCurrentIndex(i)
                break
        fp_style = c.get("fileProgressStyle", "bar")
        for i in range(self._file_progress_combo.count()):
            if self._file_progress_combo.itemData(i) == fp_style:
                self._file_progress_combo.setCurrentIndex(i)
                break

        self._theme_combo.blockSignals(False)
        self._output_dir.blockSignals(False)
        self._suffix_edit.blockSignals(False)
        self._overwrite_cb.blockSignals(False)
        self._open_folder_cb.blockSignals(False)
        self._minimize_tray_cb.blockSignals(False)
        self._log_enable_cb.blockSignals(False)
        self._system_notify_cb.blockSignals(False)
        self._taskbar_cb.blockSignals(False)
        self._silent_mode_combo.blockSignals(False)
        self._file_progress_combo.blockSignals(False)
