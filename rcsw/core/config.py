from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock


class Config:
    _instance: Config | None = None
    _lock = Lock()

    def __init__(self):
        self._data: dict = {}
        self._path = self._resolve_path()
        self._load()

    @staticmethod
    def _resolve_path() -> Path:
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            base = Path(appdata) / "RCSW"
        else:
            base = Path.home() / ".rcsw"
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
            self._data = {}

    def save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            tmp.replace(self._path)
        except OSError:
            pass

    def get(self, key: str, default: object = None) -> object:
        return self._data.get(key, default)

    def set(self, key: str, value: object) -> None:
        self._data[key] = value

    def get_all(self) -> dict:
        return dict(self._data)

    @property
    def path(self) -> Path:
        return self._path
