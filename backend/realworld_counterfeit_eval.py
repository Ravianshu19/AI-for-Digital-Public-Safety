"""
Real-world stress test for the counterfeit agent on REAL Indian note photos.

Dataset: Kaggle `gauravsahani/indian-currency-notes-classifier` — ~195 real-world
mobile photos of genuine Indian notes across 7 denominations (cluttered backgrounds,
angles, lighting). Fetch with:
    KAGGLE_KEY=KGAT_… .venv/bin/python sample_data/fetch_indian_currency.py

Purpose (honesty): the v1 glass-box heuristic is calibrated for *controlled* capture
(scanner / bank counter / the app's guided-capture frame). This script measures its
ceiling on *uncontrolled* mobile photos — quantifying the gain a CNN/ViT upgrade
(on the roadmap) would deliver. Run:  python backend/realworld_counterfeit_eval.py
"""

from __future__ import annotations

import glob
import os
from collections import defaultdict
from typing import Dict, Optional

import counterfeit

FOLDER_DENOM = {
    "Tennote": 10, "Twentynote": 20, "Fiftynote": 50, "1Hundrednote": 100,
    "2Hundrednote": 200, "5Hundrednote": 500, "2Thousandnote": 2000,
}
CACHE = os.path.expanduser(
    "~/.cache/kagglehub/datasets/gauravsahani/indian-currency-notes-classifier/versions/*")


def _base() -> Optional[str]:
    hits = sorted(glob.glob(CACHE))
    return hits[0] if hits else None


def available() -> bool:
    return _base() is not None


def run() -> Dict:
    base = _base()
    if not base:
        return {"available": False}
    n = genuine = suspect = rejected = score_sum = 0
    per = defaultdict(lambda: [0, 0, 0])  # denom -> [n, genuine, rejected]
    for split in ("Train", "Test"):
        for folder, den in FOLDER_DENOM.items():
            for img in glob.glob(os.path.join(base, split, folder, "*")):
                if not img.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                try:
                    r = counterfeit.analyze_image(open(img, "rb").read(), den)
                except Exception:
                    continue
                n += 1; score_sum += r.authenticity_score; per[den][0] += 1
                if r.verdict == "GENUINE":
                    genuine += 1; per[den][1] += 1
                elif r.verdict == "SUSPECT":
                    suspect += 1
                else:
                    rejected += 1; per[den][2] += 1
    if not n:
        return {"available": False}
    pct = lambda a: round(100 * a / n, 1)
    return {
        "available": True,
        "source": "Kaggle gauravsahani/indian-currency-notes-classifier (real mobile photos)",
        "images": n, "denominations": len(per),
        "full_clearance_pct": pct(genuine),
        "flagged_for_review_pct": pct(suspect),
        "false_rejection_pct": pct(rejected),
        "not_rejected_pct": pct(genuine + suspect),
        "mean_authenticity": round(score_sum / n, 1),
    }


if __name__ == "__main__":
    r = run()
    if not r["available"]:
        print("Dataset missing — run sample_data/fetch_indian_currency.py (Kaggle token).")
    else:
        print(f"{r['source']}")
        print(f"{r['images']} real photos across {r['denominations']} denominations")
        print(f"  full clearance (GENUINE) : {r['full_clearance_pct']}%")
        print(f"  flagged for review (SUSPECT): {r['flagged_for_review_pct']}%")
        print(f"  false rejection (genuine→COUNTERFEIT): {r['false_rejection_pct']}%")
        print(f"  mean authenticity: {r['mean_authenticity']}")
        print("Note: v1 heuristic targets controlled capture; uncontrolled mobile "
              "photos motivate the CNN/ViT upgrade on the roadmap.")
