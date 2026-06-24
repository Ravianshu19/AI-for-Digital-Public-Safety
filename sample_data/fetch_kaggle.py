"""
Fetch the public Kaggle PaySim fraud dataset for the fraud-graph module.

Uses kagglehub, which supports the new Kaggle API tokens (the "KGAT_..." format).
Provide a token one of these ways, then run this script:

  export KAGGLE_KEY="KGAT_xxx"          # new-style token
  # or place classic creds at ~/.kaggle/kaggle.json  {"username":..,"key":..}

  .venv/bin/pip install kagglehub
  .venv/bin/python sample_data/fetch_kaggle.py

The dataset lands in the kagglehub cache; backend/kaggle_fraud.py finds it there
automatically and converts it to the Indian UPI/wallet/crypto context.
"""
import os
import sys

DATASET = os.environ.get("KAGGLE_DATASET", "ealaxi/paysim1")


def main():
    if not (os.environ.get("KAGGLE_KEY") or os.environ.get("KAGGLEHUB_TOKEN")
            or os.path.exists(os.path.expanduser("~/.kaggle/kaggle.json"))):
        print("No Kaggle token found. Set KAGGLE_KEY=KGAT_... (or add ~/.kaggle/kaggle.json), then re-run.")
        sys.exit(1)
    try:
        import kagglehub
    except ImportError:
        print("Install kagglehub first:  .venv/bin/pip install kagglehub")
        sys.exit(1)
    # kagglehub reads the new-style token from KAGGLEHUB_TOKEN or KAGGLE_KEY.
    if os.environ.get("KAGGLE_KEY") and not os.environ.get("KAGGLEHUB_TOKEN"):
        os.environ["KAGGLEHUB_TOKEN"] = os.environ["KAGGLE_KEY"]
    print(f"Downloading {DATASET} via kagglehub …")
    path = kagglehub.dataset_download(DATASET)
    print("Downloaded to:", path)
    print("Now run:  .venv/bin/python backend/kaggle_fraud.py")


if __name__ == "__main__":
    main()
