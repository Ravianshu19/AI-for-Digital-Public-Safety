"""
Generate synthetic banknote images for testing the counterfeit module.
Produces:
  genuine_500.png    -> detail-rich, correct ratio/colour, sharp texture
  counterfeit_500.png-> blurry, washed-out, wrong colour (typical photocopy fake)

Run:  prahari/.venv/bin/python prahari/sample_data/make_samples.py
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.dirname(__file__)
W, H = 600, 264  # ~ ₹500 ratio (150/66)


def base(colour):
    img = Image.new("RGB", (W, H), colour)
    return img


def add_detail(img, density):
    """Add fine line/microprint texture; higher density => more 'genuine'."""
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(7)
    for _ in range(density):
        x = rng.integers(0, W); y = rng.integers(0, H)
        l = rng.integers(2, 9)
        c = tuple(int(v) for v in rng.integers(40, 210, 3))
        d.line([(x, y), (x + l, y)], fill=c, width=1)
    # security thread band
    for x in range(int(W * 0.32), int(W * 0.36)):
        for y in range(0, H, 3):
            img.putpixel((x, y), (230, 230, 210))
    return img


def label(img, txt):
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 60)
    except Exception:
        f = ImageFont.load_default()
    d.text((24, 90), txt, fill=(20, 20, 20), font=f)
    return img


# Genuine: correct stone-grey, dense microprint, sharp.
g = base((132, 130, 118))
g = add_detail(g, 9000)
g = label(g, "500")
g.save(os.path.join(OUT, "genuine_500.png"))

# Counterfeit: wrong colour cast, sparse detail, blurred (photocopy look).
c = base((170, 150, 120))
c = add_detail(c, 600)
c = label(c, "500")
c = c.filter(ImageFilter.GaussianBlur(2.2))
c.save(os.path.join(OUT, "counterfeit_500.png"))

print("Wrote genuine_500.png and counterfeit_500.png to", OUT)
