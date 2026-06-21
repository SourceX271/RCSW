from __future__ import annotations

from collections import Counter
from typing import Callable, List, Set

import fitz

from .models import WatermarkMode
from .logger import get_logger

_log = get_logger("detector")


def detect_watermarks(
    doc: fitz.Document,
    max_wm_size: int = 500,
    wm_mode: WatermarkMode = WatermarkMode.AUTO,
    cancel_fn: Callable[[], bool] | None = None,
) -> List[Set[int]]:
    """返回每页的水印图片索引集合。"""
    result, _ = detect_watermarks_with_images(doc, max_wm_size, wm_mode, cancel_fn)
    return result


def detect_watermarks_with_images(
    doc: fitz.Document,
    max_wm_size: int = 500,
    wm_mode: WatermarkMode = WatermarkMode.AUTO,
    cancel_fn: Callable[[], bool] | None = None,
) -> tuple[List[Set[int]], list[list[tuple]]]:
    """返回 (每页水印索引, 每页图片信息列表)。"""
    page_count = doc.page_count
    all_candidates: List[List[int]] = []
    all_imgs: list[list[tuple]] = []

    for pi in range(page_count):
        if cancel_fn and cancel_fn():
            return [set() for _ in range(page_count)], [[] for _ in range(page_count)]

        page = doc[pi]
        pw = page.mediabox.width
        ph = page.mediabox.height
        imgs = page.get_images(full=True)
        all_imgs.append(imgs)
        candidates = _filter_by_size(imgs, max_wm_size)

        if wm_mode != WatermarkMode.AUTO:
            candidates = _filter_by_position(
                page, imgs, candidates, pw, ph, wm_mode
            )

        all_candidates.append(candidates)

    if wm_mode == WatermarkMode.AUTO and page_count > 1:
        all_candidates = _filter_by_xref_consistency(all_imgs, all_candidates)

    result = [set(candidates) for candidates in all_candidates]
    _log.debug(
        "检测完成: %d页, 模式=%s, 最大尺寸=%d, 共%d个水印",
        page_count, wm_mode.value, max_wm_size,
        sum(len(s) for s in result),
    )
    return result, all_imgs


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


_POSITION_MARGIN = 0.15


def _match_position(
    rect: fitz.Rect,
    pw: float,
    ph: float,
    wm_mode: WatermarkMode,
) -> bool:
    margin = _POSITION_MARGIN
    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    if wm_mode == WatermarkMode.BOTTOM_RIGHT:
        return (cx > pw * (1 - margin) and cy > ph * (1 - margin) and
                x1 > pw * (1 - margin))
    if wm_mode == WatermarkMode.BOTTOM_LEFT:
        return (cx < pw * margin and cy > ph * (1 - margin) and
                x0 < pw * margin)
    if wm_mode == WatermarkMode.TOP_RIGHT:
        return (cx > pw * (1 - margin) and cy < ph * margin and
                x1 > pw * (1 - margin))
    if wm_mode == WatermarkMode.TOP_LEFT:
        return (cx < pw * margin and cy < ph * margin and
                x0 < pw * margin)
    if wm_mode == WatermarkMode.BOTTOM_CENTER:
        return abs(cx - pw / 2) < pw * 0.2 and cy > ph * (1 - margin)
    return False


def _filter_by_xref_consistency(
    all_imgs: list[list[tuple]],
    candidates_per_page: list[list[int]],
) -> list[list[int]]:
    page_count = len(all_imgs)
    xref_counter: Counter = Counter()

    for pi in range(page_count):
        imgs = all_imgs[pi]
        for idx in candidates_per_page[pi]:
            xref = imgs[idx][0]
            xref_counter[xref] += 1

    recurring_xrefs = {
        xref for xref, count in xref_counter.items()
        if count >= max(2, page_count // 3)
    }

    if not recurring_xrefs:
        return [[] for _ in range(page_count)]

    result = []
    for pi in range(page_count):
        imgs = all_imgs[pi]
        filtered = []
        for idx in candidates_per_page[pi]:
            if imgs[idx][0] in recurring_xrefs:
                filtered.append(idx)
        result.append(filtered)
    return result
