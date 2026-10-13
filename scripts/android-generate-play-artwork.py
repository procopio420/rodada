#!/usr/bin/env python3
"""Generate Play Store PNG artwork from the Rodada v1 canonical SVGs.

Run from the repository root. Install prerequisites: pip install Pillow CairoSVG.
No automatic Play Store release or deployment is performed.
"""
from pathlib import Path
from io import BytesIO
try:
    import cairosvg
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Install dependencies: python3 -m pip install Pillow CairoSVG")

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "assets/brand/v1"
OUT = ROOT / "play-artwork"
OUT.mkdir(exist_ok=True)
DARK = (18, 15, 12)
PAPER = (243, 236, 225)
AMBER = (245, 165, 36)

def render(name: str, width: int) -> Image.Image:
    png = cairosvg.svg2png(url=str(BRAND / name), output_width=width)
    return Image.open(BytesIO(png)).convert("RGBA")

def font(size: int):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

icon = Image.new("RGB", (512, 512), DARK)
symbol = render("symbol.svg", 396)
icon.paste(symbol, ((512 - symbol.width)//2, (512 - symbol.height)//2), symbol)
icon.save(OUT / "icon-512.png", optimize=True)

banner = Image.new("RGB", (1024, 500), DARK)
symbol = render("symbol.svg", 310)
banner.paste(symbol, (48, 95), symbol)
wordmark = render("wordmark.svg", 535)
banner.paste(wordmark, (425, 120), wordmark)
pen = ImageDraw.Draw(banner)
pen.text((437, 298), "ATENDIMENTO", font=font(39), fill=PAPER)
pen.rectangle((438, 369, 778, 376), fill=AMBER)
banner.save(OUT / "feature-1024x500.png", optimize=True)
print("Generated play-artwork/icon-512.png and feature-1024x500.png")
