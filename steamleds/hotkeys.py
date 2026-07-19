"""
Global (system-wide) hotkeys on Windows via Win32 RegisterHotKey — work even when
the app is minimized to the tray, and use Ctrl+Alt combos that Windows doesn't use.

No dependencies. Each binding is (modifiers, vk, callback); callbacks fire on a
background thread, so they should marshal back to the UI thread themselves.
"""
from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

# virtual-key codes for letters = ASCII of uppercase
VK = {c: ord(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"}


class HotkeyManager:
    def __init__(self, bindings: list[tuple[int, int, callable]]):
        self.bindings = bindings
        self._thread: threading.Thread | None = None
        self._tid = 0

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        u32 = ctypes.windll.user32
        self._tid = ctypes.windll.kernel32.GetCurrentThreadId()
        cbs = {}
        for i, (mods, vk, cb) in enumerate(self.bindings, start=1):
            if u32.RegisterHotKey(None, i, mods | MOD_NOREPEAT, vk):
                cbs[i] = cb
        msg = wintypes.MSG()
        while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY:
                cb = cbs.get(msg.wParam)
                if cb:
                    try:
                        cb()
                    except Exception:
                        pass
            u32.TranslateMessage(ctypes.byref(msg))
            u32.DispatchMessageW(ctypes.byref(msg))
        for i in cbs:
            u32.UnregisterHotKey(None, i)

    def stop(self) -> None:
        if self._tid:
            ctypes.windll.user32.PostThreadMessageW(self._tid, WM_QUIT, 0, 0)
