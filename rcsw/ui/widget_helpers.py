from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout
from qfluentwidgets import BodyLabel, ComboBox, Slider, SpinBox


def make_combo_row(label: str, items: list[Any], labels: dict[Any, str], default: Any, label_width: int = 150) -> tuple[QHBoxLayout, ComboBox]:
    row = QHBoxLayout()
    row.setSpacing(12)
    lbl = BodyLabel(label)
    lbl.setFixedWidth(label_width)
    row.addWidget(lbl)

    combo = ComboBox()
    for item in items:
        combo.addItem(labels[item], userData=item)
    idx = items.index(default) if default in items else 0
    combo.setCurrentIndex(idx)
    combo.setObjectName(f"combo_{label}")
    row.addWidget(combo, 1)
    return row, combo


def make_slider_row(label: str, lo: int, hi: int, default: int, suffix: str, label_width: int = 150) -> tuple[QHBoxLayout, Slider, SpinBox]:
    row = QHBoxLayout()
    row.setSpacing(12)
    lbl = BodyLabel(label)
    lbl.setFixedWidth(label_width)
    row.addWidget(lbl)

    slider = Slider(Qt.Orientation.Horizontal)
    slider.setRange(lo, hi)
    slider.setValue(default)
    row.addWidget(slider, 1)

    spin = SpinBox()
    spin.setRange(lo, hi)
    spin.setValue(default)
    spin.setFixedWidth(72)
    spin.setSuffix(f" {suffix}")
    row.addWidget(spin)

    slider.valueChanged.connect(spin.setValue)
    spin.valueChanged.connect(slider.setValue)
    return row, slider, spin
