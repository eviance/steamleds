"""GUI entry point for PyInstaller (windowed .exe).

Launches the modern desktop app. `--tray` starts minimised to the system tray.
"""
import sys

from steamleds.app import run_app

if __name__ == "__main__":
    raise SystemExit(run_app(start_tray="--tray" in sys.argv))
