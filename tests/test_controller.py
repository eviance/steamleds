"""Logic tests using the in-memory DummyBackend (no hardware/driver needed)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from steamleds.colors import parse_color, rainbow, to_hex  # noqa: E402
from steamleds.controller import (  # noqa: E402
    BASE,
    LED_COUNT,
    OFF_BLOCK_A,
    OFF_BLOCK_B,
    OFF_EFFECT,
    OFF_EFFECT_MIRROR,
    OFF_STARTUP_BRIGHT,
    OFF_STARTUP_COLOR,
    EFFECTS,
    LedController,
)
from steamleds.portio import DummyBackend  # noqa: E402


def make():
    io = DummyBackend()
    return io, LedController(io, brightness_scale=55)


def test_set_led_writes_both_blocks():
    io, ctrl = make()
    ctrl.set_led(0, (255, 0, 0))
    # raw block B == exact color
    assert io.read(BASE + OFF_BLOCK_B + 0) == 255
    assert io.read(BASE + OFF_BLOCK_B + 1) == 0
    assert io.read(BASE + OFF_BLOCK_B + 2) == 0
    # scaled block A == 255 * 55 // 255 == 55
    assert io.read(BASE + OFF_BLOCK_A + 0) == 55
    assert io.read(BASE + OFF_BLOCK_A + 1) == 0


def test_led_stride_is_three():
    io, ctrl = make()
    ctrl.set_led(5, (0x10, 0x20, 0x30))
    p = BASE + OFF_BLOCK_B + 3 * 5
    assert (io.read(p), io.read(p + 1), io.read(p + 2)) == (0x10, 0x20, 0x30)


def test_set_all_requires_full_strip():
    _io, ctrl = make()
    try:
        ctrl.set_all([(0, 0, 0)])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for wrong length")


def test_ensure_manual_sets_effect_register():
    io, ctrl = make()
    ctrl.ensure_manual()
    assert io.read(BASE + OFF_EFFECT) == EFFECTS["manual"]


def test_readback_roundtrip():
    _io, ctrl = make()
    colors = rainbow(LED_COUNT)
    ctrl.set_all(colors)
    assert ctrl.read_all() == colors


def test_brightness_rescales_block_a():
    io, ctrl = make()
    ctrl.set_led(0, (200, 100, 0))
    ctrl.set_brightness_scale(255)  # full
    assert io.read(BASE + OFF_BLOCK_A + 0) == 200
    assert io.read(BASE + OFF_BLOCK_A + 1) == 100


def test_effect_writes_index_to_both_registers():
    io, ctrl = make()
    ctrl.set_effect("rainbow")   # index 5 (confirmed on hardware)
    assert io.read(BASE + OFF_EFFECT) == EFFECTS["rainbow"] == 5
    assert io.read(BASE + OFF_EFFECT_MIRROR) == 5


def test_startup_writes_boot_registers():
    io, ctrl = make()
    ctrl.set_startup((1, 90, 255), brightness=0x38)
    assert (io.read(BASE + OFF_STARTUP_COLOR),
            io.read(BASE + OFF_STARTUP_COLOR + 1),
            io.read(BASE + OFF_STARTUP_COLOR + 2)) == (1, 90, 255)
    assert io.read(BASE + OFF_STARTUP_BRIGHT) == 0x38


def test_flags_render_and_animate():
    from steamleds.flags import FLAGS, FlagAnimator, flag_names, render_static

    assert "Poland" in flag_names()
    poland = render_static(FLAGS["Poland"], LED_COUNT)
    assert len(poland) == LED_COUNT
    assert poland[0] == (255, 255, 255)   # white on the left
    assert poland[-1] == (220, 20, 60)    # red on the right
    anim = FlagAnimator("Poland", count=LED_COUNT)
    frame = anim.next_frame()
    assert len(frame) == LED_COUNT and all(len(c) == 3 for c in frame)
    # mirror flips the layout
    m = FlagAnimator("Poland", count=LED_COUNT, mirror=True)
    assert m.next_frame() == FlagAnimator("Poland", count=LED_COUNT).next_frame()[::-1]
    # direction changes pulse travel sign
    fwd = FlagAnimator("Poland", count=LED_COUNT, direction=1)
    rev = FlagAnimator("Poland", count=LED_COUNT, direction=-1)
    fwd.next_frame(); rev.next_frame()
    assert round(fwd._pos, 3) == round((-rev._pos) % LED_COUNT, 3)


def test_color_parsing():
    assert parse_color("#ff8800") == (255, 136, 0)
    assert parse_color("255 136 0") == (255, 136, 0)
    assert to_hex((255, 136, 0)) == "#ff8800"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed")
