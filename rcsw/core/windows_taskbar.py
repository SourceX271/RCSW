from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Any


class TaskbarProgress:
    """Windows 任务栏进度条，通过 ITaskbarList3 COM 接口实现。
    非 Windows 平台静默忽略。
    """

    TBPF_NOPROGRESS = 0
    TBPF_INDETERMINATE = 1
    TBPF_NORMAL = 2
    TBPF_ERROR = 4
    TBPF_PAUSED = 8

    def __init__(self, hwnd: int):
        self._hwnd = hwnd
        self._itaskbar: Any = None
        self._init()

    def _init(self):
        try:
            clsid = ctypes.create_string_buffer(
                b"\x56\xFD\xF3\x44\x1E\x1D\x4A\x40\xAA\x79\x97\x1E\xFE\xC0\xC1\x8A"
            )
            iid = ctypes.create_string_buffer(
                b"\xEA\x1A\xF2\x89\x30\xF1\x2A\x45\xA4\xDE\x87\xB9\x3E\x9B\x8E\xC6"
            )
            self._itaskbar = ctypes.windll.shell32.CoCreateInstance
        except Exception:
            self._itaskbar = None

    def _call(self, method_index: int, *args):
        if self._itaskbar is None:
            return
        try:
            import comtypes.client
            from comtypes import CLSCTX_INPROC_SERVER
            clsid_str = "{56FDF344-FD6D-11D0-958A-006097C9A090}"
            iid_str = "{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}"
            if not hasattr(self, '_com_obj'):
                self._com_obj = comtypes.client.CreateObject(clsid_str, clsctx=CLSCTX_INPROC_SERVER)
                self._com_obj = self._com_obj.QueryInterface(comtypes.GUID(iid_str))
            method = getattr(self._com_obj, [
                None, "HrInit", None, "SetProgressState", "SetProgressValue"
            ][method_index])
            if method:
                method(*args)
        except Exception:
            pass

    def set_state(self, state: int):
        self._call(3, self._hwnd, state)

    def set_value(self, completed: int, total: int = 100):
        self._call(4, self._hwnd, completed, total)

    def set_indeterminate(self):
        self.set_state(self.TBPF_INDETERMINATE)

    def set_normal(self):
        self.set_state(self.TBPF_NORMAL)

    def hide(self):
        self.set_state(self.TBPF_NOPROGRESS)
