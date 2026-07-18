"""Command-line interface for steamleds."""
from __future__ import annotations

import argparse
import sys

from .colors import RGB, parse_color, rainbow, to_hex
from .controller import EFFECTS, LED_COUNT, LedController
from .portio import open_backend


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--backend",
        default="auto",
        choices=["auto", "inpout", "winring0", "devport", "dummy"],
        help="Port-I/O backend (default: auto-detect).",
    )
    p.add_argument(
        "--brightness",
        type=int,
        default=None,
        help="Global brightness scale 0..255 (factory default 55). Higher = brighter.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="steamleds",
        description="Control the Steam Machine (Valve Fremont) front RGB LEDs.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("solid", help="Set all LEDs to one color.")
    p.add_argument("color", help="#RRGGBB or 'r g b'")
    _add_common(p)

    p = sub.add_parser("led", help="Set a single LED (0..16).")
    p.add_argument("index", type=int)
    p.add_argument("color", help="#RRGGBB or 'r g b'")
    _add_common(p)

    p = sub.add_parser("gradient", help="Set an explicit list of colors (up to 17).")
    p.add_argument("colors", nargs="+", help="colors, e.g. #ff0000 #00ff00 ...")
    _add_common(p)

    p = sub.add_parser("rainbow", help="Spread a rainbow across the panel.")
    p.add_argument("--offset", type=float, default=0.0, help="hue offset 0..1")
    _add_common(p)

    p = sub.add_parser("off", help="Turn all LEDs off.")
    _add_common(p)

    p = sub.add_parser("effect", help="Select a firmware effect.")
    p.add_argument("name", choices=list(EFFECTS))
    p.add_argument("--delay", type=int, default=None, help="animation speed 0..20")
    p.add_argument("--breath", type=int, default=None, help="breath level 0..255")
    p.add_argument("--shift", type=int, default=None, help="color shift 0..255")
    p.add_argument("--patrol", type=int, default=None, help="patrol count 1..17")
    _add_common(p)

    p = sub.add_parser("startup", help="Persist a boot/power-on color (survives reboot).")
    p.add_argument("color", help="#RRGGBB or 'r g b'")
    _add_common(p)

    from .flags import MODES, flag_names

    p = sub.add_parser("flag", help="Show a national flag, static or as a stadium wave.")
    p.add_argument("country", choices=flag_names())
    p.add_argument("--wave", action="store_true", help="animate instead of static")
    p.add_argument("--mode", choices=list(MODES), default=MODES[0])
    p.add_argument("--seconds", type=float, default=10.0, help="animation duration")
    p.add_argument("--speed", type=float, default=1.0)
    p.add_argument("--reverse", action="store_true", help="wave travels right->left")
    p.add_argument("--mirror", action="store_true", help="flip layout for module mounting")
    _add_common(p)

    p = sub.add_parser("dump", help="Read back current LED colors.")
    _add_common(p)

    p = sub.add_parser("gui", help="Launch the graphical control panel.")
    _add_common(p)

    return parser


def _make_controller(args) -> LedController:
    io = open_backend(args.backend)
    ctrl = LedController(io)
    if getattr(args, "brightness", None) is not None:
        ctrl.set_brightness_scale(args.brightness, reapply=False)
    return ctrl


def main(argv: list[str] | None = None) -> int:
    raw = sys.argv[1:] if argv is None else argv
    if "--app" in raw:      # modern desktop app (customtkinter + tray)
        from .app import run_app

        return run_app(start_tray="--tray" in raw)

    args = build_parser().parse_args(argv)

    if args.cmd == "gui":
        from .gui import run_gui

        return run_gui(backend=args.backend)

    try:
        ctrl = _make_controller(args)
    except Exception as exc:  # backend/driver problems
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.cmd == "solid":
        ctrl.set_solid(parse_color(args.color))
    elif args.cmd == "led":
        ctrl.ensure_manual()
        ctrl.set_led(args.index, parse_color(args.color))
    elif args.cmd == "gradient":
        colors: list[RGB] = [parse_color(c) for c in args.colors]
        if len(colors) < LED_COUNT:
            colors += [colors[-1]] * (LED_COUNT - len(colors))
        ctrl.set_all(colors[:LED_COUNT])
    elif args.cmd == "rainbow":
        ctrl.set_rainbow(offset=args.offset)
    elif args.cmd == "off":
        ctrl.off()
    elif args.cmd == "effect":
        ctrl.set_effect(args.name)
        ctrl.set_effect_params(delay=args.delay, breath_level=args.breath,
                               color_shift=args.shift, patrol_num=args.patrol)
    elif args.cmd == "startup":
        ctrl.set_startup(parse_color(args.color),
                         brightness=getattr(args, "brightness", None))
    elif args.cmd == "flag":
        from .flags import FlagAnimator, FLAGS, render_static

        if not args.wave:
            frame = render_static(FLAGS[args.country], LED_COUNT)
            if args.mirror:
                frame = frame[::-1]
            ctrl.set_all(frame)
        else:
            import time

            anim = FlagAnimator(args.country, count=LED_COUNT, mode=args.mode,
                                speed=args.speed, direction=-1 if args.reverse else 1,
                                mirror=args.mirror)
            end = time.time() + args.seconds
            try:
                while time.time() < end:
                    ctrl.set_all(anim.next_frame())
                    time.sleep(0.04)
            except KeyboardInterrupt:
                pass
    elif args.cmd == "dump":
        for i, c in enumerate(ctrl.read_all()):
            print(f"LED {i:2d}: {to_hex(c)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
