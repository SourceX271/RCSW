from __future__ import annotations

import logging
import sys
from threading import Lock

_logger_initialized = False
_init_lock = Lock()


def _init() -> None:
    global _logger_initialized
    with _init_lock:
        if _logger_initialized:
            return

        fmt = logging.Formatter(
            fmt="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(fmt)
        console.setLevel(logging.DEBUG)

        root = logging.getLogger("rcsw")
        root.setLevel(logging.DEBUG)
        root.addHandler(console)
        root.propagate = False

        _logger_initialized = True


def get_logger(name: str) -> logging.Logger:
    _init()
    return logging.getLogger(f"rcsw.{name}")
