from __future__ import annotations

import os

from PySide6.QtCore import QThread, Signal

from .models import ScaleMode, WatermarkMode
from .detector import detect_watermarks
from .processor import process_page
from .logger import get_logger

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

    def _resolve_output_path(self, base_name: str) -> str:
        out_path = os.path.join(
            self._output_dir, f"{base_name}{self._output_suffix}.pdf"
        )
        if self._overwrite:
            return out_path
        counter = 1
        while os.path.exists(out_path):
            out_path = os.path.join(
                self._output_dir, f"{base_name}{self._output_suffix}_{counter}.pdf"
            )
            counter += 1
            if counter > 9999:
                break
        return out_path

    def run(self):
        _log.info("开始处理 %d 个文件, DPI=%d, JPEG=%d, 缩放=%s",
                   len(self._file_paths), self._dpi, self._jpeg_quality,
                   self._scale_mode.value)
        success_files = []
        error_files = []
        total_pages_all = 0
        page_counts: list[int] = []
        docs: list[fitz.Document] = []

        for fp in self._file_paths:
            try:
                doc = fitz.open(fp)
                docs.append(doc)
                page_counts.append(doc.page_count)
                total_pages_all += doc.page_count
            except Exception as e:
                error_files.append((fp, str(e)))
                docs.append(None)
                page_counts.append(0)

        global_idx = 0

        for fi, (fp, doc) in enumerate(zip(self._file_paths, docs)):
            if self.isInterruptionRequested():
                break
            if doc is None:
                continue

            pages_before_file = global_idx
            new_doc = None

            try:
                wm_indices_list = detect_watermarks(
                    doc, self._max_wm_size, self._wm_mode,
                    cancel_fn=self.isInterruptionRequested,
                )

                self.file_started.emit(fi, os.path.basename(fp), doc.page_count)

                new_doc = fitz.open()
                for pi in range(doc.page_count):
                    if self.isInterruptionRequested():
                        break
                    page = doc[pi]
                    page_w = page.mediabox.width
                    page_h = page.mediabox.height
                    wm_set = wm_indices_list[pi]

                    img_data = process_page(
                        page,
                        wm_set,
                        page_w,
                        page_h,
                        self._dpi,
                        self._jpeg_quality,
                        self._scale_mode,
                        doc,
                    )

                    new_page = new_doc.new_page(width=page_w, height=page_h)
                    if img_data:
                        new_page.insert_image(
                            fitz.Rect(0, 0, page_w, page_h), stream=img_data
                        )

                    global_idx += 1
                    self.progress.emit(global_idx, total_pages_all, os.path.basename(fp))
                    self.file_progress.emit(fi, pi + 1, doc.page_count)

                if self.isInterruptionRequested():
                    break

                base_name = os.path.splitext(os.path.basename(fp))[0]
                out_path = self._resolve_output_path(base_name)
                new_doc.save(out_path, deflate=True, garbage=4, clean=True)
                success_files.append((fp, out_path))
                self.file_finished.emit(fi, out_path)
                out_size = os.path.getsize(out_path) / (1024 * 1024)
                _log.info("已保存: %s -> %s (%.1f MB, %d 页)",
                          os.path.basename(fp), os.path.basename(out_path),
                          out_size, doc.page_count)

            except Exception as e:
                if self.isInterruptionRequested():
                    break
                error_files.append((fp, str(e)))
                remaining = page_counts[fi] - (global_idx - pages_before_file)
                global_idx += max(0, remaining)
                _log.error("Error processing %s: %s", os.path.basename(fp), e)
            finally:
                if new_doc is not None:
                    try:
                        new_doc.close()
                    except Exception:
                        pass

        for doc in docs:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass

        _log.info("处理完成: 成功%d, 失败%d, 输出目录=%s",
                  len(success_files), len(error_files), self._output_dir)
        self.finished.emit(success_files, error_files, self._output_dir)
