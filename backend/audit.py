"""
Tamper-evident audit ledger (legal-admissibility support).

Every analysis appends one entry to an append-only JSONL ledger. Each entry is
hash-chained to the previous one (entry_hash = SHA-256 over the entry incl. the
previous entry's hash), so any later edit/deletion breaks the chain and is
detectable — a lightweight, local stand-in for a signed append-only ledger.

Each entry records: sequence, UTC timestamp, module, model version, a SHA-256 of
the *input* (chain-of-custody without storing PII), the verdict, the confidence
score, and the previous hash.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import threading
from typing import Dict, List, Optional

LOG_PATH = os.path.join(os.path.dirname(__file__), "audit_log.jsonl")
_LOCK = threading.Lock()

MODEL_VERSIONS = {
    "scam": "scam-killchain-v1.2",
    "counterfeit": "cf-forensic-v1.1",
    "fraud_graph": "fraud-cnm-community-v1.0",
    "citizen_shield": "shield-v1.1",
    "fusion": "fusion-agent-v1.0",
    "voice": "voice-acoustic-v1.0",
    "deepfake": "df-forensics-v1.0",
}


def _sha(obj) -> str:
    return hashlib.sha256(
        (obj if isinstance(obj, (bytes, bytearray)) else
         json.dumps(obj, sort_keys=True).encode())
    ).hexdigest()


def _last_hash() -> str:
    if not os.path.exists(LOG_PATH):
        return "GENESIS"
    last = "GENESIS"
    with open(LOG_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    last = json.loads(line)["entry_hash"]
                except Exception:
                    pass
    return last


def _count() -> int:
    if not os.path.exists(LOG_PATH):
        return 0
    with open(LOG_PATH, "r") as f:
        return sum(1 for ln in f if ln.strip())


def log(module: str, raw_input, verdict: str, score, extra: Optional[Dict] = None) -> Dict:
    """Append a hash-chained audit entry. raw_input may be str or bytes."""
    with _LOCK:
        prev = _last_hash()
        entry = {
            "seq": _count() + 1,
            "ts_utc": datetime.datetime.utcnow().isoformat() + "Z",
            "module": module,
            "model_version": MODEL_VERSIONS.get(module, "unknown"),
            "input_sha256": _sha(raw_input if isinstance(raw_input, (bytes, bytearray))
                                 else str(raw_input).encode()),
            "verdict": verdict,
            "score": score,
            "extra": extra or {},
            "prev_hash": prev,
        }
        entry["entry_hash"] = _sha(entry)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry


def recent(n: int = 20) -> List[Dict]:
    if not os.path.exists(LOG_PATH):
        return []
    out = []
    with open(LOG_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out[-n:][::-1]


def verify_chain() -> Dict:
    """Re-walk the ledger and confirm the hash chain is intact."""
    if not os.path.exists(LOG_PATH):
        return {"entries": 0, "intact": True, "broken_at": None}
    prev = "GENESIS"
    n = 0
    with open(LOG_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
            e = json.loads(line)
            stored = e.get("entry_hash")
            check = dict(e)
            check.pop("entry_hash", None)
            if e.get("prev_hash") != prev or _sha(check) != stored:
                return {"entries": n, "intact": False, "broken_at": e.get("seq")}
            prev = stored
    return {"entries": n, "intact": True, "broken_at": None}
