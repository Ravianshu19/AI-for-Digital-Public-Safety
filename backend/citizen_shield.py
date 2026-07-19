"""
Citizen Fraud Shield (multi-channel conversational layer)
=========================================================

A guided, low-false-positive assistant a citizen reaches over WhatsApp / IVR /
app. It wraps the scam_detector engine and answers ENTIRELY in the citizen's
chosen language — verdict, reasons, next steps and golden rules — so a Hindi
user gets a pure-Hindi reply, a Tamil user pure Tamil, and so on.

Hindi is fully authored and verified. English is the base. Other languages
fall back to English for any string not yet translated (add verified native
strings to the tables below to complete them — machine-guessed translations
are deliberately avoided).
"""

from __future__ import annotations

from typing import Dict, List

from scam_detector import analyze


LANGS = {
    "en": "English", "hi": "हिन्दी", "bn": "বাংলা", "te": "తెలుగు",
    "mr": "मराठी", "ta": "தமிழ்", "gu": "ગુજરાતી", "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം", "pa": "ਪੰਜਾਬੀ", "or": "ଓଡ଼ିଆ", "as": "অসমীয়া",
}

VERDICT_MSG = {
    "ACTIVE_SCAM": {
        "en": "🚨 This is almost certainly a SCAM. Do NOT transfer any money. Hang up now.",
        "hi": "🚨 यह लगभग निश्चित रूप से धोखाधड़ी है। कोई पैसा ट्रांसफर न करें। तुरंत कॉल काट दें।",
        "ta": "🚨 இது கிட்டத்தட்ட நிச்சயமாக மோசடி. பணம் அனுப்ப வேண்டாம். உடனே துண்டியுங்கள்.",
        "bn": "🚨 এটি প্রায় নিশ্চিতভাবে একটি প্রতারণা। কোনো টাকা পাঠাবেন না। এখনই কল কাটুন।",
        "te": "🚨 ఇది దాదాపు ఖచ్చితంగా మోసం. డబ్బు బదిలీ చేయవద్దు. వెంటనే కాల్ కట్ చేయండి.",
    },
    "HIGH_RISK": {
        "en": "⚠️ This looks like a scam. Real police/CBI NEVER arrest you over a video call or ask for money transfers. Hang up and call 1930.",
        "hi": "⚠️ यह धोखाधड़ी जैसा लगता है। असली पुलिस/सीबीआई कभी वीडियो कॉल पर गिरफ्तार नहीं करती और न पैसे मांगती है। कॉल काटें और 1930 पर कॉल करें।",
    },
    "SUSPICIOUS": {
        "en": "🟡 Be careful. This could be a scam. Verify the caller independently before doing anything.",
        "hi": "🟡 सावधान रहें। यह धोखाधड़ी हो सकती है। कुछ भी करने से पहले कॉल करने वाले की स्वतंत्र रूप से जाँच करें।",
    },
    "SAFE": {
        "en": "🟢 No clear scam pattern detected. Still, never share OTP or transfer money to strangers.",
        "hi": "🟢 कोई स्पष्ट धोखाधड़ी नहीं मिली। फिर भी OTP साझा न करें और अनजान व्यक्ति को पैसे न भेजें।",
    },
}

# English stage label -> localized label (used to build the "why" reasons).
STAGE_I18N = {
    "1. Authority impersonation": {"hi": "1. अधिकारी होने का झूठा दावा"},
    "2. Fabricated case / parcel": {"hi": "2. झूठा केस / पार्सल"},
    "3. Isolation + secrecy": {"hi": "3. अलग-थलग करना और गोपनीयता"},
    "4. 'Digital arrest' / video custody": {"hi": "4. 'डिजिटल अरेस्ट' / वीडियो हिरासत"},
    "5. Money / verification transfer": {"hi": "5. पैसे / 'सत्यापन' के लिए ट्रांसफर"},
    "Family: UPI collect-request / QR scam": {"hi": "UPI कलेक्ट-रिक्वेस्ट / QR धोखाधड़ी"},
    "Cross-cutting: urgency + threat": {"hi": "दबाव: जल्दबाज़ी और धमकी"},
    "Cross-cutting: payment pressure": {"hi": "दबाव: भुगतान के लिए दबाव"},
    "Family: OTP / credential phishing": {"hi": "OTP / पासवर्ड चुराने की कोशिश"},
    "Family: KYC / account suspension": {"hi": "केवाईसी / खाता बंद होने का डर"},
    "Family: lottery / prize bait": {"hi": "लॉटरी / इनाम का लालच"},
    "Family: loan / refund / advance-fee": {"hi": "लोन / रिफंड / अग्रिम-शुल्क धोखाधड़ी"},
    "Family: sextortion / blackmail": {"hi": "अश्लील वीडियो से ब्लैकमेल"},
    "Family: investment / crypto scam": {"hi": "निवेश / क्रिप्टो धोखाधड़ी"},
    "Family: fake job / task scam": {"hi": "फर्ज़ी नौकरी / टास्क धोखाधड़ी"},
    "Family: tech-support impersonation": {"hi": "फर्ज़ी टेक-सपोर्ट"},
    "Family: remote-access / stay-connected pressure": {"hi": "रिमोट-एक्सेस / जुड़े रहने का दबाव"},
    "Cross-cutting: contradicts real procedure": {"hi": "असली प्रक्रिया के विपरीत बातें"},
    "Cross-cutting: compliance commands": {"hi": "आदेश मानने का दबाव"},
    "Cross-cutting: emotional manipulation": {"hi": "भावनात्मक हेरफेर"},
    "Cross-cutting: banking / identity data request": {"hi": "बैंक / पहचान की जानकारी माँगना"},
    "Cross-cutting: unsolicited callback bait": {"hi": "वापस कॉल कराने का जाल"},
    "Family: romance / matrimony / gift-customs scam": {"hi": "रोमांस / विवाह / गिफ्ट-कस्टम धोखाधड़ी"},
    "Cross-cutting: malicious link": {"hi": "खतरनाक लिंक"},
    "Cross-cutting: suspicious link": {"hi": "संदिग्ध लिंक"},
}

NEXT_STEPS = {
    "en": [
        "Do not transfer any money.",
        "Save call recording / screenshots as evidence.",
        "Call 1930 within the golden hour to freeze any transfer.",
        "File full complaint at cybercrime.gov.in.",
    ],
    "hi": [
        "कोई पैसा ट्रांसफर न करें।",
        "कॉल रिकॉर्डिंग / स्क्रीनशॉट सबूत के तौर पर सुरक्षित रखें।",
        "पहले घंटे के भीतर 1930 पर कॉल करें ताकि ट्रांसफर रोका जा सके।",
        "cybercrime.gov.in पर पूरी शिकायत दर्ज करें।",
    ],
}

GOLDEN_RULES = {
    "en": [
        "No real government agency conducts a 'digital arrest' over video call.",
        "Police/CBI/ED never ask you to transfer money to 'verify' it.",
        "Never share OTP, PIN, or screen with anyone on a call.",
        "When in doubt: hang up and call the national cyber helpline 1930.",
    ],
    "hi": [
        "कोई भी असली सरकारी एजेंसी वीडियो कॉल पर 'डिजिटल अरेस्ट' नहीं करती।",
        "पुलिस/सीबीआई/ईडी 'सत्यापन' के लिए कभी पैसे ट्रांसफर करने को नहीं कहती।",
        "कॉल पर किसी के साथ OTP, PIN या स्क्रीन कभी साझा न करें।",
        "संदेह हो तो कॉल काटें और राष्ट्रीय साइबर हेल्पलाइन 1930 पर कॉल करें।",
    ],
}

GREETING = {
    "en": "🛡 Namaste! I'm Prahari Shield. Tell me about any suspicious call, message or payment request and I'll check it for you instantly.",
    "hi": "🛡 नमस्ते! मैं प्रहरी शील्ड हूँ। किसी भी संदिग्ध कॉल, संदेश या पैसे की माँग के बारे में बताइए, मैं तुरंत जाँच कर बताऊँगा।",
}

REPORT_LABEL = {
    "en": {"portal": "https://cybercrime.gov.in  (or call 1930)",
           "category": "Online Financial Fraud > Digital Arrest / Impersonation",
           "incident": "Digital arrest / government impersonation scam"},
    "hi": {"portal": "https://cybercrime.gov.in  (या 1930 पर कॉल करें)",
           "category": "ऑनलाइन वित्तीय धोखाधड़ी > डिजिटल अरेस्ट / फर्ज़ी अधिकारी",
           "incident": "डिजिटल अरेस्ट / सरकारी अधिकारी बनकर धोखाधड़ी"},
}

CHANNELS = {
    "en": ["WhatsApp", "IVR (toll-free)", "Mobile app"],
    "hi": ["WhatsApp", "IVR (टोल-फ्री)", "मोबाइल ऐप"],
}

DANGER_LINK = {"en": "⚠ Dangerous link", "hi": "⚠ खतरनाक लिंक"}


def _pick(d: Dict[str, str], lang: str) -> str:
    return d.get(lang) or d.get("en")


def _stage(stage: str, lang: str) -> str:
    return STAGE_I18N.get(stage, {}).get(lang, stage)


def assess(message: str, lang: str = "en", call_metadata: Dict | None = None) -> Dict:
    if lang not in LANGS:
        lang = "en"
    verdict = analyze(message, call_metadata)

    report_draft = None
    if verdict.verdict in ("ACTIVE_SCAM", "HIGH_RISK"):
        rl = REPORT_LABEL.get(lang, REPORT_LABEL["en"])
        report_draft = {
            "portal": rl["portal"],
            "category": rl["category"],
            "auto_filled": {
                "incident_type": rl["incident"],
                "risk_score": verdict.risk_score,
                "evidence_phrases": [s.evidence for s in verdict.signals],
                "kill_chain_stage": _stage(verdict.stage_reached, lang),
            },
            "next_steps": NEXT_STEPS.get(lang, NEXT_STEPS["en"]),
        }

    dl = DANGER_LINK.get(lang, DANGER_LINK["en"])
    why = [f'{_stage(s.stage, lang)}: "{s.evidence}"' for s in verdict.signals[:5]]
    why += [f"{dl}: {f['url']}" for f in (verdict.url_analysis or {}).get("findings", [])
            if f["risk"] >= 22][:2]

    return {
        "language": LANGS[lang],
        "lang_code": lang,
        "verdict": verdict.verdict,
        "risk_score": verdict.risk_score,
        "message": _pick(VERDICT_MSG[verdict.verdict], lang),
        "why": why,
        "golden_rules": GOLDEN_RULES.get(lang, GOLDEN_RULES["en"]),
        "guided_report": report_draft,
        "channels": CHANNELS.get(lang, CHANNELS["en"]),
    }


def supported_languages() -> Dict[str, str]:
    return LANGS


# UI strings for the chat panel, per language (greeting + one-tap samples +
# labels). Each sample carries the message the citizen would send in that
# language, so Hindi users interact entirely in Hindi.
_UI = {
    "en": {
        "greeting": GREETING["en"],
        "placeholder": "Describe the message, or 📎 upload a screenshot…",
        "send": "Send", "typing": "typing…", "recent": "Recent checks",
        "actions_title": "What to do right now",
        "default_actions": [
            "Suspicious call or message? Don't act — check it here first.",
            "Never share OTP, PIN or password with anyone.",
            "Money already sent? Call 1930 now — the first hour matters most.",
        ],
        "samples": [
            ["🚨 Digital arrest", "CBI officer says I'm under digital arrest and must transfer money to an RBI account."],
            ["⚡ Electricity cut", "Your electricity will be disconnected tonight. Pay immediately using this link to avoid disconnection."],
            ["🎰 Lottery win", "Congratulations! You have won ₹25 lakh in the KBC lottery. Pay a small processing fee to claim."],
        ],
        "safe_actions": [
            "No scam signals found — no action needed.",
            "Still unsure? Call the official number from the bank's website, never the one in the message.",
        ],
        "no_checks": "No checks yet — tap a sample under the chat.",
        "reading": "Reading the screenshot…",
        "risk_word": "Risk", "file_label": "📋 I can file this for you:",
        "ocr_label": "📄 OCR text",
        "verdict_names": {"ACTIVE_SCAM": "ACTIVE SCAM", "HIGH_RISK": "HIGH RISK",
                          "SUSPICIOUS": "SUSPICIOUS", "SAFE": "SAFE"},
    },
    "hi": {
        "greeting": GREETING["hi"],
        "placeholder": "संदेश यहाँ लिखिए, या 📎 स्क्रीनशॉट भेजिए…",
        "send": "भेजें", "typing": "जाँच हो रही है…", "recent": "हाल की जाँचें",
        "actions_title": "अभी क्या करें",
        "default_actions": [
            "संदिग्ध कॉल या संदेश? कुछ करने से पहले यहाँ जाँच करें।",
            "OTP, PIN या पासवर्ड किसी को न बताएँ।",
            "पैसे भेज दिए? तुरंत 1930 पर कॉल करें — पहला घंटा सबसे ज़रूरी है।",
        ],
        "samples": [
            ["🚨 डिजिटल अरेस्ट", "सीबीआई अधिकारी कह रहा है कि मैं डिजिटल अरेस्ट में हूँ और मुझे आरबीआई खाते में पैसे ट्रांसफर करने होंगे।"],
            ["⚡ बिजली कटेगी", "आज रात आपकी बिजली काट दी जाएगी। कटौती से बचने के लिए तुरंत इस लिंक से भुगतान करें।"],
            ["🎰 लॉटरी जीती", "बधाई हो! आपने केबीसी लॉटरी में ₹25 लाख जीते हैं। दावा करने के लिए थोड़ा प्रोसेसिंग शुल्क भरें।"],
        ],
        "safe_actions": [
            "कोई धोखाधड़ी का संकेत नहीं मिला — कुछ करने की ज़रूरत नहीं।",
            "फिर भी संदेह हो? बैंक की आधिकारिक वेबसाइट का नंबर मिलाएँ, संदेश में दिए नंबर पर नहीं।",
        ],
        "no_checks": "अभी कोई जाँच नहीं — नीचे कोई नमूना चुनें।",
        "reading": "स्क्रीनशॉट पढ़ा जा रहा है…",
        "risk_word": "जोखिम", "file_label": "📋 मैं आपके लिए यह दर्ज कर सकता हूँ:",
        "ocr_label": "📄 पढ़ा गया टेक्स्ट",
        "verdict_names": {"ACTIVE_SCAM": "सक्रिय धोखाधड़ी", "HIGH_RISK": "उच्च जोखिम",
                          "SUSPICIOUS": "संदिग्ध", "SAFE": "सुरक्षित"},
    },
}


def ui_strings(lang: str) -> Dict:
    return _UI.get(lang, _UI["en"])
