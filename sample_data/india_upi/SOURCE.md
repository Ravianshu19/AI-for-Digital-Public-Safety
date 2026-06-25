# UPI Digital Payment Fraud — India (FY2023–FY2025)

**File:** `upi_fraud_india_dataset.csv` — 1,000 India UPI fraud cases with fraud type,
lure, amount (₹), UPI app, sender/receiver UPI IDs, linked bank, victim state/age/
occupation, whether PIN/OTP was shared, report delay, and recovery status.

**Source:** Kaggle — *UPI Digital Payment Fraud in India (FY2023–FY2025)*,
dataset `aishricadhiman/upi-fraud-dataset`.
https://www.kaggle.com/datasets/aishricadhiman/upi-fraud-dataset

Refresh with `KAGGLE_KEY=KGAT_… .venv/bin/python sample_data/fetch_india_upi.py`.

**How we use it:** powers the **Real India UPI Fraud Intelligence** panel
(`backend/india_upi.py` → `/api/fraud/india_stats`): fraud-type / lure / app / state
breakdowns, ₹ loss, OTP-shared and recovery rates — real India aggregate intelligence
alongside the synthetic ring-topology graph.
