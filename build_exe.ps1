# Build the SteamLEDs GUI .exe (windowed, self-elevating, folder layout).
# Usage:  powershell -ExecutionPolicy Bypass -File build_exe.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m pip show pyinstaller *> $null
if (-not $?) { python -m pip install pyinstaller }

python -m PyInstaller --noconfirm --clean --onefile --windowed --name SteamLEDs --uac-admin `
    --icon "steamleds/assets/icon.ico" --add-data "steamleds/assets;steamleds/assets" `
    --collect-all customtkinter --collect-all pystray --collect-submodules PIL SteamLEDs.py

Write-Host ""
Write-Host "Done -> dist\SteamLEDs\SteamLEDs.exe" -ForegroundColor Green
Write-Host "Remember: put inpoutx64.dll next to SteamLEDs.exe before running on the machine." -ForegroundColor Yellow
