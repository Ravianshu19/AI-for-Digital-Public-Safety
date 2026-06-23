"""
Citizen Fraud Shield (multi-channel conversational layer)
=========================================================

A guided, low-false-positive assistant that a citizen can reach over
WhatsApp / IVR / app. It wraps the scam_detector engine and returns a
plain-language verdict, next steps, and a guided NCRP/1930 report draft, in the
citizen's chosen language.

Translations are bundled for the verdict scaffold (the high-frequency strings);
free-text advice falls back to English in this prototype. In production this layer
would call an LLM + IndicTrans for full 12-language coverage.
"""

from __future__ import annotations

from typing import Dict

from scam_detector import analyze


LANGS = {
    "en": "English", "hi": "हिन्दी", "bn": "বাংলা", "te": "తెలుగు",
    "mr": "मराठी", "ta": "தமிழ்", "gu": "ગુજરાતી", "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം", "pa": "ਪੰਜਾਬੀ", "or": "ଓଡ଼ିଆ", "as": "অসমীয়া",
}

VERDICT_MSG = {
    "ACTIVE_SCAM": {
        "en": "🚨 This is almost certainly a SCAM. Do NOT transfer any money. Hang up now.",
        "hi": "🚨 यह लगभग निश्चित रूप से एक धोखाधड़ी है। कोई पैसा ट्रांसफर न करें। तुरंत कॉल काट दें।",
        "ta": "🚨 இது கிட்டத்தட்ட நிச்சயமாக மோசடி. பணம் அனுப்ப வேண்டாம். உடனே துண்டியுங்கள்.",
        "bn": "🚨 এটি প্রায় নিশ্চিতভাবে একটি প্রতারণা। কোনো টাকা পাঠাবেন না। এখনই কল কাটুন।",
        "te": "🚨 ఇది దాదాపు ఖచ్చితంగా మోసం. డబ్బు బదిలీ చేయవద్దు. వెంటనే కాల్ కట్ చేయండి.",
    },
    "HIGH_RISK": {
        "en": "⚠️ This looks like a scam. Real police/CBI NEVER arrest you over a video call or ask for money transfers. Hang up and call 1930.",
        "hi": "⚠️ यह धोखाधड़ी जैसा लगता है। असली पुलिस/CBI कभी वीडियो कॉल पर गिरफ्तार नहीं करती। कॉल काटें और 1930 पर कॉल करें।",
    },
    "SUSPICIOUS": {
        "en": "🟡 Be careful. This could be a scam. Verify the caller independently before doing anything.",
        "hi": "🟡 सावधान रहें। यह धोखाधड़ी हो सकती है। कुछ भी करने से पहले स्वतंत्र रूप से सत्यापित करें।",
    },
    "SAFE": {
        "en": "🟢 No clear scam pattern detected. Still, never share OTP or transfer money to strangers.",
        "hi": "🟢 कोई स्पष्ट धोखाधड़ी नहीं मिली। फिर भी OTP साझा न करें या अनजान को पैसे न भेजें।",
    },
}

GOLDEN_RULES = {
    "en": [
        "No real government agency conducts a 'digital arrest' over video call.",
        "Police/CBI/ED never ask you to transfer money to 'verify' it.",
        "Never share OTP, PIN, or screen with anyone on a call.",
        "When in doubt: hang up and call the national cyber helpline 1930.",
    ],
}


def _pick(d: Dict[str, str], lang: str) -> str:
    return d.get(lang) or d.get("en")


def assess(message: str, lang: str = "en", call_metadata: Dict | None = None) -> Dict:
    if lang not in LANGS:
        lang = "en"
    verdict = analyze(message, call_metadata)

    report_draft = None
    if verdict.verdict in ("ACTIVE_SCAM", "HIGH_RISK"):
        report_draft = {
            "portal": "https://cybercrime.gov.in  (or call 1930)",
            "category": "Online Financial Fraud > Digital Arrest / Impersonation",
            "auto_filled": {
                "incident_type": "Digital arrest / government impersonation scam",
                "risk_score": verdict.risk_score,
                "evidence_phrases": [s.evidence for s in verdict.signals],
                "kill_chain_stage": verdict.stage_reached,
            },
            "next_steps": [
                "Do not transfer any money.",
                "Save call recording / screenshots as evidence.",
                "Call 1930 within the golden hour to freeze any transfer.",
                "File full complaint at cybercrime.gov.in.",
            ],
        }

    return {
        "language": LANGS[lang],
        "lang_code": lang,
        "verdict": verdict.verdict,
        "risk_score": verdict.risk_score,
        "message": _pick(VERDICT_MSG[verdict.verdict], lang),
        "why": [f"{s.stage}: \"{s.evidence}\"" for s in verdict.signals[:5]],
        "golden_rules": GOLDEN_RULES["en"],
        "guided_report": report_draft,
        "channels": ["WhatsApp", "IVR (toll-free)", "Mobile app"],
    }


def supported_languages() -> Dict[str, str]:
    return LANGS
