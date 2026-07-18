"""Small color helpers: hex parsing and HSV rainbows."""
from __future__ import annotations

import colorsys

RGB = tuple[int, int, int]


def parse_color(text: str) -> RGB:
    """Accept '#RRGGBB', 'RRGGBB', 'r,g,b' or 'r g b'."""
    s = text.strip().lstrip("#")
    if len(s) == 6 and all(c in "0123456789abcdefABCDEF" for c in s):
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    parts = s.replace(",", " ").split()
    if len(parts) == 3:
        r, g, b = (int(p) for p in parts)
        return (r & 0xFF, g & 0xFF, b & 0xFF)
    raise ValueError(f"Cannot parse color {text!r} (use #RRGGBB or 'r g b')")


def to_hex(color: RGB) -> str:
    r, g, b = color
    return f"#{r:02x}{g:02x}{b:02x}"


def hsv(h: float, s: float = 1.0, v: float = 1.0) -> RGB:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (round(r * 255), round(g * 255), round(b * 255))


def rainbow(count: int, offset: float = 0.0, saturation: float = 1.0, value: float = 1.0) -> list[RGB]:
    """Evenly spaced hues across `count` LEDs."""
    return [hsv(offset + i / count, saturation, value) for i in range(count)]
