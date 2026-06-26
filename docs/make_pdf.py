"""
Build a clean, shareable PDF walkthrough of Prahari from the captured screenshots.
(Browser 'Save as PDF' of the live dashboard breaks — it only captures the active tab
and drops dark backgrounds/canvas. This assembles the real screenshots instead.)

Run:  .venv/bin/python docs/make_pdf.py  ->  docs/Prahari_Walkthrough.pdf
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(__file__)
SHOTS = os.path.join(HERE, "screenshots")
BG = (10, 14, 23)
PANEL = (18, 24, 38)
ACCENT = (62, 166, 255)
TXT = (230, 237, 246)
MUTED = (140, 155, 181)
PAGE = (1600, 1000)  # landscape

PAGES = [
    ("01-overview.png", "Command Overview", "Landing, live India fraud stats & intelligence feed"),
    ("02-scam.png", "Digital Arrest Scam Detection", "Real-time as-you-type kill-chain scoring + auto MHA alert"),
    ("03-counterfeit.png", "Counterfeit Currency Agent", "9-feature note forensics across ₹10–₹2000"),
    ("13-real-fake.png", "Real vs Fake Notes", "Genuine notes vs counterfeits with invalid serials"),
    ("04-fraud.png", "Fraud Network Graph", "Community detection, kingpins & lead-time"),
    ("11-india-upi.png", "Real India UPI Fraud Intelligence", "Kaggle FY23–25 — type / lure / app / state"),
    ("05-geo.png", "Geospatial Intelligence", "National hotspot map + patrol priority"),
    ("10-geo-ncrb.png", "NCRB State Cybercrime", "Real Crime-in-India 2024 state data"),
    ("12-cybercrime-motive.png", "Cybercrime by Motive", "59% of India cybercrime is financial fraud"),
    ("06-shield.png", "Citizen Fraud Shield", "12-language chatbot + screenshot OCR"),
    ("07-performance.png", "Model Performance", "100% precision · 97.1% recall · 0% false-positive"),
    ("08-counterfeit-accuracy.png", "Counterfeit Accuracy", "Per-denomination, real RBI notes"),
    ("09-audit-ledger.png", "Tamper-evident Audit Ledger", "Hash-chained evidence for legal admissibility"),
]


def font(sz, bold=False):
    for p in ([f"/System/Library/Fonts/Supplemental/Arial{' Bold' if bold else ''}.ttf",
               "/Library/Fonts/Arial.ttf"]):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def fit(img, maxw, maxh):
    r = min(maxw / img.width, maxh / img.height)
    return img.resize((int(img.width * r), int(img.height * r)))


def content_page(shot, title, sub, n, total):
    page = Image.new("RGB", PAGE, BG)
    d = ImageDraw.Draw(page)
    d.rectangle([0, 0, PAGE[0], 92], fill=PANEL)
    d.rectangle([0, 92, PAGE[0], 95], fill=ACCENT)
    d.text((48, 24), title, fill=TXT, font=font(30, True))
    d.text((50, 64), sub, fill=MUTED, font=font(16))
    d.text((PAGE[0] - 150, 38), f"{n} / {total}", fill=MUTED, font=font(18, True))
    try:
        im = Image.open(os.path.join(SHOTS, shot)).convert("RGB")
        im = fit(im, PAGE[0] - 120, PAGE[1] - 190)
        x = (PAGE[0] - im.width) // 2
        y = 95 + (PAGE[1] - 95 - 60 - im.height) // 2
        page.paste(im, (x, y))
        d.rectangle([x - 1, y - 1, x + im.width, y + im.height], outline=(40, 54, 80))
    except FileNotFoundError:
        d.text((60, 200), f"[missing {shot}]", fill=MUTED, font=font(20))
    d.text((48, PAGE[1] - 38), "PRAHARI — Digital Public Safety Intelligence", fill=MUTED, font=font(13))
    return page


def cover():
    page = Image.new("RGB", PAGE, BG)
    d = ImageDraw.Draw(page)
    for i in range(PAGE[1]):  # subtle vertical gradient
        t = i / PAGE[1]
        d.line([(0, i), (PAGE[0], i)],
               fill=(int(10 + 8 * (1 - t)), int(14 + 14 * (1 - t)), int(23 + 26 * (1 - t))))
    d.rounded_rectangle([70, 360, 150, 440], 18, fill=ACCENT)
    d.text((92, 372), "प्र", fill=(6, 18, 31), font=font(46, True))
    d.text((170, 360), "PRAHARI", fill=(255, 255, 255), font=font(58, True))
    d.text((172, 432), "Digital Public Safety Intelligence", fill=ACCENT, font=font(24))
    d.text((72, 500), "Neutralise digital fraud before the money moves.", fill=TXT, font=font(30, True))
    d.text((72, 552), "AI across digital-arrest scams, counterfeit currency, fraud networks,",
           fill=MUTED, font=font(18))
    d.text((72, 580), "geospatial crime intelligence and a multilingual citizen shield — for India.",
           fill=MUTED, font=font(18))
    d.text((72, 650), "100% scam precision    0% false positives    7 note denominations    12 languages",
           fill=(159, 208, 255), font=font(17, True))
    return page


def main():
    pages = [cover()] + [content_page(s, t, sub, i + 1, len(PAGES))
                         for i, (s, t, sub) in enumerate(PAGES)]
    out = os.path.join(HERE, "Prahari_Walkthrough.pdf")
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=150)
    print("Wrote", out, f"({len(pages)} pages)")


if __name__ == "__main__":
    main()
