"""
External real-data validation of the scam classifier.

Runs the classifier over the UCI SMS Spam Collection (5,574 real English SMS).
The headline metric is the **false-positive rate on the 4,827 genuine (ham)
messages** — a real-data check of the citizen-safety claim. Recall on this corpus
is reported too but is out-of-domain (generic UK premium-SMS spam vs. the Indian
scam families this model targets), so it should not be read as the model's recall.
"""

from __future__ import annotations

import io
import os
from typing import Dict

from scam_detector import analyze

SMS = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sms_spam",
                   "SMSSpamCollection")


def available() -> bool:
    return os.path.exists(SMS)


def run() -> Dict:
    if not available():
        return {"available": False}
    ham = spam = ham_flagged = spam_caught = 0
    with io.open(SMS, encoding="latin-1") as f:
        for line in f:
            if "\t" not in line:
                continue
            label, text = line.split("\t", 1)
            flagged = analyze(text).verdict != "SAFE"
            if label == "ham":
                ham += 1
                ham_flagged += flagged
            elif label == "spam":
                spam += 1
                spam_caught += flagged
    pct = lambda a, b: round(100 * a / b, 2) if b else 0
    return {
        "available": True,
        "source": "UCI SMS Spam Collection (Almeida et al., 2011) — 5,574 real SMS",
        "ham_total": ham,
        "spam_total": spam,
        "false_positives": ham_flagged,
        "false_positive_rate": pct(ham_flagged, ham),
        "out_of_domain_recall": pct(spam_caught, spam),
        "note": ("FPR on real legitimate SMS validates the citizen-safety claim. "
                 "Recall here is out-of-domain (generic UK SMS spam ≠ Indian scam "
                 "families); see the in-domain benchmark for true recall."),
    }


if __name__ == "__main__":
    r = run()
    if not r["available"]:
        print("Dataset missing. See sample_data/sms_spam/SOURCE.md")
    else:
        print(f"{r['source']}")
        print(f"False-positive rate on {r['ham_total']} real ham: "
              f"{r['false_positives']} → {r['false_positive_rate']}%")
        print(f"Out-of-domain recall on {r['spam_total']} spam: {r['out_of_domain_recall']}%")
