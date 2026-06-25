"""
On-device OCR for the Citizen Fraud Shield (screenshot intake).

Uses RapidOCR (ONNX Runtime) — a self-contained, offline OCR engine (no system
tesseract binary needed). The model is lazy-loaded on first use and cached.
Lets a citizen upload a scam screenshot, from which we extract the text and run
it through the scam classifier.
"""

from __future__ import annotations

import io
import re
from typing import Optional

import numpy as np
from PIL import Image

_engine = None


def respace(text: str) -> str:
    """OCR often collapses spaces ('SharetheOTPsent...'), which breaks word-boundary
    matching. Re-introduce spaces at camelCase / letter-digit boundaries and split
    long merged tokens with a word-frequency segmenter (wordninja) when available."""
    if not text:
        return text
    t = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)        # camelCase
    t = re.sub(r"([A-Za-z])(\d)", r"\1 \2", t)            # letter→digit
    t = re.sub(r"(\d)([A-Za-z])", r"\1 \2", t)            # digit→letter
    try:
        import wordninja
        out = []
        for tok in t.split():
            core = re.sub(r"[^A-Za-z]", "", tok)
            if len(core) > 10 and tok.isalpha():
                parts = wordninja.split(tok)
                out.append(" ".join(parts) if parts else tok)
            else:
                out.append(tok)
        t = " ".join(out)
    except Exception:
        pass
    return t


def _get_engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR  # heavy import, do it lazily
        _engine = RapidOCR()
    return _engine


def extract_text(image_bytes: bytes) -> str:
    """Return concatenated text detected in the image (best-effort)."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return ""
    arr = np.asarray(img)
    try:
        result, _ = _get_engine()(arr)
    except Exception:
        return ""
    if not result:
        return ""
    # result: list of [box, text, confidence]
    lines = [r[1] for r in result if len(r) >= 2 and r[1]]
    return " ".join(lines).strip()
