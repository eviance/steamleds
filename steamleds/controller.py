"""
LedController -- Steam Machine ("Valve Fremont") front-panel LED control.

Register map (reverse-engineered on SteamOS from the `leds_valve` driver, see
docs/REGISTER_MAP.md). All values are single bytes in x86 I/O-port space; the
absolute port of a register is BASE + offset.

The panel keeps two parallel 17x(R,G,B) blocks:
  * BLOCK_B (raw)    -- the target color you set (0..255 per channel)
  * BLOCK_A (scaled) -- what the EC actually drives = raw * brightness_scale / 255

We write both, exactly like the kernel driver does, so behavior matches SteamOS.
"""
from __future__ import annotations

from .colors import RGB, rainbow
from .portio import PortIO

# --- verified hardware constants -------------------------------------------
BASE = 0x0DE8
LED_COUNT = 17

# offsets from BASE
OFF_STARTUP_COLOR = 0x01      # persistent boot color (R,G,B)
OFF_STARTUP_BRIGHT = 0x04     # persistent boot brightness
OFF_BLOCK_A = 0x1B            # scaled PWM block: LED_COUNT * (R,G,B)
OFF_BLOCK_B = 0x51            # raw color block:  LED_COUNT * (R,G,B)
OFF_EFFECT = 0x84            # effect index
OFF_EFFECT_MIRROR = 0x85     # observed to mirror OFF_EFFECT
OFF_DELAY = 0x86            # animation speed, valid 0..20
OFF_BREATH_OFFSET = 0x87
OFF_BREATH_LEVEL = 0x88
OFF_PATROL_NUM = 0x89
OFF_COLOR_SHIFT = 0x8D
OFF_BRIGHTNESS_SCALE = 0x91   # global brightness scale (BIOS default ~0x37 = 55)

CMD_PORT = 0x6C               # single byte next to the block; purpose unknown (seen 0x08)

EFFECTS = {
    "patrol": 0,
    "breath": 1,
    "factory": 2,
    "normal": 3,
    "off": 4,
    "rainbow": 5,
    "demo": 6,
    "manual": 7,
}
EFFECT_NAMES = {v: k for k, v in EFFECTS.items()}

DEFAULT_BRIGHTNESS_SCALE = 0x37  # 55, matches the factory/BIOS setting


class LedController:
    def __init__(self, io: PortIO, brightness_scale: int = DEFAULT_BRIGHTNESS_SCALE,
                 reverse: bool = False):
        self.io = io
        self._scale = max(0, min(255, brightness_scale))
        # flip logical->physical LED order to match how the strip is mounted
        self.reverse = reverse
        # remember the last raw colors so brightness changes can re-apply them
        self._raw: list[RGB] = [(0, 0, 0)] * LED_COUNT
        # track effect mode so we don't rewrite the effect register every frame
        self._is_manual = False

    def _phys(self, index: int) -> int:
        return (LED_COUNT - 1 - index) if self.reverse else index

    # -- low level ----------------------------------------------------------
    def _write_rgb(self, block_off: int, index: int, color: RGB) -> None:
        p = BASE + block_off + 3 * index
        r, g, b = color
        self.io.write(p, r)
        self.io.write(p + 1, g)
        self.io.write(p + 2, b)

    def _read_rgb(self, block_off: int, index: int) -> RGB:
        p = BASE + block_off + 3 * index
        return (self.io.read(p), self.io.read(p + 1), self.io.read(p + 2))

    def _scaled(self, color: RGB) -> RGB:
        s = self._scale
        return (color[0] * s // 255, color[1] * s // 255, color[2] * s // 255)

    # -- public API ---------------------------------------------------------
    @property
    def brightness_scale(self) -> int:
        return self._scale

    def ensure_manual(self) -> None:
        """Put the panel in manual mode -- but only write the effect register when
        the mode actually changes, so animations don't re-trigger it every frame
        (which makes the EC blink/reset individual LEDs)."""
        if self._is_manual:
            return
        self.io.write(BASE + OFF_EFFECT, EFFECTS["manual"])
        self.io.write(BASE + OFF_EFFECT_MIRROR, EFFECTS["manual"])
        self._is_manual = True

    def set_led(self, index: int, color: RGB) -> None:
        if not 0 <= index < LED_COUNT:
            raise IndexError(f"LED index {index} out of range 0..{LED_COUNT - 1}")
        self._raw[index] = color
        phys = self._phys(index)
        self._write_rgb(OFF_BLOCK_B, phys, color)          # raw target
        self._write_rgb(OFF_BLOCK_A, phys, self._scaled(color))  # driven PWM

    def set_all(self, colors: list[RGB]) -> None:
        if len(colors) != LED_COUNT:
            raise ValueError(f"expected {LED_COUNT} colors, got {len(colors)}")
        self.ensure_manual()
        for i, c in enumerate(colors):
            self.set_led(i, c)

    def set_solid(self, color: RGB) -> None:
        self.set_all([color] * LED_COUNT)

    def set_rainbow(self, offset: float = 0.0) -> None:
        self.set_all(rainbow(LED_COUNT, offset=offset))

    def off(self) -> None:
        """Blank all LEDs (manual black). Use set_effect('off') for the firmware mode."""
        self.set_solid((0, 0, 0))

    def set_brightness_scale(self, scale: int, reapply: bool = True) -> None:
        self._scale = max(0, min(255, scale))
        self.io.write(BASE + OFF_BRIGHTNESS_SCALE, self._scale)
        if reapply:
            for i, c in enumerate(self._raw):
                self._write_rgb(OFF_BLOCK_A, self._phys(i), self._scaled(c))

    def set_effect(self, name: str) -> None:
        key = name.lower()
        if key not in EFFECTS:
            raise ValueError(f"Unknown effect {name!r}; choose from {list(EFFECTS)}")
        self.io.write(BASE + OFF_EFFECT, EFFECTS[key])
        self.io.write(BASE + OFF_EFFECT_MIRROR, EFFECTS[key])
        self._is_manual = (key == "manual")

    def set_effect_params(
        self,
        delay: int | None = None,
        breath_level: int | None = None,
        breath_offset: int | None = None,
        patrol_num: int | None = None,
        color_shift: int | None = None,
    ) -> None:
        if delay is not None:
            self.io.write(BASE + OFF_DELAY, max(0, min(20, delay)))
        if breath_level is not None:
            self.io.write(BASE + OFF_BREATH_LEVEL, breath_level)
        if breath_offset is not None:
            self.io.write(BASE + OFF_BREATH_OFFSET, breath_offset)
        if patrol_num is not None:
            self.io.write(BASE + OFF_PATROL_NUM, patrol_num)
        if color_shift is not None:
            self.io.write(BASE + OFF_COLOR_SHIFT, color_shift)

    def set_startup(self, color: RGB, brightness: int | None = None) -> None:
        """Persist a boot color/brightness -- the panel shows this from power-on,
        before login, and it survives reboots (written to the startup registers)."""
        self._write_rgb(OFF_STARTUP_COLOR, 0, color)
        if brightness is not None:
            self.io.write(BASE + OFF_STARTUP_BRIGHT, max(0, min(255, brightness)))

    def read_startup(self) -> tuple[RGB, int]:
        c = self._read_rgb(OFF_STARTUP_COLOR, 0)
        b = self.io.read(BASE + OFF_STARTUP_BRIGHT)
        return c, b

    def read_led(self, index: int) -> RGB:
        """Read back the raw (BLOCK_B) color of one LED."""
        return self._read_rgb(OFF_BLOCK_B, index)

    def read_all(self) -> list[RGB]:
        return [self.read_led(i) for i in range(LED_COUNT)]

    def dump_block(self) -> bytes:
        """Read the whole 0xDE8..0xE7A register window (for debugging)."""
        return bytes(self.io.read(BASE + off) for off in range(0x93))
