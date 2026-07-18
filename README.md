# steamleds

Control the **Valve Steam Machine ("Fremont")** front RGB LEDs from **Windows**.

SteamOS drives the 17 front-panel LEDs with its in-kernel `leds_valve` driver.
This project reproduces that control on Windows by writing the same Embedded-Controller
I/O-port registers through a ring0 helper — so you get per-LED color, brightness,
and the firmware effects without SteamOS.

> **Status:** the register map and the raw-port control path are **verified on the
> real hardware from SteamOS** (see [`docs/REGISTER_MAP.md`](docs/REGISTER_MAP.md)).
> The Windows port-I/O layer uses the standard `inpoutx64` / `WinRing0` drivers but
> still needs testing on a Fremont booted into Windows — see [Testing](#testing).
> Reports welcome!

## Features

- 🎨 Set all 17 LEDs individually (per-LED RGB)
- 🌈 One-shot presets: rainbow, solid color, off
- ✨ Select firmware effects: `breath`, `rainbow`, `patrol` (KITT), `demo`, …
- 🔆 Global brightness control (can go brighter than the factory default)
- 🖥️ Tkinter GUI **and** a scriptable CLI
- 🧩 No third-party Python packages (uses the standard library)

## How it works

The panel lives at x86 I/O ports `0x0DE8–0x0E7A` in the EC region. User-mode
Windows can't run `IN`/`OUT`, so — exactly like OpenRGB/HWiNFO — we call a signed
kernel helper:

- **inpoutx64** — https://www.highrez.co.uk/downloads/inpout32/ (default)
- **WinRing0** — `WinRing0x64.dll` + `.sys` (the one OpenRGB ships)

Put the chosen DLL (and its `.sys`) next to the app and run **as Administrator**.

⚠️ **This must run on the Steam Machine itself, booted into Windows.** The ports
are decoded by that machine's Embedded Controller, not by the OS; running it on any
other PC does nothing (or pokes unrelated ports).

## Install

```powershell
git clone https://github.com/<you>/steamleds
cd steamleds
# optional: pip install -e .   (adds a `steamleds` command)
```

Requires Python 3.10+ on Windows. Download `inpoutx64.dll` (and let it install its
driver on first run) or grab `WinRing0x64.dll`/`.sys`, and place it in the repo root.

## Usage (CLI)

Run an **elevated** terminal (Administrator):

```powershell
python -m steamleds rainbow
python -m steamleds solid "#ff00ff"
python -m steamleds led 0 "#00ff88"
python -m steamleds gradient "#ff0000" "#00ff00" "#0000ff"
python -m steamleds effect breath --delay 6
python -m steamleds off
python -m steamleds dump            # read back current colors
python -m steamleds gui             # graphical panel
```

Options: `--backend {auto,inpout,winring0,dummy}`, `--brightness 0..255`.
Use `--backend dummy` on any machine to try the code with no hardware/driver.

## Usage (library)

```python
from steamleds import LedController, open_backend, rainbow

ctrl = LedController(open_backend("inpout"))
ctrl.set_all(rainbow(17))
ctrl.set_led(0, (255, 0, 255))
ctrl.set_brightness_scale(120)
```

## Testing

- **Logic (any OS, no driver):** `python tests/test_controller.py` — exercises the
  register math against the in-memory `dummy` backend.
- **On SteamOS (Linux):** `sudo python3 tools/linux_reference.py rainbow` writes the
  ports directly via `/dev/port` — the reference the Windows path mirrors.
- **On Windows (the Fremont):** run any CLI command elevated and check the panel.
  Please open an issue with your results — especially safe `brightness_scale` limits.

## Safety

Poking EC I/O ports is low-level. This project only touches the `valve-leds` window
(`0x0DE8` block) documented in [`docs/REGISTER_MAP.md`](docs/REGISTER_MAP.md) and never
the ACPI EC command ports (`0x62`/`0x66`). The factory `brightness_scale` is 55
(~21% duty); raise it gradually — very high values are untested for thermal/current.

## Contributing

Issues and PRs welcome — more effects, a nicer GUI, a C#/C++ port, packaging, and
especially **hardware test reports**. See [`docs/REGISTER_MAP.md`](docs/REGISTER_MAP.md)
for the full reverse-engineering write-up.

## Credits & license

- Register map reverse-engineered from Valve's GPL `leds_valve` driver
  (`drivers/leds/rgb/leds-valve.c`, by Robert Beckett / Collabora) — thanks to them
  for shipping it open.
- This project: **MIT** (see [`LICENSE`](LICENSE)). Not affiliated with or endorsed
  by Valve.
