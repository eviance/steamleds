# Steam Machine (Valve "Fremont") front-LED register map

This documents how SteamOS drives the 17 front-panel RGB LEDs, reverse-engineered
from a retail unit, so the behaviour can be reproduced on Windows.

## Hardware / software identification

| | |
|---|---|
| Machine | Valve **Fremont** (`DMI: Valve Fremont`, BIOS `F7F0106`) |
| OS driver | kernel module **`leds_valve`** (`drivers/leds/rgb/leds-valve.c`, Robert Beckett / Collabora, GPL, in-tree in the neptune-616 kernel) |
| Bind method | platform driver matched by **DMI** (`dmi*:svn*Valve*:pn*Fremont*`, also `svn*OEM*:pn*F7F*`) |
| sysfs | `/sys/class/leds/valve-leds[0..16]` — 17 multicolor LEDs |
| Transport | **x86 I/O ports** in the Embedded-Controller region — *not* USB, *not* WMI |

The LEDs are exposed by the kernel as multicolor LED-class devices with
`multi_index = red green blue`, plus effect attributes (`effect`, `breath_level`,
`breath_offset`, `color_shift`, `patrol_num`, `delay`, `brightness_scale`, `*_startup`).

## I/O-port regions (`/proc/ioports`, as root)

```
0x0062        : EC data      (standard ACPI EC — unrelated to LEDs)
0x0066        : EC cmd
0x006c        : valve-leds   (single byte; observed 0x08, purpose unknown)
0x0de8-0x0e7a : valve-leds   (register block, base 0x0DE8, 147 bytes)
```

Everything below is expressed as **offset from base `0x0DE8`**; the absolute port
is `0x0DE8 + offset`.

## Register layout

The panel holds **two parallel 17×(R,G,B) blocks**:

| Offset | Absolute | Size | Meaning |
|---|---|---|---|
| `0x01`–`0x03` | `0x0DE9` | 3 | **startup color** (R,G,B) — persists across reboot |
| `0x04` | `0x0DEC` | 1 | **startup brightness** |
| `0x1B`–`0x4D` | `0x0E03` | 17×3 | **Block A** — *scaled* values = raw × `brightness_scale` / 255 (the driven PWM duty) |
| `0x51`–`0x83` | `0x0E39` | 17×3 | **Block B** — *raw* target color you set (0..255 per channel) |
| `0x84` | `0x0E6C` | 1 | **effect** index |
| `0x85` | `0x0E6D` | 1 | effect (mirror of 0x84) |
| `0x86` | `0x0E6E` | 1 | `delay` (animation speed, valid 0..20) |
| `0x87` | `0x0E6F` | 1 | `breath_offset` |
| `0x88` | `0x0E70` | 1 | `breath_level` |
| `0x89` | `0x0E71` | 1 | `patrol_num` |
| `0x8D` | `0x0E75` | 1 | `color_shift` |
| `0x91` | `0x0E79` | 1 | `brightness_scale` (BIOS/factory default `0x37` = 55) |

Within a block, LED *i* occupies 3 consecutive bytes (stride 3):
`R = base + block + 3*i`, `G = …+1`, `B = …+2`.

### Effects (`effect` register values)

```
0 patrol   1 breath   2 factory   3 normal
4 off      5 rainbow  6 demo      7 manual
```

`manual` (7) is the mode in which the per-LED colors in Block B are shown directly.

### The two blocks / brightness scaling

Block B is the raw color you request. Block A is what the EC actually drives:

```
BlockA[channel] = BlockB[channel] * brightness_scale / 255
```

Example (measured): with `brightness_scale = 55`, setting a LED to `170,0,255`
stored `AA 00 FF` in Block B and `23 00 35` (= 35,0,53) in Block A. Writing both
blocks — exactly what the kernel driver does — reproduces SteamOS behaviour.
Raising `brightness_scale` toward 255 makes the panel brighter (Block A → raw).

> The factory value is 55 (~21% duty). Going much higher is untested for
> thermal/current limits — raise it gradually.

## How it was mapped

1. `leds_valve` uses a `regmap` over an I/O-port region and logs writes as
   `valve-leds <fn>(): 0x%03x=0x%x`; strings in the `.ko` also expose hidden
   `test_reg_read` / `test_reg_write` / `test_raw_write` interfaces.
2. Real port base read from `/proc/ioports` as root.
3. A **gradient** was set through the official sysfs (`LED i → R=0x10+i, G=0x30+i,
   B=0x50+i`) and the whole `0x0DE8` window was dumped via `/dev/port`; the
   ascending pattern revealed Block B (raw), Block A (scaled), and the stride.
4. Direct `/dev/port` writes (bypassing the driver) were confirmed to change the
   physical LEDs — proving the same writes work from any ring0 context, including
   Windows. See [`tools/linux_reference.py`](../tools/linux_reference.py).

## Reproducing on Windows

User-mode Windows can't run `IN`/`OUT`, so a signed ring0 helper is used
(`inpoutx64.dll` or `WinRing0x64.dll`) to poke the same ports. The app **must run
on the Steam Machine itself booted into Windows** — the ports are decoded by that
machine's EC, not by the OS. See the top-level `README.md`.
