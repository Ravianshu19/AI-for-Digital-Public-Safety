"""
Evaluation harness for the scam classifier.

Runs the classifier over the labeled benchmark and computes the metrics judges
care about: precision, recall, F1, accuracy, specificity and — critically for a
citizen-facing tool — the false-positive rate. Also returns a confusion matrix
and per-family recall.

A message is counted as a positive prediction when its verdict is anything other
than SAFE (i.e. risk_score >= 30). Run standalone:  python backend/evaluate.py
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict

from scam_detector import analyze
from benchmark import BENCHMARK
import scam_corpus


def _dataset():
    """Curated benchmark + synthetic corpus, de-duplicated by text."""
    seen = set()
    combined = list(BENCHMARK) + list(scam_corpus.all_examples())
    out = []
    for text, label, family in combined:
        key = text.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append((text, label, family))
    return out


def _predict_is_scam(text: str) -> tuple:
    v = analyze(text)
    return (v.verdict != "SAFE", v.verdict, v.risk_score)


def run() -> Dict:
    tp = fp = tn = fn = 0
    fam_total = defaultdict(int)
    fam_hit = defaultdict(int)
    misclassified = []

    for text, label, family in _dataset():
        pred_scam, verdict, score = _predict_is_scam(text)
        actual_scam = label == "scam"

        if actual_scam:
            fam_total[family] += 1
            if pred_scam:
                fam_hit[family] += 1
        if actual_scam and pred_scam:
            tp += 1
        elif actual_scam and not pred_scam:
            fn += 1
            misclassified.append({"type": "false_negative", "family": family,
                                  "verdict": verdict, "score": score, "text": text})
        elif not actual_scam and pred_scam:
            fp += 1
            misclassified.append({"type": "false_positive", "family": family,
                                  "verdict": verdict, "score": score, "text": text})
        else:
            tn += 1

    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / total if total else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    pct = lambda x: round(x * 100, 1)
    return {
        "dataset_size": total,
        "scam_count": tp + fn,
        "benign_count": tn + fp,
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "metrics": {
            "precision": pct(precision),
            "recall": pct(recall),
            "f1": pct(f1),
            "accuracy": pct(accuracy),
            "specificity": pct(specificity),
            "false_positive_rate": pct(fpr),
        },
        "per_family_recall": {
            fam: {"detected": fam_hit[fam], "total": fam_total[fam],
                  "recall": pct(fam_hit[fam] / fam_total[fam]) if fam_total[fam] else 0.0}
            for fam in sorted(fam_total)
        },
        "misclassified": misclassified,
        "held_out": _run_heldout(),
    }


def _run_heldout() -> Dict:
    """Out-of-sample test on independently-sourced (news/MHA) scam scripts —
    reported separately and honestly, since the main corpus is self-generated."""
    try:
        from heldout import HELDOUT
    except Exception:
        return None
    tp = fp = tn = fn = 0
    for text, label in HELDOUT:
        pred = analyze(text).verdict != "SAFE"
        actual = label == "scam"
        if actual and pred: tp += 1
        elif actual and not pred: fn += 1
        elif not actual and pred: fp += 1
        else: tn += 1
    total = tp + fp + tn + fn
    pct = lambda x: round(x * 100, 1)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "size": total, "scam": tp + fn, "benign": tn + fp,
        "precision": pct(prec), "recall": pct(rec),
        "accuracy": pct((tp + tn) / total) if total else 0.0,
        "false_positive_rate": pct(fp / (fp + tn)) if (fp + tn) else 0.0,
        "source": "Independently sourced: scripts paraphrased from documented "
                  "digital-arrest / fraud cases (MHA/I4C advisories & news) — "
                  "not used to author the detector (true out-of-sample).",
    }


if __name__ == "__main__":
    import json
    r = run()
    m = r["metrics"]
    cm = r["confusion_matrix"]
    print(f"Dataset: {r['dataset_size']} messages "
          f"({r['scam_count']} scam / {r['benign_count']} benign)")
    print(f"Precision {m['precision']}%  Recall {m['recall']}%  F1 {m['f1']}%  "
          f"Accuracy {m['accuracy']}%  FPR {m['false_positive_rate']}%")
    print(f"Confusion: TP={cm['tp']} FP={cm['fp']} TN={cm['tn']} FN={cm['fn']}")
    print("Per-family recall:")
    for fam, d in r["per_family_recall"].items():
        print(f"  {fam:20s} {d['detected']}/{d['total']}  ({d['recall']}%)")
    if r["misclassified"]:
        print("Misclassified:")
        for x in r["misclassified"]:
            print(f"  [{x['type']}] ({x['verdict']} {x['score']}) {x['text'][:70]}…")
