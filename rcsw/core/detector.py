from __future__ import annotations

from collections import Counter
from typing import Callable, List, Set

import fitz

from .models import WatermarkMode


def detect_watermarks(
    doc: fitz.Document,
    max_wm_size: int = 500,
    wm_mode: WatermarkMode = WatermarkMode.AUTO,
    cancel_fn: Callable[[], bool] | None = None,
) -> List[Set[int]]:
    page_count = doc.page_count
    all_candidates: List[List[int]] = []
    all_imgs: list[list[tuple]] = []

    for pi in range(page_count):
        if cancel_fn and cancel_fn():
            return [set() for _ in range(page_count)]

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

    return [set(candidates) for candidates in all_candidates]


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
        return candidates_per_page

    result = []
    for pi in range(page_count):
        imgs = all_imgs[pi]
        filtered = []
        for idx in candidates_per_page[pi]:
            if imgs[idx][0] in recurring_xrefs:
                filtered.append(idx)
        result.append(filtered)
    return result
