from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QFileDialog,
)
from qfluentwidgets import (
    BodyLabel,
    Slider,
    SpinBox,
    ComboBox,
    LineEdit,
    PushButton,
    ScrollArea,
    StrongBodyLabel,
    SegmentedWidget,
    Dialog,
    InfoBar,
    InfoBarPosition,
)

from ..core.models import (
    ScaleMode,
    SCALE_MODE_LABELS,
    WatermarkMode,
    WM_MODE_LABELS,
    QualityTier,
    QUALITY_TIERS,
)
from ..core.config import Config
from .widget_helpers import make_combo_row, make_slider_row
from .style import PANEL_BG, TransparentCard


class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPanel")
        self._current_tier_idx: int = 3
        self._wm_slider: Slider | None = None
        self._wm_spin: SpinBox | None = None
        self._scale_combo: ComboBox | None = None
        self._wm_mode_combo: ComboBox | None = None
        self._quality_segment: SegmentedWidget | None = None
        self._output_dir: LineEdit | None = None
        self._output_suffix: LineEdit | None = None
        self._cfg = Config.instance()
        self._setup_ui()
        self.load()

    def _setup_ui(self):
        self.setStyleSheet(PANEL_BG)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        title = StrongBodyLabel("处理设置")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("settingsScroll")

        root = QWidget()
        root.setAutoFillBackground(False)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 8, 0, 0)
        root_layout.setSpacing(12)

        base_card = TransparentCard()
        base_card.setObjectName("baseCard")
        base_layout = QVBoxLayout(base_card)
        base_layout.setContentsMargins(16, 12, 16, 16)
        base_layout.setSpacing(16)

        scale_row, self._scale_combo = make_combo_row(
            "缩放模式", list(ScaleMode), SCALE_MODE_LABELS, ScaleMode.FILL_CROP, 140
        )
        base_layout.addLayout(scale_row)
        base_layout.addLayout(self._make_quality_segment_row())

        self._wm_row, self._wm_slider, self._wm_spin = make_slider_row(
            "最大水印尺寸 (px)", 100, 1000, 500, "", 140
        )
        base_layout.addLayout(self._wm_row)

        wm_mode_row, self._wm_mode_combo = make_combo_row(
            "水印位置", list(WatermarkMode), WM_MODE_LABELS, WatermarkMode.AUTO, 140
        )
        base_layout.addLayout(wm_mode_row)

        base_layout.addLayout(self._make_output_dir_row())
        base_layout.addLayout(self._make_suffix_row())

        reset_btn = PushButton("恢复默认设置")
        reset_btn.clicked.connect(self._on_reset_settings)
        base_layout.addWidget(reset_btn, 0, Qt.AlignmentFlag.AlignRight)

        root_layout.addWidget(base_card)
        root_layout.addStretch()

        scroll.setWidget(root)
        scroll.enableTransparentBackground()
        layout.addWidget(scroll, 1)

        self._connect_settings()

    def _connect_settings(self):
        c = self._cfg
        if self._quality_segment:
            self._quality_segment.currentItemChanged.connect(
                lambda key: self._on_quality_changed(int(key))
            )
        if self._scale_combo:
            self._scale_combo.currentIndexChanged.connect(
                lambda: c.set("scaleMode", self.scale_mode.value)
            )
        if self._wm_slider:
            self._wm_slider.valueChanged.connect(
                lambda v: c.set("maxWmSize", v)
            )
        if self._wm_mode_combo:
            self._wm_mode_combo.currentIndexChanged.connect(
                lambda: c.set("wmMode", self.wm_mode.value)
            )
        if self._output_dir:
            self._output_dir.textChanged.connect(
                lambda t: c.set("outputDir", t)
            )
        if self._output_suffix:
            self._output_suffix.textChanged.connect(
                lambda t: c.set("outputSuffix", t)
            )

    def _make_quality_segment_row(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = BodyLabel("输出质量")
        lbl.setFixedWidth(140)
        row.addWidget(lbl)

        segment = SegmentedWidget()
        for i, t in enumerate(QUALITY_TIERS):
            segment.addItem(str(i), t.name, onClick=None)
        segment.setFixedHeight(36)
        segment.setCurrentItem(str(self._current_tier_idx))
        self._quality_segment = segment
        row.addWidget(segment, 1)
        return row

    def _on_quality_changed(self, tier: int):
        self._current_tier_idx = tier
        self._cfg.set("qualityTier", tier)
        self._cfg.set("dpi", QUALITY_TIERS[tier].dpi)
        self._cfg.set("jpegQuality", QUALITY_TIERS[tier].jpeg)

    def _make_output_dir_row(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = BodyLabel("输出目录")
        lbl.setFixedWidth(140)
        row.addWidget(lbl)

        self._output_dir = LineEdit()
        row.addWidget(self._output_dir, 1)

        btn = PushButton("浏览")
        btn.clicked.connect(self._on_browse_output)
        row.addWidget(btn)

        src_btn = PushButton("源文件目录")
        src_btn.clicked.connect(lambda: self._output_dir.setText(""))
        row.addWidget(src_btn)
        return row

    def _make_suffix_row(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = BodyLabel("输出文件名后缀")
        lbl.setFixedWidth(140)
        row.addWidget(lbl)

        self._output_suffix = LineEdit()
        self._output_suffix.setText("_RCSW")
        self._output_suffix.setObjectName("outputSuffix")
        row.addWidget(self._output_suffix, 1)
        return row

    def _on_browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self._output_dir.setText(path)

    def _on_reset_settings(self):
        dlg = Dialog("恢复默认", "确定要恢复处理设置为默认值吗？", self.window())
        dlg.setTitleBarVisible(False)
        dlg.yesSignal.connect(self._do_reset_settings)
        dlg.show()

    def _do_reset_settings(self):
        c = self._cfg
        defaults = {
            "scaleMode": ScaleMode.FILL_CROP.value,
            "qualityTier": 3,
            "dpi": QUALITY_TIERS[3].dpi,
            "jpegQuality": QUALITY_TIERS[3].jpeg,
            "maxWmSize": 500,
            "wmMode": WatermarkMode.AUTO.value,
            "outputDir": "",
            "outputSuffix": "_RCSW",
        }
        for k, v in defaults.items():
            c.set(k, v)
        self.load()
        InfoBar.success(
            title="已恢复", content="处理设置已恢复为默认值",
            parent=self.window(), position=InfoBarPosition.TOP, duration=3000,
        )

    def showEvent(self, event):
        self.load()
        super().showEvent(event)

    @property
    def dpi(self) -> int:
        return QUALITY_TIERS[self._current_tier_idx].dpi

    @property
    def jpeg_quality(self) -> int:
        return QUALITY_TIERS[self._current_tier_idx].jpeg

    @property
    def max_wm_size(self) -> int:
        return self._wm_slider.value() if self._wm_slider else 500

    @property
    def scale_mode(self) -> ScaleMode:
        if self._scale_combo:
            val = self._scale_combo.currentData()
            if isinstance(val, ScaleMode):
                return val
        return ScaleMode.FILL_CROP

    @property
    def wm_mode(self) -> WatermarkMode:
        if self._wm_mode_combo:
            val = self._wm_mode_combo.currentData()
            if isinstance(val, WatermarkMode):
                return val
        return WatermarkMode.AUTO

    @property
    def output_dir(self) -> str:
        return self._output_dir.text() if self._output_dir else ""

    @property
    def output_suffix(self) -> str:
        return self._output_suffix.text() if self._output_suffix else "_RCSW"

    def save_to_config(self):
        c = self._cfg
        c.set("scaleMode", self.scale_mode.value)
        c.set("qualityTier", self._current_tier_idx)
        c.set("dpi", self.dpi)
        c.set("jpegQuality", self.jpeg_quality)
        c.set("maxWmSize", self.max_wm_size)
        c.set("wmMode", self.wm_mode.value)
        c.set("outputDir", self.output_dir)
        c.set("outputSuffix", self.output_suffix)

    def _default_quality_tier(self) -> QualityTier:
        ci = self._cfg.get("defaultQualityIndex", 3)
        idx = max(0, min(int(ci), len(QUALITY_TIERS) - 1))
        return QUALITY_TIERS[idx]

    def load(self):
        c = self._cfg
        if self._scale_combo:
            mode = c.get("scaleMode") or ScaleMode.FILL_CROP.value
            for i in range(self._scale_combo.count()):
                d = self._scale_combo.itemData(i)
                if isinstance(d, ScaleMode) and d.value == mode:
                    self._scale_combo.setCurrentIndex(i)
                    break
        if self._quality_segment:
            tier = c.get("qualityTier", 3)
            if isinstance(tier, int) and 0 <= tier <= 3:
                self._current_tier_idx = tier
            else:
                self._current_tier_idx = 3
            self._quality_segment.blockSignals(True)
            self._quality_segment.setCurrentItem(str(self._current_tier_idx))
            self._quality_segment.blockSignals(False)
        if self._wm_slider:
            val = c.get("maxWmSize", 500)
            self._wm_slider.setValue(int(val))
        if self._wm_mode_combo:
            mode = c.get("wmMode") or WatermarkMode.AUTO.value
            for i in range(self._wm_mode_combo.count()):
                d = self._wm_mode_combo.itemData(i)
                if isinstance(d, WatermarkMode) and d.value == mode:
                    self._wm_mode_combo.setCurrentIndex(i)
                    break
        if self._output_dir:
            val = c.get("outputDir") or c.get("defaultOutputDir", "")
            self._output_dir.setText(val)
        if self._output_suffix:
            val = c.get("outputSuffix") or c.get("defaultOutputSuffix", "_RCSW")
            self._output_suffix.setText(val)
