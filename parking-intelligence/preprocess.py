"""
ParkSight — Parking Congestion Intelligence
Data engine: turns raw Bengaluru parking-enforcement records into compact,
demo-ready aggregates.

Input  : the anonymised police-violation CSV (298k rows, Nov-2023 -> Apr-2024).
Output : data/aggregates.json  — heatmap grid, ranked enforcement zones,
         congestion-impact scores, temporal patterns and city KPIs.

Design notes
------------
* No pandas dependency — pure stdlib so it runs anywhere the demo runs.
* "Congestion impact" is *modelled*, not measured: this dataset has no traffic
  speed/flow feed, so every violation is weighted by how much it chokes a
  carriageway (a main-road block hurts flow far more than a footpath scooter).
  The weights live in IMPACT_WEIGHTS and are shown in the UI so the model is
  transparent, not a black box.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "aggregates.json")

# Default location of the raw CSV (overridable via argv[1]).
DEFAULT_CSV = os.path.expanduser(
    "~/Downloads/jan to may police violation_anonymized791b166.csv"
)

IST = timezone(timedelta(hours=5, minutes=30))

# ---------------------------------------------------------------------------
# Congestion-impact model
# ---------------------------------------------------------------------------
# How much each violation type obstructs moving traffic. Higher = worse choke.
# Footpath/number-plate/fare offences barely touch the carriageway; main-road,
# junction and double parking are the real flow killers.
IMPACT_WEIGHTS = {
    "PARKING IN A MAIN ROAD": 5.0,
    "DOUBLE PARKING": 4.5,
    "PARKING NEAR ROAD CROSSING": 4.0,
    "PARKING NEAR TRAFFIC LIGHT OR ZEBRA CROSS": 4.0,
    "PARKING OPPOSITE TO ANOTHER PARKED VEHICLE": 3.5,
    "PARKING NEAR BUSTOP/SCHOOL/HOSPITAL ETC": 3.0,
    "NO PARKING": 3.0,
    "PARKING OTHER THAN BUS STOP": 2.5,
    "WRONG PARKING": 2.0,
    "PARKING ON FOOTPATH": 1.5,       # blocks pedestrians, not the carriageway
    "AGAINST ONE WAY/NO ENTRY": 3.0,
    "OBSTRUCTING DRIVER": 3.0,
    "H T V PROHIBITED": 2.5,
}
DEFAULT_WEIGHT = 1.0  # number-plate/fare/helmet etc. — negligible flow impact

# Grid cell ~150 m. At ~13 deg N, 0.0015 deg lat ~= 165 m, lon ~= 162 m.
CELL = 0.0015


def impact_of(vtypes):
    return sum(IMPACT_WEIGHTS.get(v, DEFAULT_WEIGHT) for v in vtypes)


def parse_dt_ist(raw):
    if not raw or raw == "NULL":
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("+00", "+00:00"))
        return dt.astimezone(IST)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Forecasting + coverage helpers  (pure stdlib, transparent models)
# ---------------------------------------------------------------------------
def _linreg(ys):
    """Ordinary least-squares slope/intercept over x = 0..n-1."""
    n = len(ys)
    if n < 2:
        return 0.0, (ys[0] if ys else 0.0)
    mx = (n - 1) / 2.0
    my = sum(ys) / n
    den = sum((i - mx) ** 2 for i in range(n)) or 1.0
    slope = sum((i - mx) * (ys[i] - my) for i in range(n)) / den
    return slope, my - slope * mx


def _std(v):
    n = len(v)
    if n < 2:
        return 0.0
    m = sum(v) / n
    return (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5


def forecast_daily(series, horizon=7, dow_window=56):
    """Forecast a daily series = linear trend × multiplicative weekday
    seasonality, with an 80% prediction interval from the residual spread.

    This is a genuine (if lightweight) statistical model — not a flat average:
    it learns the trend and the seven weekday factors from history, so a
    forecast Saturday differs from a forecast Tuesday. Returns the last 28 days
    of history plus `horizon` forecast points (mean/lo/hi).
    """
    dates = sorted(series)
    if len(dates) < 14:
        return None
    vals = [series[d] for d in dates]
    n = len(vals)
    slope, intercept = _linreg(vals)
    trend = [intercept + slope * i for i in range(n)]

    recent = range(max(0, n - dow_window), n)
    fv, ft = defaultdict(list), defaultdict(list)
    for i in recent:
        wd = datetime.fromisoformat(dates[i]).weekday()
        fv[wd].append(vals[i])
        ft[wd].append(max(trend[i], 1e-6))
    factor = {wd: (sum(fv[wd]) / len(fv[wd])) / (sum(ft[wd]) / len(ft[wd]))
              for wd in fv}

    resid = [vals[i] - trend[i] * factor.get(
                 datetime.fromisoformat(dates[i]).weekday(), 1.0)
             for i in recent]
    sigma = _std(resid)

    last = datetime.fromisoformat(dates[-1])
    fc = []
    for h in range(1, horizon + 1):
        d = last + timedelta(days=h)
        i = n - 1 + h
        f = max(0.0, (intercept + slope * i) * factor.get(d.weekday(), 1.0))
        fc.append({"date": d.date().isoformat(), "dow": d.strftime("%a"),
                   "mean": round(f),
                   "lo": round(max(0.0, f - 1.2816 * sigma)),
                   "hi": round(f + 1.2816 * sigma)})

    recent_mean = (sum(vals[-28:]) / min(28, n)) or 1.0
    tail = [{"date": dates[i], "value": vals[i],
             "dow": datetime.fromisoformat(dates[i]).strftime("%a")}
            for i in range(max(0, n - 28), n)]
    return {
        "history": tail,
        "forecast": fc,
        "weekly_trend_pct": round(slope * 7 / recent_mean * 100, 1),
        "sigma": round(sigma),
    }


def main(csv_path):
    if not os.path.exists(csv_path):
        sys.exit(f"CSV not found: {csv_path}")

    cells = defaultdict(lambda: {
        "n": 0, "impact": 0.0, "lat": 0.0, "lon": 0.0,
        "vio": defaultdict(int), "hour": defaultdict(int),
    })
    zones = defaultdict(lambda: {
        "n": 0, "impact": 0.0, "high": 0,
        "vio": defaultdict(int), "hour": defaultdict(int),
        "veh": defaultdict(int), "junc": defaultdict(int),
        "lat": 0.0, "lon": 0.0, "geo_n": 0,
    })
    vio_total = defaultdict(int)
    veh_total = defaultdict(int)
    hour_total = defaultdict(int)   # by IST hour
    dow_total = defaultdict(int)    # by IST weekday
    month_total = defaultdict(int)
    daily_all = defaultdict(int)    # date -> all violations (for the forecast)
    zone_daily = defaultdict(lambda: defaultdict(int))  # zone -> date -> count

    total = 0
    high_impact = 0          # main-road / junction / double etc.
    footpath = 0
    dt_min = dt_max = None

    HIGH = {"PARKING IN A MAIN ROAD", "DOUBLE PARKING",
            "PARKING NEAR ROAD CROSSING",
            "PARKING NEAR TRAFFIC LIGHT OR ZEBRA CROSS",
            "PARKING NEAR BUSTOP/SCHOOL/HOSPITAL ETC"}

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            total += 1
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
            except (TypeError, ValueError):
                lat = lon = None

            try:
                vtypes = json.loads(row.get("violation_type") or "[]")
            except Exception:
                vtypes = []
            impact = impact_of(vtypes)
            is_high = any(v in HIGH for v in vtypes)
            for v in vtypes:
                vio_total[v] += 1

            veh = (row.get("vehicle_type") or "UNKNOWN").strip() or "UNKNOWN"
            veh_total[veh] += 1

            dt = parse_dt_ist(row.get("created_datetime"))
            hr = dt.hour if dt else None
            dd = None
            if dt:
                hour_total[dt.hour] += 1
                dow_total[dt.strftime("%a")] += 1
                month_total[dt.strftime("%Y-%m")] += 1
                dd = dt.date().isoformat()
                daily_all[dd] += 1
                dt_min = dt if dt_min is None else min(dt_min, dt)
                dt_max = dt if dt_max is None else max(dt_max, dt)

            if is_high:
                high_impact += 1
            if "PARKING ON FOOTPATH" in vtypes:
                footpath += 1

            # --- grid cell ---
            if lat is not None:
                gx = round(lat / CELL) * CELL
                gy = round(lon / CELL) * CELL
                c = cells[(gx, gy)]
                c["n"] += 1
                c["impact"] += impact
                c["lat"] += lat
                c["lon"] += lon
                for v in vtypes:
                    c["vio"][v] += 1
                if hr is not None:
                    c["hour"][hr] += 1

            # --- police-station zone ---
            ps = (row.get("police_station") or "Unknown").strip() or "Unknown"
            z = zones[ps]
            z["n"] += 1
            z["impact"] += impact
            if dd:
                zone_daily[ps][dd] += 1
            if is_high:
                z["high"] += 1
            for v in vtypes:
                z["vio"][v] += 1
            z["veh"][veh] += 1
            if hr is not None:
                z["hour"][hr] += 1
            junc = (row.get("junction_name") or "").strip()
            if junc and junc != "No Junction":
                z["junc"][junc] += 1
            if lat is not None:
                z["lat"] += lat
                z["lon"] += lon
                z["geo_n"] += 1

    # -------- build heatmap points (one weighted point per cell) --------
    heat = []
    max_cell_impact = max((c["impact"] for c in cells.values()), default=1.0)
    for (gx, gy), c in cells.items():
        if c["n"] < 2:            # drop lone points — noise, keeps payload small
            continue
        dom = max(c["vio"].items(), key=lambda kv: kv[1])[0] if c["vio"] else ""
        peak = max(c["hour"].items(), key=lambda kv: kv[1])[0] if c["hour"] else None
        heat.append({
            "lat": round(c["lat"] / c["n"], 5),
            "lon": round(c["lon"] / c["n"], 5),
            "n": c["n"],
            "impact": round(c["impact"], 1),
            "w": round(c["impact"] / max_cell_impact, 3),   # 0..1 for heat layer
            "dom": dom,
            "peak": peak,
        })
    heat.sort(key=lambda h: h["impact"], reverse=True)

    # -------- top individual hotspots (for the "worst spots" list) --------
    top_spots = [{
        "rank": i + 1,
        "lat": h["lat"], "lon": h["lon"],
        "count": h["n"], "impact": h["impact"],
        "dominant": h["dom"],
        "peak_hour": h["peak"],
    } for i, h in enumerate(heat[:25])]

    # -------- ranked enforcement zones --------
    zlist = []
    for name, z in zones.items():
        dom = max(z["vio"].items(), key=lambda kv: kv[1])[0] if z["vio"] else ""
        peak = max(z["hour"].items(), key=lambda kv: kv[1])[0] if z["hour"] else None
        topveh = max(z["veh"].items(), key=lambda kv: kv[1])[0] if z["veh"] else ""
        top_junc = sorted(z["junc"].items(), key=lambda kv: kv[1], reverse=True)[:3]
        zlist.append({
            "zone": name,
            "count": z["n"],
            "impact": round(z["impact"], 1),
            "impact_per": round(z["impact"] / z["n"], 2) if z["n"] else 0,
            "high_impact": z["high"],
            "high_pct": round(100 * z["high"] / z["n"], 1) if z["n"] else 0,
            "dominant": dom,
            "top_vehicle": topveh,
            "peak_hour": peak,
            "top_junctions": [{"name": n, "count": c} for n, c in top_junc],
            "lat": round(z["lat"] / z["geo_n"], 5) if z["geo_n"] else None,
            "lon": round(z["lon"] / z["geo_n"], 5) if z["geo_n"] else None,
        })
    zlist.sort(key=lambda z: z["impact"], reverse=True)
    for i, z in enumerate(zlist):
        z["rank"] = i + 1

    # -------- recommended enforcement windows (top zones) --------
    # a 2-hour deployment window = the peak hour + neighbour with most load.
    recs = []
    for z in zlist[:8]:
        zh = zones[z["zone"]]["hour"]
        if not zh:
            continue
        best_start, best_load = 0, -1
        for h in range(24):
            load = zh.get(h, 0) + zh.get((h + 1) % 24, 0)
            if load > best_load:
                best_load, best_start = load, h
        recs.append({
            "zone": z["zone"],
            "window": f"{best_start:02d}:00–{(best_start + 2) % 24:02d}:00",
            "window_load": best_load,
            "share": round(100 * best_load / z["count"], 1) if z["count"] else 0,
            "dominant": z["dominant"],
        })

    # -------- enforcement coverage vs. effort curve --------
    # Greedily deploy to the zones with the most high-impact violations first;
    # trace how much of the city's high-impact load you cover as you add zones.
    # This turns the ranking into a decision tool: "cover X% for Y% of effort".
    zc = sorted(zlist, key=lambda z: z["high_impact"], reverse=True)
    n_zones = len(zc) or 1
    total_high = sum(z["high_impact"] for z in zc) or 1
    total_all = sum(z["count"] for z in zc) or 1
    curve, ch, ca = [{"k": 0, "effort_pct": 0.0, "cov_high": 0.0, "cov_all": 0.0}], 0, 0
    for i, z in enumerate(zc, 1):
        ch += z["high_impact"]
        ca += z["count"]
        curve.append({
            "k": i, "zone": z["zone"],
            "effort_pct": round(100 * i / n_zones, 1),
            "cov_high": round(100 * ch / total_high, 1),
            "cov_all": round(100 * ca / total_all, 1),
        })

    def _zones_for(pct):
        acc = 0
        for i, z in enumerate(zc, 1):
            acc += z["high_impact"]
            if 100 * acc / total_high >= pct:
                return i
        return n_zones

    coverage = {
        "curve": curve,
        "total_zones": n_zones,
        "total_high": total_high,
        "markers": {str(p): {"zones": _zones_for(p),
                             "effort_pct": round(100 * _zones_for(p) / n_zones, 1)}
                    for p in (50, 70, 80, 90)},
    }

    # -------- 7-day city-wide forecast --------
    forecast = forecast_daily(daily_all, horizon=7)

    # -------- per-zone "rising hotspots" --------
    # Momentum = last-14-day daily rate vs the prior 14 days, on total zone
    # activity (a dense, stable signal). Predicted next-week load = recent
    # 28-day daily average × 7 (seasonal-naive level) rather than extrapolating
    # a per-zone trend line, which is too volatile on one zone.
    zone_forecast = []
    for z in zlist[:20]:
        s = zone_daily.get(z["zone"], {})
        if len(s) < 28:
            continue
        dates = sorted(s)
        vals = [s[d] for d in dates]
        last14 = sum(vals[-14:])
        prev14 = sum(vals[-28:-14]) or 1
        mean28 = sum(vals[-28:]) / min(28, len(vals))
        momentum = round(100 * (last14 - prev14) / prev14, 1)
        zone_forecast.append({
            "zone": z["zone"], "rank": z["rank"],
            "pred_next7": round(mean28 * 7),
            "momentum_pct": momentum,
            "trend": "rising" if momentum >= 8 else
                     "falling" if momentum <= -8 else "steady",
        })
    # display by predicted load (the operationally important zones); the trend
    # badge surfaces risers without letting noisy low-volume zones lead.
    zone_forecast.sort(key=lambda x: x["pred_next7"], reverse=True)

    aggregates = {
        "meta": {
            "source_rows": total,
            "date_from": dt_min.strftime("%Y-%m-%d") if dt_min else None,
            "date_to": dt_max.strftime("%Y-%m-%d") if dt_max else None,
            "generated": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
            "cell_metres": int(CELL * 111000),
            "impact_weights": IMPACT_WEIGHTS,
            "note": "Congestion impact is modelled from violation type + density; "
                    "this dataset has no live traffic-speed feed.",
        },
        "kpis": {
            "total_violations": total,
            "high_impact_violations": high_impact,
            "high_impact_pct": round(100 * high_impact / total, 1),
            "footpath_violations": footpath,
            "distinct_hotspot_cells": len(heat),
            "worst_zone": zlist[0]["zone"] if zlist else None,
            "worst_zone_impact": zlist[0]["impact"] if zlist else None,
            "peak_hour": max(hour_total.items(), key=lambda kv: kv[1])[0]
                         if hour_total else None,
            "total_impact_score": round(sum(z["impact"] for z in zlist), 0),
        },
        "violation_breakdown": sorted(
            [{"type": k, "count": v, "weight": IMPACT_WEIGHTS.get(k, DEFAULT_WEIGHT)}
             for k, v in vio_total.items()],
            key=lambda d: d["count"], reverse=True),
        "vehicle_breakdown": sorted(
            [{"type": k, "count": v} for k, v in veh_total.items()],
            key=lambda d: d["count"], reverse=True)[:12],
        "by_hour": [{"hour": h, "count": hour_total.get(h, 0)} for h in range(24)],
        "by_dow": [{"day": d, "count": dow_total.get(d, 0)}
                   for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]],
        "by_month": [{"month": m, "count": c}
                     for m, c in sorted(month_total.items())],
        "zones": zlist,
        "heat": heat,
        "top_spots": top_spots,
        "recommendations": recs,
        "coverage": coverage,
        "forecast": forecast,
        "zone_forecast": zone_forecast,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(aggregates, fh, separators=(",", ":"))

    kb = os.path.getsize(OUT) / 1024
    print(f"OK  {total:,} rows -> {len(heat):,} hotspot cells, "
          f"{len(zlist)} zones")
    print(f"    worst zone: {zlist[0]['zone']} "
          f"(impact {zlist[0]['impact']:,.0f}, "
          f"{zlist[0]['high_pct']}% high-impact)")
    m80 = coverage["markers"]["80"]
    print(f"    coverage: {m80['zones']} of {n_zones} zones "
          f"({m80['effort_pct']}% effort) cover 80% of high-impact violations")
    if forecast:
        nxt = sum(p["mean"] for p in forecast["forecast"])
        print(f"    forecast: next 7 days ~{nxt:,} violations "
              f"(weekly trend {forecast['weekly_trend_pct']:+}%)")
    print(f"    wrote {OUT}  ({kb:.0f} KB)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV)
