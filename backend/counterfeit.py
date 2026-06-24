"""
Counterfeit Currency Identification Agent
=========================================

Image-forensics pipeline for Indian banknotes (Mahatma Gandhi New Series).

A production system would run a fine-tuned CNN/ViT on each security feature ROI.
For a runnable, dependency-light prototype we implement a transparent, multi-
feature image-forensics scorer (PIL + numpy) that mirrors the *same feature set*
a trained model would attend to, and returns a per-feature breakdown so a teller
or field officer sees WHY a note was flagged — not just a number.

Features checked (per RBI genuine-note specification):
  1. Aspect ratio / dimensions vs. denomination spec.
  2. Dominant colour vs. the RBI base colour for that denomination.
  3. Microprint sharpness  -> high-frequency energy (counterfeits print blurry).
  4. Security-thread region -> vertical band luminance signature.
  5. Intaglio/print texture -> local contrast variance.
  6. Serial number format   -> RBI serial grammar validation (3 letters + 6 digits).
  7. UV feature (simulated)  -> consumed from device UV-channel flag if present.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from PIL import Image


# RBI MG (new) series base colours + aspect ratio (w/h) per denomination.
# Base colours calibrated from genuine RBI note imagery (ink-region mean,
# background masked) — see sample_data/currency/ and fetch_reference_notes.py.
DENOM_SPEC = {
    10:   {"colour": (202, 171, 145), "ratio": 123 / 63,  "name": "₹10 Chocolate Brown"},
    20:   {"colour": (212, 208, 148), "ratio": 129 / 63,  "name": "₹20 Greenish Yellow"},
    50:   {"colour": (155, 190, 171), "ratio": 135 / 66,  "name": "₹50 Fluorescent Blue"},
    100:  {"colour": (188, 172, 210), "ratio": 142 / 66,  "name": "₹100 Lavender"},
    200:  {"colour": (215, 174, 126), "ratio": 146 / 66,  "name": "₹200 Bright Yellow"},
    500:  {"colour": (164, 168, 135), "ratio": 150 / 66,  "name": "₹500 Stone Grey"},
}

# RBI serials: a short alphanumeric prefix (e.g. "8AB") followed by 6 digits.
SERIAL_RE = re.compile(r"^[0-9]{0,2}[A-Z]{1,3}\s?[0-9]{6}$")


@dataclass
class FeatureResult:
    name: str
    passed: bool
    confidence: float       # 0..1
    detail: str

    def to_dict(self):
        return {
            "name": self.name,
            "passed": self.passed,
            "confidence": round(self.confidence, 3),
            "detail": self.detail,
        }


@dataclass
class CounterfeitResult:
    denomination: int
    verdict: str            # GENUINE / SUSPECT / COUNTERFEIT / UNREADABLE
    authenticity_score: int  # 0..100
    features: List[FeatureResult] = field(default_factory=list)
    notes: str = ""

    def to_dict(self):
        return {
            "denomination": self.denomination,
            "verdict": self.verdict,
            "authenticity_score": self.authenticity_score,
            "features": [f.to_dict() for f in self.features],
            "notes": self.notes,
        }


def _high_freq_energy(gray: np.ndarray) -> float:
    """Laplacian-style high-frequency energy => print/microprint sharpness."""
    gy, gx = np.gradient(gray.astype(float))
    lap = np.abs(gx) + np.abs(gy)
    return float(lap.var())


def _ink_mask(rgb: np.ndarray) -> np.ndarray:
    """Boolean mask of the note's paper/ink region, excluding near-white scan
    background and pure-black borders — so margins don't skew colour stats."""
    mn = rgb.min(axis=2)
    mx = rgb.max(axis=2)
    not_white = mn < 235          # drop near-white scan background
    not_black = mx > 18           # drop pure-black borders
    return not_white & not_black


def _crop_to_note(rgb: np.ndarray) -> np.ndarray:
    """Crop to the bounding box of the note (largest non-white region) so that
    aspect ratio and feature ROIs are computed on the note, not the scan margins."""
    mask = _ink_mask(rgb)
    if mask.sum() < 0.05 * mask.size:
        return rgb
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if rows.size < 2 or cols.size < 2:
        return rgb
    return rgb[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]


def _dominant_colour(rgb: np.ndarray) -> tuple:
    """Mean colour over the ink/paper region only (ignores white background)."""
    mask = _ink_mask(rgb)
    pix = rgb[mask] if mask.any() else rgb.reshape(-1, 3)
    return tuple(int(c) for c in pix.reshape(-1, 3).mean(axis=0))


def _colour_distance(a, b) -> float:
    return float(np.sqrt(sum((x - y) ** 2 for x, y in zip(a, b))))


def analyze_image(
    image_bytes: bytes,
    denomination: int,
    serial_number: Optional[str] = None,
    uv_feature_present: Optional[bool] = None,
) -> CounterfeitResult:
    spec = DENOM_SPEC.get(denomination)
    if spec is None:
        return CounterfeitResult(
            denomination=denomination, verdict="UNREADABLE",
            authenticity_score=0, notes="Unsupported denomination.",
        )

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return CounterfeitResult(
            denomination=denomination, verdict="UNREADABLE",
            authenticity_score=0, notes="Image could not be decoded.",
        )

    rgb = np.asarray(img)
    # Crop away scan margins so all geometry/colour stats are on the note itself.
    rgb = _crop_to_note(rgb)
    h, w = rgb.shape[:2]
    gray = rgb.mean(axis=2)
    features: List[FeatureResult] = []

    # 1. Aspect ratio (tolerance allows for hand-held / partially-cropped captures)
    ratio = w / h if h else 0
    ratio_err = abs(ratio - spec["ratio"]) / spec["ratio"]
    ratio_ok = ratio_err < 0.22
    features.append(FeatureResult(
        "Aspect ratio / dimensions", ratio_ok,
        max(0.0, 1 - ratio_err / 0.22),
        f"measured w/h={ratio:.2f} vs spec {spec['ratio']:.2f} ({ratio_err*100:.0f}% off)",
    ))

    # 2. Dominant colour
    dom = _dominant_colour(rgb)
    dist = _colour_distance(dom, spec["colour"])
    colour_ok = dist < 95
    features.append(FeatureResult(
        "Base colour match", colour_ok,
        max(0.0, 1 - dist / 160),
        f"dominant RGB {dom} vs spec {spec['colour']} (Δ={dist:.0f})",
    ))

    # 3. Microprint sharpness
    energy = _high_freq_energy(gray)
    # genuine notes are detail-rich; very low energy => blurry counterfeit/photo
    sharp_ok = energy > 120
    features.append(FeatureResult(
        "Microprint / intaglio sharpness", sharp_ok,
        min(1.0, energy / 400),
        f"high-frequency energy={energy:.0f} (threshold 120)",
    ))

    # 4. Security thread (vertical luminance band, left-of-centre on MG series)
    band = gray[:, int(w * 0.30):int(w * 0.42)]
    col_means = band.mean(axis=0)
    thread_contrast = float(col_means.max() - col_means.min()) if col_means.size else 0
    thread_ok = thread_contrast > 18
    features.append(FeatureResult(
        "Security thread signature", thread_ok,
        min(1.0, thread_contrast / 60),
        f"vertical band contrast={thread_contrast:.0f} (threshold 18)",
    ))

    # 5. Intaglio texture (local contrast variance across tiles)
    tiles = []
    for i in range(0, h - 20, max(1, h // 8)):
        for j in range(0, w - 20, max(1, w // 8)):
            tiles.append(gray[i:i+20, j:j+20].std())
    texture = float(np.mean(tiles)) if tiles else 0
    texture_ok = texture > 8
    features.append(FeatureResult(
        "Intaglio print texture", texture_ok,
        min(1.0, texture / 25),
        f"mean local contrast={texture:.1f} (threshold 8)",
    ))

    # 6. Serial number grammar
    if serial_number:
        sn = serial_number.strip().upper()
        serial_ok = bool(SERIAL_RE.match(sn))
        features.append(FeatureResult(
            "Serial number format (RBI grammar)", serial_ok,
            1.0 if serial_ok else 0.0,
            f"'{sn}' {'matches' if serial_ok else 'violates'} RBI serial pattern",
        ))

    # 7. UV feature (from hardware UV channel if device provides it)
    if uv_feature_present is not None:
        features.append(FeatureResult(
            "UV fluorescence feature", bool(uv_feature_present),
            1.0 if uv_feature_present else 0.0,
            "UV-reactive ink/thread detected by device sensor"
            if uv_feature_present else "No UV fluorescence — major red flag",
        ))

    # Weighted fusion. Security-critical features weigh more.
    weights = {
        "Aspect ratio / dimensions": 0.8,
        "Base colour match": 1.0,
        "Microprint / intaglio sharpness": 1.6,
        "Security thread signature": 1.6,
        "Intaglio print texture": 1.2,
        "Serial number format (RBI grammar)": 1.2,
        "UV fluorescence feature": 2.0,
    }
    total_w = sum(weights[f.name] for f in features)
    score = sum(weights[f.name] * f.confidence for f in features) / total_w
    authenticity = int(round(score * 100))

    if authenticity >= 75:
        verdict = "GENUINE"
    elif authenticity >= 50:
        verdict = "SUSPECT"
    else:
        verdict = "COUNTERFEIT"

    failed = [f.name for f in features if not f.passed]
    notes = (
        f"{len(failed)} of {len(features)} security features failed."
        + (f" Failed: {', '.join(failed)}." if failed else " All features passed.")
    )

    return CounterfeitResult(
        denomination=denomination, verdict=verdict,
        authenticity_score=authenticity, features=features, notes=notes,
    )
