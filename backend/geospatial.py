"""
Geospatial Crime Pattern Intelligence
=====================================

Lightweight geospatial analytics over crime points: hotspot ranking, grid-based
density (a proxy for kernel-density heatmapping), and patrol-priority scoring for
a command-centre view.
"""

from __future__ import annotations

import csv
import math
import os
from collections import defaultdict
from typing import Dict, List

NCRB_CSV = os.path.join(os.path.dirname(__file__), "..", "sample_data",
                        "ncrb_cybercrime_2022.csv")
MOTIVE_CSV = os.path.join(os.path.dirname(__file__), "..", "sample_data",
                          "cybercrime_india", "cybercrime_by_city_motive.csv")


def cybercrime_motives() -> Dict:
    """Real city-level cybercrime by motive (NCRB via Kaggle) — national motive
    breakdown + top cybercrime cities."""
    if not os.path.exists(MOTIVE_CSV):
        return {"available": False}
    motive_tot = defaultdict(float)
    cities = []
    with open(MOTIVE_CSV, encoding="latin-1") as f:
        reader = csv.DictReader(f)
        cols = [c for c in reader.fieldnames if c not in ("City", "Total")]
        for r in reader:
            city = (r.get("City") or "").strip()
            cl = city.lower()
            # skip NCRB aggregate rows (Total All India / Total State(s) / etc.)
            if not city or "total" in cl or "all india" in cl or "state(s)" in cl:
                continue
            try:
                total = float(r.get("Total") or 0)
            except ValueError:
                total = 0
            cities.append({"city": city, "total": int(total)})
            for c in cols:
                try:
                    motive_tot[c] += float(r.get(c) or 0)
                except ValueError:
                    pass
    by_motive = sorted(
        ({"label": k, "count": int(v)} for k, v in motive_tot.items() if v > 0),
        key=lambda x: x["count"], reverse=True)
    top_cities = sorted(cities, key=lambda x: x["total"], reverse=True)[:10]
    return {
        "available": True,
        "source": "NCRB city-level cybercrime by motive (Kaggle dataset-cybercrime-in-india)",
        "cities_covered": len(cities),
        "total_cases": int(sum(c["total"] for c in cities)),
        "by_motive": by_motive,
        "top_cities": top_cities,
    }


def state_stats() -> Dict:
    """Load real state-level cybercrime counts (NCRB 'Crime in India' 2022).

    Schema-driven (state,lat,lon,cyber_cases_2022) — swap in the official CSV from
    https://data.gov.in / https://ncrb.gov.in to refresh.
    """
    rows = []
    if os.path.exists(NCRB_CSV):
        with open(NCRB_CSV) as f:
            for r in csv.DictReader(f):
                try:
                    rows.append({
                        "state": r["state"],
                        "lat": float(r["lat"]), "lon": float(r["lon"]),
                        "cases": int(r["cyber_cases_2022"]),
                    })
                except Exception:
                    continue
    rows.sort(key=lambda x: x["cases"], reverse=True)
    total = sum(r["cases"] for r in rows)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        r["share_pct"] = round(100 * r["cases"] / total, 1) if total else 0
    return {
        "source": "NCRB — Crime in India 2022 (cyber crimes by state) · Data.gov.in",
        "year": 2022,
        "total_cases": total,
        "states": rows,
    }


TYPE_WEIGHT = {
    "digital_arrest": 1.4,   # highest harm per incident
    "scam_compound": 1.5,    # source infrastructure
    "cyber_fraud": 1.0,
    "ficn_seizure": 1.1,
}


def _haversine(a, b) -> float:
    R = 6371.0
    dlat = math.radians(b[0] - a[0])
    dlon = math.radians(b[1] - a[1])
    x = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0]))
         * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(x))


def analyze(points: List[Dict]) -> Dict:
    # Hotspot score per point = own intensity*typeweight + neighbour contribution.
    hotspots = []
    for p in points:
        base = p["intensity"] * TYPE_WEIGHT.get(p["type"], 1.0)
        neigh = 0.0
        for q in points:
            if q is p:
                continue
            d = _haversine((p["lat"], p["lon"]), (q["lat"], q["lon"]))
            if d < 400:  # within 400 km influence radius
                neigh += q["intensity"] * TYPE_WEIGHT.get(q["type"], 1.0) * (1 - d / 400)
        score = round(base + 0.3 * neigh, 1)
        hotspots.append({**p, "hotspot_score": score})

    hotspots.sort(key=lambda h: h["hotspot_score"], reverse=True)

    # Patrol priority = top hotspots (excluding foreign source compounds).
    patrol = [
        {
            "rank": i + 1,
            "location": h["label"],
            "score": h["hotspot_score"],
            "dominant_threat": h["type"].replace("_", " "),
            "recommended_units": max(1, int(h["hotspot_score"] / 4)),
        }
        for i, h in enumerate(
            [h for h in hotspots if h["type"] != "scam_compound"]
        )
    ][:6]

    by_type = defaultdict(int)
    for p in points:
        by_type[p["type"]] += 1

    return {
        "summary": {
            "total_points": len(points),
            "by_type": dict(by_type),
            "top_hotspot": hotspots[0]["label"] if hotspots else None,
        },
        "hotspots": hotspots,
        "patrol_priority": patrol,
    }
