"""Generate the SteamLEDs app icon (flat rounded square + LED dots) as PNG + ICO."""
import colorsys
import os

from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "steamleds", "assets")
os.makedirs(OUT, exist_ok=True)


def render(size: int) -> Image.Image:
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # flat rounded square background
    pad = int(s * 0.06)
    d.rounded_rectangle([pad, pad, s - pad, s - pad], radius=int(s * 0.22),
                        fill=(36, 29, 61, 255))  # flat deep purple
    # a row of flat LED dots (rainbow)
    n = 5
    r = int(s * 0.07)
    gap = int(s * 0.045)
    total = n * (2 * r) + (n - 1) * gap
    x0 = (s - total) // 2 + r
    y = int(s * 0.5)
    for i in range(n):
        cr, cg, cb = [int(x * 255) for x in colorsys.hsv_to_rgb(i / n, 0.85, 1.0)]
        cx = x0 + i * (2 * r + gap)
        d.ellipse([cx - r, y - r, cx + r, y + r], fill=(cr, cg, cb, 255))
    return img


def main():
    base = render(256)
    base.save(os.path.join(OUT, "icon.png"))
    sizes = [16, 24, 32, 48, 64, 128, 256]
    base.save(os.path.join(OUT, "icon.ico"), sizes=[(x, x) for x in sizes])
    print("wrote", os.path.join(OUT, "icon.png"), "and icon.ico")


if __name__ == "__main__":
    main()
