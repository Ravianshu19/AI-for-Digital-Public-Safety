"""
Citizen Fraud Shield (multi-channel conversational layer)
=========================================================

A guided, low-false-positive assistant a citizen reaches over WhatsApp / IVR /
app. It wraps the scam_detector engine and answers ENTIRELY in the citizen's
chosen language — verdict, reasons, next steps and golden rules — so a Hindi
user gets a pure-Hindi reply, a Tamil user pure Tamil, and so on.

Only languages that are FULLY authored are offered in the picker — English,
हिन्दी, தமிழ் and বাংলা. We deliberately do not list a language we cannot answer
in end-to-end: a half-translated safety tool that silently drops back to English
mid-conversation is worse than one that is honest about its coverage. Adding a
language = filling the tables below with verified native strings.
"""

from __future__ import annotations

from typing import Dict, List

from scam_detector import analyze


LANGS = {
    "en": "English", "hi": "हिन्दी", "ta": "தமிழ்", "bn": "বাংলা",
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
        "ta": "⚠️ இது மோசடி போல் தெரிகிறது. உண்மையான காவல்துறை/சிபிஐ வீடியோ அழைப்பில் கைது செய்யாது, பணமும் கேட்காது. அழைப்பைத் துண்டித்து 1930 ஐ அழையுங்கள்.",
        "bn": "⚠️ এটি প্রতারণা বলে মনে হচ্ছে। আসল পুলিশ/সিবিআই কখনও ভিডিও কলে গ্রেপ্তার করে না বা টাকা চায় না। কল কেটে ১৯৩০ নম্বরে ফোন করুন।",
    },
    "SUSPICIOUS": {
        "en": "🟡 Be careful. This could be a scam. Verify the caller independently before doing anything.",
        "hi": "🟡 सावधान रहें। यह धोखाधड़ी हो सकती है। कुछ भी करने से पहले कॉल करने वाले की स्वतंत्र रूप से जाँच करें।",
        "ta": "🟡 கவனமாக இருங்கள். இது மோசடியாக இருக்கலாம். எதுவும் செய்வதற்கு முன் அழைப்பாளரைத் தனியாக உறுதிப்படுத்துங்கள்.",
        "bn": "🟡 সাবধান থাকুন। এটি প্রতারণা হতে পারে। কিছু করার আগে কলকারীকে স্বাধীনভাবে যাচাই করুন।",
    },
    "SAFE": {
        "en": "🟢 No clear scam pattern detected. Still, never share OTP or transfer money to strangers.",
        "hi": "🟢 कोई स्पष्ट धोखाधड़ी नहीं मिली। फिर भी OTP साझा न करें और अनजान व्यक्ति को पैसे न भेजें।",
        "ta": "🟢 தெளிவான மோசடி அறிகுறி இல்லை. இருப்பினும் OTP ஐப் பகிரவோ அந்நியருக்குப் பணம் அனுப்பவோ வேண்டாம்.",
        "bn": "🟢 স্পষ্ট প্রতারণার লক্ষণ পাওয়া যায়নি। তবুও OTP শেয়ার করবেন না বা অচেনা কাউকে টাকা পাঠাবেন না।",
    },
}

# English stage label -> localized label (used to build the "why" reasons).
STAGE_I18N = {
    "1. Authority impersonation": {"hi": "1. अधिकारी होने का झूठा दावा", "ta": "1. அதிகாரி என்று பொய் கூறுதல்", "bn": "১. কর্মকর্তা সেজে প্রতারণা"},
    "2. Fabricated case / parcel": {"hi": "2. झूठा केस / पार्सल", "ta": "2. போலி வழக்கு / பார்சல்", "bn": "২. বানানো মামলা / পার্সেল"},
    "3. Isolation + secrecy": {"hi": "3. अलग-थलग करना और गोपनीयता", "ta": "3. தனிமைப்படுத்துதல் + இரகசியம்", "bn": "৩. একা করে ফেলা ও গোপনীয়তা"},
    "4. 'Digital arrest' / video custody": {"hi": "4. 'डिजिटल अरेस्ट' / वीडियो हिरासत", "ta": "4. 'டிஜிட்டல் கைது' / வீடியோ காவல்", "bn": "৪. 'ডিজিটাল অ্যারেস্ট' / ভিডিও হেফাজত"},
    "5. Money / verification transfer": {"hi": "5. पैसे / 'सत्यापन' के लिए ट्रांसफर", "ta": "5. பணம் / 'சரிபார்ப்பு' பரிமாற்றம்", "bn": "৫. টাকা / 'যাচাইয়ের' জন্য ট্রান্সফার"},
    "Family: UPI collect-request / QR scam": {"hi": "UPI कलेक्ट-रिक्वेस्ट / QR धोखाधड़ी"},
    "Cross-cutting: urgency + threat": {"hi": "दबाव: जल्दबाज़ी और धमकी", "ta": "அழுத்தம்: அவசரம் + மிரட்டல்", "bn": "চাপ: তাড়াহুড়ো ও হুমকি"},
    "Cross-cutting: payment pressure": {"hi": "दबाव: भुगतान के लिए दबाव"},
    "Family: OTP / credential phishing": {"hi": "OTP / पासवर्ड चुराने की कोशिश", "ta": "OTP / கடவுச்சொல் திருட்டு", "bn": "OTP / পাসওয়ার্ড চুরির চেষ্টা"},
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
    "Cross-cutting: malicious link": {"hi": "खतरनाक लिंक", "ta": "ஆபத்தான இணைப்பு", "bn": "বিপজ্জনক লিঙ্ক"},
    "Cross-cutting: suspicious link": {"hi": "संदिग्ध लिंक", "ta": "சந்தேகத்திற்குரிய இணைப்பு", "bn": "সন্দেহজনক লিঙ্ক"},
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
    "ta": [
        "எந்தப் பணத்தையும் அனுப்ப வேண்டாம்.",
        "அழைப்புப் பதிவு / திரைப்படங்களை ஆதாரமாகச் சேமியுங்கள்.",
        "முதல் மணி நேரத்திற்குள் 1930 ஐ அழைத்துப் பரிமாற்றத்தை நிறுத்துங்கள்.",
        "cybercrime.gov.in இல் முழு புகாரைப் பதிவு செய்யுங்கள்.",
    ],
    "bn": [
        "কোনো টাকা পাঠাবেন না।",
        "কল রেকর্ডিং / স্ক্রিনশট প্রমাণ হিসেবে সংরক্ষণ করুন।",
        "প্রথম ঘণ্টার মধ্যে ১৯৩০ নম্বরে ফোন করে ট্রান্সফার আটকান।",
        "cybercrime.gov.in-এ সম্পূর্ণ অভিযোগ দায়ের করুন।",
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
    "ta": [
        "எந்த உண்மையான அரசு அமைப்பும் வீடியோ அழைப்பில் 'டிஜிட்டல் கைது' செய்வதில்லை.",
        "காவல்துறை/சிபிஐ/ED 'சரிபார்ப்புக்காக' பணம் அனுப்பச் சொல்வதில்லை.",
        "அழைப்பில் யாருடனும் OTP, PIN அல்லது திரையைப் பகிர வேண்டாம்.",
        "சந்தேகம் என்றால் அழைப்பைத் துண்டித்து 1930 ஐ அழையுங்கள்.",
    ],
    "bn": [
        "কোনো প্রকৃত সরকারি সংস্থা ভিডিও কলে 'ডিজিটাল অ্যারেস্ট' করে না।",
        "পুলিশ/সিবিআই/ইডি 'যাচাইয়ের' জন্য কখনও টাকা পাঠাতে বলে না।",
        "কলে কারও সঙ্গে OTP, PIN বা স্ক্রিন শেয়ার করবেন না।",
        "সন্দেহ হলে কল কেটে জাতীয় সাইবার হেল্পলাইন ১৯৩০-এ ফোন করুন।",
    ],
}

GREETING = {
    "ta": "🛡 வணக்கம்! நான் பிரஹரி ஷீல்ட். சந்தேகமான அழைப்பு, செய்தி அல்லது பணக் கோரிக்கை பற்றிச் சொல்லுங்கள் — உடனே சரிபார்க்கிறேன்.",
    "bn": "🛡 নমস্কার! আমি প্রহরী শিল্ড। সন্দেহজনক কল, বার্তা বা টাকার অনুরোধ সম্পর্কে বলুন — আমি সঙ্গে সঙ্গে যাচাই করে দেব।",
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

DANGER_LINK = {"en": "⚠ Dangerous link", "hi": "⚠ खतरनाक लिंक",
               "ta": "⚠ ஆபத்தான இணைப்பு", "bn": "⚠ বিপজ্জনক লিঙ্ক"}


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
        "guard_other_q": "None of these — tell me what they said",
        "guard_other_ph": "Type what the caller said…",
        "guard_other_btn": "Check it",
        "guard_cta": "🔴 I'm on a suspicious call RIGHT NOW",
        "guard_title": "Live Call Guard",
        "guard_sub": "Tap what the caller is doing. I'll tell you what to do at each step — while you are still on the call.",
        "guard_exit": "← Back to chat",
        "guard_steps": [["They say they are Police / CBI / Customs / TRAI", "Real officers do not phone you like this. Ask which station, then hang up and call that station yourself."], ["They say there is a case, parcel, FIR or warrant in my name", "No agency informs you of a case by phone call. This is a script — it is not real."], ["They told me not to tell anyone / keep it secret", "This is the trap. Tell a family member RIGHT NOW. Secrecy is how they keep control."], ["They want me to stay on video call or not disconnect", "'Digital arrest' does not exist in Indian law. No one can arrest you on a video call. Disconnect."], ["They are asking for money, OTP, UPI PIN or bank details", "STOP. Do not pay and do not share anything. No verification ever needs your money or OTP."]],
        "guard_lvl": ["No clear danger yet — stay alert and never share OTP.", "⚠️ Warning signs. Do not follow their instructions.", "🚨 This is a digital-arrest scam. HANG UP NOW."],
        "guard_money_q": "Have you already sent money?",
        "guard_money_yes": "Yes, money is gone",
        "guard_money_no": "No, not yet",
        "guard_timer": "Golden hour remaining — a 1930 report inside this window gives the best chance to freeze the transfer",
        "guard_call": "📞 Call 1930 now",
        "guard_after": ["Call 1930 immediately and say: 'I am a victim of a digital arrest fraud, I transferred money at <time>.'", "Tell your bank to freeze the beneficiary account.", "File at cybercrime.gov.in with your transaction ID.", "Do not answer that number again — they will call back."],
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
        "guard_other_q": "इनमें से कुछ नहीं — बताइए उसने क्या कहा",
        "guard_other_ph": "कॉल करने वाले ने जो कहा वह लिखिए…",
        "guard_other_btn": "जाँचें",
        "guard_cta": "🔴 मैं अभी संदिग्ध कॉल पर हूँ",
        "guard_title": "लाइव कॉल गार्ड",
        "guard_sub": "कॉल करने वाला जो कर रहा है उस पर टैप करें। मैं हर कदम पर बताऊँगा कि क्या करना है — जब आप कॉल पर ही हैं।",
        "guard_exit": "← चैट पर वापस",
        "guard_steps": [["वह कह रहा है कि वह पुलिस / सीबीआई / कस्टम / ट्राई से है", "असली अधिकारी इस तरह फोन नहीं करते। थाने का नाम पूछिए, कॉल काटिए और खुद उस थाने में फोन कीजिए।"], ["वह कह रहा है कि मेरे नाम पर केस, पार्सल, एफआईआर या वारंट है", "कोई भी एजेंसी फोन पर केस की सूचना नहीं देती। यह एक रटी हुई स्क्रिप्ट है — सच नहीं।"], ["उसने कहा किसी को मत बताना / यह गोपनीय है", "यही जाल है। अभी घर के किसी सदस्य को बताइए। गोपनीयता से ही वे काबू रखते हैं।"], ["वह चाहता है कि मैं वीडियो कॉल पर रहूँ या कॉल न काटूँ", "भारतीय कानून में 'डिजिटल अरेस्ट' है ही नहीं। वीडियो कॉल पर कोई गिरफ्तार नहीं कर सकता। कॉल काट दीजिए।"], ["वह पैसे, OTP, UPI पिन या बैंक जानकारी माँग रहा है", "रुकिए। पैसे मत भेजिए, कुछ मत बताइए। किसी भी सत्यापन के लिए आपके पैसे या OTP की ज़रूरत नहीं होती।"]],
        "guard_lvl": ["अभी स्पष्ट खतरा नहीं — सतर्क रहें और OTP कभी न बताएँ।", "⚠️ चेतावनी के संकेत हैं। उनके निर्देश मत मानिए।", "🚨 यह डिजिटल अरेस्ट धोखाधड़ी है। तुरंत कॉल काटिए।"],
        "guard_money_q": "क्या आप पहले ही पैसे भेज चुके हैं?",
        "guard_money_yes": "हाँ, पैसे चले गए",
        "guard_money_no": "नहीं, अभी नहीं",
        "guard_timer": "गोल्डन आवर बाकी — इस समय के भीतर 1930 पर शिकायत से पैसे रुकने की सबसे ज़्यादा संभावना है",
        "guard_call": "📞 अभी 1930 पर कॉल करें",
        "guard_after": ["तुरंत 1930 पर कॉल करके कहिए: 'मैं डिजिटल अरेस्ट धोखाधड़ी का शिकार हूँ, मैंने <समय> पर पैसे भेजे हैं।'", "अपने बैंक को कहिए कि लाभार्थी खाता तुरंत फ्रीज़ करे।", "cybercrime.gov.in पर ट्रांज़ैक्शन आईडी के साथ शिकायत दर्ज कीजिए।", "उस नंबर का दोबारा जवाब मत दीजिए — वे फिर कॉल करेंगे।"],
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
    "ta": {
        "guard_other_q": "இதில் எதுவும் இல்லை — அவர் என்ன சொன்னார் என்று சொல்லுங்கள்",
        "guard_other_ph": "அழைப்பாளர் சொன்னதை எழுதுங்கள்…",
        "guard_other_btn": "சரிபார்",
        "guard_cta": "🔴 நான் இப்போது சந்தேகமான அழைப்பில் இருக்கிறேன்",
        "guard_title": "நேரடி அழைப்பு காவலர்",
        "guard_sub": "அழைப்பாளர் என்ன செய்கிறார் என்பதைத் தட்டுங்கள். ஒவ்வொரு படியிலும் என்ன செய்வது என்று சொல்கிறேன் — நீங்கள் அழைப்பில் இருக்கும்போதே.",
        "guard_exit": "← அரட்டைக்குத் திரும்பு",
        "guard_steps": [["தான் காவல்துறை / சிபிஐ / சுங்கம் என்று கூறுகிறார்", "உண்மையான அதிகாரிகள் இப்படி அழைப்பதில்லை. நிலையத்தின் பெயரைக் கேட்டு, துண்டித்து நீங்களே அந்த நிலையத்தை அழையுங்கள்."], ["என் பெயரில் வழக்கு, பார்சல் அல்லது வாரண்ட் இருப்பதாகக் கூறுகிறார்", "எந்த அமைப்பும் தொலைபேசியில் வழக்கைத் தெரிவிப்பதில்லை. இது ஒரு திரைக்கதை — உண்மை அல்ல."], ["யாரிடமும் சொல்ல வேண்டாம் என்கிறார்", "இதுவே வலை. இப்போதே குடும்பத்தில் ஒருவரிடம் சொல்லுங்கள். இரகசியம் மூலமே அவர்கள் கட்டுப்படுத்துகிறார்கள்."], ["வீடியோ அழைப்பில் இருக்கவோ துண்டிக்காமல் இருக்கவோ சொல்கிறார்", "இந்திய சட்டத்தில் 'டிஜிட்டல் கைது' கிடையாது. வீடியோ அழைப்பில் யாரும் கைது செய்ய முடியாது. துண்டியுங்கள்."], ["பணம், OTP, UPI PIN அல்லது வங்கி விவரம் கேட்கிறார்", "நிறுத்துங்கள். பணம் அனுப்பவோ எதையும் பகிரவோ வேண்டாம். எந்தச் சரிபார்ப்புக்கும் உங்கள் பணம் தேவையில்லை."]],
        "guard_lvl": ["இதுவரை தெளிவான ஆபத்து இல்லை — விழிப்புடன் இருங்கள், OTP பகிர வேண்டாம்.", "⚠️ எச்சரிக்கை அறிகுறிகள். அவர்கள் சொல்வதைச் செய்ய வேண்டாம்.", "🚨 இது டிஜிட்டல் கைது மோசடி. உடனே துண்டியுங்கள்."],
        "guard_money_q": "நீங்கள் ஏற்கனவே பணம் அனுப்பிவிட்டீர்களா?",
        "guard_money_yes": "ஆம், பணம் போய்விட்டது",
        "guard_money_no": "இல்லை, இன்னும் இல்லை",
        "guard_timer": "தங்க நேரம் மீதம் — இதற்குள் 1930 இல் புகார் அளித்தால் பணத்தை நிறுத்த சிறந்த வாய்ப்பு",
        "guard_call": "📞 இப்போதே 1930 ஐ அழையுங்கள்",
        "guard_after": ["உடனே 1930 ஐ அழைத்துச் சொல்லுங்கள்: 'நான் டிஜிட்டல் கைது மோசடிக்கு ஆளானேன், <நேரம்> இல் பணம் அனுப்பினேன்.'", "பயனாளி கணக்கை முடக்கச் சொல்லி வங்கியைத் தொடர்பு கொள்ளுங்கள்.", "பரிவர்த்தனை ஐடியுடன் cybercrime.gov.in இல் புகார் அளியுங்கள்.", "அந்த எண்ணுக்கு மீண்டும் பதில் அளிக்க வேண்டாம் — அவர்கள் மீண்டும் அழைப்பார்கள்."],
        "greeting": GREETING["ta"],
        "placeholder": "செய்தியை இங்கே எழுதுங்கள், அல்லது 📎 திரைப்படம் அனுப்புங்கள்…",
        "send": "அனுப்பு", "typing": "சரிபார்க்கிறது…", "recent": "சமீபத்திய சரிபார்ப்புகள்",
        "actions_title": "இப்போது என்ன செய்ய வேண்டும்",
        "default_actions": [
            "சந்தேகமான அழைப்பு அல்லது செய்தியா? எதுவும் செய்வதற்கு முன் இங்கே சரிபார்க்கவும்.",
            "OTP, PIN அல்லது கடவுச்சொல்லை யாருடனும் பகிர வேண்டாம்.",
            "பணம் அனுப்பிவிட்டீர்களா? உடனே 1930 ஐ அழையுங்கள் — முதல் மணி நேரம் மிக முக்கியம்.",
        ],
        "samples": [
            ["🚨 டிஜிட்டல் கைது", "சிபிஐ அதிகாரி நான் டிஜிட்டல் கைதில் இருப்பதாகவும் ஆர்பிஐ கணக்கிற்குப் பணம் அனுப்ப வேண்டும் என்றும் கூறுகிறார். யாரிடமும் சொல்ல வேண்டாம் என்கிறார்."],
            ["⚡ மின்சாரம் துண்டிப்பு", "இன்று இரவு உங்கள் மின் இணைப்பு துண்டிக்கப்படும். தவிர்க்க இந்த இணைப்பில் உடனே பணம் செலுத்துங்கள்."],
            ["🎰 லாட்டரி வெற்றி", "வாழ்த்துக்கள்! நீங்கள் ₹25 லட்சம் வென்றுள்ளீர்கள். பெற சிறிய கட்டணம் செலுத்துங்கள்."],
        ],
        "safe_actions": [
            "மோசடி அறிகுறி எதுவும் இல்லை — நடவடிக்கை தேவையில்லை.",
            "இன்னும் சந்தேகமா? வங்கியின் அதிகாரப்பூர்வ இணையதளத்தில் உள்ள எண்ணை அழையுங்கள்.",
        ],
        "no_checks": "இதுவரை சரிபார்ப்பு இல்லை — கீழே ஒரு மாதிரியைத் தேர்ந்தெடுங்கள்.",
        "reading": "திரைப்படம் படிக்கப்படுகிறது…",
    },
    "bn": {
        "guard_other_q": "এর কোনোটিই নয় — তিনি কী বললেন বলুন",
        "guard_other_ph": "কলকারী যা বলেছেন তা লিখুন…",
        "guard_other_btn": "যাচাই করুন",
        "guard_cta": "🔴 আমি এখনই সন্দেহজনক কলে আছি",
        "guard_title": "লাইভ কল গার্ড",
        "guard_sub": "কলকারী যা করছে তাতে ট্যাপ করুন। প্রতিটি ধাপে কী করবেন আমি বলব — আপনি কলে থাকা অবস্থাতেই।",
        "guard_exit": "← চ্যাটে ফিরুন",
        "guard_steps": [["তিনি বলছেন তিনি পুলিশ / সিবিআই / কাস্টমস", "আসল অফিসাররা এভাবে ফোন করেন না। থানার নাম জিজ্ঞেস করুন, কল কেটে নিজে সেই থানায় ফোন করুন।"], ["আমার নামে মামলা, পার্সেল বা ওয়ারেন্ট আছে বলছেন", "কোনো সংস্থা ফোনে মামলার খবর দেয় না। এটি একটি মুখস্থ স্ক্রিপ্ট — সত্যি নয়।"], ["কাউকে বলতে নিষেধ করেছেন / গোপন রাখতে বলেছেন", "এটাই ফাঁদ। এখনই পরিবারের কাউকে বলুন। গোপনীয়তা দিয়েই ওরা নিয়ন্ত্রণ রাখে।"], ["ভিডিও কলে থাকতে বা কল না কাটতে বলছেন", "ভারতীয় আইনে 'ডিজিটাল অ্যারেস্ট' বলে কিছু নেই। ভিডিও কলে কেউ গ্রেপ্তার করতে পারে না। কল কাটুন।"], ["টাকা, OTP, UPI PIN বা ব্যাঙ্কের তথ্য চাইছেন", "থামুন। টাকা পাঠাবেন না, কিছু জানাবেন না। কোনো যাচাইয়ের জন্য আপনার টাকা বা OTP লাগে না।"]],
        "guard_lvl": ["এখনও স্পষ্ট বিপদ নেই — সতর্ক থাকুন, OTP জানাবেন না।", "⚠️ সতর্কতার লক্ষণ। ওদের কথা শুনবেন না।", "🚨 এটি ডিজিটাল অ্যারেস্ট প্রতারণা। এখনই কল কাটুন।"],
        "guard_money_q": "আপনি কি ইতিমধ্যে টাকা পাঠিয়েছেন?",
        "guard_money_yes": "হ্যাঁ, টাকা চলে গেছে",
        "guard_money_no": "না, এখনও নয়",
        "guard_timer": "গোল্ডেন আওয়ার বাকি — এর মধ্যে ১৯৩০-এ জানালে টাকা আটকানোর সবচেয়ে ভালো সুযোগ",
        "guard_call": "📞 এখনই ১৯৩০-এ ফোন করুন",
        "guard_after": ["এখনই ১৯৩০-এ ফোন করে বলুন: 'আমি ডিজিটাল অ্যারেস্ট প্রতারণার শিকার, আমি <সময়>-এ টাকা পাঠিয়েছি।'", "ব্যাঙ্ককে বলুন প্রাপকের অ্যাকাউন্ট ফ্রিজ করতে।", "লেনদেন আইডি সহ cybercrime.gov.in-এ অভিযোগ করুন।", "ওই নম্বরে আর সাড়া দেবেন না — ওরা আবার ফোন করবে।"],
        "greeting": GREETING["bn"],
        "placeholder": "বার্তাটি এখানে লিখুন, বা 📎 স্ক্রিনশট পাঠান…",
        "send": "পাঠান", "typing": "যাচাই করা হচ্ছে…", "recent": "সাম্প্রতিক যাচাই",
        "actions_title": "এখন কী করবেন",
        "default_actions": [
            "সন্দেহজনক কল বা বার্তা? কিছু করার আগে এখানে যাচাই করুন।",
            "OTP, PIN বা পাসওয়ার্ড কাউকে বলবেন না।",
            "টাকা পাঠিয়ে ফেলেছেন? এখনই ১৯৩০-এ ফোন করুন — প্রথম ঘণ্টা সবচেয়ে জরুরি।",
        ],
        "samples": [
            ["🚨 ডিজিটাল অ্যারেস্ট", "সিবিআই অফিসার বলছেন আমি ডিজিটাল অ্যারেস্টে আছি এবং আরবিআই অ্যাকাউন্টে টাকা পাঠাতে হবে। কাউকে বলতে নিষেধ করেছেন।"],
            ["⚡ বিদ্যুৎ বিচ্ছিন্ন", "আজ রাতে আপনার বিদ্যুৎ সংযোগ কেটে দেওয়া হবে। এড়াতে এই লিঙ্কে এখনই টাকা দিন।"],
            ["🎰 লটারি জয়", "অভিনন্দন! আপনি ₹২৫ লাখ জিতেছেন। দাবি করতে সামান্য প্রসেসিং ফি দিন।"],
        ],
        "safe_actions": [
            "প্রতারণার কোনো লক্ষণ পাওয়া যায়নি — কিছু করার দরকার নেই।",
            "তবুও সন্দেহ? ব্যাঙ্কের অফিসিয়াল ওয়েবসাইটের নম্বরে ফোন করুন।",
        ],
        "no_checks": "এখনও কোনো যাচাই নেই — নিচে একটি নমুনা বেছে নিন।",
        "reading": "স্ক্রিনশট পড়া হচ্ছে…",
    },
}


def ui_strings(lang: str) -> Dict:
    return _UI.get(lang, _UI["en"])
