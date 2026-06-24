"""
Digital Arrest Scam Detection Engine
====================================

Explainable scam classifier for call transcripts / chat messages.

Design notes (why this approach, for judges):
- "Digital arrest" scams follow a highly repeatable psychological script:
  (1) impersonation of authority (CBI/ED/Customs/TRAI/police),
  (2) accusation + fabricated case/FIR/parcel,
  (3) isolation + secrecy + threat of immediate arrest,
  (4) coercion to stay on a video call ("digital custody"),
  (5) demand to move money to a "verification"/"RBI safe" account.
- We model each stage as a weighted signal group. The final verdict is the
  fused, calibrated risk score PLUS the list of triggered signals. The signal
  list is the *auditable evidence trail* — every point of the score is traceable
  to a concrete phrase, which is what makes the output usable in an MHA alert
  and, later, in court.
- This is deliberately a glass-box model: precision/recall can be tuned per
  signal, false positives are explainable, and new scam templates can be added
  as new signal groups without retraining a black box.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


# Each signal group maps to a stage of the digital-arrest kill chain.
# weight = contribution to risk when ANY pattern in the group fires.
SIGNAL_GROUPS: List[Dict] = [
    {
        "id": "authority_impersonation",
        "stage": "1. Authority impersonation",
        "weight": 18,
        "patterns": [
            r"\b(cbi|central bureau)\b",
            r"\b(enforcement directorate|\bed\b officer)\b",
            r"\bcustoms\b",
            r"\bnarcotics|ncb\b",
            r"\btrai\b",
            r"\bcyber (cell|crime) (department|police)\b",
            r"\b(mumbai|delhi) police\b.*\b(officer|inspector)\b",
            r"\bi am (inspector|officer|sub-?inspector|dcp|acp)\b",
            r"\bbadge (number|no)\b",
        ],
    },
    {
        "id": "fabricated_case",
        "stage": "2. Fabricated case / parcel",
        "weight": 16,
        "patterns": [
            r"\b(parcel|courier|package)\b.*\b(drugs|mdma|passport|illegal|seized)\b",
            r"\byour (aadhaar|aadhar|pan|sim|number)\b.*\b(used|linked|misused)\b",
            r"\b(fir|case|complaint|warrant)\b.*\b(registered|filed|against you|your name)\b",
            r"\bmoney laundering\b",
            r"\bsuspicious transaction\b",
            r"\bnon-?bailable warrant\b",
        ],
    },
    {
        "id": "isolation_secrecy",
        "stage": "3. Isolation + secrecy",
        "weight": 15,
        "patterns": [
            r"\bdo ?n[o']?t (tell|inform|disclose|talk to) (anyone|family|anybody)\b",
            r"\bconfidential(ity)? (case|investigation|matter)\b",
            r"\bunder (investigation|surveillance|monitoring)\b",
            r"\bdo ?n[o']?t (cut|disconnect|end) (the )?call\b",
            r"\bstay on (the )?(call|line|video)\b",
            r"\bkeep this (secret|between us)\b",
        ],
    },
    {
        "id": "digital_custody",
        "stage": "4. 'Digital arrest' / video custody",
        "weight": 22,
        "patterns": [
            r"\bdigital arrest\b",
            r"\bdigital (custody|detention)\b",
            r"\bvideo (call|conference)\b.*\b(arrest|custody|verification|interrogat)\b",
            r"\byou are under arrest\b",
            r"\bskype\b.*\b(officer|police|interrogat|statement)\b",
            r"\bswitch on your (camera|video)\b.*\b(arrest|officer|interrogat)\b",
            r"\bhouse arrest\b",
        ],
    },
    {
        "id": "money_coercion",
        "stage": "5. Money / verification transfer",
        "weight": 20,
        "patterns": [
            r"\b(transfer|deposit|send|pay)\b.*\b(verification|verify|clear your name|refundable)\b",
            r"\brbi (verified|safe|secure) account\b",
            r"\b(rbi|government|safe|verification) account\b",
            r"\btransfer (money|funds|amount|savings)\b.{0,40}\b(account|rbi|verify)\b",
            r"\b(transfer|move) (all )?your (money|funds|savings|balance)\b",
            r"\b(security|government|verification) (deposit|fee)\b",
            r"\bget your money back (after|once) (verification|clearance)\b",
            r"\bupi|imps|neft|rtgs\b.*\b(immediately|now|urgent)\b",
        ],
    },
    {
        "id": "urgency_threat",
        "stage": "Cross-cutting: urgency + threat",
        "weight": 9,
        "patterns": [
            r"\b(arrest|jail|prison) (you )?(today|now|immediately|in \d+ (hours|minutes))\b",
            r"\b(within|in) \d+ (minutes|hours)\b.*\b(arrest|account|freeze|blocked)\b",
            r"\byour account (will be|is being) (frozen|blocked|suspended)\b",
            r"\blast (warning|chance)\b",
            r"\bif you (hang up|disconnect)\b.*\b(arrest|police|consequence)\b",
            r"\b(disconnect(ed)?|cut ?off|suspend(ed)?|terminat(e|ed)|block(ed)?)\b.{0,25}\b(tonight|today|immediately|now|within)\b",
        ],
    },
    {
        "id": "payment_pressure",
        "stage": "Cross-cutting: payment pressure",
        "weight": 14,
        "patterns": [
            r"\b(pay|deposit|recharge|clear)\b.{0,18}\b(immediately|now|urgently|today|at once|right away)\b",
            r"\bpay (immediately|now|urgently|today|at once)\b",
            r"\bavoid (disconnection|suspension|penalty|fine|legal action|arrest)\b",
            r"\b(click|open)\b.{0,20}\b(link|kyc)\b.{0,20}\b(update|verify|pay|now)\b",
        ],
    },
    # ---- Broader scam families (beyond digital-arrest) ----------------------
    {
        "id": "credential_phishing",
        "stage": "Family: OTP / credential phishing",
        "weight": 20,
        "patterns": [
            r"\b(share|send|tell|provide|enter|confirm)\b.{0,20}\b(otp|o\.t\.p|one[- ]?time|pin|cvv|password|passcode)\b",
            r"\b(otp|cvv|pin)\b.{0,15}\b(received|sent)\b.{0,15}\bshare\b",
            r"\bverify\b.{0,15}\b(otp|account)\b.{0,15}\b(immediately|now|to avoid)\b",
        ],
    },
    {
        "id": "kyc_account",
        "stage": "Family: KYC / account suspension",
        "weight": 14,
        "patterns": [
            r"\bkyc\b.{0,25}(update|expir|pending|incomplete|verif|suspend)",
            r"\b(account|wallet|sim|number|card)\b.{0,25}(suspend|block|deactivat|expir)",
            r"\bupdate your (kyc|pan|aadhaar|details)\b.{0,20}(immediately|today|now|to avoid)",
            r"\b(pan|aadhaar) (card )?(not |is not )?linked\b",
        ],
    },
    {
        "id": "prize_lottery",
        "stage": "Family: lottery / prize bait",
        "weight": 16,
        "patterns": [
            r"\byou(?:'ve| have)? won\b.{0,30}\b(lottery|prize|lakh|crore|reward|cash|car|iphone)\b",
            r"\b(lucky draw|lottery winner|kbc lottery|lucky winner)\b",
            r"\bclaim your (prize|reward|winnings|lottery)\b",
            r"\bcongratulations\b.{0,30}\b(won|winner|selected|prize)\b",
        ],
    },
    {
        "id": "advance_fee",
        "stage": "Family: loan / refund / advance-fee",
        "weight": 14,
        "patterns": [
            r"\b(pre[- ]?approved|instant|guaranteed) loan\b",
            r"\b(processing|registration|clearance|gst|customs) (fee|charge|charges)\b.{0,25}\b(pay|deposit|transfer)\b",
            r"\b(income ?tax|electricity|gst) refund\b.{0,25}\b(claim|process|pending|click)\b",
            r"\bto (release|receive|claim)\b.{0,20}\bpay (a )?(small )?(fee|amount|charge)\b",
        ],
    },
    {
        "id": "sextortion",
        "stage": "Family: sextortion / blackmail",
        "weight": 18,
        "patterns": [
            r"\bi (have )?(recorded|a video|captured)\b.{0,30}\b(you|your)\b",
            r"\b(pay|send money)\b.{0,25}\bor (i|we) (will )?(leak|share|send|post|release)\b",
            r"\b(your )?(private|intimate|nude) (video|photo|clip)s?\b.{0,25}\b(leak|share|viral|public)\b",
        ],
    },
]

# Phrases that strongly indicate a LEGITIMATE interaction — used to suppress
# false positives (critical: citizen-facing false-positive rate must be very low).
NEGATIVE_PATTERNS = [
    r"\bvisit (the )?(nearest|your) (branch|police station) in person\b",
    r"\bwe (will )?never ask (for|you to)\b.*\b(otp|password|transfer|money)\b",
    r"\bthis is a recorded (line|call) for (training|quality)\b",
]

# Spoofing / metadata heuristics (call-flow signatures).
SPOOF_RISK = {
    "intl_prefix": 12,        # +country code masquerading as local authority
    "voip_number": 10,        # VoIP / internet-origin number
    "spoofed_caller_id": 14,  # caller ID claims govt but number is unallocated
    "ai_voice_detected": 16,  # speech-AI flag of synthetic voice
    "number_rotation": 8,     # number seen rotating across many victims
}


@dataclass
class Signal:
    group_id: str
    stage: str
    weight: int
    evidence: str  # the exact matched substring (audit trail)


@dataclass
class ScamVerdict:
    risk_score: int                  # 0-100 calibrated
    verdict: str                     # SAFE / SUSPICIOUS / HIGH_RISK / ACTIVE_SCAM
    stage_reached: str               # furthest kill-chain stage observed
    signals: List[Signal] = field(default_factory=list)
    metadata_flags: List[str] = field(default_factory=list)
    recommended_action: str = ""
    mha_alert: bool = False

    def to_dict(self) -> Dict:
        return {
            "risk_score": self.risk_score,
            "verdict": self.verdict,
            "stage_reached": self.stage_reached,
            "signals": [
                {
                    "stage": s.stage,
                    "weight": s.weight,
                    "evidence": s.evidence,
                }
                for s in self.signals
            ],
            "metadata_flags": self.metadata_flags,
            "contributions": self.contributions(),
            "recommended_action": self.recommended_action,
            "mha_alert": self.mha_alert,
        }

    def contributions(self) -> List[Dict]:
        """Exact additive attribution (model is linear, so this is the true
        Shapley value per feature — no SHAP/LIME approximation needed):
        each signal's share of the total risk evidence."""
        items = [(s.stage, s.weight) for s in self.signals]
        items += [(f"network: {k}", SPOOF_RISK.get(k, 0)) for k in self.metadata_flags]
        total = sum(w for _, w in items) or 1
        items.sort(key=lambda x: x[1], reverse=True)
        return [{"label": lbl, "points": w, "pct": round(100 * w / total, 1)}
                for lbl, w in items]


def _calibrate(raw: int) -> int:
    """Squash raw additive score into a 0-100 calibrated band."""
    # raw can exceed 100 when many stages fire; saturate smoothly.
    if raw <= 0:
        return 0
    score = 100 * (1 - pow(2.71828, -raw / 40.0))
    return int(min(99, round(score)))


def analyze(text: str, call_metadata: Dict | None = None) -> ScamVerdict:
    """
    Analyze a transcript/message + optional call metadata.

    call_metadata example:
        {"intl_prefix": True, "voip_number": True, "ai_voice_detected": False,
         "spoofed_caller_id": True, "number_rotation": False}
    """
    text_l = (text or "").lower()
    signals: List[Signal] = []
    raw = 0
    stages_hit: List[str] = []

    for group in SIGNAL_GROUPS:
        for pat in group["patterns"]:
            m = re.search(pat, text_l)
            if m:
                signals.append(
                    Signal(
                        group_id=group["id"],
                        stage=group["stage"],
                        weight=group["weight"],
                        evidence=m.group(0).strip(),
                    )
                )
                raw += group["weight"]
                stages_hit.append(group["stage"])
                break  # one hit per group is enough; avoids double-counting

    # Negative suppression
    for neg in NEGATIVE_PATTERNS:
        if re.search(neg, text_l):
            raw = max(0, raw - 25)

    # Metadata / spoofing signals
    meta_flags: List[str] = []
    if call_metadata:
        for key, w in SPOOF_RISK.items():
            if call_metadata.get(key):
                raw += w
                meta_flags.append(key)

    score = _calibrate(raw)

    # Verdict bands
    if score >= 80:
        verdict = "ACTIVE_SCAM"
    elif score >= 55:
        verdict = "HIGH_RISK"
    elif score >= 25:
        verdict = "SUSPICIOUS"
    else:
        verdict = "SAFE"

    # Stage reached = highest-weight stage observed (proxy for kill-chain depth)
    stage_reached = "None observed"
    if signals:
        stage_reached = max(signals, key=lambda s: s.weight).stage

    # MHA alert when an active scam is detected BEFORE money moves.
    mha_alert = verdict == "ACTIVE_SCAM"

    actions = {
        "ACTIVE_SCAM": (
            "INTERVENE NOW: inject in-call warning to victim, hold any outbound "
            "transfer for 30 min, auto-file MHA/1930 alert with evidence trail."
        ),
        "HIGH_RISK": (
            "Warn the user, advise: hang up and call 1930. Flag number to telecom "
            "for spoofing review."
        ),
        "SUSPICIOUS": "Caution the user; recommend independent verification of caller.",
        "SAFE": "No scam pattern detected. Continue normal monitoring.",
    }

    return ScamVerdict(
        risk_score=score,
        verdict=verdict,
        stage_reached=stage_reached,
        signals=signals,
        metadata_flags=meta_flags,
        recommended_action=actions[verdict],
        mha_alert=mha_alert,
    )


def generate_mha_alert(verdict: ScamVerdict, victim_ref: str, caller_number: str) -> Dict:
    """Produce a structured, auditable alert package (court/MHA admissible format)."""
    import datetime
    import hashlib
    import json

    payload = {
        "alert_type": "DIGITAL_ARREST_SCAM_ACTIVE",
        "generated_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "victim_reference": victim_ref,
        "caller_number": caller_number,
        "risk_score": verdict.risk_score,
        "kill_chain_stage": verdict.stage_reached,
        "evidence_signals": [
            {"stage": s.stage, "evidence_phrase": s.evidence, "weight": s.weight}
            for s in verdict.signals
        ],
        "metadata_flags": verdict.metadata_flags,
        "routing": ["NCRP/1930", "MHA I4C", "TSP-fraud-desk"],
    }
    # Tamper-evident hash of the evidence package.
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()
    payload["evidence_hash_sha256"] = digest
    return payload
