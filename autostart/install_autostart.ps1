# Add SteamLEDs to autostart via a Scheduled Task that runs at logon with highest
# privileges (starts elevated into the tray, no UAC prompt each login).
# Run this ONCE as Administrator from the folder that contains SteamLEDs.exe.
$exe = Join-Path $PSScriptRoot "..\SteamLEDs.exe"
if (-not (Test-Path $exe)) { $exe = Join-Path (Get-Location) "SteamLEDs.exe" }
$exe = (Resolve-Path $exe).Path

schtasks /Create /TN "SteamLEDs" /TR "`"$exe`" --tray" /SC ONLOGON /RL HIGHEST /F
if ($LASTEXITCODE -eq 0) {
    Write-Host "Autostart enabled (Scheduled Task 'SteamLEDs')." -ForegroundColor Green
} else {
    Write-Host "Failed - run this script as Administrator." -ForegroundColor Red
}
