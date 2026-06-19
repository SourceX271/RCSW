from __future__ import annotations

from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QLabel,
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
    SegmentedWidget,
    StrongBodyLabel,
)

from ..core.models import (
    ScaleMode,
    SCALE_MODE_LABELS,
    WatermarkMode,
    WM_MODE_LABELS,
    QualityTier,
    QUALITY_TIERS,
    tier_from_dpi_q,
)
from ..core.config import Config
from .widget_helpers import make_combo_row, make_slider_row
from .style import ACCENT, hint_color, dot_inactive_color, TIER_LABEL_STYLE, PANEL_BG, TransparentCard


class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPanel")
        self._block_sync = False
        self._tier_labels: list[QLabel] = []
        self._dpi_slider: Slider | None = None
        self._dpi_spin: SpinBox | None = None
        self._jpeg_slider: Slider | None = None
        self._jpeg_spin: SpinBox | None = None
        self._wm_slider: Slider | None = None
        self._wm_spin: SpinBox | None = None
        self._scale_combo: ComboBox | None = None
        self._wm_mode_combo: ComboBox | None = None
        self._quality_slider: Slider | None = None
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

        self._mode_switcher = SegmentedWidget()
        self._mode_switcher.addItem("basic", "基础设置", onClick=None)
        self._mode_switcher.addItem("advanced", "高级设置", onClick=None)
        self._mode_switcher.setFixedHeight(36)
        self._mode_switcher.currentItemChanged.connect(
            lambda key: self._switch_mode(key)
        )
        layout.addWidget(self._mode_switcher)

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
        base_layout.addLayout(self._make_quality_slider_row())
        base_layout.addLayout(self._make_output_dir_row())
        base_layout.addLayout(self._make_suffix_row())

        root_layout.addWidget(base_card)

        self._adv_card = TransparentCard()
        self._adv_card.setObjectName("advCard")
        adv_layout = QVBoxLayout(self._adv_card)
        adv_layout.setContentsMargins(16, 12, 16, 16)
        adv_layout.setSpacing(16)

        sep_label = StrongBodyLabel("高级选项")
        sep_label.setObjectName("advSectionTitle")
        adv_layout.addWidget(sep_label)

        self._dpi_row, dpi_slider, dpi_spin = make_slider_row("输出 DPI", 72, 600, 200, "", 140)
        dpi_slider.valueChanged.connect(self._on_advanced_param_changed)
        dpi_spin.valueChanged.connect(self._on_advanced_param_changed)
        self._dpi_slider = dpi_slider
        self._dpi_spin = dpi_spin
        adv_layout.addLayout(self._dpi_row)

        self._jpeg_row, jpeg_slider, jpeg_spin = make_slider_row("JPEG 质量", 50, 100, 90, "", 140)
        jpeg_slider.valueChanged.connect(self._on_advanced_param_changed)
        jpeg_spin.valueChanged.connect(self._on_advanced_param_changed)
        self._jpeg_slider = jpeg_slider
        self._jpeg_spin = jpeg_spin
        adv_layout.addLayout(self._jpeg_row)

        self._wm_row, self._wm_slider, self._wm_spin = make_slider_row("最大水印尺寸 (px)", 100, 1000, 500, "", 140)
        adv_layout.addLayout(self._wm_row)

        wm_mode_row, self._wm_mode_combo = make_combo_row(
            "水印位置", list(WatermarkMode), WM_MODE_LABELS, WatermarkMode.AUTO, 140
        )
        adv_layout.addLayout(wm_mode_row)

        root_layout.addWidget(self._adv_card)
        root_layout.addStretch()

        scroll.setWidget(root)
        scroll.enableTransparentBackground()
        layout.addWidget(scroll, 1)

        self._mode_switcher.blockSignals(True)
        self._mode_switcher.setCurrentItem("basic")
        self._mode_switcher.blockSignals(False)
        self._switch_mode("basic")

    def _switch_mode(self, mode: str):
        is_adv = mode == "advanced"
        self._adv_card.setVisible(is_adv)

        if mode == "basic":
            self._block_sync = True
            tier = tier_from_dpi_q(self.dpi, self.jpeg_quality)
            self._last_quality_tier = tier
            self._quality_slider.setValue(self._tier_to_value(tier))
            self._block_sync = False

    def _make_quality_slider_row(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = BodyLabel("输出质量")
        lbl.setFixedWidth(140)
        row.addWidget(lbl)

        container = QVBoxLayout()
        container.setSpacing(6)

        slider = Slider(Qt.Orientation.Horizontal)
        slider.setRange(0, 300)
        slider.setValue(112)
        slider.setSingleStep(25)
        slider.setPageStep(75)
        slider.setObjectName("qualitySlider")
        slider.installEventFilter(self)
        container.addWidget(slider)

        dot_row = QHBoxLayout()
        dot_row.setContentsMargins(6, 0, 6, 2)
        dot_row.setSpacing(0)
        self._tier_dots: list[QLabel] = []
        for i in range(4):
            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setCursor(Qt.CursorShape.PointingHandCursor)
            dot.setProperty("tier", i)
            dot.installEventFilter(self)
            dot_row.addWidget(dot, 1, Qt.AlignmentFlag.AlignHCenter)
            self._tier_dots.append(dot)
        container.addLayout(dot_row)

        label_row = QHBoxLayout()
        label_row.setContentsMargins(0, 0, 0, 0)
        for i, t in enumerate(QUALITY_TIERS):
            lbl_text = t.name
            if t.hint:
                lbl_text = f"{t.name} ({t.hint})"
            lbl = QLabel(lbl_text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            lbl.setProperty("tier", i)
            lbl.installEventFilter(self)
            label_row.addWidget(lbl, 1)
            self._tier_labels.append(lbl)
        container.addLayout(label_row)

        row.addLayout(container, 1)

        slider.valueChanged.connect(self._on_quality_slider_changed)
        self._quality_slider = slider

        self._update_tier_labels(1)
        self._update_tier_dots(1)
        return row

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

    def _value_to_tier(self, value: int) -> int:
        return min(3, value // 75)

    def _tier_to_value(self, tier: int) -> int:
        return tier * 75 + 37

    def _update_tier_labels(self, active: int):
        for i, lbl in enumerate(self._tier_labels):
            if i == active:
                lbl.setStyleSheet(
                    f"color: {ACCENT}; {TIER_LABEL_STYLE} font-weight: bold;"
                )
            else:
                lbl.setStyleSheet(f"color: {hint_color()}; {TIER_LABEL_STYLE}")

    def _update_tier_dots(self, active: int):
        for i, dot in enumerate(self._tier_dots):
            if i == active:
                dot.setStyleSheet(
                    f"border-radius: 5px; background-color: {ACCENT};"
                )
            else:
                dot.setStyleSheet(
                    f"border-radius: 5px; background-color: {dot_inactive_color()};"
                )

    def _on_quality_slider_changed(self, value: int):
        tier = self._value_to_tier(value)
        self._update_tier_labels(tier)
        self._update_tier_dots(tier)

        if getattr(self, "_last_quality_tier", None) == tier:
            return
        self._last_quality_tier = tier

        if self._block_sync:
            return
        self._apply_tier(tier)

    def _apply_tier(self, tier: int):
        t = QUALITY_TIERS[tier]
        dpi_val, jpg_val = t.dpi, t.jpeg

        self._block_sync = True

        if self._dpi_slider:
            self._dpi_slider.setEnabled(dpi_val > 0)
            if dpi_val > 0:
                self._dpi_slider.setValue(dpi_val)
        if self._dpi_spin:
            self._dpi_spin.setEnabled(dpi_val > 0)
            if dpi_val > 0:
                self._dpi_spin.setValue(dpi_val)

        if self._jpeg_slider:
            self._jpeg_slider.setValue(jpg_val)
        if self._jpeg_spin:
            self._jpeg_spin.setValue(jpg_val)

        self._block_sync = False

    def _on_advanced_param_changed(self, _value):
        if self._block_sync:
            return
        self._block_sync = True
        tier = tier_from_dpi_q(self.dpi, self.jpeg_quality)
        self._last_quality_tier = tier
        self._quality_slider.setValue(self._tier_to_value(tier))
        self._update_tier_labels(tier)
        self._update_tier_dots(tier)
        self._block_sync = False

    def _on_browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self._output_dir.setText(path)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonRelease:
            tier = watched.property("tier")
            if tier is not None and isinstance(tier, int):
                self._quality_slider.setValue(self._tier_to_value(tier))
                return True
        return super().eventFilter(watched, event)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.StyleChange:
            if hasattr(self, '_tier_labels') and self._tier_labels:
                qv = self._quality_slider.value() if self._quality_slider else 112
                tier = self._value_to_tier(qv)
                self._update_tier_labels(tier)
                self._update_tier_dots(tier)
        super().changeEvent(event)

    def showEvent(self, event):
        self.load()
        super().showEvent(event)

    @property
    def dpi(self) -> int:
        if self._quality_slider and self._value_to_tier(self._quality_slider.value()) == 3:
            return 0
        return self._dpi_slider.value() if self._dpi_slider else 200

    @property
    def jpeg_quality(self) -> int:
        return self._jpeg_slider.value() if self._jpeg_slider else 90

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
        qv = self._quality_slider.value() if self._quality_slider else 112
        c.set("qualitySliderValue", qv)
        c.set("dpi", self.dpi)
        c.set("jpegQuality", self.jpeg_quality)
        c.set("maxWmSize", self.max_wm_size)
        c.set("wmMode", self.wm_mode.value)
        c.set("outputDir", self.output_dir)
        c.set("outputSuffix", self.output_suffix)

    def _default_quality_tier(self) -> QualityTier:
        ci = self._cfg.get("defaultQualityIndex", 1)
        idx = max(0, min(int(ci), len(QUALITY_TIERS) - 1))
        return QUALITY_TIERS[idx]

    def load(self):
        c = self._cfg
        if self._scale_combo:
            mode = c.get("scaleMode") or c.get("defaultScaleMode", ScaleMode.FILL_CROP.value)
            for i in range(self._scale_combo.count()):
                d = self._scale_combo.itemData(i)
                if isinstance(d, ScaleMode) and d.value == mode:
                    self._scale_combo.setCurrentIndex(i)
                    break
        if self._quality_slider:
            self._block_sync = True
            qv = c.get("qualitySliderValue")
            if qv is not None:
                self._quality_slider.setValue(int(qv))
            else:
                t = self._default_quality_tier()
                self._quality_slider.setValue(self._tier_to_value(tier_from_dpi_q(t.dpi, t.jpeg)))
            self._block_sync = False
        if self._dpi_slider:
            self._block_sync = True
            dpi = c.get("dpi")
            if dpi is not None:
                self._dpi_slider.setValue(int(dpi))
            else:
                self._dpi_slider.setValue(self._default_quality_tier().dpi)
            self._block_sync = False
        if self._jpeg_slider:
            self._block_sync = True
            jpg = c.get("jpegQuality")
            if jpg is not None:
                self._jpeg_slider.setValue(int(jpg))
            else:
                self._jpeg_slider.setValue(self._default_quality_tier().jpeg)
            self._block_sync = False
        if self._wm_slider:
            val = c.get("maxWmSize")
            if val is None:
                val = c.get("defaultWmSize", 500)
            self._wm_slider.setValue(int(val))
        if self._wm_mode_combo:
            mode = c.get("wmMode") or c.get("defaultWmMode", WatermarkMode.AUTO.value)
            for i in range(self._wm_mode_combo.count()):
                d = self._wm_mode_combo.itemData(i)
                if isinstance(d, WatermarkMode) and d.value == mode:
                    self._wm_mode_combo.setCurrentIndex(i)
                    break
        if self._output_dir:
            val = c.get("outputDir")
            if not val:
                val = c.get("defaultOutputDir", "")
            self._output_dir.setText(val)
        if self._output_suffix:
            val = c.get("outputSuffix")
            if not val:
                val = c.get("defaultOutputSuffix", "_RCSW")
            self._output_suffix.setText(val)
