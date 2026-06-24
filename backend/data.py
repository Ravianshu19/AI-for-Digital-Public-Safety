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
    # --- Ring A: digital-arrest campaign -> UPI mules -> Paytm wallet -> bank -> crypto exit
    {"src": "victim:V001", "dst": "upi:mule1@okaxis",  "type": "upi_transfer", "amount": 480000, "ts": "2025-06-08"},
    {"src": "victim:V002", "dst": "upi:mule1@okaxis",  "type": "upi_transfer", "amount": 250000, "ts": "2025-06-09"},
    {"src": "victim:V003", "dst": "upi:mule2@oksbi",   "type": "upi_transfer", "amount": 610000, "ts": "2025-06-10"},
    {"src": "victim:V004", "dst": "upi:mule2@oksbi",   "type": "upi_transfer", "amount": 150000, "ts": "2025-06-11"},
    {"src": "victim:V005", "dst": "upi:mule3@okhdfc",  "type": "upi_transfer", "amount": 900000, "ts": "2025-06-12"},
    {"src": "upi:mule1@okaxis", "dst": "wallet:paytm-AGGR", "type": "upi_transfer", "amount": 700000, "ts": "2025-06-12"},
    {"src": "upi:mule2@oksbi",  "dst": "wallet:paytm-AGGR", "type": "upi_transfer", "amount": 740000, "ts": "2025-06-13"},
    {"src": "upi:mule3@okhdfc", "dst": "wallet:paytm-AGGR", "type": "upi_transfer", "amount": 850000, "ts": "2025-06-13"},
    {"src": "wallet:paytm-AGGR", "dst": "acct:HDFC-50021", "type": "transfer", "amount": 2100000, "ts": "2025-06-14"},
    {"src": "acct:HDFC-50021", "dst": "crypto:binance-exit", "type": "transfer", "amount": 2050000, "ts": "2025-06-15"},
    {"src": "phone:+919800011111", "dst": "victim:V001", "type": "call"},
    {"src": "phone:+919800011111", "dst": "victim:V002", "type": "call"},
    {"src": "phone:+919800011111", "dst": "victim:V004", "type": "call"},
    {"src": "phone:+918700022222", "dst": "victim:V003", "type": "call"},
    {"src": "phone:+918700022222", "dst": "victim:V005", "type": "call"},
    {"src": "device:IMEI-86xx-Skype", "dst": "phone:+919800011111", "type": "uses"},
    {"src": "device:IMEI-86xx-Skype", "dst": "phone:+918700022222", "type": "uses"},
    {"src": "device:IMEI-86xx-Skype", "dst": "wallet:paytm-AGGR", "type": "login"},

    # --- Ring B: UPI collect-request scam -> GPay mule -> crypto exit
    {"src": "victim:V101", "dst": "upi:refund2025@okicici", "type": "upi_transfer", "amount": 120000, "ts": "2025-06-15"},
    {"src": "victim:V102", "dst": "upi:refund2025@okicici", "type": "upi_transfer", "amount": 95000, "ts": "2025-06-16"},
    {"src": "upi:refund2025@okicici", "dst": "wallet:gpay-MULE", "type": "upi_transfer", "amount": 200000, "ts": "2025-06-16"},
    {"src": "wallet:gpay-MULE", "dst": "crypto:wazirx-exit", "type": "transfer", "amount": 195000, "ts": "2025-06-17"},
    {"src": "phone:+917600099999", "dst": "victim:V101", "type": "call"},
    {"src": "phone:+917600099999", "dst": "victim:V102", "type": "call"},
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
