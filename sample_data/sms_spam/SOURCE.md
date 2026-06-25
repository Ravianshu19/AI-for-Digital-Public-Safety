# SMS Spam Collection — source & attribution

**File:** `SMSSpamCollection` — 5,574 real English SMS messages labelled `ham` (legit)
or `spam`, tab-separated.

**Source:** UCI Machine Learning Repository — SMS Spam Collection Data Set.
https://archive.ics.uci.edu/dataset/228/sms+spam+collection

**Citation:** Almeida, T.A., Gómez Hidalgo, J.M., Yamakami, A. (2011). *Contributions
to the Study of SMS Spam Filtering: New Collection and Results.* Proceedings of the
2011 ACM Symposium on Document Engineering (DOCENG'11).

**How we use it (read this — it matters for interpretation):**
We use this real corpus as an **external validation of the citizen-safety claim**:
the false-positive rate on the **4,827 genuine (ham)** messages. The classifier is
tuned for *Indian* scam families (digital-arrest, UPI, KYC, etc.), so its recall on
this *generic UK premium-SMS* spam is intentionally low and out of domain — recall is
reported on the India-specific benchmark (`backend/evaluate.py`), not here.
