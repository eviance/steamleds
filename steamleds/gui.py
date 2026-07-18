"""Tkinter control panel for the Steam Machine front LEDs.

Zero third-party dependencies -- tkinter ships with CPython on Windows.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, messagebox, ttk

from .colors import RGB, rainbow, to_hex
from .controller import EFFECTS, LED_COUNT, LedController
from .portio import open_backend


class LedPanel(tk.Frame):
    def __init__(self, master: tk.Misc, ctrl: LedController):
        super().__init__(master, padx=12, pady=12)
        self.ctrl = ctrl
        self.colors: list[RGB] = [(0, 0, 0)] * LED_COUNT
        self.swatches: list[tk.Label] = []
        self._build()
        self.set_rainbow()  # start with something pretty

    # -- layout -------------------------------------------------------------
    def _build(self) -> None:
        tk.Label(self, text="Steam Machine LEDs", font=("Segoe UI", 15, "bold")).grid(
            row=0, column=0, sticky="w"
        )

        strip = tk.Frame(self)
        strip.grid(row=1, column=0, pady=(8, 12), sticky="w")
        for i in range(LED_COUNT):
            sw = tk.Label(strip, width=3, height=2, relief="raised", bd=1, bg="#000000",
                          cursor="hand2")
            sw.grid(row=0, column=i, padx=2)
            sw.bind("<Button-1>", lambda _e, idx=i: self._pick(idx))
            tk.Label(strip, text=str(i), font=("Segoe UI", 7)).grid(row=1, column=i)
            self.swatches.append(sw)

        # --- presets row ---
        controls = tk.Frame(self)
        controls.grid(row=2, column=0, sticky="we")
        ttk.Button(controls, text="Rainbow", command=self.set_rainbow).grid(row=0, column=0, padx=3)
        ttk.Button(controls, text="Solid…", command=self.set_solid_pick).grid(row=0, column=1, padx=3)
        ttk.Button(controls, text="Off", command=self.turn_off).grid(row=0, column=2, padx=3)
        ttk.Button(controls, text="Set as boot color…", command=self.set_boot).grid(
            row=0, column=3, padx=(16, 3))

        # --- effects ---
        fx = tk.LabelFrame(self, text="Firmware effect (runs on the panel itself)",
                           padx=8, pady=8)
        fx.grid(row=3, column=0, sticky="we", pady=(12, 0))
        ttk.Label(fx, text="Effect:").grid(row=0, column=0, sticky="e")
        self.effect_var = tk.StringVar(value="manual")
        eff = ttk.Combobox(fx, textvariable=self.effect_var, values=list(EFFECTS),
                           width=10, state="readonly")
        eff.grid(row=0, column=1, padx=(2, 12))
        eff.bind("<<ComboboxSelected>>", lambda _e: self._apply_effect())

        self.p_speed = self._param(fx, "Speed", 0, 20, 10, 0, 2, self._apply_params)
        self.p_breath = self._param(fx, "Breath", 0, 255, 32, 1, 0, self._apply_params)
        self.p_shift = self._param(fx, "Color shift", 0, 255, 5, 1, 2, self._apply_params)
        self.p_patrol = self._param(fx, "Patrol #", 1, 17, 3, 2, 0, self._apply_params)

        # --- global brightness ---
        bright = tk.Frame(self)
        bright.grid(row=4, column=0, sticky="we", pady=(12, 0))
        ttk.Label(bright, text="Brightness").pack(side="left")
        self.bright_var = tk.IntVar(value=self.ctrl.brightness_scale)
        ttk.Scale(bright, from_=1, to=255, variable=self.bright_var,
                  command=lambda _v: self._apply_brightness()).pack(
            side="left", fill="x", expand=True, padx=8)

        self.status = tk.Label(self, text="", anchor="w", fg="#666")
        self.status.grid(row=5, column=0, sticky="we", pady=(10, 0))

    def _param(self, parent, label, lo, hi, init, r, c, cb):
        ttk.Label(parent, text=label).grid(row=r + 1, column=c, sticky="e", pady=2)
        var = tk.IntVar(value=init)
        s = ttk.Scale(parent, from_=lo, to=hi, variable=var,
                      command=lambda _v, v=var: cb(), length=140)
        s.grid(row=r + 1, column=c + 1, sticky="we", padx=(2, 14), pady=2)
        return var

    # -- helpers ------------------------------------------------------------
    def _refresh_swatches(self) -> None:
        for sw, c in zip(self.swatches, self.colors):
            sw.configure(bg=to_hex(c))

    def _push(self) -> None:
        try:
            self.ctrl.set_all(self.colors)
            self.status.configure(text="Applied ✓")
        except Exception as exc:
            self.status.configure(text=f"error: {exc}")

    # -- actions ------------------------------------------------------------
    def _pick(self, index: int) -> None:
        rgb, _hexv = colorchooser.askcolor(color=to_hex(self.colors[index]),
                                           title=f"LED {index}")
        if rgb is None:
            return
        self.colors[index] = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
        self._refresh_swatches()
        self.effect_var.set("manual")
        self._push()

    def set_rainbow(self) -> None:
        self.colors = rainbow(LED_COUNT)
        self._refresh_swatches()
        self.effect_var.set("manual")
        self._push()

    def set_solid_pick(self) -> None:
        rgb, _ = colorchooser.askcolor(title="Solid color")
        if rgb is None:
            return
        self.colors = [(int(rgb[0]), int(rgb[1]), int(rgb[2]))] * LED_COUNT
        self._refresh_swatches()
        self.effect_var.set("manual")
        self._push()

    def turn_off(self) -> None:
        self.colors = [(0, 0, 0)] * LED_COUNT
        self._refresh_swatches()
        self._push()

    def set_boot(self) -> None:
        rgb, _ = colorchooser.askcolor(title="Boot / power-on color")
        if rgb is None:
            return
        try:
            self.ctrl.set_startup((int(rgb[0]), int(rgb[1]), int(rgb[2])),
                                  brightness=int(self.bright_var.get()))
            self.status.configure(text="Boot color saved ✓ (shows from power-on)")
        except Exception as exc:
            self.status.configure(text=f"error: {exc}")

    def _apply_effect(self) -> None:
        try:
            name = self.effect_var.get()
            self.ctrl.set_effect(name)
            if name == "manual":
                self.ctrl.set_all(self.colors)
            self.status.configure(text=f"Effect: {name}")
        except Exception as exc:
            self.status.configure(text=f"error: {exc}")

    def _apply_params(self) -> None:
        try:
            self.ctrl.set_effect_params(
                delay=int(self.p_speed.get()),
                breath_level=int(self.p_breath.get()),
                color_shift=int(self.p_shift.get()),
                patrol_num=int(self.p_patrol.get()),
            )
            self.status.configure(text="Effect params updated")
        except Exception as exc:
            self.status.configure(text=f"error: {exc}")

    def _apply_brightness(self) -> None:
        try:
            self.ctrl.set_brightness_scale(int(self.bright_var.get()))
            self.status.configure(text=f"Brightness scale: {self.ctrl.brightness_scale}")
        except Exception as exc:
            self.status.configure(text=f"error: {exc}")


def run_gui(backend: str = "auto") -> int:
    preview = False
    try:
        io = open_backend(backend)
    except Exception as exc:
        # No ring0 driver / not running on the Steam Machine: offer preview mode.
        root = tk.Tk()
        root.withdraw()
        from .portio import DummyBackend

        go = messagebox.askyesno(
            "steamleds",
            "Could not access the LED hardware:\n\n"
            f"{exc}\n\n"
            "This app must run on the Steam Machine (booted into Windows), as "
            "Administrator, with inpoutx64.dll next to it.\n\n"
            "Open in PREVIEW mode (no changes sent to hardware)?",
        )
        root.destroy()
        if not go:
            return 2
        io = DummyBackend()
        preview = True

    ctrl = LedController(io)
    root = tk.Tk()
    title = "steamleds — Steam Machine LED control"
    if preview:
        title += "  [PREVIEW — no hardware]"
    root.title(title)
    root.resizable(False, False)
    LedPanel(root, ctrl).pack()
    root.mainloop()
    io.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_gui())
