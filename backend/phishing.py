"""
Phishing / malicious-link analysis
==================================

Almost every digital-fraud message carries a link — fake KYC portals,
"electricity bill" payment pages, refund/lottery claims, brand-lookalike
banking sites. This module extracts URLs from a message and scores each for
classic phishing indicators (glass-box, offline, no threat-intel feed needed):

  IP-literal host · "@" in authority · punycode · URL shorteners · risky TLDs ·
  brand-lookalike domains · excessive subdomains/hyphens · no-HTTPS ·
  credential-harvest keywords in the path.

Known-good Indian bank / government / UPI domains are allow-listed so genuine
links (which legitimately contain "login"/"kyc") don't false-positive.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

_URL_RE = re.compile(r"\b((?:https?://|www\.)[^\s<>\"')]+)", re.I)

# Legit destinations — a genuine link to one of these is not phishing.
_ALLOW = {
    "sbi.co.in", "onlinesbi.sbi", "hdfcbank.com", "icicibank.com", "axisbank.com",
    "pnbindia.in", "bankofbaroda.in", "kotak.com", "rbi.org.in", "npci.org.in",
    "paytm.com", "phonepe.com", "gpay.app", "amazon.in", "cybercrime.gov.in",
    "incometax.gov.in", "uidai.gov.in", "india.gov.in", "irctc.co.in",
}
# Brand tokens scammers imitate; if present but the domain isn't allow-listed → lookalike.
_BRANDS = ["sbi", "hdfc", "icici", "axis", "kotak", "pnb", "rbi", "npci", "paytm",
           "phonepe", "gpay", "googlepay", "aadhaar", "uidai", "incometax", "kyc",
           "netbanking", "onlinesbi"]
_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "rb.gy",
               "goo.gl", "ow.ly", "shorturl.at", "rebrand.ly", "tiny.cc"}
_RISKY_TLD = {"tk", "top", "xyz", "buzz", "club", "online", "click", "gq", "ml",
              "cf", "ga", "work", "support", "rest", "fit", "icu", "link"}
_CRED_KW = ("login", "verify", "secure", "update", "kyc", "account", "otp",
            "netbanking", "refund", "confirm", "signin", "wallet", "password")


@dataclass
class UrlFinding:
    url: str
    risk: int
    verdict: str            # PHISHING / SUSPICIOUS / LIKELY_SAFE
    reasons: List[str] = field(default_factory=list)

    def to_dict(self):
        return {"url": self.url, "risk": self.risk, "verdict": self.verdict,
                "reasons": self.reasons}


def _host(url: str) -> str:
    u = re.sub(r"^https?://", "", url, flags=re.I)
    u = u.split("/")[0].split("?")[0]
    if "@" in u:                      # userinfo@host trick — take the real host
        u = u.split("@")[-1]
    return u.split(":")[0].lower()


def _registrable(host: str) -> str:
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def analyze_url(url: str) -> UrlFinding:
    raw = url.rstrip(".,);]")
    host = _host(raw)
    reg = _registrable(host)
    path = raw[len(host):].lower() if host in raw else raw.lower()
    reasons: List[str] = []
    risk = 0

    if reg in _ALLOW or host in _ALLOW:
        return UrlFinding(raw, 0, "LIKELY_SAFE", ["official domain — allow-listed"])

    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
        risk += 32; reasons.append("IP address instead of a domain name")
    if "@" in raw.split("//")[-1].split("/")[0]:
        risk += 25; reasons.append("'@' in link hides the real destination")
    if host.startswith("xn--") or "xn--" in host:
        risk += 25; reasons.append("punycode domain (look-alike characters)")
    if reg in _SHORTENERS:
        risk += 22; reasons.append("URL shortener hides the destination")
    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    if tld in _RISKY_TLD:
        risk += 18; reasons.append(f"high-abuse TLD .{tld}")
    brand = next((b for b in _BRANDS if b in host or b in path), None)
    if brand and reg not in _ALLOW:
        risk += 30; reasons.append(f"impersonates '{brand}' on an unofficial domain")
    if host.count(".") >= 4:
        risk += 15; reasons.append("excessive sub-domains")
    if host.count("-") >= 2:
        risk += 10; reasons.append("many hyphens in domain (look-alike trick)")
    if raw.lower().startswith("http://"):
        risk += 8; reasons.append("no HTTPS")
    kw = [k for k in _CRED_KW if k in path]
    if kw:
        risk += 12; reasons.append(f"credential-harvest keywords in path: {', '.join(kw[:3])}")
    if sum(c.isdigit() for c in reg) >= 4:
        risk += 8; reasons.append("digit-heavy domain")

    risk = min(99, risk)
    verdict = "PHISHING" if risk >= 45 else ("SUSPICIOUS" if risk >= 22 else "LIKELY_SAFE")
    if not reasons:
        reasons = ["no obvious phishing markers"]
    return UrlFinding(raw, risk, verdict, reasons)


def analyze_text(text: str) -> Dict:
    urls = _URL_RE.findall(text or "")
    findings = [analyze_url(u) for u in dict.fromkeys(urls)]   # dedupe, keep order
    worst = max(findings, key=lambda f: f.risk, default=None)
    return {
        "urls_found": len(findings),
        "max_risk": worst.risk if worst else 0,
        "worst_verdict": worst.verdict if worst else None,
        "findings": [f.to_dict() for f in findings],
    }
