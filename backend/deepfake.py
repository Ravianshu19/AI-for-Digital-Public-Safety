"""
Deepfake / tamper screening for video-call frames
=================================================

Digital-arrest scammers pose as officers over video call, increasingly with
face-swapped or AI-generated frames. A trained CNN (e.g. XceptionNet on
FaceForensics++) is the production detector; for a runnable, offline,
dependency-light prototype we implement transparent IMAGE FORENSICS (PIL +
numpy) that flags the artifacts manipulation leaves behind:

  1. Error-Level Analysis (ELA) — recompress and diff; spliced/edited regions
     show a different error level than the rest of the frame.
  2. Noise-residual uniformity — real camera sensor noise is uniform; pasted /
     GAN-generated regions break that uniformity.
  3. High-frequency energy — GAN/upsampled faces are often unnaturally smooth
     (low micro-detail) or carry periodic upsampling artifacts.

Reported per-feature, glass-box. This is a tamper SCREENER, not a trained
face-swap model (documented honestly) — a real first-pass filter that routes
suspicious frames to a human or the CNN on the roadmap.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
from PIL import Image


@dataclass
class DFFeature:
    name: str
    suspicious: bool
    detail: str

    def to_dict(self):
        return {"name": self.name, "suspicious": self.suspicious, "detail": self.detail}


@dataclass
class DeepfakeResult:
    verdict: str             # LIKELY_MANIPULATED / REVIEW / LIKELY_AUTHENTIC / UNREADABLE
    manipulation_score: int  # 0..100 (higher = more likely fake/edited)
    features: List[DFFeature] = field(default_factory=list)
    notes: str = ""

    def to_dict(self):
        return {
            "verdict": self.verdict,
            "manipulation_score": self.manipulation_score,
            "features": [f.to_dict() for f in self.features],
            "notes": self.notes,
        }


def _ela(img: Image.Image, quality=90) -> np.ndarray:
    """Absolute difference between the image and its JPEG recompression."""
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    buf.seek(0)
    recomp = Image.open(buf).convert("RGB")
    a = np.asarray(img, dtype=np.int16)
    b = np.asarray(recomp, dtype=np.int16)
    return np.abs(a - b).astype(np.float64)


def analyze_image(image_bytes: bytes) -> DeepfakeResult:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return DeepfakeResult(verdict="UNREADABLE", manipulation_score=0,
                              notes="Image could not be decoded.")
    # keep it a sensible size for stable stats
    img.thumbnail((1024, 1024))
    rgb = np.asarray(img, dtype=np.float64)
    h, w = rgb.shape[:2]
    if h < 40 or w < 40:
        return DeepfakeResult(verdict="UNREADABLE", manipulation_score=0,
                              notes="Frame too small to analyse.")
    gray = rgb.mean(axis=2)
    feats: List[DFFeature] = []

    # 1. ELA — spliced regions light up unevenly. Measure how peaky the error is.
    ela = _ela(img).mean(axis=2)
    ela_mean = float(ela.mean())
    ela_p99 = float(np.percentile(ela, 99))
    ela_ratio = ela_p99 / (ela_mean + 1e-6)     # high => localized bright edits
    f1 = ela_ratio > 8.0 and ela_p99 > 12
    feats.append(DFFeature("Error-level analysis (splice)", f1,
        f"ELA peak/mean ratio={ela_ratio:.1f} (peak {ela_p99:.0f}) "
        f"({'uneven — possible edit' if f1 else 'uniform compression'})"))

    # 2. Noise-residual uniformity across tiles (real sensor noise is uniform)
    resid = gray - _boxblur(gray, 3)
    ts = []
    step = max(20, min(h, w) // 8)
    for i in range(0, h - step, step):
        for j in range(0, w - step, step):
            ts.append(resid[i:i+step, j:j+step].std())
    ts = np.array(ts) if ts else np.array([0.0])
    noise_cv = float(ts.std() / (ts.mean() + 1e-6))
    f2 = noise_cv > 0.85
    feats.append(DFFeature("Sensor-noise uniformity", f2,
        f"noise variation across frame CV={noise_cv:.2f} "
        f"({'inconsistent — pasted region likely' if f2 else 'uniform — single capture'})"))

    # 3. High-frequency micro-detail (GAN faces are often over-smooth)
    gy, gx = np.gradient(gray)
    hf = float((np.abs(gx) + np.abs(gy)).mean())
    f3 = hf < 4.0
    feats.append(DFFeature("Micro-detail / sharpness", f3,
        f"high-frequency energy={hf:.1f} "
        f"({'over-smooth — synthetic-like' if f3 else 'natural detail'})"))

    weights = {"Error-level analysis (splice)": 45, "Sensor-noise uniformity": 35,
               "Micro-detail / sharpness": 20}
    score = sum(weights[f.name] for f in feats if f.suspicious)
    # Conservative bands: a screener must not confidently clear a fake nor cry
    # wolf on a real face, so any single artifact routes to human REVIEW.
    if score >= 55:
        verdict = "LIKELY_MANIPULATED"
    elif score >= 20:
        verdict = "REVIEW"
    else:
        verdict = "LIKELY_AUTHENTIC"
    flagged = [f.name for f in feats if f.suspicious]
    notes = (f"{len(flagged)} of {len(feats)} tamper markers triggered"
             + (f": {', '.join(flagged)}." if flagged else " — frame looks authentic.")
             + " Heuristic screener — confirm high-risk frames with the CNN detector.")
    return DeepfakeResult(verdict=verdict, manipulation_score=score,
                          features=feats, notes=notes)


def _boxblur(a: np.ndarray, r: int) -> np.ndarray:
    """Cheap separable box blur for the noise residual."""
    k = 2 * r + 1
    pad = np.pad(a, r, mode="edge")
    c = np.cumsum(np.cumsum(pad, axis=0), axis=1)
    c = np.pad(c, ((1, 0), (1, 0)), mode="constant")
    H, W = a.shape
    tot = (c[k:k+H, k:k+W] - c[0:H, k:k+W] - c[k:k+H, 0:W] + c[0:H, 0:W])
    return tot / (k * k)
