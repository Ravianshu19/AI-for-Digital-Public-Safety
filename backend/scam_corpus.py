"""
Synthetic Indian scam-call / message corpus.

Real scam-call recordings are rarely released, so a labelled synthetic corpus is
the practical (and legal) training/benchmark asset. This module generates one
deterministically across the major Indian scam categories, in the schema:

    {"call_text": "...", "label": "digital_arrest", "agency_claimed": "CBI", "risk": 0.98}

Use `all_examples()` for (text, label, category) tuples and `export_json()` to
write sample_data/scam_corpus.json.
"""

from __future__ import annotations

import itertools
import json
import os
import random
from typing import Dict, List

_RND = random.Random(20240624)

# ---- Digital arrest (agency impersonation) --------------------------------
AGENCIES = ["CBI", "Mumbai Police", "Enforcement Directorate", "Customs Department",
            "Narcotics Control Bureau", "TRAI", "Delhi Cyber Cell"]
OFFICERS = ["Inspector Sharma", "Officer Verma", "DCP Singh", "Sub-Inspector Rao"]
ACCUSE = [
    "A parcel in your name has illegal drugs and a fake passport.",
    "Your Aadhaar is linked to a money laundering case.",
    "Your SIM card is used in a criminal investigation.",
    "A non-bailable warrant has been issued against you.",
]
THREAT = [
    "You are under digital arrest, stay on this video call.",
    "Do not tell anyone, this is a confidential investigation.",
    "We will arrest you today if you disconnect.",
]
DEMAND = [
    "Transfer all your money to an RBI verified account for verification.",
    "Pay a verification deposit immediately to clear your name.",
]

# ---- Other scam families: list of message templates -----------------------
FAMILIES: Dict[str, List[str]] = {
    "upi_fraud": [
        "I accidentally sent money to your UPI, please return it by approving this collect request.",
        "Approve the UPI collect request to receive your refund of 4999.",
        "Scan this QR code to receive your 5000 cashback immediately.",
        "Your PhonePe payment failed, share the OTP to reverse the transaction.",
    ],
    "kyc_scam": [
        "Your KYC has expired, update your KYC immediately or your account will be suspended.",
        "Dear customer your PAN is not linked, click the link to update KYC now.",
        "Paytm KYC pending, your wallet will be deactivated unless you verify today.",
    ],
    "parcel_scam": [
        "Your FedEx parcel is held at customs with illegal items, pay the clearance fee now.",
        "Customs department: your courier contains banned goods, pay a fine immediately.",
    ],
    "investment_scam": [
        "Join our VIP trading group, guaranteed 30% daily returns on crypto.",
        "Double your money in 7 days with our forex tips, invest now.",
        "Assured 20% monthly profit on this stock tip, join the channel.",
    ],
    "job_scam": [
        "Work from home and earn 5000 daily, pay a 500 registration fee to start.",
        "Part time job: like videos and earn money, small joining deposit required.",
        "Earn 3000 per day from home doing simple tasks, register now.",
    ],
    "loan_scam": [
        "Pre-approved instant loan of 5 lakh, just pay a processing fee to release it.",
        "Guaranteed loan approval, pay the registration fee to receive the amount.",
    ],
    "lottery_scam": [
        "Congratulations! You won 25 lakh in the KBC lottery, pay processing fee to claim.",
        "You are a lucky winner of a brand new car, claim your prize by paying the fee.",
    ],
    "sextortion": [
        "I have recorded a private video of you, pay money or I will leak it to your contacts.",
        "I captured your intimate video on a call, send money or we share it publicly.",
    ],
    "matrimony_scam": [
        "I sent you a gift from abroad but it is stuck at customs, please pay the clearance fee.",
        "My parcel with jewellery is held at the airport, send money for the customs duty.",
    ],
    "credential_phishing": [
        "Your account will be blocked, share the OTP you just received to keep it active.",
        "To complete verification enter your OTP, PIN and CVV now to avoid suspension.",
    ],
}

# ---- Benign / hard negatives (must stay SAFE) -----------------------------
BENIGN = [
    "This is a recorded line for quality from your bank. We will never ask for your OTP or to transfer money. Please visit your nearest branch in person.",
    "Your OTP for the transaction is 482913. Do not share it with anyone.",
    "Reminder: your electricity bill of Rs 1,240 is due on 30 June. Pay anytime via the official app.",
    "Your loan EMI of Rs 8,500 has been successfully debited from your account.",
    "Dear customer, your KYC is complete and your account is active. No action required.",
    "Your salary of Rs 65,000 has been credited to your account ending 4421.",
    "Your Amazon order has shipped and will arrive by Thursday. Track it in the app.",
    "Your Swiggy order is on the way and will reach you in 15 minutes.",
    "Flipkart: your refund of Rs 999 has been initiated to your original payment method.",
    "Hi mom, can we have dinner at 8 tonight?",
    "Meeting moved to 3pm tomorrow, please confirm if that works for you.",
    "Don't forget to pick up the groceries on your way home.",
    "Happy birthday! Wishing you a wonderful year ahead.",
    "The project report is ready for your review, I have shared it on the drive.",
    "Last day! Flat 40% off on all shoes. Shop now on our official store.",
    "Your Netflix subscription will renew on 1 July. Manage your plan in account settings.",
    "Your appointment with Dr. Rao is confirmed for Monday at 11am.",
    "Your cab is arriving in 2 minutes. Driver: Suresh, vehicle DL 1AB 1234.",
    "Congratulations on your work anniversary! Thanks for five great years.",
    "Your UPI payment of Rs 250 to Big Bazaar was successful.",
]


def _digital_arrest_examples(n: int = 14) -> List[Dict]:
    combos = list(itertools.product(OFFICERS, AGENCIES, ACCUSE, THREAT, DEMAND))
    _RND.shuffle(combos)
    out = []
    for off, ag, ac, th, dm in combos[:n]:
        out.append({
            "call_text": f"This is {off} from {ag}. {ac} {th} {dm}",
            "label": "digital_arrest", "agency_claimed": ag,
            "risk": round(_RND.uniform(0.9, 0.98), 2),
        })
    return out


def build() -> List[Dict]:
    rows = _digital_arrest_examples()
    for fam, templates in FAMILIES.items():
        for t in templates:
            rows.append({"call_text": t, "label": fam, "agency_claimed": None,
                         "risk": round(_RND.uniform(0.78, 0.95), 2)})
    for b in BENIGN:
        rows.append({"call_text": b, "label": "benign", "agency_claimed": None,
                     "risk": round(_RND.uniform(0.02, 0.10), 2)})
    return rows


def all_examples():
    """(text, binary_label, category) where binary_label is 'scam' | 'benign'."""
    for r in build():
        yield (r["call_text"], "benign" if r["label"] == "benign" else "scam", r["label"])


def export_json(path: str = None) -> str:
    path = path or os.path.join(os.path.dirname(__file__), "..", "sample_data", "scam_corpus.json")
    with open(path, "w") as f:
        json.dump(build(), f, indent=2)
    return path


if __name__ == "__main__":
    rows = build()
    cats = {}
    for r in rows:
        cats[r["label"]] = cats.get(r["label"], 0) + 1
    print(f"Generated {len(rows)} examples across {len(cats)} categories:")
    for c, n in sorted(cats.items()):
        print(f"  {c:20s} {n}")
    print("Wrote", export_json())
