"""
Held-out, independently-sourced benchmark
=========================================

The main benchmark mixes a curated set with a corpus this repo generates
(scam_corpus.py) — a perfect score there can read as circular. This file is a
SEPARATE, held-out set: scam scripts paraphrased from PUBLICLY DOCUMENTED
digital-arrest / financial-fraud cases (MHA / I4C advisories and mainstream
news coverage of real victims), plus genuine hard-negative messages.

None of these phrasings were used to write the detector's patterns — it is a
true out-of-sample test. We report this number SEPARATELY and honestly, even
though it is lower than the in-house benchmark, because an independently-sourced
85–95% is more credible than a self-graded 100%.

Sources paraphrased (not quoted): reported CBI/TRAI/FedEx-parcel "digital
arrest" scripts, electricity-bill and KYC-expiry SMS waves, courier-parcel and
"your number will be blocked" TRAI calls, and NCRP-published examples.
label: "scam" | "benign".
"""

HELDOUT = [
    # --- documented digital-arrest / impersonation scripts (paraphrased) ---
    ("This is Sub-Inspector Verma from Delhi Cyber Cell. A SIM card issued on "
     "your Aadhaar was used in a money-laundering case in Kanpur. You must stay "
     "on this video call under digital arrest until we verify your accounts.", "scam"),
    ("FedEx courier here — a parcel in your name to Taiwan contains 4 passports "
     "and drugs. Mumbai Narcotics has your case. Do not disconnect; an officer "
     "will take your statement now.", "scam"),
    ("TRAI notice: all your mobile numbers will be disconnected within 2 hours "
     "for illegal activity. Press 9 to speak to a telecom officer.", "scam"),
    ("Madam, I am calling from the CBI. Your bank account is linked to a "
     "terror-funding investigation. To prove your innocence, move your balance "
     "to this RBI-supervised safe account for verification; it will be returned.", "scam"),
    ("Your electricity connection will be cut tonight at 9:30 pm as last month's "
     "bill was not updated. Call this number immediately or pay via the link.", "scam"),
    ("Dear customer, your SBI YONO account is blocked. Complete KYC now at "
     "http://sbi-yono-kyc.online/verify or the account stays frozen.", "scam"),
    ("Sir this is the customs department. A gift parcel from your online friend "
     "is held at the airport. Pay the clearance and GST fee to release it.", "scam"),
    ("We are from the Enforcement Directorate. There is a non-bailable warrant "
     "in your name. Keep your camera on and do not tell your family — this is a "
     "confidential national-security matter.", "scam"),
    ("Congratulations, your number won ₹25,00,000 in the KBC lucky draw. Pay a "
     "small refundable GST amount to release the prize money.", "scam"),
    ("Install AnyDesk so our bank security team can secure your account. Do not "
     "close the app or share this call with anyone.", "scam"),
    ("Your PAN card is suspended. Update immediately via this link and confirm "
     "your net-banking password to reactivate it.", "scam"),
    ("आप डिजिटल अरेस्ट में हैं। सीबीआई की जांच चल रही है, किसी को मत बताइए और "
     "सत्यापन के लिए अपना सारा पैसा आरबीआई के सुरक्षित खाते में ट्रांसफर करें।", "scam"),
    # --- genuine hard negatives (must NOT flag) ---
    ("Your OTP for SBI YONO login is 483920. Do not share it with anyone. "
     "- SBI", "benign"),
    ("Reminder: your electricity bill of ₹1,240 is due on 25th. Pay via the "
     "BESCOM app or any authorised centre. No action needed if already paid.", "benign"),
    ("Your Amazon order #402-9911 has shipped and will arrive tomorrow. Track "
     "it in the Amazon app.", "benign"),
    ("Dear customer, your credit card statement is ready. View it by logging in "
     "at the official HDFC net-banking portal. We never ask for OTP or PIN.", "benign"),
    ("Namaste, this is a reminder from your bank branch that your locker rent is "
     "due. Please visit the branch in person at your convenience.", "benign"),
    ("Your train PNR 2841559023 is confirmed, coach B4 seat 32. Happy journey "
     "from IRCTC.", "benign"),
    ("Congratulations on your new job offer! HR will email your appointment "
     "letter from the company domain by Friday.", "benign"),
    ("आपके खाते में ₹5,000 जमा हुए हैं। शेष राशि ₹18,240। धन्यवाद - बैंक।", "benign"),
]
