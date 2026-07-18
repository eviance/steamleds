#!/usr/bin/env python3
"""
Linux reference implementation — drives the Steam Machine front LEDs directly
through /dev/port on SteamOS. This is the exact mechanism the Windows app mirrors;
handy for verifying the register map on the device itself.

Run as root, e.g.:
    sudo python3 tools/linux_reference.py rainbow
    sudo python3 tools/linux_reference.py solid 255 0 255
    sudo python3 tools/linux_reference.py off

It does NOT go through the leds_valve driver — it writes the I/O ports raw.
"""
import colorsys
import os
import sys

BASE = 0x0DE8
LED_COUNT = 17
BLOCK_A = BASE + 0x1B   # scaled PWM
BLOCK_B = BASE + 0x51   # raw color
EFFECT = BASE + 0x84
SCALE = 55              # brightness_scale (factory default)


def _open():
    return os.open("/dev/port", os.O_RDWR)


def _w(fd, port, val):
    os.lseek(fd, port, os.SEEK_SET)
    os.write(fd, bytes([val & 0xFF]))


def set_led(fd, i, r, g, b):
    _w(fd, BLOCK_B + 3 * i, r); _w(fd, BLOCK_B + 3 * i + 1, g); _w(fd, BLOCK_B + 3 * i + 2, b)
    _w(fd, BLOCK_A + 3 * i, r * SCALE // 255)
    _w(fd, BLOCK_A + 3 * i + 1, g * SCALE // 255)
    _w(fd, BLOCK_A + 3 * i + 2, b * SCALE // 255)


def manual(fd):
    _w(fd, EFFECT, 7); _w(fd, EFFECT + 1, 7)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "rainbow"
    fd = _open()
    try:
        manual(fd)
        if cmd == "rainbow":
            for i in range(LED_COUNT):
                r, g, b = (round(x * 255) for x in colorsys.hsv_to_rgb(i / LED_COUNT, 1, 1))
                set_led(fd, i, r, g, b)
        elif cmd == "solid":
            r, g, b = (int(x) for x in argv[2:5])
            for i in range(LED_COUNT):
                set_led(fd, i, r, g, b)
        elif cmd == "off":
            for i in range(LED_COUNT):
                set_led(fd, i, 0, 0, 0)
        else:
            print(__doc__)
            return 1
    finally:
        os.close(fd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
