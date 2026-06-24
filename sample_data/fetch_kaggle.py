"""
Fetch a public Kaggle fraud dataset (PaySim by default) for the fraud-graph module.

Kaggle downloads require an API token. To enable:
  1. https://www.kaggle.com/settings → "Create New API Token" → downloads kaggle.json
  2. mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json
  3. .venv/bin/pip install kaggle
  4. .venv/bin/python sample_data/fetch_kaggle.py

Then convert to the Indian UPI context with:  python backend/kaggle_fraud.py
"""
import os
import subprocess
import sys

DATASET = os.environ.get("KAGGLE_DATASET", "ealaxi/paysim1")
OUT = os.path.join(os.path.dirname(__file__), "kaggle")


def has_credentials() -> bool:
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return True
    return os.path.exists(os.path.expanduser("~/.kaggle/kaggle.json"))


def main():
    if not has_credentials():
        print("No Kaggle credentials found.")
        print("Add ~/.kaggle/kaggle.json (or set KAGGLE_USERNAME / KAGGLE_KEY), then re-run.")
        print("See the header of this file for steps.")
        sys.exit(1)
    os.makedirs(OUT, exist_ok=True)
    print(f"Downloading {DATASET} → {OUT} …")
    subprocess.run(
        [sys.executable, "-m", "kaggle", "datasets", "download",
         "-d", DATASET, "-p", OUT, "--unzip"],
        check=True,
    )
    print("Done. Files:")
    for f in os.listdir(OUT):
        print("  ", f)


if __name__ == "__main__":
    main()
