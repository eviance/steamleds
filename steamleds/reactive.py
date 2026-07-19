"""
Reactive lighting sources (no third-party deps):
- cpu_percent(): system CPU load via GetSystemTimes
- load_colors(): CPU load as a green->red bar across the strip
- temp_color(): a colour from a temperature (blue = cool, red = hot)
- screen_colors(): ambient colours sampled across the screen (Ambilight-style)
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt

from .colors import RGB, hsv

_prev = {"idle": 0, "kern": 0, "user": 0, "last": 0.0}


def _times():
    idle, kern, user = wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
    ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user))

    def v(f):
        return (f.dwHighDateTime << 32) | f.dwLowDateTime

    return v(idle), v(kern), v(user)


def cpu_percent() -> float:
    idle, kern, user = _times()
    di = idle - _prev["idle"]
    total = (kern - _prev["kern"]) + (user - _prev["user"])   # kernel already includes idle
    _prev.update(idle=idle, kern=kern, user=user)
    if total <= 0:
        return _prev["last"]
    pct = max(0.0, min(100.0, 100.0 * (total - di) / total))
    _prev["last"] = pct
    return pct


def load_colors(pct: float, n: int) -> list[RGB]:
    lit = round(pct / 100.0 * n)
    out: list[RGB] = []
    for i in range(n):
        if i < lit:
            out.append(hsv(0.33 * (1.0 - i / max(1, n - 1))))   # green -> red
        else:
            out.append((0, 0, 0))
    return out


def temp_color(temp_c: float, lo: float = 30.0, hi: float = 85.0) -> RGB:
    t = max(0.0, min(1.0, (temp_c - lo) / (hi - lo)))
    return hsv(0.66 * (1.0 - t))   # blue (cool) -> red (hot)


def screen_colors(n: int) -> list[RGB]:
    from PIL import ImageGrab

    img = ImageGrab.grab().resize((n, 1)).convert("RGB")
    return [img.getpixel((i, 0)) for i in range(n)]


def mouse_colors(n: int, color: RGB = (0, 180, 255)) -> list[RGB]:
    """A glowing dot that follows the horizontal mouse position across the strip."""
    pt = wt.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    sw = ctypes.windll.user32.GetSystemMetrics(0) or 1920
    frac = max(0.0, min(1.0, pt.x / max(1, sw)))
    pos = frac * (n - 1)
    out: list[RGB] = []
    for i in range(n):
        b = max(0.0, 1.0 - abs(i - pos) / 2.0)   # ~2-LED glow radius
        out.append((int(color[0] * b), int(color[1] * b), int(color[2] * b)))
    return out
