from __future__ import annotations

import os

from PySide6.QtCore import QThread, Signal

from .models import ScaleMode, WatermarkMode
from .engine import process_file
from .logger import get_logger
from .utils import resolve_output_path

import fitz

_log = get_logger("worker")


class ProcessingWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(list, list, str)
    file_started = Signal(int, str, int)
    file_progress = Signal(int, int, int)
    file_finished = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_paths: list[str] = []
        self._output_dir: str = ""
        self._dpi: int = 200
        self._jpeg_quality: int = 95
        self._max_wm_size: int = 500
        self._wm_mode: WatermarkMode = WatermarkMode.AUTO
        self._scale_mode: ScaleMode = ScaleMode.FILL_CROP
        self._output_suffix: str = "_RCSW"
        self._overwrite: bool = False

    def configure(
        self,
        file_paths: list[str],
        output_dir: str,
        dpi: int,
        jpeg_quality: int,
        max_wm_size: int,
        wm_mode: WatermarkMode,
        scale_mode: ScaleMode,
        output_suffix: str = "_RCSW",
        overwrite: bool = False,
    ):
        self._file_paths = list(file_paths)
        self._output_dir = output_dir
        self._dpi = dpi
        self._jpeg_quality = jpeg_quality
        self._max_wm_size = max_wm_size
        self._wm_mode = wm_mode
        self._scale_mode = scale_mode
        self._output_suffix = output_suffix
        self._overwrite = overwrite

    def run(self):
        _log.info("开始处理 %d 个文件, DPI=%d, JPEG=%d, 缩放=%s",
                   len(self._file_paths), self._dpi, self._jpeg_quality,
                   self._scale_mode.value)
        success_files = []
        error_files = []
        page_counts: list[int] = []
        docs: list[fitz.Document | None] = []

        for fp in self._file_paths:
            try:
                doc = fitz.open(fp)
                docs.append(doc)
                page_counts.append(doc.page_count)
            except Exception as e:
                error_files.append((fp, str(e)))
                docs.append(None)
                page_counts.append(0)

        total_pages_all = sum(page_counts)
        global_idx = [0]

        for fi, fp in enumerate(self._file_paths):
            if self.isInterruptionRequested():
                break
            if docs[fi] is None:
                global_idx[0] += page_counts[fi]
                continue

            doc = docs[fi]
            self.file_started.emit(fi, os.path.basename(fp), doc.page_count)
            pages_before = global_idx[0]

            def make_progress(f_idx: int, f_name: str):
                def cb(cur: int, total: int, _fname: str):
                    global_idx[0] += 1
                    self.progress.emit(global_idx[0], total_pages_all, f_name)
                    self.file_progress.emit(f_idx, cur, total)
                return cb

            result = process_file(
                file_path=fp,
                output_dir=self._output_dir,
                dpi=self._dpi,
                jpeg_quality=self._jpeg_quality,
                max_wm_size=self._max_wm_size,
                wm_mode=self._wm_mode,
                scale_mode=self._scale_mode,
                output_suffix=self._output_suffix,
                overwrite=self._overwrite,
                cancel_fn=self.isInterruptionRequested,
                page_progress_fn=make_progress(fi, os.path.basename(fp)),
                pre_opened_doc=doc,
            )

            if result is None:
                processed = global_idx[0] - pages_before
                remaining = max(0, page_counts[fi] - processed)
                global_idx[0] += remaining
                if not self.isInterruptionRequested():
                    error_files.append((fp, "处理失败"))
            else:
                success_files.append(result)
                self.file_finished.emit(fi, result[1])

        for doc in docs:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass

        _log.info("处理完成: 成功%d, 失败%d, 输出目录=%s",
                   len(success_files), len(error_files), self._output_dir)
        self.finished.emit(success_files, error_files, self._output_dir)
