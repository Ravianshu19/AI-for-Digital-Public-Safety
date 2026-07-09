"""
ParkSight — Parking Congestion Intelligence API
================================================
Serves the pre-computed aggregates plus a live congestion-impact scorer so the
UI can explain *why* a spot ranks where it does. Pure-stdlib + FastAPI, no DB.

Run:  uvicorn backend.app:app --reload --port 8010   (from parking-intelligence/)
"""

from __future__ import annotations

import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "aggregates.json")
FRONTEND = os.path.join(ROOT, "frontend")

app = FastAPI(title="ParkSight — Parking Congestion Intelligence", version="1.0")

_cache = {}


def agg():
    """Load + cache aggregates (mtime-aware so a re-run of preprocess shows up)."""
    if not os.path.exists(DATA):
        raise HTTPException(503, "aggregates.json missing — run preprocess.py first")
    m = os.path.getmtime(DATA)
    if _cache.get("m") != m:
        with open(DATA, encoding="utf-8") as f:
            _cache["data"] = json.load(f)
        _cache["m"] = m
    return _cache["data"]


@app.get("/api/overview")
def overview():
    a = agg()
    return {
        "meta": a["meta"],
        "kpis": a["kpis"],
        "violation_breakdown": a["violation_breakdown"],
        "vehicle_breakdown": a["vehicle_breakdown"],
        "by_hour": a["by_hour"],
        "by_dow": a["by_dow"],
        "by_month": a["by_month"],
    }


@app.get("/api/zones")
def zones(limit: int = 55):
    return {"zones": agg()["zones"][:limit]}


@app.get("/api/heat")
def heat(limit: int = 4500):
    a = agg()
    return {"heat": a["heat"][:limit], "top_spots": a["top_spots"]}


@app.get("/api/recommendations")
def recommendations():
    return {"recommendations": agg()["recommendations"]}


@app.get("/api/coverage")
def coverage():
    return agg()["coverage"]


@app.get("/api/forecast")
def forecast():
    a = agg()
    return {"forecast": a["forecast"], "zone_forecast": a["zone_forecast"]}


@app.post("/api/score")
def score(payload: dict):
    """Live congestion-impact score for a hypothetical spot — makes the model
    interactive: pick violation types + a daily count, get an impact score and
    an enforcement-priority band using the same weights the rankings use."""
    a = agg()
    weights = a["meta"]["impact_weights"]
    default_w = 1.0
    vtypes = payload.get("violation_types", []) or []
    count = float(payload.get("daily_count", 0) or 0)
    per_event = sum(weights.get(v, default_w) for v in vtypes) or default_w
    impact = round(per_event * count, 1)
    # band thresholds tuned to the observed per-cell impact distribution
    if impact >= 2000:
        band, action = "CRITICAL", "Deploy tow + marshal daily in peak window"
    elif impact >= 800:
        band, action = "HIGH", "Scheduled enforcement 3–4x/week in peak window"
    elif impact >= 250:
        band, action = "MEDIUM", "Weekly patrol + signage / bollards review"
    else:
        band, action = "LOW", "Passive monitoring; citizen-report driven"
    return {
        "per_event_impact": round(per_event, 2),
        "impact_score": impact,
        "band": band,
        "recommended_action": action,
        "explain": [{"type": v, "weight": weights.get(v, default_w)} for v in vtypes],
    }


@app.get("/api/health")
def health():
    ok = os.path.exists(DATA)
    return {"ok": ok, "rows": agg()["meta"]["source_rows"] if ok else 0}


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND, "index.html"))


if os.path.isdir(FRONTEND):
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
