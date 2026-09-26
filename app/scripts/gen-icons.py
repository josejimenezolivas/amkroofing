"""Regenerate the AMK Roofing favicon / app-icon / social-card set.

Source of truth for everything under app/assets/brand/. Run from anywhere:
    python3 app/scripts/gen-icons.py   (needs Pillow)
Then copy the .ico to the site root:  cp app/assets/brand/favicon.ico app/favicon.ico
"""
from PIL import Image, ImageFilter, ImageDraw
import os

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(APP, 'assets', 'amk-logo-light.png')
OUT = os.path.join(APP, 'assets', 'brand')
os.makedirs(OUT, exist_ok=True)

full = Image.open(SRC).convert('RGBA')
# AMK wordmark + roof chevron only (drop the faint "ROOFING" line: illegible at icon sizes)
mark = full.crop((0, 0, full.width, 218)).crop(
    Image.open(SRC).convert('RGBA').crop((0, 0, full.width, 218)).getbbox())

def tile(size, pad_ratio=0.72, bleed=True):
    """Dark brand tile with the AMK mark centred. pad_ratio = mark width / tile width."""
    S = 1024
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # vertical gradient backdrop: deep slate -> near-black (matches site --bg)
    for y in range(S):
        t = y / (S - 1)
        r = int(0x11 + (0x06 - 0x11) * t)
        g = int(0x1e + (0x0a - 0x1e) * t)
        b = int(0x2a + (0x0e - 0x2a) * t)
        d.line([(0, y), (S, y)], fill=(r, g, b, 255))

    mw = int(S * pad_ratio)
    mh = max(1, round(mark.height * mw / mark.width))
    m = mark.resize((mw, mh), Image.LANCZOS)
    img.alpha_composite(m, ((S - mw) // 2, (S - mh) // 2))

    out = img.resize((size, size), Image.LANCZOS)
    if size <= 64:  # keep the letterforms crisp when tiny
        out = out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=110, threshold=2))
    return out.convert('RGB')

# --- favicons -------------------------------------------------------------
# Google wants a square favicon whose size is a multiple of 48px.
for s in (48, 96, 144, 192, 512):
    tile(s, 0.84).save(f'{OUT}/favicon-{s}x{s}.png', optimize=True)

# Multi-resolution .ico: largest frame is the base, the rest are appended so each
# size is rendered (and sharpened) at its own resolution rather than downscaled twice.
ico_sizes = (64, 48, 32, 16)
ico = [tile(s, 0.84 if s >= 32 else 0.90) for s in ico_sizes]
ico[0].save(f'{OUT}/favicon.ico', format='ICO',
            sizes=[(s, s) for s in ico_sizes],
            append_images=ico[1:])

# --- apple touch icon (iOS rounds the corners itself, so full bleed) -------
tile(180, 0.72).save(f'{OUT}/apple-touch-icon.png', optimize=True)

# --- social share card ----------------------------------------------------
W, H = 1200, 630
og = Image.new('RGBA', (W, H))
d = ImageDraw.Draw(og)
for y in range(H):
    t = y / (H - 1)
    r = int(0x11 + (0x06 - 0x11) * t)
    g = int(0x1e + (0x0a - 0x1e) * t)
    b = int(0x2a + (0x0e - 0x2a) * t)
    d.line([(0, y), (W, y)], fill=(r, g, b, 255))
lw = int(W * 0.52)
lh = round(full.height * lw / full.width)
og.alpha_composite(full.resize((lw, lh), Image.LANCZOS), ((W - lw) // 2, (H - lh) // 2))
og.convert('RGB').save(f'{OUT}/og-image.png', optimize=True)

for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(f'{OUT}/{f}'))
