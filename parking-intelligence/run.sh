#!/usr/bin/env bash
# ParkSight — build aggregates (if missing) then serve the dashboard on :8010.
# Zero-dependency by default: uses stdlib serve.py, so plain `python3` is enough.
set -e
cd "$(dirname "$0")"
PY="$(command -v python3 || echo ../.venv/bin/python)"
CSV="${1:-$HOME/Downloads/jan to may police violation_anonymized791b166.csv}"

if [ ! -f data/aggregates.json ]; then
  echo "· building aggregates from raw CSV…"
  "$PY" preprocess.py "$CSV"
fi

echo "· ParkSight on http://127.0.0.1:8010  (Ctrl-C to stop)"
exec "$PY" serve.py
