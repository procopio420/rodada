#!/usr/bin/env python3
"""Generate store artwork from Rodada's dark/paper tokens. Requires: pip install Pillow."""
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit("Install Pillow first: python3 -m pip install Pillow") from exc

OUT = Path("play-artwork")
OUT.mkdir(exist_ok=True)
DARK = (18, 15, 12)
PAPER = (243, 236, 225)
MUTED = (181, 168, 153)

def font(size, bold=False):
    names = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
        if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    )
    for path in names:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def monogram(draw, cx, cy, scale=1, fill=PAPER):
    """Simplified R shape matching the XML launcher monogram."""
    x, y = cx - 54 * scale, cy - 54 * scale
    p = lambda u, v: (round(x + u * scale), round(y + v * scale))
    # thick left stem, upper bowl, and diagonal leg
    draw.rounded_rectangle([p(30, 29), p(43, 83)], radius=2 * scale, fill=fill)
    draw.rounded_rectangle([p(40, 29), p(80, 69)], radius=17 * scale, fill=fill)
    draw.rounded_rectangle([p(43, 41), p(68, 57)], radius=8 * scale, fill=DARK)
    draw.polygon([p(53, 61), p(67, 61), p(84, 83), p(68, 83)], fill=fill)

icon = Image.new("RGB", (512, 512), DARK)
d = ImageDraw.Draw(icon)
monogram(d, 256, 256, 3.8)
icon.save(OUT / "icon-512.png", optimize=True)

banner = Image.new("RGB", (1024, 500), DARK)
b = ImageDraw.Draw(banner)
b.rounded_rectangle((60, 85, 372, 397), radius=64, outline=(75, 66, 58), width=3)
monogram(b, 216, 241, 2.1)
b.text((432, 170), "Rodada", fill=PAPER, font=font(78, True))
b.text((436, 279), "ATENDIMENTO", fill=MUTED, font=font(33, True))
banner.save(OUT / "feature-1024x500.png", optimize=True)
print("Created:", OUT / "icon-512.png", "and", OUT / "feature-1024x500.png")
