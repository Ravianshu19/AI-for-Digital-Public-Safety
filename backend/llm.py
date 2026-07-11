"""
Optional LLM second-opinion layer (hybrid NLP)
==============================================

The explainable signal model is the PRIMARY, court-defensible classifier and
runs fully offline. This module adds an OPTIONAL large-language-model second
opinion for novel phrasings the rule set hasn't seen yet — the hybrid that
answers "where's the LLM?" without sacrificing the glass-box guarantee:

  - If ANTHROPIC_API_KEY is configured, we ask a small, fast model for a
    structured risk read and surface it ALONGSIDE (never replacing) the
    explainable verdict.
  - If no key / no network, `available()` is False and the app runs exactly as
    before. The rule engine's verdict is always the one of record.

This keeps the deployment honest: the LLM enriches, it does not gate.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Dict, Optional

MODEL = "claude-haiku-4-5-20251001"
_ENDPOINT = (os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
             + "/v1/messages")


def available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def second_opinion(text: str, timeout: float = 8.0) -> Optional[Dict]:
    """Return {'risk': 0-100, 'verdict': str, 'reason': str, 'model': str} or None.
    Never raises — any failure degrades silently to the rule engine."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or not (text or "").strip():
        return None
    prompt = (
        "You are a fraud-triage assistant for Indian digital-arrest / financial "
        "scams. Read the message and reply with STRICT JSON only: "
        '{"risk": <0-100>, "verdict": "SAFE|SUSPICIOUS|HIGH_RISK|ACTIVE_SCAM", '
        '"reason": "<=20 words"}.\n\nMESSAGE:\n' + text[:2000]
    )
    body = json.dumps({
        "model": MODEL, "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(_ENDPOINT, body, {
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        txt = "".join(b.get("text", "") for b in data.get("content", []))
        start, end = txt.find("{"), txt.rfind("}")
        parsed = json.loads(txt[start:end + 1])
        return {
            "risk": int(parsed.get("risk", 0)),
            "verdict": str(parsed.get("verdict", "")),
            "reason": str(parsed.get("reason", ""))[:200],
            "model": MODEL,
        }
    except Exception:
        return None
