"""steamleds -- control the Valve Steam Machine ("Fremont") front LEDs from Windows.

See README.md and docs/REGISTER_MAP.md.
"""
from .colors import RGB, parse_color, rainbow, to_hex
from .controller import EFFECTS, LED_COUNT, LedController
from .portio import open_backend

__version__ = "0.1.0"

__all__ = [
    "LedController",
    "LED_COUNT",
    "EFFECTS",
    "open_backend",
    "RGB",
    "parse_color",
    "to_hex",
    "rainbow",
]
