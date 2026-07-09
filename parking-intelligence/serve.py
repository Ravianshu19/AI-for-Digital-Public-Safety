"""
ParkSight — zero-dependency server (stdlib only).
Serves the dashboard + JSON API without FastAPI/uvicorn, so the demo runs on a
bare `python3` with nothing installed. Mirrors backend/app.py's routes.

Run:  python3 serve.py            # -> http://127.0.0.1:8010
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "aggregates.json")
FRONTEND = os.path.join(HERE, "frontend")
PORT = int(os.environ.get("PARKSIGHT_PORT", "8010"))

with open(DATA, encoding="utf-8") as f:
    AGG = json.load(f)

MIME = {".html": "text/html", ".css": "text/css", ".js": "application/javascript",
        ".json": "application/json", ".png": "image/png", ".svg": "image/svg+xml"}


def score(payload):
    weights = AGG["meta"]["impact_weights"]
    vtypes = payload.get("violation_types", []) or []
    count = float(payload.get("daily_count", 0) or 0)
    per = sum(weights.get(v, 1.0) for v in vtypes) or 1.0
    impact = round(per * count, 1)
    if impact >= 2000:
        band, act = "CRITICAL", "Deploy tow + marshal daily in peak window"
    elif impact >= 800:
        band, act = "HIGH", "Scheduled enforcement 3–4x/week in peak window"
    elif impact >= 250:
        band, act = "MEDIUM", "Weekly patrol + signage / bollards review"
    else:
        band, act = "LOW", "Passive monitoring; citizen-report driven"
    return {"per_event_impact": round(per, 2), "impact_score": impact,
            "band": band, "recommended_action": act,
            "explain": [{"type": v, "weight": weights.get(v, 1.0)} for v in vtypes]}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # quiet

    def _send(self, obj, code=200, ctype="application/json"):
        body = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._file(os.path.join(FRONTEND, "index.html"))
        if path.startswith("/static/"):
            return self._file(os.path.join(FRONTEND, path[len("/static/"):]))
        if path == "/api/health":
            return self._send({"ok": True, "rows": AGG["meta"]["source_rows"]})
        if path == "/api/overview":
            return self._send({k: AGG[k] for k in (
                "meta", "kpis", "violation_breakdown", "vehicle_breakdown",
                "by_hour", "by_dow", "by_month")})
        if path == "/api/zones":
            return self._send({"zones": AGG["zones"]})
        if path == "/api/heat":
            return self._send({"heat": AGG["heat"], "top_spots": AGG["top_spots"]})
        if path == "/api/recommendations":
            return self._send({"recommendations": AGG["recommendations"]})
        if path == "/api/coverage":
            return self._send(AGG["coverage"])
        if path == "/api/forecast":
            return self._send({"forecast": AGG["forecast"],
                               "zone_forecast": AGG["zone_forecast"]})
        self._send({"error": "not found"}, 404)

    def do_POST(self):
        if urlparse(self.path).path == "/api/score":
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n) or b"{}")
            return self._send(score(payload))
        self._send({"error": "not found"}, 404)

    def _file(self, fp):
        if not os.path.isfile(fp):
            return self._send({"error": "not found"}, 404)
        ext = os.path.splitext(fp)[1]
        with open(fp, "rb") as f:
            self._send(f.read(), ctype=MIME.get(ext, "application/octet-stream"))


if __name__ == "__main__":
    print(f"ParkSight (stdlib) · http://127.0.0.1:{PORT} · {AGG['meta']['source_rows']:,} records")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
