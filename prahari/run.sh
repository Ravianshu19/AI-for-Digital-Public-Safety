#!/usr/bin/env bash
# Launch the Prahari platform.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create venv + install deps on first run.
if [ ! -d "$DIR/.venv" ]; then
  echo "Creating virtualenv and installing dependencies…"
  python3 -m venv "$DIR/.venv"
  "$DIR/.venv/bin/pip" install --quiet --upgrade pip
  "$DIR/.venv/bin/pip" install --quiet -r "$DIR/requirements.txt"
fi

PORT="${PORT:-8008}"
echo "Prahari running at  http://127.0.0.1:$PORT"
exec "$DIR/.venv/bin/uvicorn" app:app --app-dir "$DIR/backend" --host 127.0.0.1 --port "$PORT"
