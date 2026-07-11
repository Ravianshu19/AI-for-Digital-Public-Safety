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
    2000: {"colour": (196, 142, 176), "ratio": 166 / 66,  "name": "₹2000 Magenta (historical)"},
}

# Denominations that carry colour-shifting intaglio ink on the value numeral.
COLOUR_SHIFT_DENOMS = {100, 200, 500, 2000}

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
    verdict: str            # GENUINE / SUSPECT / COUNTERFEIT / MISMATCH / UNREADABLE
    authenticity_score: int  # 0..100
    features: List[FeatureResult] = field(default_factory=list)
    notes: str = ""
    identified_denomination: Optional[int] = None   # what the image reads as

    def to_dict(self):
        return {
            "denomination": self.denomination,
            "verdict": self.verdict,
            "authenticity_score": self.authenticity_score,
            "features": [f.to_dict() for f in self.features],
            "notes": self.notes,
            "identified_denomination": self.identified_denomination,
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


def identify_denomination(rgb: np.ndarray) -> Dict[int, float]:
    """Score the cropped note against every denomination's colour + geometry
    baseline (lower = closer). Used as a *fallback* mismatch check when the
    printed value can't be OCR-read."""
    h, w = rgb.shape[:2]
    dom = _dominant_colour(rgb)
    ratio = w / h if h else 0
    return {
        den: _colour_distance(dom, sp["colour"]) + 60 * abs(ratio - sp["ratio"]) / sp["ratio"]
        for den, sp in DENOM_SPEC.items()
    }


# Word cues printed on the note ("FIVE HUNDRED RUPEES"), longest first so
# "two hundred" is consumed before a bare "hundred".
_DENOM_WORDS = [
    ("two thousand", 2000), ("twothousand", 2000),
    ("five hundred", 500), ("fivehundred", 500),
    ("two hundred", 200), ("twohundred", 200),
    ("one hundred", 100), ("onehundred", 100),
    ("hundred", 100), ("fifty", 50), ("twenty", 20), ("ten", 10),
]


def read_printed_denomination(image_bytes: bytes) -> Dict[int, float]:
    """OCR the note and score how strongly each denomination's *printed value*
    appears — the word phrase ("FIVE HUNDRED", weight 2, very reliable) plus the
    digit token ("500", weight 1). This reads what the note actually says, so it
    separates ₹10 from ₹500 where colour cannot. Returns {} if OCR is
    unavailable or finds nothing (caller then falls back to the colour gate)."""
    try:
        import ocr
        text = ocr.extract_text(image_bytes) or ""
    except Exception:
        return {}
    if not text.strip():
        return {}
    ev: Dict[int, float] = {}
    low = text.lower()
    for phrase, val in _DENOM_WORDS:
        if phrase in low:
            ev[val] = max(ev.get(val, 0), 2)   # word phrase = strong evidence
            low = low.replace(phrase, " ")      # consume so "hundred" not double-counted
    for tok in re.findall(r"\b(2000|500|200|100|50|20|10)\b", text.replace(",", "")):
        v = int(tok)
        ev[v] = ev.get(v, 0) + 1
    return ev


def analyze_image(
    image_bytes: bytes,
    denomination: int,
    serial_number: Optional[str] = None,
    uv_feature_present: Optional[bool] = None,
    force: bool = False,          # skip the denomination-identity gate
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

    # Denomination-identity gate: verify the image is the selected denomination
    # before scoring it against that spec. PRIMARY signal is the value printed
    # on the note (OCR) — that reliably tells ₹10 from ₹500; the colour/geometry
    # match is only a fallback when the print can't be read. `force` overrides.
    id_best = None
    if not force:
        printed = read_printed_denomination(image_bytes)
        # Denominations whose value is clearly printed (word-phrase evidence).
        strong = {d: s for d, s in printed.items() if s >= 2}
        if strong:
            top = max(strong, key=strong.get)
            sel_ev = printed.get(denomination, 0)
            # Mismatch only when another denomination is clearly printed and the
            # selected one isn't (dominates by a clear margin) — avoids firing on
            # a stray OCR digit while catching "₹500 note analysed as ₹10".
            if top != denomination and strong[top] - sel_ev >= 2:
                return CounterfeitResult(
                    denomination=denomination, verdict="MISMATCH", authenticity_score=0,
                    identified_denomination=top,
                    notes=(f"The note reads ₹{top} — its printed value does not match the "
                           f"selected ₹{denomination}. Switch to ₹{top} and re-verify, or "
                           f"proceed anyway if you are certain."),
                )
            id_best = top
        else:
            # OCR inconclusive → colour/geometry fallback (confident mismatch only).
            id_scores = identify_denomination(rgb)
            cbest = min(id_scores, key=id_scores.get)
            if (cbest != denomination and id_scores[cbest] < 35
                    and id_scores[denomination] - id_scores[cbest] > 30):
                return CounterfeitResult(
                    denomination=denomination, verdict="MISMATCH", authenticity_score=0,
                    identified_denomination=cbest,
                    notes=(f"This note looks like a ₹{cbest}, not the selected ₹{denomination} "
                           f"(colour/size match). Switch to ₹{cbest} and re-verify, or proceed "
                           f"anyway if you are certain."),
                )
            id_best = cbest

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

    # 6b. Watermark window (pale electrotype/portrait panel). It sits on the
    #     right margin of the obverse and — mirrored — on the left margin of
    #     the reverse, so score both margins and keep the better candidate.
    body = gray[:, int(w * 0.20):int(w * 0.65)]
    candidates = {
        "right margin (obverse)": gray[:, int(w * 0.86):],
        "left margin (reverse)": gray[:, :int(w * 0.14)],
    }
    if body.size:
        best = None
        for side, panel in candidates.items():
            if not panel.size:
                continue
            lift = float(panel.mean() - body.mean())   # >0 => window is lighter
            struct = float(panel.std())                # texture => electrotype digits
            conf = max(0.0, min(1.0, (lift / 25 + struct / 45) / 2))
            if best is None or conf > best[3]:
                best = (side, lift, struct, conf)
        if best:
            side, wm_lift, wm_struct, wm_conf = best
            wm_ok = wm_lift > 2 and wm_struct > 6
            features.append(FeatureResult(
                "Watermark window (approx.)", wm_ok, wm_conf,
                f"{side}: brightness +{wm_lift:.0f} vs body, structure σ={wm_struct:.0f}",
            ))

    # 6c. Colour-shifting ink on the value numeral (₹100 and above).
    #     Approximate: bottom-right numeral region must carry saturated ink.
    if denomination in COLOUR_SHIFT_DENOMS:
        roi = rgb[int(h * 0.62):, int(w * 0.80):]
        if roi.size:
            mx = roi.max(axis=2).astype(float)
            mn = roi.min(axis=2).astype(float)
            sat = float(((mx - mn) / (mx + 1e-6)).mean())
            ink = float((roi.mean(axis=2) < 160).mean())  # fraction of inked pixels
            cs_ok = sat > 0.10 or ink > 0.08
            features.append(FeatureResult(
                "Colour-shift ink numeral (approx.)", cs_ok,
                max(0.0, min(1.0, sat * 3 + ink)),
                f"numeral saturation={sat:.2f}, inked area={ink*100:.0f}%",
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
        "Watermark window (approx.)": 0.6,
        "Colour-shift ink numeral (approx.)": 0.7,
        "Serial number format (RBI grammar)": 1.2,
        "UV fluorescence feature": 2.0,
    }
    total_w = sum(weights[f.name] for f in features)
    # The verdict is driven primarily by WHICH security features pass their
    # calibrated thresholds (a feature that meets spec should not be punished
    # for passing "only" 1.5x over threshold); the analog confidence remains
    # as a secondary term so stronger signatures still score higher.
    pass_rate = sum(weights[f.name] * (1.0 if f.passed else 0.0) for f in features) / total_w
    conf_rate = sum(weights[f.name] * f.confidence for f in features) / total_w
    authenticity = int(round((0.6 * pass_rate + 0.4 * conf_rate) * 100))

    # Bands calibrated to the pass-driven score: controlled-capture genuine
    # notes land ≥ 84, print-quality fakes ≤ ~55 — so < 60 is a rejection.
    if authenticity >= 75:
        verdict = "GENUINE"
    elif authenticity >= 60:
        verdict = "SUSPECT"
    else:
        verdict = "COUNTERFEIT"
    # Hard rules mirroring bank practice, whatever the optics say:
    # - a serial that violates the RBI grammar is disqualifying on its own;
    # - a *measured* absence of UV fluorescence can never clear as GENUINE.
    serial_fail = any(f.name.startswith("Serial number") and not f.passed for f in features)
    uv_fail = any(f.name.startswith("UV fluorescence") and not f.passed for f in features)
    if serial_fail:
        verdict = "COUNTERFEIT"
    elif uv_fail and verdict == "GENUINE":
        verdict = "SUSPECT"

    # An image-only rejection must be backed by print-quality evidence:
    # counterfeits print blurry (microprint sharpness / intaglio texture fail),
    # while a sharp, well-textured note that still scored low almost always
    # means a bad *capture* (angle, crop, lighting) — not a fake. Rejecting a
    # citizen's genuine note is the costly error, so those go to manual review.
    capture_issue = False
    passed = {f.name: f.passed for f in features}
    if (verdict == "COUNTERFEIT" and not serial_fail and not uv_fail
            and passed.get("Microprint / intaglio sharpness")
            and passed.get("Intaglio print texture")):
        verdict = "SUSPECT"
        capture_issue = True

    failed = [f.name for f in features if not f.passed]
    notes = (
        f"{len(failed)} of {len(features)} security features failed."
        + (f" Failed: {', '.join(failed)}." if failed else " All features passed.")
    )
    if capture_issue:
        notes += (" Print quality reads genuine — the failures are position/geometry checks, "
                  "which usually means a capture issue. Re-photograph the note flat, filling the "
                  "frame, in even light; verify the security thread and watermark physically.")

    return CounterfeitResult(
        denomination=denomination, verdict=verdict,
        authenticity_score=authenticity, features=features, notes=notes,
        identified_denomination=id_best,
    )
