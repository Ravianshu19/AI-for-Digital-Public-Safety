"""
Fetch the India UPI fraud dataset (Kaggle: aishricadhiman/upi-fraud-dataset).

Provide a Kaggle token, then run:
  export KAGGLE_KEY="KGAT_xxx"        # new-style token works with kagglehub
  .venv/bin/pip install kagglehub
  .venv/bin/python sample_data/fetch_india_upi.py

A copy already ships in sample_data/india_upi/; this refreshes it from source.
"""
import os
import shutil
import sys

DATASET = "aishricadhiman/upi-fraud-dataset"
DEST = os.path.join(os.path.dirname(__file__), "india_upi")


def main():
    if os.environ.get("KAGGLE_KEY") and not os.environ.get("KAGGLEHUB_TOKEN"):
        os.environ["KAGGLEHUB_TOKEN"] = os.environ["KAGGLE_KEY"]
    try:
        import kagglehub
    except ImportError:
        print("Install kagglehub:  .venv/bin/pip install kagglehub"); sys.exit(1)
    path = kagglehub.dataset_download(DATASET)
    os.makedirs(DEST, exist_ok=True)
    for f in os.listdir(path):
        if f.endswith(".csv"):
            shutil.copy(os.path.join(path, f), os.path.join(DEST, f))
            print("Refreshed", f)


if __name__ == "__main__":
    main()
