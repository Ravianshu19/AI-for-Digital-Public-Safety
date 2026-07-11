"""
Prahari — Digital Public Safety Intelligence Platform
=====================================================
FastAPI backend. Run from the project root:

    ./run.sh          (or)
    .venv/bin/uvicorn app:app --reload --app-dir backend

Then open http://127.0.0.1:8008
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Input-validation limits (defensive — these endpoints are public)
MAX_TEXT = 5000          # chars for transcripts / messages
MAX_IMAGE_BYTES = 10 * 1024 * 1024   # 10 MB upload cap
ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp", "image/bmp"}


def _check_image(image: UploadFile, data: bytes):
    if (image.content_type or "") not in ALLOWED_IMAGE:
        raise HTTPException(status_code=415,
                            detail=f"Unsupported file type '{image.content_type}'. Upload a JPEG/PNG/WebP image.")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 10 MB).")
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")

import scam_detector
import counterfeit
import fraud_graph
import geospatial
import citizen_shield
import evaluate
import counterfeit_eval
import audit
import ocr
import india_upi
import data
import fusion
import voice
import deepfake
import llm

app = FastAPI(title="Prahari — Digital Public Safety Intelligence", version="1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


# --------------------------------------------------------------------------- #
# Module 1: Digital Arrest Scam Detection
# --------------------------------------------------------------------------- #
class ScamRequest(BaseModel):
    text: str = Field(..., max_length=MAX_TEXT)
    call_metadata: Optional[Dict] = None
    victim_ref: Optional[str] = Field("V-DEMO", max_length=64)
    caller_number: Optional[str] = Field("+910000000000", max_length=20)


@app.post("/api/scam/analyze")
def scam_analyze(req: ScamRequest):
    verdict = scam_detector.analyze(req.text, req.call_metadata)
    out = verdict.to_dict()
    if verdict.mha_alert:
        out["mha_alert_package"] = scam_detector.generate_mha_alert(
            verdict, req.victim_ref, req.caller_number
        )
    # Optional LLM second opinion (hybrid NLP) — enriches, never gates.
    opinion = llm.second_opinion(req.text) if llm.available() else None
    out["llm_second_opinion"] = opinion
    out["llm_available"] = llm.available()
    out["audit_entry"] = audit.log("scam", req.text, verdict.verdict, verdict.risk_score)
    return out


# --------------------------------------------------------------------------- #
# Speech AI: synthetic / AI-voice screening for call audio
# --------------------------------------------------------------------------- #
@app.post("/api/voice/analyze")
async def voice_analyze(audio: UploadFile = File(...)):
    data_bytes = await audio.read()
    if len(data_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Audio too large (max 10 MB).")
    if not data_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")
    result = voice.analyze_audio(data_bytes)
    out = result.to_dict()
    out["audit_entry"] = audit.log("voice", data_bytes, result.verdict, result.synthetic_score)
    return out


# --------------------------------------------------------------------------- #
# Computer Vision: deepfake / tamper screening for video-call frames
# --------------------------------------------------------------------------- #
@app.post("/api/deepfake/analyze")
async def deepfake_analyze(image: UploadFile = File(...)):
    img_bytes = await image.read()
    _check_image(image, img_bytes)
    result = deepfake.analyze_image(img_bytes)
    out = result.to_dict()
    out["audit_entry"] = audit.log("deepfake", img_bytes, result.verdict, result.manipulation_score)
    return out


@app.get("/api/scam/samples")
def scam_samples():
    return data.SAMPLE_TRANSCRIPTS


# --------------------------------------------------------------------------- #
# Intelligence Fusion: agentic cross-module correlation on one case
# --------------------------------------------------------------------------- #
class FusionRequest(BaseModel):
    risk_score: int = Field(..., ge=0, le=100)
    verdict: str = Field(..., max_length=20)
    stage_reached: str = Field("", max_length=160)
    caller_number: Optional[str] = Field(None, max_length=20)
    text_sha256: Optional[str] = Field(None, max_length=64)


@app.post("/api/fusion/analyze")
def fusion_analyze(req: FusionRequest):
    """Chain fraud-graph, geospatial, alerting and the audit ledger on a
    confirmed scam session — one incident flowing through every module."""
    return fusion.run(req.risk_score, req.verdict, req.stage_reached,
                      req.caller_number, req.text_sha256)


# --------------------------------------------------------------------------- #
# Module 2: Counterfeit Currency Identification
# --------------------------------------------------------------------------- #
@app.post("/api/counterfeit/analyze")
async def counterfeit_analyze(
    denomination: int = Form(...),
    serial_number: Optional[str] = Form(None),
    uv_feature_present: Optional[bool] = Form(None),
    force: Optional[bool] = Form(False),
    image: UploadFile = File(...),
):
    img_bytes = await image.read()
    _check_image(image, img_bytes)
    if denomination not in counterfeit.DENOM_SPEC:
        raise HTTPException(status_code=400, detail="Unsupported denomination.")
    result = counterfeit.analyze_image(
        img_bytes, denomination, serial_number, uv_feature_present, force=bool(force)
    )
    out = result.to_dict()
    out["audit_entry"] = audit.log(
        "counterfeit", img_bytes, result.verdict, result.authenticity_score,
        extra={"denomination": denomination},
    )
    return out


# --------------------------------------------------------------------------- #
# Module 3: Fraud Network Graph Intelligence
# --------------------------------------------------------------------------- #
@app.get("/api/fraud/analyze")
def fraud_analyze():
    out = fraud_graph.analyze(data.FRAUD_RECORDS)
    out["summary"]["source"] = "Synthetic Indian rings (UPI / wallet / crypto)"
    return out


@app.get("/api/fraud/india_stats")
def fraud_india_stats():
    """Real India UPI fraud aggregate intelligence (Kaggle FY23–25 dataset)."""
    return india_upi.stats()


class FraudCustom(BaseModel):
    records: List[Dict]


@app.post("/api/fraud/analyze")
def fraud_analyze_custom(req: FraudCustom):
    return fraud_graph.analyze(req.records)


# --------------------------------------------------------------------------- #
# Module 4: Geospatial Crime Pattern Intelligence
# --------------------------------------------------------------------------- #
@app.get("/api/geo/analyze")
def geo_analyze():
    return {**geospatial.analyze(data.GEO_POINTS), "points": data.GEO_POINTS,
            "state_stats": geospatial.state_stats(),
            "cybercrime_motives": geospatial.cybercrime_motives()}


# --------------------------------------------------------------------------- #
# Module 5: Citizen Fraud Shield (multi-channel chat)
# --------------------------------------------------------------------------- #
class ShieldRequest(BaseModel):
    message: str = Field(..., max_length=MAX_TEXT)
    lang: str = Field("en", max_length=5)
    call_metadata: Optional[Dict] = None


@app.post("/api/shield/assess")
def shield_assess(req: ShieldRequest):
    return citizen_shield.assess(req.message, req.lang, req.call_metadata)


@app.get("/api/shield/languages")
def shield_languages():
    return citizen_shield.supported_languages()


@app.post("/api/shield/ocr")
async def shield_ocr(lang: str = Form("en"), image: UploadFile = File(...)):
    """Citizen uploads a scam screenshot -> OCR -> scam risk assessment."""
    img_bytes = await image.read()
    _check_image(image, img_bytes)
    text = ocr.extract_text(img_bytes)
    if not text.strip():
        return {"extracted_text": "", "error": "No readable text found in image."}
    # OCR can collapse spaces; assess both raw and re-spaced text, keep higher risk
    # so a spacing artdefact never under-classifies a real scam screenshot.
    fixed = ocr.respace(text)
    r_raw = citizen_shield.assess(text, lang)
    r_fix = citizen_shield.assess(fixed, lang)
    result = r_fix if r_fix["risk_score"] >= r_raw["risk_score"] else r_raw
    result["extracted_text"] = text
    result["normalized_text"] = fixed
    audit.log("citizen_shield", text, result["verdict"], result["risk_score"],
              extra={"channel": "screenshot_ocr"})
    return result


# --------------------------------------------------------------------------- #
# Model Performance: live benchmark of the scam classifier
# --------------------------------------------------------------------------- #
@app.get("/api/eval/metrics")
def eval_metrics():
    return evaluate.run()


@app.get("/api/eval/counterfeit")
def eval_counterfeit():
    return counterfeit_eval.run()


# --------------------------------------------------------------------------- #
# Audit ledger (legal admissibility)
# --------------------------------------------------------------------------- #
@app.get("/api/audit/recent")
def audit_recent(n: int = 15):
    return {"chain": audit.verify_chain(), "entries": audit.recent(n)}


# --------------------------------------------------------------------------- #
# Health + frontend
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health():
    return {"status": "ok", "platform": "Prahari", "version": "1.0"}


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
