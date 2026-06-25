"""
Real India UPI fraud intelligence — aggregates over the Kaggle dataset
"UPI Digital Payment Fraud in India (FY2023–FY2025)" (1,000 real-shaped cases).

The data is transaction/case level (receivers are ~all unique → no shared-mule
rings), so we surface it as real **aggregate intelligence** (fraud type, lure,
UPI app, state, ₹ loss, OTP-shared & recovery rates) rather than a network graph.
"""

from __future__ import annotations

import csv
import glob
import os
from collections import Counter
from typing import Dict, List

_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "..", "sample_data", "india_upi", "*.csv"),
    os.path.expanduser("~/.cache/kagglehub/datasets/aishricadhiman/upi-fraud-dataset/versions/*/*.csv"),
]


def _csv():
    for pat in _CANDIDATES:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[0]
    return None


def available() -> bool:
    return _csv() is not None


def _top(rows, key, n=8) -> List[Dict]:
    c = Counter(r[key] for r in rows if r.get(key))
    return [{"label": k, "count": v} for k, v in c.most_common(n)]


def stats() -> Dict:
    path = _csv()
    if not path:
        return {"available": False}
    with open(path) as f:
        rows = [r for r in csv.DictReader(f) if r.get("is_fraud") == "1"]
    n = len(rows)
    if not n:
        return {"available": False}
    total_loss = sum(int(r["amount_inr"]) for r in rows if r["amount_inr"].isdigit())
    otp_shared = sum(1 for r in rows if r.get("pin_otp_shared") == "Yes")
    recovered = sum(1 for r in rows if r.get("recovery_status") == "Fully Recovered")
    reported = sum(1 for r in rows if r.get("reported_to_cybercrime_portal") == "Yes")
    pct = lambda a: round(100 * a / n, 1)
    return {
        "available": True,
        "source": "Kaggle — UPI Digital Payment Fraud in India (FY2023–FY2025)",
        "cases": n,
        "total_loss_inr": total_loss,
        "total_loss_str": f"₹{total_loss/10000000:.2f} cr",
        "avg_loss_inr": int(total_loss / n),
        "otp_shared_pct": pct(otp_shared),
        "recovery_pct": pct(recovered),
        "reported_pct": pct(reported),
        "by_fraud_type": _top(rows, "fraud_type"),
        "by_lure": _top(rows, "fraud_lure"),
        "by_app": _top(rows, "upi_app"),
        "by_state": _top(rows, "victim_state", 8),
        "by_age": _top(rows, "victim_age_group", 6),
    }


if __name__ == "__main__":
    s = stats()
    if not s.get("available"):
        print("Dataset missing — run sample_data/fetch_india_upi.py")
    else:
        print(f"{s['source']}: {s['cases']} cases, {s['total_loss_str']} lost")
        print("OTP shared:", s["otp_shared_pct"], "% | recovered:", s["recovery_pct"], "%")
        print("Top fraud types:", [(x["label"], x["count"]) for x in s["by_fraud_type"][:5]])
        print("Top lures:", [(x["label"], x["count"]) for x in s["by_lure"][:5]])
