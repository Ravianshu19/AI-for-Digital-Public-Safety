"""
Fetch a real Indian banknote image dataset for the counterfeit real-world stress test.

Kaggle: gauravsahani/indian-currency-notes-classifier (~195 real mobile photos,
7 denominations). Provide a Kaggle token, then run:

  export KAGGLE_KEY="KGAT_xxx"
  .venv/bin/pip install kagglehub
  .venv/bin/python sample_data/fetch_indian_currency.py
  .venv/bin/python backend/realworld_counterfeit_eval.py
"""
import os
import sys

DATASET = "gauravsahani/indian-currency-notes-classifier"


def main():
    if os.environ.get("KAGGLE_KEY") and not os.environ.get("KAGGLEHUB_TOKEN"):
        os.environ["KAGGLEHUB_TOKEN"] = os.environ["KAGGLE_KEY"]
    try:
        import kagglehub
    except ImportError:
        print("Install kagglehub:  .venv/bin/pip install kagglehub"); sys.exit(1)
    path = kagglehub.dataset_download(DATASET)
    print("Downloaded to:", path)
    print("Now run:  .venv/bin/python backend/realworld_counterfeit_eval.py")


if __name__ == "__main__":
    main()
