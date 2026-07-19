"""
Animation engine: build custom LED animations from a Pattern x Motion, with
speed / direction / mirror, and save them as named presets (JSON).

An Animation is deterministic in time: `frame(t)` returns the 17 LED colors at
time `t` seconds, so the UI just calls it at its frame rate. This generalises the
flag wave into a reusable system the user can compose and save.
"""
from __future__ import annotations

import dataclasses
import json
import math
import os

from .colors import RGB, hsv
from .flags import FLAGS, render_static

PATTERNS = ("solid", "gradient", "rainbow", "flag", "police", "fire")
MOTIONS = ("static", "scroll", "wave", "pulse", "breathe", "blink", "comet", "twinkle")

_FIRE = [(0, 0, 0), (70, 0, 0), (160, 25, 0), (255, 90, 0), (255, 160, 25), (255, 230, 130)]


def _police(n, t, speed):
    """Police light bar: left half blue, right half red, brightness alternating."""
    half = max(1, n // 2)
    ph = int(t * 4.0 * max(0.1, speed)) % 2
    b_hi, b_lo = (0, 60, 255), (0, 10, 60)
    r_hi, r_lo = (255, 30, 30), (60, 5, 5)
    out = []
    for i in range(n):
        if i < half:
            out.append(b_hi if ph == 0 else b_lo)
        else:
            out.append(r_hi if ph == 1 else r_lo)
    return out


def _fire(n, t, speed):
    out = []
    for i in range(n):
        v = 0.5 + 0.5 * math.sin(t * 5 * speed + i * 1.3) * math.cos(t * 3.1 * speed + i * 0.7)
        v = 0.3 + 0.7 * max(0.0, min(1.0, v))   # lift the floor so it always reads as fire
        v = min(0.999, v)
        x = v * (len(_FIRE) - 1)
        k = int(x)
        out.append(_lerp(_FIRE[k], _FIRE[k + 1], x - k))
    return out


def _comet(base, n, t, speed, direction):
    head = (t * speed * 4.0 * (1 if direction >= 0 else -1)) % n
    color = base[0]
    out = []
    for i in range(n):
        d = (head - i) % n
        b = max(0.0, 1.0 - d / (n * 0.45))
        out.append(_scale(color, b * b))
    return out


def _twinkle(base, n, t, speed):
    out = []
    for i in range(n):
        ph = math.sin(t * 3 * speed + i * 12.9898) * 43758.5453
        frac = ph - math.floor(ph)
        b = 0.12 + 0.88 * max(0.0, math.sin((t * speed + frac * 6.283) * 2.0)) ** 4
        out.append(_scale(base[i], b))
    return out


def _scale(c: RGB, m: float) -> RGB:
    return (max(0, min(255, int(c[0] * m))),
            max(0, min(255, int(c[1] * m))),
            max(0, min(255, int(c[2] * m))))


def _lerp(a: RGB, b: RGB, t: float) -> RGB:
    return (round(a[0] + (b[0] - a[0]) * t),
            round(a[1] + (b[1] - a[1]) * t),
            round(a[2] + (b[2] - a[2]) * t))


def _gradient(stops: list[RGB], n: int) -> list[RGB]:
    if not stops:
        return [(0, 0, 0)] * n
    if len(stops) == 1:
        return [stops[0]] * n
    out: list[RGB] = []
    seg = len(stops) - 1
    for i in range(n):
        x = i / max(1, n - 1) * seg
        k = min(seg - 1, int(x))
        out.append(_lerp(stops[k], stops[k + 1], x - k))
    return out


@dataclasses.dataclass
class Animation:
    name: str = "New animation"
    pattern: str = "solid"
    colors: list[RGB] = dataclasses.field(default_factory=lambda: [(0, 150, 255)])
    flag: str = "Poland"
    motion: str = "static"
    speed: float = 1.0
    direction: int = 1
    mirror: bool = False

    # -- base layout (no motion) -------------------------------------------
    def base_colors(self, n: int) -> list[RGB]:
        if self.pattern == "solid":
            return [self.colors[0] if self.colors else (0, 0, 0)] * n
        if self.pattern == "gradient":
            return _gradient(self.colors, n)
        if self.pattern == "rainbow":
            return [hsv(i / n) for i in range(n)]
        if self.pattern == "flag":
            return render_static(FLAGS.get(self.flag, [(255, 255, 255)]), n)
        return [(0, 0, 0)] * n

    # -- animated frame -----------------------------------------------------
    def frame(self, t: float, n: int = 17) -> list[RGB]:
        sp = max(0.0, self.speed)
        if self.pattern == "police":
            out = _police(n, t, sp)
            return out[::-1] if self.mirror else out
        if self.pattern == "fire":
            out = _fire(n, t, sp)
            return out[::-1] if self.mirror else out

        base = self.base_colors(n)
        d = 1 if self.direction >= 0 else -1
        m = self.motion

        if m == "comet":
            out = _comet(base, n, t, sp, self.direction)
            return out[::-1] if self.mirror else out
        if m == "twinkle":
            out = _twinkle(base, n, t, sp)
            return out[::-1] if self.mirror else out

        if m == "scroll":
            # fractional shift + interpolation between neighbours -> smooth flow, no stepping
            shift = (sp * t * 1.2 * d) % n
            out = []
            for i in range(n):
                pos = (i - shift) % n
                k = int(pos)
                out.append(_lerp(base[k % n], base[(k + 1) % n], pos - k))
        elif m == "wave":
            pos = (sp * t * 6.0 * d) % n
            out = []
            for i in range(n):
                dist = (i - pos) % n
                dist = min(dist, n - dist)
                lvl = 0.15 + 0.85 * math.exp(-(dist * dist) / 8.0)
                out.append(_scale(base[i], lvl))
        elif m in ("pulse", "breathe"):
            phase = 0.5 - 0.5 * math.cos(2 * math.pi * sp * 0.5 * t)  # 0..1 smooth
            lvl = 0.1 + 0.9 * phase
            out = [_scale(c, lvl) for c in base]
        elif m == "blink":
            on = (int(sp * t * 2.0) % 2) == 0
            out = base if on else [(0, 0, 0)] * n
        else:  # static
            out = base

        return out[::-1] if self.mirror else out

    # -- serialisation ------------------------------------------------------
    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["colors"] = [list(c) for c in self.colors]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Animation":
        d = dict(d)
        d["colors"] = [tuple(c) for c in d.get("colors", [])]
        allowed = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in allowed})


# --- preset store ----------------------------------------------------------
def config_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "steamleds")
    os.makedirs(d, exist_ok=True)
    return d


def presets_path() -> str:
    return os.path.join(config_dir(), "animations.json")


def default_presets() -> list[Animation]:
    return [
        Animation("Polish flag wave", "flag", flag="Poland", motion="wave", speed=1.0),
        Animation("Rainbow scroll", "rainbow", motion="scroll", speed=1.0),
        Animation("Breathe blue", "solid", colors=[(0, 120, 255)], motion="breathe", speed=1.0),
        Animation("Sunset gradient", "gradient",
                  colors=[(255, 94, 0), (255, 0, 128), (80, 0, 200)], motion="scroll", speed=0.6),
        Animation("Police lights", "police", motion="static", speed=1.0),
        Animation("Fire", "fire", motion="static", speed=1.0),
        Animation("Comet", "solid", colors=[(0, 200, 255)], motion="comet", speed=1.0),
        Animation("Twinkle stars", "gradient",
                  colors=[(0, 40, 120), (120, 120, 255)], motion="twinkle", speed=1.0),
    ]


def load_presets() -> list[Animation]:
    path = presets_path()
    if not os.path.exists(path):
        save_presets(default_presets())
        return default_presets()
    try:
        with open(path, encoding="utf-8") as fh:
            saved = [Animation.from_dict(d) for d in json.load(fh)]
    except Exception:
        return default_presets()
    # add any newly-shipped default presets the user's file doesn't have yet
    names = {p.name for p in saved}
    for d in default_presets():
        if d.name not in names:
            saved.append(d)
    return saved


def save_presets(presets: list[Animation]) -> None:
    with open(presets_path(), "w", encoding="utf-8") as fh:
        json.dump([a.to_dict() for a in presets], fh, indent=2)
