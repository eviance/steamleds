"""
Read Steam Machine sensors (temperatures + fan RPM) from the ChromeOS-EC
memory-mapped region at I/O port 0x900 -- portable to Windows through the same
ring0 port backend used for the LEDs (inpoutx64 / WinRing0).

Verified on the Fremont EC:
  0x900 + 0x00 : temperature sensors, one byte each, value = degrees C directly
  0x900 + 0x10 : fan RPM, 16-bit little-endian per fan
  0x900 + 0x20 : ASCII "EC" id + version
"""
from __future__ import annotations

EC_MEMMAP = 0x900
OFF_TEMP = 0x00
OFF_FAN = 0x10
OFF_ID = 0x20

MAX_TEMPS = 8
MAX_FANS = 2

_TEMP_INVALID = (0x00, 0xFE, 0xFF)   # not present / error / not present


def _r8(io, off: int) -> int:
    return io.read(EC_MEMMAP + off) & 0xFF


def _r16(io, off: int) -> int:
    return _r8(io, off) | (_r8(io, off + 1) << 8)


def ec_present(io) -> bool:
    try:
        return _r8(io, OFF_ID) == ord("E") and _r8(io, OFF_ID + 1) == ord("C")
    except Exception:
        return False


def read_temps(io, n: int = MAX_TEMPS) -> list[int]:
    out: list[int] = []
    for i in range(n):
        v = _r8(io, OFF_TEMP + i)
        if v in _TEMP_INVALID:
            continue
        if 5 <= v <= 120:            # plausible °C
            out.append(v)
    return out


def read_fans(io, n: int = MAX_FANS) -> list[int]:
    out: list[int] = []
    for i in range(n):
        rpm = _r16(io, OFF_FAN + 2 * i)
        if rpm in (0xFFFF,):         # not present
            continue
        out.append(rpm)
    return out


def read_all(io) -> dict:
    if not ec_present(io):
        return {"present": False, "temps": [], "fans": []}
    return {"present": True, "temps": read_temps(io), "fans": read_fans(io)}
