"""
Counterfeit-agent accuracy benchmark (per denomination).

Scans sample_data/currency/<denom>/*.{jpg,png} — genuine RBI reference notes
(Mahatma Gandhi New Series, sourced from Wikimedia Commons) — and runs each
through the counterfeit agent at its true denomination.

Because possessing/sharing real FICN (fake notes) is a criminal offence in India,
we cannot benchmark fake-detection on real counterfeits. So we report:
  - Genuine-acceptance / false-rejection across denominations (the citizen-safety
    metric — you must NOT reject real money), measured on genuine notes, and
  - a synthetic print-quality stress test showing the agent rejects a degraded note.

Drop your own captured genuine-note images into sample_data/currency/<denom>/ and
re-run to extend the benchmark. Run:  python backend/counterfeit_eval.py
"""

from __future__ import annotations

import os
from typing import Dict

import counterfeit

CUR_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data", "currency")
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")
EXTS = (".jpg", ".jpeg", ".png")


def _scan(denom_dir: str):
    for f in sorted(os.listdir(denom_dir)):
        if f.lower().endswith(EXTS):
            yield os.path.join(denom_dir, f)


def run() -> Dict:
    per_denom = {}
    total = genuine = suspect = counterfeit_ct = 0
    score_sum = 0

    if os.path.isdir(CUR_DIR):
        for denom in sorted(os.listdir(CUR_DIR),
                            key=lambda x: int(x) if x.isdigit() else 0):
            dd = os.path.join(CUR_DIR, denom)
            if not (os.path.isdir(dd) and denom.isdigit()):
                continue
            n = g = s = c = 0
            ssum = 0
            for path in _scan(dd):
                r = counterfeit.analyze_image(open(path, "rb").read(), int(denom))
                n += 1
                ssum += r.authenticity_score
                g += r.verdict == "GENUINE"
                s += r.verdict == "SUSPECT"
                c += r.verdict == "COUNTERFEIT"
            if n:
                per_denom[denom] = {
                    "samples": n,
                    "mean_score": round(ssum / n, 1),
                    "genuine": g, "suspect": s, "counterfeit": c,
                    "false_rejections": c,  # genuine notes wrongly called fake
                }
                total += n; genuine += g; suspect += s; counterfeit_ct += c
                score_sum += ssum

    pct = lambda x: round(x * 100, 1)
    overall = {
        "denominations": len(per_denom),
        "total_genuine_notes": total,
        "mean_authenticity": round(score_sum / total, 1) if total else 0,
        "cleared_genuine": genuine,
        "flagged_for_review": suspect,
        "false_rejections": counterfeit_ct,
        "false_rejection_rate": pct(counterfeit_ct / total) if total else 0,
        "genuine_acceptance_rate": pct((total - counterfeit_ct) / total) if total else 0,
        "full_clearance_rate": pct(genuine / total) if total else 0,
    }

    # Synthetic print-quality stress test (legal stand-in for a degraded fake).
    fake = None
    fp = os.path.join(SAMPLE_DIR, "counterfeit_500.png")
    if os.path.exists(fp):
        fr = counterfeit.analyze_image(open(fp, "rb").read(), 500)
        fake = {"verdict": fr.verdict, "score": fr.authenticity_score,
                "detected": fr.verdict == "COUNTERFEIT"}

    return {
        "source": "Genuine RBI Mahatma Gandhi New Series notes (Wikimedia Commons)",
        "per_denomination": per_denom,
        "overall": overall,
        "fake_stress_test": fake,
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    r = run()
    o = r["overall"]
    print(f"Genuine reference notes: {o['total_genuine_notes']} across "
          f"{o['denominations']} denominations")
    print(f"Genuine-acceptance {o['genuine_acceptance_rate']}%  "
          f"(false-rejection {o['false_rejection_rate']}%)  "
          f"full-clearance {o['full_clearance_rate']}%  "
          f"mean authenticity {o['mean_authenticity']}")
    print("Per denomination:")
    for d, v in r["per_denomination"].items():
        print(f"  ₹{d:<4} n={v['samples']} mean={v['mean_score']:5}  "
              f"GENUINE={v['genuine']} SUSPECT={v['suspect']} "
              f"COUNTERFEIT={v['counterfeit']}")
    if r["fake_stress_test"]:
        f = r["fake_stress_test"]
        print(f"Fake stress test (synthetic): {f['verdict']} ({f['score']}) "
              f"-> {'detected' if f['detected'] else 'MISSED'}")
