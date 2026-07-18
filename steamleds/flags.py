"""
National-flag colors mapped onto the 17-LED front strip, with a stadium-wave
("Mexican wave") animation and a color-scroll ("waving flag") animation.

A flag is defined as ordered stripes (left -> right along the strip). Rendering
tiles those stripes across the LEDs; animations advance a phase each frame.
"""
from __future__ import annotations

import math

from .colors import RGB

# Ordered stripe colors, left -> right. Vertical-stripe flags map most cleanly to a
# 1-D strip; horizontal ones (e.g. Poland) are shown as left/right bands.
FLAGS: dict[str, list[RGB]] = {
    "Poland":       [(255, 255, 255), (220, 20, 60)],
    "Ukraine":      [(0, 87, 183), (255, 215, 0)],
    "France":       [(0, 35, 149), (255, 255, 255), (237, 28, 36)],
    "Germany":      [(0, 0, 0), (221, 0, 0), (255, 206, 0)],
    "Italy":        [(0, 140, 69), (255, 255, 255), (205, 33, 42)],
    "Netherlands":  [(174, 28, 40), (255, 255, 255), (33, 70, 139)],
    "Spain":        [(170, 21, 27), (241, 191, 0), (170, 21, 27)],
    "Sweden":       [(0, 106, 167), (254, 204, 41)],
    "Ireland":      [(22, 155, 98), (255, 255, 255), (255, 136, 62)],
    "Lithuania":    [(253, 185, 19), (0, 106, 68), (193, 39, 45)],
    "Belgium":      [(0, 0, 0), (255, 233, 54), (237, 41, 57)],
    "USA":          [(60, 59, 110), (255, 255, 255), (178, 34, 52)],
    "Japan":        [(255, 255, 255), (188, 0, 45), (255, 255, 255)],
}

MODES = ("Stadium wave", "Waving colors")


def flag_names() -> list[str]:
    return list(FLAGS)


def render_static(stripes: list[RGB], count: int) -> list[RGB]:
    n = len(stripes)
    return [stripes[min(n - 1, i * n // count)] for i in range(count)]


def _scale(color: RGB, m: float) -> RGB:
    return (int(color[0] * m), int(color[1] * m), int(color[2] * m))


def frame_stadium(stripes: list[RGB], count: int, pos: float,
                  sigma: float = 2.0, base: float = 0.18) -> list[RGB]:
    """Static flag bands with a bright pulse travelling along (wraps around)."""
    static = render_static(stripes, count)
    out: list[RGB] = []
    for i in range(count):
        d = (i - pos) % count
        d = min(d, count - d)                      # circular distance
        m = base + (1.0 - base) * math.exp(-(d * d) / (2 * sigma * sigma))
        out.append(_scale(static[i], m))
    return out


def frame_scroll(stripes: list[RGB], count: int, phase: float) -> list[RGB]:
    """Flag colors scroll across the strip (the flag 'waves')."""
    n = len(stripes)
    out: list[RGB] = []
    for i in range(count):
        t = ((i / count) + phase) % 1.0
        out.append(stripes[int(t * n) % n])
    return out


class FlagAnimator:
    """Stateful frame generator. Call next_frame() at your frame rate."""

    def __init__(self, name: str, count: int = 17, mode: str = "Stadium wave",
                 speed: float = 1.0):
        self.set_flag(name)
        self.count = count
        self.mode = mode
        self.speed = speed
        self._phase = 0.0   # 0..1 for scroll
        self._pos = 0.0     # 0..count for stadium pulse

    def set_flag(self, name: str) -> None:
        if name not in FLAGS:
            raise ValueError(f"unknown flag {name!r}")
        self.name = name
        self.stripes = FLAGS[name]

    def next_frame(self) -> list[RGB]:
        if self.mode == "Waving colors":
            self._phase = (self._phase + 0.02 * self.speed) % 1.0
            return frame_scroll(self.stripes, self.count, self._phase)
        # default: stadium wave
        self._pos = (self._pos + 0.35 * self.speed) % self.count
        return frame_stadium(self.stripes, self.count, self._pos)
