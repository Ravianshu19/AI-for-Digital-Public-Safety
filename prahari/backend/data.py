"""
Seed / demo data for the Prahari prototype.

All data here is SYNTHETIC and for demonstration only. It is shaped to look like
the kind of multi-source feed the platform would ingest in production
(NCRP/1930 complaints, TSP CDR linkages, bank STR feeds, FICN seizure logs).
"""

# ---------------------------------------------------------------------------
# Fraud-network demo edges (one big "digital arrest" ring + a smaller mule ring)
# ---------------------------------------------------------------------------
FRAUD_RECORDS = [
    # Ring A: digital-arrest campaign funnelling to aggregator acct:A-AGGR
    {"src": "victim:V001", "dst": "acct:A-MULE1", "type": "transfer", "amount": 480000, "ts": "2026-06-08"},
    {"src": "victim:V002", "dst": "acct:A-MULE1", "type": "transfer", "amount": 250000, "ts": "2026-06-09"},
    {"src": "victim:V003", "dst": "acct:A-MULE2", "type": "transfer", "amount": 610000, "ts": "2026-06-10"},
    {"src": "victim:V004", "dst": "acct:A-MULE2", "type": "transfer", "amount": 150000, "ts": "2026-06-11"},
    {"src": "victim:V005", "dst": "acct:A-MULE3", "type": "transfer", "amount": 900000, "ts": "2026-06-12"},
    {"src": "acct:A-MULE1", "dst": "acct:A-AGGR", "type": "transfer", "amount": 700000, "ts": "2026-06-12"},
    {"src": "acct:A-MULE2", "dst": "acct:A-AGGR", "type": "transfer", "amount": 740000, "ts": "2026-06-13"},
    {"src": "acct:A-MULE3", "dst": "acct:A-AGGR", "type": "transfer", "amount": 850000, "ts": "2026-06-13"},
    {"src": "acct:A-AGGR", "dst": "cashout:C-DUBAI", "type": "transfer", "amount": 2200000, "ts": "2026-06-14"},
    {"src": "phone:+910000011111", "dst": "victim:V001", "type": "call"},
    {"src": "phone:+910000011111", "dst": "victim:V002", "type": "call"},
    {"src": "phone:+910000011111", "dst": "victim:V004", "type": "call"},
    {"src": "phone:+910000022222", "dst": "victim:V003", "type": "call"},
    {"src": "phone:+910000022222", "dst": "victim:V005", "type": "call"},
    {"src": "device:DEV-SKYPE-7", "dst": "phone:+910000011111", "type": "uses"},
    {"src": "device:DEV-SKYPE-7", "dst": "phone:+910000022222", "type": "uses"},
    {"src": "device:DEV-SKYPE-7", "dst": "acct:A-AGGR", "type": "login"},

    # Ring B: smaller, independent mule cluster
    {"src": "victim:V101", "dst": "acct:B-MULE1", "type": "transfer", "amount": 120000, "ts": "2026-06-15"},
    {"src": "victim:V102", "dst": "acct:B-MULE1", "type": "transfer", "amount": 95000, "ts": "2026-06-16"},
    {"src": "acct:B-MULE1", "dst": "upi:scam@okbank", "type": "transfer", "amount": 200000, "ts": "2026-06-16"},
    {"src": "phone:+910000099999", "dst": "victim:V101", "type": "call"},
    {"src": "phone:+910000099999", "dst": "victim:V102", "type": "call"},
]

# ---------------------------------------------------------------------------
# Geospatial demo: cybercrime / FICN seizure / scam-complaint points (India)
# ---------------------------------------------------------------------------
GEO_POINTS = [
    # lat, lon, type, intensity(1-10), label
    {"lat": 28.6139, "lon": 77.2090, "type": "digital_arrest", "intensity": 9, "label": "New Delhi"},
    {"lat": 19.0760, "lon": 72.8777, "type": "digital_arrest", "intensity": 8, "label": "Mumbai"},
    {"lat": 12.9716, "lon": 77.5946, "type": "digital_arrest", "intensity": 7, "label": "Bengaluru"},
    {"lat": 17.3850, "lon": 78.4867, "type": "cyber_fraud", "intensity": 6, "label": "Hyderabad"},
    {"lat": 22.5726, "lon": 88.3639, "type": "cyber_fraud", "intensity": 5, "label": "Kolkata"},
    {"lat": 13.0827, "lon": 80.2707, "type": "cyber_fraud", "intensity": 5, "label": "Chennai"},
    {"lat": 26.8467, "lon": 80.9462, "type": "ficn_seizure", "intensity": 8, "label": "Lucknow"},
    {"lat": 25.5941, "lon": 85.1376, "type": "ficn_seizure", "intensity": 9, "label": "Patna"},
    {"lat": 23.2599, "lon": 77.4126, "type": "ficn_seizure", "intensity": 4, "label": "Bhopal"},
    {"lat": 26.1445, "lon": 91.7362, "type": "ficn_seizure", "intensity": 6, "label": "Guwahati"},
    {"lat": 21.1458, "lon": 79.0882, "type": "cyber_fraud", "intensity": 4, "label": "Nagpur"},
    {"lat": 30.7333, "lon": 76.7794, "type": "digital_arrest", "intensity": 5, "label": "Chandigarh"},
    {"lat": 26.9124, "lon": 75.7873, "type": "cyber_fraud", "intensity": 5, "label": "Jaipur"},
    {"lat": 23.0225, "lon": 72.5714, "type": "digital_arrest", "intensity": 6, "label": "Ahmedabad"},
    {"lat": 15.2993, "lon": 74.1240, "type": "ficn_seizure", "intensity": 3, "label": "Goa"},
    # cross-border source compounds (intelligence overlay)
    {"lat": 11.5564, "lon": 104.9282, "type": "scam_compound", "intensity": 10, "label": "Phnom Penh (source)"},
    {"lat": 16.8409, "lon": 96.1735, "type": "scam_compound", "intensity": 9, "label": "Myanmar border (source)"},
]

# ---------------------------------------------------------------------------
# Example scam transcripts for the demo (good for one-click testing)
# ---------------------------------------------------------------------------
SAMPLE_TRANSCRIPTS = {
    "digital_arrest": (
        "Sir, I am Inspector Sharma from CBI Mumbai, badge number 4471. A parcel "
        "in your name was seized at Customs containing illegal drugs and your Aadhaar "
        "was used for money laundering. A non-bailable warrant is registered against you. "
        "Do not tell anyone, this is a confidential investigation. You are now under "
        "digital arrest and must stay on this video call. To clear your name you must "
        "transfer all your money to an RBI verified account for verification within 2 hours "
        "or we will arrest you today."
    ),
    "legit": (
        "Hello, this is a recorded line for quality from your bank. We noticed a login "
        "from a new device. We will never ask you for your OTP or to transfer money. "
        "If you did not do this, please visit your nearest branch in person."
    ),
    "suspicious": (
        "Your electricity bill is pending and your connection will be disconnected "
        "tonight. Please pay immediately to avoid disconnection."
    ),
}
