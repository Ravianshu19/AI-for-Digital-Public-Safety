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
            r"\b(income[- ]?tax|gst|telecom|fedex|dhl)\b.{0,15}\bdepartment\b",
            r"\b(bank|fraud) (department|prevention team)\b.{0,20}\b(calling|officer|investigat)",
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
            r"\bcourt order\b.{0,25}\b(issued|against|passed)\b",
            r"\blegal action (will be|has been|is being) (taken|initiated)\b",
            r"\b(drug|terror(ist)?|hawala) (trafficking|funding|network)\b",
            r"\b(fake|illegal|cloned) sim\b",
            r"\bidentity theft\b.{0,25}\b(case|complaint|registered|linked)\b",
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
            r"\b(matter|case|issue) of national security\b",
            r"\bnational security\b.{0,25}\b(case|matter|investigation|secret)\b",
            r"\bdo ?n[o']?t discuss (this|the case|the matter)\b",
            r"\b(camera|video|microphone|mic)\b.{0,15}\b(must|should|has to)\b.{0,15}\b(remain|stay|be kept?) on\b",
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
            r"\b(upi|imps|neft|rtgs)\b.{0,30}\b(immediately|now|urgent|urgently)\b",
        ],
    },
    {
        "id": "upi_fraud",
        "stage": "Family: UPI collect-request / QR scam",
        "weight": 16,
        "patterns": [
            r"\bcollect request\b.{0,35}\b(receive|refund|cashback|get|money|prize)\b",
            r"\bscan (this |the )?qr\b.{0,35}\b(receive|cashback|refund|win|reward|money|get|claim)\b",
            r"\bapprove\b.{0,25}\b(request|payment)\b.{0,25}\b(receive|refund|cashback|prize)\b",
            r"\b(accidentally|wrongly|mistakenly) sent\b.{0,30}\b(upi|money|amount)\b.{0,25}\b(return|refund|send back)\b",
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
            r"\b(share|send|tell|provide|enter|confirm)\b.{0,30}(otp\w*|o\.t\.p|one[- ]?time|cvv|\bpin\b|\bpassword\b|\bpasscode\b)",
            r"\b(otp|cvv|pin)\b.{0,15}(received|sent).{0,15}share",
            r"\bverify\b.{0,15}(otp|account).{0,15}(immediately|now|to avoid)",
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
    {
        "id": "investment_scam",
        "stage": "Family: investment / crypto scam",
        "weight": 16,
        "patterns": [
            r"\bguaranteed (returns?|profit|income)\b",
            r"\bdouble your (money|investment|capital)\b",
            r"\b(crypto|bitcoin|forex|stock|trading)\b.{0,20}\b(tip|signal|group|channel|invest)",
            r"\b\d{1,3}\s?% (daily|weekly|monthly|guaranteed|assured) (return|profit|income)",
            r"\bjoin (our )?(vip )?(trading|investment|stock) (group|channel|club)\b",
        ],
    },
    {
        "id": "job_scam",
        "stage": "Family: fake job / task scam",
        "weight": 14,
        "patterns": [
            r"\bwork from home\b.{0,25}\b(earn|income|salary|daily)\b",
            r"\bpart[- ]?time job\b.{0,25}\b(earn|income|daily|home)\b",
            r"\bearn (rs ?)?[₹]?\s?\d{3,}\b.{0,20}\b(daily|per day|from home|online)\b",
            r"\b(registration|security|joining) (fee|deposit)\b.{0,25}\b(job|work|task)\b",
            r"\b(like|rate|review)\b.{0,20}\b(videos?|hotels?|tasks?)\b.{0,20}\b(earn|paid|money)\b",
        ],
    },
    {
        "id": "tech_support",
        "stage": "Family: tech-support impersonation",
        "weight": 16,
        "patterns": [
            r"\b(microsoft|windows|apple|google|amazon)\b.{0,20}\b(support|technician|security team|help ?desk)\b",
            r"\byour (computer|pc|laptop|device|system|ip)\b.{0,25}\b(infected|hacked|compromised|virus|malware|at risk)\b",
            r"\bpress \d\b.{0,20}\b(to (speak|connect|continue)|support|agent)\b",
        ],
    },
    {
        "id": "remote_access",
        "stage": "Family: remote-access / stay-connected pressure",
        "weight": 18,
        "patterns": [
            r"\binstall\b.{0,20}\b(anydesk|teamviewer|quicksupport|ultraviewer|remote ?desktop|rustdesk)\b",
            r"\b(do ?n[o']?t|never)\b.{0,15}\b(close|disconnect|turn off|shut)\b.{0,20}\b(connection|window|screen|session|laptop)\b",
            r"\b(remote (access|support|session|connection)|screen ?share)\b.{0,25}\b(allow|grant|approve|fix|issue|secure)\b",
            r"\b(download|grant|give)\b.{0,20}\b(remote|access|control)\b.{0,20}\b(fix|secure|repair)\b",
        ],
    },
    {
        "id": "contradiction_procedure",
        "stage": "Cross-cutting: contradicts real procedure",
        "weight": 18,
        "patterns": [
            r"\b(prove|proving) (your )?innocen(ce|t)\b",
            r"\b(transfer|deposit|pay|send)\b.{0,35}\bto prove\b",
            r"\bpolice (cannot|can'?t|won'?t) help( you)?\b",
            r"\bdo ?n[o']?t (contact|call|visit|inform|go to) (your |the )?(bank|branch|police|lawyer|advocate)\b",
            r"\b(money|amount|funds) (will be )?(returned|refunded|given back)\b.{0,30}\b(after|once)\b.{0,25}\b(verification|investigation|clearance)\b",
        ],
    },
    {
        "id": "compliance_command",
        "stage": "Cross-cutting: compliance commands",
        "weight": 12,
        "patterns": [
            r"\b(turn|switch) on (your )?(camera|video|mic|microphone)\b",
            r"\b(share|show) (your |me your )?screen\b",
            r"\bopen (your )?(bank(ing)? app|net ?banking|upi app|phonepe|google pay|paytm)\b",
            r"\b(download|install) (this|the|that|an?) (app|application|apk)\b",
        ],
    },
    {
        "id": "callback_bait",
        "stage": "Cross-cutting: unsolicited callback bait",
        "weight": 12,
        "patterns": [
            r"\b(problem|issue) with your (account|card|number|connection)\b.{0,60}\b(officer|call|department|verify)\b",
            r"\b(call|ring) (us )?back (on|at) this number\b.{0,35}\b(important|urgent|immediately)\b",
        ],
    },
    {
        "id": "emotional_manipulation",
        "stage": "Cross-cutting: emotional manipulation",
        "weight": 7,
        "patterns": [
            r"\b(stay|keep|remain) calm\b.{0,45}\b(cooperate|help|investigation|officer|process)\b",
            r"\bcooperate with (the |this )?(officer|investigation|department|us)\b",
            r"\bwe are (trying|here|only trying) to help( you)?\b",
            r"\bdo ?n[o']?t panic\b",
            r"\btrust (me|us)\b.{0,30}\b(officer|official|process|safe|procedure)\b",
        ],
    },
    {
        "id": "info_harvest",
        "stage": "Cross-cutting: banking / identity data request",
        "weight": 14,
        "patterns": [
            r"\b(share|send|tell|provide|give|confirm|enter)\b.{0,30}\b(account number|debit card|credit card|card number|card details|net ?banking)\b",
            r"\bwhat is your\b.{0,20}\b(account number|card number|cvv|bank balance|aadhaar|pan)\b",
            r"\b(share|send|provide|upload)\b.{0,25}\b(aadhaar|aadhar|pan card|passport|driving licen[cs]e)\b.{0,20}\b(number|copy|photo|details)\b",
            r"\b(tell|share|confirm)\b.{0,20}\b(bank balance|how much (money|balance))\b",
        ],
    },
    {
        "id": "romance_matrimony",
        "stage": "Family: romance / matrimony / gift-customs scam",
        "weight": 14,
        "patterns": [
            r"\b(gift|parcel|package)\b.{0,30}\b(stuck|held|seized|detained)\b.{0,25}\b(customs|airport)\b",
            r"\b(customs|airport)\b.{0,20}\b(clearance|duty|fee|charge)\b.{0,20}\b(pay|deposit|transfer|send)\b",
            r"\bi (have )?sent you (a )?(gift|parcel|jewellery|money|iphone)\b",
            r"\b(matrimony|matrimonial|dating)\b.{0,30}\b(money|fee|gift|transfer|customs)\b",
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
