from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QFileDialog,
)
from qfluentwidgets import (
    StrongBodyLabel,
    BodyLabel,
    CheckBox,
    ComboBox,
    Slider,
    LineEdit,
    PushButton,
    ScrollArea,
    CardWidget,
    SpinBox,
    setTheme,
    Theme,
)

from ..core.models import (
    ScaleMode,
    SCALE_MODE_LABELS,
    WatermarkMode,
    WM_MODE_LABELS,
    QUALITY_TIERS,
)
from ..core.config import Config
from .widget_helpers import make_combo_row, make_slider_row
from .style import PANEL_BG


class SoftwareSettingsPanel(QWidget):

    _theme_combo: ComboBox
    _scale_combo: ComboBox
    _quality_combo: ComboBox
    _wm_mode_combo: ComboBox
    _wm_size_slider: Slider
    _wm_size_spin: SpinBox
    _output_dir: LineEdit
    _suffix_edit: LineEdit
    _overwrite_cb: CheckBox
    _open_folder_cb: CheckBox

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

        c1 = CardWidget()
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

        root_layout.addWidget(c1)

        c2 = CardWidget()
        c2_layout = QVBoxLayout(c2)
        c2_layout.setContentsMargins(16, 12, 16, 16)
        c2_layout.setSpacing(14)
        c2_layout.addWidget(StrongBodyLabel("默认处理参数"))

        row, self._scale_combo = make_combo_row(
            "默认缩放模式",
            list(ScaleMode),
            SCALE_MODE_LABELS,
            ScaleMode.FILL_CROP,
        )
        c2_layout.addLayout(row)

        row, self._quality_combo = self._make_quality_row()
        c2_layout.addLayout(row)

        row, self._wm_mode_combo = make_combo_row(
            "默认水印位置",
            list(WatermarkMode),
            WM_MODE_LABELS,
            WatermarkMode.AUTO,
        )
        c2_layout.addLayout(row)

        row, self._wm_size_slider, self._wm_size_spin = make_slider_row(
            "默认水印尺寸阈值", 100, 1000, 500, "px"
        )
        c2_layout.addLayout(row)

        root_layout.addWidget(c2)

        c3 = CardWidget()
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

        root_layout.addStretch()

        scroll.setWidget(root)
        layout.addWidget(scroll, 1)

    def _make_quality_row(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = BodyLabel("默认输出质量")
        lbl.setFixedWidth(150)
        row.addWidget(lbl)

        combo = ComboBox()
        for t in QUALITY_TIERS:
            display = f"{t.name} — {t.hint}" if t.hint else f"{t.name} (DPI={t.dpi}, 质量={t.jpeg})"
            combo.addItem(display, userData=(t.dpi, t.jpeg))
        combo.setCurrentIndex(1)
        row.addWidget(combo, 1)
        return row, combo

    def _make_output_dir_row(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = BodyLabel("默认输出目录")
        lbl.setFixedWidth(150)
        row.addWidget(lbl)

        self._output_dir = LineEdit()
        self._output_dir.setReadOnly(True)
        self._output_dir.setPlaceholderText("留空则使用源文件所在目录")
        row.addWidget(self._output_dir, 1)

        btn = PushButton("浏览")
        btn.clicked.connect(self._on_browse_output)
        row.addWidget(btn)
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

    @property
    def default_scale_mode(self) -> ScaleMode:
        val = self._scale_combo.currentData()
        if isinstance(val, ScaleMode):
            return val
        return ScaleMode.FILL_CROP

    @property
    def default_wm_mode(self) -> WatermarkMode:
        val = self._wm_mode_combo.currentData()
        if isinstance(val, WatermarkMode):
            return val
        return WatermarkMode.AUTO

    @property
    def default_max_wm_size(self) -> int:
        return self._wm_size_slider.value()

    @property
    def default_quality_dpi(self) -> int:
        data = self._quality_combo.currentData()
        return data[0] if data else 200

    @property
    def default_quality_jpeg(self) -> int:
        data = self._quality_combo.currentData()
        return data[1] if data else 90

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

    def _connect_signals(self):
        c = self._cfg
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self._scale_combo.currentIndexChanged.connect(lambda: c.set("defaultScaleMode", self.default_scale_mode.value))
        self._quality_combo.currentIndexChanged.connect(lambda: c.set("defaultQualityIndex", self._quality_combo.currentIndex()))
        self._wm_mode_combo.currentIndexChanged.connect(lambda: c.set("defaultWmMode", self.default_wm_mode.value))
        self._wm_size_slider.valueChanged.connect(lambda v: c.set("defaultWmSize", v))
        self._output_dir.textChanged.connect(lambda t: c.set("defaultOutputDir", t))
        self._suffix_edit.textChanged.connect(lambda t: c.set("defaultOutputSuffix", t))
        self._overwrite_cb.stateChanged.connect(lambda v: c.set("overwriteExisting", bool(v)))
        self._open_folder_cb.stateChanged.connect(lambda v: c.set("openFolderAfter", bool(v)))

    def save_to_config(self):
        c = self._cfg
        theme = self._theme_combo.currentData()
        c.set("theme", theme.value if isinstance(theme, Theme) else Theme.LIGHT.value)
        c.set("defaultScaleMode", self.default_scale_mode.value)
        c.set("defaultQualityIndex", self._quality_combo.currentIndex())
        c.set("defaultWmMode", self.default_wm_mode.value)
        c.set("defaultWmSize", self.default_max_wm_size)
        c.set("defaultOutputDir", self.default_output_dir)
        c.set("defaultOutputSuffix", self.output_suffix)
        c.set("overwriteExisting", self.overwrite_existing)
        c.set("openFolderAfter", self.open_folder_after)

    def load(self):
        c = self._cfg
        theme_val = c.get("theme", Theme.LIGHT.value)
        for i in range(self._theme_combo.count()):
            d = self._theme_combo.itemData(i)
            if d.value == theme_val:
                self._theme_combo.setCurrentIndex(i)
                break

        mode = c.get("defaultScaleMode", ScaleMode.FILL_CROP.value)
        for i in range(self._scale_combo.count()):
            d = self._scale_combo.itemData(i)
            if isinstance(d, ScaleMode) and d.value == mode:
                self._scale_combo.setCurrentIndex(i)
                break

        idx = int(c.get("defaultQualityIndex", 1))
        self._quality_combo.setCurrentIndex(max(0, min(idx, self._quality_combo.count() - 1)))

        mode = c.get("defaultWmMode", WatermarkMode.AUTO.value)
        for i in range(self._wm_mode_combo.count()):
            d = self._wm_mode_combo.itemData(i)
            if isinstance(d, WatermarkMode) and d.value == mode:
                self._wm_mode_combo.setCurrentIndex(i)
                break

        self._wm_size_slider.setValue(int(c.get("defaultWmSize", 500)))
        self._output_dir.setText(c.get("defaultOutputDir", ""))
        self._suffix_edit.setText(c.get("defaultOutputSuffix", "_RCSW"))
        self._overwrite_cb.setChecked(bool(c.get("overwriteExisting", False)))
        self._open_folder_cb.setChecked(bool(c.get("openFolderAfter", False)))
