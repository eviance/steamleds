"""
Windows 11 window effects via DWM (ctypes, no dependencies):
dark title bar, rounded corners, and a Mica/Acrylic system backdrop.

All best-effort: silently no-ops on non-Windows or older builds.
"""
from __future__ import annotations

import ctypes
import sys

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_SYSTEMBACKDROP_TYPE = 38

_BACKDROPS = {"none": 1, "mica": 2, "acrylic": 3, "tabbed": 4}


def _hwnd(window) -> int:
    window.update_idletasks()
    # Tk wraps the real top-level; its parent is the actual window handle.
    return ctypes.windll.user32.GetParent(window.winfo_id())


def _set(hwnd: int, attr: int, value: int) -> None:
    v = ctypes.c_int(value)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))


def apply_effects(window, dark: bool = True, rounded: bool = True,
                  backdrop: str = "mica") -> bool:
    """Apply dark/rounded/backdrop to a Tk window. Returns True if it ran."""
    if sys.platform != "win32":
        return False
    try:
        hwnd = _hwnd(window)
        if dark:
            _set(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 1)
        if rounded:
            _set(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, 2)  # 2 = round
        if backdrop in _BACKDROPS:
            _set(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, _BACKDROPS[backdrop])
        return True
    except Exception:
        return False
