# Building the Windows `.exe`

The GUI is packaged with **PyInstaller** into a windowed, self-elevating app.

## Prerequisites
- Python 3.10+ and `pip install pyinstaller`
- Build on x64 (the Steam Machine / Fremont is AMD x64)

## Build
```powershell
cd steamleds
python -m PyInstaller --noconfirm --clean --onedir --windowed `
    --name SteamLEDs --uac-admin SteamLEDs.py
```
Result: `dist\SteamLEDs\` containing `SteamLEDs.exe` + an `_internal\` folder.

- `--windowed`  — no console window (GUI app)
- `--onedir`    — folder layout (fast start; easy to drop the DLL beside the exe)
- `--uac-admin` — embeds a manifest so the app requests Administrator on launch
  (required: the ring0 port-I/O driver needs elevation)

A helper is provided: run `build_exe.ps1`.

## Runtime dependency — `inpoutx64.dll`

The exe controls the LEDs through a signed ring0 helper that is **not bundled**
(it ships its own kernel driver and must be obtained by the user):

1. Download **InpOut** from https://www.highrez.co.uk/downloads/inpout32/
2. Copy **`inpoutx64.dll`** into `dist\SteamLEDs\`, right next to `SteamLEDs.exe`.
   (Alternatively use WinRing0: put `WinRing0x64.dll` + `WinRing0x64.sys` there.)

## Running

- Must run **on the Steam Machine booted into Windows** — the LED ports are decoded
  by that machine's Embedded Controller, not by the OS.
- Double-click `SteamLEDs.exe` → accept the UAC prompt.
- Without the DLL (or on any other PC) the app offers a **PREVIEW mode** so you can
  see the UI, but it won't touch hardware.

## Distributing
Zip the whole `dist\SteamLEDs\` folder (after adding `inpoutx64.dll`) and share that.
The `build\`, `dist\` folders and `*.spec` are git-ignored — they are build output.
