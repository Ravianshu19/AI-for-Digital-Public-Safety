"""
Convert the Kaggle PaySim dataset into Indian-context fraud-graph records.

PaySim simulates mobile-money transactions with a fraud label. We relabel it to
the Indian payments stack (UPI / wallet / bank / crypto exit) so the same graph
engine (community detection + lead-time) runs on a public, real-shaped dataset.

PaySim columns: step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,
                nameDest,oldbalanceDest,newbalanceDest,isFraud,isFlaggedFraud

Usage (after sample_data/fetch_kaggle.py has downloaded it):
    from kaggle_fraud import load_paysim_records
    records = load_paysim_records(limit=300)   # -> feed fraud_graph.analyze(records)
"""

from __future__ import annotations

import csv
import glob
import os
from typing import Dict, List

# PaySim CSV can live in the repo's sample_data/kaggle/ or the kagglehub cache.
_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "..", "sample_data", "kaggle", "*.csv"),
    os.path.expanduser("~/.cache/kagglehub/datasets/ealaxi/paysim1/versions/*/*.csv"),
]


def _find_csv():
    for pat in _CANDIDATES:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[0]
    return None


PAYSIM = _find_csv()

# PaySim cash-out / transfer types → Indian rails
RAIL = {"TRANSFER": "upi_transfer", "CASH_OUT": "transfer",
        "PAYMENT": "upi_transfer", "DEBIT": "transfer", "CASH_IN": "upi_transfer"}


def available() -> bool:
    return _find_csv() is not None


def load_paysim_records(limit: int = 60, fraud_only: bool = True) -> List[Dict]:
    """Return fraud_graph-style edges from PaySim, relabelled to UPI/bank context.

    Default limit is small so the resulting graph stays legible in the dashboard;
    raise it for analytics runs.
    """
    csv_path = _find_csv()
    if not csv_path:
        return []
    out = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            if fraud_only and row.get("isFraud") != "1":
                continue
            orig, dest = row["nameOrig"], row["nameDest"]
            # PaySim 'C' = customer (UPI), 'M' = merchant (wallet)
            src = f"upi:{orig}" if orig.startswith("C") else f"wallet:{orig}"
            dst = (f"crypto:{dest}" if row["type"] == "CASH_OUT"
                   else (f"upi:{dest}" if dest.startswith("C") else f"wallet:{dest}"))
            out.append({
                "src": src, "dst": dst,
                "type": RAIL.get(row["type"], "transfer"),
                "amount": int(float(row["amount"])),
                # PaySim 'step' is an hour index; fold to a date for the lead-time KPI.
                "ts": f"2025-06-{1 + (int(row['step']) % 28):02d}",
            })
            if len(out) >= limit:
                break
    return out


if __name__ == "__main__":
    if not available():
        print("PaySim not found. Run sample_data/fetch_kaggle.py first (needs a Kaggle token).")
    else:
        recs = load_paysim_records()
        print(f"Loaded {len(recs)} Indian-context fraud edges from PaySim.")
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        import fraud_graph
        res = fraud_graph.analyze(recs)
        print("Campaigns:", res["summary"]["campaigns_detected"],
              "| modularity:", res["summary"]["modularity_score"])
