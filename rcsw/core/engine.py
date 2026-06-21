from __future__ import annotations

import os
from typing import Callable

import fitz

from .models import ScaleMode, WatermarkMode
from .detector import detect_watermarks_with_images
from .processor import process_page
from .logger import get_logger
from .utils import resolve_output_path

_log = get_logger("engine")


def process_file(
    file_path: str,
    output_dir: str,
    dpi: int,
    jpeg_quality: int,
    max_wm_size: int,
    wm_mode: WatermarkMode,
    scale_mode: ScaleMode,
    output_suffix: str,
    overwrite: bool,
    cancel_fn: Callable[[], bool] | None = None,
    page_progress_fn: Callable[[int, int, str], None] | None = None,
    pre_opened_doc: fitz.Document | None = None,
) -> tuple[str, str] | None:
    """处理单个 PDF 文件。返回 (源文件路径, 输出路径) 或 None(取消/失败)。"""
    if pre_opened_doc is not None:
        doc = pre_opened_doc
        own_doc = False
    else:
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            _log.error("无法打开文件 %s: %s", os.path.basename(file_path), e)
            return None
        own_doc = True

    new_doc = None
    try:
        wm_indices_list, all_imgs = detect_watermarks_with_images(
            doc, max_wm_size, wm_mode, cancel_fn=cancel_fn,
        )

        page_count = doc.page_count
        file_basename = os.path.basename(file_path)

        new_doc = fitz.open()
        for pi in range(page_count):
            if cancel_fn and cancel_fn():
                break

            page = doc[pi]
            page_w = page.mediabox.width
            page_h = page.mediabox.height
            wm_set = wm_indices_list[pi]

            img_data = process_page(
                page, wm_set, page_w, page_h, dpi, jpeg_quality,
                scale_mode, doc, cached_imgs=all_imgs[pi],
            )

            new_page = new_doc.new_page(width=page_w, height=page_h)
            if img_data:
                new_page.insert_image(
                    fitz.Rect(0, 0, page_w, page_h), stream=img_data,
                )

            if page_progress_fn:
                page_progress_fn(pi + 1, page_count, file_basename)

        if cancel_fn and cancel_fn():
            return None

        base_name = os.path.splitext(file_basename)[0]
        out_path = resolve_output_path(output_dir, base_name, output_suffix, overwrite)
        new_doc.save(out_path, deflate=True, garbage=4, clean=True)

        out_size = os.path.getsize(out_path) / (1024 * 1024)
        _log.info("已保存: %s -> %s (%.1f MB, %d 页)",
                   file_basename, os.path.basename(out_path),
                   out_size, page_count)
        return (file_path, out_path)

    except Exception as e:
        _log.error("处理文件失败 %s: %s", os.path.basename(file_path), e)
        return None
    finally:
        if new_doc is not None:
            try:
                new_doc.close()
            except Exception as e:
                _log.warning("关闭输出文档失败: %s", e)
        if own_doc:
            try:
                doc.close()
            except Exception as e:
                _log.warning("关闭文档失败: %s", e)
