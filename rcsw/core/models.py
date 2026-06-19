from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass
class QualityTier:
    name: str
    dpi: int
    jpeg: int
    hint: str = ""


QUALITY_TIERS: list[QualityTier] = [
    QualityTier("低质量", 150, 75, "文件最小"),
    QualityTier("中等质量", 200, 90, "文件中等"),
    QualityTier("高质量", 300, 95, "文件较大"),
    QualityTier("原图", 0, 100, "文件最大"),
]


class ScaleMode(Enum):
    FILL_CROP = "fill_crop"
    FIT = "fit"
    STRETCH = "stretch"
    FIT_WIDTH = "fit_width"
    FIT_HEIGHT = "fit_height"


SCALE_MODE_LABELS: dict[ScaleMode, str] = {
    ScaleMode.FILL_CROP: "保持长宽比 - 填充整页（居中裁剪）",
    ScaleMode.FIT: "保持长宽比 - 适应页面（留白边距）",
    ScaleMode.STRETCH: "拉伸至整页",
    ScaleMode.FIT_WIDTH: "适应宽度",
    ScaleMode.FIT_HEIGHT: "适应高度",
}


class WatermarkMode(Enum):
    AUTO = "auto"
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_LEFT = "bottom_left"
    TOP_RIGHT = "top_right"
    TOP_LEFT = "top_left"
    BOTTOM_CENTER = "bottom_center"


WM_MODE_LABELS: dict[WatermarkMode, str] = {
    WatermarkMode.AUTO: "自动检测",
    WatermarkMode.BOTTOM_RIGHT: "右下角",
    WatermarkMode.BOTTOM_LEFT: "左下角",
    WatermarkMode.TOP_RIGHT: "右上角",
    WatermarkMode.TOP_LEFT: "左上角",
    WatermarkMode.BOTTOM_CENTER: "底部居中",
}


def tier_from_dpi_q(dpi: int, quality: int) -> int:
    if dpi == 0:
        return 3
    best = 1
    best_dist = 9999
    for i, t in enumerate(QUALITY_TIERS):
        if t.dpi == 0:
            continue
        dist = abs(dpi - t.dpi) + abs(quality - t.jpeg) * 2
        if dist < best_dist:
            best_dist = dist
            best = i
    return best
