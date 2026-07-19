# SteamLEDs v1.1 — first public release 🎉

Control the **Valve Steam Machine ("Fremont")** front RGB lighting on **Windows** —
reverse-engineered from SteamOS and rebuilt as a modern tray app.

## 📥 Download
**`SteamLEDs-v1.1-win-x64.zip`** — unzip **on the Steam Machine booted into Windows**,
run `SteamLEDs.exe` (accept the admin prompt). The ring0 driver (`inpoutx64.dll`) is
included. On any other PC it opens in preview mode.

## ✨ Highlights
- 🎨 Per-LED color for all 17 LEDs + one-click **default blue**
- ✨ Hardware effects (breathe / rainbow / patrol) with live parameters
- 🏁 **Flag stadium wave** — national flags sweeping across, with direction & mirror
- 🛠️ **Animation builder** — Pattern × Motion, save your own presets
- 🌡️ **System monitor** — live temperatures + fan RPM from the EC
- 🌀 **Fan boost** — *up-only* by design (adds cooling, never less) + Auto
- 🌍 **7 languages** — EN · PL · DE · FR · ES · 中文 · 日本語
- 🪟 Flat design, optional Windows 11 glass, tray + start-with-Windows

## ⚠️ Notes
- Must run **on the Fremont under Windows** (LED ports are hardware-decoded).
- Fan control is **experimental** and opt-in; validate on your unit.
- Not affiliated with Valve. MIT licensed.

## ☕ Support
If it helps you: **https://ko-fi.com/eviance**

**Full reverse-engineering write-up:** `docs/REGISTER_MAP.md`.
