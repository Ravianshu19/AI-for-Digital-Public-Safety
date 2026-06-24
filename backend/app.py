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

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import scam_detector
import counterfeit
import fraud_graph
import geospatial
import citizen_shield
import evaluate
import counterfeit_eval
import data

app = FastAPI(title="Prahari — Digital Public Safety Intelligence", version="1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


# --------------------------------------------------------------------------- #
# Module 1: Digital Arrest Scam Detection
# --------------------------------------------------------------------------- #
class ScamRequest(BaseModel):
    text: str
    call_metadata: Optional[Dict] = None
    victim_ref: Optional[str] = "V-DEMO"
    caller_number: Optional[str] = "+910000000000"


@app.post("/api/scam/analyze")
def scam_analyze(req: ScamRequest):
    verdict = scam_detector.analyze(req.text, req.call_metadata)
    out = verdict.to_dict()
    if verdict.mha_alert:
        out["mha_alert_package"] = scam_detector.generate_mha_alert(
            verdict, req.victim_ref, req.caller_number
        )
    return out


@app.get("/api/scam/samples")
def scam_samples():
    return data.SAMPLE_TRANSCRIPTS


# --------------------------------------------------------------------------- #
# Module 2: Counterfeit Currency Identification
# --------------------------------------------------------------------------- #
@app.post("/api/counterfeit/analyze")
async def counterfeit_analyze(
    denomination: int = Form(...),
    serial_number: Optional[str] = Form(None),
    uv_feature_present: Optional[bool] = Form(None),
    image: UploadFile = File(...),
):
    img_bytes = await image.read()
    result = counterfeit.analyze_image(
        img_bytes, denomination, serial_number, uv_feature_present
    )
    return result.to_dict()


# --------------------------------------------------------------------------- #
# Module 3: Fraud Network Graph Intelligence
# --------------------------------------------------------------------------- #
@app.get("/api/fraud/analyze")
def fraud_analyze():
    return fraud_graph.analyze(data.FRAUD_RECORDS)


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
    return {**geospatial.analyze(data.GEO_POINTS), "points": data.GEO_POINTS}


# --------------------------------------------------------------------------- #
# Module 5: Citizen Fraud Shield (multi-channel chat)
# --------------------------------------------------------------------------- #
class ShieldRequest(BaseModel):
    message: str
    lang: str = "en"
    call_metadata: Optional[Dict] = None


@app.post("/api/shield/assess")
def shield_assess(req: ShieldRequest):
    return citizen_shield.assess(req.message, req.lang, req.call_metadata)


@app.get("/api/shield/languages")
def shield_languages():
    return citizen_shield.supported_languages()


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
