# Remove SteamLEDs from autostart (delete the Scheduled Task).
schtasks /Delete /TN "SteamLEDs" /F
Write-Host "Autostart disabled." -ForegroundColor Yellow
