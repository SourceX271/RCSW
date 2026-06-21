from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock

_logger_initialized = False
_init_lock = Lock()
_file_handler: RotatingFileHandler | None = None
_console_handler: logging.StreamHandler | None = None


def _get_log_dir() -> Path:
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        base = Path(appdata) / "RCSW"
    else:
        base = Path.home() / ".rcsw"
    return base / "logs"


def get_log_path() -> Path:
    return _get_log_dir() / "rcsw.log"


def _init() -> None:
    global _logger_initialized, _file_handler, _console_handler
    with _init_lock:
        if _logger_initialized:
            return

        log_dir = _get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        file_fmt = logging.Formatter(
            fmt="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        _file_handler = RotatingFileHandler(
            log_dir / "rcsw.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        _file_handler.setFormatter(file_fmt)
        _file_handler.setLevel(logging.DEBUG)

        console_fmt = logging.Formatter(
            fmt="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        _console_handler = logging.StreamHandler(sys.stderr)
        _console_handler.setFormatter(console_fmt)
        _console_handler.setLevel(logging.CRITICAL)

        root = logging.getLogger("rcsw")
        root.setLevel(logging.DEBUG)
        root.addHandler(_file_handler)
        root.addHandler(_console_handler)
        root.propagate = False

        _logger_initialized = True


def get_logger(name: str) -> logging.Logger:
    _init()
    return logging.getLogger(f"rcsw.{name}")


def set_console_enabled(enabled: bool):
    """控制终端日志输出。文件日志始终启用。"""
    _init()
    if _console_handler:
        _console_handler.setLevel(logging.DEBUG if enabled else logging.CRITICAL)


def is_console_enabled() -> bool:
    _init()
    if _console_handler:
        return _console_handler.level < logging.CRITICAL
    return False
