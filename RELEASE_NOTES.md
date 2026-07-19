# SteamLEDs v1.3 🎉

Control the **Valve Steam Machine ("Fremont")** front RGB lighting on **Windows** —
reverse-engineered from SteamOS and rebuilt as a modern tray app. **Verified on real
hardware.**

## 📥 Download
**`SteamLEDs-v1.3-win-x64.zip`** — a single **`SteamLEDs.exe`** plus the ring0 driver
(`inpoutx64.dll`). Unzip **on the Steam Machine booted into Windows**, run
`SteamLEDs.exe` (accept the admin prompt). On any other PC it opens in preview mode.

## ✨ Highlights
- 🎨 Per-LED color for all 17 LEDs + one-click **default blue**
- 🔄 **Reverse LED order on by default** — the app matches how the strip is mounted
- 🌈 **Flowing rainbow** — smooth, continuous flow (no stepping)
- ✨ Hardware effects (breathe / rainbow / patrol) with live parameters
- 🏁 Flag stadium waves — national flags with direction & mirror
- 🛠️ Animation builder — Pattern × Motion, save your own presets
- 🌡️ **System monitor** — live temperatures + fan RPM from the EC
- 🌀 Fan boost — *up-only* by design (adds cooling, never less) + Auto
- ⌨️ **Global hotkeys** — Ctrl+Alt+O toggle blue/off · Ctrl+Alt+R rainbow flow
  (work from the tray)
- 🌍 7 languages — EN · PL · DE · FR · ES · 中文 · 日本語
- 🪟 Flat design, optional Windows 11 glass, tray + start-with-Windows, single-file exe

## ⚠️ Notes
- Must run **on the Fremont under Windows** (LED ports are hardware-decoded).
- Fan control is experimental and opt-in; it can only raise the fan.

## ☕ Support
If it helps you: **https://ko-fi.com/eviance**

**Full reverse-engineering write-up:** `docs/REGISTER_MAP.md`.
