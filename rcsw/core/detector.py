from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import List, Set

import fitz


@dataclass
class QualityTier:
    name: str
    dpi: int
    jpeg: int
    hint: str = ""


QUALITY_TIERS: list[QualityTier] = [
    QualityTier("低质量", 150, 75, "文件最小"),
    QualityTier("中等质量", 200, 90, "推荐"),
    QualityTier("高质量", 300, 95),
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


def detect_watermarks(
    doc: fitz.Document,
    max_wm_size: int = 500,
    wm_mode: WatermarkMode = WatermarkMode.AUTO,
) -> List[Set[int]]:
    page_count = doc.page_count
    all_candidates: List[List[int]] = []

    for pi in range(page_count):
        page = doc[pi]
        pw = page.mediabox.width
        ph = page.mediabox.height
        imgs = page.get_images(full=True)
        candidates = _filter_by_size(imgs, max_wm_size)

        if wm_mode != WatermarkMode.AUTO:
            candidates = _filter_by_position(
                page, imgs, candidates, pw, ph, wm_mode
            )

        all_candidates.append(candidates)

    if wm_mode == WatermarkMode.AUTO and page_count > 1:
        all_candidates = _filter_by_xref_consistency(doc, all_candidates)

    result: List[Set[int]] = []
    for candidates in all_candidates:
        result.append(set(candidates))
    return result


def _filter_by_size(imgs: list[tuple], max_wm_size: int) -> list[int]:
    candidates = []
    for idx, img in enumerate(imgs):
        w, h = img[2], img[3]
        if w <= max_wm_size and h <= max_wm_size:
            candidates.append(idx)
    return candidates


def _filter_by_position(
    page: fitz.Page,
    imgs: list[tuple],
    candidates: list[int],
    pw: float,
    ph: float,
    wm_mode: WatermarkMode,
) -> list[int]:
    result = []
    for idx in candidates:
        rects = page.get_image_rects(imgs[idx][0])
        if not rects:
            continue
        rect = rects[0]
        if _match_position(rect, pw, ph, wm_mode):
            result.append(idx)
    return result


def _match_position(
    rect: fitz.Rect,
    pw: float,
    ph: float,
    wm_mode: WatermarkMode,
) -> bool:
    margin = 0.15
    if wm_mode == WatermarkMode.BOTTOM_RIGHT:
        return rect.x0 > pw * (1 - margin) and rect.y0 > ph * (1 - margin)
    if wm_mode == WatermarkMode.BOTTOM_LEFT:
        return rect.x1 < pw * margin and rect.y0 > ph * (1 - margin)
    if wm_mode == WatermarkMode.TOP_RIGHT:
        return rect.x0 > pw * (1 - margin) and rect.y1 < ph * margin
    if wm_mode == WatermarkMode.TOP_LEFT:
        return rect.x1 < pw * margin and rect.y1 < ph * margin
    if wm_mode == WatermarkMode.BOTTOM_CENTER:
        cx = (rect.x0 + rect.x1) / 2
        return abs(cx - pw / 2) < pw * 0.2 and rect.y0 > ph * (1 - margin)
    return False


def _filter_by_xref_consistency(
    doc: fitz.Document,
    candidates_per_page: list[list[int]],
) -> list[list[int]]:
    page_count = doc.page_count
    xref_counter: Counter = Counter()
    xref_page_map: dict[int, set[int]] = {}

    for pi in range(page_count):
        page = doc[pi]
        imgs = page.get_images(full=True)
        for idx in candidates_per_page[pi]:
            xref = imgs[idx][0]
            xref_counter[xref] += 1
            xref_page_map.setdefault(xref, set()).add(pi)

    recurring_xrefs = {
        xref for xref, count in xref_counter.items() if count >= max(2, page_count // 3)
    }

    if not recurring_xrefs:
        return candidates_per_page

    result = []
    for pi in range(page_count):
        page = doc[pi]
        imgs = page.get_images(full=True)
        filtered = []
        for idx in candidates_per_page[pi]:
            xref = imgs[idx][0]
            if xref in recurring_xrefs:
                filtered.append(idx)
        result.append(filtered)
    return result
