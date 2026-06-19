from __future__ import annotations

import os

from PySide6.QtCore import QObject, Signal

from ..core.worker import ProcessingWorker
from ..core.config import Config
from ..core.logger import get_logger
from ..core.models import ScaleMode, WatermarkMode

_log = get_logger("controller")


def _safe_int(value, default=0):
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    try:
        return bool(int(value))
    except (ValueError, TypeError):
        return default


class UIController(QObject):
    processing_progress = Signal(int, int, str)
    processing_finished = Signal(list, list, str)
    processing_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: ProcessingWorker | None = None
        self._config = Config.instance()
        self._shutting_down = False

    @property
    def is_processing(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def load_all_settings(self) -> dict:
        c = self._config
        return {
            "theme": _safe_int(c.get("theme"), 0),
            "dpi": _safe_int(c.get("dpi"), 200),
            "jpeg_quality": _safe_int(c.get("jpegQuality"), 90),
            "max_wm_size": _safe_int(c.get("maxWmSize"), 500),
            "wm_mode": c.get("wmMode", WatermarkMode.AUTO.value),
            "scale_mode": c.get("scaleMode", ScaleMode.FILL_CROP.value),
            "output_dir": c.get("outputDir", ""),
            "output_suffix": c.get("outputSuffix", "_RCSW"),
            "quality_slider_value": _safe_int(c.get("qualitySliderValue"), 112),
            "default_quality_index": _safe_int(c.get("defaultQualityIndex"), 1),
            "default_scale_mode": c.get("defaultScaleMode", ScaleMode.FILL_CROP.value),
            "default_wm_mode": c.get("defaultWmMode", WatermarkMode.AUTO.value),
            "default_wm_size": _safe_int(c.get("defaultWmSize"), 500),
            "default_output_dir": c.get("defaultOutputDir", ""),
            "default_output_suffix": c.get("defaultOutputSuffix", "_RCSW"),
            "overwrite_existing": _safe_bool(c.get("overwriteExisting"), False),
            "open_folder_after": _safe_bool(c.get("openFolderAfter"), False),
        }

    def save_all_settings(self, settings: dict) -> bool:
        c = self._config
        key_map = {
            "theme": "theme",
            "dpi": "dpi",
            "jpeg_quality": "jpegQuality",
            "max_wm_size": "maxWmSize",
            "wm_mode": "wmMode",
            "scale_mode": "scaleMode",
            "output_dir": "outputDir",
            "output_suffix": "outputSuffix",
            "quality_slider_value": "qualitySliderValue",
            "default_quality_index": "defaultQualityIndex",
            "default_scale_mode": "defaultScaleMode",
            "default_wm_mode": "defaultWmMode",
            "default_wm_size": "defaultWmSize",
            "default_output_dir": "defaultOutputDir",
            "default_output_suffix": "defaultOutputSuffix",
            "overwrite_existing": "overwriteExisting",
            "open_folder_after": "openFolderAfter",
        }
        for sk, ck in key_map.items():
            if sk in settings:
                c.set(ck, settings[sk])
        return c.save()

    def start_processing(self, file_paths: list[str], settings: dict) -> bool:
        if self.is_processing:
            _log.warning("start_processing called while worker is running")
            return False

        output_dir = settings.get("output_dir", "")
        if not output_dir and file_paths:
            output_dir = os.path.dirname(file_paths[0])
        if not output_dir or not os.path.isdir(output_dir):
            return False

        self._shutting_down = False
        self._worker = ProcessingWorker()
        self._worker.configure(
            file_paths=list(file_paths),
            output_dir=output_dir,
            dpi=_safe_int(settings.get("dpi"), 200),
            jpeg_quality=_safe_int(settings.get("jpeg_quality"), 90),
            max_wm_size=_safe_int(settings.get("max_wm_size"), 500),
            wm_mode=settings.get("wm_mode", WatermarkMode.AUTO),
            scale_mode=settings.get("scale_mode", ScaleMode.FILL_CROP),
            output_suffix=settings.get("output_suffix", "_RCSW"),
            overwrite=_safe_bool(settings.get("overwrite"), False),
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
        return True

    def cancel_processing(self):
        if self._worker and not self._worker.isFinished():
            self._worker.requestInterruption()

    def shutdown(self):
        self._shutting_down = True
        if not self._worker:
            return
        if not self._worker.isRunning():
            return

        _log.info("Waiting for worker thread to finish...")
        self._worker.requestInterruption()

        self._worker.finished.disconnect(self._on_finished)
        self._worker.progress.disconnect(self._on_progress)

        if self._worker.wait(30000):
            _log.info("Worker thread finished gracefully")
        else:
            _log.warning("Worker thread did not finish in time, forcing termination")
            self._worker.terminate()
            self._worker.wait(5000)

        self._worker = None
        self.processing_cancelled.emit()

    def _on_progress(self, current: int, total: int, filename: str):
        self.processing_progress.emit(current, total, filename)

    def _on_finished(self, success: list, errors: list, output_dir: str):
        worker = self._worker
        if worker:
            try:
                worker.finished.disconnect(self._on_finished)
            except (TypeError, RuntimeError):
                pass
            try:
                worker.progress.disconnect(self._on_progress)
            except (TypeError, RuntimeError):
                pass
        self._worker = None
        self.processing_finished.emit(success, errors, output_dir)
