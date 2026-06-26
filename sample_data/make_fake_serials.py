"""
Generate four ILLUSTRATIVE counterfeit ₹500 notes, each with a DIFFERENT invalid
serial number — one per type of RBI serial-grammar violation. Used in the
Counterfeit module's Real-vs-Fake showcase to demonstrate the serial-number check
across varied fakes (real counterfeits are illegal to hold/redistribute).

Output: frontend/showcase/fake/fake1..4.jpg
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "frontend", "showcase", "fake")
W, H = 600, 264
BG = (168, 170, 150)  # ₹500 stone-grey-ish

# (serial, why-invalid) — each violates RBI grammar [0-2 digits][1-3 letters][6 digits]
FAKES = [
    ("0 0 0 0 0 0", "all-zero placeholder serial"),
    ("1234 567890", "too many digits in prefix"),
    ("ZZ 12AB34", "letters inside the number block"),
    ("9XYZ 8888", "only 4 trailing digits (needs 6)"),
]


def _font(sz, bold=False):
    for p in ([
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf"]):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def make(serial: str, idx: int):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(idx)
    # faint microprint-ish texture
    for _ in range(1500):
        x, y = rng.integers(0, W), rng.integers(0, H)
        c = tuple(int(v) for v in rng.integers(120, 190, 3))
        d.line([(x, y), (x + rng.integers(2, 7), y)], fill=c, width=1)
    # header (ASCII only — avoids missing-glyph boxes)
    d.text((18, 12), "RESERVE BANK OF INDIA", fill=(70, 70, 60), font=_font(20, True))
    # Gandhi placeholder
    d.ellipse([250, 70, 360, 200], fill=(150, 152, 132), outline=(110, 110, 95))
    d.text((40, 150), "500", fill=(60, 60, 50), font=_font(64, True))
    d.text((455, 178), "Rs.500", fill=(40, 90, 80), font=_font(32, True))
    # serial — top-left and bottom-right (like a real note)
    sf = _font(26, True)
    d.text((20, 56), serial, fill=(140, 30, 30), font=sf)
    d.text((W - 175, 30), serial, fill=(140, 30, 30), font=sf)
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, f"fake{idx}.jpg"), quality=84)


if __name__ == "__main__":
    for i, (s, why) in enumerate(FAKES, 1):
        make(s, i)
        print(f"  fake{i}: '{s}'  — {why}")
    print("Wrote 4 illustrative counterfeits to", OUT)
