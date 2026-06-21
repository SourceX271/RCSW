from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from threading import Lock

from .logger import get_logger

_log = get_logger("config")


class Config:
    _instance: Config | None = None
    _lock = Lock()
    _save_lock = Lock()

    def __init__(self):
        self._data: dict = {}
        self._path = self._resolve_path()
        self._load()

    @staticmethod
    def _resolve_path() -> Path:
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", "") or Path.home() / "AppData" / "Roaming") / "RCSW"
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support" / "RCSW"
        else:
            xdg = os.environ.get("XDG_CONFIG_HOME", "")
            if xdg:
                base = Path(xdg) / "rcsw"
            else:
                base = Path.home() / ".config" / "rcsw"
        base.mkdir(parents=True, exist_ok=True)
        return base / "rcsw_config.json"

    @classmethod
    def instance(cls) -> Config:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _load(self) -> None:
        try:
            if self._path.exists():
                with open(self._path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                self._data = {}
        except (json.JSONDecodeError, OSError):
            _log.warning("Failed to load config, using defaults")
            self._data = {}

    def save(self) -> bool:
        with self._save_lock:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self._path.with_suffix(".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, ensure_ascii=False, indent=2)
                tmp.replace(self._path)
                return True
            except OSError as e:
                _log.error("Failed to save config: %s", e)
                return False

    def get(self, key: str, default: object = None) -> object:
        return self._data.get(key, default)

    def set(self, key: str, value: object) -> None:
        with self._save_lock:
            self._data[key] = value

    def get_all(self) -> dict:
        return dict(self._data)

    def clear_all(self) -> None:
        self._data = {}
        self.save()

    @property
    def path(self) -> Path:
        return self._path
