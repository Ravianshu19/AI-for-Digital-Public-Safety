# ParkSight — Parking Congestion Intelligence

**Problem:** on-street illegal parking near markets, metro stations and events
chokes carriageways, but enforcement is patrol-based and reactive — there is no
heatmap of parking violations vs. congestion impact, so it's hard to prioritise
enforcement zones.

**ParkSight** turns 298,450 real Bengaluru parking-enforcement records
(Nov 2023 → Apr 2024) into an AI-driven command centre that:

- **maps illegal-parking hotspots** as a weighted kernel-density heatmap,
- **quantifies congestion impact** by weighting every violation by how much its
  type chokes moving traffic (a main-road block hurts flow far more than a
  footpath scooter),
- **ranks enforcement-priority zones** and the worst individual spots,
- **recommends deployment windows** — the peak 2-hour block per top zone,
- **forecasts** the next 7 days of violations and flags which zones are heating up,
- **quantifies enforcement ROI** with a coverage-vs-effort curve,
- lets an officer **simulate** a hypothetical spot and get a priority band.

---

## Run it

Zero dependencies — the demo runs on a bare `python3` (stdlib only):

```bash
cd parking-intelligence
./run.sh                 # builds data/aggregates.json if missing, serves :8010
# open http://127.0.0.1:8010
```

Point it at a different CSV: `./run.sh /path/to/violations.csv`

The FastAPI version (identical API) is also available if you prefer uvicorn:

```bash
../.venv/bin/python -m uvicorn backend.app:app --port 8010   # needs fastapi+uvicorn
```

---

## How it works

```
raw CSV (298k rows)
   │   preprocess.py  — pure stdlib, no pandas
   ▼
data/aggregates.json  (~400 KB: heat grid, ranked zones, temporal, KPIs)
   │   serve.py (stdlib)  ·or·  backend/app.py (FastAPI)
   ▼
frontend/  — Leaflet heatmap + Chart.js, single-page command centre
```

### The congestion-impact model

This dataset has **no live traffic-speed feed**, so "impact on traffic flow" is
*modelled*, not measured — and the model is shown in the UI, not hidden. Each
violation is scored by how much its type obstructs the carriageway:

| Weight | Violation types |
|--------|-----------------|
| 5.0 | Parking in a main road |
| 4.5 | Double parking |
| 4.0 | Near road crossing / traffic light / zebra |
| 3.0 | No parking · near bus-stop/school/hospital · against one-way |
| 2.0 | Wrong parking |
| 1.5 | Parking on footpath (blocks pedestrians, not the carriageway) |
| 1.0 | Number plate / fare / helmet etc. (negligible flow impact) |

**Cell impact** = Σ(weight) over all violations in a ~166 m grid cell.
**Zone impact** = Σ(weight) over a police-station area.
The heatmap's intensity and the zone ranking are both driven by this score;
"Raw density" toggle shows unweighted counts for comparison.

### 7-day forecast (the predictive / AI layer)

`forecast_daily()` fits a **linear trend × multiplicative weekday-seasonality**
model to the daily violation series and projects 7 days ahead with an 80%
prediction interval (from the residual spread). It's a genuine statistical model,
not a flat average — a forecast Saturday differs from a forecast Tuesday because
the seven weekday factors are learned from history. Per zone, a **14-day
momentum** signal (last fortnight vs. the prior one) flags which areas are
heating up so patrols can be pre-positioned, with next-week load predicted from
the recent 28-day level.

### Enforcement coverage vs. effort

Greedily "deploy" to the highest-impact zones first and trace how much of the
city's high-impact load you cover as you add zones. The result is a decision
curve: **17 of 55 zones (31% of effort) cover 80% of all high-impact
violations** — the quantified case for targeted over patrol-based enforcement.

### What's real vs. modelled

- **Real (from the data):** every location, violation type, vehicle type,
  timestamp, police station and junction; all hotspot, zone, temporal and
  vehicle breakdowns.
- **Modelled (transparent heuristic):** the congestion-impact weights, the
  priority bands, and the recommended deployment windows.
- **Not in this dataset:** live vehicle speed / flow. A production version would
  fuse ParkSight scores with SCITA/ANPR speed feeds (86% of these records are
  already flagged `data_sent_to_scita`) to calibrate the weights against
  measured slowdowns.

---

## Headline findings

- **9.2%** of violations are high-impact (main-road / junction / double parking)
  — **27,413** carriageway-choking events.
- Worst enforcement zone: **Upparpet** (impact 90,361), then **HAL Old Airport**
  and **Shivajinagar**.
- City-wide peak is **08:00–11:00 IST** — the single best enforcement window.
- Some smaller zones punch above their volume: **Mahadevapura (39.9%)** and
  **K.R. Pura (25.5%)** are disproportionately high-impact despite fewer cases.
- Targeting pays off: **17 of 55 zones (31% effort) cover 80%** of high-impact
  violations — vs. 80% effort if patrols were spread evenly.
- Next 7 days forecast ~**12,300** violations (−0.9%/week), with **Shivajinagar
  (+95%)** and **Upparpet (+47%)** heating up fastest among high-load zones.

---

## API

| Route | Returns |
|-------|---------|
| `GET /api/overview` | KPIs, violation/vehicle mix, hourly & daily curves |
| `GET /api/zones` | police-station areas ranked by congestion impact |
| `GET /api/heat` | weighted heat points + 25 worst individual spots |
| `GET /api/recommendations` | peak 2-hour deployment window per top zone |
| `GET /api/forecast` | 7-day city forecast (mean + 80% band) + per-zone momentum |
| `GET /api/coverage` | coverage-vs-effort curve + 50/70/80/90% markers |
| `POST /api/score` | live impact score + priority band for a hypothetical spot |
| `GET /api/health` | liveness + row count |

## Files

```
preprocess.py      data engine: raw CSV -> data/aggregates.json (stdlib)
serve.py           zero-dependency server (stdlib http.server)
backend/app.py     equivalent FastAPI app (optional)
frontend/          index.html · styles.css · app.js · vendor/chart.umd.min.js
data/aggregates.json   pre-computed aggregates (regenerated by preprocess.py)
```

The raw CSV is **not** bundled (large / sensitive); `preprocess.py` reads it
from `~/Downloads/` by default or a path you pass in.
