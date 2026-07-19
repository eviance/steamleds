<div align="center">

<img src="steamleds/assets/icon.png" width="120" alt="SteamLEDs icon" />

# SteamLEDs

**Control the Valve Steam Machine's front RGB lighting — on Windows.**

Colors · hardware effects · custom animations · national-flag stadium waves · live temps & fan RPM — in a clean, translucent app that lives in your tray.

![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-f5a623)
![Languages](https://img.shields.io/badge/i18n-7%20languages-3ac569)
[![Ko-fi](https://img.shields.io/badge/support-Ko--fi-ff5e5b)](https://ko-fi.com/eviance)

</div>

---

The Steam Machine ("Valve Fremont") has **17 front RGB LEDs**, but there's no tool for
them on Windows. **SteamLEDs fixes that.** I reverse-engineered how SteamOS's kernel
driver talks to the board's embedded controller, confirmed it on real hardware, and
rebuilt the whole thing as a modern Windows app.

> 📸 _Add a screenshot here → `docs/screenshot.png`_

## ✨ Features

| | |
|---|---|
| 🎨 **Per-LED color** | Paint all 17 LEDs individually, or one solid color |
| 🔵 **Standard default** | One click restores the main blue |
| ✨ **Hardware effects** | breathe · rainbow · patrol (KITT) · demo — with live params |
| 🏁 **Flag stadium wave** | National flags sweeping across like a crowd wave — pick direction/mirror |
| 🛠️ **Animation builder** | Compose Pattern × Motion, tune it, **save presets** |
| 🌡️ **System monitor** | Live temperatures + fan RPM, straight from the EC |
| 🌀 **Fan boost** | *Up-only* by design — can only add cooling, never less |
| 🌍 **7 languages** | English · Polski · Deutsch · Français · Español · 中文 · 日本語 |
| 🪟 **Modern UI** | Flat dark design, optional Windows 11 glass, tray + autostart |

## 🚀 Download & run

1. Grab the latest **`SteamLEDs-vX.Y-win-x64.zip`** from [Releases](../../releases).
2. Unzip **on the Steam Machine, booted into Windows** (the LED ports are decoded by
   that machine's hardware — it won't do anything on another PC).
3. Run **`SteamLEDs.exe`** → accept the Administrator prompt. That's it. 🎉

`inpoutx64.dll` (the signed ring0 helper) is bundled. Without hardware the app opens
in a harmless **preview** mode so you can explore the UI anywhere.

**Start with Windows:** Settings → *Start with Windows*, or run `autostart\install_autostart.ps1`.

## 🧑‍💻 Build from source

```powershell
pip install customtkinter pystray pillow
python -m steamleds --app          # run the desktop app
python -m steamleds rainbow        # or use the CLI
python build_exe.ps1               # package the .exe (needs pyinstaller)
```

## 🔬 How it works

The LEDs sit at x86 I/O ports `0x0DE8…` in the embedded-controller region; temps and
fan RPM at the ChromeOS-EC memory-mapped window `0x900`. SteamLEDs pokes the same ports
via a signed ring0 driver (`inpoutx64` / WinRing0) — exactly like OpenRGB does for other
gear. Full reverse-engineering write-up: **[`docs/REGISTER_MAP.md`](docs/REGISTER_MAP.md)**.

## 🛡️ Safety

Only the documented `valve-leds` and EC sensor windows are touched — never the ACPI EC
command ports. Fan control is **up-only** (it can raise cooling, never lower it) and hands
back to the EC's automatic control at any time.

## ☕ Support

SteamLEDs is free and open-source. If it's useful to you, a coffee keeps it going:
**[ko-fi.com/eviance](https://ko-fi.com/eviance)** — thank you! 🙏

## 📄 Credits & license

Register map reverse-engineered from Valve's GPL `leds_valve` driver (Robert Beckett /
Collabora — thanks for shipping it open). This project is **MIT** licensed and is **not**
affiliated with or endorsed by Valve.
