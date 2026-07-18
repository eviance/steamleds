"""
Windows autostart via a Scheduled Task that runs at logon with highest
privileges -- so the app starts elevated (needed for the ring0 LED driver)
straight into the tray, WITHOUT a UAC prompt every login.

Creating a highest-privileges task itself requires elevation; the packaged app
runs elevated (its manifest requests admin), so the in-app toggle works.
"""
from __future__ import annotations

import os
import subprocess
import sys

TASK_NAME = "SteamLEDs"
_NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW


def launch_target() -> str:
    """The command the task should run (app minimised to tray)."""
    if getattr(sys, "frozen", False):          # PyInstaller exe
        return f'"{sys.executable}" --tray'
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pyw):
        pyw = sys.executable
    return f'"{pyw}" -m steamleds --app --tray'


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, creationflags=_NO_WINDOW)


def enable() -> None:
    r = _run(["schtasks", "/Create", "/TN", TASK_NAME, "/TR", launch_target(),
              "/SC", "ONLOGON", "/RL", "HIGHEST", "/F"])
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip() or "schtasks failed")


def disable() -> None:
    _run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"])


def is_enabled() -> bool:
    return _run(["schtasks", "/Query", "/TN", TASK_NAME]).returncode == 0
