from __future__ import annotations

import os
from typing import Callable

import fitz

from .core.config import Config
from .core.logger import get_logger
from .core.models import ScaleMode, WatermarkMode
from .core.engine import process_file

_log = get_logger("silent")


def run_silent(
    file_paths: list[str],
    on_progress: Callable[[int, int, str], None] | None = None,
    on_finished: Callable[[list, list], None] | None = None,
    check_cancel: Callable[[], bool] | None = None,
) -> tuple[list, list]:
    """静默处理 PDF 文件。"""
    cfg = Config.instance()
    dpi = int(cfg.get("dpi", 200) or 0)
    jpeg_quality = int(cfg.get("jpegQuality", 90))
    max_wm_size = int(cfg.get("maxWmSize", 500))
    output_suffix = cfg.get("outputSuffix", "_RCSW")
    overwrite = cfg.get("overwriteExisting", False)

    scale_mode_str = cfg.get("scaleMode", "fill_crop")
    wm_mode_str = cfg.get("wmMode", "auto")

    try:
        scale_mode = ScaleMode(scale_mode_str)
    except ValueError:
        scale_mode = ScaleMode.FILL_CROP

    try:
        wm_mode = WatermarkMode(wm_mode_str)
    except ValueError:
        wm_mode = WatermarkMode.AUTO

    success_files = []
    error_files = []
    docs: list[fitz.Document | None] = []
    page_counts: list[int] = []

    for fp in file_paths:
        try:
            doc = fitz.open(fp)
            docs.append(doc)
            page_counts.append(doc.page_count)
        except Exception as e:
            error_files.append((fp, str(e)))
            docs.append(None)
            page_counts.append(0)

    total_pages_all = sum(pc for pc in page_counts)
    global_idx = [0]

    def make_progress(fp_name: str) -> Callable:
        def cb(_current: int, _total: int, _fname: str):
            global_idx[0] += 1
            if on_progress:
                on_progress(global_idx[0], total_pages_all, fp_name)
        return cb

    for fi, fp in enumerate(file_paths):
        if check_cancel and check_cancel():
            break
        if docs[fi] is None:
            global_idx[0] += page_counts[fi]
            continue

        doc = docs[fi]
        try:
            result = process_file(
                file_path=fp,
                output_dir=os.path.dirname(fp),
                dpi=dpi,
                jpeg_quality=jpeg_quality,
                max_wm_size=max_wm_size,
                wm_mode=wm_mode,
                scale_mode=scale_mode,
                output_suffix=output_suffix,
                overwrite=overwrite,
                cancel_fn=check_cancel,
                page_progress_fn=make_progress(os.path.basename(fp)),
                pre_opened_doc=doc,
            )
            if result is None:
                error_files.append((fp, "处理失败或已取消"))
            else:
                success_files.append(result)
        except Exception as e:
            error_files.append((fp, str(e)))
            global_idx[0] += page_counts[fi]

    for doc in docs:
        if doc is not None:
            try:
                doc.close()
            except Exception as e:
                _log.warning("关闭文档失败: %s", e)

    if on_finished:
        on_finished(success_files, error_files)

    return success_files, error_files


def parse_file_args(argv: list[str]) -> list[str]:
    pdfs = []
    for arg in argv[1:]:
        arg = arg.strip().strip('"').strip("'")
        if arg.lower().endswith(".pdf") and os.path.isfile(arg):
            pdfs.append(os.path.abspath(arg))
    return pdfs
