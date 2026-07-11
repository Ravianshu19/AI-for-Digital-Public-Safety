"""
Speech AI — synthetic / AI-voice screening for call audio
=========================================================

Digital-arrest gangs increasingly use AI-cloned or TTS voices. A trained
ASVspoof-class model is the production answer; for a runnable, offline,
dependency-light prototype we implement a transparent ACOUSTIC screener
(stdlib `wave` + numpy) that scores the features a synthetic voice betrays:

  1. Pitch (f0) variability  — natural speech is prosodic; TTS is flatter.
  2. Energy dynamics         — humans vary loudness; synthetic is steadier.
  3. Pause regularity        — human pauses are irregular; TTS is metronomic.
  4. Spectral flatness       — vocoder output is spectrally flatter / buzzier.
  5. Zero-crossing stability — synthetic frames are unnaturally consistent.

Every feature is reported with its measured value, so the verdict is a glass
box — the same philosophy as the scam and counterfeit engines. This is a
heuristic SCREENER, not a trained deepfake-voice model (documented honestly).
"""

from __future__ import annotations

import io
import wave
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np


@dataclass
class VoiceFeature:
    name: str
    synthetic: bool          # True => this feature looks synthetic
    detail: str

    def to_dict(self):
        return {"name": self.name, "synthetic": self.synthetic, "detail": self.detail}


@dataclass
class VoiceResult:
    verdict: str             # LIKELY_SYNTHETIC / UNCERTAIN / LIKELY_HUMAN / UNREADABLE
    synthetic_score: int     # 0..100 (higher = more likely AI/synthetic)
    features: List[VoiceFeature] = field(default_factory=list)
    notes: str = ""
    duration_s: float = 0.0

    def to_dict(self):
        return {
            "verdict": self.verdict,
            "synthetic_score": self.synthetic_score,
            "features": [f.to_dict() for f in self.features],
            "notes": self.notes,
            "duration_s": round(self.duration_s, 2),
        }


def _decode_wav(data: bytes):
    """Return (mono float32 samples in [-1,1], sample_rate) or (None, None)."""
    try:
        wf = wave.open(io.BytesIO(data), "rb")
    except Exception:
        return None, None
    sr = wf.getframerate()
    n = wf.getnframes()
    ch = wf.getnchannels()
    sw = wf.getsampwidth()
    raw = wf.readframes(n)
    wf.close()
    if not raw:
        return None, None
    dt = {1: np.int8, 2: np.int16, 4: np.int32}.get(sw)
    if dt is None:
        return None, None
    x = np.frombuffer(raw, dtype=dt).astype(np.float64)
    if ch > 1:                       # stereo -> mono
        x = x.reshape(-1, ch).mean(axis=1)
    peak = float(np.max(np.abs(x))) or 1.0
    return x / peak, sr


def _frame(x: np.ndarray, sr: int, win_ms=30):
    w = max(1, int(sr * win_ms / 1000))
    n = len(x) // w
    if n < 2:
        return np.array([x])
    return x[: n * w].reshape(n, w)


def _f0(frame: np.ndarray, sr: int) -> float:
    """Crude autocorrelation pitch estimate (Hz), 0 if unvoiced."""
    f = frame - frame.mean()
    if np.sqrt((f ** 2).mean()) < 1e-3:
        return 0.0
    corr = np.correlate(f, f, "full")[len(f) - 1:]
    lo, hi = int(sr / 400), int(sr / 75)          # 75–400 Hz voice band
    if hi >= len(corr) or lo >= hi:
        return 0.0
    peak = np.argmax(corr[lo:hi]) + lo
    return sr / peak if peak else 0.0


def analyze_audio(data: bytes) -> VoiceResult:
    x, sr = _decode_wav(data)
    if x is None:
        return VoiceResult(verdict="UNREADABLE", synthetic_score=0,
                           notes="Audio could not be decoded — upload an uncompressed WAV clip.")
    dur = len(x) / sr
    if dur < 0.4:
        return VoiceResult(verdict="UNREADABLE", synthetic_score=0, duration_s=dur,
                           notes="Clip too short — need at least ~0.5s of audio.")

    frames = _frame(x, sr)
    energies = np.sqrt((frames ** 2).mean(axis=1)) + 1e-9
    # 1. Pitch variability (coefficient of variation of voiced f0)
    f0s = np.array([_f0(fr, sr) for fr in frames])
    voiced = f0s[f0s > 0]
    pitch_cv = float(np.std(voiced) / (np.mean(voiced) + 1e-9)) if len(voiced) > 3 else 0.0
    # 2. Energy dynamics (coefficient of variation)
    energy_cv = float(np.std(energies) / (np.mean(energies) + 1e-9))
    # 3. Pause regularity: gaps between low-energy frames; humans irregular
    thr = np.percentile(energies, 35)
    silent = energies < thr
    gaps, run = [], 0
    for s in silent:
        if s:
            run += 1
        elif run:
            gaps.append(run); run = 0
    pause_reg = float(np.std(gaps) / (np.mean(gaps) + 1e-9)) if len(gaps) > 2 else 1.0
    # 4. Spectral flatness (geometric/arithmetic mean of magnitude spectrum)
    mag = np.abs(np.fft.rfft(x * np.hanning(len(x)))) + 1e-9
    flatness = float(np.exp(np.mean(np.log(mag))) / np.mean(mag))
    # 5. Zero-crossing-rate stability across frames
    zcr = (np.abs(np.diff(np.sign(frames), axis=1)) > 0).mean(axis=1)
    zcr_cv = float(np.std(zcr) / (np.mean(zcr) + 1e-9))

    feats: List[VoiceFeature] = []
    # each flag True => looks synthetic; thresholds are conservative heuristics
    p1 = pitch_cv < 0.12
    feats.append(VoiceFeature("Pitch (f0) variability", p1,
        f"prosody CV={pitch_cv:.2f} ({'flat — synthetic-like' if p1 else 'natural variation'})"))
    p2 = energy_cv < 0.35
    feats.append(VoiceFeature("Loudness dynamics", p2,
        f"energy CV={energy_cv:.2f} ({'unnaturally steady' if p2 else 'human-like dynamics'})"))
    p3 = pause_reg < 0.45
    feats.append(VoiceFeature("Pause rhythm", p3,
        f"pause irregularity={pause_reg:.2f} ({'metronomic — synthetic-like' if p3 else 'irregular — human'})"))
    p4 = flatness > 0.30
    feats.append(VoiceFeature("Spectral flatness", p4,
        f"flatness={flatness:.2f} ({'vocoder-like' if p4 else 'natural timbre'})"))
    p5 = zcr_cv < 0.20
    feats.append(VoiceFeature("Frame consistency (ZCR)", p5,
        f"ZCR CV={zcr_cv:.2f} ({'over-consistent' if p5 else 'natural'})"))

    weights = {"Pitch (f0) variability": 30, "Loudness dynamics": 20,
               "Pause rhythm": 20, "Spectral flatness": 15, "Frame consistency (ZCR)": 15}
    score = sum(weights[f.name] for f in feats if f.synthetic)
    if score >= 60:
        verdict = "LIKELY_SYNTHETIC"
    elif score >= 35:
        verdict = "UNCERTAIN"
    else:
        verdict = "LIKELY_HUMAN"
    flagged = [f.name for f in feats if f.synthetic]
    notes = (f"{len(flagged)} of {len(feats)} acoustic markers look synthetic"
             + (f": {', '.join(flagged)}." if flagged else "."))
    return VoiceResult(verdict=verdict, synthetic_score=score, features=feats,
                       notes=notes, duration_s=dur)
