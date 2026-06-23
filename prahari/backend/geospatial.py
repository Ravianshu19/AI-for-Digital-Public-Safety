"""
Geospatial Crime Pattern Intelligence
=====================================

Lightweight geospatial analytics over crime points: hotspot ranking, grid-based
density (a proxy for kernel-density heatmapping), and patrol-priority scoring for
a command-centre view.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, List


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
