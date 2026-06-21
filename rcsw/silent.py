from __future__ import annotations

import os
import sys
from typing import Callable

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)

from .core.config import Config
from .core.logger import get_logger

_log = get_logger("silent")


class MiniProgressWindow(QDialog):

    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RCSW - 处理中")
        self.setFixedSize(420, 130)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self._setup_ui()
        self._cancelled = False

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        self._file_label = QLabel("准备中...")
        layout.addWidget(self._file_label)

        self._page_progress = QProgressBar()
        self._page_progress.setRange(0, 100)
        layout.addWidget(self._page_progress)

        self._page_label = QLabel("")
        layout.addWidget(self._page_label)

        btn_row = QHBoxLayout()
        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addStretch()
        btn_row.addWidget(self._cancel_btn)
        layout.addLayout(btn_row)

    def _on_cancel(self):
        self._cancelled = True
        self.cancelled.emit()

    def update_file(self, filename: str):
        self._file_label.setText(f"处理中: {filename}")
        self._page_progress.setValue(0)
        self._page_label.setText("")

    def update_page(self, current: int, total: int):
        if total > 0:
            pct = int(current / total * 100)
            self._page_progress.setValue(pct)
            self._page_label.setText(f"{current}/{total} 页 ({pct}%)")

    def show_done(self, success: int, errors: int):
        self._file_label.setText(f"处理完成: 成功 {success}, 失败 {errors}")
        self._page_progress.setValue(100)
        self._cancel_btn.setText("关闭")
        self._cancel_btn.clicked.disconnect()
        self._cancel_btn.clicked.connect(self.accept)

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled


def run_silent(
    file_paths: list[str],
    mode: str = "mini",
    on_progress: Callable[[int, int, str], None] | None = None,
    on_finished: Callable[[list, list], None] | None = None,
    check_cancel: Callable[[], bool] | None = None,
) -> tuple[list, list]:
    """静默处理 PDF 文件，不创建主窗口。

    Args:
        file_paths: PDF 文件路径列表
        mode: "headless" 或 "mini"
        on_progress: 进度回调 (current, total, filename)
        on_finished: 完成回调 (success_files, error_files)
        check_cancel: 取消检查回调

    Returns:
        (success_files, error_files) 元组
    """
    import fitz

    cfg = Config.instance()
    dpi = int(cfg.get("dpi", 200) or 0)
    jpeg_quality = int(cfg.get("jpegQuality", 90))
    max_wm_size = int(cfg.get("maxWmSize", 500))
    output_suffix = cfg.get("outputSuffix", "_RCSW")
    overwrite = cfg.get("overwriteExisting", False)

    scale_mode_str = cfg.get("scaleMode", "fill_crop")
    wm_mode_str = cfg.get("wmMode", "auto")

    from .core.models import ScaleMode, WatermarkMode
    from .core.detector import detect_watermarks
    from .core.processor import process_page

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
    total_pages_all = 0
    docs = []
    page_counts = []

    for fp in file_paths:
        try:
            doc = fitz.open(fp)
            docs.append(doc)
            pc = doc.page_count
            page_counts.append(pc)
            total_pages_all += pc
        except Exception as e:
            error_files.append((fp, str(e)))
            docs.append(None)
            page_counts.append(0)

    global_idx = 0
    for fi, (fp, doc) in enumerate(zip(file_paths, docs)):
        if check_cancel and check_cancel():
            break
        if doc is None:
            global_idx += page_counts[fi]
            continue

        try:
            wm_indices = detect_watermarks(doc, max_wm_size, wm_mode)
            new_doc = fitz.open()
            base_name = os.path.splitext(os.path.basename(fp))[0]

            for pi in range(doc.page_count):
                if check_cancel and check_cancel():
                    break
                page = doc[pi]
                pw = page.mediabox.width
                ph = page.mediabox.height
                wm_set = wm_indices[pi]

                img_data = process_page(
                    page, wm_set, pw, ph, dpi, jpeg_quality,
                    scale_mode, doc,
                )
                np = new_doc.new_page(width=pw, height=ph)
                if img_data:
                    np.insert_image(fitz.Rect(0, 0, pw, ph), stream=img_data)

                global_idx += 1
                if on_progress:
                    on_progress(global_idx, total_pages_all, os.path.basename(fp))

            if check_cancel and check_cancel():
                new_doc.close()
                break

            out_path = _resolve_path(
                os.path.dirname(fp), base_name, output_suffix, overwrite
            )
            new_doc.save(out_path, deflate=True, garbage=4, clean=True)
            new_doc.close()
            success_files.append((fp, out_path))

        except Exception as e:
            error_files.append((fp, str(e)))
            global_idx += page_counts[fi]

    for doc in docs:
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass

    if on_finished:
        on_finished(success_files, error_files)

    return success_files, error_files


def _resolve_path(dir_: str, base: str, suffix: str, overwrite: bool) -> str:
    out = os.path.join(dir_, f"{base}{suffix}.pdf")
    if overwrite:
        return out
    counter = 1
    while os.path.exists(out):
        out = os.path.join(dir_, f"{base}{suffix}_{counter}.pdf")
        counter += 1
    return out


def parse_file_args(argv: list[str]) -> list[str]:
    """解析命令行参数中的 PDF 文件路径。"""
    pdfs = []
    for arg in argv[1:]:
        arg = arg.strip().strip('"').strip("'")
        if arg.lower().endswith(".pdf") and os.path.isfile(arg):
            pdfs.append(os.path.abspath(arg))
    return pdfs
