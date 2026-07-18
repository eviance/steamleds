"""
SteamLEDs desktop app -- modern dark-purple UI (customtkinter), tabs, system-tray
background running, and a custom-animation builder.

Runs the animation loop on the Tk main thread via after(); minimises to the tray
(pystray) so it keeps running by the clock with a right-click Quit.
"""
from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import colorchooser

import customtkinter as ctk

from . import autostart
from .anim import MOTIONS, PATTERNS, Animation, load_presets, save_presets
from .colors import RGB, to_hex
from .controller import EFFECTS, LED_COUNT, LedController
from .flags import MODES, flag_names
from .portio import DummyBackend, open_backend

# palette (inspired by the reference mockup)
BG = "#241d3d"
CARD = "#2e2650"
CARD2 = "#3a2f66"
ACCENT = "#f5a623"
ACCENT_HOVER = "#d98e12"
TEXT = "#ffffff"
MUTED = "#a89fc9"


def _tray_image():
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, 60, 60], radius=16, fill=(58, 47, 102, 255))
    for i in range(7):
        import colorsys
        r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(i / 7, 1, 1)]
        d.ellipse([12 + i * 6, 28, 16 + i * 6, 36], fill=(r, g, b, 255))
    return img


class SteamLedsApp(ctk.CTk):
    def __init__(self, backend: str = "auto", start_tray: bool = False):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("SteamLEDs")
        self.geometry("560x620")
        self.minsize(520, 600)
        self.configure(fg_color=BG)

        self.preview = False
        try:
            io = open_backend(backend)
        except Exception:
            io = DummyBackend()
            self.preview = True
        self.ctrl = LedController(io)

        self.colors: list[RGB] = [(0, 0, 0)] * LED_COUNT
        self.presets: list[Animation] = load_presets()
        self._anim: Animation | None = None
        self._anim_t0 = 0.0
        self._anim_job: str | None = None
        self._tray = None

        self._build_header()
        self._build_tabs()
        self._set_rainbow()

        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self._start_tray()
        if start_tray:
            self.after(200, self.hide_to_tray)

    # ================= header =================
    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(16, 6))
        ctk.CTkLabel(head, text="SteamLEDs", font=("Segoe UI", 24, "bold"),
                     text_color=TEXT).pack(side="left")
        self.status = ctk.CTkLabel(head, text="", text_color=MUTED, font=("Segoe UI", 12))
        self.status.pack(side="right", pady=(10, 0))
        if self.preview:
            self._status("PREVIEW — no hardware")
        else:
            self._status("ready")

    def _status(self, txt: str):
        self.status.configure(text=txt)

    # ================= tabs =================
    def _build_tabs(self):
        tabs = ctk.CTkTabview(self, fg_color=CARD, segmented_button_selected_color=ACCENT,
                              segmented_button_selected_hover_color=ACCENT_HOVER,
                              text_color=TEXT)
        tabs.pack(fill="both", expand=True, padx=18, pady=10)
        for name in ("Colors", "Effects", "Flags", "Animations", "Settings"):
            tabs.add(name)
        self._tab_colors(tabs.tab("Colors"))
        self._tab_effects(tabs.tab("Effects"))
        self._tab_flags(tabs.tab("Flags"))
        self._tab_anim(tabs.tab("Animations"))
        self._tab_settings(tabs.tab("Settings"))

    def _card(self, parent, title=None):
        c = ctk.CTkFrame(parent, fg_color=CARD2, corner_radius=16)
        c.pack(fill="x", padx=6, pady=8)
        if title:
            ctk.CTkLabel(c, text=title, text_color=MUTED,
                         font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
        return c

    # ---- Colors ----
    def _tab_colors(self, tab):
        card = self._card(tab, "Per-LED colors")
        strip = ctk.CTkFrame(card, fg_color="transparent")
        strip.pack(padx=12, pady=12)
        self.sw: list[ctk.CTkButton] = []
        for i in range(LED_COUNT):
            b = ctk.CTkButton(strip, text="", width=22, height=30, corner_radius=6,
                              fg_color="#000000", hover=False,
                              command=lambda idx=i: self._pick(idx))
            b.grid(row=0, column=i, padx=1)
            self.sw.append(b)

        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=(2, 6))
        for txt, cmd in (("Rainbow", self._set_rainbow), ("Solid…", self._set_solid),
                         ("Off", self._set_off), ("Boot color…", self._set_boot)):
            ctk.CTkButton(row, text=txt, command=cmd, fg_color=ACCENT, hover_color=ACCENT_HOVER,
                          text_color="#20183a", font=("Segoe UI", 12, "bold"),
                          width=96).pack(side="left", padx=4)

        b = self._card(tab, "Brightness")
        self.bright = ctk.CTkSlider(b, from_=1, to=255, command=self._on_bright)
        self.bright.set(self.ctrl.brightness_scale)
        self.bright.pack(fill="x", padx=14, pady=12)

    def _refresh_sw(self):
        for b, c in zip(self.sw, self.colors):
            b.configure(fg_color=to_hex(c))

    def _push(self):
        try:
            self.ctrl.set_all(self.colors)
            self._status("applied")
        except Exception as e:
            self._status(f"error: {e}")

    def _pick(self, i):
        self._stop_anim()
        rgb, _ = colorchooser.askcolor(color=to_hex(self.colors[i]), title=f"LED {i}")
        if rgb:
            self.colors[i] = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
            self._refresh_sw()
            self._push()

    def _set_rainbow(self):
        from .colors import rainbow
        self._stop_anim()
        self.colors = rainbow(LED_COUNT)
        self._refresh_sw()
        self._push()

    def _set_solid(self):
        rgb, _ = colorchooser.askcolor(title="Solid color")
        if rgb:
            self._stop_anim()
            self.colors = [(int(rgb[0]), int(rgb[1]), int(rgb[2]))] * LED_COUNT
            self._refresh_sw()
            self._push()

    def _set_off(self):
        self._stop_anim()
        self.colors = [(0, 0, 0)] * LED_COUNT
        self._refresh_sw()
        self._push()

    def _set_boot(self):
        rgb, _ = colorchooser.askcolor(title="Boot / power-on color")
        if rgb:
            try:
                self.ctrl.set_startup((int(rgb[0]), int(rgb[1]), int(rgb[2])),
                                      brightness=int(self.bright.get()))
                self._status("boot color saved")
            except Exception as e:
                self._status(f"error: {e}")

    def _on_bright(self, _v):
        try:
            self.ctrl.set_brightness_scale(int(self.bright.get()))
        except Exception as e:
            self._status(f"error: {e}")

    # ---- Effects ----
    def _tab_effects(self, tab):
        card = self._card(tab, "Firmware effect (runs on the panel)")
        self.effect = ctk.CTkOptionMenu(card, values=list(EFFECTS), command=self._on_effect,
                                        fg_color=ACCENT, button_color=ACCENT_HOVER,
                                        text_color="#20183a")
        self.effect.set("manual")
        self.effect.pack(anchor="w", padx=14, pady=10)
        self.fx = {}
        for key, lo, hi in (("delay (speed)", 0, 20), ("breath", 0, 255),
                            ("color shift", 0, 255), ("patrol #", 1, 17)):
            f = ctk.CTkFrame(card, fg_color="transparent")
            f.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(f, text=key, width=110, anchor="w", text_color=MUTED).pack(side="left")
            s = ctk.CTkSlider(f, from_=lo, to=hi, command=lambda _v: self._on_fx())
            s.pack(side="left", fill="x", expand=True)
            self.fx[key] = s
        self.fx["delay (speed)"].set(10)
        self.fx["breath"].set(32)
        self.fx["color shift"].set(5)
        self.fx["patrol #"].set(3)

    def _on_effect(self, name):
        self._stop_anim()
        try:
            self.ctrl.set_effect(name)
            if name == "manual":
                self.ctrl.set_all(self.colors)
            self._status(f"effect: {name}")
        except Exception as e:
            self._status(f"error: {e}")

    def _on_fx(self):
        try:
            self.ctrl.set_effect_params(
                delay=int(self.fx["delay (speed)"].get()),
                breath_level=int(self.fx["breath"].get()),
                color_shift=int(self.fx["color shift"].get()),
                patrol_num=int(self.fx["patrol #"].get()))
        except Exception as e:
            self._status(f"error: {e}")

    # ---- Flags ----
    def _tab_flags(self, tab):
        card = self._card(tab, "Flag wave (stadium)")
        r1 = ctk.CTkFrame(card, fg_color="transparent"); r1.pack(fill="x", padx=14, pady=8)
        self.flag = ctk.CTkOptionMenu(r1, values=flag_names(), width=140,
                                      fg_color=CARD, button_color=ACCENT)
        self.flag.set("Poland"); self.flag.pack(side="left", padx=(0, 8))
        self.flag_mode = ctk.CTkOptionMenu(r1, values=list(MODES), width=140,
                                           fg_color=CARD, button_color=ACCENT)
        self.flag_mode.set(MODES[0]); self.flag_mode.pack(side="left")

        r2 = ctk.CTkFrame(card, fg_color="transparent"); r2.pack(fill="x", padx=14, pady=8)
        self.flag_dir = ctk.CTkOptionMenu(r2, values=["L → R", "R → L"], width=90,
                                          fg_color=CARD, button_color=ACCENT)
        self.flag_dir.set("L → R"); self.flag_dir.pack(side="left", padx=(0, 8))
        self.flag_mirror = ctk.CTkCheckBox(r2, text="Mirror (module)", fg_color=ACCENT)
        self.flag_mirror.pack(side="left")

        r3 = ctk.CTkFrame(card, fg_color="transparent"); r3.pack(fill="x", padx=14, pady=8)
        ctk.CTkLabel(r3, text="Speed", text_color=MUTED, width=50).pack(side="left")
        self.flag_speed = ctk.CTkSlider(r3, from_=0.2, to=3.0); self.flag_speed.set(1.0)
        self.flag_speed.pack(side="left", fill="x", expand=True, padx=8)

        ctk.CTkButton(card, text="Start ▶", command=self._flag_start, fg_color=ACCENT,
                      hover_color=ACCENT_HOVER, text_color="#20183a",
                      font=("Segoe UI", 13, "bold")).pack(pady=(4, 12))

    def _flag_start(self):
        a = Animation(
            "flag", pattern="flag", flag=self.flag.get(),
            motion="wave" if self.flag_mode.get() == "Stadium wave" else "scroll",
            speed=float(self.flag_speed.get()),
            direction=1 if self.flag_dir.get() == "L → R" else -1,
            mirror=bool(self.flag_mirror.get()))
        self._play(a)

    # ---- Animations (builder) ----
    def _tab_anim(self, tab):
        top = self._card(tab, "Presets")
        r = ctk.CTkFrame(top, fg_color="transparent"); r.pack(fill="x", padx=14, pady=10)
        self.preset_menu = ctk.CTkOptionMenu(r, values=[p.name for p in self.presets],
                                             command=self._load_preset, width=200,
                                             fg_color=CARD, button_color=ACCENT)
        self.preset_menu.pack(side="left")
        ctk.CTkButton(r, text="Play ▶", width=70, command=self._builder_play, fg_color=ACCENT,
                      hover_color=ACCENT_HOVER, text_color="#20183a").pack(side="left", padx=6)
        ctk.CTkButton(r, text="Stop ■", width=70, command=self._stop_anim,
                      fg_color=CARD).pack(side="left")

        b = self._card(tab, "Build your own")
        g = ctk.CTkFrame(b, fg_color="transparent"); g.pack(fill="x", padx=14, pady=8)
        ctk.CTkLabel(g, text="Pattern", text_color=MUTED, width=70).grid(row=0, column=0, sticky="w")
        self.b_pat = ctk.CTkOptionMenu(g, values=list(PATTERNS), fg_color=CARD, button_color=ACCENT)
        self.b_pat.set("gradient"); self.b_pat.grid(row=0, column=1, padx=6, pady=4, sticky="w")
        ctk.CTkLabel(g, text="Motion", text_color=MUTED, width=70).grid(row=1, column=0, sticky="w")
        self.b_mot = ctk.CTkOptionMenu(g, values=list(MOTIONS), fg_color=CARD, button_color=ACCENT)
        self.b_mot.set("scroll"); self.b_mot.grid(row=1, column=1, padx=6, pady=4, sticky="w")

        self.b_colors: list[RGB] = [(255, 94, 0), (255, 0, 128), (80, 0, 200)]
        cbar = ctk.CTkFrame(b, fg_color="transparent"); cbar.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(cbar, text="Colors:", text_color=MUTED).pack(side="left")
        self.b_swatches = ctk.CTkFrame(cbar, fg_color="transparent"); self.b_swatches.pack(side="left", padx=6)
        ctk.CTkButton(cbar, text="+", width=28, command=self._b_add_color, fg_color=CARD).pack(side="left")
        ctk.CTkButton(cbar, text="−", width=28, command=self._b_del_color, fg_color=CARD).pack(side="left", padx=4)
        self._b_refresh_colors()

        s = ctk.CTkFrame(b, fg_color="transparent"); s.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(s, text="Speed", text_color=MUTED, width=50).pack(side="left")
        self.b_speed = ctk.CTkSlider(s, from_=0.2, to=3.0); self.b_speed.set(1.0)
        self.b_speed.pack(side="left", fill="x", expand=True, padx=8)
        self.b_dir = ctk.CTkOptionMenu(s, values=["L → R", "R → L"], width=80,
                                       fg_color=CARD, button_color=ACCENT)
        self.b_dir.set("L → R"); self.b_dir.pack(side="left", padx=4)
        self.b_mirror = ctk.CTkCheckBox(s, text="Mirror", fg_color=ACCENT); self.b_mirror.pack(side="left")

        nr = ctk.CTkFrame(b, fg_color="transparent"); nr.pack(fill="x", padx=14, pady=(6, 12))
        self.b_name = ctk.CTkEntry(nr, placeholder_text="animation name")
        self.b_name.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(nr, text="Save preset", width=100, command=self._save_preset,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#20183a").pack(side="left", padx=6)

    def _b_refresh_colors(self):
        for w in self.b_swatches.winfo_children():
            w.destroy()
        for i, c in enumerate(self.b_colors):
            ctk.CTkButton(self.b_swatches, text="", width=24, height=24, fg_color=to_hex(c),
                          hover=False, command=lambda idx=i: self._b_pick(idx)).pack(side="left", padx=2)

    def _b_pick(self, i):
        rgb, _ = colorchooser.askcolor(color=to_hex(self.b_colors[i]))
        if rgb:
            self.b_colors[i] = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
            self._b_refresh_colors()

    def _b_add_color(self):
        self.b_colors.append((255, 255, 255)); self._b_refresh_colors()

    def _b_del_color(self):
        if len(self.b_colors) > 1:
            self.b_colors.pop(); self._b_refresh_colors()

    def _build_anim(self, name="preview") -> Animation:
        return Animation(
            name=name, pattern=self.b_pat.get(), colors=list(self.b_colors),
            flag=self.flag.get() if hasattr(self, "flag") else "Poland",
            motion=self.b_mot.get(), speed=float(self.b_speed.get()),
            direction=1 if self.b_dir.get() == "L → R" else -1,
            mirror=bool(self.b_mirror.get()))

    def _builder_play(self):
        self._play(self._build_anim())

    def _save_preset(self):
        name = self.b_name.get().strip() or f"Preset {len(self.presets) + 1}"
        a = self._build_anim(name)
        self.presets.append(a)
        save_presets(self.presets)
        self.preset_menu.configure(values=[p.name for p in self.presets])
        self.preset_menu.set(name)
        self._status(f"saved preset: {name}")

    def _load_preset(self, name):
        for p in self.presets:
            if p.name == name:
                self.b_pat.set(p.pattern); self.b_mot.set(p.motion)
                self.b_colors = list(p.colors) or [(255, 255, 255)]
                self._b_refresh_colors()
                self.b_speed.set(p.speed)
                self.b_dir.set("L → R" if p.direction >= 0 else "R → L")
                (self.b_mirror.select if p.mirror else self.b_mirror.deselect)()
                self._play(p)
                break

    # ---- Settings ----
    def _tab_settings(self, tab):
        c = self._card(tab, "Startup & tray")
        self.cb_autostart = ctk.CTkCheckBox(c, text="Start with Windows (run in tray)",
                                            command=self._toggle_autostart, fg_color=ACCENT)
        if autostart.is_enabled():
            self.cb_autostart.select()
        self.cb_autostart.pack(anchor="w", padx=14, pady=10)
        ctk.CTkLabel(c, text="Closing the window hides SteamLEDs to the tray by the clock;\n"
                            "it keeps running your animation. Right-click the tray icon to Quit.",
                     text_color=MUTED, justify="left").pack(anchor="w", padx=14, pady=(0, 12))

        c2 = self._card(tab, "About")
        info = "PREVIEW mode (no hardware detected)" if self.preview else "Hardware connected ✓"
        ctk.CTkLabel(c2, text=info, text_color=MUTED).pack(anchor="w", padx=14, pady=8)
        ctk.CTkButton(c2, text="Quit SteamLEDs", command=self.quit_app, fg_color="#7a2b2b",
                      hover_color="#5e2020").pack(anchor="w", padx=14, pady=(0, 12))

    def _toggle_autostart(self):
        try:
            if self.cb_autostart.get():
                autostart.enable()
                self._status("autostart enabled")
            else:
                autostart.disable()
                self._status("autostart disabled")
        except Exception as e:
            self._status(f"autostart error: {e}")

    # ================= animation loop =================
    def _play(self, anim: Animation):
        self._anim = anim
        self._anim_t0 = time.perf_counter()
        if self._anim_job is None:
            self._tick()
        self._status(f"playing: {anim.name}")

    def _tick(self):
        if self._anim is None:
            self._anim_job = None
            return
        t = time.perf_counter() - self._anim_t0
        try:
            self.ctrl.set_all(self._anim.frame(t, LED_COUNT))
        except Exception as e:
            self._status(f"error: {e}")
            self._anim = None
            self._anim_job = None
            return
        self._anim_job = self.after(40, self._tick)

    def _stop_anim(self):
        if self._anim_job is not None:
            self.after_cancel(self._anim_job)
        self._anim_job = None
        self._anim = None

    # ================= tray =================
    def _start_tray(self):
        try:
            import pystray
        except Exception:
            return
        menu = pystray.Menu(
            pystray.MenuItem("Show", self._tray_show, default=True),
            pystray.MenuItem("Stop animation", lambda: self.after(0, self._stop_anim)),
            pystray.MenuItem("Quit", self._tray_quit),
        )
        self._tray = pystray.Icon("SteamLEDs", _tray_image(), "SteamLEDs", menu)
        threading.Thread(target=self._tray.run, daemon=True).start()

    def _tray_show(self, *_):
        self.after(0, self.deiconify)

    def _tray_quit(self, *_):
        self.after(0, self.quit_app)

    def hide_to_tray(self):
        if self._tray is not None:
            self.withdraw()
            self._status("running in tray")
        else:
            self.quit_app()

    def quit_app(self):
        self._stop_anim()
        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.destroy()


def run_app(backend: str = "auto", start_tray: bool = False) -> int:
    app = SteamLedsApp(backend=backend, start_tray=start_tray)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_app())
